"""
End-to-end WebSocket integration tests.

These tests exercise the real transport path instead of stubbing it:

- the real ``JWTAuthMiddleware`` (JWT from subprotocol -> DB user lookup)
- the real ``AsyncGameConsumer`` connect / receive / disconnect handlers
- the real Channels channel layer (``group_add`` / ``group_send`` dispatch
  to consumer handlers)
- the real ``GameStateStore`` persistence layer (backed by fakeredis, so
  the store class and redis-py calls run for real without needing a server)

This covers the wiring that unit tests deliberately dodge: envelope
parsing, group broadcasts reaching every member, move application +
persistence, and the game-over flow.
"""

from __future__ import annotations

import asyncio

import fakeredis.aioredis
import pytest
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from backend.middleware import JWTAuthMiddleware
from baghchal.consumers import AsyncGameConsumer
from baghchal.persistence.store import GameStateStore

# Real ASGI application: JWT auth middleware -> game consumer.
application = JWTAuthMiddleware(AsyncGameConsumer.as_asgi())


def _initial_state(players: dict[str, str]) -> dict:
    state = {
        "board": {"0-0": "tiger", "0-4": "tiger", "4-0": "tiger", "4-4": "tiger"},
        "currentPlayer": "goat",
        "phase": "placement",
        "unusedGoat": 20,
        "deadGoatCount": 0,
        "status": "ongoing" if (players.get("goat") and players.get("tiger")) else "waiting",
        "winner": None,
        "newPosition": "",
        "previousPosition": "",
        "isCaptured": False,
        "player": {"goat": players.get("goat", ""), "tiger": players.get("tiger", "")},
        "history": [],
    }
    return state


async def _make_guest_user(username: str) -> str:
    """Create a guest user in the test DB and return a JWT access token."""
    User = get_user_model()
    user, _created = await asyncio.to_thread(
        User.objects.get_or_create, username=username, defaults={"is_guest": True}
    )
    return await asyncio.to_thread(
        lambda: str(RefreshToken.for_user(user).access_token)
    )


async def _seed_game(store: GameStateStore, game_id: str, state: dict) -> None:
    await store.set_game(f"game_{game_id}", state)


async def _connect(game_id: str, token: str) -> WebsocketCommunicator:
    communicator = WebsocketCommunicator(
        application,
        f"/ws/game/?game_id={game_id}",
        subprotocols=[token],
    )
    connected, _subprotocol = await communicator.connect()
    assert connected, "expected WebSocket connection to succeed"
    return communicator


async def _receive(communicator: WebsocketCommunicator, timeout: float = 2) -> dict:
    message = await communicator.receive_json_from(timeout=timeout)
    assert message is not None, "timed out waiting for a WebSocket frame"
    return message


async def _drain(communicator: WebsocketCommunicator, count: int) -> list[dict]:
    return [await _receive(communicator) for _ in range(count)]


@pytest.fixture()
async def game_store():
    """Point the consumer and persistence helpers at a fakeredis store."""
    from baghchal import consumers as consumers_module
    from baghchal.persistence import play as play_module
    from baghchal.persistence import store as store_module

    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    test_store = GameStateStore(redis_client=fake)

    old_consumer_store = consumers_module._store
    old_store_global = store_module._store
    old_play_store = play_module._default_store
    consumers_module._store = test_store
    store_module._set_store(test_store)
    play_module._default_store = test_store

    yield test_store

    consumers_module._store = old_consumer_store
    store_module._set_store(old_store_global)
    play_module._default_store = old_play_store
    await fake.aclose()


# ---------------------------------------------------------------------------
# Connection / auth
# ---------------------------------------------------------------------------


async def test_unauthenticated_connection_is_rejected(game_store):
    communicator = WebsocketCommunicator(application, "/ws/game/?game_id=room-auth")
    connected, close_code = await communicator.connect()
    assert connected is False
    assert close_code == 4001
    await communicator.disconnect()


