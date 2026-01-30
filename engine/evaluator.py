# 3.
# engine/evaluator.py
"""
Texas Hold'em 5-card hand category evaluator.

Contract (project-specific):
- Input: exactly 5 cards in RS format (e.g., "AS", "7H").
- Output: category string ONLY (no kicker ranking / tie-break).
  Scoring depends ONLY on category. 
- Deterministic and order-invariant.

Categories:
- HIGH_CARD
- ONE_PAIR
- TWO_PAIR
- THREE_OF_A_KIND
- STRAIGHT           (includes wheel A-2-3-4-5)
- FLUSH
- FULL_HOUSE
- FOUR_OF_A_KIND
- STRAIGHT_FLUSH     (includes "royal flush" as straight flush)
"""

from __future__ import annotations

from collections import Counter
from typing import Iterable, List

from engine.cards import is_valid_card_rs, parse_card_rs, RANK_VALUE


# Public category constants (useful for scoring mapping later)
HIGH_CARD = "HIGH_CARD"
ONE_PAIR = "ONE_PAIR"
TWO_PAIR = "TWO_PAIR"
THREE_OF_A_KIND = "THREE_OF_A_KIND"
STRAIGHT = "STRAIGHT"
FLUSH = "FLUSH"
FULL_HOUSE = "FULL_HOUSE"
FOUR_OF_A_KIND = "FOUR_OF_A_KIND"
STRAIGHT_FLUSH = "STRAIGHT_FLUSH"

ALL_CATEGORIES = (
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


def evaluate_5card_category(cards: Iterable[str]) -> str:
    """
    Classify a 5-card poker hand into a category.

    This function evaluates EXACTLY 5 cards and returns ONLY the category name.
    It does NOT compute points, and it does NOT perform "best 5 out of 7" selection.

    Args:
        cards: An iterable of 5 RS-encoded cards (e.g., ["AS","KD","7H","4C","2D"]).

    Returns:
        A category string from ALL_CATEGORIES.

    Raises:
        ValueError:
            - if the input does not contain exactly 5 cards
            - if any card is not a valid RS string
            - if any exact card appears more than once
    """
    card_list: List[str] = list(cards)

    if len(card_list) != 5:
        raise ValueError(f"Expected exactly 5 cards, got {len(card_list)}")

    # Validate RS encoding (engine.cards is the single source of truth for RS format)
    for c in card_list:
        if not is_valid_card_rs(c):
            raise ValueError(f"Invalid card RS: {c!r}")

    # Reject duplicates (a real deck cannot contain identical cards)
    if len(set(card_list)) != 5:
        raise ValueError(f"Duplicate cards detected: {card_list!r}")

    ranks: List[int] = []
    suits: List[str] = []
    for c in card_list:
        r_char, s_char = parse_card_rs(c)
        ranks.append(RANK_VALUE[r_char])
        suits.append(s_char)

    rank_counts = Counter(ranks)
    counts_sorted = sorted(rank_counts.values(), reverse=True)

    is_flush = len(set(suits)) == 1
    is_straight = _is_straight_5(ranks)

    # Highest categories first (no kicker needed, only category)
    if is_straight and is_flush:
        return STRAIGHT_FLUSH

    if counts_sorted == [4, 1]:
        return FOUR_OF_A_KIND

    if counts_sorted == [3, 2]:
        return FULL_HOUSE

    if is_flush:
        return FLUSH

    if is_straight:
        return STRAIGHT

    if counts_sorted == [3, 1, 1]:
        return THREE_OF_A_KIND

    if counts_sorted == [2, 2, 1]:
        return TWO_PAIR

    if counts_sorted == [2, 1, 1, 1]:
        return ONE_PAIR

    return HIGH_CARD


def _is_straight_5(rank_values: List[int]) -> bool:
    """
    Determine whether 5 ranks form a straight.

    Rules:
    - Must be 5 distinct ranks.
    - Normal straight: max(rank) - min(rank) == 4
    - Wheel straight: A-2-3-4-5, represented as [14,2,3,4,5]

    Args:
        rank_values: List of 5 rank numeric values (2..14), may contain duplicates.

    Returns:
        True if ranks form a straight, otherwise False.
    """
    unique = set(rank_values)
    if len(unique) != 5:
        return False

    sorted_vals = sorted(unique)

    # Wheel straight: A(14) + 2,3,4,5
    if sorted_vals == [2, 3, 4, 5, 14]:
        return True

    return sorted_vals[-1] - sorted_vals[0] == 4


# ---------------------------------------------------------------------------
# Jackpot / modeling helpers
#
# These definitions exist to explicitly separate:
#   - factual hand classification (what the hand IS),
#   - from system modeling (what the AI / calibration CARES about).
#
# Some extremely rare categories (e.g. STRAIGHT_FLUSH) are treated as
# "jackpot events" in gameplay, but are intentionally excluded from
# calibration and AI decision modeling to avoid statistical noise.
# ---------------------------------------------------------------------------


# Categories that exist in gameplay, but are excluded from calibration / AI modeling.
#
# A jackpot category:
# - is still a real, valid hand category
# - is recognized by the evaluator
# - but does NOT participate in difficulty calibration, EV estimation,
#   or heuristic decision logic
#
# Currently, STRAIGHT_FLUSH is the only jackpot category.
JACKPOT_CATEGORIES = (STRAIGHT_FLUSH,)


# Categories visible to the calibration / AI "model world".
#
# This represents the complete category universe as seen by:
# - calibration
# - AI heuristics
# - ai_trace / ai_hint
#
# Jackpot categories are intentionally removed to keep the model stable
# and focused on statistically meaningful outcomes.
MODEL_CATEGORIES = tuple(
    c for c in ALL_CATEGORIES if c not in JACKPOT_CATEGORIES
)


def is_jackpot_category(category: str) -> bool:
    """
    Check whether a category is treated as a jackpot in gameplay.

    This function provides a semantic check rather than a raw comparison,
    allowing gameplay logic to ask:
        "Should this category trigger special jackpot behavior?"

    It should be used by:
    - gameplay scoring
    - win-condition checks
    - UI / replay effects

    It should NOT be used by:
    - calibration
    - AI decision logic

    Args:
        category: A category string from ALL_CATEGORIES.

    Returns:
        True if the category is considered a jackpot event.
    """
    return category in JACKPOT_CATEGORIES


def normalize_model_category(category: str) -> str:
    """
    Normalize a gameplay category into its model-world equivalent.

    This function collapses jackpot-only categories into ordinary categories
    so they can be safely included in calibration and AI modeling.

    Design rationale:
    - STRAIGHT_FLUSH is both a straight and a flush.
    - In the model world (where jackpots do not exist), it is treated as FLUSH,
      which preserves hand strength ordering while avoiding a separate,
      ultra-rare category.

    This function is intended for:
    - calibration statistics
    - AI heuristics
    - ai_trace / ai_hint output

    It should NOT be used for gameplay scoring.

    Args:
        category: A category string from ALL_CATEGORIES.

    Returns:
        A category string that belongs to MODEL_CATEGORIES.
    """
    if category == STRAIGHT_FLUSH:
        return FLUSH
    return category
