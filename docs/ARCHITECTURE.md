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
- Scores 5-card hands (Texas Hold'em categories).
- Maintains action history for replay/jump.

### AI (`ai/`)
Policy AI under uncertainty (does **not** know draw order).
- During live gameplay the AI does **not** see the deck composition; it only sees `deck_remaining_count` and public state fields (hand, `p_remaining`, `d_remaining`, etc.).
- Produces either:
  - `ai_hint` (one-step recommended action + explanation key), or
  - `ai_trace` (full recommended sequence from start state).
- Offline calibration uses a **two-pass pipeline** specifically for seed bucketing and may include a calibration step that inspects full deck composition (unordered) per seed for that purpose:
  1) baseline heuristic policy (fast coarse bucketing)
  2) EV rollout policy (slower boundary refinement)

Artifacts and runtime optimization:
- The calibration pipeline SHOULD emit two artifact types: calibration-only artifacts (e.g., `out/calibration/<task>/<seed>.json`) that MAY be generated with known-deck access for tiering, and public precomputed traces (e.g., `out/traces/public/ev_rollout_v1/<seed>.json`) that MUST be generated under unknown-deck constraints.
- The server may consume public precomputed traces at runtime to serve `ai_hint` or `ai_trace` payloads without exposing deck composition, saving compute resources.
- Runtime policy: the server SHOULD NOT compute a full `ai_trace` on-demand; it MAY compute a single-step `ai_hint` using public state and/or serve a precomputed public `ai_trace` artifact (which MUST declare `info_set: "unknown_deck"`).
- Artifacts should be stored in `out/` or secure storage (not committed to git).

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
- `ai_hint` may be shown during play (policy-driven).
- `ai_trace` may be available anytime.

### Challenge
- Pass/fail via `target_score`.
- Jump/undo disabled (or optionally limited later).
- `ai_hint` is typically hidden during play and may be enabled in limited form by difficulty (policy-driven).
- `ai_trace` is revealed only after completion.

---

## Determinism Contract (What we guarantee)
- **Given**: `seed` and a list of actions (`action_log`)
- **Then**: the engine must reproduce the same hand sequence, state sequence, and final score exactly.
- This is the foundation for debugging, testing, AI evaluation, and difficulty calibration.
