"""
Test helpers for initial game state and sample moves.

Kept small so both domain tests and store tests can use the same data shapes.
"""

from __future__ import annotations

from typing import Any, Dict, List

from baghchal.game_engine import get_initial_game_state

# Coordinate keys use the internal "row-col" format, not user-facing "1-1" style.
EMPTY_BOARD_KEYS = [
    "0-1", "0-2", "0-3",
    "1-0", "1-1", "1-2", "1-3", "1-4",
    "2-0", "2-1", "2-2", "2-3", "2-4",
    "3-0", "3-1", "3-2", "3-3", "3-4",
    "4-1", "4-2", "4-3",
]


def make_initial_state(
    player: Dict[str, str] | None = None,
    status: str = "waiting",
    game_id: str | None = None,
) -> Dict[str, Any]:
    state = get_initial_game_state()
    if player is not None:
        state["player"] = dict(player)
    state["status"] = status
    if game_id is not None:
        state["game_id"] = game_id
    return state


def make_place_move(to_key: str) -> Dict[str, str]:
    return {"moveType": "place", "toKey": to_key}


def make_displace_move(from_key: str, to_key: str, current_player: str) -> Dict[str, str]:
    return {
        "moveType": "displace",
        "fromKey": from_key,
        "toKey": to_key,
        "currentPlayer": current_player,
    }


def make_capture_move(from_key: str, to_key: str, current_player: str) -> Dict[str, str]:
    return {
        "moveType": "capture",
        "fromKey": from_key,
        "toKey": to_key,
        "currentPlayer": current_player,
    }


def player_state(goat: str = "", tiger: str = "") -> Dict[str, str]:
    return {"goat": goat, "tiger": tiger}
