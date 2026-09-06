"""
Application glue that makes the bot play inside a real game room.

After a human move (or a connection that finds the bot on move), this
schedules the bot's reply through the same move pipeline the human uses, so
persistence, archival, and events behave identically for both sides.
"""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable

from . import BOT_REPLY_DELAY_MS, BOT_USERNAME
from .bot import choose_bot_move

# Per-room locks keep a single bot reply in flight per game, even when
# several connections trigger the check at once (e.g. a reconnect while the
# bot is already thinking).
_bot_locks: dict[str, asyncio.Lock] = {}


async def maybe_trigger_bot_reply(
    game_state: dict[str, Any],
    *,
    game_id: str,
    get_game: Callable[[str], Awaitable[dict[str, Any] | None]],
    apply_and_broadcast: Callable[[dict[str, Any]], Awaitable[dict[str, Any] | None]],
    bot_username: str = BOT_USERNAME,
    delay_ms: float | None = None,
) -> None:
    """
    If the position leaves the bot to move, compute and apply its move.

    ``apply_and_broadcast`` receives the bot's chosen move and is expected to
    apply it through the normal move pipeline and broadcast the resulting
    ``gameState`` / ``gameOver`` events.

    The current position is re-read from the store under a per-room lock both
    before and after the thinking delay, so two triggers can never double-move
    and the bot never acts on a stale or finished game.
    """
    bot = game_state.get("bot")
    if not bot or game_state.get("status") == "over":
        return
    if game_state.get("currentPlayer") != bot.get("role"):
        return

    delay = BOT_REPLY_DELAY_MS if delay_ms is None else delay_ms
    lock = _bot_locks.setdefault(game_id, asyncio.Lock())

    async with lock:
        fresh = await get_game(game_id)
        if not fresh or fresh.get("status") == "over":
            return
        if fresh.get("currentPlayer") != bot.get("role"):
            return

        await asyncio.sleep(delay / 1000.0)

        # Re-read after the pause: the human may have moved or the game may
        # have ended while we waited.
        fresh = await get_game(game_id)
        if not fresh or fresh.get("status") == "over":
            return
        if fresh.get("currentPlayer") != bot.get("role"):
            return

        move = choose_bot_move(fresh, difficulty=bot.get("difficulty") or "medium")
        if move is None:
            return
        await apply_and_broadcast(move)