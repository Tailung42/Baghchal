"""
Gateway error taxonomy.

This is a small, explicit set of error codes and messages so the server can
return consistent responses instead of ad-hoc strings.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GatewayError(Exception):
    """
    A domain error that can be raised (``raise GAME_NOT_FOUND``) and also
    mapped to a response envelope via :meth:`to_response`.
    """

    code: str
    message: str

    def __str__(self) -> str:
        return self.message

    def to_response(self, *, ok: bool = False) -> dict[str, Any]:
        return {"ok": ok, "error_code": self.code, "message": self.message}


INVALID_MESSAGE = GatewayError("invalid_message", "Unsupported or malformed command")
NOT_AUTHENTICATED = GatewayError("not_authenticated", "No authenticated user for this connection")
NOT_IN_GAME = GatewayError("not_in_game", "You are not a participant in this game")
NOT_YOUR_TURN = GatewayError("not_your_turn", "It is not your turn")
INVALID_MOVE = GatewayError("invalid_move", "Move failed validation")
GAME_NOT_FOUND = GatewayError("game_not_found", "Game does not exist")
GAME_ALREADY_OVER = GatewayError("game_already_over", "Action on finished game")
CONNECTION_ERROR = GatewayError("connection_error", "Connection setup or session error")


__all__ = [
    "GatewayError",
    "INVALID_MESSAGE",
    "NOT_AUTHENTICATED",
    "NOT_IN_GAME",
    "NOT_YOUR_TURN",
    "INVALID_MOVE",
    "GAME_NOT_FOUND",
    "GAME_ALREADY_OVER",
    "CONNECTION_ERROR",
]
