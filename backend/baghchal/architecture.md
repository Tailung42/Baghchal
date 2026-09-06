# Bagh Chal Backend Architecture

## Current Data Flow

### HTTP game lifecycle
1. Client calls `/game/create/`, `/game/join/`, `/game/rejoin/`, or `/game/quick-match/`
2. View validates auth, checks the live-state store for game presence, mutates state, schedules an async write
3. Client then opens a WebSocket for play

### WebSocket play
1. `AsyncGameConsumer` authenticates the connection and attaches to a gateway session
2. Client sends legacy messages (`newMove`, `exitGame`) or command envelopes
3. The consumer translates inbound frames and delegates command authorization/execution to `GameGateway`
4. `GameGateway` authorizes the sender, then the consumer applies moves through `game_engine` and persists via the persistence layer
5. End-game persistence is archived to the ORM via `persistence/archival.py`, and the live Redis state is cleaned up

### Persistence
- Live game state lives in Redis, accessed through `persistence/store.py`
- Completed games are persisted to the `Game` model via `persistence/archival.py`
- `redis.py` is now a compatibility facade over the store; new code should import from `persistence`
- User data and stats live in Django ORM

## Layered architecture

### 1) Transport layer
- `baghchal.consumers.AsyncGameConsumer`
- Only responsible for:
  - WebSocket handshake/auth
  - connection open/close
  - inbound frame parsing and translation
  - sending outbound event/error frames
  - delegating command outcomes to the gateway and persistence layer
- No game rule logic, no Redis access, no direct persistence orchestration beyond calling persistence helpers

### 2) Application / gateway layer
- `baghchal.gateway`
- Responsible for:
  - owning active sessions (`GameSession`)
  - authorizing who may act in a room
  - dispatching commands (`move`, `leave`)
  - broadcasting room events through the session
  - coordinating with the persistence layer for live-state reads/writes and archival
- `GameGateway` is intentionally transport-agnostic: it receives callbacks for store access so it can be reused in tests and consumers

### 3) Domain layer
- `baghchal.domain` and `baghchal.game_engine`
- Responsible for:
  - move validation
  - move application
  - turn switching
  - win/end conditions
- No Redis, no ORM, no Channels, no HTTP
- `baghchal.domain` is the stable domain API; `baghchal.game_engine` is the implementation detail

### 4) Persistence layer
- `baghchal.persistence`
- Includes:
  - `persistence/store.py`: live-game Redis abstraction (`get_game`, `set_game`, `delete_game`, `game_exists`, `get_all_games`, `list_active_games`)
  - `persistence/archival.py`: finished-game ORM archival
- Clear split between live transient state and archived records

## Separation rules
- Consumer and views should not contain game rule logic
- `game_engine` and persistence should not import Channels or HTTP abstractions
- Redis access should be centralized in `persistence/store.py`; the legacy `redis.py` module has been removed
- The store lifecycle is centralized: `persistence.store` owns a shared store instance that the HTTP and WebSocket paths use instead of creating their own
- The consumer no longer exposes its own thin Redis helper wrappers; it reads and writes directly through the shared store and persistence/play helpers
- Finished-game archival belongs in persistence, not in the game engine service layer

## Gateway command handling
`GameGateway.dispatch` owns the application-layer outcome for supported commands:
- rejects unknown commands as `invalid_message`
- rejects unknown or missing sessions as `game_not_found`
- rejects non-participants as `not_in_game`
- delegates leave/move handling to an application command service or persistence helpers

Today the consumer delegates real move/leave execution to `persistence/play.py`, so the consumer is a transport adapter and does not mutate game state or schedule persistence itself.

## Real-time play persistence
`persistence/play.py` owns the live-state side effects for WebSocket play:
- loading the game for play
- applying a leave and returning the updated state
- applying a move through the game engine and persistence callbacks
- archiving finished games

This keeps the consumer and gateway decoupled from the details of Redis mutations and ORM archival.

## WebSocket message contract

### Client command envelope
```
{ "command": "<command_type>", "payload": { ... } }
```

Supported commands:
- `move`
- `leave`

Legacy support:
- frontend `newMove` is translated to `move`
- frontend `exitGame` is translated to `leave`

### Server event envelope
```
{ "event": "<event_type>", "payload": { ... } }
```

Supported server events:
- `gameState`
- `playerLeft`
- `playerDisconnected`
- `gameOver`
- `error`

Error payload shape:
```
{ "code": "<error_code>", "message": "<message>" }
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

## Connection and disconnection model
- Gateway sessions track active connections per game
- On disconnect, the consumer notifies the session and the session broadcasts `playerDisconnected`
- Disconnect-side persistence is now delegated to `persistence/play.disconnect_game`, so the consumer no longer mutates live state directly for disconnects
- If a game has no remaining active players, live state is cleared or reset to `waiting`
- Reconnect behavior is partial today: clients may reconnect and resync via the existing game-state broadcast during connect

## Redis hardening
Completed improvements:
- Live game state is now accessed through `GameStateStore`
- Active games are tracked via a Redis set (`active_games`) in addition to key lookup
- `redis.py` no longer owns its own Redis client directly; it delegates to the store
- `persistence/store.py` centralizes serialization and key layout

Remaining known concerns:
- `list_active_games` uses `keys()` style behavior through the store wrapper in some legacy paths; the store itself prefers set-based active-game tracking
- TTL policy is not fully enforced yet

## Observability
- Replace most `print` statements with structured logging
- Use consistent error codes for client-visible failures
- Log connection lifecycle and game end events
- Keep game rule errors separate from transport errors

## Test strategy
- Domain tests for move validation and win logic
- Store tests for Redis abstraction behavior
- Gateway/session tests for connection and dispatch logic
- Consumer/protocol tests for transport boundary behavior
- At least one integration test for the HTTP + WebSocket join/move/end flow

## Current module layout

```
baghchal/
  consumers.py          # transport adapter
  views.py             # HTTP facade
  routing.py           # WebSocket routing
  urls.py              # HTTP URL routing
  models.py            # ORM records

  domain/
    game.py            # stable domain API over the game engine

  game_engine/
    board.py           # board rules
    game_state.py      # state helpers and move application
    services.py        # game-state orchestration with injected persistence callbacks

  gateway/
    game_gateway.py    # application-layer dispatch and session ownership
    session.py         # connection/presence registry and broadcast entrypoint
    commands.py        # command/event envelope helpers
    errors.py          # gateway error taxonomy
    integration.py     # session attach/broadcast helpers
    managers.py        # module-level gateway instance
    routing.py         # gateway routing notes

  persistence/
    store.py           # live-game Redis abstraction
    archival.py        # finished-game ORM archival
```
