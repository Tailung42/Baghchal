"""
Application helpers for HTTP game lifecycle endpoints.

These helpers own the game creation/join/rejoin/quick-match rules and the
live-state persistence calls behind them. They are used by the HTTP views
and can also be reused by other application code without importing DRF or
async view machinery.

Error handling is intentionally explicit so the HTTP layer can map failures
to the same status codes the existing endpoints returned.
"""

from __future__ import annotations

import asyncio
import random
import uuid

from .store import GameStateStore

_store: GameStateStore | None = None


def _store_instance() -> GameStateStore:
    global _store
    if _store is None:
        _store = GameStateStore()
    return _store


async def _set_game(game_id: str, game_state: dict) -> bool:
    return await _store_instance().set_game(game_id, game_state)


async def _get_game(game_id: str) -> dict | None:
    return await _store_instance().get_game(game_id)


async def _game_exists(game_id: str) -> bool:
    return await _store_instance().game_exists(game_id)


async def _get_all_games() -> dict[str, dict]:
    return await _store_instance().get_all_games()


async def create_game(
    username: str,
    *,
    game_id_override: str | None = None,
    player_role: str = "tiger",
    game_id_length: int = 8,
) -> str:
    """
    Create a new game and initialize it in the live store.

    Returns the created game id.
    """
    if not username:
        raise ValueError("Username required")

    game_id = game_id_override or str(uuid.uuid4())[:game_id_length]
    room_group_name = f"game_{game_id}"

    if await _game_exists(room_group_name):
        raise ValueError("Game already exists")

    initial_state = _initial_game_state()
    initial_state["player"][player_role] = username
    initial_state["game_id"] = room_group_name

    await asyncio.create_task(_set_game(room_group_name, initial_state))
    return game_id


async def join_game(game_id: str, username: str) -> str:
    """
    Join an existing waiting game as a new participant.

    Returns the joined game id.
    """
    if not game_id or not username:
        raise ValueError("Game ID and username required")

    room_group_name = f"game_{game_id}"
    game_state = await _get_game(room_group_name)

    if not game_state:
        raise ValueError("Game not found")

    game_state["game_id"] = room_group_name

    if game_state["status"] == "ongoing":
        raise ValueError("Cannot join ongoing game as new player")

    for role, player in game_state.get("player", {}).items():
        if player == username:
            raise ValueError("Cannot join a game twice")

    available_role = None
    for role, player in game_state.get("player", {}).items():
        if not player:
            available_role = role
            break

    if not available_role:
        raise ValueError("Game is full, no available roles")

    game_state["player"][available_role] = username

    if all(game_state["player"].values()):
        game_state["status"] = "ongoing"

    await asyncio.create_task(_set_game(room_group_name, game_state))
    return game_id


async def validate_rejoin(game_id: str, username: str) -> None:
    """
    Validate that the user is already part of the requested game.

    Raises ValueError when the user is not part of the game.
    """
    if not game_id or not username:
        raise ValueError("Game ID and username required")

    room_group_name = f"game_{game_id}"
    game_state = await _get_game(room_group_name)

    if not game_state:
        raise ValueError("Game not found")

    game_state["game_id"] = room_group_name

    user_role = None
    for role, player in game_state.get("player", {}).items():
        if player == username:
            user_role = role
            break

    if not user_role:
        raise ValueError("User is not part of this game")


async def quick_match(username: str, *, game_id_length: int = 8) -> str:
    """
    Find an available waiting game and join it, or create a new one.

    Returns the game id the user joined or created.
    """
    game_id, _created = await quick_match_split(username, game_id_length=game_id_length)
    return game_id


async def quick_match_split(username: str, *, game_id_length: int = 8) -> tuple[str, bool]:
    """
    Find an available waiting game and join it, or create a new one.

    Returns (game_id, created).
    """
    if not username:
        raise ValueError("Username required")

    all_games = await _get_all_games()
    waiting_games = [
        (game_id, game_state)
        for game_id, game_state in all_games.items()
        if game_state.get("status") == "waiting"
    ]

    if waiting_games:
        game_id, game_state = random.choice(waiting_games)
        game_id = game_id.replace("game_", "")

        available_role = None
        for role, player in game_state.get("player", {}).items():
            if not player:
                available_role = role
                break

        if available_role:
            game_state["player"][available_role] = username
            if all(game_state["player"].values()):
                game_state["status"] = "ongoing"
            game_state["game_id"] = f"game_{game_id}"
            await asyncio.create_task(_set_game(f"game_{game_id}", game_state))
            return game_id, False

    # No waiting games, create a new one
    game_id = str(uuid.uuid4())[:game_id_length]
    room_group_name = f"game_{game_id}"
    initial_state = _initial_game_state()
    initial_state["player"]["tiger"] = username
    initial_state["game_id"] = room_group_name
    await asyncio.create_task(_set_game(room_group_name, initial_state))
    return game_id, True


def _initial_game_state() -> dict:
    from baghchal.game_engine import get_initial_game_state

    return get_initial_game_state()


async def load_game_for_play(game_id: str) -> dict | None:
    """
    Load the live game state a player is trying to act in.
    """
    return await _get_game(game_id)


async def apply_leave(
    game_id: str,
    username: str,
    *,
    game_exists: callable = None,
    get_game: callable = None,
    set_game: callable = None,
    delete_game: callable = None,
) -> dict | None:
    """
    Apply a player leaving a game.

    Returns the updated game state, or None if the game was deleted.
    """
    exists = game_exists or _game_exists
    get = get_game or _get_game
    set_ = set_game or _set_game
    delete = delete_game or _delete_game

    if not await exists(game_id):
        return None

    game_state = await get(game_id)
    if not game_state:
        return None

    role = None
    for candidate_role, player in list(game_state.get("player", {}).items()):
        if player == username:
            role = candidate_role
            game_state["player"][candidate_role] = ""
            break

    if not any(game_state["player"].values()):
        await delete(game_id)
        return None

    await set_(game_id, game_state)
    return game_state


async def _delete_game(game_id: str) -> bool:
    return await _store_instance().delete_game(game_id)


async def finish_game(
    game_id: str,
    game_state: dict,
    *,
    archive_game: callable = None,
    delete_game: callable = None,
) -> None:
    """
    Persist a finished game and clear the live state.
    """
    archiver = archive_game or _archive_game
    deleter = delete_game or _delete_game

    await asyncio.create_task(archiver(game_id, game_state))
    await deleter(game_id)


async def _archive_game(game_id: str, game_state: dict) -> None:
    from .archival import archive_game as _real_archive

    await _real_archive(game_id, game_state)


def configure_shared_store(store: GameStateStore) -> None:
    """Wire the shared store instance used by the HTTP lifecycle helpers."""
    from .store import _set_store

    _set_store(store)