async def test_connect_broadcasts_initial_game_state(game_store):
    token = await _make_guest_user("tiger-player")
    await _seed_game(game_store, "room-init", _initial_state({"tiger": "tiger-player"}))

    communicator = await _connect("room-init", token)
    event = await _receive(communicator)

    assert event["event"] == "gameState"
    state = event["payload"]["game_state"]
    assert state["player"]["tiger"] == "tiger-player"
    assert state["status"] == "waiting"
    await communicator.disconnect()


async def test_connect_rejects_user_not_in_game(game_store):
    token = await _make_guest_user("outsider")
    await _seed_game(game_store, "room-unauth", _initial_state({"tiger": "tiger-player"}))

    communicator = WebsocketCommunicator(
        application, "/ws/game/?game_id=room-unauth", subprotocols=[token]
    )
    connected, _ = await communicator.connect()
    assert connected

    event = await _receive(communicator)
    assert event["event"] == "error"
    assert event["payload"]["code"] == "connection_error"
    assert "participant" in event["payload"]["message"]
    await communicator.disconnect()


async def test_connect_rejects_unknown_game(game_store):
    token = await _make_guest_user("lone-player")

    communicator = WebsocketCommunicator(
        application, "/ws/game/?game_id=room-missing", subprotocols=[token]
    )
    connected, _ = await communicator.connect()
    assert connected

    event = await _receive(communicator)
    assert event["event"] == "error"
    assert event["payload"]["code"] == "connection_error"
    assert "does not exist" in event["payload"]["message"]
    await communicator.disconnect()


# ---------------------------------------------------------------------------
# Moves and room broadcasts
# ---------------------------------------------------------------------------


async def test_move_applies_and_broadcasts_to_both_players(game_store):
    tiger_token = await _make_guest_user("tiger-player")
    goat_token = await _make_guest_user("goat-player")
    await _seed_game(
        game_store,
        "room-move",
        _initial_state({"tiger": "tiger-player", "goat": "goat-player"}),
    )

    tiger = await _connect("room-move", tiger_token)
    goat = await _connect("room-move", goat_token)
    # tiger: own initial broadcast + echo when goat joined; goat: initial only
    await _drain(tiger, 2)
    await _drain(goat, 1)

    await goat.send_json_to(
        {
            "command": "move",
            "payload": {"moveType": "place", "currentPlayer": "goat", "toKey": "0-2"},
        }
    )

    for communicator in (tiger, goat):
        event = await _receive(communicator)
        assert event["event"] == "gameState"
        state = event["payload"]["game_state"]
        assert state["board"]["0-2"] == "goat"
        assert state["unusedGoat"] == 19
        assert state["currentPlayer"] == "tiger"

    # The move was persisted to the store, not just broadcast.
    persisted = await game_store.get_game("game_room-move")
    assert persisted["board"]["0-2"] == "goat"

    await tiger.disconnect()
    await goat.disconnect()


async def test_invalid_move_returns_error_frame(game_store):
    token = await _make_guest_user("goat-player")
    await _seed_game(game_store, "room-invalid", _initial_state({"goat": "goat-player"}))

    communicator = await _connect("room-invalid", token)
    await _drain(communicator, 1)

    # Placing on a corner already occupied by a tiger is invalid.
    await communicator.send_json_to(
        {
            "command": "move",
            "payload": {"moveType": "place", "currentPlayer": "goat", "toKey": "0-0"},
        }
    )

    event = await _receive(communicator)
    assert event["event"] == "error"
    assert event["payload"]["code"] == "invalid_move"
    await communicator.disconnect()


async def test_unsupported_command_returns_error_frame(game_store):
    token = await _make_guest_user("goat-player")
    await _seed_game(game_store, "room-badcmd", _initial_state({"goat": "goat-player"}))

    communicator = await _connect("room-badcmd", token)
    await _drain(communicator, 1)

    await communicator.send_json_to({"command": "start", "payload": {}})
    event = await _receive(communicator)
    assert event["event"] == "error"
    assert event["payload"]["code"] == "invalid_message"
    await communicator.disconnect()


