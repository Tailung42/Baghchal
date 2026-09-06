"""
Tests for playing against the server-side bot: game creation (persistence +
HTTP view) and the consumer hook that makes the bot reply after human moves
over the real WebSocket pipeline.
"""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import fakeredis.aioredis
import pytest
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from django.urls import include, path
from rest_framework_simplejwt.tokens import RefreshToken

from backend.middleware import JWTAuthMiddleware
from baghchal.bot import BOT_USERNAME
from baghchal.consumers import AsyncGameConsumer
from baghchal.game_engine import generate_moves
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


def _bot_game_state(human_role: str, difficulty: str = "easy") -> dict:
    bot_role = "goat" if human_role == "tiger" else "tiger"
    state = _initial_state(
        {"goat": "goat-player" if bot_role == "tiger" else BOT_USERNAME,
         "tiger": "tiger-player" if bot_role == "goat" else BOT_USERNAME}
    )
    state["status"] = "ongoing"
    state["opponent_type"] = "bot"
    state["bot"] = {"role": bot_role, "difficulty": difficulty}
    return state


# ---------------------------------------------------------------------------
# Persistence: create_bot_game
# ---------------------------------------------------------------------------


async def _fake_views_store(monkeypatch) -> GameStateStore:
    from baghchal.persistence import views as persistence_views

    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    store = GameStateStore(redis_client=fake)
    monkeypatch.setattr(persistence_views, "_store", store)
    return store


@pytest.mark.asyncio
async def test_create_bot_game_seeds_live_store(monkeypatch):
    from baghchal.persistence import views as persistence_views

    store = await _fake_views_store(monkeypatch)

    game_id = await persistence_views.create_bot_game(
        "alice", player_role="tiger", difficulty="easy"
    )
    await asyncio.sleep(0.01)  # the store write happens in a background task

    state = await store.get_game(f"game_{game_id}")
    assert state is not None
    assert state["status"] == "ongoing"
    assert state["player"]["tiger"] == "alice"
    assert state["player"]["goat"] == BOT_USERNAME
    assert state["opponent_type"] == "bot"
    assert state["bot"] == {"role": "goat", "difficulty": "easy"}
    # The human is tiger, so the goat bot opens.
    assert state["currentPlayer"] == "goat"


@pytest.mark.asyncio
async def test_create_bot_game_human_goat_means_bot_tiger_opens_last(monkeypatch):
    from baghchal.persistence import views as persistence_views

    store = await _fake_views_store(monkeypatch)

    game_id = await persistence_views.create_bot_game(
        "bob", player_role="goat", difficulty="hard"
    )
    await asyncio.sleep(0.01)

    state = await store.get_game(f"game_{game_id}")
    assert state["player"]["goat"] == "bob"
    assert state["player"]["tiger"] == BOT_USERNAME
    assert state["bot"] == {"role": "tiger", "difficulty": "hard"}
    # Human goat opens; the bot only moves after the human's first move.
    assert state["currentPlayer"] == "goat"


@pytest.mark.asyncio
async def test_create_bot_game_rejects_invalid_role_and_difficulty(monkeypatch):
    from baghchal.persistence import views as persistence_views

    await _fake_views_store(monkeypatch)

    with pytest.raises(ValueError):
        await persistence_views.create_bot_game("alice", player_role="queen")
    with pytest.raises(ValueError):
        await persistence_views.create_bot_game("alice", difficulty="nightmare")


# ---------------------------------------------------------------------------
# HTTP view
# ---------------------------------------------------------------------------


class BotGameViewTestCase(TransactionTestCase):
    databases = ["default"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = get_user_model().objects.create_user(
            username="botuser", password="testpass"
        )

    def setUp(self):
        from rest_framework.test import APIClient

        super().setUp()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def _override_root_urls(self):
        class _IncludedBaghchalURLConf:
            urlpatterns = [path("game/", include("baghchal.urls"))]

        return _IncludedBaghchalURLConf

    def test_start_bot_game_returns_game_id(self):
        with patch(
            "baghchal.persistence.views.create_bot_game", return_value="bot12345"
        ) as mocked:
            with self.settings(ROOT_URLCONF=self._override_root_urls()):
                response = self.client.post(
                    "/game/bot/",
                    {"player_role": "goat", "difficulty": "hard"},
                    format="json",
                )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, {"game_id": "bot12345"})
        mocked.assert_called_once_with(
            "botuser", player_role="goat", difficulty="hard", game_id_length=8
        )

    def test_start_bot_game_defaults_role_and_difficulty(self):
        with patch(
            "baghchal.persistence.views.create_bot_game", return_value="bot12345"
        ) as mocked:
            with self.settings(ROOT_URLCONF=self._override_root_urls()):
                response = self.client.post("/game/bot/", {}, format="json")

        self.assertEqual(response.status_code, 201)
        mocked.assert_called_once_with(
            "botuser", player_role="tiger", difficulty="medium", game_id_length=8
        )

    def test_start_bot_game_invalid_difficulty_is_400(self):
        with patch(
            "baghchal.persistence.views.create_bot_game",
            side_effect=ValueError("Invalid difficulty"),
        ):
            with self.settings(ROOT_URLCONF=self._override_root_urls()):
                response = self.client.post(
                    "/game/bot/", {"difficulty": "nightmare"}, format="json"
                )
        self.assertEqual(response.status_code, 400)


# ---------------------------------------------------------------------------
# Consumer: bot replies over the WebSocket
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bot_opens_when_human_is_tiger_and_replies_after_each_move(
    game_store, monkeypatch
):
    monkeypatch.setattr("baghchal.bot.integration.BOT_REPLY_DELAY_MS", 1.0)

    token = await _make_guest_user("tiger-player")
    state = _bot_game_state("tiger")
    await _seed_game(game_store, "room-bot", state)

    communicator = await _connect("room-bot", token)

    # 1) initial broadcast, 2) the goat bot's opening placement.
    event1 = await _receive(communicator)
    event2 = await _receive(communicator)
    assert event1["event"] == "gameState"
    assert event2["event"] == "gameState"
    after_bot_open = event2["payload"]["game_state"]
    assert after_bot_open["currentPlayer"] == "tiger"
    assert any(v == "goat" for v in after_bot_open["board"].values())

    # Human (tiger) makes a legal slide; the bot (goat) must reply.
    tiger_slide = next(
        m
        for m in generate_moves(after_bot_open)
        if m["currentPlayer"] == "tiger" and m["moveType"] == "displace"
    )
    await communicator.send_json_to({"command": "move", "payload": tiger_slide})

    event3 = await _receive(communicator)  # human move broadcast
    event4 = await _receive(communicator)  # bot reply broadcast
    assert event3["event"] == "gameState"
    assert event3["payload"]["game_state"]["currentPlayer"] == "goat"
    assert event4["event"] == "gameState"
    bot_reply = event4["payload"]["game_state"]
    assert bot_reply["currentPlayer"] == "tiger"
    assert bot_reply["history"][-1].startswith("goat")

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_bot_does_not_reply_in_normal_human_game(game_store, monkeypatch):
    monkeypatch.setattr("baghchal.bot.integration.BOT_REPLY_DELAY_MS", 5.0)

    token = await _make_guest_user("tiger-player")
    state = _initial_state({"tiger": "tiger-player"})  # no bot metadata
    await _seed_game(game_store, "room-normal", state)

    communicator = await _connect("room-normal", token)

    event = await _receive(communicator)
    assert event["event"] == "gameState"

    # No bot metadata -> no extra frame should arrive.
    assert await communicator.receive_nothing(timeout=0.3) is True

    await communicator.disconnect()