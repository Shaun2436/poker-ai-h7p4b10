# tests/test_state_init.py

import random
from collections import Counter

from engine.state import GameState, INITIAL_HAND_SIZE, INITIAL_P, INITIAL_D
from engine.cards import standard_deck_rs


def test_game_state_initialization_counts():
    """
    Verifies that a newly initialized GameState has correct initial sizes and counters:
    - hand size equals INITIAL_HAND_SIZE
    - remaining deck size is 52 - INITIAL_HAND_SIZE
    - public deck count matches internal deck size
    - play count (P), discard budget (D), and score start at defined defaults
    """
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
    """
    Ensures determinism of GameState initialization:
    creating two states with the same seed must produce identical
    internal state (hand, deck, counters, score) and identical
    public representations.
    """
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


def test_public_state_shape():
    """
    Locks the exact shape of the public state dictionary.
    This test will fail if public API fields are added, removed,
    or renamed, making API changes explicit and intentional.
    """
    state = GameState.from_seed(1)
    pub = state.to_public_dict()

    assert set(pub.keys()) == {
        "hand",
        "deck_remaining_count",
        "p_remaining",
        "d_remaining",
        "score_total",
        "deck_remaining_counts",
        "deck_remaining",
    }


def test_public_state_includes_unordered_deck_composition():
    """
    Remaining deck composition is always public:
    - includes deck_remaining_counts (unordered map; key order not a contract)
    - includes deck_remaining (canonical order, not draw order)
    - never includes internal draw-order deck field ("deck")
    """
    state = GameState.from_seed(123)
    pub = state.to_public_dict()

    # should include composition fields
    assert "deck_remaining_counts" in pub
    assert "deck_remaining" in pub

    # should still NOT include internal draw-order deck
    assert "deck" not in pub

    # counts should match internal deck multiset (order-independent equality)
    counts = pub["deck_remaining_counts"]
    assert sum(counts.values()) == len(state.deck)
    assert counts == dict(Counter(state.deck))

    # deck_remaining should include exactly the remaining multiset, in canonical order
    remaining_list = pub["deck_remaining"]
    assert len(remaining_list) == len(state.deck)
    assert Counter(remaining_list) == Counter(state.deck)

    # and it should be canonical order: same as iterating standard_deck_rs and expanding counts
    expected_remaining: list[str] = []
    remaining_counter = Counter(state.deck)
    for card in standard_deck_rs():
        expected_remaining.extend([card] * remaining_counter.get(card, 0))
    assert remaining_list == expected_remaining


def test_public_determinism_with_deck_composition():
    """
    Public output must be deterministic for the same seed.
    """
    s1 = GameState.from_seed(555)
    s2 = GameState.from_seed(555)

    assert s1.to_public_dict() == s2.to_public_dict()


def test_public_state_does_not_leak_draw_order():
    """
    Verifies that deck_remaining (the array) is returned in canonical deck order,
    not the internal draw order.

    Two states with the same remaining multiset but different internal deck order
    should produce identical deck_remaining output.
    """
    state = GameState.from_seed(999)
    original_remaining = state.deck[:]  # same multiset

    # Mutate internal deck order to simulate a different draw sequence
    rng = random.Random(111)
    rng.shuffle(state.deck)

    pub = state.to_public_dict()

    # Expected canonical expansion from the ORIGINAL multiset
    expected_remaining: list[str] = []
    remaining_counter = Counter(original_remaining)
    for card in standard_deck_rs():
        expected_remaining.extend([card] * remaining_counter.get(card, 0))

    assert pub["deck_remaining"] == expected_remaining
