# Bagh Chal Backend Architecture

Current-state description of how the backend is organized. This doc describes the code as it is, not a roadmap.

## Data flow

### HTTP game lifecycle

1. Client calls `POST /game/create/`, `/game/join/`, `/game/rejoin/`, or `/game/quick-match/`.
2. The view validates auth (JWT from the request), checks the live-state store for game presence, applies the lifecycle rule (create / join / rejoin / quick-match), and schedules an async write to Redis.
3. The HTTP response returns `game_id` (and only `game_id`). The full initial game state is delivered over the WebSocket after the client connects.
4. Client opens a WebSocket for play.

### WebSocket play

1. `AsyncGameConsumer` authenticates the connection (JWT from the WebSocket subprotocol → DB user lookup via `JWTAuthMiddleware`).
2. On connect, the consumer looks up the game in the store, verifies the user is a player, attaches to a gateway session, joins the Channels group, and broadcasts the current `gameState`.
3. Client sends commands as `{ "command": "...", "payload": {...} }`. The consumer also bridges the legacy `{ "message": {...} }` envelope for backwards compatibility.
4. The consumer translates inbound frames and delegates authorization to `GameGateway.dispatch`. The actual move/leave execution happens in the persistence layer (`persistence/play.py`), not in the consumer.
5. The persistence layer applies the move through the game engine (`game_engine/services.py` → `game_engine/game_state.py`), persists the updated state to Redis, and schedules archival on game over.
6. On game over, the consumer broadcasts the final `gameState` (with `status: "over"`) and then a `gameOver` event. The live Redis state is cleared.
7. On disconnect, the consumer notifies the session, broadcasts `playerDisconnected`, and runs `persistence/play.disconnect_game` for cleanup.

### Persistence

- **Live game state** lives in Redis, accessed through `persistence/store.py` (`GameStateStore`).
- **Completed games** are archived to the ORM via `persistence/archival.py` (writes `baghchal.models.Game`).
- **User data and stats** live in the Django ORM (`core.models.User`, `core/user_stats.py`).
- The old `baghchal/redis.py` module is dead. New code should import from `persistence/store.py` (or the persistence helpers that wrap it).

## Layered architecture

### 1. Transport layer

`baghchal/consumers.py` — `AsyncGameConsumer`.

Only responsible for:
- WebSocket handshake and auth (via the middleware + JWT subprotocol).
- Connection open/close.
- Inbound frame parsing and translation (new envelope + legacy bridge).
- Sending outbound event/error frames.
- Delegating command outcomes to the gateway and persistence layer.

No game rule logic, no direct Redis access, no persistence orchestration beyond calling the persistence helpers.

### 2. Application / gateway layer

`baghchal/gateway/`:
- `game_gateway.py` — `GameGateway`: owns active sessions, authorizes who may act in a room, dispatches commands (`move`, `leave`), and broadcasts room events through the session.
- `session.py` — `GameSession` + `ConnectionInfo`: per-game connection registry and a single broadcast entrypoint.
- `commands.py` — command/event envelope helpers (`parse_client_envelope`, `make_event`, `make_error_event`, etc.).
- `errors.py` — gateway error taxonomy (`GatewayError`, the named error constants).
- `integration.py` — session attach / broadcast helpers for wiring a consumer channel into a session.
- `managers.py` — the process-level `game_gateway` singleton instance used by the consumer.
- `routing.py` — notes only; the actual WebSocket routing still points at the consumer.

`GameGateway` is intentionally transport-agnostic: it receives callbacks for store access so the same gateway can be used by the consumer and by tests. The default command service is thin; the real move/leave execution is delegated by the consumer to `persistence/play.py`.

### 3. Domain layer

`baghchal/game_engine/`:
- `board.py` — board rules: move/capture connections, blocking, win conditions.
- `game_state.py` — game state helpers, move validation (`is_valid_move`), move application (`apply_move`), game-over checks (`check_game_over`).
- `services.py` — orchestration: `async_update_game_state` applies a move and persists the result using callbacks the caller provides (so it works with both legacy and new persistence paths).

`baghchal/domain/` exists as a thin re-export layer over `game_engine`. In practice, code imports from `baghchal.game_engine` (or `baghchal.game_engine.services` for the service layer). The domain package is decorative; the real home is `game_engine/`.

Domain layer rules:
- Move validation, move application, turn switching, win/end conditions.
- No Redis, no ORM, no Channels, no HTTP.

### 4. Persistence layer

`baghchal/persistence/`:
- `store.py` — `GameStateStore`: live-game Redis abstraction. Key layout: `game:<game_id>` for state, `active_games` set for the active-game index. Methods: `get_game`, `set_game`, `delete_game`, `game_exists`, `list_active_games`, `get_all_games`, `close`.
- `archival.py` — finished-game ORM archival (`archive_game`). Writes `baghchal.models.Game`.
- `views.py` — HTTP lifecycle helpers (create/join/rejoin/quick-match rules, `_initial_game_state`, `apply_leave`, `finish_game`, store wiring via `configure_shared_store`).
- `play.py` — real-time play persistence orchestration (load game for play, `execute_move`, `execute_leave`, `disconnect_game`). Sits between the gateway/consumer and the store/archival layer.

Persistence layer rules:
- Clear split between live transient state (Redis) and archived records (ORM).
- Redis access is centralized in `store.py`.
- The consumer and views read/write through the shared store instance, not their own Redis clients.

## Separation rules

