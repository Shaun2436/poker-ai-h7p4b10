# 7.
# engine/rng.py

"""
Seeded randomness helpers (engine-owned).

----------------------
The project has a strict determinism contract:

    same seed + same action_log  =>  identical final state / score

To make that contract easier to enforce and test, the engine should avoid using
the *global* random generator and instead construct explicit RNG instances
from a seed.

Important boundary notes
------------------------
- This module does NOT implement game rules, scoring, or replay.
- This module does NOT expose any hidden information to the UI. It only helps
  produce deterministic internal randomness.

Implementation choice
---------------------
We use Python's `random.Random(seed)`. For a given Python
runtime, it is deterministic for the same seed.
"""

from __future__ import annotations

import random
from typing import List, Sequence, TypeVar

from engine.cards import standard_deck_rs

T = TypeVar("T")


def _validate_seed(seed: int) -> None:
    """Validate that seed is a plain int (not bool).

    We reject other types to keep determinism reproducible 
    and avoid surprising implicit conversions.

    Raises:
        TypeError: If seed is not an int (or is a bool).
    """
    # Note: bool is a subclass of int in Python, 
    # but treating True/False asseeds is a bug.
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError(f"seed must be int (got {type(seed).__name__})")


def make_rng(seed: int) -> random.Random:
    """Create a new deterministic RNG for the given seed.

    Args:
        seed: Integer seed.

    Returns:
        A fresh `random.Random` instance seeded with `seed`.
    """
    _validate_seed(seed)
    return random.Random(seed)


def shuffled(items: Sequence[T], *, seed: int) -> List[T]:
    """Return a shuffled copy of `items` using a deterministic seed.

    This helper is intentionally *pure*:
    - It never mutates the input sequence.
    - It always returns a new list.

    Args:
        items: Any finite sequence (list/tuple/etc.).
        seed: Integer seed used to shuffle.

    Returns:
        A new list containing the same elements in shuffled order.
    """
    rng = make_rng(seed)
    out = list(items)
    rng.shuffle(out)
    return out


def shuffled_deck_rs(*, seed: int) -> List[str]:
    """Return the standard 52-card deck shuffled deterministically by seed.

    The deck starts from the canonical order returned by `standard_deck_rs()`,
    then is shuffled using `random.Random(seed).shuffle(...)`.

    Args:
        seed: Integer seed.

    Returns:
        A list of 52 RS card strings in draw order.
    """
    deck = standard_deck_rs()
    make_rng(seed).shuffle(deck)
    return deck
