# tests/test_evaluator.py
"""
Unit tests for engine.evaluator.

Goals:
- Verify correct classification of ALL 5-card poker hand categories.
- Ensure evaluator is order-invariant and deterministic.
- Ensure invalid inputs are rejected explicitly.
- Confirm evaluator does NOT perform scoring, ranking, or best-of-7 logic.
"""

import pytest

from engine.evaluator import (
    evaluate_5card_category,
    HIGH_CARD,
    ONE_PAIR,
    TWO_PAIR,
    THREE_OF_A_KIND,
    STRAIGHT,
    FLUSH,
    FULL_HOUSE,
    FOUR_OF_A_KIND,
    STRAIGHT_FLUSH,
)


def test_high_card():
    """
    No matching ranks, no straight, no flush.

    This locks the baseline category when nothing else applies.
    """
    hand = ["AS", "KD", "7H", "4C", "2D"]
    assert evaluate_5card_category(hand) == HIGH_CARD


def test_one_pair():
    """
    Exactly one pair of equal ranks.

    Confirms evaluator detects a single duplicated rank.
    """
    hand = ["AS", "AD", "7H", "4C", "2D"]
    assert evaluate_5card_category(hand) == ONE_PAIR


def test_two_pair():
    """
    Two distinct pairs plus one unrelated card.

    Order of cards must not matter.
    """
    hand = ["AS", "AD", "7H", "7C", "2D"]
    assert evaluate_5card_category(hand) == TWO_PAIR


def test_three_of_a_kind():
    """
    Three cards of the same rank and two kickers.

    Confirms this is NOT misclassified as full house.
    """
    hand = ["AS", "AD", "AC", "7C", "2D"]
    assert evaluate_5card_category(hand) == THREE_OF_A_KIND


def test_straight_normal():
    """
    Five consecutive ranks, mixed suits.

    Verifies normal straight detection (non-flush).
    """
    hand = ["9S", "TD", "JH", "QC", "KS"]  # 9-T-J-Q-K
    assert evaluate_5card_category(hand) == STRAIGHT


def test_straight_wheel_ace_low():
    """
    Ace-low straight (A-2-3-4-5).

    Locks the special-case rule where Ace counts as low.
    """
    hand = ["AS", "2D", "3H", "4C", "5S"]
    assert evaluate_5card_category(hand) == STRAIGHT


def test_flush_not_straight():
    """
    All cards same suit, but ranks are not consecutive.

    Confirms flush does NOT require a straight.
    """
    hand = ["AS", "9S", "7S", "4S", "2S"]
    assert evaluate_5card_category(hand) == FLUSH


def test_full_house():
    """
    Three cards of one rank and two cards of another rank.

    Confirms correct classification over three-of-a-kind.
    """
    hand = ["AS", "AD", "AC", "7H", "7C"]
    assert evaluate_5card_category(hand) == FULL_HOUSE


def test_four_of_a_kind():
    """
    Four cards of the same rank.

    Confirms highest rank-count category (excluding straight flush).
    """
    hand = ["AS", "AD", "AH", "AC", "2D"]
    assert evaluate_5card_category(hand) == FOUR_OF_A_KIND


def test_straight_flush_includes_royal_as_straight_flush():
    """
    Straight flush including the 'royal flush' case.

    Project rule: royal flush is NOT a separate category.
    """
    hand = ["TS", "JS", "QS", "KS", "AS"]
    assert evaluate_5card_category(hand) == STRAIGHT_FLUSH


def test_order_invariant():
    """
    Card order must not affect evaluation.

    Same hand in different order must yield identical category.
    """
    hand1 = ["AS", "AD", "7H", "7C", "2D"]
    hand2 = ["7C", "2D", "AS", "7H", "AD"]
    assert evaluate_5card_category(hand1) == evaluate_5card_category(hand2) == TWO_PAIR


def test_rejects_non_five_cards():
    """
    Evaluator must require EXACTLY five cards.

    It must not silently accept 4 or 6 cards.
    """
    with pytest.raises(ValueError):
        evaluate_5card_category(["AS", "KD", "7H", "4C"])
        
    with pytest.raises(ValueError):
        evaluate_5card_category(["AS", "KD", "7H", "4C", "2D", "3S"])


def test_rejects_invalid_rs():
    """
    Invalid RS strings must be rejected.

    Ensures engine.cards remains the single source of truth for card encoding.
    """
    with pytest.raises(ValueError):
        evaluate_5card_category(["AS", "KD", "7H", "4C", "10S"])


def test_rejects_duplicate_exact_cards():
    """
    Exact duplicate cards are impossible in a real deck.

    Evaluator must reject such input instead of producing nonsense.
    """
    with pytest.raises(ValueError):
        evaluate_5card_category(["AS", "AS", "7H", "4C", "2D"])


def test_straight_flush_beats_flush_and_straight():
    """
    Straight+Flush must be classified as STRAIGHT_FLUSH, not STRAIGHT or FLUSH.

    This locks the category priority ordering.
    """
    hand = ["9S", "TS", "JS", "QS", "KS"]
    assert evaluate_5card_category(hand) == STRAIGHT_FLUSH


def test_best_of_7_is_not_performed():
    """
    Evaluator must NOT pick the best 5 out of 7.

    We feed 7 cards as a single iterable, which must be rejected.
    """
    with pytest.raises(ValueError):
        evaluate_5card_category(["AS", "KS", "QS", "JS", "TS", "2D", "3H"])


def test_no_kicker_ranking_high_card_is_still_high_card():
    """
    Evaluator returns ONLY the category, not tie-break strength.

    Two different high-card hands must both be HIGH_CARD.
    """
    hand1 = ["AS", "KD", "7H", "4C", "2D"]
    hand2 = ["KS", "QD", "9H", "4D", "2C"]
    assert evaluate_5card_category(hand1) == HIGH_CARD
    assert evaluate_5card_category(hand2) == HIGH_CARD
