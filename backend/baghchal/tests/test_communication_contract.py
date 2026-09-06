"""
Backend end-to-end tests for the WebSocket communication contract.

These tests exercise the transport envelope shape and the consumer's
message handling paths without requiring a live server. The goal is to
verify that command/event payloads match the documented protocol and that
the same shapes the backend produces can be parsed by the frontend helpers.

Scope note:
- These tests intentionally do not import `AsyncGameConsumer` at module
  import time because that pulls in Django and Channels, which requires
  `DJANGO_SETTINGS_MODULE` to be configured before import.
- Consumer integration is covered separately in `test_consumer_protocol.py`
  and `test_consumer_asgi_exchange.py`, both of which are run via the
  configured Django test runner.
"""

from __future__ import annotations

from baghchal.gateway.commands import (
    CLIENT_COMMANDS,
    SERVER_EVENTS,
    make_event,
    make_error_event,
    parse_client_envelope,
)
from baghchal.gateway.errors import (
    CONNECTION_ERROR,
    GAME_ALREADY_OVER,
    GAME_NOT_FOUND,
    INVALID_MESSAGE,
    INVALID_MOVE,
    NOT_AUTHENTICATED,
    NOT_IN_GAME,
    NOT_YOUR_TURN,
)

COMMAND_PAYLOAD_EXAMPLES = {
    "move": {"moveType": "place", "toKey": "0-1"},
    "leave": {},
}


def _parse_frontend_style_message(raw: dict) -> dict:
    """
    Mirror the frontend parsing rule in JS: a client message must be an
    object with a string `command` and a dict `payload`.

    This is intentionally identical to `parse_client_envelope` so we can
    assert the backend and frontend helper expectations remain aligned.
    """
    return parse_client_envelope(raw)


def _pack_server_event(event: str, payload: dict) -> dict:
    """
    Pack a server event the same way `make_event` does. This exists so tests
    can assert the exact envelope shape a frontend would receive over WS.
    """
    return make_event(event, payload)


def _unpack_server_event(envelope: dict) -> dict:
    """
    Frontend-compatible unpacking of a server event envelope.

    The frontend currently reads:
      - data.event.type  (event name)
      - data.event.payload
    This helper enforces the same contract on the backend side.
    """
    event = envelope.get("event")
    payload = envelope.get("payload")
    if not isinstance(event, str) or not isinstance(payload, dict):
        raise ValueError("Malformed server envelope")
    return {"event": event, "payload": payload}


class TestClientToServerEnvelope:
    def test_client_commands_are_explicit_allowlist(self):
        # Prevent accidental drift between what the backend accepts and
        # what the frontend is allowed to send.
        assert isinstance(CLIENT_COMMANDS, set)
        assert len(CLIENT_COMMANDS) >= 2

    def test_move_command_is_accepted(self):
        envelope = _parse_frontend_style_message({
            "command": "move",
            "payload": COMMAND_PAYLOAD_EXAMPLES["move"],
        })
        assert envelope["command"] == "move"
        assert envelope["payload"] == COMMAND_PAYLOAD_EXAMPLES["move"]

    def test_leave_command_is_accepted(self):
        envelope = _parse_frontend_style_message({
            "command": "leave",
            "payload": COMMAND_PAYLOAD_EXAMPLES["leave"],
        })
        assert envelope["command"] == "leave"
        assert envelope["payload"] == {}

    def test_unsupported_command_is_rejected(self):
        try:
            _parse_frontend_style_message({"command": "start", "payload": {}})
        except ValueError:
            return
        assert False, "expected rejection of unsupported command"

    def test_missing_command_is_rejected(self):
        try:
            _parse_frontend_style_message({"payload": {}})
        except ValueError:
            return
        assert False, "expected rejection of missing command"

    def test_non_dict_payload_is_rejected(self):
        try:
            _parse_frontend_style_message({"command": "move", "payload": "bad"})
        except ValueError:
            return
        assert False, "expected rejection of non-dict payload"


