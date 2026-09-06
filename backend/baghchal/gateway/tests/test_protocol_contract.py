"""
Protocol contract tests for the backend side.

These tests verify that the backend command/event helpers encode and decode
the same shapes the frontend is expected to use.
"""

from baghchal.gateway.commands import (
    CLIENT_COMMANDS,
    SERVER_EVENTS,
    make_event,
    make_error_event,
    make_player_disconnected_event,
    make_player_left_event,
    parse_client_envelope,
)


class TestClientCommandEnvelope:
    def test_parse_move_command(self):
        raw = {"command": "move", "payload": {"moveType": "place", "toKey": "0-1"}}
        parsed = parse_client_envelope(raw)
        assert parsed["command"] == "move"
        assert parsed["payload"] == {"moveType": "place", "toKey": "0-1"}

    def test_parse_leave_command(self):
        raw = {"command": "leave", "payload": {}}
        parsed = parse_client_envelope(raw)
        assert parsed["command"] == "leave"
        assert parsed["payload"] == {}

    def test_parse_rejects_unsupported_command(self):
        raw = {"command": "ping", "payload": {}}
        try:
            parse_client_envelope(raw)
        except ValueError as exc:
            assert "unsupported" in str(exc).lower() or "invalid" in str(exc).lower()
        else:
            assert False, "expected ValueError"

    def test_parse_rejects_non_dict_payload(self):
        raw = {"command": "move", "payload": "bad"}
        try:
            parse_client_envelope(raw)
        except ValueError:
            return
        assert False, "expected ValueError"

    def test_parse_rejects_non_dict_body(self):
        raw = "not-a-dict"
        try:
            parse_client_envelope(raw)
        except ValueError:
            return
        assert False, "expected ValueError"


class TestServerEventEnvelope:
    def test_make_game_state_event(self):
        event = make_event("gameState", {"game_state": {"status": "ongoing"}})
        assert event["event"] == "gameState"
        assert event["payload"] == {"game_state": {"status": "ongoing"}}

    def test_make_player_left_event(self):
        event = make_player_left_event("alice", "goat")
        assert event["event"] == "playerLeft"
        assert event["payload"] == {"username": "alice", "role": "goat"}

    def test_make_player_disconnected_event(self):
        event = make_player_disconnected_event("alice", "goat")
        assert event["event"] == "playerDisconnected"
        assert event["payload"] == {"username": "alice", "role": "goat"}

    def test_make_error_event(self):
        event = make_error_event("invalid_move", "Move failed validation")
        assert event["event"] == "error"
        assert event["payload"] == {"code": "invalid_move", "message": "Move failed validation"}

    def test_make_event_rejects_unknown_event(self):
        try:
            make_event("unknown", {})
        except ValueError:
            return
        assert False, "expected ValueError"


class TestProtocolContractAlignment:
    def test_client_commands_match_frontend_expectations(self):
        assert "move" in CLIENT_COMMANDS
        assert "leave" in CLIENT_COMMANDS

    def test_server_events_includes_provided_events(self):
        expected = {"gameState", "playerLeft", "playerDisconnected", "gameOver", "error"}
        assert expected.issubset(SERVER_EVENTS)

    def test_error_event_shape_is_stable(self):
        event = make_error_event("not_your_turn", "It is not your turn")
        payload = event["payload"]
        assert payload["code"] == "not_your_turn"
        assert payload["message"] == "It is not your turn"
        assert "ok" not in payload
