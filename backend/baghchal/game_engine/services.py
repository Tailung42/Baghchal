import asyncio
from typing import Any, Awaitable, Callable

from .game_state import apply_move, check_game_over

GAME_ID_LENGTH = 8

class GameStatus:
    WAITING = 'waiting'
    ONGOING = 'ongoing'
    OVER = 'over'


async def async_update_game_state(
    room_name: str,
    move: dict[str, Any],
    *,
    store_get: Callable[[str], Awaitable[dict[str, Any] | None]] = None,
    store_set: Callable[[str, dict[str, Any]], Awaitable[bool]] = None,
    store_delete: Callable[[str], Awaitable[bool]] = None,
    archive_game: Callable[[str, dict[str, Any]], Awaitable[Any]] = None,
) -> dict[str, Any] | None:
    """
    Apply a move to the live game state and persist the result.

    This helper no longer owns Redis or ORM directly. Callers pass in the
    persistence callbacks they want used, which makes this usable by both the
    legacy redis-based path and the new persistence/store path.
    """
    get_game = store_get or (lambda key: None)  # type: ignore[misc]
    set_game = store_set or (lambda key, state: True)  # type: ignore[misc]
    delete_game = store_delete or (lambda key: True)  # type: ignore[misc]

    game_state = await get_game(room_name)
    if not game_state:
        return None

    new_game_state = apply_move(game_state, move)
    if new_game_state is None:
        return None

    if check_game_over(new_game_state):
        if archive_game is not None:
            asyncio.create_task(archive_game(room_name, new_game_state))
        asyncio.create_task(delete_game(room_name))
    else:
        asyncio.create_task(set_game(room_name, new_game_state))

    return new_game_state
