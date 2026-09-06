"""
Game session and connection registry.

This is the start of a gateway layer for WebSocket connections.
It is intentionally minimal for the first surgical pass:
- track active connections per game
- provide a single place to broadcast to a game room
- prepare for reconnect / resync / cleanup behavior later
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Coroutine


# Type alias for a broadcast sender callback.
# In this project that is currently a channel_layer.group_send style callable.
SendCallback = Callable[[dict[str, Any]], Coroutine[None, None, None]]


@dataclass
class ConnectionInfo:
    """
    Presence info for one WebSocket connection in a game session.
    """
    username: str
    role: str | None = None
    last_heartbeat: float | None = None


class GameSession:
    """
    Represents one active game room on the server side.

    Responsibilities:
    - keep track of connections in this room
    - provide a single broadcast entrypoint for the room
    - expose presence info for disconnect decisions
    """

    def __init__(
        self,
        game_id: str,
        broadcast: SendCallback,
    ):
        self.game_id = game_id
        self.broadcast = broadcast
        self.connections: dict[str, ConnectionInfo] = {}


    def register_connection(
        self,
        channel_name: str,
        username: str,
        role: str | None = None,
    ) -> ConnectionInfo:
        conn = ConnectionInfo(username=username, role=role)
        self.connections[channel_name] = conn
        return conn

    def update_heartbeat(self, channel_name: str) -> bool:
        if channel_name not in self.connections:
            return False
        self.connections[channel_name].last_heartbeat = 0.0  # real impl should use time.monotonic()
        return True

    def remove_connection(self, channel_name: str) -> ConnectionInfo | None:
        return self.connections.pop(channel_name, None)

    def active_players(self) -> set[str]:
        return {conn.username for conn in self.connections.values() if conn.username}

    def is_empty(self) -> bool:
        return not self.active_players()

    async def broadcast_event(self, event_type: str, payload: dict[str, Any]) -> None:
        await self.broadcast({"type": event_type, "payload": payload})

    def connection_count(self) -> int:
        return len(self.connections)

    def any_player(self) -> str | None:
        for conn in self.connections.values():
            if conn.username:
                return conn.username
        return None

    def player_count(self) -> int:
        return len(self.active_players())


__all__ = [
    "ConnectionInfo",
    "GameSession",
    "SendCallback",
]
