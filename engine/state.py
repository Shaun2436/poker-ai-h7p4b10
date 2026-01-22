# 1.
# engine/state.py

"""
GameState: H, P, D, score, deck...
Initialize a new game from seed, generate a new static deck, dealing 7 cards
save the state of hand, deck, p_remaining, d_remaining, score_total

NOTE (public info model):
- The engine may store the full deck internally for determinism/replay.
- Public state must NOT expose deck composition. It exposes only deck_remaining_count.
"""

from __future__ import annotations

import random
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
    """
    hand: List[str]
    deck: List[str]    # internal only (do NOT expose via API)
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
    
    def to_public_dict(self) -> Dict[str, Any]:
        """
        Public view of state (matches API contract shape).
        Must NOT include deck composition
        """
        return {
            "hand": list(self.hand),
            "deck_remaining_count": self.deck_remaining_count,
            "p_remaining": self.p_remaining,
            "d_remaining": self.d_remaining,
            "score_total": self.score_total,
        }

    