- Consumer and HTTP views must not contain game rule logic.
- `game_engine` and persistence must not import Channels or HTTP abstractions.
- Redis access is centralized in `persistence/store.py`. The dead `redis.py` must not be re-introduced.
- The store lifecycle is centralized: `persistence.store` owns a shared store instance that the HTTP and WebSocket paths use. The consumer configures it at module load (`configure_store` + `configure_play_store` with the same instance).
- Game-over archival belongs in persistence (`persistence/archival.py`), not in the game engine service layer.
- The consumer no longer mutates game state or schedules persistence directly; it delegates to `persistence/play.py`.

## Store wiring (current state)

Three modules historically juggled store instances:
- `persistence/store.py` — the shared store, with `_set_store` / `configure_store` / `configure_shared_store`.
- `persistence/views.py` — has its own `_store` global, wired via `configure_shared_store`.
- `persistence/play.py` — has `_default_store`, wired via `configure_store`.

In the current consumer, all three are pointed at the same `GameStateStore` instance created in `consumers.py` at module load. That works, but the three globals are a mild bug farm. The clean long-term shape is a single configured store owned in one place, with all modules importing from one module. For now, make sure any new code uses the shared store rather than creating its own `GameStateStore()`.

## Gateway command handling

`GameGateway.dispatch` owns the application-layer outcome for supported commands:
- Rejects unknown commands as `invalid_message`.
- Rejects missing sessions as `game_not_found`.
- Rejects non-participants as `not_in_game`.
- Delegates leave/move handling to the application command service or persistence helpers.

Today the consumer delegates real move/leave execution to `persistence/play.py`, so the consumer is a transport adapter. `GameGateway.dispatch` itself does not apply moves.

## WebSocket message contract

### Client → server envelope

```json
{
  "command": "<command>",
  "payload": { ... }
}
```

Supported commands:
- `move`
- `leave`

Legacy support (bridged by the consumer):
- frontend `newMove` → `move`
- frontend `exitGame` → `leave`

### Server → client envelope

```json
{
  "event": "<event>",
  "payload": { ... }
}
```

Supported server events:
- `gameState`
- `playerLeft`
- `playerDisconnected`
- `gameOver`
- `error`

Error payload shape:
```json
{
  "code": "<error_code>",
  "message": "<message>"
}
```

Server error codes:
- `invalid_message`
- `not_authenticated`
- `not_in_game`
- `not_your_turn`
- `invalid_move`
- `game_not_found`
- `game_already_over`
- `connection_error`

### Game-over flow

On the winning move, the consumer broadcasts:
1. The final `gameState` (`status: "over"`, final board, winner, `deadGoatCount`, etc.).
2. The `gameOver` event (`winner`, `endReason`).

Both arrive. The frontend detects game over from either `gameState.status === "over"` or the `gameOver` event. Do not depend on only one.

## Connection and disconnection model

- Gateway sessions track active connections per game.
- On connect, the consumer joins the Channels group (`group_add`) so broadcasts reach the connection.
- On disconnect, the consumer notifies the session, broadcasts `playerDisconnected`, runs `persistence/play.disconnect_game`, and discards from the group (`group_discard`).
- If a game has no remaining active players, live state is cleared or reset to `waiting`.
- Reconnect behavior is partial: a client can reconnect and resync via the game-state broadcast on connect, but rejoining a live game as the same player uses the HTTP `rejoin` endpoint, not automatic WS reconnect.

## Redis notes

- Live game state is accessed through `GameStateStore`.
- Active games are tracked via a Redis set (`active_games`) in addition to key lookup.
- `get_all_games()` still uses `KEYS game:*` (legacy contract preserved for callers). `list_active_games()` uses the set.
- TTL policy is not fully enforced yet. Abandoned games can persist in Redis until cleaned up.

## Where to look

| Concern | Path |
|---|---|
| Auth views (signup/login/guest/google/token refresh/user stats) | `backend/core/views.py` |
| Auth URL routing | `backend/core/urls.py` |
| User model + serializer | `backend/core/models.py`, `backend/core/serializers.py` |
| User stats | `backend/core/user_stats.py` |
| JWT auth middleware | `backend/backend/middleware.py` |
| Game HTTP views (create/join/rejoin/quick-match) | `backend/baghchal/views.py` |
| Game URL routing | `backend/baghchal/urls.py` |
| Root URL config | `backend/backend/urls.py` |
| WebSocket consumer | `backend/baghchal/consumers.py` |
| WS routing | `backend/baghchal/routing.py` |
| Game state + move logic | `backend/baghchal/game_engine/game_state.py`, `board.py` |
| Move orchestration with persistence callbacks | `backend/baghchal/game_engine/services.py` |
| Gateway (session + dispatch + commands + errors) | `backend/baghchal/gateway/` |
| Persistence (Redis store) | `backend/baghchal/persistence/store.py` |
| Play lifecycle (move/leave/disconnect) | `backend/baghchal/persistence/play.py` |
| HTTP persistence helpers | `backend/baghchal/persistence/views.py` |
| Game archival (ORM) | `backend/baghchal/persistence/archival.py` |
| Game ORM model | `backend/baghchal/models.py` |
| Protocol (in-code) | `backend/baghchal/protocol.md` |

The frontend-facing API and WebSocket protocol are documented in `backend/API_DOC.md`. The envelope helpers (`gateway/commands.py`) and the frontend's communication contract tests (`frontend/src/communication.test.js`, `frontend/src/protocol.test.js`) should stay aligned — they are the real spec for the wire format.

