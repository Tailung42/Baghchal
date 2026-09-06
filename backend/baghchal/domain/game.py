"""
Domain layer entry points for game logic.

This layer reuses the existing game engine but isolates it behind a clean
domain API. That makes it easier to test game behavior without Django,
Channels, or Redis.
"""

from __future__ import annotations

from typing import Any

from baghchal.game_engine import (
    apply_move,
    check_game_over,
    get_initial_game_state,
    is_valid_move,
)


def fresh_game_state() -> dict[str, Any]:
    return get_initial_game_state()


def validate_move(game_state: dict[str, Any], move: dict[str, Any]) -> bool:
    return is_valid_move(game_state, move)


def apply_move_to_state(game_state: dict[str, Any], move: dict[str, Any]) -> dict[str, Any] | None:
    return apply_move(game_state, move)


def is_over(game_state: dict[str, Any]) -> bool:
    return check_game_over(game_state)
