# Development Plan

## Phase 0 – Repository Skeleton
- Project structure
- Rules documentation
- Planning documents

## Phase 1 – Python Engine MVP
Goal: deterministic and testable core logic.
- Card and deck abstraction
- Seeded shuffle and reproducibility
- State representation (hand, P, D, remaining deck)
- Action execution (PLAY / DISCARD)
- Poker hand classification
- CLI simulation of a full game

## Phase 2 – AI v1
Goal: decision-making without knowledge of draw order.
- Legal action generation
- Heuristic evaluation
- Rollout-based expected value estimation
- Action recommendation

## Phase 3 – Difficulty Calibration
- Offline evaluation of large numbers of seeds
- Difficulty metrics (expected score, variance, pass rate)
- Difficulty tier bucketing

## Phase 4 – Web Integration
- Web UI mock (card selection and visualization)
- Python API for game state transitions
- Frontend-backend integration via JSON
