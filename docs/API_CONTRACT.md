<!-- Z:\Project\poker-ai-h7p4b10\docs\API_CONTRACT.md -->

# API Contract

This file defines the **exact JSON shapes** exchanged between the Web UI (client)
and the Python API (server).

The frontend is a thin client.
All validation, scoring, and rule enforcement happen server-side.

> Important: Examples may shorten long arrays (e.g., `events`, `ai_trace.steps`) for readability.
> Real responses must include the full required fields.

---

## Conventions

### Card Encoding
Cards are encoded as strings using `RS` format:
- `R` rank: `2–9`, `T`, `J`, `Q`, `K`, `A`
- `S` suit: `S`, `H`, `D`, `C`

Examples: `AS`, `TD`, `7H`

### Selection Indices
- `selected_indices` is **0-based** and refers to positions in the server-provided `state.hand` array.
- If the UI sorts cards visually, it must preserve a mapping back to these indices.

### Modes
- `practice`: training mode (jump/undo may be enabled, AI hints/trace available)
- `challenge`: pass/fail mode (target score, AI trace available after success or fail; jump/undo and AI hint may vary by difficulty)

### Difficulty
- `difficulty_tier`: project-defined string (e.g., `easy`, `medium`, `hard`)
- Practice and Challenge use **separate seed pools** per tier.

### Scoring (FINAL)
- Points are determined ONLY by the best 5-card Texas Hold’em category.
- Card ranks do not add extra points (no “kicker value” scoring).
- The scoring table is a fixed mapping: `category -> points`.

### Deck Information (FINAL)
The full deck order is determined by `seed` and is kept server-side to support deterministic replay.

Visibility (gameplay):
- The **server** stores the full deck order (or equivalent RNG state + draw pointer).
- Draw order is **never** exposed to the player or in-game decision AI.
- `state.deck_remaining_count` is always exposed to the client.
- Remaining deck composition (unordered) may be exposed to the client depending on mode/policy (e.g., freely in `practice`, limited in `challenge`).
- `ai_hint` and `ai_trace` will use remaining deck composition (unordered) but MUST NOT depend on draw order. This does not imply the composition is sent to the client.

API requirements (gameplay):
- The API **MUST** include `state.deck_remaining_count` in gameplay responses.
- The API **MAY** include remaining deck composition in gameplay responses when allowed by the server’s reveal policy (see `reveal_policy` below).

Offline calibration:
- For offline **difficulty calibration** (seed bucketing), a dedicated calibration step may examine the full deck order (ordered) for each seed for the sole purpose of assigning difficulty tiers and computing `target_score`. These calibration runs are separate from normal gameplay and from public trace generation; their outputs (tier files, target scores) are consumed by the server to seed challenge pools.

Replay guarantee:
- Given the same `seed` and the same `action_log`, the server can reproduce the exact same game.

### Hint / Jump Policies
To support "vary by difficulty" and limited usage, the server returns policies:

- `hint_policy`: `"off" | "unlimited" | "limited"`
- `jump_policy`: `"off" | "unlimited" | "limited"`

If a policy is `"limited"`, the response MUST include:
- `<policy>_budget_total`
- `<policy>_budget_remaining`

Notes:
- The client may *request* hints/jumps, but the server decides the final policies.

### Reveal Policy (Deck Composition)
To support "view remaining deck composition" with optional limits, the server returns a reveal policy:

- `reveal_policy`: `"off" | "unlimited" | "limited"`

If `reveal_policy` is `"limited"`, the response MUST include:
- `reveal_budget_total`
- `reveal_budget_remaining`

Notes:
- `reveal_policy` controls whether `state.deck_remaining_counts` / `state.deck_remaining` may be included in responses.
- If `reveal_policy = off`, the server MUST omit `deck_remaining_counts` / `deck_remaining`.
- If `reveal_policy = limited`, each response that includes deck composition MUST decrement `reveal_budget_remaining` (server-defined; may be triggered by an explicit reveal request or by including the fields).

### Target Score (Challenge)
Challenge mode enforces a pass/fail `target_score`.

- `target_score` is determined server-side from `(mode, difficulty_tier)` using **offline calibration output**
  (e.g., per-tier config or metadata stored alongside the challenge seed pool).
- The API **MUST** return `target_score` for `challenge`.
- The API **MUST** return `target_score: null` for `practice`.

### Common Success Response Shape
To keep the frontend simple, all successful game endpoints should return:

