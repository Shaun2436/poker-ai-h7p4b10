# tests/test_cards.py

import pytest
from engine.cards import standard_deck_rs, is_valid_card_rs, parse_card_rs


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

