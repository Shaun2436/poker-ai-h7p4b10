# 2.
# engine/cards.py


"""
Card utilities for the engine.

Cards are encoded in "RS" format:
- R = rank: '2'..'9', 'T', 'J', 'Q', 'K', 'A'
- S = suit: 'S', 'H', 'D', 'C'
Example: 'AS', 'TD', '7H'

Important:
- standard_deck_rs() must return a stable, deterministic ordering every time.
"""


from __future__ import annotations
from typing import List, Tuple, Dict

# Public constants , useful for evaluator/scoring later
RANKS: Tuple[str,...] = ("2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A")
SUITS: Tuple[str,...] = ("S", "H", "D", "C") # order never changes

# useful rank mapping for evaluator later 
RANK_VALUE: Dict[str, int] = {r: i for i, r in enumerate(RANKS, start=2)}


def is_valid_card_rs(card: str) -> bool:
    """Return True if card is a valid RS string like 'AS' or '7H'."""
    if not isinstance(card, str) or len(card) != 2:   # must be str and len of 2
        return False
    r, s = card[0], card[1]    # r must in RANKS, s must in SUITS
    return (r in RANKS) and (s in SUITS)


def parse_card_rs(card: str) -> Tuple[str, str]:
    """
    Parse RS card string into (rank, suit).
    Raises ValueError for invalid cards.
    """
    if not is_valid_card_rs(card):
        raise ValueError(f"Invalid card RS: {card!r}")
    return card[0], card[1]


def standard_deck_rs() -> List[str]:
    """
    Return a standard 52-card deck in a fixed, deterministic order.

    Design choice:
    - rank-major order, then suit order (SUITS)
    - e.g. 2S, 2H, 2D, 2C, 3S, 3H, ... AS, AH, AD, AC
    """
    return [r + s for r in RANKS for s in SUITS]


def card_sort_key(card: str) -> Tuple[int, int]:
    """
    A stable sort key for RS cards by (rank_value, suit_index).
    Useful if UI wants sorted display without losing stable logic.
    """
    r, s = parse_card_rs(card)
    return (RANK_VALUE[r], SUITS.index(s))