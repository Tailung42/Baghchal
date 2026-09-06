import json
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

from . import gateway
from .bot import BOT_USERNAME
from .bot.integration import maybe_trigger_bot_reply
from .gateway.integration import attach_session
from .gateway.managers import game_gateway
from .persistence.play import configure_store as configure_play_store
from .persistence.play import disconnect_game, execute_leave, execute_move, load_game
from .persistence.store import GameStateStore, configure_store

_store = GameStateStore()
configure_store(_store)
configure_play_store(_store)


def _gateway_error_for_code(code: str) -> gateway.errors.GatewayError:
    """
    Map a gateway error code to the corresponding GatewayError object.

    This keeps the consumer error responses aligned with the gateway error
    taxonomy instead of ad-hoc strings.
    """
    error_map = {
        "invalid_message": gateway.errors.INVALID_MESSAGE,
        "not_authenticated": gateway.errors.NOT_AUTHENTICATED,
        "not_in_game": gateway.errors.NOT_IN_GAME,
        "not_your_turn": gateway.errors.NOT_YOUR_TURN,
        "invalid_move": gateway.errors.INVALID_MOVE,
        "game_not_found": gateway.errors.GAME_NOT_FOUND,
        "game_already_over": gateway.errors.GAME_ALREADY_OVER,
        "connection_error": gateway.errors.CONNECTION_ERROR,
    }
    return error_map.get(code, gateway.errors.INVALID_MESSAGE)


