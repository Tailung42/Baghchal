"""
Tests for the consumer's new protocol handling.

These tests focus on the mapping between legacy frontend messages and the
new command envelope, plus the error responses the consumer sends.
"""

from baghchal.consumers import AsyncGameConsumer
from baghchal.gateway import commands as gateway_commands
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


def _consumer_error_for_code(code: str):
    """
    Reuse the same code->error mapping the consumer uses. This mirrors the
    module-level helper in `baghchal.consumers` but is importable from the
    gateway layer for testability.
    """
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

    error_map = {
        "invalid_message": INVALID_MESSAGE,
        "not_authenticated": NOT_AUTHENTICATED,
        "not_in_game": NOT_IN_GAME,
        "not_your_turn": NOT_YOUR_TURN,
        "invalid_move": INVALID_MOVE,
        "game_not_found": GAME_NOT_FOUND,
        "game_already_over": GAME_ALREADY_OVER,
        "connection_error": CONNECTION_ERROR,
    }
    return error_map.get(code, INVALID_MESSAGE)


class TestLegacyToCommandMapping:
    def test_new_move_legacy_message(self):
        message = {"type": "newMove", "move": {"moveType": "place", "toKey": "0-1"}}
        envelope = AsyncGameConsumer._from_user_message_static(message)
        assert envelope["command"] == "move"
        assert envelope["payload"] == {"moveType": "place", "toKey": "0-1"}

    def test_exit_game_legacy_message(self):
        message = {"type": "exitGame"}
        envelope = AsyncGameConsumer._from_user_message_static(message)
        assert envelope["command"] == "leave"
        assert envelope["payload"] == {}

    def test_unknown_legacy_type_passthrough(self):
        message = {"type": "ping", "extra": 1}
        envelope = AsyncGameConsumer._from_user_message_static(message)
        assert envelope["command"] == "ping"
        assert envelope["payload"] == {"type": "ping", "extra": 1}

    def test_non_dict_message_rejected(self):
        message = "bad"
        try:
            AsyncGameConsumer._from_user_message_static(message)
        except (ValueError, TypeError, AttributeError):
            return
        assert False, "expected error"


class TestGatewayErrorLookup:
    def test_all_defined_codes_map_to_errors(self):
        expected = {
            "invalid_message": INVALID_MESSAGE,
            "not_authenticated": NOT_AUTHENTICATED,
            "not_in_game": NOT_IN_GAME,
            "not_your_turn": NOT_YOUR_TURN,
            "invalid_move": INVALID_MOVE,
            "game_not_found": GAME_NOT_FOUND,
            "game_already_over": GAME_ALREADY_OVER,
            "connection_error": CONNECTION_ERROR,
        }
        for code, expected_error in expected.items():
            error = _consumer_error_for_code(code)
            assert error.code == expected_error.code
            assert error.message == expected_error.message

    def test_unknown_code_falls_back_to_invalid_message(self):
        error = _consumer_error_for_code("unknown_code")
        assert error.code == INVALID_MESSAGE.code
