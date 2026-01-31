<!-- Z:\Project\poker-ai-h7p4b10\docs\CALIBRATION_PIPELINE.md -->

# Calibration Pipeline (Offline)

This document describes the **offline difficulty calibration pipeline** used to generate
difficulty tiers and challenge targets from reproducible simulation data.

It is written for:
- reviewers/interviewers evaluating engineering and responsible-AI practices, and
- future contributors implementing the offline pipeline runner.

> Scope note: This document is **explanatory**. It does not modify the API contract.
> Runtime behavior is still governed by `docs/API_CONTRACT.md`.

---

## Goals

1. **Difficulty tiering**  
   Bucket deterministic seeds into difficulty tiers using offline simulation.

2. **Challenge targets**  
   Compute per-tier target scores (or other targets) for Challenge mode.

3. **Responsible AI boundary enforcement**  
   Ensure offline calibration uses privileged information **only offline** and that
   runtime-facing AI remains constrained to the gameplay information set.

4. **Data preparation & evaluation**  
   Treat calibration as a data pipeline that produces **cleaned, labeled, and analyzed**
   evaluation data (JSONL artifacts) suitable for reporting and audit.

---

## Terminology

- **Seed**: Integer that deterministically initializes a game (shuffle + initial deal).
- **Mode**: `practice` or `challenge`.
- **Difficulty tier**: A discrete bucket name (e.g., `easy/medium/hard`) used for runtime sampling.
- **Ordered deck**: The engine’s internal draw sequence (`GameState.deck`).
- **Remaining deck composition (unordered)**: Multiset/counts of remaining cards with **no draw order**.

---

## Information sets (must not be mixed)

The project has **two AI contexts** defined in `docs/API_CONTRACT.md`:

### Gameplay AI (ai_hint / ai_trace)
- Same information available to the player.
- Always includes **remaining deck composition (unordered)**.
- MUST NOT include **deck order** or any **future draw** knowledge.

### Calibration AI (bucketing only)
- Full internal game state, including **ordered deck**.
- Outputs MUST NOT appear in gameplay APIs.

**Design intent**: Stage B may use ordered-deck access to estimate *upper-bound* performance,
but no ordered-deck-derived decision guidance is ever exposed to runtime UI or gameplay endpoints.

---

## Engine contracts leveraged by calibration

Calibration is a consumer of the engine. The engine remains the single source of truth for rules.

Relevant engine guarantees (see `engine/state.py`, `engine/scoring.py`):
- The engine may store the **full ordered deck** internally for determinism/replay.
- Public state **never exposes draw order**.
- Public state **always exposes remaining deck composition** (unordered),
  constructed canonically so that map/list ordering does not leak the internal draw order.
- Scoring is separated into:
  - **gameplay** scoring (jackpots allowed), and
  - **model** scoring (jackpots collapsed/ignored) used by calibration/AI to stabilize statistics.

---

## Pipeline overview (staged)

Offline calibration uses a staged pipeline (see `docs/README.md`, `docs/PLAN.md`, `docs/ARCHITECTURE.md`):

1. **Baseline heuristic policy**  
   Fast, zero-rollout evaluation for coarse bucketing / pruning.

2. **Rollout / EV refinement (calibration-only, fully known-deck, ordered)**  
   Used to refine boundary seeds and compute challenge targets.

3. **Heuristic trace validation gate (order-unknown)**  
   Generates one feasible `ai_trace` per seed under **runtime constraints** and filters out seeds
   that are not achievable without deck-order knowledge.

The final output is a runtime-consumable seed pool:
- `seed_manifest.json` grouped by tier
- separated pools for Practice and Challenge

---

## Stage 1 — Baseline heuristic (coarse bucketing)

### Purpose
Produce a cheap, stable signal for many seeds:
- initial ranking,
- pruning, and
- selecting “boundary seeds” that require more expensive evaluation.

### Inputs
- Seed list (or seed range)
- Mode (`practice` / `challenge`)
- Engine version/config (recorded for audit)

### Outputs
Per-seed records appended to `calibration_results.jsonl` (at minimum):
- seed, mode
- baseline score/metric
- any flags (invalid run, exceptions, etc.)

### Notes
Stage 1 should be designed to be:
- deterministic given the seed,
- fast enough to run in large batches,
- explainable (simple heuristics, no hidden information assumptions beyond what Stage 1 allows).

---

## Stage 2 — Rollout / EV refinement (ordered-deck, offline only)

### Purpose
Refine evaluation for boundary seeds by estimating:
- expected total score (EV) and variability,
- (challenge) success probability under a defined evaluation policy,
- and tier targets (e.g., target score thresholds).

Stage 2 exists to answer:
> “Given this seed, what performance is realistically achievable (upper bound) under offline evaluation?”

### Information set
Stage 2 is permitted to use:
- the full internal game state, including **ordered deck**.

Stage 2 MUST NOT:
- produce outputs that are directly exposed as runtime hints/traces,
- rely on ordered-deck knowledge in any runtime-facing policy.

### Recommended minimal evaluation approach (non-normative)
The exact algorithm is not fixed by the project docs. A low-complexity, interview-friendly approach is:

1. **Generate candidate actions**  
   - Enumerate legal PLAY actions (choose 5 from 7), score by a cheap heuristic, keep top-K.
   - For DISCARD, consider a small, fixed set of discard templates (e.g., discard 0/1/2/3 “worst” cards)
     to avoid combinatorial explosion.

