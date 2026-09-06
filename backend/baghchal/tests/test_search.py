"""
Tests for the bot search: position evaluation, negamax with alpha-beta
pruning, iterative deepening, and the ``choose_bot_move`` facade.
"""

from __future__ import annotations

import time

import pytest

from baghchal.bot import choose_bot_move
from baghchal.game_engine import (
    INF,
    apply_move,
    evaluate_position,
    generate_moves,
    get_initial_game_state,
    search_best_move,
)
from baghchal.initial_data import make_initial_state, player_state


def _tiger_win_state() -> dict:
    state = make_initial_state(
        player=player_state(goat="alice", tiger="bob"),
        status="ongoing",
        game_id="game_1",
    )
    state["currentPlayer"] = "tiger"
    state["deadGoatCount"] = 5
    return state


def _goat_win_state() -> dict:
    """Single tiger at 0-0 fully surrounded: all neighbors and every capture
    landing square are goats."""
    state = make_initial_state(
        player=player_state(goat="alice", tiger="bob"),
        status="ongoing",
        game_id="game_1",
    )
    state["currentPlayer"] = "goat"
    state["board"] = {
        "0-0": "tiger",
        "0-1": "goat",
        "0-2": "goat",
        "1-0": "goat",
        "1-1": "goat",
        "2-0": "goat",
        "2-2": "goat",
    }
    return state


def _capture_threat_state(current_player: str) -> dict:
    """Tiger at 0-0 can capture the goat at 0-1 to land on 0-2; 4 goats are
    already dead so that capture would win for the tiger."""
    state = make_initial_state(
        player=player_state(goat="alice", tiger="bob"),
        status="ongoing",
        game_id="game_1",
    )
    state["board"] = {
        "0-0": "tiger",
        "0-1": "goat",
        "0-4": "tiger",
        "4-0": "tiger",
        "4-4": "tiger",
    }
    state["deadGoatCount"] = 4
    state["currentPlayer"] = current_player
    state["phase"] = "placement" if current_player == "goat" else "displacement"
    return state


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


def test_evaluate_initial_position_is_symmetric_by_turn():
    state = get_initial_game_state()
    goat_to_move = evaluate_position(state)  # goat to move
    tiger_state = dict(state)
    tiger_state["currentPlayer"] = "tiger"
    tiger_to_move = evaluate_position(tiger_state)

    assert goat_to_move == -tiger_to_move
    assert goat_to_move < 0  # initial position favors the tigers
    assert tiger_to_move > 0


def test_evaluate_more_dead_goats_helps_tiger():
    state = get_initial_game_state()
    state["currentPlayer"] = "tiger"

    base = evaluate_position(state)
    state["deadGoatCount"] = 3
    assert evaluate_position(state) == base + 3 * 700


def test_evaluate_tiger_win_is_infinite_for_tiger():
    state = _tiger_win_state()
    assert evaluate_position(state) == INF

    goat_state = dict(state)
    goat_state["currentPlayer"] = "goat"
    assert evaluate_position(goat_state) == -INF


def test_evaluate_goat_win_is_infinite_for_goat():
    state = _goat_win_state()
    assert evaluate_position(state) == INF  # goat to move, goat wins

    tiger_state = dict(state)
    tiger_state["currentPlayer"] = "tiger"
    assert evaluate_position(tiger_state) == -INF


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


def test_search_returns_a_legal_move():
    state = get_initial_game_state()
    move = search_best_move(state, max_depth=2, time_limit_ms=None)
    assert move is not None
    assert move in generate_moves(state)
    assert apply_move(state, move) is not None


def test_search_is_deterministic_for_fixed_depth():
    state = get_initial_game_state()
    first = search_best_move(state, max_depth=3, time_limit_ms=None)
    second = search_best_move(state, max_depth=3, time_limit_ms=None)
    assert first == second


def test_search_finds_winning_capture():
    state = _capture_threat_state("tiger")
    move = search_best_move(state, max_depth=2, time_limit_ms=None)
    assert move is not None
    assert move == {
        "moveType": "capture",
        "currentPlayer": "tiger",
        "fromKey": "0-0",
        "toKey": "0-2",
        "pieceType": "tiger",
    }


def test_search_as_goat_blocks_the_winning_capture():
    state = _capture_threat_state("goat")
    move = search_best_move(state, max_depth=2, time_limit_ms=None)
    assert move is not None
    # Only occupying the landing square 0-2 stops the tiger's winning capture.
    assert move["moveType"] == "place"
    assert move["toKey"] == "0-2"


def test_search_returns_none_when_game_is_over():
    assert search_best_move(_tiger_win_state(), max_depth=2) is None
    assert search_best_move(_goat_win_state(), max_depth=2) is None


def test_time_budget_returns_quickly_with_a_legal_move():
    state = get_initial_game_state()
    start = time.monotonic()
    move = search_best_move(state, max_depth=6, time_limit_ms=20)
    elapsed = time.monotonic() - start

    assert move is not None
    assert move in generate_moves(state)
    assert elapsed < 2.0


# ---------------------------------------------------------------------------
# choose_bot_move facade
# ---------------------------------------------------------------------------


def test_choose_bot_move_default_difficulty_returns_legal_move():
    state = get_initial_game_state()
    move = choose_bot_move(state)
    assert move is not None
    assert move in generate_moves(state)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_choose_bot_move_all_difficulties_return_legal_moves(difficulty):
    state = get_initial_game_state()
    move = choose_bot_move(state, difficulty=difficulty)
    assert move is not None
    assert move in generate_moves(state)


def test_choose_bot_move_none_when_game_over():
    assert choose_bot_move(_tiger_win_state()) is None


def test_bot_self_play_terminates_with_a_winner():
    """A full bot-vs-bot game must end in a win for one side."""
    state = get_initial_game_state()
    state["status"] = "ongoing"
    moves_played = 0
    winner = None

    while moves_played < 400:
        move = choose_bot_move(state, max_depth=1, time_limit_ms=None)
        if move is None:
            break
        state = apply_move(state, move)
        assert state is not None
        moves_played += 1
        score = evaluate_position(state)
        if abs(score) >= INF:
            # +INF: the side to move wins; -INF: the other side wins.
            winner = state["currentPlayer"] if score > 0 else (
                "goat" if state["currentPlayer"] == "tiger" else "tiger"
            )
            break

    assert moves_played < 400, "self-play did not terminate"
    assert winner in ("tiger", "goat")