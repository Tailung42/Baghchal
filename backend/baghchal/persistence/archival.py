"""
Persistence helpers for archiving finished games into the Django ORM.

This layer is intentionally separate from the live-state store. Live state
stays in Redis; completed-game records live in the ORM so they can be queried
later without keeping Redis entries alive forever.
"""

from __future__ import annotations

import asyncio
from datetime import datetime

from baghchal.models import Game
from core.models import User


def _get_user_by_username(username: str) -> User | None:
    """
    Resolve a username to a User for archival.

    Returns None when the user does not exist yet, so archival can still
    record the game result without crashing if a user was deleted.
    """
    if not username:
        return None
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        return None


async def archive_game(game_id: str, game_state: dict) -> Game:
    """
    Persist a finished game to the ORM and return the created record.

    This should only be called after the game is known to be over and the
    Redis live state has already been cleared or scheduled for cleanup.
    """
    winner_role = game_state["winner"]
    dead_goats = game_state["deadGoatCount"]

    goat_user = await asyncio.to_thread(
        _get_user_by_username, game_state["player"]["goat"]
    )
    tiger_user = await asyncio.to_thread(
        _get_user_by_username, game_state["player"]["tiger"]
    )

    game = Game(
        game_id=game_id,
        goat_player=goat_user,
        tiger_player=tiger_user,
        winner_role=winner_role,
        total_moves=len(game_state["history"]),
        goats_captured=dead_goats,
        created_at=datetime.now(),
    )
    await asyncio.to_thread(game.save)
    return game
