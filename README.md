<!-- Z:\Project\poker-ai-h7p4b10\README.md -->

# Poker AI Decision Game (H7 P4 D10)

A deterministic, seed-reproducible poker decision game focused on
expected-value (EV) decision making and clean software architecture.

This project is designed as a **decision system**, not a traditional poker simulator.
It emphasizes:
- separation of concerns (engine vs AI vs API vs UI),
- determinism and replayability,
- testability,
- and explainable AI recommendations.

---

## Overview

- **Python Engine (`engine/`)**  
  Single source of truth for rules, state transitions, scoring, and validation.

- **Policy AI (`ai/`)**  
  Decision-making under uncertainty using heuristics and rollout-based EV estimation.
  The AI does **not** know future draw order.

- **Python API (`api/`)**  
  Exposes engine transitions via JSON. No game logic lives in the API.

- **Web UI (`web/`)**  
  Thin client for visualization and interaction only.

- **Tests (`tests/`)**  
  Unit tests for evaluator correctness, determinism, validation, and replay.

---

## Fixed Parameters (Current Version)

- Hand size **H = 7**
- Number of plays **P = 4**
- Discard budget **D = 10**
- Standard 52-card deck, no jokers
- **Remaining deck composition is NOT exposed to player or in-game AI during gameplay; only `deck_remaining_count` is provided.**  For offline difficulty calibration, the calibration step that performs seed bucketing will examine full deck composition (unordered) per seed — other offline artifacts intended for runtime (public precomputed traces) will be generated without access to deck composition.
- No round structure: the game ends immediately when `P == 0`

---

## Core Mechanics

### Actions

**PLAY**
- Select exactly 5 cards from the 7-card hand
- Score the best 5-card Texas Hold’em category
- Remove those cards, draw 5 new cards
- Decrement `P`

**DISCARD**
- Discard `n` cards where `1 <= n <= min(hand_size, D)`
- Reduce `D` by `n`
- Draw `n` cards to restore hand size
- Discarding yields no score

---

## Determinism and Replay

- All randomness is controlled by a seeded RNG inside the engine.
- Same seed + same action sequence ⇒ identical game evolution and final score.
- Replay is implemented by reapplying the action log from the initial seed.

---

## Game Modes

### Practice Mode
- No pass/fail target score
- Jump/undo allowed via replay
- Optional sync AI hint (`ai_hint`) (policy-driven; may be limited by difficulty)
- Full AI policy trace (`ai_trace`) available

### Challenge Mode
- Pass/fail **target score enforced**
- AI trace is revealed only after completion.
- Jump/undo disabled or limited
- AI hint is typically hidden and may be enabled in limited form by difficulty (policy-driven).

---

## Difficulty Calibration

Difficulty tiers are generated offline using a two-stage pipeline:

1. **Baseline heuristic policy**  
   Fast, zero-rollout evaluation for coarse bucketing.

2. **Policy AI (EV)**  
   Rollout-based EV estimation for boundary refinement.

Separate seed pools are used for Practice and Challenge modes.

---

## Development Roadmap

1. Engine MVP
2. API MVP
3. Policy AI
4. Difficulty calibration
5. Web integration

---

## Documentation

- API contract: `docs/API_CONTRACT.md`
- Architecture notes: `docs/ARCHITECTURE.md`
- Development plan: `docs/PLAN.md`

---

## Notes

- Only **Baseline heuristic policy** and **Policy AI (EV)** are used. No perfect-information oracle AI exists.
- The frontend never computes scores or validates rules.
- Anti-cheat is out of scope for the MVP.
