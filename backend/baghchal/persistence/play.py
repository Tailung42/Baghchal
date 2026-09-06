"""
Persistence orchestration for real-time play commands.

This layer sits between the gateway and the live-state store/archival layer.
It owns the "what happens to live game state when a player moves, leaves, or
disconnects" logic for WebSocket play.

The consumer should delegate to these helpers instead of mutating game state
or scheduling persistence directly.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from .views import (
    apply_leave as _apply_leave,
    finish_game as _finish_game,
    load_game_for_play as _load_game_for_play,
    _get_game as _real_get_game,
    _set_game as _real_set_game,
    _delete_game as _real_delete_game,
    _archive_game as _real_archive_game,
)

from .store import GameStateStore, configure_shared_store

_default_store: GameStateStore | None = None


def configure_store(store: GameStateStore) -> None:
    global _default_store
    _default_store = store
    configure_shared_store(store)


async def _resolve_store() -> GameStateStore:
    from .store import _store

    if _store is not None:
        return _store

    from .views import _store_instance

    return await _store_instance()



async def load_game(game_id: str) -> dict[str, Any] | None:
    from .store import _store

    store = _store
    if store is None:
        store = await _resolve_store()

    return await store.get_game(game_id)


async def execute_leave(
    game_id: str,
    username: str,
    *,
    on_left: Callable[[dict[str, Any], str, str | None], Any] | None = None,
    game_exists: Callable[[str], Awaitable[bool]] | None = None,
    get_game: Callable[[str], Awaitable[dict[str, Any] | None]] | None = None,
    set_game: Callable[[str, dict[str, Any]], Awaitable[bool]] | None = None,
    delete_game: Callable[[str], Awaitable[bool]] | None = None,
    store: GameStateStore | None = None,
) -> dict[str, Any] | None:
    """
    Apply a leave command to the live game state.

    If `on_left` is provided it is called with (game_state, username, role)
    before the state is written or deleted, so the transport layer can emit
    the appropriate event without the persistence layer knowing about Channels.
    """
    if store is None:
        store = await _resolve_store()

    game_state = await _apply_leave(
        game_id,
        username,
        game_exists=game_exists or store.game_exists,
        get_game=get_game or store.get_game,
        set_game=set_game or store.set_game,
        delete_game=delete_game or store.delete_game,
    )

    if game_state is None:
        return None

    if on_left is not None:
        await on_left(game_state, username, None)

    return game_state


async def execute_move(
    game_id: str,
    username: str,
    payload: dict[str, Any],
    *,
    get_game: Callable[[str], Awaitable[dict[str, Any] | None]] = None,
    set_game: Callable[[str, dict[str, Any]], Awaitable[bool]] = None,
    delete_game: Callable[[str], Awaitable[bool]] = None,
    archive_game: Callable[[str, dict[str, Any]], Awaitable[Any]] = None,
    store: GameStateStore | None = None,
) -> dict[str, Any] | None:
    """
    Apply a move command to the live game state.

    Returns the updated game state, or None when the move was not applied.
    """
    from baghchal.game_engine import async_update_game_state as _async_update_game_state

    if store is None:
        store = await _resolve_store()

    new_game_state = await _async_update_game_state(
        game_id,
        payload,
        store_get=get_game or store.get_game,
        store_set=set_game or store.set_game,
        store_delete=delete_game or store.delete_game,
        archive_game=archive_game or _real_archive_game,
    )

    return new_game_state


async def disconnect_game(
    game_id: str,
    *,
    session_is_empty: Callable[[], bool] = None,
    session_player_count: Callable[[], int] = None,
    delete_game: Callable[[str], Awaitable[bool]] = None,
    set_game: Callable[[str, dict[str, Any]], Awaitable[bool]] = None,
    store: GameStateStore | None = None,
) -> dict[str, Any] | None:
    """
    Apply disconnect-side cleanup for a game room.

    Returns the updated game state when the room was reset to waiting, or None
    when the game was deleted or left unchanged.
    """
    if store is None:
        store = await _resolve_store()

    is_empty = session_is_empty or (lambda: True)
    player_count = session_player_count or (lambda: 0)
    delete = delete_game or store.delete_game
    set_ = set_game or store.set_game

    if is_empty():
        await delete(game_id)
        return None

    if player_count() == 0:
        updated = {
            "player": {
                "goat": "",
                "tiger": "",
            },
            "status": "waiting",
        }
        await set_(game_id, updated)
        return updated

    return None
