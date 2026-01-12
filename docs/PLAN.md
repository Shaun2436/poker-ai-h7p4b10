<!-- Z:\Project\poker-ai-h7p4b10\docs\PLAN.md -->

# Development Plan

This plan is ordered by **software architecture dependencies**, not by gameplay difficulty.
You implement the deterministic core first, then wrap it with API, then add AI, then calibrate difficulty, then build UI.

---

## Phase 0 — Repository Skeleton (DONE)
Definition of done:
- README explains rules, determinism, and modes
- `docs/` contains API contract + architecture + plan
- Base folder structure exists (`engine/`, `ai/`, `api/`, `web/`, `tests/`, `docs/`)

---

## Phase 1 — Engine MVP (Python)
Goal: deterministic, testable core rules engine.

Definition of done:
- Seeded shuffle is reproducible
- `GameState` initializes from seed
- `apply(action)` validates + transitions deterministically
- 5-card evaluator correctly classifies categories
- Scoring policy maps categories to points
- Replay works: `seed + action_log` reproduces identical final score
- Unit tests cover determinism, validation, evaluator

Deliverables:
- `engine/` implementation
- `tests/` for evaluator + determinism + validation
- CLI harness to run a full game from scripted actions (good for debugging)

---

## Phase 2 — API MVP (Python FastAPI)
Goal: stable JSON contract between UI and backend.

Definition of done:
- `POST /game/start` creates a game (seed or difficulty pool)
- `POST /game/step` applies one action and returns updated state + events
- `POST /game/jump` supports undo in Practice mode (and optional limited undo in Challenge)
- Server validates all actions
- Responses contain **no hard-coded UI sentences** (use `message_key + params`)

Deliverables:
- `api/` endpoints + request/response models
- Contract implemented as documented in `docs/API_CONTRACT.md`

---

## Phase 3 — AI v1 (Two Policies)
Goal: recommend actions without knowing draw order.

Definition of done:
- Legal action generation (PLAY combos, DISCARD combos)
- **Baseline heuristic** policy (0 rollouts)
- **Policy AI (EV)** using rollout sampling
- Optional output:
  - one-step hint (`ai_hint`) returned per step
  - full trace (`ai_trace`) from initial state

Deliverables:
- `ai/` policies
- tests for action generation and determinism of AI plumbing (where applicable)

---

## Phase 4 — Difficulty Calibration (Offline)
Goal: bucket seeds into tiers using offline simulation.

Definition of done:
- Runs large batches of seeds offline
- Two-stage bucketing:
  - baseline heuristic for coarse bucketing
  - EV rollouts to refine boundary seeds
- Calibration runs may be executed with access to the full remaining deck composition (unordered) per seed to enable accurate seed evaluation; these runs are offline and separate from live gameplay
- Separate pools for Practice and Challenge
- Outputs tier files (JSON) consumed by `/game/start`
- Outputs optional precomputed public AI trace artifacts (e.g., `out/traces/public/<policy>/<seed>.json`) which may be used by the server at runtime to serve traces quickly without performing expensive rollouts; these public artifacts MUST be generated under unknown-deck constraints.

Deliverables:
- `ai/seed_eval.py` (or similar)
- `out/` artifacts (ignored by git)
- `docs/` notes on tiering strategy

---

## Phase 5 — Web Integration
Goal: interactive UI with real backend.

Definition of done:
- Web UI can start a game by mode + difficulty
- User can select cards and submit actions
- Practice supports jump/undo UI
- Challenge enforces pass/fail and reveals only after completion 
- AI hint is typically hidden and may be enabled in limited form by   difficulty (policy-driven).
- Displays AI hint and explanation keys (rendered as UI text client-side)

Deliverables:
- `web/` UI wired to API via JSON
- minimal UX polish (selection, feedback, errors)
