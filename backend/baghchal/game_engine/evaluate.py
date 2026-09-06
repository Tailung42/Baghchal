"""
Position evaluation for the bot search.

The heuristic is adapted from the reference ``pybaghchal`` engine. From the
tiger's perspective:

    score = 300 * movable_tigers + 700 * dead_goats - 700 * closed_spaces

- ``movable_tigers`` — tigers with at least one legal slide or capture.
- ``dead_goats`` — tiger material (5 dead goats wins the game).
- ``closed_spaces`` — empty squares surrounded by goats that no tiger can
  capture into; a proxy for goat control and tiger entrapment.

``evaluate_position`` returns the score from the perspective of the player
to move, so the same function works for both sides in a negamax search.
Wins and losses are returned as ``±INF``.
"""

from __future__ import annotations

from typing import Any

from .board import (
    CAPTURE_CONNECTIONS,
    MOVE_CONNECTIONS,
    check_goat_win,
    check_tiger_win,
    is_blocked,
)

INF = 1_000_000

TIGER_MOBILITY_WEIGHT = 300
DEAD_GOAT_WEIGHT = 700
CLOSED_SPACE_WEIGHT = 700


def movable_tiger_count(board: dict[str, str]) -> int:
    """Number of tigers with at least one legal slide or capture."""
    return sum(
        1
        for pos, piece in board.items()
        if piece == "tiger" and not is_blocked(pos, board)
    )


def closed_space_count(board: dict[str, str]) -> int:
    """
    Number of empty squares surrounded by goats that no tiger can reach by
    capture. Goats accumulate these as they surround the tigers.
    """
    count = 0
    for pos in MOVE_CONNECTIONS:
        if pos in board:
            continue
        neighbors_are_goats = all(
            board.get(neighbor) == "goat"
            for neighbor in MOVE_CONNECTIONS[pos]
        )
        if not neighbors_are_goats:
            continue
        tiger_can_capture_here = any(
            board.get(capture_endpoint) == "tiger"
            for capture_endpoint in CAPTURE_CONNECTIONS[pos]
        )
        if not tiger_can_capture_here:
            count += 1
    return count


def tiger_score(board: dict[str, str], dead_goats: int) -> int:
    """Heuristic score from the tiger's perspective (higher = better tiger)."""
    return (
        TIGER_MOBILITY_WEIGHT * movable_tiger_count(board)
        + DEAD_GOAT_WEIGHT * dead_goats
        - CLOSED_SPACE_WEIGHT * closed_space_count(board)
    )


def evaluate_position(game_state: dict[str, Any]) -> int:
    """
    Score a position from the perspective of the player to move.

    Returns ``±INF`` when the game is decided in that player's favor.
    """
    board = game_state["board"]
    dead_goats = game_state["deadGoatCount"]
    side_to_move = game_state["currentPlayer"]

    if check_tiger_win(dead_goats):
        return INF if side_to_move == "tiger" else -INF
    if check_goat_win(board):
        return INF if side_to_move == "goat" else -INF

    score = tiger_score(board, dead_goats)
    return score if side_to_move == "tiger" else -score