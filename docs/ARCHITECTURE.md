# Architecture Notes

## Design Goals
- Deterministic engine (seed + actions => exact replay)
- Separation of concerns (engine vs AI vs API vs UI)
- Testability (unit tests for evaluator, validation, determinism)
- No duplicated rules across languages

## Layers

### Engine (`engine/`)
- Owns game rules and state transitions
- Accepts structured actions
- Returns structured events (message_key + params)
- Never returns UI sentences

### AI (`ai/`)
- Calls engine to simulate outcomes
- Produces recommendations (action + explanation key)

### API (`api/`)
- Translates HTTP requests into engine actions
- Validates and executes transitions
- Returns state + events + optional AI hint
- Does not implement game logic

### Web (`web/`)
- Renders current state and events
- Collects user input (card selection)
- Sends actions to API
- Never computes scores or validates rules
