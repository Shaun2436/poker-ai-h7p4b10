# tests/test_rng.py

"""Tests for engine.rng (seeded randomness helpers).

These tests exist to protect the determinism contract:

- same seed => same shuffle / same random stream
- different seeds => (almost always) different results
- helper functions never mutate caller inputs
"""

import random
import pytest

from engine.cards import standard_deck_rs
from engine.rng import make_rng, shuffled, shuffled_deck_rs
from engine.state import GameState, INITIAL_HAND_SIZE


def test_make_rng_rejects_non_int_seed():
    """Seed must be a plain int (not bool, not str, etc.)."""
    with pytest.raises(TypeError):
        make_rng("123")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        make_rng(123.0)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        make_rng(True)  # bool is a subclass of int


def test_make_rng_same_seed_produces_same_stream():
    """Two RNGs constructed from the same seed should produce identical outputs."""
    r1 = make_rng(42)
    r2 = make_rng(42)

    # Compare a short prefix of the random stream.
    seq1 = [r1.random() for _ in range(10)]
    seq2 = [r2.random() for _ in range(10)]
    assert seq1 == seq2


def test_shuffled_is_pure_and_deterministic():
    """`shuffled` should not mutate input and should be deterministic by seed."""
    items = [1, 2, 3, 4, 5]
    original = list(items)

    a = shuffled(items, seed=7)
    b = shuffled(items, seed=7)

    # Input not mutated
    assert items == original

    # Deterministic result
    assert a == b

    # It's still a permutation of the same elements.
    assert sorted(a) == sorted(items)


def test_shuffled_deck_rs_matches_manual_shuffle():
    """`shuffled_deck_rs` should match the canonical manual shuffle algorithm."""
    seed = 123

    # Manual reference: standard deck then random.Random(seed).shuffle(deck)
    ref = standard_deck_rs()
    random.Random(seed).shuffle(ref)

    got = shuffled_deck_rs(seed=seed)
    assert got == ref
    assert len(got) == 52
    assert set(got) == set(standard_deck_rs())


def test_shuffled_deck_rs_is_consistent_with_state_init():
    """State init should be equivalent to (shuffled deck split into hand + remaining)."""
    seed = 999
    full = shuffled_deck_rs(seed=seed)

    s = GameState.from_seed(seed)

    assert s.hand == full[:INITIAL_HAND_SIZE]
    assert s.deck == full[INITIAL_HAND_SIZE:]
