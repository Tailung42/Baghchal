"""
Tests for the game gateway.

These tests verify dispatch responses, broadcast routing, and session
lifecycle behavior using the in-memory gateway.
"""

import asyncio

import pytest

from baghchal.gateway.game_gateway import GameGateway
from baghchal.gateway.session import GameSession


@pytest.fixture
def loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


async def fake_broadcast(message: dict):
    fake_broadcast.last_message = message


fake_broadcast.last_message = None


def _reset_fake_broadcast():
    fake_broadcast.last_message = None


async def test_gateway_ensure_session():
    gateway = GameGateway()
    session = gateway.ensure_session("game_1", fake_broadcast)
    assert isinstance(session, GameSession)
    assert session.game_id == "game_1"

    same = gateway.get_session("game_1")
    assert same is session


async def test_gateway_broadcast_when_session_exists():
    gateway = GameGateway()
    gateway.ensure_session("game_1", fake_broadcast)

    await gateway.broadcast("game_1", "gameState", {"status": "ongoing"})
    assert fake_broadcast.last_message["type"] == "gameState"
    assert fake_broadcast.last_message["payload"] == {"status": "ongoing"}


async def test_gateway_broadcast_when_session_missing():
    gateway = GameGateway()
    _reset_fake_broadcast()
    await gateway.broadcast("missing", "gameState", {"status": "ongoing"})
    assert fake_broadcast.last_message is None


async def test_dispatch_invalid_command():
    gateway = GameGateway()
    gateway.ensure_session("game_1", fake_broadcast)

    result = await gateway.dispatch("game_1", "alice", "unknown", {})
    assert result["ok"] is False
    assert result["error_code"] == "invalid_message"


async def test_dispatch_game_not_found():
    gateway = GameGateway()
    _reset_fake_broadcast()
    result = await gateway.dispatch("missing", "alice", "move", {})
    assert result["ok"] is False
    assert result["error_code"] == "game_not_found"


async def test_dispatch_not_in_game():
    gateway = GameGateway()
    gateway.ensure_session("game_1", fake_broadcast)

    result = await gateway.dispatch("game_1", "alice", "move", {})
    assert result["ok"] is False
    assert result["error_code"] == "not_in_game"


async def test_dispatch_valid_command():
    gateway = GameGateway()
    session = gateway.ensure_session("game_1", fake_broadcast)
    session.register_connection("ch1", "alice", role="goat")

    result = await gateway.dispatch("game_1", "alice", "move", {"fromKey": "0-0", "toKey": "0-1"})
    assert result["ok"] is True
    assert result["action"] == "move"
