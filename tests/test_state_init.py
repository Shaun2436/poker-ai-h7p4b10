# tests/test_state_init.py

from engine.state import GameState, INITIAL_HAND_SIZE, INITIAL_P, INITIAL_D


def test_game_state_initialization_counts():
    '''
    Verifies that a newly initialized GameState has correct initial sizes and counters:
    - hand size equals INITIAL_HAND_SIZE
    - remaining deck size is 52 - INITIAL_HAND_SIZE
    - public deck count matches internal deck size
    - play count (P), discard budget (D), and score start at defined defaults
    '''
    state = GameState.from_seed(123)

    # Internal facts
    assert len(state.hand) == INITIAL_HAND_SIZE
    assert len(state.deck) == 52 - INITIAL_HAND_SIZE

    # Public facts (API-safe)
    assert state.deck_remaining_count == 52 - INITIAL_HAND_SIZE

    assert state.p_remaining == INITIAL_P
    assert state.d_remaining == INITIAL_D
    assert state.score_total == 0


def test_game_initialization_determinism():
    '''
    Ensures determinism of GameState initialization:
    creating two states with the same seed must produce identical
    internal state (hand, deck, counters, score) and identical
    public representations.
    '''
    s1 = GameState.from_seed(999)
    s2 = GameState.from_seed(999)

    # Internal determinism
    assert s1.hand == s2.hand
    assert s1.deck == s2.deck
    assert s1.p_remaining == s2.p_remaining
    assert s1.d_remaining == s2.d_remaining
    assert s1.score_total == s2.score_total

    # Public determinism
    assert s1.to_public_dict() == s2.to_public_dict()


def test_public_state_does_not_leak_deck_composition():
    '''
    Ensures that the public-facing state representation does NOT
    expose the internal deck contents.
    Only the remaining deck count is allowed to be visible.
    '''
    state = GameState.from_seed(42)
    public_state = state.to_public_dict()

    assert "deck" not in public_state
    assert public_state["deck_remaining_count"] == 52 - INITIAL_HAND_SIZE


def test_public_state_shape():
    '''
    Locks the exact shape of the public state dictionary.
    This test will fail if public API fields are added, removed,
    or renamed, making API changes explicit and intentional.
    '''
    state = GameState.from_seed(1)
    pub = state.to_public_dict()
    assert set(pub.keys()) == {
        "hand","deck_remaining_count","p_remaining","d_remaining","score_total"
    }
