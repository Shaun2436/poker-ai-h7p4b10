import pytest

from engine.scoring import (
    JACKPOT_POINTS,
    points_for_category_gameplay,
    points_for_category_model,
    score_5card_hand_gameplay,
    score_5card_hand_model,
    validate_scoring_tables,
)
from engine.evaluator import (
    HIGH_CARD, FLUSH, STRAIGHT_FLUSH,
    MODEL_CATEGORIES, ALL_CATEGORIES,
    normalize_model_category,
)

def test_tables_are_consistent_with_evaluator_groups():
    validate_scoring_tables()
    assert STRAIGHT_FLUSH in ALL_CATEGORIES
    assert STRAIGHT_FLUSH not in MODEL_CATEGORIES

def test_jackpot_points_in_gameplay():
    assert points_for_category_gameplay(STRAIGHT_FLUSH) == JACKPOT_POINTS

def test_straight_flush_collapses_in_model():
    assert normalize_model_category(STRAIGHT_FLUSH) == FLUSH
    assert points_for_category_model(STRAIGHT_FLUSH) == points_for_category_model(FLUSH)

def test_high_card_not_zero():
    assert points_for_category_gameplay(HIGH_CARD) > 0

def test_score_functions_return_expected_category_forms():
    sf = ["9S","TS","JS","QS","KS"]  # straight flush
    raw_cat, raw_pts = score_5card_hand_gameplay(sf)
    assert raw_cat == STRAIGHT_FLUSH
    assert raw_pts == JACKPOT_POINTS

    model_cat, model_pts = score_5card_hand_model(sf)
    assert model_cat == FLUSH
    assert model_pts == points_for_category_model(FLUSH)
