"""
Domain tests for game logic.

These test the domain wrapper around the existing game engine so we can
validate behavior without Django, Channels, or Redis.
"""

from baghchal.domain.game import apply_move_to_state, fresh_game_state, is_over, validate_move
from baghchal.initial_data import (
    make_capture_move,
    make_displace_move,
    make_initial_state,
    make_place_move,
    player_state,
)


def test_fresh_game_state_defaults():
    state = fresh_game_state()
    assert state["status"] == "waiting"
    assert state["currentPlayer"] == "goat"
    assert state["phase"] == "placement"
    assert state["unusedGoat"] == 20
    assert set(state["board"]) == {"0-0", "0-4", "4-0", "4-4"}


def test_place_move_is_valid_when_square_is_free():
    state = make_initial_state(player=player_state(goat="alice", tiger=""))
    move = make_place_move("0-1")
    assert validate_move(state, move) is True


def test_place_move_is_invalid_when_square_is_occupied():
    state = make_initial_state(player=player_state(goat="", tiger=""))
    move = make_place_move("0-0")
    assert validate_move(state, move) is False


def test_place_move_applied_state_changes():
    state = make_initial_state(
        player=player_state(goat="alice", tiger=""),
        status="ongoing",
    )
    move = make_place_move("0-1")
    new_state = apply_move_to_state(state, move)
    assert new_state is not None
    assert new_state["board"]["0-1"] == "goat"
    assert new_state["unusedGoat"] == 19
    assert new_state["currentPlayer"] == "tiger"


def test_displace_move_requires_piece_to_belong_to_current_player():
    state = make_initial_state(
        player=player_state(goat="alice", tiger="bob"),
        status="ongoing",
        game_id="game_1",
    )
    # Tigers may slide as soon as it is their turn, regardless of goat
    # placement phase.
    state["currentPlayer"] = "tiger"
    state["unusedGoat"] = 0
    state["phase"] = "displacement"

    # Claiming the wrong piece for the move is invalid.
    move = make_displace_move("0-0", "0-1", "goat")
    assert validate_move(state, move) is False

    move = make_displace_move("0-0", "0-1", "tiger")
    assert validate_move(state, move) is True


def test_out_of_turn_move_is_rejected():
    state = make_initial_state(
        player=player_state(goat="alice", tiger="bob"),
        status="ongoing",
        game_id="game_1",
    )
    # It is the goat's turn (placement), so a tiger slide is out of turn.
    move = make_displace_move("0-0", "0-1", "tiger")
    assert validate_move(state, move) is False


def _clear_corner(square):
    # Helper to remove a corner tiger from the board for test setup.
    # Initial states include tiger corners at 0-0, 0-4, 4-0, 4-4.
    return None


def test_capture_increments_dead_goat_count():
    state = make_initial_state(
        player=player_state(goat="alice", tiger="bob"),
        status="ongoing",
        game_id="game_1",
    )
    # Arrange a simple capture scenario using a real tiger capture line.
    # Tiger at 2-2, goat at 1-2, landing at 0-4.
    # The midpoint of 2-2 and 0-4 is 1-3, so is_valid_move requires that
    # midpoint square to be free and occupied by a goat for a capture.
    # The destination square must also be empty in the board state.
    state["board"].pop("0-4", None)
    state["board"]["2-2"] = "tiger"
    state["board"]["1-2"] = "goat"
    state["board"]["1-3"] = "goat"
    state["currentPlayer"] = "tiger"
    state["phase"] = "displacement"
    state["unusedGoat"] = 0

    move = make_capture_move("2-2", "0-4", "tiger")
    assert validate_move(state, move) is True
    new_state = apply_move_to_state(state, move)
    assert new_state is not None
    assert new_state["deadGoatCount"] == 1
    assert new_state["isCaptured"] is True
    assert new_state["board"].get("1-2") == "goat"


def test_game_is_not_over_initially():
    state = make_initial_state(player=player_state(goat="alice", tiger="bob"))
    assert is_over(state) is False


def test_game_over_payload_present_after_tiger_wins():
    state = make_initial_state(
        player=player_state(goat="alice", tiger="bob"),
        status="ongoing",
    )
    state["deadGoatCount"] = 4
    state["currentPlayer"] = "tiger"

    # One more capture should make dead_goats 5 and trigger tiger win.
    state["board"].pop("0-4", None)
    state["board"]["2-2"] = "tiger"
    state["board"]["1-2"] = "goat"
    state["board"]["1-3"] = "goat"
    move = make_capture_move("2-2", "0-4", "tiger")
    new_state = apply_move_to_state(state, move)
    assert new_state is not None
    assert new_state["deadGoatCount"] == 5
    assert is_over(new_state) is True
    assert new_state.get("winner") == "tiger"
    assert new_state.get("status") == "over"
    assert new_state["board"].get("1-2") == "goat"
