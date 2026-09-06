"""
Tests for the game session gateway.

These tests focus on connection tracking, presence, and broadcast routing
without requiring a real channel layer.
"""

import asyncio

import pytest

from baghchal.gateway.session import ConnectionInfo, GameSession


@pytest.fixture
def loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


async def fake_broadcast(message: dict):
    fake_broadcast.last_message = message


fake_broadcast.last_message = None


async def test_session_register_and_active_players():
    session = GameSession(game_id="game_1", broadcast=fake_broadcast)
    session.register_connection("ch1", "alice", role="goat")
    session.register_connection("ch2", "bob", role="tiger")
    session.register_connection("ch3", "alice", role="goat")  # same user, second connection

    assert session.active_players() == {"alice", "bob"}
    assert session.is_empty() is False


async def test_session_remove_connection():
    session = GameSession(game_id="game_2", broadcast=fake_broadcast)
    session.register_connection("ch1", "alice", role="goat")

    removed = session.remove_connection("ch1")
    assert removed is not None
    assert removed.username == "alice"
    assert session.active_players() == set()
    assert session.is_empty() is True


async def test_session_remove_unknown_connection():
    session = GameSession(game_id="game_3", broadcast=fake_broadcast)
    assert session.remove_connection("missing") is None


async def test_session_broadcast_event():
    session = GameSession(game_id="game_4", broadcast=fake_broadcast)
    await session.broadcast_event("gameState", {"status": "ongoing"})
    assert fake_broadcast.last_message["type"] == "gameState"
    assert fake_broadcast.last_message["payload"] == {"status": "ongoing"}


async def test_session_update_heartbeat():
    session = GameSession(game_id="game_5", broadcast=fake_broadcast)
    session.register_connection("ch1", "alice")
    assert session.update_heartbeat("ch1") is True
    assert session.update_heartbeat("missing") is False


async def test_connection_info_defaults():
    conn = ConnectionInfo(username="alice")
    assert conn.username == "alice"
    assert conn.role is None
    assert conn.last_heartbeat is None