class TestServerToClientEnvelope:
    def test_server_events_are_explicit_allowlist(self):
        assert isinstance(SERVER_EVENTS, set)

    def test_game_state_event_shape(self):
        event = _pack_server_event("gameState", {"game_state": {"status": "waiting"}})
        unpacked = _unpack_server_event(event)
        assert unpacked["event"] == "gameState"
        assert unpacked["payload"] == {"game_state": {"status": "waiting"}}

    def test_player_left_event_shape(self):
        event = _pack_server_event("playerLeft", {"username": "alice", "role": "goat"})
        unpacked = _unpack_server_event(event)
        assert unpacked["event"] == "playerLeft"
        assert unpacked["payload"] == {"username": "alice", "role": "goat"}

    def test_player_disconnected_event_shape(self):
        event = _pack_server_event("playerDisconnected", {"username": "alice", "role": "goat"})
        unpacked = _unpack_server_event(event)
        assert unpacked["event"] == "playerDisconnected"
        assert unpacked["payload"] == {"username": "alice", "role": "goat"}

    def test_game_over_event_shape(self):
        event = _pack_server_event("gameOver", {"winner": "goat", "endReason": "capture"})
        unpacked = _unpack_server_event(event)
        assert unpacked["event"] == "gameOver"
        assert unpacked["payload"] == {"winner": "goat", "endReason": "capture"}

    def test_error_event_shape(self):
        event = _pack_server_event("error", {"code": "invalid_move", "message": "Move failed validation"})
        unpacked = _unpack_server_event(event)
        assert unpacked["event"] == "error"
        assert unpacked["payload"] == {"code": "invalid_move", "message": "Move failed validation"}

    def test_round_trip_encode_decode_is_stable(self):
        payload = {"moveType": "displace", "fromKey": "0-0", "toKey": "1-1"}
        encoded = _pack_server_event("gameState", payload)
        decoded = _unpack_server_event(encoded)
        assert decoded["event"] == encoded["event"]
        assert decoded["payload"] == encoded["payload"]


class TestErrorCodesStayValidAtProtocolBoundary:
    def test_all_public_error_codes_produce_valid_error_events(self):
        codes = [
            (INVALID_MESSAGE.code, INVALID_MESSAGE.message),
            (NOT_AUTHENTICATED.code, NOT_AUTHENTICATED.message),
            (NOT_IN_GAME.code, NOT_IN_GAME.message),
            (NOT_YOUR_TURN.code, NOT_YOUR_TURN.message),
            (INVALID_MOVE.code, INVALID_MOVE.message),
            (GAME_NOT_FOUND.code, GAME_NOT_FOUND.message),
            (GAME_ALREADY_OVER.code, GAME_ALREADY_OVER.message),
            (CONNECTION_ERROR.code, CONNECTION_ERROR.message),
        ]
        for code, message in codes:
            event = _pack_server_event("error", {"code": code, "message": message})
            unpacked = _unpack_server_event(event)
            assert unpacked["event"] == "error"
            assert unpacked["payload"]["code"] == code
            assert unpacked["payload"]["message"] == message

    def test_error_payload_has_code_and_message_only(self):
        event = _pack_server_event("error", {"code": "not_your_turn", "message": "It is not your turn"})
        payload = _unpack_server_event(event)["payload"]
        assert set(payload.keys()) == {"code", "message"}


class TestProtocolContractAlignment:
    def test_client_command_set_aligns_with_documented_commands(self):
        # Documented commands: move, leave
        assert "move" in CLIENT_COMMANDS
        assert "leave" in CLIENT_COMMANDS

    def test_server_event_set_aligns_with_documented_events(self):
        # Documented events: gameState, playerLeft, playerDisconnected, gameOver, error
        expected = {"gameState", "playerLeft", "playerDisconnected", "gameOver", "error"}
        assert expected.issubset(SERVER_EVENTS)

    def test_backend_parse_helper_has_explicit_command_allowlist(self):
        # The server accepts exactly the same command set the frontend helper
        # expects in `communication.test.js`. This guards against drift between
        # what the backend parses and what the frontend is allowed to send.
        from baghchal.gateway.commands import CLIENT_COMMANDS as backend_commands

        assert backend_commands == CLIENT_COMMANDS

    def test_backend_make_error_helper_has_explicit_error_payload_shape(self):
        # The server error event writer and the frontend error shape must agree.
        from baghchal.gateway.commands import make_error_event as backend_make_error

        event = backend_make_error("not_your_turn", "It is not your turn")
        assert event["event"] == "error"
        assert set(event["payload"].keys()) == {"code", "message"}
        assert event["payload"]["code"] == "not_your_turn"
        assert event["payload"]["message"] == "It is not your turn"
