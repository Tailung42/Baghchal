"""
Tests for the persistence store abstraction.

These tests currently validate the abstraction shape and serialization
behavior. They intentionally do not require a live Redis instance in this
first surgical pass.
"""

import json

import pytest

from baghchal.persistence.store import ACTIVE_GAME_INDEX_KEY, GAME_KEY_PREFIX, GameStateStore


def test_key_prefix_constants():
    assert GAME_KEY_PREFIX == "game:"
    assert ACTIVE_GAME_INDEX_KEY == "active_games"


def test_store_serialization_compatibility():
    """
    Verify the store uses compact JSON compatible with the current game state
    shapes. This is a structural check, not an integration test.
    """
    store = GameStateStore(redis_client=object())
    sample = {
        "board": {"0-0": "tiger", "0-4": "tiger", "4-0": "tiger", "4-4": "tiger"},
        "currentPlayer": "goat",
        "phase": "placement",
        "unusedGoat": 20,
        "deadGoatCount": 0,
        "status": "waiting",
        "winner": None,
        "player": {"goat": "alice", "tiger": "bob"},
        "history": [],
    }

    encoded = json.dumps(sample, separators=(",", ":"))
    decoded = json.loads(encoded)
    assert decoded == sample


class DummyRedis:
    """
    Minimal dummy async Redis client for interface-shape checks only.
    """

    def __init__(self):
        self.data = {}
        self.smembers_result = set()

    async def get(self, key):
        return self.data.get(key)

    async def set(self, key, value):
        self.data[key] = value

    async def exists(self, key):
        return 1 if key in self.data else 0

    async def sadd(self, key, member):
        self.smembers_result.add(member)

    async def srem(self, key, member):
        self.smembers_result.discard(member)

    async def delete(self, key):
        self.data.pop(key, None)

    async def smembers(self, key):
        return self.smembers_result

    async def pipeline(self):
        return DummyPipeline(self)


class DummyPipeline:
    def __init__(self, redis):
        self.redis = redis
        self._ops = []

    def delete(self, key):
        self._ops.append(("delete", key))

    def srem(self, key, member):
        self._ops.append(("srem", key, member))

    async def execute(self):
        for op in self._ops:
            if op[0] == "delete":
                self.redis.data.pop(op[1], None)


def test_store_interface_shape():
    """
    Verify the public store interface exists and has the expected methods.
    """
    store = GameStateStore(redis_client=object())
    assert hasattr(store, "get_game")
    assert hasattr(store, "set_game")
    assert hasattr(store, "delete_game")
    assert hasattr(store, "game_exists")
    assert hasattr(store, "list_active_games")
    assert callable(store.get_game)
    assert callable(store.set_game)
    assert callable(store.delete_game)
    assert callable(store.game_exists)
    assert callable(store.list_active_games)
