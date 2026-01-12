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

### Deck Information (FINAL)
The full deck order is determined by `seed` and is kept server-side to support deterministic replay.

Visibility (gameplay):
- The **server** stores the full deck order (or equivalent RNG state + draw pointer).
- During live gameplay (both `practice` and `challenge`) the **player and in-game decision AI** do **not** see the deck composition or draw order. They only receive `state.deck_remaining_count` and other public state fields.

API requirements (gameplay):
- The API **MUST** include `state.deck_remaining_count` in gameplay responses.
- The API **MUST NOT** include `state.deck_remaining` in normal gameplay responses.

Offline calibration:
- For offline **difficulty calibration** (seed bucketing), a dedicated calibration step may examine the full deck composition (unordered) for each seed for the sole purpose of assigning difficulty tiers and computing `target_score`. These calibration runs are separate from normal gameplay and from public trace generation; their outputs (tier files, target scores) are consumed by the server to seed challenge pools.

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

Note: During normal gameplay the API MUST NOT include `deck_remaining`. For offline diagnostic or calibration exports, an offline tool may export the full remaining deck as either an unordered array `deck_remaining` (e.g., `["2C", "AH", ...]`) or a counts map `deck_remaining_counts` (e.g., `{ "2C": 1, "AH": 1, "...": 0 }`). These offline exports are not part of normal game responses.

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
    "explanation_key": "ai.reason.sampled_ev",
    "params": { "samples": 2000, "estimated_ev": 153.2 }
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

Return the Policy AI trace for this game seed (no draw-order knowledge during gameplay).
- In `practice`: can be available anytime.
- In `challenge`: reveal only after completion.

Note: AI traces used strictly for offline calibration/bucketing may be generated using full deck composition for seed evaluation; these calibration-only traces are separate from public precomputed traces intended for runtime (which MUST be generated under unknown-deck constraints).

### Offline Trace Artifacts (two kinds)
For offline activities we distinguish two kinds of artifacts:

1) Calibration-only artifacts (used for seed bucketing and target computation)
- These artifacts may be generated with access to the full deck composition for the purpose of assigning difficulty tiers and computing `target_score` for seeds. Store calibration artifacts under `out/calibration/` and treat them as sensitive; they are not part of the live API.

2) Public precomputed AI traces (used for runtime hints/traces)
- These artifacts MUST be generated under the **unknown-deck** constraint (i.e., the AI used to generate them must not have access to the deck composition or draw order). They are intended to be safe for runtime use and may be stored under `out/traces/public/`.

Recommended public precomputed trace schema (JSON):
```json
{
  "seed": 123456,
  "policy": "ev_rollout_v1",
  "info_set": "unknown_deck",        // required for public traces
  "generated_at": "2026-01-11T12:00:00Z",
  "steps": [
    {
      "step_index": 0,
      "recommended_action": { "type": "DISCARD", "selected_indices": [2,5] },
      "explanation_key": "ai.reason.sampled_ev",
      "params": { "samples": 2000, "estimated_ev": 153.2 }
    }
  ]
}
```
Storage and access:
- Suggested storage path for public traces: `out/traces/public/<policy>/<seed>.json` (project `out/` is git-ignored).
- Public precomputed traces MUST NOT include privileged/sensitive deck composition fields.

Suggested usage:
- Calibration-only artifacts (in `out/calibration/`) are used to compute seed tiers and `target_score` and may be generated with access to deck composition.
- Public precomputed traces (in `out/traces/public/`) MUST be generated under unknown-deck constraints and may be read by the server at runtime to serve `ai_hint`/`ai_trace` payloads without revealing deck composition.

Testing notes:
- There should be tests that assert live API endpoints do not include `deck_remaining` and that public precomputed traces include `"info_set": "unknown_deck"`.

### Runtime policy
During live gameplay the server SHOULD NOT compute a full `ai_trace` on-demand. Instead it must follow this runtime policy:

- Live responses MAY include a single-step `ai_hint` computed using only public state (`hand`, `p_remaining`, `d_remaining`, `deck_remaining_count`) and any server-side policies.
- The server SHOULD NOT perform an on-demand full-sequence rollout to produce an `ai_trace` for a live request; if a trace is required for UI purposes it SHOULD be served from a precomputed public `ai_trace` artifact generated offline under the **unknown-deck** constraint (the artifact MUST include `"info_set": "unknown_deck"`).
- Any `ai_trace` served at runtime MUST NOT contain sensitive fields like `deck_remaining` or any representation of draw order.

Note: Calibration artifacts generated with access to known-deck composition remain separate and must never be exposed to live gameplay clients.

### Response (example)
```json
{
  "game_id": "local-dev",
  "policy": "ev_rollout_v1",
  "steps": [
    {
      "step_index": 0,
      "recommended_action": {
        "type": "DISCARD",
        "selected_indices": [2, 5]
      },
      "explanation_key": "ai.reason.sampled_ev",
      "params": { "samples": 2000, "estimated_ev": 153.2 }
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
- `ai.reason.sampled_ev`
