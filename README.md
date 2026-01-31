<!-- Z:\Project\poker-ai-h7p4b10\README.md -->

# Poker AI Decision Game (H7 P4 D10)

A deterministic, seed-reproducible poker decision game focused on decision-making under uncertainty, 
clean software architecture, reproducible offline calibration, and explainable heuristic recommendations.

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
  Decision-making under uncertainty using heuristics.
  - `ai_hint`: computed at runtime from public state (heuristic-only, order-unknown; remaining deck composition always known)
  - `ai_trace`: generated offline from public state (heuristic-only, order-unknown; remaining deck composition always known); revealed freely in practice, and revealed only after completion in challenge.
  - Rollout/EV is used **only** for offline difficulty calibration.
  - See docs/CALIBRATION_PIPELINE.md for offline calibration and data preparation details.

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
- **Remaining deck composition is ALWAYS exposed to the player/UI (draw order is never exposed).**
- **Scoring depends ONLY on the 5-card hand category. Card ranks do not add extra points.**
- Offline calibration will inspect full deck composition (ordered) per seed to assign difficulty tiers and target scores.
- Any offline artifacts intended for gameplay (e.g., `ai_trace`) are generated under the same order-unknown constraints as runtime (remaining deck count and composition known; draw order unknown).
- No round structure: the game ends immediately when `P == 0`

---

## Core Mechanics

### Actions

**PLAY**
- Select exactly 5 cards from the 7-card hand
- Score the selected 5-card hand category (no best-of-7 search)
- Remove those cards, draw 5 new cards
- Decrement `P`

**DISCARD**
- Discard `n` cards where `1 <= n <= min(hand_size, D)`
- Reduce `D` by `n`
- Draw `n` cards to restore hand size
- Discarding yields no score

### Scoring
- Points are determined ONLY by the evaluated 5-card hand category (no best-of-7 search).
- Card rank values (e.g., A>K>Q...) do not modify points.
- Full scoring table is defined in `docs/API_CONTRACT.md`.
- `STRAIGHT_FLUSH` is a gameplay scoring category with a large point award; there is no special early-termination “auto-pass” rule (the game still ends when `P == 0`).
- For calibration and AI modeling, `STRAIGHT_FLUSH` is treated as `FLUSH` (collapsed) to keep MODEL_CATEGORIES stable.
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
- `ai_hint` available with unlimited uses (server returns `hint_policy: "unlimited"`)
- Remaining deck composition is always visible to the player/UI (unordered)
- Full AI policy trace (`ai_trace`) available at any time
- Practice policy is fixed: `hint_policy` and `jump_policy` are always `"unlimited"` (see `docs/API_CONTRACT.md`).

### Challenge Mode
- Pass/fail **target score enforced**
- `ai_hint` is typically hidden during play (controlled by `hint_policy`: off/unlimited/limited + optional budgets; may be enabled in limited form by difficulty)
- `ai_trace` is revealed only after completion
- `jump_policy` controls jump/undo (off/unlimited/limited + optional budgets)
- Remaining deck composition is always visible to the player/UI (unordered)
- Other anti-cheat limits (e.g., “replay after fail”) are future work and are not part of the current API contract

---



## Difficulty Calibration

Difficulty tiers are generated offline using a staged pipeline:

1. **Baseline heuristic policy**  
   Fast, zero-rollout evaluation for coarse bucketing / pruning.

2. **Rollout / EV refinement (calibration-only, fully known-deck, ordered)** 
   Used to refine boundary seeds and compute challenge targets.

3. **Heuristic trace validation gate (order-unknown)**  
      After calibration, run a heuristic-only `ai_trace` once per candidate seed to verify it is achievable under runtime constraints (remaining deck count and composition known; draw order unknown).
   - pass → eligible for the runtime seed pool
   - fail → retained for analysis, excluded from runtime pools

The runtime seed pool is emitted as `seed_manifest.json` (grouped by difficulty tier).
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
- offline calibration: `CALIBRATION_PIPELINE.md`

---

## Notes

- Runtime decision support (`ai_hint`, `ai_trace`) is **heuristic-only** (order-unknown; remaining deck count and composition are always known). Rollout/EV is used **only** in offline calibration.
- The frontend never computes scores or validates rules.
- Anti-cheat is out of scope for the MVP.
