# 1.
# engine/state.py

"""
GameState: H, P, D, score, deck...
Initialize a new game from seed, generate a new static deck, dealing 7 cards
save the state of hand, deck, p_remaining, d_remaining, score_total

NOTE (public info model):
- The engine may store the full deck internally for determinism/replay.
- Public state must NOT expose deck draw order.
- Public state may expose unordered deck composition only if allowed by reveal policy.
"""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass
from typing import List, Dict, Any

from engine.cards import standard_deck_rs

INITIAL_HAND_SIZE = 7
INITIAL_P = 4
INITIAL_D = 10

@dataclass
class GameState:
    """
    Represents the entire state of the game at a specific moment.

    Attributes:
        hand (List[str]): The player's current hand of cards (RS strings).
        deck (List[str]): The remaining deck of cards (internal, ordered for determinism).
        p_remaining (int): Plays remaining.
        d_remaining (int): Discard budget remaining.
        score_total (int): Total score accumulated so far.
    
    - `deck` is stored in draw order for determinism/replay.
    - Public state must NOT reveal draw order. Only reveal count / composition (unordered) if allowed.
    """
    hand: List[str]
    deck: List[str]    # internal draw order
    p_remaining: int
    d_remaining: int
    score_total: int

    @classmethod
    def from_seed(cls, seed: int) -> "GameState":
        """
        Initialize a new game state from a shuffled seed
        Deterministic: same seed => same hand and deck
        """
        rng = random.Random(seed)

        deck = standard_deck_rs()
        rng.shuffle(deck)

        hand = deck[:INITIAL_HAND_SIZE]
        remaining_deck = deck[INITIAL_HAND_SIZE:]
        
        return cls(
            hand=hand,
            deck=remaining_deck,
            p_remaining=INITIAL_P,
            d_remaining=INITIAL_D,
            score_total=0,
        )
    
    @property
    def deck_remaining_count(self) -> int:
        """Publicly safe deck info: only the count, not composition."""
        return len(self.deck)
    
    def deck_remaining_counts(self) -> Dict[str, int]:
        """
        Canonical, unordered composition of remaining deck.
        Key: card RS string (e.g., "AS")
        Value: count (int)
        """
        # Counter preserves insertion order of first-seen keys,
        # but ordering of dict keys should not be relied on by clients anyway.
        return dict(Counter(self.deck))

    def deck_remaining_unordered(self) -> List[str]:
        """
        Unordered view of remaining deck composition.
        IMPORTANT: returns a sorted copy so we don't leak internal draw order.
        """
        return sorted(self.deck)
    
    def to_public_dict(self, include_deck_composition: bool = False) -> Dict[str, Any]:
        """
        Public view of state.
        - Always safe fields are always included.
        - If include_deck_composition=True, include composition but NOT draw order.
        """
        out: Dict[str, Any] = {
            "hand": list(self.hand),
            "deck_remaining_count": self.deck_remaining_count,
            "p_remaining": self.p_remaining,
            "d_remaining": self.d_remaining,
            "score_total": self.score_total,
        }

        if include_deck_composition:
            out["deck_remaining_counts"] = self.deck_remaining_counts()
            out["deck_remaining"] = self.deck_remaining_unordered()

        return out

    