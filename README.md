# Poker AI Decision Game (H7 P4 D10)

A deterministic, seed-reproducible poker decision game focused on
expected-value reasoning and AI-based decision making.

The project is designed as a **decision system**, not a traditional poker simulator.
Its primary goal is to explore decision-making under uncertainty, offline difficulty
calibration, and AI policy evaluation with cleanly separated components.

---

## Overview

- **Python** is used for the game rules engine and AI logic.
- **Web UI** is a thin client responsible only for interaction and visualization.
- All game rules, scoring, and AI decisions live exclusively in the Python backend.
- The system is fully reproducible given a shuffle seed and an action sequence.

This separation allows the same core engine to support human play,
AI decision making, and offline simulation.

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

## Determinism and Reproducibility

The game engine is **deterministic** in the following sense:

- Given the same shuffle seed and the same sequence of actions,
  the game state and final score are guaranteed to be identical.
- All randomness is explicitly controlled by the seed.
- This enables reliable AI evaluation, rollout-based expected value estimation,
  offline difficulty calibration, and exact replay for debugging.

From the player or AI perspective, future draws remain unknown,
but the underlying system behavior is fully reproducible.

---

## Game Modes

### Mode 1: Human vs AI
- Human and AI have identical information
- Both see remaining deck composition but not draw order
- Each plays a full game independently
- Results can be compared across individual seeds or aggregated runs

### Mode 2: Difficulty / Endless Mode
- Shuffle seeds are evaluated offline using AI or baseline policies
- Seeds are bucketed into difficulty tiers (e.g. Easy / Medium / Hard)
- During gameplay, seeds are sampled from a chosen tier
- Progress is measured by consecutive clears or cumulative score

---

## Repository Structure

```
engine/ # Python game engine (state, actions, scoring)
ai/ # AI logic and offline seed evaluation
web/ # Web UI (thin client; no game logic)
docs/ # Rules and design documentation
```

- `engine/` is the single source of truth for game rules.
- `ai/` builds on top of the engine for decision-making and simulation.
- `web/` handles only user interaction and visualization.
- `docs/` captures rules, design decisions, and planning.

---

## Development Roadmap

### Phase 0 – Repository Skeleton
- Project structure
- Rules documentation
- Planning documents

### Phase 1 – Engine MVP
Goal: deterministic, testable core logic.
- Seeded shuffle and reproducibility
- State representation (hand, P, D, remaining deck)
- Action execution (PLAY / DISCARD)
- Poker hand classification
- CLI-based full game simulation

### Phase 2 – AI v1
Goal: decision making without knowledge of draw order.
- Legal action generation
- Heuristic evaluation
- Rollout-based expected value estimation
- Action recommendation

### Phase 3 – Difficulty Calibration
- Offline evaluation of large numbers of seeds
- Difficulty metrics (expected score, variance, pass rate)
- Seed bucketing into difficulty tiers

### Phase 4 – Web Integration
- Web UI mock (card selection and visualization)
- Python API for game state transitions
- Frontend-backend integration via JSON

---

## Notes

- Game logic is intentionally implemented in a single language (Python).
- The web frontend never computes scores or validates actions.
- Server-side validation and anti-cheat mechanisms are out of scope for the MVP.
