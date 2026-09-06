"""
Tests for the gateway error taxonomy.
"""

import pytest

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


def test_error_codes_are_unique():
    codes = {
        INVALID_MESSAGE.code,
        NOT_AUTHENTICATED.code,
        NOT_IN_GAME.code,
        NOT_YOUR_TURN.code,
        INVALID_MOVE.code,
        GAME_NOT_FOUND.code,
        GAME_ALREADY_OVER.code,
        CONNECTION_ERROR.code,
    }
    assert len(codes) == 8


def test_error_response_shape():
    response = INVALID_MESSAGE.to_response(ok=False)
    assert response["ok"] is False
    assert response["error_code"] == "invalid_message"
    assert "message" in response


def test_error_frozen():
    with pytest.raises(Exception):
        INVALID_MESSAGE.code = "changed"
