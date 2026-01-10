# API Contract (Draft)

This file defines the **exact JSON shapes** exchanged between the Web UI (client) and the Python API (server).

Rule of thumb:
- For each endpoint, always include **Request** and **Response** examples.
- Do **not** mix multiple endpoints in the same JSON block.
- Keep text minimal; the important part is the JSON.

---

## Conventions

### Card Encoding
Cards are encoded as strings using `RS` format:
- `R` rank: `2–9`, `T`, `J`, `Q`, `K`, `A`
- `S` suit: `S`, `H`, `D`, `C`

Examples: `AS`, `TD`, `7H`

### Event Format
All API responses may include an `events` array.
Each event uses a message key and parameters (no hard-coded UI sentences).

Example event:
```json
{
  "type": "info",
  "message_key": "game.started",
  "params": { "seed": 123456 }
}
```

---

## POST /game/start

### Request
```json
{
  "seed": 123456
}
```

### Response (example)
```json
{
  "game_id": "local-dev",
  "state": {
    "hand": ["AS", "KD", "7H", "7C", "3S", "9D", "JH"],
    "p_remaining": 4,
    "d_remaining": 10,
    "score_total": 0,
    "deck_remaining_count": 45
  },
  "events": [
    {
      "type": "info",
      "message_key": "game.started",
      "params": { "seed": 123456 }
    }
  ]
}
```

---

## POST /game/step

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

### Response (example)
```json
{
  "state": {
    "hand": ["2C", "QS", "7D", "AC", "5H", "9S", "KH"],
    "p_remaining": 3,
    "d_remaining": 8,
    "score_total": 120,
    "deck_remaining_count": 43
  },
  "events": [
    {
      "type": "score",
      "message_key": "play.scored",
      "params": {
        "category": "TWO_PAIR",
        "points": 120
      }
    }
  ],
  "ai_hint": {
    "recommended_action": {
      "type": "DISCARD",
      "selected_indices": [1, 4]
    },
    "explanation_key": "ai.reason.sampled_ev",
    "params": {
      "samples": 2000,
      "estimated_ev": 153.2
    }
  }
}
```

---

## Message Keys (Examples)

- `game.started`
- `error.invalid_action`
- `error.play_requires_five`
- `error.discard_budget_exceeded`
- `play.scored`
- `ai.reason.sampled_ev`
