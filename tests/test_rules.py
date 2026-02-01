# tests/test_rules.py

"""Tests for engine.rules (state transitions).

These tests are intentionally specific about:
- which cards are removed (by position indices)
- how draws happen (front of internal deck, deterministic)
- how budgets/score update
"""

from engine.actions import Action, PLAY, DISCARD
from engine.rules import apply_action
from engine.state import GameState, INITIAL_HAND_SIZE


def test_play_transition_updates_state_and_draws_in_order():
    """
    PLAY:
    - consumes exactly 1 play
    - scores exactly the chosen 5 cards (not best-of-7)
    - removes those 5 cards from the hand (by index), keeps the other 2 in order
    - draws 5 cards from the *front* of the internal deck to refill back to 7
    """
    s0 = GameState.from_seed(123)

    # Choose the first 5 cards by position.
    action = Action(type=PLAY, selected_indices=(0, 1, 2, 3, 4))

    expected_kept = [s0.hand[5], s0.hand[6]]
    expected_drawn = s0.deck[:5]
    expected_hand = expected_kept + expected_drawn

    s1, events = apply_action(s0, action)

    assert s1.p_remaining == s0.p_remaining - 1
    assert s1.d_remaining == s0.d_remaining  # play does not consume discard budget
    assert s1.hand == expected_hand
    assert s1.deck == s0.deck[5:]
    assert len(s1.hand) == INITIAL_HAND_SIZE
    assert len(events) == 1
    assert events[0]["type"] == "PLAY"
    assert events[0]["drawn"] == expected_drawn


def test_discard_transition_updates_state_and_draws_in_order():
    """
    DISCARD:
    - consumes discard budget equal to number of discarded cards
    - removes those cards (by index), keeps the others in order
    - draws the same number of cards from the *front* of the internal deck
    """
    s0 = GameState.from_seed(999)

    # Discard 2nd and 4th cards by position (0-based indices).
    action = Action(type=DISCARD, selected_indices=(1, 3))

    expected_kept = [c for i, c in enumerate(s0.hand) if i not in {1, 3}]
    expected_drawn = s0.deck[:2]
    expected_hand = expected_kept + expected_drawn

    s1, events = apply_action(s0, action)

    assert s1.p_remaining == s0.p_remaining  # discard does not consume plays
    assert s1.d_remaining == s0.d_remaining - 2
    assert s1.score_total == s0.score_total  # discard does not add score
    assert s1.hand == expected_hand
    assert s1.deck == s0.deck[2:]
    assert len(s1.hand) == INITIAL_HAND_SIZE
    assert len(events) == 1
    assert events[0]["type"] == "DISCARD"
    assert events[0]["drawn"] == expected_drawn


def test_apply_action_rejects_invalid_budget_via_validate_action():
    """
    apply_action() must reuse validate_action() rules.

    If p_remaining is 0, PLAY should raise ValueError("No plays remaining").
    """
    s0 = GameState.from_seed(1)
    s0.p_remaining = 0  # mutate for test; GameState is not frozen in this repo

    action = Action(type=PLAY, selected_indices=(0, 1, 2, 3, 4))

    try:
        apply_action(s0, action)
        assert False, "Expected ValueError for no plays remaining"
    except ValueError as e:
        assert str(e) == "No plays remaining"


def test_apply_action_is_deterministic_for_same_seed_and_action():
    """
    Determinism property:
    same seed + same action => identical next_state (hand/deck/budgets/score).
    """
    a = Action(type=DISCARD, selected_indices=(0,))

    s0a = GameState.from_seed(42)
    s0b = GameState.from_seed(42)

    s1a, _ = apply_action(s0a, a)
    s1b, _ = apply_action(s0b, a)

    assert s1a.hand == s1b.hand
    assert s1a.deck == s1b.deck
    assert s1a.p_remaining == s1b.p_remaining
    assert s1a.d_remaining == s1b.d_remaining
    assert s1a.score_total == s1b.score_total
