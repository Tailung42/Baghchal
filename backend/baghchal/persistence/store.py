"""
Redis-backed game state store abstraction.

For the first surgical pass this mirrors the current Redis usage but puts it
behind a small interface so callers do not depend on raw Redis key layout or
serialization details.

Longer term this is where TTL, active-game indexing, retries, and backend
swapping would live.
"""

from __future__ import annotations

import json
import os
from typing import Any, Coroutine

import redis.asyncio as aioredis

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

GAME_KEY_PREFIX = "game:"
ACTIVE_GAME_INDEX_KEY = "active_games"


class GameStateStore:
    """
    Abstraction for live game state in Redis.

    Keys:
    - live game state: `game:<game_id>`
    - active game set: `active_games` (a Redis set of game ids)
    """

    def __init__(self, redis_client: aioredis.Redis | None = None):
        self._client = redis_client or aioredis.from_url(REDIS_URL, decode_responses=True)

    async def get_game(self, game_id: str) -> dict[str, Any] | None:
        key = f"{GAME_KEY_PREFIX}{game_id}"
        data = await self._client.get(key)
        if not data:
            return None
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None

    async def set_game(self, game_id: str, game_state: dict[str, Any]) -> bool:
        key = f"{GAME_KEY_PREFIX}{game_id}"
        try:
            await self._client.set(key, json.dumps(game_state, separators=(",", ":")))
            await self._client.sadd(ACTIVE_GAME_INDEX_KEY, game_id)
            return True
        except Exception:
            return False

    async def delete_game(self, game_id: str) -> bool:
        key = f"{GAME_KEY_PREFIX}{game_id}"
        try:
            pipeline = self._client.pipeline()
            pipeline.delete(key)
            pipeline.srem(ACTIVE_GAME_INDEX_KEY, game_id)
            await pipeline.execute()
            return True
        except Exception:
            return False

    async def game_exists(self, game_id: str) -> bool:
        key = f"{GAME_KEY_PREFIX}{game_id}"
        try:
            return await self._client.exists(key) > 0
        except Exception:
            return False

    async def list_active_games(self) -> list[str]:
        try:
            members = await self._client.smembers(ACTIVE_GAME_INDEX_KEY)
            return sorted(members)
        except Exception:
            return []

    async def get_all_games(self) -> dict[str, dict[str, Any]]:
        """
        Return every live game by game_id.

        This preserves the legacy `async_get_all_games()` contract so callers
        that already import from `baghchal.redis` can be migrated once without
        changing behavior.
        """
        try:
            keys = await self._client.keys(f"{GAME_KEY_PREFIX}*")
            games = {}
            for key in keys:
                game_id = key.removeprefix(GAME_KEY_PREFIX)
                data = await self._client.get(key)
                if data:
                    games[game_id] = json.loads(data)
            return games
        except Exception:
            return {}

    async def close(self) -> None:
        try:
            await self._client.aclose()
        except Exception:
            return


def configure_store(store: GameStateStore) -> GameStateStore:
    """
    Set the process-level store instance used by the persistence helpers.

    Call this once during app startup if you want the HTTP and WebSocket paths
    to share a single store instance.
    """
    _set_store(store)
    return store


def _set_store(store: GameStateStore) -> None:
    global _store
    _store = store


def configure_shared_store(store: GameStateStore) -> GameStateStore:
    """Public helper used by higher-level persistence modules to set the shared store."""
    _set_store(store)
    return store
