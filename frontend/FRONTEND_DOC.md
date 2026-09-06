# Frontend Architecture & Contracts

Intended for engineers working on the React/TypeScript-ish (JSX) frontend. Source of truth is the code in `frontend/src/`; this doc captures modules, the API/WS contracts the frontend speaks, and the behaviors that are easy to break.

## Stack & entry points

- React + React Router DOM (browser router).
- Vite dev server (`npm run dev`) serves the SPA on `:5173` and proxies to the backend for API/WS during dev.
- Build: `npm run build`.
- Tests: `npm run test:run` (vitest, jsdom env).

**Entry:** `frontend/src/main.jsx` mounts `App`. `App.jsx` wraps everything in `GoogleOAuthProvider` → `AuthProvider` → router with `WebSocketProvider` inside the Layout tree.

**Routing:**
- `/` — Home (create / join / quick match).
- `/game/:gameId` — Game page.
- `/rules` — Rules page.
- `/user` — UserProfile (own profile).
- `:username` — UserProfile (any user's profile; also the path used for the sidebar user link).
- `AuthModal` is rendered outside the router as an overlay (login/signup/google).

**Layout:** `Layout.jsx` renders a fixed sidebar (`SideBar`) + `Outlet`. The sidebar shows the current username, a home button, rules, and a login/logout toggle. Mobile has a hamburger nav. The sidebar user card navigates to `/${username}` on click.

---

## Environment variables (frontend)

All exposed to the app via `import.meta.env.VITE_*`. Defined in `frontend/.env` (gitignored).

| Variable | Used for | Default (if missing) |
|---|---|---|
| `VITE_BASE_HTTP_URL` | Axios base URL for all API calls | `http://127.0.0.1:8000/` |
| `VITE_BASE_WS_URL` | WebSocket base URL | (must be set for WS to work) |
| `VITE_GOOGLE_CLIENT_ID` | Google OAuth client ID passed to `GoogleOAuthProvider` | undefined — Google login breaks without it |

The HTTP base URL should end with `/` (the Axios client appends paths to it). The WS base URL must be `ws://...` (or `wss://` in production), without a trailing path — the consumer expects `/ws/game/?game_id=...`.

**Important:** the Axios client in `frontend/src/api/client.js` creates one `api` instance with `baseURL: API_BASE_URL`. All exported `authApi`, `gameApi`, `userApi` use that instance. Don't create separate axios instances or you'll bypass the interceptor.

---

## API client (`frontend/src/api/client.js`)

One axios instance, with a request interceptor that attaches the JWT access token from storage.

```js
import { authApi, gameApi, userApi } from "./api/client";
```

### `authApi`

- `login(username, password)` → `POST /login/`
- `signup(formData)` → `POST /signup/` (multipart/form-data — pass a `FormData`, not a JSON body)
- `googleAuth(token, mode)` → `POST /auth/google`
- `guestLogin(guestId)` → `POST /guest-login/` with `{ guest_id: guestId }`

### `gameApi`

- `create(gameId, playerRole)` → `POST /game/create/` with `{ game_id, player_role }`
- `join(gameId)` → `POST /game/join/` with `{ game_id }`
- `rejoin(gameId)` → `POST /game/rejoin/` with `{ game_id }`
- `quickMatch()` → `POST /game/quick-match/`

All game endpoints return `{ game_id, ... }` on success. The full initial game state is not in the HTTP response — it comes via the WebSocket `gameState` event after you connect.

### `userApi`

- `getProfile(username)` → `GET /users/<username>/`

Returns the user stats object. The frontend's `UserProfile` spreads `res.data` onto a `{ username, ...data }` shape.

### Error handling in the client

The axios interceptor only adds the token; it doesn't transform errors. Components catch errors from the promises and read `error.response?.data?.error` (or `error.message` for timeouts). The `AuthModal` has its own `getErrorMessage` helper that normalizes DRF error shapes.

### Timeouts on game actions

`Home.jsx`'s modal wraps `joinGame` and `quickMatch` in `Promise.race` with a timeout (60s for join, 90s for quick match). If the race rejects with a `JOIN_GAME_TIMEOUT` / `QUICK_MATCH_TIMEOUT` message, the modal shows a user-friendly timeout error. Don't remove these without updating the UI.

---

## Auth context (`frontend/src/context/AuthContext.jsx`)

`AuthProvider` holds `{ auth, isLoading, login, signup, googleAuth, logout }`.

`auth` shape: `{ user: <user_data or null>, guest: <guest_data or null> }`. You're either logged in as a real user (`auth.user`) or a guest (`auth.guest`), not both.

`useAuth()` returns the context value. Used widely: `useUsername()` derives the display username from `auth.user?.username || auth.guest?.username`.

### Guest login flow (the one that touches this bug repeatedly)

1. On mount, if there's no stored user and there's a stored guest with a usable access token, the existing guest session is trusted.
2. If there's a stored guest but no usable token (fresh load or corrupted storage), the app calls `loginAsGuest()`.
3. `loginAsGuest()`:
   - Generates a provisional guest identity immediately via `generateUsername()` from `unique-username-generator` and stores it, so the UI doesn't wait on the network.
   - Calls `authApi.guestLogin(guestId)`.
   - On success: stores `data.user_data` as the guest, stores `data.access`/`data.refresh` as tokens, returns `guest_user`.
   - On failure: keeps the provisional guest so the app is still usable.

**Bug history:** an older version of this code called `authStorage.setToken(guestUser.access, guestUser.refresh)` where `guestUser` was the `user_data` payload (which has no `access`/`refresh`), overwriting the real tokens with the string `"undefined"`. That caused every API call to fail in the interceptor (`JSON.parse("undefined")`). The current code does not do that — `loginAsGuest` stores tokens from `response.data.access/refresh`, and the post-login `finish()` only stores the guest user data.

**If a session is acting up:** clear local storage (the logout button calls `authStorage.clearAll()`) and reload. A guest session is cheap to recreate.

### `loginAsGuest` returns the user_data payload (no tokens)

If you call `loginAsGuest().then(guestUser => ...)` and then try to read `guestUser.access`, you'll get `undefined`. The tokens are in `response.data`, not in the returned value. Don't re-store them from the return value.

---

## Storage (`frontend/src/utils/storage.js`)

Two exports: `authStorage` and `gameStorage`.

### `authStorage`

Keys:
- `user` — `USER_STORAGE_KEY` — stored user_data (real logged-in user).
- `guest` — `GUEST_STORAGE_KEY` — stored guest_data.
- `access_token` — `ACCESS_TOKEN_KEY` — JWT access token (stringified).
- `refresh_token` — `REFRESH_TOKEN_KEY` — JWT refresh token (stringified).

Methods:
- `getToken()` → `[access, refresh]`. Both can be `null`. If either value in localStorage is garbage (e.g. the literal string `"undefined"` from the old bug), it's removed and returns `null`. This self-heals corrupted sessions.
- `setToken(access, refresh)` — only stores if the value is truthy. Passing `undefined` does nothing (this is what prevents the old bug from recurring).
- `setUser(user)` — stores user, clears guest.
- `getUser()` → parsed user object or null.
- `setGuest(guest)` — stores guest, clears user.
- `getGuest()` → parsed guest object or null.
- `clearUser` / `clearGuest` / `clearAll`.

`authStorage.getUsername()` returns `user.username || guest.username || null`.

### `gameStorage`

Keys:
- `gameId` — `GAME_STORAGE_KEY` — stored in `sessionStorage` (not localStorage), so it clears when the tab closes.

Methods:
- `isInGame()` → boolean.
- `setGame(gameId)`.
- `removeGame()`.

**Why sessionStorage:** the game ID is a transient play session; it shouldn't survive a tab close. Auth tokens are in localStorage because you want to stay logged in across reloads.

---

## WebSocket context (`frontend/src/context/WebSocketContext.jsx`)

`WebSocketProvider` manages the single game WebSocket. Exposed via `useWebSocket()`:

```js
const {
  createGame, joinGame, rejoinGame, quickMatch,  // HTTP + connect
  send, sendCommand, disconnect,
  gameState, isConnected, gameId,
  optimisticState, updateOptimisticState, clearOptimisticState,
  winnerModalOpen, setWinnerModalOpen, winner,
} = useWebSocket();
```

### Connection lifecycle

- `connectWebSocket(gameId)` is called after any successful game HTTP action (create/join/rejoin/quickMatch). It closes any existing socket, builds the URL `wsBase?game_id=<id>`, and passes the JWT access token as the subprotocol.
- `createGameHTTP` / `joinGameHTTP` / `rejoinGameHTTP` / `quickMatchHTTP` are the HTTP actions. The outer callbacks (`createGame`, etc.) call the HTTP action, then store the game ID in sessionStorage. The WS connect happens inside `createGameHTTP` after the response.

**Don't call `connectWebSocket` yourself for a new game** — use `createGame`/`joinGame` from `useGame()`, which handle the HTTP + storage + connect sequence.

### Sending commands

- `sendCommand(command, payload)` — sends `{ command, payload }` JSON. This is the new envelope. Use this for `move` and `leave`.
- `send(message)` — raw send. Exists for legacy/compatibility; prefer `sendCommand`.

The frontend sends `move` payloads with `currentPlayer` included (from the current `gameState.currentPlayer`). The backend validates turn, so send the value you have.

### Receiving messages (`handleMessage`)

The server envelope is `{ event: "<type>", payload: {...} }`. `handleMessage` branches on `event`:

- **`gameState`** — updates `gameState` from `payload.game_state`. Clears optimistic state unless it diverges from the server (then warns). If the state has a `game_id` and you're not already on `/game/<id>`, it navigates there.
- **`error`** — logs a warning. Doesn't throw; the UI should surface actionable errors.
- **`playerLeft` / `playerDisconnected`** — if the event's username is you, `disconnect()` is called (you got kicked/disconnected). Otherwise it's a room update.
- **`gameOver`** — sets `winner` from `payload.winner`, sets `winnerModalOpen = true`.

**Important contract detail:** the frontend reads `data.event` (a string) and `data.payload` (an object). Both `communication.test.js` and `protocol.test.js` assert this exact shape. If the backend ever changes `event` to an object, the frontend breaks. Don't change this without updating both test files and the backend.

### Optimistic state

- `optimisticState` — a provisional game state applied immediately on your own move, before the server confirms.
- `updateOptimisticState(newState)` — set it (e.g. after `applyMove`).
- `clearOptimisticState()` — cleared when the server's `gameState` arrives and matches.
- When a move is sent, the typical pattern (in `Game.jsx`) is: compute the optimistic new state via `applyMove`, set it, send the command. When the server's `gameState` comes back, if it matches the optimistic state, clear it; if not, warn (reconciliation needed).

**Don't over-use optimistic state.** It's for smooth UI on your own moves. It should be a strict improvement — if the server disagrees, something is wrong and you should reconcile, not silently override.

### `winnerModalOpen` / `winner`

Driven by the `gameOver` event. The `WinnerModal` is rendered in `Game.jsx` gated on local `modalOpen`, which is set to `true` when either `gameState.status === "over"` or `winnerModalOpen` becomes true. Don't bypass this wiring — the modal is the only game-over UI.

---

## Game hook (`frontend/src/hooks/useGame.js`)

`useGame()` composes the WebSocket context with the HTTP API and session storage. Returns:

- `isInGame` — from `gameStorage.isInGame()`.
- `gameState`, `isConnected` — from context.
- `createGame(gameId, playerRole)` — calls `createGameHTTP`, stores game ID.
- `joinGame(gameId)` — calls `joinGameHTTP`, stores game ID.
- `rejoinGame(gameId)` — calls `rejoinGameHTTP`, stores game ID.
- `quickMatch()` — calls `quickMatchHTTP`, stores game ID.
- `sendMove(move)` — `sendCommand("move", move)`.
- `exitGame()` — removes game from storage, sends `leave`, disconnects.
- `isGameInProgress()` — `gameState?.status !== "over"`.
- `optimisticState`, `updateOptimisticState`, `clearOptimisticState`.

**`isGameInProgress` is used by `useGameNavigation`** (the router blocker). If it returns true while you're on the game page, navigation away is blocked with a confirmation modal. This is why the game-over modal must fire — if the game ends but `status` never becomes `"over"`, you're stuck on the page.

---

## Game navigation / blocker (`frontend/src/hooks/useGameNavigation.js`)

Wraps `useBlocker` from React Router. Blocks navigation away from the game page while `isGameInProgress()` is true. Shows `LeaveConfirmationModal`. On confirm, calls `exitGame()` and proceeds.

`handleGameEnd()` resets the blocker when the game ends (called from the game-over effect in `Game.jsx`). This is what frees you to navigate home after a win/loss.

**If the modal never opens and you can't leave:** either `isGameInProgress()` never became false (no `status: "over"` arrived) or the game-over event never reached the modal wiring. Check the WS events first.

---

## Game page (`frontend/src/routes/Game.jsx`)

State machine in one component:

- Guards: if no auth, navigate home. If not connected or no `displayState`, show a spinner.
- `displayState = optimisticState || gameState` — render the optimistic state if present, else the server state.
- On `gameState.status === "over"` → open modal + `handleGameEnd()`.
- On `winnerModalOpen` → open modal + `handleGameEnd()`.
- On `gameState.newPosition` change (with dedup) → play move sound (`useGameSounds`).
- `handleMoveSend(move)` — compute optimistic state via `applyMove`, set it, play sound, send move.
- `handleWinnerModelClick()` — close modal, clear winner modal flag, `exitGame()`, navigate home.

Renders: `PlayerCard`, `Board`, `GameStatusIndicator`, `WinnerModal`, `WaitingModal`, `LeaveConfirmationModal`.

### Board component (`frontend/src/components/Board.jsx`)

Renders a 5x5 SVG grid (0-4), with grid lines, diagonals, and pieces. Handles piece click → selection → move construction → `onMoveSend`.

The move it constructs includes `moveType`, `currentPlayer`, `pieceType`, `fromKey`, `toKey`. This is what gets sent to `sendMove` → `sendCommand("move", move)`. The `currentPlayer` field is required by the backend; don't strip it.

Selection logic: handles placement (goat places on empty), displacement (goat picks a goat to move, then a destination), and tiger moves/captures. Validates via `ValidateMove` from `MoveValidation.js`.

---

## Game state utilities (`frontend/src/utils/GameUtils.js`)

### `applyMove(gameState, move)`

Returns a new game state with the move applied (for optimistic UI). Mutates a deep clone. Handles:
- `place` — puts a goat on `toKey`, decrements `unusedGoat`, switches to displacement when 0.
- `displace` — moves a piece from `fromKey` to `toKey`.
- `capture` — moves piece, removes the jumped goat if present, increments `deadGoatCount`, sets `isCaptured`.

Also updates `currentPlayer` (toggles goat/tiger), `newPosition`, `previousPosition`, and appends to `history`.

**Note:** `applyMove` does **not** check win conditions or validate the move. It just applies. Validation is in `MoveValidation.js` (`ValidateMove`) and the real authority is the backend.

### `compareGameStates(state1, state2)`

Deep-compares the state fields the frontend cares about (board, currentPlayer, phase, unusedGoat, deadGoatCount, status, winner, newPosition, previousPosition). Used to decide whether to clear optimistic state when the server state arrives.

---

## Move validation (`frontend/src/utils/MoveValidation.js`)

`ValidateMove(fromKey, toKey, pieceType, board)` — returns the move type string if valid, else falsy. Used by `Board.jsx` to decide whether a clicked piece/destination is a legal move for the current board. Mirrors backend rules enough for optimistic UI, but the backend is authoritative.

---

## Modals

- `WinnerModal` (`/components/modals/WinnerModal.jsx`) — shows when `isOpen`. Displays winner and a "Return Home" button. Calls `onClick` on Enter key or backdrop click.
- `WaitingModal` — shown when `gameState.status === "waiting"`.
- `LeaveConfirmationModal` — shown when the router blocker is active and you try to navigate away.

---

## Communication contract (testable)

The frontend's contract is defined and tested in two files:

- `frontend/src/communication.test.js` — defines `CLIENT_COMMANDS = {move, leave}`, `SERVER_EVENTS = {gameState, playerLeft, playerDisconnected, gameOver, error}`, and helpers `parseClientEnvelope`, `makeEvent`, `makeErrorEvent`, `unpackServerEvent`. The tests assert exact envelope shapes.
- `frontend/src/protocol.test.js` — a second assertion of the same contract, independent of the communication helpers.

Both agree: client sends `{ command, payload }`; server sends `{ event (string), payload }`; error payload is `{ code, message }`.

**These tests are the spec.** If you change the wire format, update these tests first. If they pass and the backend's `gateway.commands` contract matches (see backend API doc), you're compatible.

---

## Backend contract alignment

The backend's `baghchal/gateway/commands.py` defines the same `CLIENT_COMMANDS` and `SERVER_EVENTS` sets, plus `parse_client_envelope`, `make_event`, `make_error_event`. The frontend's test helpers are intentionally a mirror of these.

If you ever drift them apart, the tests will catch it — but only if you run both suites. Run backend tests and frontend tests together when changing the protocol.

---

## Common frontend failure modes

1. **API calls failing with `JSON.parse: unexpected character`** — almost always a corrupted token in localStorage. `authStorage.getToken()` now self-heals, but if you're debugging a live session, check what's in localStorage under `access_token`. If it's the string `"undefined"`, clear and reload.
2. **Can't create/join/quick-match but guest session works** — typically the token was overwritten after login. Re-login or clear storage.
3. **Game page stuck, can't navigate away after game ends** — the game-over event/`status: "over"` didn't arrive or wasn't handled. Check WS events. The blocker won't release until `isGameInProgress()` is false.
4. **Winner modal doesn't show** — `winnerModalOpen` may have fired but `modalOpen` wasn't set, or `winner` is empty. Check that the `gameOver` handler in `WebSocketContext` runs and that `Game.jsx`'s effect on `winnerModalOpen` fires.
5. **Move sent but nothing happens** — check `currentPlayer` in the payload matches the current turn. Out-of-turn moves come back as `invalid_move` or `not_your_turn` error events.
6. **WebSocket doesn't connect** — verify `VITE_BASE_WS_URL` is set and `ws://` (not `http://`). Check that the token is being passed as the subprotocol. If the backend is restarting, WS handshakes can be slow.
7. **Profile page 500** — if the backend's `baghchal_game` table is missing, the profile endpoint crashes. That's a backend migration issue, not frontend.
8. **Quick match timeouts** — if no waiting game is available, quick match creates one, which is fast. If it times out (90s), the backend may be down or the store isn't responding. Check backend health at `/health/`.

---

## Where to look

| Concern | Path |
|---|---|
| App shell, routing, providers | `frontend/src/App.jsx`, `frontend/src/main.jsx` |
| Layout + sidebar | `frontend/src/routes/Layout.jsx` |
| Home (create/join/quick match) | `frontend/src/routes/Home.jsx` |
| Game page | `frontend/src/routes/Game.jsx` |
| User profile | `frontend/src/routes/UserProfile.jsx` |
| Rules page | `frontend/src/routes/Rules.jsx` |
| Auth (context + modal) | `frontend/src/context/AuthContext.jsx`, `frontend/src/components/AuthModal.jsx` |
| WebSocket context | `frontend/src/context/WebSocketContext.jsx` |
| Game hook | `frontend/src/hooks/useGame.js` |
| Auth hook / username hook | `frontend/src/hooks/useAuth.js`, `frontend/src/hooks/useUsername.js` |
| Game navigation (blocker) | `frontend/src/hooks/useGameNavigation.js` |
| Join game hook | `frontend/src/hooks/useJoinGame.js` |
| API client | `frontend/src/api/client.js` |
| Storage | `frontend/src/utils/storage.js` |
| Game state + applyMove | `frontend/src/utils/GameUtils.js` |
| Move validation | `frontend/src/utils/MoveValidation.js` |
| Board | `frontend/src/components/Board.jsx` |
| Pieces | `frontend/src/components/Piece.jsx` |
| Player card / status indicator | `frontend/src/components/PlayerCard.jsx`, `frontend/src/components/GameStatusIndicator.jsx` |
| Modals | `frontend/src/components/modals/*.jsx` |
| UI primitives | `frontend/src/components/ui/*.jsx` |
| Communication contract tests | `frontend/src/communication.test.js`, `frontend/src/protocol.test.js` |

Env: `frontend/.env` (gitignored). Vite config: `frontend/vite.config.js`. Test config: `frontend/vitest.config.ts`.

