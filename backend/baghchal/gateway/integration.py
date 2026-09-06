from __future__ import annotations

from typing import Any, Awaitable, Callable

from .game_gateway import GameGateway
from .session import ConnectionInfo, GameSession


def attach_session(
    gateway: GameGateway,
    game_id: str,
    broadcast: Callable[[dict[str, Any]], Awaitable[None]],
    channel_name: str,
    username: str,
    role: str | None = None,
) -> GameSession:
    """
    Attach a consumer channel to a game session.

    `broadcast` should be the callable that actually sends a group message.
    """
    session = gateway.ensure_session(game_id, broadcast)
    session.register_connection(channel_name, username, role)
    return session


async def broadcast_to_session(
    session: GameSession,
    event_type: str,
    payload: Any,
) -> None:
    await session.broadcast_event(event_type, payload)
