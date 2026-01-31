import pytest

from engine.actions import (
    Action,
    PLAY,
    DISCARD,
    action_from_dict,
    action_to_dict,
    validate_action,
)


def test_action_roundtrip_dict():
    a = Action(type=PLAY, selected_indices=(0, 1, 2, 3, 4))
    d = action_to_dict(a)
    assert d == {"type": "PLAY", "selected_indices": [0, 1, 2, 3, 4]}
    a2 = action_from_dict(d)
    assert a2 == a


def test_action_from_dict_rejects_bad_type():
    with pytest.raises(ValueError):
        action_from_dict({"type": "NOPE", "selected_indices": [0]})


def test_action_from_dict_rejects_non_list_indices():
    with pytest.raises(ValueError):
        action_from_dict({"type": "PLAY", "selected_indices": "0,1,2,3,4"})


def test_action_from_dict_rejects_non_int_indices():
    # bool is a subclass of int; must be rejected.
    with pytest.raises(ValueError):
        action_from_dict({"type": "PLAY", "selected_indices": [True, 1, 2, 3, 4]})


def test_validate_play_requires_five():
    a = Action(type=PLAY, selected_indices=(0, 1, 2, 3))
    with pytest.raises(ValueError) as e:
        validate_action(a, hand_len=7, p_remaining=1, d_remaining=10)
    assert "play_requires_five" in str(e.value)


def test_validate_play_requires_budget():
    a = Action(type=PLAY, selected_indices=(0, 1, 2, 3, 4))
    with pytest.raises(ValueError):
        validate_action(a, hand_len=7, p_remaining=0, d_remaining=10)


def test_validate_discard_budget_exceeded():
    a = Action(type=DISCARD, selected_indices=(0, 1, 2))
    with pytest.raises(ValueError) as e:
        validate_action(a, hand_len=7, p_remaining=4, d_remaining=2)
    assert "discard_budget_exceeded" in str(e.value)


def test_validate_indices_must_be_unique_and_in_bounds():
    dup = Action(type=DISCARD, selected_indices=(1, 1))
    with pytest.raises(ValueError):
        validate_action(dup, hand_len=7, p_remaining=4, d_remaining=10)

    oob = Action(type=DISCARD, selected_indices=(7,))
    with pytest.raises(ValueError):
        validate_action(oob, hand_len=7, p_remaining=4, d_remaining=10)