class AsyncGameConsumer(AsyncWebsocketConsumer):
    """
    Transport adapter for real-time play.

    Responsibilities:
    - authenticate the WebSocket connection
    - attach the channel to a gateway session
    - translate inbound frames into commands
    - send outbound event/error frames
    - delegate play lifecycle to the persistence layer

    Game rule logic and persistence orchestration do not live here.
    """

    _gateway = game_gateway

    async def connect(self):
        query = parse_qs(self.scope["query_string"].decode())
        self.game_id = query.get("game_id", [None])[0]

        user = self.scope["user"]
        if isinstance(user, AnonymousUser) or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.username = user.username
        self._session = None

        try:
            # Echo the requested subprotocol (the JWT access token) back to
            # the client, otherwise browsers reject the handshake with
            # "non-empty Sec-WebSocket-Protocol header but no response".
            subprotocols = self.scope.get("subprotocols", [])
            await self.accept(
                subprotocol=subprotocols[0] if subprotocols else None
            )
            await self.setup_session()
        except Exception as e:
            await self.close_with_error(str(e))
            return

    async def setup_session(self):
        if not self.username:
            raise gateway.errors.NOT_AUTHENTICATED
        if not self.game_id:
            raise gateway.errors.CONNECTION_ERROR

        self.room_group_name = f"game_{self.game_id}"

        if not await _store.game_exists(self.room_group_name):
            raise gateway.errors.GAME_NOT_FOUND

        game_state = await _store.get_game(self.room_group_name)
        if not game_state:
            raise gateway.errors.CONNECTION_ERROR

        user_is_player = any(
            player == self.username
            for player in game_state.get("player", {}).values()
        )
        if not user_is_player:
            raise gateway.errors.NOT_IN_GAME

        role = self._player_role(game_state)
        self._session = attach_session(
            self._gateway,
            self.room_group_name,
            self._broadcast,
            self.channel_name,
            self.username,
            role=role,
        )

        # Join the Channels group so broadcasts reach this connection.
        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )

        await self._session.broadcast_event("gameState", game_state)

        # If the bot is on move (e.g. the human chose tigers, so the goat bot
        # opens), have the bot reply right away.
        await maybe_trigger_bot_reply(
            game_state,
            game_id=self.room_group_name,
            get_game=load_game,
            apply_and_broadcast=lambda move: self._apply_move_and_broadcast(
                BOT_USERNAME, move
            ),
        )

    def _broadcast(self, event: dict):
        return self._channel_group_send(self.room_group_name, event)

    async def _channel_group_send(self, group_name: str, event: dict):
        await self.channel_layer.group_send(group_name, event)

    def _player_role(self, game_state: dict):
        for role, player in game_state.get("player", {}).items():
            if player == self.username:
                return role
        return None

    @staticmethod
    def _from_user_message_static(message: dict):
        """Bridge legacy 'message' envelopes to the new command envelope shape."""
        command = message.get("type")
        if command == "newMove":
            return {"command": "move", "payload": message.get("move", {})}
        if command == "exitGame":
            return {"command": "leave", "payload": {}}
        return {"command": command, "payload": message}

    async def receive(self, text_data):
        try:
            parsed = json.loads(text_data)
        except (json.JSONDecodeError, ValueError):
            await self.send_error(gateway.errors.INVALID_MESSAGE)
            return

        message = parsed.get("message")
        if isinstance(message, dict):
            # Legacy envelope: {"message": {"type": ..., "move": ...}}
            envelope = self._from_user_message_static(message)
        else:
            # New envelope: {"command": ..., "payload": ...}
            try:
                envelope = gateway.commands.parse_client_envelope(parsed)
            except ValueError:
                await self.send_error(gateway.errors.INVALID_MESSAGE)
                return

        command = envelope["command"]
        payload = envelope["payload"]

        result = await self._gateway.dispatch(
            self.room_group_name,
            self.username,
            command,
            payload,
        )

        if not result.get("ok"):
            error_code = result.get("error_code", "invalid_message")
            error = _gateway_error_for_code(error_code)
            await self.send_error(error)
            return

        if command == "leave":
            await self._handle_leave()
        elif command == "move":
            await self._handle_move(payload)
        else:
            await self.send_error(gateway.errors.INVALID_MESSAGE)

    async def _handle_leave(self):
        await execute_leave(
            self.room_group_name,
            self.username,
            on_left=self._emit_player_left,
        )

    async def _emit_player_left(self, game_state: dict, username: str, role: str | None):
        if role is None:
            role = self._player_role(game_state)
        await self._session.broadcast_event(
            "playerLeft",
            {"username": username, "role": role},
        )

    async def _apply_move_and_broadcast(
        self,
        username: str,
        payload: dict,
    ) -> dict | None:
        """
        Apply a move through the normal pipeline and broadcast the result.

        Used by the human's ``move`` command and by the bot's replies, so
        both sides persist and broadcast identically. Returns the new game
        state, or None when the move was rejected.
        """
        new_game_state = await execute_move(
            self.room_group_name,
            username,
            payload,
            archive_game=self._archive_game,
        )

        if new_game_state is None:
            return None

        if new_game_state.get("status") == "over":
            # Broadcast the final board first so every client sees the last
            # move and a game state marked as over; then announce the winner.
            await self._session.broadcast_event("gameState", new_game_state)
            await self._session.broadcast_event(
                "gameOver",
                {
                    "winner": new_game_state.get("winner"),
                    "endReason": _end_reason_for(new_game_state),
                },
            )
            return new_game_state

        await self._session.broadcast_event("gameState", new_game_state)
        return new_game_state

    async def _handle_move(self, payload):
        new_game_state = await self._apply_move_and_broadcast(self.username, payload)
        if new_game_state is None:
            await self.send_error(gateway.errors.INVALID_MOVE)
            return

        # If the move leaves the bot to move, let the bot reply.
        await maybe_trigger_bot_reply(
            new_game_state,
            game_id=self.room_group_name,
            get_game=load_game,
            apply_and_broadcast=lambda move: self._apply_move_and_broadcast(
                BOT_USERNAME, move
            ),
        )

    async def _archive_game(self, game_id: str, game_state: dict):
        from .persistence.archival import archive_game as _archive

        await _archive(game_id, game_state)

    async def handle_disconnect(self):
        if not hasattr(self, "room_group_name"):
            return

        session = getattr(self, "_session", None)
        if session is None:
            return

        conn = session.remove_connection(self.channel_name)
        if conn and conn.username:
            await session.broadcast_event(
                "playerDisconnected",
                {"username": conn.username, "role": conn.role},
            )

            await disconnect_game(
                self.room_group_name,
                session_is_empty=session.is_empty,
                session_player_count=session.player_count,
            )

    async def disconnect(self, close_code):
        await self.handle_disconnect()
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    # ------------------------------------------------------------------
    # Channel-layer event handlers.
    #
    # The gateway session broadcasts to the room group with
    # {"type": <event_type>, "payload": ...}. Channels dispatches group
    # events to consumer methods by exact type name (dots replaced by
    # underscores), so these handlers must match the event types emitted
    # by the session: gameState, playerLeft, playerDisconnected, gameOver.
    # ------------------------------------------------------------------

    async def gameState(self, event):
        await self.send(
            text_data=json.dumps(
                {"event": "gameState", "payload": {"game_state": event["payload"]}}
            )
        )

    async def playerLeft(self, event):
        await self.send(
            text_data=json.dumps(
                {"event": "playerLeft", "payload": event["payload"]}
            )
        )

    async def playerDisconnected(self, event):
        await self.send(
            text_data=json.dumps(
                {"event": "playerDisconnected", "payload": event["payload"]}
            )
        )

    async def gameOver(self, event):
        await self.send(
            text_data=json.dumps(
                {"event": "gameOver", "payload": event["payload"]}
            )
        )

    async def send_error(self, error):
        await self.send(
            text_data=json.dumps(
                gateway.commands.make_error_event(error.code, error.message)
            )
        )

    async def close_with_error(self, message):
        await self.send(
            text_data=json.dumps(
                gateway.commands.make_event(
                    "error", {"code": "connection_error", "message": message}
                )
            )
        )
        await self.close(4000)


def _end_reason_for(game_state: dict):
    """Derive a simple end reason from the final game state for gameOver events."""
    if game_state.get("winner") == "tiger":
        return "goats_captured"
    if game_state.get("winner") == "goat":
        return "tigers_blocked"
    return "unknown"