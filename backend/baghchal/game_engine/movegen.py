"""
Legal move generation.

Enumerates every legal move for the player to move, using the connection
tables in ``board.py`` as the single source of truth for adjacency and
capture lines. This is what the bot searches over, and it is the yardstick
``is_valid_move`` is measured against.

Generated moves use the same shape the rest of the pipeline sends over the
wire: ``{moveType, currentPlayer, fromKey, toKey, pieceType}``. Place moves
carry ``fromKey: None`` (the frontend sends ``null`` for place moves).
"""

from __future__ import annotations

from typing import Any

from .board import CAPTURE_CONNECTIONS, MOVE_CONNECTIONS, get_mid_key


def generate_moves(game_state: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Return every legal move for the player to move.

    Ordering is deterministic: tiger captures come before tiger slides
    (handy for search move ordering); everything else is sorted by
    coordinate.
    """
    board = game_state.get("board", {})
    current_player = game_state.get("currentPlayer")

    if current_player == "goat":
        return _generate_goat_moves(board, game_state)
    return _generate_tiger_moves(board)


def _generate_goat_moves(
    board: dict[str, str],
    game_state: dict[str, Any],
) -> list[dict[str, Any]]:
    moves: list[dict[str, Any]] = []

    if game_state.get("phase") == "placement":
        # Goats place on any empty cell while goats remain to be placed.
        for to_key in sorted(MOVE_CONNECTIONS):
            if to_key not in board:
                moves.append(
                    {
                        "moveType": "place",
                        "currentPlayer": "goat",
                        "fromKey": None,
                        "toKey": to_key,
                        "pieceType": "goat",
                    }
                )
        return moves

    # Displacement: a goat slides to an empty adjacent cell.
    for from_key in sorted(board):
        if board[from_key] != "goat":
            continue
        for to_key in MOVE_CONNECTIONS[from_key]:
            if to_key not in board:
                moves.append(
                    {
                        "moveType": "displace",
                        "currentPlayer": "goat",
                        "fromKey": from_key,
                        "toKey": to_key,
                        "pieceType": "goat",
                    }
                )
    return moves


def _generate_tiger_moves(
    board: dict[str, str],
) -> list[dict[str, Any]]:
    slides: list[dict[str, Any]] = []
    captures: list[dict[str, Any]] = []

    for from_key in sorted(board):
        if board[from_key] != "tiger":
            continue

        for to_key in MOVE_CONNECTIONS[from_key]:
            if to_key not in board:
                slides.append(
                    {
                        "moveType": "displace",
                        "currentPlayer": "tiger",
                        "fromKey": from_key,
                        "toKey": to_key,
                        "pieceType": "tiger",
                    }
                )

        for to_key in CAPTURE_CONNECTIONS[from_key]:
            if to_key in board:
                continue
            if board.get(get_mid_key(from_key, to_key)) != "goat":
                continue
            captures.append(
                {
                    "moveType": "capture",
                    "currentPlayer": "tiger",
                    "fromKey": from_key,
                    "toKey": to_key,
                    "pieceType": "tiger",
                }
            )

    return captures + slides