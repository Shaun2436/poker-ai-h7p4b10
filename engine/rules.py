# 6.
# engine/rules.py
# apply(action) + validation + events
"""
Core game rules / state transitions.

This module is the missing glue between:
- public input language (engine.actions.Action)
- state container (engine.state.GameState)
- scoring policy (engine.scoring)

Scope boundary:
- This file OWNS state transitions (apply_action()).
- It reuses engine.actions.validate_action() for all input validation.
- It does NOT implement API message translation, UI rendering, replay, or AI.

Determinism:
- All draws come from the *front* of GameState.deck (index 0..n-1).
- Same seed + same action sequence => same resulting states.

Public info model note:
- GameState may store internal draw-order deck for determinism/replay.
- Public state must not expose draw order; that is handled by GameState.to_public_dict().
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Dict, List, Tuple

from engine.actions import Action, PLAY, DISCARD, validate_action
from engine.scoring import score_5card_hand_gameplay
from engine.state import GameState, INITIAL_HAND_SIZE


# Minimal structured event for replay/logging. API/UI can translate later.
Event = Dict[str, Any]


def _draw_from_deck(deck: List[str], n: int) -> Tuple[List[str], List[str]]:
    """
    Draw n cards from the *front* of the internal deck.

    Args:
        deck: Internal draw-order deck (front is next card).
        n: Number of cards to draw (>= 0).

    Returns:
        (drawn_cards, remaining_deck)

    Raises:
        ValueError: If n is negative or deck does not have enough cards.
    """
    if n < 0:
        raise ValueError(f"n must be >= 0 (got {n})")
    if n > len(deck):
        raise ValueError(f"Deck underflow: need {n} cards but only {len(deck)} remain")
    return deck[:n], deck[n:]


def _remove_indices_preserve_order(hand: List[str], indices: Tuple[int, ...]) -> Tuple[List[str], List[str]]:
    """
    Remove specific positions from the hand while preserving the order of survivors.

    Important: indices refer to positions in the *current* hand, not card identities.

    Returns:
        (kept_cards, removed_cards_in_hand_order)
    """
    idx_set = set(indices)
    kept: List[str] = []
    removed: List[str] = []
    for i, card in enumerate(hand):
        if i in idx_set:
            removed.append(card)
        else:
            kept.append(card)
    return kept, removed


def apply_action(state: GameState, action: Action) -> Tuple[GameState, List[Event]]:
    """
    Apply an action to the current GameState.

    This is the engine's authoritative state transition function.

    Args:
        state: Current game state (contains hand + internal deck draw order).
        action: Player action (PLAY or DISCARD) using indices into state.hand.

    Returns:
        (next_state, events)

        next_state: New GameState with updated hand/deck/budgets/score.
        events: Minimal structured events describing what happened (for logging/replay).

    Raises:
        ValueError: If action is invalid under current budgets/hand size,
                    or if the deck cannot satisfy the required draw.
    """
    # Centralized validation: budgets + bounds + required selection counts.
    validate_action(
        action,
        hand_len=len(state.hand),
        p_remaining=state.p_remaining,
        d_remaining=state.d_remaining,
    )

    # Remove selected cards (by indices) from the hand.
    kept, removed = _remove_indices_preserve_order(state.hand, action.selected_indices)

    if action.type == DISCARD:
        n = len(removed)

        # Draw exactly n cards to refill hand back to 7.
        drawn, next_deck = _draw_from_deck(state.deck, n)
        next_hand = kept + drawn

        # Invariant: hand stays at fixed size.
        if len(next_hand) != INITIAL_HAND_SIZE:
            raise ValueError(f"Hand size invariant broken after DISCARD: {len(next_hand)}")

        next_state = replace(
            state,
            hand=next_hand,
            deck=next_deck,
            d_remaining=state.d_remaining - n,
        )

        events: List[Event] = [
            {
                "type": "DISCARD",
                "discarded": removed,
                "drawn": drawn,
                "d_remaining_after": next_state.d_remaining,
            }
        ]
        return next_state, events

    if action.type == PLAY:
        # PLAY always scores EXACTLY the chosen 5 cards (not best-of-7).
        played_cards = removed
        category, points = score_5card_hand_gameplay(played_cards)

        # Draw exactly 5 to refill hand back to 7.
        drawn, next_deck = _draw_from_deck(state.deck, 5)
        next_hand = kept + drawn

        if len(next_hand) != INITIAL_HAND_SIZE:
            raise ValueError(f"Hand size invariant broken after PLAY: {len(next_hand)}")

        next_state = replace(
            state,
            hand=next_hand,
            deck=next_deck,
            p_remaining=state.p_remaining - 1,
            score_total=state.score_total + points,
        )

        events = [
            {
                "type": "PLAY",
                "played": played_cards,
                "category": category,
                "points": points,
                "drawn": drawn,
                "p_remaining_after": next_state.p_remaining,
                "score_total_after": next_state.score_total,
            }
        ]
        return next_state, events

    # Defensive: ActionType is a Literal, but keep runtime safety.
    raise ValueError(f"Unknown action type: {action.type!r}")