- `game_id`, `seed` (returned on start; may be included on other responses for convenience)
- `mode`, `difficulty_tier`
- `hint_policy`, optional `hint_budget_total`, optional `hint_budget_remaining`
- `jump_policy`, optional `jump_budget_total`, optional `jump_budget_remaining`
- `reveal_policy`, optional `reveal_budget_total`, optional `reveal_budget_remaining`
- `target_score`, `step_index`, `history_len`
- `state`, optional `events`, optional `ai_hint`

---

## Data Shapes

### State
```json
{
  "hand": ["AS", "KD", "7H", "7C", "3S", "9D", "JH"],
  "p_remaining": 4,
  "d_remaining": 10,
  "score_total": 0,
  "deck_remaining_count": 45
}
```

Note: During gameplay, draw order MUST NOT be exposed. Remaining deck composition may be exposed only when allowed by the server’s reveal policy.
- When composition is exposed, the server SHOULD prefer a canonical counts map `deck_remaining_counts` (stable for regression/replay), and MAY also provide `deck_remaining` as an unordered array for UI convenience.
- When composition is not exposed, the server MUST omit `deck_remaining` / `deck_remaining_counts`.
- `reveal_policy` governs what the client can see; it does not restrict server-side heuristic computation (e.g., `ai_hint`).

### Event
```json
{
  "type": "info",
  "message_key": "game.started",
  "params": { "seed": 123456 }
}
```

### Error Response (recommended)
```json
{
  "error": {
    "code": "INVALID_ACTION",
    "message_key": "error.invalid_action",
    "params": { "reason": "play_requires_five" }
  }
}
```

---

## Endpoints

## POST /game/start

Start a new game.

### Request
- `seed` is optional:
  - if provided: start exactly that seed
  - if omitted: server samples a seed from the pool for `(mode, difficulty_tier)`
  - Seed pools are emitted offline as `seed_manifest.json` (grouped by tier and separated by mode),
  and are the sole runtime source for random seed selection.


```json
{
  "mode": "practice",
  "difficulty_tier": "medium",
  "seed": 123456,
  "hint_request": { "enabled": true },
  "jump_request": { "enabled": true }
}
```

### Response (example)
```json
{
  "game_id": "local-dev",
  "seed": 123456,
  "mode": "practice",
  "difficulty_tier": "medium",

  "hint_policy": "limited",
  "hint_budget_total": 2,
  "hint_budget_remaining": 2,

  "jump_policy": "unlimited",

  "target_score": null,
  "step_index": 0,
  "history_len": 0,

  "state": {
    "hand": ["AS", "KD", "7H", "7C", "3S", "9D", "JH"],
    "p_remaining": 4,
    "d_remaining": 10,
    "score_total": 0,
    "deck_remaining_count": 45
  },
  "events": [
    { "type": "info", "message_key": "game.started", "params": { "seed": 123456 } }
  ]
}
```

---

## POST /game/step

Apply one action.

### Game end: plays exhausted (`p_remaining == 0`)
- The game ends normally when `state.p_remaining == 0` (valid terminal state; not an error).
- When the game is ended, `POST /game/step` MUST NOT apply a forward action and MUST NOT mutate state/history.

#### Mode-specific exceptions (e.g., undo/jump)
- Some modes (e.g., `practice`, `challenge`) MAY support explicit "time travel" operations (such as undo/jump)
  that revert the game to a previous non-terminal state.
- If such an operation reverts to a state where `p_remaining > 0`, the game is considered in progress again
  and `POST /game/step` may proceed normally from that reverted state.
- Terminal state only blocks forward progression; it does not forbid reverting to earlier states when the mode allows it.

### Action: PLAY
Rules:
- must select **exactly 5** indices
- indices must be unique and within `[0, len(hand)-1]`

### Action: DISCARD
Rules:
- must select `n` indices where `1 <= n <= min(len(hand), d_remaining)`
- indices must be unique and within bounds

### Request (PLAY)
```json
{
  "game_id": "local-dev",
  "action": {
    "type": "PLAY",
    "selected_indices": [0, 1, 2, 3, 4]
  }
}
```

### Request (DISCARD)
```json
{
  "game_id": "local-dev",
  "action": {
    "type": "DISCARD",
    "selected_indices": [2, 5]
  }
}
```

### Response (example, with hint)
```json
{
  "game_id": "local-dev",
  "seed": 123456,
  "mode": "practice",
  "difficulty_tier": "medium",

  "hint_policy": "limited",
  "hint_budget_total": 2,
  "hint_budget_remaining": 1,

  "jump_policy": "unlimited",

  "target_score": null,
  "step_index": 1,
  "history_len": 1,

  "state": {
    "hand": ["2C", "QS", "7D", "AC", "5H", "9S", "KH"],
    "p_remaining": 3,
    "d_remaining": 10,
    "score_total": 120,
    "deck_remaining_count": 40
  },
  "events": [
    {
      "type": "score",
      "message_key": "play.scored",
      "params": { "category": "TWO_PAIR", "points": 120 }
    }
  ],
  "ai_hint": {
    "recommended_action": {
      "type": "DISCARD",
      "selected_indices": [1, 4]
    },
    "explanation_key": "ai.reason.heuristic",
    "params": {"rule": "prefer_made_hand_or_draw", "detail": "discard low-synergy cards" }
  }
}
```

