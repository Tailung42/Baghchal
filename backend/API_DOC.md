# Backend API & WebSocket Protocol

Intended for frontend engineers. Source of truth is the running server; this doc captures the current contract and the common failure modes you'll hit.

## Base URLs

| Environment | HTTP API | WebSocket |
|---|---|---|
| Dev (what you're running locally) | `http://localhost:8000/` | `ws://localhost:8000/ws/game/` |
| The frontend reads these from `VITE_BASE_HTTP_URL` / `VITE_BASE_WS_URL` in `frontend/.env`. |

All HTTP endpoints live under the Django root. The game-specific ones are mounted at `/game/...`. Auth endpoints are at the root (signup, login, guest-login, token refresh, google, user profile).

---

## HTTP: Authentication

### `POST /signup/`
Create a user account.

**Request body (multipart/form-data):**
- `username` — string, required
- `password` — string, required
- `email` — string, required
- `avatar` — file, optional

**Response 200:**
```json
{
  "user_data": {
    "id": 1,
    "username": "alice",
    "avatar_url": "http://localhost:8000/media/avatars/...",
    "is_guest": false
  },
  "access": "<JWT access token>",
  "refresh": "<JWT refresh token>"
}
```

**Errors:** 400 `incomplete data`, `username already taken`, `email already registered`.

---

### `POST /login/`
Username + password login.

**Request body (JSON):**
- `username`
- `password`

**Response 200:** same shape as signup.

**Errors:** 400 `usenrame and password required` (yes, typo in the code — don't depend on exact string), `user doesn't exist`.

---

### `POST /guest-login/`
Get a JWT for a generated guest identity. The frontend generates the guest ID client-side and sends it here.

**Request body (JSON):**
- `guest_id` — string, required (the frontend-generated guest username)

**Response 200:**
```json
{
  "user_data": {
    "id": 2,
    "username": "randomly-generated-id",
    "avatar_url": null,
    "is_guest": true
  },
  "access": "<JWT access token>",
  "refresh": "<JWT refresh token>"
}
```

**Errors:** 400 `guest_id required`, 500 on backend failure.

**Important:** The frontend's `authStorage.setToken(access, refresh)` must be called with the real tokens from this response. A past frontend bug overwrote them with `undefined`; if your session is acting up, clear local storage and reload.

---

### `POST /token/refresh/`
Built-in DRF SimpleJWT endpoint. Send `{ "refresh": "<refresh token>" }` to get a new access token.

---

### `POST /auth/google`
Google OAuth sign-in/up.

**Request body (JSON):**
- `token` — Google id_token, required
- `mode` — `"login"` or `"signup"`, optional, default `"login"`

**Response 200:** same user shape as login/signup.

**Errors:**
- 400 `No token provided`, `Google client ID not configured` (means `GOOGLE_CLIENT_ID` env var is missing on the backend — local dev without a real client ID won't work for Google login), `No email from google`, `Invalid Google token: ...`
- 500 `Authentication failed: ...`

**Note:** Google login only works if the backend has a real `GOOGLE_CLIENT_ID`. Locally, guest login is the path that works out of the box.

---

### `GET /users/<username>/`
Public profile / stats for a user.

**Response 200:** see the "User stats shape" section below.

**Errors:** 400 `Have not provided proper username`, 500 if the `baghchal_game` table is missing (that's a migration bug — should be fixed; if you hit it, the `Game` model has no applied migration).

---

## HTTP: Game lifecycle

All game endpoints require a valid JWT in `Authorization: Bearer <access>`. Unauthenticated → 401 from the DRF permission layer.

### `POST /game/create/`
Create a new game. You become one of the players.

**Request body (JSON):**
- `game_id` — string, optional. If you omit it, the server generates one. The frontend generates an 8-char ID client-side and sends it here.
- `player_role` — `"tiger"` or `"goat"`, optional, default `"tiger"`.

**Response 201:**
```json
{
  "game_id": "12345678"
}
```

**When you also get the initial game state:** In the current frontend path, after create you call `gameApi.create(...)` and then the WebSocket connection delivers the full initial `game_state` via the `gameState` event. The HTTP response itself only returns `game_id`. Don't assume the HTTP response contains the board.

**Errors:** 400 `Username required`, `Failed to create game: ...`. 500 on unexpected failure.

---

### `POST /game/join/`
Join an existing waiting game by ID.

**Request body (JSON):**
- `game_id` — string, required

**Response 200:**
```json
{
  "game_id": "12345678"
}
```

**Errors:**
- 400 `Game ID and username required`, `Cannot join a game twice`, `Game is full, no available roles`
- 404 `Game not found`

After joining, open the WebSocket to get the live state.

---

### `POST /game/rejoin/`
Rejoin a game you're already part of (e.g. after reconnecting).

**Request body (JSON):**
- `game_id` — string, required

**Response 200:**
```json
{
  "game_id": "12345678"
}
```

**Errors:** 400 `Game ID and username required`, 403 `User is not part of this game`.

---

### `POST /game/quick-match/`
Find an open waiting game and join it, or create one if none is available.

**Request body:** none.

**Response:**
- 201 if a new game was created: `{ "game_id": "..." }`
- 200 if you joined an existing waiting game: `{ "game_id": "..." }`

**Errors:** 500 `Failed to find quick match: ...`.

**Note:** The matching is currently O(N) over all live games (`KEYS game:*`). It picks a random waiting game and assigns you the open role. If two players quick-match simultaneously, the second one may end up creating a new game instead.

---

## HTTP: User stats shape

Returned by `GET /users/<username>/`. Shape depends on the backend's `get_user_stats` implementation. The frontend's `UserProfile` reads these fields:

```json
{
  "username": "alice",
  "games_played": 10,
  "wins": 6,
  "losses": 4,
  "win_rate": 60,
  "games_as_goat": 5,
  "wins_as_goat": 3,
  "games_as_tiger": 5,
  "wins_as_tiger": 3
}
```

If a field is missing, the frontend fallbacks may show zeros or blanks. The `win_rate` is a number (percent), not a decimal.

---

## WebSocket: connection

**URL:** `ws://localhost:8000/ws/game/?game_id=<game_id>`

**Subprotocol:** pass your JWT access token as the WebSocket subprotocol. In the browser:

```js
const ws = new WebSocket(`${baseSocketUrl}?${params}`, [accessToken]);
```

**Why subprotocol:** the server authenticates the connection by reading the first subprotocol as a JWT and looking up the user. There's no separate auth message.

**Failure modes:**
- No token / invalid token → connection rejected with close code `4001` (unauthenticated).
- `game_id` missing or game doesn't exist → you'll get an `error` event with `code: "connection_error"` and `message: "Game does not exist"`.
- You're not a player in that game → `error` event, `code: "connection_error"`, message mentions "participant".
- If the server is mid-reload / daphne is restarting, handshakes can be slow or fail transiently. HTTP stays fast; WS is the one that blinks during restarts.

**On successful connect:** you immediately receive a `gameState` event with the full current state (see "Server events").

---

## WebSocket: client → server envelope

Every message you send is a JSON object:

```json
{
  "command": "<command>",
  "payload": { ... }
}
```

### Supported commands

#### `move`

```json
{
  "command": "move",
  "payload": {
    "moveType": "place" | "displace" | "capture",
    "fromKey": "<optional for place>",
    "toKey": "<coord>",
    "currentPlayer": "<goat|tiger>"
  }
}
```

**Payload fields:**
- `moveType` — required. One of `"place"`, `"displace"`, `"capture"`.
- `toKey` — required. Board coordinate like `"0-1"`, `"2-2"`, row-column with 0-based indices.
- `fromKey` — required for `displace` and `capture`. The coordinate you're moving from.
- `currentPlayer` — required. The player whose turn it is (`"goat"` or `"tiger"`). The server validates turn, so send the value from the current `gameState.currentPlayer`.

**Examples:**

Place a goat (placement phase):
```json
{
  "command": "move",
  "payload": {
    "moveType": "place",
    "toKey": "0-2",
    "currentPlayer": "goat"
  }
}
```

Tiger moves from 0-0 to 1-1:
```json
{
  "command": "move",
  "payload": {
    "moveType": "displace",
    "fromKey": "0-0",
    "toKey": "1-1",
    "currentPlayer": "tiger"
  }
}
```

Tiger captures a goat (jumps over it):
```json
{
  "command": "move",
  "payload": {
    "moveType": "capture",
    "fromKey": "0-0",
    "toKey": "0-2",
    "currentPlayer": "tiger"
  }
}
```

**Coordinate system:** the board is a 5x5 grid of intersections (0-4 in each axis). Keys are `"row-col"`. Initial tigers sit at the four corners: `"0-0"`, `"0-4"`, `"4-0"`, `"4-4"`. There are 25 positions total.

**Errors on move:**
- `invalid_move` — move failed domain validation (wrong turn, piece doesn't belong to you, destination occupied, invalid capture geometry, etc.).
- `not_your_turn` — you submitted a move but it's not your turn.
- `game_already_over` — the game ended; further moves are rejected.
- `invalid_message` — payload missing fields or malformed.

#### `leave`

```json
{
  "command": "leave",
  "payload": {}
}
```

Leaves the game cleanly. The room gets a `playerLeft` event. Your persistence layer will clear your player from the game state.

**Errors:** `not_in_game` if you're not a participant.

### Unsupported commands

Any command other than `move` and `leave` is rejected with an `error` event:
```json
{
  "event": "error",
  "payload": {
    "code": "invalid_message",
    "message": "Unsupported or malformed command"
  }
}
```

---

## WebSocket: server → client envelope

Every message you receive is a JSON object:

```json
{
  "event": "<event>",
  "payload": { ... }
}
```

`event` is a string. `payload` is an object.

### `gameState`

```json
{
  "event": "gameState",
  "payload": {
    "game_state": { ...full game state... }
  }
}
```

The `game_state` object is the authoritative current state. This is what you render. It arrives:
- Immediately after you connect.
- After every successful move.
- After a player leaves / disconnects (updated state).
- As the final state when the game ends (status `"over"`), right before or alongside `gameOver`.

**Full game state shape:**

```json
{
  "game_id": "game_12345678",
  "board": {
    "0-0": "tiger",
    "0-4": "tiger",
    "4-0": "tiger",
    "4-4": "tiger"
  },
  "currentPlayer": "goat",
  "phase": "placement",
  "unusedGoat": 20,
  "deadGoatCount": 0,
  "status": "waiting",
  "winner": null,
  "newPosition": "",
  "previousPosition": "",
  "isCaptured": false,
  "player": {
    "goat": "goat-player-username",
    "tiger": "tiger-player-username"
  },
  "history": []
}
```

**Field notes:**
- `board` — keys are `"row-col"` (0-4). Value is `"tiger"` or `"goat"`. Empty squares are absent (not `null`). Example: `{ "0-0": "tiger", "2-2": "goat" }`.
- `currentPlayer` — whose turn it is: `"goat"` or `"tiger"`.
- `phase` — `"placement"` (goats are being placed), `"displacement"` (goats placed, tigers move / goats displace), or possibly others as the engine evolves.
- `unusedGoat` — goats still to be placed on the board. Starts at 20. When it hits 0, phase switches to `"displacement"`.
- `deadGoatCount` — goats captured by tigers so far.
- `status` — `"waiting"` (game created, waiting for second player), `"ongoing"` (both players joined and play is active), `"over"` (game ended).
- `winner` — `"goat"`, `"tiger"`, or `null` while the game is live.
- `newPosition` / `previousPosition` — the last move's destination / origin, for animation. Empty string if no move yet.
- `isCaptured` — boolean, true when the last move was a capture.
- `player` — maps role → username. Empty string means that role is unassigned.
- `history` — array of human-readable move strings like `"goat: placed at 1-2"` or `"tiger: 0-0 -> 1-1"`. Used by the move history UI.

**Goat win:** when all tigers are blocked (can't move and can't capture), `status` becomes `"over"`, `winner` is `"goat"`.

**Tiger win:** when 5 goats have been captured (`deadGoatCount` reaches 5), `status` becomes `"over"`, `winner` is `"tiger"`.

---

### `playerLeft`

```json
{
  "event": "playerLeft",
  "payload": {
    "username": "alice",
    "role": "goat"
  }
}
```

A player left the game cleanly (via `leave`). The frontend may want to show a notice and update the player list. The game may continue if the other player remains.

---

### `playerDisconnected`

```json
{
  "event": "playerDisconnected",
  "payload": {
    "username": "alice",
    "role": "goat"
  }
}
```

A player's WebSocket dropped unexpectedly. Same payload shape as `playerLeft`. The frontend should treat it similarly (player is gone), though the backend may try to keep the game alive briefly for a reconnect.

**Your own disconnect:** if the `username` in the event matches your username, the frontend's `WebSocketContext` calls `disconnect()`. Don't reconnect blindly — you'd need to rejoin via HTTP first.

---

### `gameOver`

```json
{
  "event": "gameOver",
  "payload": {
    "winner": "tiger",
    "endReason": "goats_captured"
  }
}
```

The game ended. `winner` is `"goat"` or `"tiger"`. `endReason` is a string like `"goats_captured"` (tiger won by capturing 5 goats) or `"tigers_blocked"` (goat won by blocking all tigers).

**Frontend contract:** the `WinnerModal` component is driven by this event (via the context's `winnerModalOpen`/`winner`). The modal shows the winner and a "Return Home" button.

**Important:** the game-ending move also sends a `gameState` with `status: "over"` and the final board. Both arrive. The frontend's `Game.jsx` opens the modal on either `gameState.status === "over"` or the `gameOver` event. Don't depend on only one.

---

### `error`

```json
{
  "event": "error",
  "payload": {
    "code": "<error_code>",
    "message": "<human readable>"
  }
}
```

Error codes you may see:
- `invalid_message` — malformed or unsupported command.
- `not_authenticated` — no valid user for the connection.
- `not_in_game` — user is not a participant in this game.
- `not_your_turn` — move submitted out of turn.
- `invalid_move` — move failed domain validation.
- `game_not_found` — game does not exist.
- `game_already_over` — action on a finished game.
- `connection_error` — connection setup or session error (e.g. game missing, you're not a player, or a setup exception).

**On error:** log it, show a user-friendly message if it's actionable, but don't treat every error as fatal. Some (like `invalid_move`) are expected during normal play.

---

## Board geometry (needed for moves)

- The board is a 5x5 lattice of intersection points. Rows 0-4, columns 0-4.
- Coordinates are `"row-col"` strings, 0-indexed. Example: `"2-2"` is the center.
- Tigers start at the four corners: `(0,0)`, `(0,4)`, `(4,0)`, `(4,4)`.
- Goats start off-board; they're placed one at a time during the placement phase.
- A tiger can move one step along the lattice to an adjacent empty intersection, or capture by jumping over an adjacent goat to the next intersection (the goat is removed).
- A goat, during placement, is placed on any empty intersection. During displacement (after all 20 goats are placed), goats can move to adjacent empty intersections to block tigers.
- Win for tigers: capture 5 goats.
- Win for goats: block all tigers so none can move or capture.

For move validation, see `backend/baghchal/game_engine/board.py` and `game_state.py` if you need the exact rules. The frontend's `MoveValidation.js` and `GameUtils.js` mirror the same logic for optimistic UI.

---

## Error handling guidelines

1. **HTTP 401** — token expired or missing. Try refreshing the access token via `POST /token/refresh/` with your refresh token. If that fails, re-login (guest login if you're a guest).
2. **HTTP 400** with an `error` string — show it to the user where it makes sense (e.g. "Game ID and username required", "Cannot join a game twice").
3. **WS `error` events** — these are server-side responses to bad commands. Show `payload.message` for user-actionable ones (`invalid_move`, `not_your_turn`). Ignore or log `invalid_message` from experiments.
4. **WS close code 4001** — unauthenticated. Re-establish the token and reconnect.
5. **WS close code 4000** — server-side setup error. The `close_with_error` path sends an `error` event before closing; handle that event before the socket drops.
6. **Game disappears** — if you get `game_not_found` or the game vanishes from state, the game may have been archived/cleaned up. You can't resume; go back to home and create/join again.

---

## Current known gaps / things that may change

- **Quick match race:** two simultaneous quick matches can both create new games. The matching is best-effort.
- **`baghchal_game` table:** the `Game` model migration must be applied for archival and user stats to work. If you see `no such table: baghchal_game`, the migration is missing.
- **Migrations are gitignored** in this repo (`backend/*/migrations/`). Anyone setting up from scratch needs to run `manage.py migrate`. If a migration is missing, create it.
- **`GOOGLE_CLIENT_ID`** — must be set in `backend/.env` for Google login to work. Without it, the Google endpoint returns 500.
- **Migrations/legacy code:** some older paths still exist alongside the new hexagonal layers. The consumer speaks the new envelope but bridges the legacy `message` envelope for backwards compatibility. Prefer the new envelope (`command`/`payload`) in any new frontend code.
- **`async_update_game_state`:** imported from `baghchal.game_engine.services`, not from the package `__init__` (the package re-exports it, but the persistence layer imports from `services` directly to avoid a legacy wrapper). If you're writing new persistence code, import from `baghchal.game_engine.services`.

---

## Where to look in the code

| Concern | Path |
|---|---|
| Auth views (signup/login/guest/google/stats) | `backend/core/views.py` |
| Auth URL routing | `backend/core/urls.py` |
| User model + serializer | `backend/core/models.py`, `backend/core/serializers.py` |
| Game HTTP views (create/join/rejoin/quick-match) | `backend/baghchal/views.py` |
| Game URL routing | `backend/baghchal/urls.py` |
| Root URL config | `backend/backend/urls.py` |
| WebSocket consumer | `backend/baghchal/consumers.py` |
| WS routing | `backend/baghchal/routing.py` |
| Game state + move logic | `backend/baghchal/game_engine/game_state.py`, `board.py` |
| Move orchestration with persistence callbacks | `backend/baghchal/game_engine/services.py` |
| Gateway (session + dispatch) | `backend/baghchal/gateway/game_gateway.py`, `session.py`, `commands.py`, `errors.py` |
| Persistence (Redis store) | `backend/baghchal/persistence/store.py` |
| Play lifecycle (move/leave/disconnect) | `backend/baghchal/persistence/play.py` |
| HTTP persistence helpers | `backend/baghchal/persistence/views.py` |
| Game archival (ORM) | `backend/baghchal/persistence/archival.py` |
| Game ORM model | `backend/baghchal/models.py` |
| Protocol doc (in-code) | `backend/baghchal/protocol.md`, `backend/baghchal/architecture.md` |
| JWT auth middleware | `backend/backend/middleware.py` |

Settings/env: `backend/backend/settings.py` reads `SECRET_KEY`, `DEBUG`, `REDIS_URL`, `ALLOWED_HOSTS` etc. from env. See `backend/.env` (gitignored) for the local values.

