# tests/test_cards.py

import pytest
from engine.cards import standard_deck_rs, is_valid_card_rs, parse_card_rs, card_sort_key


def test_standard_deck_is_stable_and_complete():
    '''
    Verifies that the standard deck generator:
    - always returns the same ordering (deterministic)
    - contains exactly 52 cards
    - contains no duplicate cards
    '''
    d1 = standard_deck_rs()
    d2 = standard_deck_rs()
    assert d1 == d2
    assert len(d1) == 52
    assert len(set(d1)) == 52


def test_card_validation_and_parsing():
    '''
    Tests basic RS card validation and parsing:
    - valid cards are accepted
    - malformed or invalid cards are rejected
    - parsing returns the correct (rank, suit) tuple for valid cards
    '''
    assert is_valid_card_rs("AS")
    assert is_valid_card_rs("TD")
    assert not is_valid_card_rs("10S")
    assert not is_valid_card_rs("1Z")
    assert parse_card_rs("7H") == ("7", "H")


def test_parse_card_raises_on_invalid():
    '''
    Ensures parse_card_rs fails loudly on invalid input
    instead of silently returning incorrect data.
    '''
    with pytest.raises(ValueError):
        parse_card_rs("1Z")
    with pytest.raises(ValueError):
        parse_card_rs(123)
    with pytest.raises(ValueError):
        parse_card_rs(None)

def test_rank_and_suit_edges():
    '''
    # Tests boundary cases for ranks and suits:
    # verifies that the lowest rank ('2') and highest rank ('A'),
    # as well as different suits, are considered valid.
    '''
    assert is_valid_card_rs("2S")
    assert is_valid_card_rs("AC")


def test_is_valid_rejects_non_string():
    '''
    # Ensures non-string inputs are safely rejected by card validation,
    # protecting against accidental type misuse.
    '''
    assert not is_valid_card_rs(123)  # type: ignore[arg-type]
    assert not is_valid_card_rs(None) # type: ignore[arg-type]


def test_standard_deck_known_first_last():
    '''
    # Locks down the canonical ordering of the standard deck.
    # This prevents accidental changes to rank or suit ordering
    # from silently breaking determinism or replay logic.
    '''
    d = standard_deck_rs()
    assert d[0] == "2S"
    assert d[-1] == "AC"


def test_standard_deck_prefix_pattern():
    '''
    # Further locks down the canonical ordering beyond first/last.
    # This ensures the deck is rank-major, then suit order (S, H, D, C):
    # 2S, 2H, 2D, 2C, 3S, 3H, 3D, 3C, ...
    '''
    d = standard_deck_rs()
    assert d[:8] == ["2S", "2H", "2D", "2C", "3S", "3H", "3D", "3C"]


def test_validation_is_strict_about_case_and_whitespace():
    '''
    # Ensures validation is strict:
    # - lower-case ranks/suits are rejected
    # - leading/trailing whitespace is rejected
    # This prevents multiple representations of the same card leaking into logs/replay.
    '''
    assert not is_valid_card_rs("as")
    assert not is_valid_card_rs("7h")
    assert not is_valid_card_rs(" AS")
    assert not is_valid_card_rs("AS ")


def test_card_sort_key_matches_standard_deck_order():
    '''
    # Ensures card_sort_key ordering matches the engine's canonical deck ordering.
    # If UI sorts using this key, it should match standard_deck_rs() order.
    '''
    d = standard_deck_rs()
    assert sorted(d, key=card_sort_key) == d