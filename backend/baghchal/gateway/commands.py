"""
Minimal command/event helpers for the proposed WebSocket protocol.

This module is intentionally lightweight. It exists so the server can validate
envelopes and route them without scattering parsing logic across consumers.
"""

from __future__ import annotations

from typing import Any

from .errors import INVALID_MESSAGE


CLIENT_COMMANDS = {"move", "leave"}
SERVER_EVENTS = {"gameState", "playerLeft", "playerDisconnected", "gameOver", "error"}


def parse_client_envelope(raw: Any) -> dict[str, Any]:
    """
    Return {'command': ..., 'payload': ...} or raise ValueError.
    """
    if not isinstance(raw, dict):
        raise ValueError(INVALID_MESSAGE.message)

    command = raw.get("command")
    payload = raw.get("payload", {})

    if not isinstance(command, str) or command not in CLIENT_COMMANDS:
        raise ValueError(INVALID_MESSAGE.message)

    if not isinstance(payload, dict):
        raise ValueError(INVALID_MESSAGE.message)

    return {"command": command, "payload": payload}


def make_event(event: str, payload: Any) -> dict[str, Any]:
    if event not in SERVER_EVENTS:
        raise ValueError("Unknown server event type")
    return {"event": event, "payload": payload}


def make_error_event(code: str, message: str) -> dict[str, Any]:
    return make_event("error", {"code": code, "message": message})


def make_player_left_event(username: str, role: str) -> dict[str, Any]:
    return make_event("playerLeft", {"username": username, "role": role})


def make_player_disconnected_event(username: str, role: str) -> dict[str, Any]:
    return make_event("playerDisconnected", {"username": username, "role": role})


__all__ = [
    "CLIENT_COMMANDS",
    "SERVER_EVENTS",
    "parse_client_envelope",
    "make_event",
    "make_error_event",
    "make_player_left_event",
    "make_player_disconnected_event",
]
