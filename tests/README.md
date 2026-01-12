# Tests
Unit tests will be added here (evaluator, determinism, validation).

Additional test guidance:
- API behavior tests must assert that live gameplay responses do not contain sensitive fields such as `deck_remaining` and only include `deck_remaining_count`.
- Offline calibration tests should validate generated artifacts (trace JSON schema, estimated EV values, and that generators can run reproducibly for a given seed).
- When adding tests that rely on precomputed traces, keep traces as test fixtures under `tests/fixtures/` rather than generating calibration artifacts at runtime.
- Public precomputed traces used for runtime MUST include `"info_set": "unknown_deck"` to indicate they were generated without access to deck composition.
