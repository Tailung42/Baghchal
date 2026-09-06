"""
Game engine public API.

This package is intentionally importable without Django being configured
for lightweight scripts and tests that only need board rules and game
state helpers.

If Django is available and configured, the full service layer will also
be importable through the existing import chain.
"""

from .board import (
    CAPTURE_CONNECTIONS,
    MOVE_CONNECTIONS,
    can_capture,
    check_goat_win,
    check_tiger_win,
    get_mid_key,
    get_possible_tiger_moves,
    is_blocked,
)
from .game_state import (
    apply_move,
    check_game_over,
    get_initial_game_state,
    is_valid_move,
    to_user_coord,
)
from .movegen import generate_moves
from .evaluate import INF, evaluate_position
from .search import search_best_move

try:
    from .services import (
        GAME_ID_LENGTH,
        GameStatus,
        async_update_game_state,
    )
except Exception:
    GameStatus = None  # type: ignore[assignment]
    async_update_game_state = None  # type: ignore[assignment]
    GAME_ID_LENGTH = 8  # type: ignore[assignment]


__all__ = [
    "get_mid_key",
    "get_possible_tiger_moves",
    "can_capture",
    "is_blocked",
    "check_tiger_win",
    "check_goat_win",
    "MOVE_CONNECTIONS",
    "CAPTURE_CONNECTIONS",
    "get_initial_game_state",
    "to_user_coord",
    "is_valid_move",
    "generate_moves",
    "evaluate_position",
    "search_best_move",
    "INF",
    "check_game_over",
    "apply_move",
    "async_update_game_state",
    "GameStatus",
    "GAME_ID_LENGTH",
]