2. **Estimate action value with limited rollouts**  
   For each candidate action:
   - Apply the action on a cloned state.
   - Perform `R` rollouts to terminal (P==0) using a simple deterministic policy for subsequent steps
     (e.g., always choose the highest-heuristic play).
   - Record terminal score (and for challenge, whether a target threshold is met, if applicable).

3. **Select best candidate by EV**  
   Choose the action with the highest mean terminal score (or other defined objective).

4. **Aggregate seed-level metrics**  
   Store per-seed aggregates:
   - EV mean (`stage_b_ev_mean`)
   - EV std (`stage_b_ev_std`)
   - (challenge) success rate (`stage_b_success_rate`)

This produces stable, reproducible evaluation data without requiring ML frameworks.

### Model scoring guidance
Stage 2 evaluation should use the **model** scoring context (`engine/scoring.py`) to avoid jackpot outliers
polluting difficulty statistics. In particular, jackpot categories (e.g., `STRAIGHT_FLUSH`) are collapsed/ignored
for calibration metrics, while gameplay scoring remains unchanged.

### Outputs
Append refined per-seed records to `calibration_results.jsonl`, including:
- seed, mode
- Stage 1 baseline metric (if available)
- Stage 2 EV metrics (mean/std, success rate if relevant)
- evaluation configuration (policy name/version, rollout count, K)

---

## Stage 3 — Heuristic trace validation gate (order-unknown)

### Purpose
Ensure seeds admitted to runtime pools are **achievable under runtime constraints**:
- remaining deck count and composition are known,
- draw order is unknown.

This is both:
- a **fairness / anti-leak** guardrail, and
- a UX artifact generator for Challenge mode (`ai_trace` reveal after completion).

### Information set
Stage 3 MUST use the same information available at runtime:
- public state only,
- remaining deck composition (unordered),
- no ordered-deck access.

### Procedure
For each candidate seed:
1. Run the heuristic-only policy once to produce a single feasible trace (action sequence).
2. If the trace completes without relying on deck order:
   - write seed + trace summary to `trace_pass.jsonl`,
   - mark the seed eligible for runtime pools.
3. Otherwise:
   - write seed + failure reason to `trace_fail.jsonl`,
   - exclude from runtime pools (retained for analysis).

### Outputs
- `trace_pass.jsonl`
- `trace_fail.jsonl`
- optionally, stored `ai_trace` artifacts (generated under order-unknown constraints)

---

## Data preparation tasks (cleaning, labeling, exploratory analysis)

Calibration is treated as a **data pipeline**, not just “AI logic”.

### Dataset definition
The primary dataset is the set of per-seed evaluation records emitted per run:
- `calibration_results.jsonl` (Stage 1 + Stage 2 metrics)
- `trace_pass.jsonl` / `trace_fail.jsonl` (Stage 3 validation labels)

### Cleaning
Examples of cleaning steps (policy choices, recorded per run):
- remove or flag seeds that crash/raise exceptions during simulation,
- flag non-reproducible runs (should be rare given determinism),
- exclude seeds that fail the trace validation gate from runtime pools,
- optionally flag extreme outliers (even in model scoring) for manual review.

### Labeling
Programmatic labels derived from calibration outputs:
- difficulty tier assignment per seed,
- (challenge) success/fail label under the evaluation policy,
- trace validation pass/fail.

These labels are the primary bridge from offline analysis to runtime configuration.

### Exploratory analysis (EDA)
Typical offline analysis over artifacts:
- score/EV distributions per tier,
- boundary seed inspection (where Stage 1 and Stage 2 disagree),
- tier threshold sensitivity (e.g., quantile cutoffs),
- calibration stability across multiple runs/configs.

EDA outputs should be summarized in `summary.json` for repeatability.

---

## Artifacts and storage

Per `docs/PLAN.md` / `docs/ARCHITECTURE.md`, artifacts are stored per run (git-ignored):

- `artifacts/pipeline/<run_id>/calibration_results.jsonl`
- `artifacts/pipeline/<run_id>/trace_pass.jsonl`
- `artifacts/pipeline/<run_id>/trace_fail.jsonl`
- `artifacts/pipeline/<run_id>/seed_manifest.json`
- `artifacts/pipeline/<run_id>/summary.json`

### Traceability expectations
Each run should record:
- run_id timestamp/identifier,
- engine commit/version,
- configuration (K, rollouts, policy name/version),
- seed source (range or explicit list),
- summary stats (counts per tier, pass/fail rates).

---

## Runtime integration

Runtime seed selection is defined in `docs/API_CONTRACT.md` (`POST /game/start`):

- If a request provides `seed`, the server starts exactly that seed.
- If `seed` is omitted, the server samples from the offline-emitted `seed_manifest.json`
  for the requested `(mode, difficulty_tier)`.
- Practice and Challenge use **separate pools**.
- Challenge mode may use calibration-derived `target_score` values (per tier).

**Contract note**: Remaining deck composition is always exposed to the player/UI as counts (unordered).
Draw order is never exposed.

---

## Responsible AI notes (public-sector aligned)

This project intentionally separates:
- **evaluation-time privileges** (ordered-deck access) and
- **deployment-time constraints** (public information only),

to prevent information leakage and preserve fairness.

Additional governance-friendly properties:
- reproducible simulation data (seeded determinism),
- auditable artifacts (JSONL logs per run),
- explainable heuristics (no opaque model dependency required),
- no personal data (all data is synthetic, generated from game rules).

---

## Status

As of the Engine MVP stage:
- The engine supports determinism, public/private state separation, and model vs gameplay scoring.
- The offline pipeline runner and `ai/` policies are planned (see `docs/PLAN.md` Phase 4) and will
  emit the artifacts described above.
