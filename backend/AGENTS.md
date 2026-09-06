# Bagh Chal Backend - Agent Brief

## Project purpose
Real-time multiplayer Bagh Chal server:
- HTTP API for auth, game creation/joining/rejoin/quick match
- WebSocket channel for real-time play
- Redis-backed live game state
- Django ORM for users and completed game records

## Current architecture summary
- Django + DRF + Django Channels + Daphne
- `core`: auth (JWT, Google, guest), `User`, user stats
- `baghchal`:
  - HTTP views for game lifecycle
  - `AsyncGameConsumer` for WebSocket play
  - Redis store in `redis.py`
  - Game rules in `game_engine/` and game services in `game_engine/services.py`
- Frontend owns optimistic state and reconnection UX

## Identified architectural flaws
1. No clear layered separation. Consumers, views, and services all touch Redis and the ORM directly.
2. No single gateway for WebSocket messaging. Broadcasting logic is scattered across consumers and background tasks.
3. Connection/disconnection is implicit. There is no connection registry, no heartbeat, and no robust reconnect/resync policy.
4. Game lifecycle is partially async fire-and-forget with minimal error handling around persistence and cleanup.
5. Redis usage is basic: global client, manual JSON, and `keys()` scanning.
6. No formal message contract or error taxonomy for the WebSocket protocol.
7. Limited observability and very few backend tests.

## Target architecture
Keep Django/Channels as the foundation, but organize backend code into layers:

1. **Transport layer**
   - Thin Channels consumers (`baghchal.consumers.AsyncGameConsumer`)
   - Responsibility: auth, connection lifecycle, inbound frame parsing/translation, outbound event/error frames, session attachment, and delegating play lifecycle to the persistence layer
   - No game rule logic here
   - No direct Redis mutation or persistence orchestration except delegating to persistence helpers

2. **Application/gateway layer**
   - `baghchal.gateway`
   - Responsibility:
     - own active sessions (`GameSession`)
     - validate that a sender is a participant
     - dispatch supported commands (`move`, `leave`)
     - broadcast events to a game room through the session
     - delegate command execution to the persistence/application layer
   - This is now the place that owns application-level command outcomes instead of scattering them across the consumer
   - The gateway is transport-agnostic: it can be wired with callbacks or a command service so the same gateway can be used in tests and in the consumer

3. **Domain layer**
   - `baghchal.domain` and `baghchal.game_engine`
   - Responsibility:
     - validate moves
     - apply moves
     - determine game-over and winner
   - Should be testable without Redis, Django, or Channels
   - `baghchal.domain` is the stable domain API; `baghchal.game_engine` is the implementation detail

4. **Persistence layer**
   - `baghchal.persistence`
   - Includes:
     - live-state Redis store (`persistence/store.py`)
     - HTTP game lifecycle helpers (`persistence/views.py`)
     - real-time play orchestration (`persistence/play.py`)
     - finished-game ORM archival (`persistence/archival.py`)
   - Clear boundary: live transient state vs archived results
   - `redis.py` is now a compatibility facade over the store, not the primary Redis interface

5. **Message contract**
   - Small WebSocket message schema in `baghchal.gateway.commands`
   - Server events and client commands separated clearly
   - Validation and serialization centralized at the gateway/command-helpers layer
   - Errors use an explicit taxonomy in `baghchal.gateway.errors`

## Non-goals for the first surgical pass
- Do not rewrite existing game logic unless it blocks robustness.
- Do not delete existing consumers or views.
- Do not change frontend behavior yet.
- Do not introduce a separate service unless we later decide it is necessary.

## Surgical fix plan
1. Create a Python venv and lock a consistent Python version for backend work.
2. Add an explicit layered backend structure:
   - `baghchal/domain/` for pure game logic
   - `baghchal/gateway/` for connection and message dispatch
   - `baghchal/persistence/` for the Redis store abstraction and archival
3. Define a small WebSocket message protocol:
   - client command types
   - server event types
   - error codes
4. Add a game session/connection registry so connect/disconnect can be handled explicitly and broadcast can go through one gateway.
5. Harden Redis usage:
   - store abstraction
   - safer get/set/delete semantics
   - avoid key scanning for production paths
6. Add observability and error taxonomy:
   - structured logging
   - common error codes
7. Add targeted tests:
   - domain rules
   - gateway/session handling
   - basic store behavior
8. Thin the consumer and views so they do not own game logic or direct persistence orchestration.
9. Move finished-game archival out of the game engine service layer and into the persistence layer.
10. Centralize Redis access through `persistence/store.py`; keep `redis.py` as a backward-compatible facade.
11. Make the consumer a transport adapter that delegates play lifecycle to `persistence/play.py`.
12. Give `GameGateway` a command service hook so command handling stays in one application place instead of scattering it across the consumer.

## Decisions already made
- Redis remains the live state store for now.
- Django/Channels remains the transport.
- Existing game rules in `game_engine` are treated as the domain core and should be isolated, not rewritten from scratch.
- Python virtual environment location for backend work: `backend/.venv`.
- This environment currently uses Python 3.14.
- `persistence/store.py` is the canonical Redis interface; the legacy `redis.py` facade has been removed.
- Store lifecycle is centralized in `persistence.store` and shared by the HTTP and WebSocket paths.
- The consumer no longer keeps its own thin Redis helpers; it reads and writes directly through the shared store and `persistence/play`.
- `persistence/archival.py` owns finished-game ORM persistence.
- `GameGateway.dispatch` owns application-layer command authorization and outcomes for supported commands.
- The consumer is now a transport adapter that delegates to the gateway and persistence layer instead of owning move/leave execution directly.
- Disconnect-side persistence is delegated to `persistence/play.disconnect_game` instead of being implemented directly in the consumer.

## Open questions
- Desired Python version for the project long term: keep 3.14 in this environment, or pin a lower LTS version for deployment?
- Whether to add connection presence metadata such as last heartbeat and role.
- Whether to add rate limiting and move validation gating at the gateway layer before the domain layer.
- Whether to move more command execution/persistence orchestration into `GameGateway` so the consumer becomes even thinner.
- The legacy `redis.py` facade has been removed; all live-state access now goes through `persistence.store`.
