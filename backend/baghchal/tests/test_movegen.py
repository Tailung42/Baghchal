"""
Tests for legal move generation and the hardened move validation.

``generate_moves`` and ``is_valid_move`` must agree: a move is legal if and
only if it is produced by move generation. These tests pin the counting,
phase, turn, adjacency, and capture semantics of the engine core.
"""

from __future__ import annotations

import pytest

from baghchal.game_engine import (
    apply_move,
    generate_moves,
    get_initial_game_state,
    is_valid_move,
)
from baghchal.initial_data import (
    EMPTY_BOARD_KEYS,
    make_capture_move,
    make_displace_move,
    make_initial_state,
    make_place_move,
    player_state,
)


def _tiger_turn_state(**overrides) -> dict:
    """A state with tigers to move and only the corner tigers on the board."""
    state = make_initial_state(
        player=player_state(goat="alice", tiger="bob"),
        status="ongoing",
        game_id="game_1",
    )
    state["currentPlayer"] = "tiger"
    state["unusedGoat"] = 0
    state["phase"] = "displacement"
    state.update(overrides)
    return state


# ---------------------------------------------------------------------------
# Placement phase
# ---------------------------------------------------------------------------


def test_initial_position_generates_only_placements():
    state = get_initial_game_state()
    moves = generate_moves(state)

    assert len(moves) == len(EMPTY_BOARD_KEYS) == 21
    assert all(m["moveType"] == "place" for m in moves)
    assert all(m["currentPlayer"] == "goat" for m in moves)
    assert all(m["fromKey"] is None for m in moves)
    assert {m["toKey"] for m in moves} == set(EMPTY_BOARD_KEYS)


def test_placement_move_count_decreases_as_goats_are_placed():
    state = get_initial_game_state()
    state = apply_move(state, make_place_move("0-1"))
    assert state is not None
    # After a goat places, it is the tiger's turn; switch back to goat to
    # enumerate the next goat placement options.
    state["currentPlayer"] = "goat"
    moves = generate_moves(state)
    assert len(moves) == 20
    assert "0-1" not in {m["toKey"] for m in moves}


def test_place_move_is_valid_for_every_empty_cell():
    state = get_initial_game_state()
    for to_key in EMPTY_BOARD_KEYS:
        assert is_valid_move(state, make_place_move(to_key)) is True


# ---------------------------------------------------------------------------
# Displacement phase (goats)
# ---------------------------------------------------------------------------


def test_displacement_generates_goat_slides_only():
    state = get_initial_game_state()
    state["currentPlayer"] = "goat"
    state["unusedGoat"] = 0
    state["phase"] = "displacement"
    state["board"]["1-1"] = "goat"
    state["board"]["3-3"] = "goat"

    moves = generate_moves(state)

    assert len(moves) == 14  # 7 empty neighbors each for 1-1 and 3-3
    assert all(m["moveType"] == "displace" for m in moves)
    assert all(m["currentPlayer"] == "goat" for m in moves)
    assert all(m["pieceType"] == "goat" for m in moves)


def test_goat_displace_rejected_during_placement_phase():
    state = get_initial_game_state()
    state["board"]["1-1"] = "goat"
    move = make_displace_move("1-1", "1-2", "goat")
    assert is_valid_move(state, move) is False


def test_displace_rejected_when_destination_is_not_adjacent():
    state = _tiger_turn_state()
    move = make_displace_move("0-0", "0-3", "tiger")
    assert is_valid_move(state, move) is False


# ---------------------------------------------------------------------------
# Tiger moves
# ---------------------------------------------------------------------------


def test_tiger_generates_captures_before_slides():
    state = _tiger_turn_state()
    state["board"] = {"0-0": "tiger", "0-1": "goat", "1-1": "goat"}

    moves = generate_moves(state)

    # Captures: 0-0 -> 0-2 (over 0-1) and 0-0 -> 2-2 (over 1-1).
    assert [m["moveType"] for m in moves] == ["capture", "capture", "displace"]
    assert moves[0] == {
        "moveType": "capture",
        "currentPlayer": "tiger",
        "fromKey": "0-0",
        "toKey": "0-2",
        "pieceType": "tiger",
    }
    assert moves[2]["moveType"] == "displace"
    assert moves[2]["toKey"] == "1-0"


def test_capture_not_generated_when_midpoint_has_no_goat():
    state = _tiger_turn_state()
    state["board"] = {"0-0": "tiger"}  # no goat anywhere near a capture line

    moves = generate_moves(state)

    assert all(m["moveType"] != "capture" for m in moves)
    assert is_valid_move(state, make_capture_move("0-0", "0-2", "tiger")) is False


def test_capture_not_generated_when_landing_occupied():
    state = _tiger_turn_state()
    state["board"] = {
        "0-0": "tiger",
        "0-1": "goat",
        "0-2": "goat",
    }

    moves = generate_moves(state)

    assert all(m["moveType"] != "capture" for m in moves)
    assert is_valid_move(state, make_capture_move("0-0", "0-2", "tiger")) is False


def test_tiger_capture_is_valid_when_mid_is_goat():
    state = _tiger_turn_state()
    state["board"] = {"0-0": "tiger", "0-1": "goat"}
    assert is_valid_move(state, make_capture_move("0-0", "0-2", "tiger")) is True


# ---------------------------------------------------------------------------
# Turn ownership
# ---------------------------------------------------------------------------


def test_generate_moves_only_for_current_player():
    state = get_initial_game_state()  # goat to move
    assert all(m["currentPlayer"] == "goat" for m in generate_moves(state))

    tiger_state = _tiger_turn_state()
    tiger_state["board"] = {"0-0": "tiger"}
    assert all(m["currentPlayer"] == "tiger" for m in generate_moves(tiger_state))


def test_out_of_turn_move_is_rejected():
    state = get_initial_game_state()  # goat's turn
    move = make_displace_move("0-0", "0-1", "tiger")
    assert is_valid_move(state, move) is False


def test_place_move_without_current_player_falls_back_to_state_turn():
    state = get_initial_game_state()  # goat's turn
    assert is_valid_move(state, make_place_move("0-1")) is True

    tiger_state = _tiger_turn_state()
    assert is_valid_move(tiger_state, make_place_move("0-1")) is False


# ---------------------------------------------------------------------------
# Agreement between generation and validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "make_state",
    [
        get_initial_game_state,
        lambda: apply_move(get_initial_game_state(), make_place_move("0-1")),
        lambda: _tiger_turn_state(
            board={"0-0": "tiger", "0-1": "goat", "1-1": "goat"}
        ),
        lambda: _tiger_turn_state(
            currentPlayer="goat",
            board={"0-0": "tiger", "1-1": "goat", "3-3": "goat"},
        ),
    ],
    ids=["initial", "placed", "midgame", "goat-displacement"],
)
def test_every_generated_move_is_valid_and_applies(make_state):
    state = make_state()
    assert state is not None

    moves = generate_moves(state)
    assert moves, "expected at least one generated move"

    for move in moves:
        assert is_valid_move(state, move) is True
        next_state = apply_move(state, move)
        assert next_state is not None
        assert next_state["currentPlayer"] != state["currentPlayer"]
        assert len(next_state["history"]) == len(state["history"]) + 1


def test_apply_move_rejects_malformed_move_without_crashing():
    state = get_initial_game_state()
    assert apply_move(state, None) is None
    assert apply_move(state, {}) is None
    assert apply_move(state, {"moveType": "teleport", "toKey": "9-9"}) is None