# Poker AI Decision Game (H7 P4 D10)

A deterministic, seed-reproducible poker decision game focused on expected-value reasoning and AI decision-making.

This project is designed as a **decision system**, not a traditional poker simulator. It emphasizes:
- clean separation of concerns (engine vs AI vs API vs UI),
- reproducibility (seed + action log replay),
- testability (unit tests for rules and determinism),
- and a thin web client (UI only, no game logic).

---

## Overview

- **Python Engine (`engine/`)**: single source of truth for rules, state transitions, scoring, and validation.
- **Python AI (`ai/`)**: policies that choose actions using the engine (heuristics + rollout sampling).
- **Python API (`api/`)**: HTTP endpoints that expose game state transitions to the frontend.
- **Web UI (`web/`)**: interaction + visualization only (card selection, sending actions, rendering results).
- **Tests (`tests/`)**: unit tests for evaluator, actions, determinism, and replay.

---

## Fixed Parameters (Current Version)

- Hand size **H = 7**
- Number of plays **P = 4**
- Discard budget **D = 10**  
  (consumed by the number of discarded cards, not by discard actions)
- Standard 52-card deck, no jokers
- Remaining deck composition is public; draw order is unknown
- No round structure: the game ends immediately when `P == 0`

---

## Core Mechanics (Summary)

### Actions

**PLAY**
- Choose exactly 5 cards from the 7-card hand
- Score once based on the best 5-card Texas Hold’em category
- Remove the 5 cards, draw 5 new cards
- Decrement `P`
- When `P == 0`, the game ends immediately

**DISCARD**
- Discard `n` cards where `1 <= n <= min(hand_size, D)`
- Reduce `D` by `n`
- Draw `n` cards to restore hand size
- Discarding yields no score

### Scoring
- Each PLAY action produces exactly one score
- Scores are determined by a fixed category-to-points mapping
- Total score is the sum of all PLAY scores

---

## Determinism and Replay

The engine is **deterministic** in the following sense:
- Given the same shuffle seed and the same sequence of actions, the game state and final score are identical.
- All randomness is explicitly controlled by the seed.

This enables:
- exact replay for debugging (seed + action log),
- reliable AI evaluation (rollouts),
- and offline difficulty calibration (seed bucketing).

---

## Contracts and Documentation

- API contract (request/response JSON): `docs/API_CONTRACT.md`
- Architecture / layering notes: `docs/ARCHITECTURE.md`
- Development plan: `docs/PLAN.md`

---

## Repository Structure

```
engine/ # rules engine: state, actions, validation, scoring (no UI text)
ai/ # AI policies: heuristics + rollouts (calls engine)
api/ # HTTP API: start/step endpoints (returns structured events)
web/ # UI only: selection + rendering (no scoring, no rule checks)
tests/ # unit tests: evaluator, determinism, replay, validations
docs/ # documentation: plan, architecture, API contract
```


---

## Development Roadmap

### Phase 0 – Repository Skeleton (DONE)
- README + docs
- project structure
- initial UI mock (optional)

### Phase 1 – Engine MVP
Goal: deterministic, testable core logic.
- Seeded shuffle and reproducibility
- `GameState` representation (hand, P, D, score, remaining deck)
- Action validation + state transition (`apply(action)`)
- Poker hand classification (5-card evaluator)
- Scoring policy
- Replay log (seed + action list)

### Phase 2 – AI v1
Goal: decision-making without knowledge of draw order.
- Legal action generation
- Heuristic evaluation
- Rollout-based expected value estimation
- Action recommendation (with structured explanation keys)

### Phase 3 – Difficulty Calibration (Mode 2)
- Offline evaluation of many seeds
- Difficulty metrics (expected score, variance, pass rate)
- Seed bucketing into difficulty tiers

### Phase 4 – Web Integration
- Web UI mock → backend API integration
- Server-side validation (UI never validates rules)
- Display AI hint + explanation

---

## Notes

- Game logic is intentionally implemented in a single language (Python) to avoid duplicate implementations.
- The frontend never computes scores or validates actions.
- Anti-cheat is out of scope for MVP (but replay validation is a natural next step).
