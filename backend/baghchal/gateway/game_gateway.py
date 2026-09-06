"""
Game gateway.

This is the intended single place for:
- deciding whether a WebSocket sender is allowed to act in a game
- dispatching commands to a session
- broadcasting server events

For this first surgical pass it does not replace the existing consumer.
It exists so future work can route messages through one gateway instead of
scattering group_send logic across consumers and background tasks.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from .session import GameSession


# Allowed client commands at the application layer.
_KNOWN_COMMANDS = {"move", "leave"}


class GameGateway:
    """
    Application-layer gateway for game rooms.

    Responsibilities:
    - own active sessions
    - authorize who may act in a room
    - dispatch commands to the application command handlers
    - broadcast room events

    It does not directly touch Redis or the Channels channel layer. Those
    concerns are handed to it via callbacks or application service helpers so
    the same gateway can be used by the consumer and by tests.
    """

    def __init__(
        self,
        *,
        game_store: Callable[[str], Awaitable[dict[str, Any] | None]] | None = None,
        game_set: Callable[[str, dict[str, Any]], Awaitable[bool]] | None = None,
        game_delete: Callable[[str], Awaitable[bool]] = None,
        command_service: Callable | None = None,
    ):
        self._sessions: dict[str, GameSession] = {}
        self._game_store = game_store
        self._game_set = game_set
        self._game_delete = game_delete
        self._command_service = command_service

    def get_session(self, game_id: str) -> GameSession | None:
        return self._sessions.get(game_id)

    def ensure_session(
        self,
        game_id: str,
        broadcast: Any,
    ) -> GameSession:
        if game_id not in self._sessions:
            self._sessions[game_id] = GameSession(game_id=game_id, broadcast=broadcast)
        return self._sessions[game_id]

    async def broadcast(
        self,
        game_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        session = self._sessions.get(game_id)
        if session is None:
            return
        await session.broadcast_event(event_type, payload)

    async def dispatch(
        self,
        game_id: str,
        username: str,
        command: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Dispatch a client command through the application layer.

        Returns an outcome dict the transport layer can turn into either an
        event frame or an error frame.
        """
        if command not in _KNOWN_COMMANDS:
            return {"ok": False, "error_code": "invalid_message", "message": "Unsupported command"}

        session = self._sessions.get(game_id)
        if session is None:
            return {"ok": False, "error_code": "game_not_found", "message": "Game not found"}

        if username not in session.active_players():
            return {"ok": False, "error_code": "not_in_game", "message": "You are not in this game"}

        service = self._command_service or _default_command_service
        return await service(self, game_id, username, command, payload)


async def _default_command_service(
    gateway: GameGateway,
    game_id: str,
    username: str,
    command: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Default application command service used when the gateway is not wired to
    a custom one.

    This keeps the gateway thin while still allowing command behavior to live
    in one place instead of scattered across the consumer.
    """
    if command == "leave":
        return {"ok": True, "action": "leave", "username": username}

    if command == "move":
        return {"ok": True, "action": "move", "username": username, "payload": payload}

    return {"ok": False, "error_code": "invalid_message", "message": "Unsupported command"}


__all__ = [
    "GameGateway",
]
