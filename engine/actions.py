# 5.
# engine/actions.py

"""
Action definitions and validation.

This module defines the *input language* that drives the engine: an Action is
either:

- PLAY: choose exactly 5 cards from the current hand to score.
- DISCARD: choose 1..min(len(hand), d_remaining) cards to throw away and redraw.

Scope boundary:
- This file does NOT mutate GameState. It only validates and normalizes
  action input.
- State transitions are owned by the engine's apply(action) function (to be
  implemented elsewhere).

Contract alignment:
- JSON shape matches docs/API_CONTRACT.md:
    {"type": "PLAY"|"DISCARD", "selected_indices": [int, ...]}
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Sequence


ActionType = Literal["PLAY", "DISCARD"]

PLAY: ActionType = "PLAY"
DISCARD: ActionType = "DISCARD"


@dataclass(frozen=True, slots=True)
class Action:
    """
    A validated player action.

    Attributes:
        type: "PLAY" or "DISCARD".
        selected_indices: Zero-based indices into the *current* hand.
            - For PLAY: exactly 5 indices.
            - For DISCARD: 1..min(len(hand), d_remaining) indices.

    Notes:
        - Indices refer to positions, not card identities.
        - Validation against hand size/budgets is done by validate_action().
    """

    type: ActionType
    selected_indices: tuple[int, ...]


def _ensure_int_indices(indices: Sequence[Any]) -> List[int]:
    """Convert and validate indices are ints (no bools)."""
    out: List[int] = []
    for x in indices:
        # bool is a subclass of int; reject explicitly.
        if isinstance(x, bool) or not isinstance(x, int):
            raise ValueError(f"Index must be an int (got {type(x).__name__}: {x!r})")
        out.append(x)
    return out


def _validate_unique_in_bounds(indices: Sequence[int], hand_len: int) -> None:
    """Validate index uniqueness and range within current hand."""
    if hand_len < 0:
        raise ValueError(f"hand_len must be >= 0 (got {hand_len})")
    if len(set(indices)) != len(indices):
        raise ValueError(f"Duplicate indices are not allowed: {list(indices)!r}")
    for i in indices:
        if i < 0 or i >= hand_len:
            raise ValueError(f"Index out of bounds for hand_len={hand_len}: {i}")


def validate_action(action: Action, *, hand_len: int, p_remaining: int, d_remaining: int) -> None:
    """
    Validate an Action against the current public game state.

    Args:
        action: The Action to validate.
        hand_len: Current hand length.
        p_remaining: Plays remaining.
        d_remaining: Discard budget remaining.

    Raises:
        ValueError: If the action is invalid under the rules/contract.

    Rules (docs/API_CONTRACT.md and README fixed parameters):
        - PLAY:
            - must have p_remaining > 0
            - must select exactly 5 unique indices within bounds
        - DISCARD:
            - must have d_remaining > 0
            - must select n unique indices within bounds where:
                1 <= n <= min(hand_len, d_remaining)
    """
    if p_remaining < 0 or d_remaining < 0:
        raise ValueError("Budgets must be non-negative")

    if action.type == PLAY:
        if p_remaining <= 0:
            raise ValueError("No plays remaining")
        if len(action.selected_indices) != 5:
            # mirrors API_CONTRACT example params.reason = "play_requires_five"
            raise ValueError("play_requires_five")
        _validate_unique_in_bounds(action.selected_indices, hand_len)
        return

    if action.type == DISCARD:
        if d_remaining <= 0:
            raise ValueError("No discards remaining")
        n = len(action.selected_indices)
        max_n = min(hand_len, d_remaining)
        if n < 1:
            raise ValueError("discard_requires_at_least_one")
        if n > max_n:
            # mirrors API_CONTRACT message key example "error.discard_budget_exceeded"
            raise ValueError("discard_budget_exceeded")
        _validate_unique_in_bounds(action.selected_indices, hand_len)
        return

    # Defensive: ActionType is a Literal, but keep runtime safety for untrusted input.
    raise ValueError(f"Unknown action type: {action.type!r}")


def action_from_dict(obj: Dict[str, Any]) -> Action:
    """
    Parse an Action from an API JSON dict.

    Expected shape:
        {"type": "PLAY"|"DISCARD", "selected_indices": [0, 1, ...]}

    Raises:
        ValueError: on missing fields or wrong types.
    """
    if not isinstance(obj, dict):
        raise ValueError("Action must be an object")

    t = obj.get("type")
    if t not in (PLAY, DISCARD):
        raise ValueError(f"Invalid action type: {t!r}")

    sel = obj.get("selected_indices")
    if not isinstance(sel, list):
        raise ValueError("selected_indices must be a list")

    indices = _ensure_int_indices(sel)
    return Action(type=t, selected_indices=tuple(indices))


def action_to_dict(action: Action) -> Dict[str, Any]:
    """Serialize an Action into an API JSON dict."""
    return {
        "type": action.type,
        "selected_indices": list(action.selected_indices),
    }
