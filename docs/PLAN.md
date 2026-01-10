# Development Plan

This plan prioritizes software engineering fundamentals:
clear boundaries, deterministic replay, testability, and incremental delivery.

---

## Phase 0 — Repository Skeleton (DONE)
Definition of done:
- `README.md` explains rules, determinism, and architecture.
- `docs/` contains API contract and architecture notes.
- Base folder structure exists.

Deliverables:
- `README.md`
- `docs/PLAN.md`
- `docs/API_CONTRACT.md`
- `docs/ARCHITECTURE.md`

---

## Phase 1 — Engine MVP (Python)
Goal: deterministic, testable core rules engine.

Definition of done:
- A seed produces a reproducible shuffle.
- `GameState` can be initialized from a seed.
- `apply(action)` validates and transitions state deterministically.
- 5-card evaluator correctly classifies hand categories.
- Score is computed via a scoring policy.
- Replay works: seed + action list reproduces identical final score.
- Unit tests cover determinism, validation, and evaluator.

Deliverables:
- `engine/` implementation
- `tests/` for evaluator + determinism + validation
- CLI or minimal API harness to run a full game by providing actions

---

## Phase 2 — API MVP (Python FastAPI)
Goal: expose the engine to the frontend via a stable JSON contract.

Definition of done:
- `POST /game/start` returns initial state.
- `POST /game/step` accepts an action and returns next state + events.
- Server validates all actions.
- Responses contain no hard-coded UI sentences; use structured keys + params.

Deliverables:
- `api/` endpoints + request/response models
- Contract documented in `docs/API_CONTRACT.md`

---

## Phase 3 — AI v1
Goal: a policy that recommends actions without knowing draw order.

Definition of done:
- Generates legal actions.
- Heuristic ranking (baseline).
- Rollout sampling to estimate expected value.
- Produces a recommended action + explanation (structured keys).

Deliverables:
- `ai/` policies
- optional offline script to run many seeds and collect metrics

---

## Phase 4 — Mode 2 Difficulty Calibration
Goal: bucket seeds into tiers using offline simulation.

Definition of done:
- Runs many seeds offline.
- Produces difficulty metrics (expected score, pass rate).
- Outputs tier files (e.g., JSON lists of seeds per tier).

Deliverables:
- `ai/seed_eval.py` (or similar)
- `docs/` notes on tiering strategy

---

## Phase 5 — Web Integration
Goal: interactive UI with real backend.

Definition of done:
- Web UI can start a game (seed or random).
- User can select cards, send actions, and see updated state.
- Displays AI hint and explanation.
- No duplicated rules in frontend.

Deliverables:
- `web/` UI using the API endpoints
