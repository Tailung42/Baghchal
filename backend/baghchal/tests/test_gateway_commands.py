"""
Tests for command/event envelope parsing.

These verify the proposed message contract helpers.
"""

import pytest

from baghchal.gateway.commands import CLIENT_COMMANDS, SERVER_EVENTS, make_event, parse_client_envelope


def test_parse_valid_move_command():
    envelope = {"command": "move", "payload": {"fromKey": "0-0", "toKey": "0-1"}}
    result = parse_client_envelope(envelope)
    assert result["command"] == "move"
    assert result["payload"] == {"fromKey": "0-0", "toKey": "0-1"}


def test_parse_valid_leave_command():
    envelope = {"command": "leave", "payload": {}}
    result = parse_client_envelope(envelope)
    assert result["command"] == "leave"


def test_parse_rejects_non_dict_envelope():
    with pytest.raises(ValueError):
        parse_client_envelope("not-a-dict")


def test_parse_rejects_unknown_command():
    with pytest.raises(ValueError):
        parse_client_envelope({"command": "ping", "payload": {}})


def test_parse_rejects_missing_payload_dict():
    with pytest.raises(ValueError):
        parse_client_envelope({"command": "move", "payload": "bad"})


def test_make_event_game_state():
    event = make_event("gameState", {"status": "ongoing"})
    assert event["event"] == "gameState"
    assert event["payload"] == {"status": "ongoing"}


def test_make_event_error():
    event = make_event("error", {"code": "invalid_move", "message": "bad"})
    assert event["event"] == "error"


def test_make_event_rejects_unknown_event():
    with pytest.raises(ValueError):
        make_event("unknown", {})


def test_known_sets_are_disjoint():
    overlap = CLIENT_COMMANDS & SERVER_EVENTS
    assert not overlap