async def test_malformed_frame_returns_error_frame(game_store):
    token = await _make_guest_user("goat-player")
    await _seed_game(game_store, "room-badjson", _initial_state({"goat": "goat-player"}))

    communicator = await _connect("room-badjson", token)
    await _drain(communicator, 1)

    await communicator.send_to(text_data="not-json")
    event = await _receive(communicator)
    assert event["event"] == "error"
    assert event["payload"]["code"] == "invalid_message"
    await communicator.disconnect()


# ---------------------------------------------------------------------------
# Game over
# ---------------------------------------------------------------------------


async def test_winning_move_broadcasts_final_state_and_game_over(game_store):
    token = await _make_guest_user("tiger-player")
    state = _initial_state({"tiger": "tiger-player", "goat": "goat-player"})
    state["board"]["0-1"] = "goat"
    state["deadGoatCount"] = 4
    state["currentPlayer"] = "tiger"
    state["phase"] = "displacement"
    state["unusedGoat"] = 0
    await _seed_game(game_store, "room-win", state)

    communicator = await _connect("room-win", token)
    await _drain(communicator, 1)

    # Winning capture: tiger at 0-0 jumps over the goat at 0-1 to 0-2.
    await communicator.send_json_to(
        {
            "command": "move",
            "payload": {
                "moveType": "capture",
                "currentPlayer": "tiger",
                "fromKey": "0-0",
                "toKey": "0-2",
            },
        }
    )

    event1 = await _receive(communicator)
    event2 = await _receive(communicator)
    assert {event1["event"], event2["event"]} == {"gameState", "gameOver"}

    final_state = next(
        e["payload"]["game_state"]
        for e in (event1, event2)
        if e["event"] == "gameState"
    )
    assert final_state["status"] == "over"
    assert final_state["winner"] == "tiger"
    assert final_state["deadGoatCount"] == 5
    assert final_state["board"]["0-2"] == "tiger"

    game_over = next(
        e["payload"] for e in (event1, event2) if e["event"] == "gameOver"
    )
    assert game_over["winner"] == "tiger"
    assert game_over["endReason"] == "goats_captured"
    await communicator.disconnect()


# ---------------------------------------------------------------------------
# Leave + legacy envelope
# ---------------------------------------------------------------------------


async def test_leave_broadcasts_player_left(game_store):
    tiger_token = await _make_guest_user("tiger-player")
    goat_token = await _make_guest_user("goat-player")
    await _seed_game(
        game_store,
        "room-leave",
        _initial_state({"tiger": "tiger-player", "goat": "goat-player"}),
    )

    tiger = await _connect("room-leave", tiger_token)
    goat = await _connect("room-leave", goat_token)
    await _drain(tiger, 2)
    await _drain(goat, 1)

    await tiger.send_json_to({"command": "leave", "payload": {}})

    for communicator in (tiger, goat):
        event = await _receive(communicator)
        assert event["event"] == "playerLeft"
        assert event["payload"]["username"] == "tiger-player"

    persisted = await game_store.get_game("game_room-leave")
    assert persisted["player"]["tiger"] == ""
    assert persisted["player"]["goat"] == "goat-player"

    await tiger.disconnect()
    await goat.disconnect()


async def test_legacy_message_envelope_is_bridged(game_store):
    token = await _make_guest_user("goat-player")
    await _seed_game(game_store, "room-legacy", _initial_state({"goat": "goat-player"}))

    communicator = await _connect("room-legacy", token)
    await _drain(communicator, 1)

    await communicator.send_json_to(
        {
            "message": {
                "type": "newMove",
                "move": {"moveType": "place", "currentPlayer": "goat", "toKey": "1-1"},
            }
        }
    )

    event = await _receive(communicator)
    assert event["event"] == "gameState"
    assert event["payload"]["game_state"]["board"]["1-1"] == "goat"
    await communicator.disconnect()