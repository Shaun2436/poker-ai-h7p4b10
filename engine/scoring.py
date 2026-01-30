"""
Scoring policy.

This project intentionally separates scoring into TWO contexts:

1) gameplay:
   - This is the "real" scoring shown to the player.
   - Jackpot categories (e.g. STRAIGHT_FLUSH) are allowed and can award
     extremely large points to create a strong player experience.

2) model:
   - This is the simplified scoring universe used by calibration and AI.
   - Jackpot categories are collapsed / ignored to avoid polluting statistics
     and to keep heuristic decision-making stable and explainable.

Important boundary:
- engine.evaluator classifies hands into categories (facts).
- engine.scoring maps categories to points (policy).
"""

from __future__ import annotations

from typing import Dict, Iterable, Tuple

from engine.evaluator import (
    evaluate_5card_category,
    ALL_CATEGORIES,
    MODEL_CATEGORIES,
    normalize_model_category,
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

# Gameplay-only jackpot award.
# This value is intentionally extreme so that a straight flush feels like
# an instant-win / celebration event for the player.
JACKPOT_POINTS = 999_999


# ---------------------------------------------------------------------------
# Scoring tables
#
# These tables are the ONLY place that numeric points are defined.
# The evaluator must never contain points logic.
# ---------------------------------------------------------------------------

# Gameplay points:
# - Must cover exactly ALL_CATEGORIES (including jackpot categories).
# - HIGH_CARD must be > 0 (otherwise playing a high-card hand is equivalent
#   to wasting a play vs discarding, which harms gameplay incentives).
GAMEPLAY_POINTS: Dict[str, int] = {
    HIGH_CARD: 50,
    ONE_PAIR: 70,
    TWO_PAIR: 150,
    THREE_OF_A_KIND: 250,
    STRAIGHT: 300,
    FLUSH: 360,
    FULL_HOUSE: 440,
    FOUR_OF_A_KIND: 730,
    STRAIGHT_FLUSH: JACKPOT_POINTS,
}

# Model points:
# - Must cover exactly MODEL_CATEGORIES (jackpots excluded).
# - This table intentionally has NO STRAIGHT_FLUSH entry.
MODEL_POINTS: Dict[str, int] = {
    HIGH_CARD: 50,
    ONE_PAIR: 70,
    TWO_PAIR: 150,
    THREE_OF_A_KIND: 250,
    STRAIGHT: 300,
    FLUSH: 360,
    FULL_HOUSE: 440,
    FOUR_OF_A_KIND: 730,
}


def points_for_category_gameplay(category: str) -> int:
    """
    Look up gameplay points for a given category.

    This is the player-facing scoring universe:
    - Jackpot categories are valid here.
    - No normalization occurs: callers must provide a real gameplay category.

    Args:
        category: A category string from engine.evaluator.ALL_CATEGORIES.

    Returns:
        The integer point value for that category.

    Raises:
        ValueError: if category is not recognized (prevents silent bugs).
    """
    if category not in GAMEPLAY_POINTS:
        raise ValueError(f"Unknown gameplay category: {category!r}")
    return GAMEPLAY_POINTS[category]


def points_for_category_model(category: str) -> int:
    """
    Look up model-world points for a category.

    This is the calibration/AI scoring universe:
    - Jackpot categories are NOT modeled as separate outcomes.
    - Any jackpot category is collapsed into a normal model category using
      engine.evaluator.normalize_model_category().

    This function intentionally accepts either:
    - a raw gameplay category (e.g. STRAIGHT_FLUSH), or
    - an already-normalized model category (e.g. FLUSH)

    Args:
        category: A category string from engine.evaluator.ALL_CATEGORIES
                  or engine.evaluator.MODEL_CATEGORIES.

    Returns:
        The integer point value in the model world.

    Raises:
        ValueError: if the normalized category is not present in MODEL_POINTS.
    """
    cat = normalize_model_category(category)
    if cat not in MODEL_POINTS:
        raise ValueError(f"Unknown model category: {cat!r} (from {category!r})")
    return MODEL_POINTS[cat]


def score_5card_hand_gameplay(cards: Iterable[str]) -> Tuple[str, int]:
    """
    Score EXACTLY 5 cards in gameplay context.

    Steps:
    1) classify the hand via engine.evaluator.evaluate_5card_category()
    2) map category -> points via GAMEPLAY_POINTS

    Args:
        cards: Iterable of exactly 5 RS-encoded cards (order does not matter).

    Returns:
        (raw_category, gameplay_points)

    Raises:
        ValueError: bubbled up from evaluator for invalid input (wrong count,
                    invalid RS card, duplicates), or from points lookup.
    """
    category = evaluate_5card_category(cards)
    return category, points_for_category_gameplay(category)


def score_5card_hand_model(cards: Iterable[str]) -> Tuple[str, int]:
    """
    Score EXACTLY 5 cards in model context (calibration/AI).

    Key difference from gameplay:
    - The returned category is normalized to the model world.
    - Jackpot categories are collapsed (e.g. STRAIGHT_FLUSH -> FLUSH).

    Args:
        cards: Iterable of exactly 5 RS-encoded cards (order does not matter).

    Returns:
        (normalized_model_category, model_points)

    Raises:
        ValueError: bubbled up from evaluator or points lookup.
    """
    raw = evaluate_5card_category(cards)

    # Normalize for the category we return to the caller (AI/calibration view).
    category = normalize_model_category(raw)

    # Compute points in the model world. Passing raw is allowed because
    # points_for_category_model() also normalizes internally.
    points = points_for_category_model(raw)

    return category, points


def validate_scoring_tables() -> None:
    """
    Validate scoring tables against evaluator category definitions.

    This is a development-time safety check:
    - If evaluator categories change, scoring must be updated explicitly.
    - Prevents "forgot to add points for new category" type errors.

    Raises:
        ValueError: if scoring tables are inconsistent with evaluator categories
                    or violate required invariants (e.g. HIGH_CARD > 0).
    """
    # Gameplay must cover exactly what evaluator can output.
    if set(GAMEPLAY_POINTS.keys()) != set(ALL_CATEGORIES):
        raise ValueError("GAMEPLAY_POINTS must cover exactly ALL_CATEGORIES")

    # Model points must cover exactly the model-visible category universe.
    if set(MODEL_POINTS.keys()) != set(MODEL_CATEGORIES):
        raise ValueError("MODEL_POINTS must cover exactly MODEL_CATEGORIES")

    # Gameplay invariant: high card must still reward something.
    if GAMEPLAY_POINTS[HIGH_CARD] <= 0:
        raise ValueError("HIGH_CARD gameplay points must be > 0")