Notes:
- Both `practice` and `challenge` may include `ai_hint`, depending on `hint_policy`.
- If `hint_policy = off`, the server MUST omit `ai_hint` (or return `"ai_hint": null`).
- If `hint_policy = limited`, returning an `ai_hint` MUST decrement `hint_budget_remaining`.

---

## POST /game/jump

Jump to an earlier step when `jump_policy` allows it. Implemented via deterministic replay.

- If `jump_policy = off`: server returns an error (e.g., `error.jump_not_allowed`).
- If `jump_policy = limited`: server decrements `jump_budget_remaining` per jump.
- `step_index` may be any value in `[0, history_len]`.
- If the client applies a new action after jumping back, the server MUST truncate any future history (no branching timelines).
- Budgets (`hint_budget_*`, `jump_budget_*`) are session-level and are NOT refunded by jumping.

### Request
```json
{
  "game_id": "local-dev",
  "step_index": 0
}
```

### Response
```json
{
  "game_id": "local-dev",
  "seed": 123456,
  "mode": "practice",
  "difficulty_tier": "medium",

  "hint_policy": "limited",
  "hint_budget_total": 2,
  "hint_budget_remaining": 1,

  "jump_policy": "unlimited",

  "target_score": null,
  "step_index": 0,
  "history_len": 8,

  "state": {
    "hand": ["AS", "KD", "7H", "7C", "3S", "9D", "JH"],
    "p_remaining": 4,
    "d_remaining": 10,
    "score_total": 0,
    "deck_remaining_count": 45
  },
  "events": [
    { "type": "info", "message_key": "game.jumped", "params": { "step_index": 0 } }
  ]
}
```

---

## GET /game/{game_id}/ai_trace

Return the heuristic AI trace for this game seed (order-unknown information set; remaining deck count and remaining deck composition are known to the heuristic policy, unordered; draw order unknown).
- In `practice`: can be available anytime.
- In `challenge`: reveal optionally only after completion.

Important:
- `ai_trace` is heuristic-only and WILL use remaining deck count and remaining deck composition (unordered).
- `ai_trace` MUST NOT depend on draw order.
- Reveal timing is mode-dependent (practice anytime; challenge after completion).

### Offline Trace Artifacts
Public trace artifacts are generated offline (after calibration) under order-unknown constraints (no draw order; remaining deck composition is known to the heuristic policy, unordered).


Recommended public trace schema (JSON):
```json
{
  "seed": 123456,
  "policy": "heuristic_v1",
  "info_set": "order_unknown",
  "generated_at": "2026-01-11T12:00:00Z",
  "steps": [
    {
      "step_index": 0,
      "recommended_action": { "type": "DISCARD", "selected_indices": [2,5] },
      "explanation_key": "ai.reason.heuristic",
      "params": { "rule": "prefer_made_hand_or_draw" }
    }
  ]
}

```
Suggested storage:
- Per-run pipeline artifacts (git-ignored), e.g. artifacts/pipeline/<run_id>/...
- Trace artifacts may be stored alongside other pipeline outputs as needed for UI reveal.

### Runtime policy
- When enabled by `hint_policy`, live responses include a single-step `ai_hint` computed using public state and server-known remaining-deck information (remaining deck count and composition, unordered). `ai_hint` MUST NOT depend on draw order.
- ai_trace SHOULD be served from an offline-generated heuristic trace artifact when available.
- Any ai_trace served at runtime MUST NOT contain sensitive fields like deck_remaining or any representation of draw order.

### Response (example)
```json
{
  "game_id": "local-dev",
  "policy": "heuristic_v1",
  "steps": [
    {
      "step_index": 0,
      "recommended_action": {
        "type": "DISCARD",
        "selected_indices": [2, 5]
      },
      "explanation_key": "ai.reason.heuristic",
      "params": { "rule": "prefer_made_hand_or_draw" }
    }
  ]
}
```

---

## Message Keys (Examples)
- `game.started`
- `game.jumped`
- `game.ended`
- `error.invalid_action`
- `error.play_requires_five`
- `error.discard_budget_exceeded`
- `error.jump_not_allowed`
- `play.scored`
- `ai.reason.heuristic`
