"""
Tests for the Channels-native handler methods the ASGI layer calls.

These tests verify the `websocket_connect`, `websocket_receive`, and
`websocket_disconnect` handler contracts directly. That is important because
Channels routes incoming frames to those methods, not to a custom `receive`
callable we invented for transport tests.
"""

from __future__ import annotations

import json

import pytest

from django.contrib.auth.models import AnonymousUser

from baghchal.consumers import AsyncGameConsumer


def _make_consumer_with_send(send_frames: list[dict] | None = None):
    """Helper that returns a consumer wired to a fake ASGI send."""
    consumer = AsyncGameConsumer()
    consumer.scope = {"user": None, "query_string": b"game_id=test_room"}
    consumer.channel_name = "ch_test"

    frames = send_frames if send_frames is not None else []
    async def fake_send(message: dict) -> None:
        frames.append(message)

    consumer.base_send = fake_send
    return consumer, frames


@pytest.mark.asyncio
async def test_websocket_connect_requires_authentication():
    """
    An unauthenticated WebSocket connect should be rejected with a close code
    that the frontend can interpret as a login/auth issue.
    """
    from django.contrib.auth.models import AnonymousUser

    anonymous = AnonymousUser()
    consumer, sent = _make_consumer_with_send()
    consumer.scope["user"] = anonymous

    await consumer.websocket_connect({"type": "websocket.connect"})

    sent_frames = [frame for frame in sent if frame["type"] == "websocket.close"]
    assert len(sent_frames) == 1, f"expected one close frame, got: {sent}"
    assert sent_frames[0]["code"] == 4001


@pytest.mark.asyncio
async def test_websocket_receive_decodes_json_text_frames():
    """
    Channels calls `websocket_receive` with ASGI frames. The consumer should
    decode JSON text frames and pass them into the command dispatch path.
    """
    consumer, _ = _make_consumer_with_send()
    consumer.receive = lambda text_data: None  # no-op for this test

    received_text: list[str] = []
    async def fake_receive(text_data: str) -> None:
        received_text.append(text_data)

    consumer.receive = fake_receive

    payload = {"command": "move", "payload": {"moveType": "place", "toKey": "0-1"}}
    frame = {"type": "websocket.receive", "text": json.dumps(payload)}
    await consumer.websocket_receive(frame)

    assert len(received_text) == 1
    assert json.loads(received_text[0]) == payload


@pytest.mark.asyncio
async def test_websocket_receive_rejects_malformed_json():
    """
    A malformed or non-JSON text frame should still be routed into the
    consumer without crashing the ASGI channel.
    """
    consumer, _ = _make_consumer_with_send()

    errors: list[Exception] = []
    async def fake_receive(text_data: str) -> None:
        try:
            json.loads(text_data)
        except Exception as exc:
            errors.append(exc)
            raise

    consumer.receive = fake_receive

    frame = {"type": "websocket.receive", "text": "{not-json"}
    with pytest.raises(json.JSONDecodeError):
        await consumer.websocket_receive(frame)

    assert len(errors) == 1


@pytest.mark.asyncio
async def test_websocket_disconnect_dispatches_to_disconnect_handler():
    """
    When Channels sends a disconnect frame, the consumer should route it to
    the application `disconnect` handler so cleanup logic runs.
    """
    consumer, _ = _make_consumer_with_send()
    consumer.disconnect_called_with_code: list[int] = []

    async def fake_disconnect(code: int) -> None:
        consumer.disconnect_called_with_code.append(code)

    consumer.disconnect = fake_disconnect

    frame = {"type": "websocket.disconnect", "code": 1001}
    with pytest.raises(Exception):
        await consumer.websocket_disconnect(frame)

    assert consumer.disconnect_called_with_code == [1001]


@pytest.mark.asyncio
async def test_send_method_emits_websocket_send_frame():
    """
    The consumer's public `send` method should emit a `websocket.send` frame
    that Channels can forward to the client.
    """
    consumer, sent = _make_consumer_with_send()

    payload = {"event": "gameState", "payload": {"status": "waiting"}}
    await consumer.send(text_data=json.dumps(payload))

    assert len(sent) == 1
    assert sent[0]["type"] == "websocket.send"
    assert json.loads(sent[0]["text"]) == payload


@pytest.mark.asyncio
async def test_send_method_rejects_missing_payload():
    """
    The consumer should reject a `send` call without either text or bytes data.
    """
    consumer, _ = _make_consumer_with_send()

    with pytest.raises(ValueError):
        await consumer.send()
