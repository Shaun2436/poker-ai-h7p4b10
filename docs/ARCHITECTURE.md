<!-- Z:\Project\poker-ai-h7p4b10\docs\ARCHITECTURE.md -->

# Architecture Notes

This document explains how the project is structured and why.

## Design Goals
- **Deterministic replay**: same `seed + action_log` ⇒ identical final score/state.
- **Separation of concerns**: engine vs AI vs API vs UI; no duplicated rules.
- **Testability**: unit tests for evaluator, validation, determinism, replay.
- **Structured messaging**: API returns `message_key + params`, not hard-coded UI strings.

---

## Key Layers

### Engine (`engine/`)
**Single source of truth** for the game.
- Owns rules and state transitions (`apply(action)`).
- Owns shuffle determinism (seeded RNG).
- Validates actions (PLAY/DISCARD constraints).
- Scores 5-card hands (Texas Hold'em categories). Points depend ONLY on category (no rank-based points).
- Maintains action history for replay/jump.

### AI (`ai/`)
Heuristic-only policy under uncertainty (does **not** know draw order).
- During live gameplay the AI does **not** know draw order.
- The heuristic policy (e.g., `ai_hint`, `ai_trace`) WILL use remaining deck count and remaining deck composition (unordered) as part of its decision process.
- What the player/UI can see may be more restricted (e.g., challenge reveal limits); this does not change the server-side heuristic information set.
- Produces:
  - `ai_hint`: computed live per step from public state (no rollouts)
  - `ai_trace`: generated offline (heuristic-only) as one feasible path per seed (used for validation gate and UI reveal)

Offline calibration (seed bucketing) uses a **staged pipeline** and may include a calibration step that inspects the full deck order (ordered) per seed:
1) baseline heuristic policy (fast coarse bucketing / pruning)
2) rollout / EV refinement (calibration-only)

Offline pipeline artifacts:
- Stored per run (git-ignored), e.g. `artifacts/pipeline/<run_id>/...`
- Key outputs:
  - `calibration_results.jsonl`
  - `trace_pass.jsonl` / `trace_fail.jsonl`
  - `seed_manifest.json` (runtime seed pool grouped by tier)

### API (`api/`)
Thin translation layer between HTTP and the engine.
- Parses requests into structured actions.
- Calls engine transitions and returns JSON.
- Enforces **mode-specific** rules (practice vs challenge).
- Never implements game logic.

### Web (`web/`)
Thin client (UI only).
- Renders cards/state/events.
- Lets user select indices and sends actions to API.
- Never validates actions or computes scoring.

---

## Supporting Directories (Not “layers”)
- `tests/`: unit tests (engine determinism, validation, evaluator correctness)
- `docs/`: specs and planning docs (this file, API contract, plan)

---

## Mode Rules (Visibility / Constraints)

### Practice
- Jump/undo allowed (implemented via deterministic replay).
- `ai_hint` will be shown during play.
- `ai_trace` will be available anytime.
- Remaining deck composition (unordered) may be revealed to the player/UI freely (draw order never revealed).

### Challenge
- Pass/fail via `target_score`.
- Jump/undo disabled (or optionally limited later).
- `ai_hint` is typically hidden during play and may be enabled in limited form by difficulty (policy-driven).
- `ai_trace` is revealed only after completion.
- Remaining deck composition (unordered) may be revealed to the player/UI in limited uses (reveal budget / tokens); draw order never revealed.

---

## Determinism Contract (What we guarantee)
- **Given**: `seed` and a list of actions (`action_log`)
- **Then**: the engine must reproduce the same hand sequence, state sequence, and final score exactly.
- This is the foundation for debugging, testing, AI evaluation, and difficulty calibration.
