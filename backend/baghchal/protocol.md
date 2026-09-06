# WebSocket Protocol Draft

This is a proposed contract for the backend-side robustness work. It does not change the frontend yet.

## Envelope

### Client -> Server
```
{
  "command": "<command>",
  "payload": { ... }
}
```

### Server -> Client
```
{
  "event": "<event>",
  "payload": { ... }
}
```

If something goes wrong, the server may also send:
```
{
  "event": "error",
  "payload": {
    "code": "<error_code>",
    "message": "<human readable>"
  }
}
```

## Command catalog

### `move`
Payload:
```
{
  "moveType": "place" | "displace" | "capture",
  "fromKey": "<optional for place>",
  "toKey": "<coord>"
}
```
Purpose: submit a move for the current player.

### `leave`
Payload: none
Purpose: leave the current game session cleanly.

## Event catalog

### `gameState`
Payload: full current game state as stored/returned by the server.

### `playerLeft`
Payload:
```
{
  "username": "<username>",
  "role": "<goat|tiger>"
}
```
Purpose: inform the room that a player disconnected or left.

### `gameOver`
Payload:
```
{
  "winner": "<goat|tiger>",
  "endReason": "<end_reason>"
}
```

### `playerLeft`
Payload:
```
{
  "username": "<username>",
  "role": "<goat|tiger>"
}
```
Purpose: inform the room that a player left cleanly.

### `playerDisconnected`
Payload:
```
{
  "username": "<username>",
  "role": "<goat|tiger>"
}
```
Purpose: inform the room that a player disconnected unexpectedly.

### `gameState`
Payload: full current game state as stored/returned by the server.

### `error`
Payload:
```
{
  "code": "<error_code>",
  "message": "<human readable>"
}
```

## Error codes

- `invalid_message` - malformed or unsupported command
- `not_authenticated` - no valid user for the connection
- `not_in_game` - user is not a participant in this game
- `not_your_turn` - move submitted out of turn
- `invalid_move` - move failed domain validation
- `game_not_found` - game does not exist
- `game_already_over` - action on finished game
- `connection_error` - connection setup or session error

## Notes

- Commands and events should remain versioned if they evolve.
- The domain layer should not know about transport envelopes.
- The gateway should translate between transport envelopes and domain/game-state operations.
- The consumer now sends `gameState`, `playerLeft`, `playerDisconnected`, `gameOver`, and `error` events using the new envelopes and error codes.
