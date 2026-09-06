# Plan: Play vs Bot (🤖)

Add a "Play vs Bot" mode so a single player can start a game against a
server-side AI opponent. The AI implementation is modeled on the reference
repo `pybaghchal` (`https://github.com/code-geek/pybaghchal`, cloned locally to
`../pybaghchal` for reference only — do not vendor its code, adapt the ideas).

Reference takeaways from `../pybaghchal`:

- `Board.py` — board abstraction with `generate_move_list()`, `make_move()`,
  `revert_move()` (move generation + search-friendly apply/revert).
- `Engine.py` — minimax with alpha-beta pruning (`minmax`), evaluation
  heuristic from the tiger's perspective (`300 * movable_tigers +
  700 * dead_goats - 700 * blocked_spaces - depth`), configurable search
  depth (= difficulty).
- `Game.py` — human vs AI loop; AI plays whichever side is not human.

---

## Current-state gaps (what the bot needs that doesn't exist yet)

| Need | Today | Gap |
|---|---|---|
| Enumerate all legal moves for a player | `is_valid_move(state, move)` only validates a *given* move | No `generate_moves(state)` anywhere in `game_engine` |
| Strict legality (adjacency, capture jumps) | `game_state.is_valid_move` is lenient: it never checks adjacency or that a capture jump has a goat to jump; strictness lives in `frontend/src/utils/MoveValidation.js` | Backend must be authoritative for the bot |
| Position evaluation | — | No heuristic exists |
| Search (minimax / alpha-beta) | — | Nothing (reference `Engine.py` is the model) |
| Fast state copy for search | `apply_move` does `copy.deepcopy` per move | Too slow for deep search; need in-place apply/revert or a lighter search position |
| Game state shape | wire-shaped dict (`board`, `currentPlayer`, `phase`, `unusedGoat`, …) with `player` map and `history` | Keep as canonical wire format — bots operate on the same dict |

---

## Phase 1 — Restructure the application/domain layer (bot-friendly core)

**Goal:** one authoritative, pure-Python game core that both the human pipeline
and the bot use. No Django/Channels/Redis imports (matches existing separation
rules in `backend/baghchal/architecture.md`).

### 1a. Move generation (`backend/baghchal/game_engine/movegen.py`, new)

- `generate_moves(game_state) -> list[dict]` returning the exact same move
  shape the pipeline uses (`{moveType, fromKey, toKey, currentPlayer, pieceType}`).
  - **Placement phase** (`phase == "placement"`): every empty cell for the goat.
  - **Displacement** (goat): every goat piece → empty neighbor via
    `board.MOVE_CONNECTIONS`.
  - **Tiger moves**: slide along `MOVE_CONNECTIONS` OR jump-capture via
    `CAPTURE_CONNECTIONS` when the midpoint holds a goat and the landing cell
    is empty (use `board.can_capture` / `get_mid_key`).
- Driven by the connection tables in `board.py` (single source of truth).

### 1b. Harden validation (`backend/baghchal/game_engine/game_state.py`)

- Tighten `is_valid_move` so it is exactly `move in generate_moves(state)`
  (or shares the same checks). This closes the backend/frontend validation
  gap (`MoveValidation.js` is currently stricter than the server) and makes
  the bot trustworthy. Add tests for the newly rejected moves (non-adjacent
  displacement, fake captures, off-turn moves).

### 1c. Search position adapter (`backend/baghchal/game_engine/search_position.py`, new)

- Small internal representation optimized for the search loop:
  - Lightweight board copy (tuple of occupied cells + counts, not a deepcopy
    of the whole wire dict), or an in-place `apply/revert` pair like the
    reference `Board.make_move/revert_move`.
  - Always a valid dict → can be serialized back to wire `game_state` when
    the bot's move is chosen.
- Keep the wire dict as the canonical public shape; the adapter is internal
  to the search.

### 1e. Evaluation (`backend/baghchal/game_engine/evaluate.py`, new)

- `evaluate_position(game_state) -> float` from the tiger's perspective,
  adapted from the reference heuristic:
  - material: `dead_goat_count` × weight
  - mobility: movable tigers (via `board.is_blocked` / move counts)
  - safety: number of blocked tiger spaces (goat progress)
  - win/loss: `±INF` when `check_tiger_win` / `check_goat_win`
  - small `+depth` bias to prefer faster wins (as in reference)
- Symmetric evaluation for the goat side via `-score`.

### 1f. Search (`backend/baghchal/game_engine/search.py`, new)

- `negamax` (or reference-style minimax) with alpha-beta pruning over
  `generate_moves`.
- Iterative deepening with a **time budget** (not just fixed depth) so the
  server never blocks: e.g. Easy = depth 2 / ~50 ms, Medium = depth 4 /
  ~300 ms, Hard = depth 6 / ~1 s (tuned later).
- Move ordering to make pruning effective (captures first, then slides).
- Deterministic tie-break (stable, so tests are repeatable).

### 1g. Bot player facade (`backend/baghchal/bot/bot.py`, new)

- `choose_bot_move(game_state, *, difficulty) -> move` — the only public
  entry point; pure, sync, no I/O.
- Difficulty mapping lives here.
- Note: keep the `pybaghchal` implementation as a reference for the
  algorithm, not copied code — ours is dict-based and turn-aware.

### Phase 1 tests

- `backend/baghchal/tests/test_movegen.py` — move counts at initial position,
  placement→displacement transition, capture generation, per-player legality.
- `backend/baghchal/tests/test_search.py` — bot finds the winning capture in
  crafted endgame positions; never returns an illegal move; deterministic at
  fixed depth; respects time budget.
- `backend/baghchal/tests/test_evaluate.py` — monotonicity sanity checks
  (more dead goats ⇒ higher tiger score, etc.).
- Keep `test_game_domain.py` green; extend it for the stricter validation.

---

## Phase 2 — API gateway for bot play + storage decision

**Design decision (recommended): the bot is a normal player in a normal room.**
No new wire protocol, no parallel persistence. Reuse the existing gateway /
WS / Redis / archival pipeline so reconnects, stats, and archival "just work".

### 2a. How a bot game is created

- New HTTP endpoint `POST /game/bot/` with `{ player_role: "tiger"|"goat",
  difficulty: "easy"|"medium"|"hard" }`.
- Reuses `persistence/views.create_game` then fills the other role with the
  bot and sets `status = "ongoing"` immediately:
  - `game_state["player"][bot_role] = "🤖 Bot"`
  - `game_state["bot"] = {"role": bot_role, "difficulty": difficulty}`
  - `game_state["opponent_type"] = "bot"`
- Returns `{ game_id }` like every other lifecycle endpoint; the client then
  connects over the existing WebSocket exactly as it does today.

### 2b. How the bot plays (gateway integration)

- The human sends `move` over WS; `consumers._handle_move` →
  `persistence/play.execute_move` applies it and broadcasts `gameState` —
  unchanged.
- After the broadcast, if the new state is not over and
  `currentPlayer == bot.role`, schedule the bot's move:
  - `choose_bot_move(new_state, difficulty)` (Phase 1),
  - apply it through the **same** `execute_move` path (so persistence,
    archival, and events are identical to a human move),
  - broadcast the resulting `gameState` (and `gameOver` if it ends).
- Placement of the hook:
  - New `backend/baghchal/bot/integration.py`: `maybe_trigger_bot_reply(...)`
    called from the consumer after each successful human move. Keep the bot
    decision out of the transport layer as much as possible.
  - Add a small artificial delay (e.g. 400–800 ms) before the bot moves so
    the human sees the board settle and a "Bot is thinking..." moment.
- Serialization: guard against overlapping bot turns (per-room in-flight
  flag or a per-room asyncio task) so two bot moves can never race; the bot
  never acts when `currentPlayer != bot.role`.

### 2c. Storage decision (explicit)

- **Live state:** same Redis store (`persistence/store.py`,
  `game:<game_id>` key, `active_games` set). No new keys, no TTL changes.
  The only addition is the `bot`/`opponent_type` metadata inside the state
  dict.
- **Archived games:** extend `baghchal.models.Game` with
  `opponent_type` (`"bot"`/`"human"`, default `"human"`) and
  `bot_difficulty` (nullable). `persistence/archival.py` reads them from
  `game_state`; `core` user stats are untouched (they already count games by
  player role).
- **Rejected alternatives (recorded, not chosen):**
  - Stateless HTTP turn API (`POST /game/bot/move` → bot reply) — no
    reconnect, no archival, no stats, and the client must own state.
  - Separate Redis key namespace / ORM table for bot games — duplicates the
    live+archival pipeline for no benefit.
- **Guard rails:** humans can't `join` a bot room (bot rooms start
  `ongoing`, and `join_game` rejects ongoing rooms — add an explicit check
  anyway); `quick_match` must skip bot rooms; leaving a bot game behaves
  like leaving a human game (disconnect cleanup already handles it).

### Phase 2 tests

- HTTP: `POST /game/bot/` creates an ongoing room with both roles filled and
  correct `bot` metadata; auth required.
- Consumer/gateway: after a human move, a `gameState` with the bot's reply
  arrives; bot moves are legal; bot never moves when it's the human's turn;
  game-over broadcast works when the bot finishes the game.
- Persistence: bot game archived with `opponent_type="bot"` +
  `bot_difficulty`; `quick_match`/`join` never touch bot rooms.

---

## Phase 3 — Frontend

### 3a. Home (`frontend/src/routes/Home.jsx`)

- New "🤖 Play vs Bot" button (primary style, like Quick Match).
- Opens a modal (reuse `GameModal` pattern): choose role (🐅 Tiger /
  🐐 Goat) and difficulty (Easy / Medium / Hard).
- On submit: same UX as create/quick — blurred loading overlay
  (`LoadingModal`) while `POST /game/bot/` runs, then the WS `gameState`
  event navigates to `/game/<id>` (existing behavior, zero changes needed).
- `useGame`/`useWebSocket` gain a `startBotGame(role, difficulty)` wrapper
  mirroring `createGame` (HTTP + `gameStorage.setGame`).

### 3b. Game page (`frontend/src/routes/Game.jsx`)

- Opponent card: show the bot as `🤖 Bot` with a difficulty badge
  (read from `gameState.player[role]` / `gameState.bot`).
- "Bot is thinking..." indicator: derived from
  `displayState.currentPlayer === botRole && connected` — no new events
  needed.
- No `WaitingModal` for bot games (`status` is `ongoing` from the start, so
  it never appears naturally — just verify).
- Leave/blocker behavior unchanged; leaving a bot game just ends it.

### 3c. API client + contract

- `gameApi.startBot(...)` in `frontend/src/api/client.js`.
- No changes to `communication.test.js` / `protocol.test.js` (wire format is
  unchanged: `move` command in, `gameState`/`gameOver` events out).

### Phase 3 tests

- Component/flow test (or manual checklist): bot button → modal → loading
  overlay → `/game/<id>` with bot opponent; bot replies visible after the
  human moves; difficulty selection reaches the API payload.
- Existing suites stay green (`npm run test:run`, `npm run build`).

---

## Milestones (in order)

1. **M1 — Phase 1 core:** movegen + hardened validation + evaluation +
   search + `choose_bot_move`, all pure, fully unit-tested. Bot can be
   driven from a Python REPL/script against any saved position.
2. **M2 — Phase 2 gateway:** `POST /game/bot/`, bot-reply hook in the
   consumer, storage metadata, guard rails, integration tests. A bot game
   can be played end-to-end from curl + WS client.
3. **M3 — Phase 3 frontend:** Home button/modal, game-page bot UI, client
   API wrapper, manual E2E via the dev stack (backend `:8000`, frontend
   `:5173`).

## Open questions to settle during M1/M2

- Difficulty tuning (depth/time) — benchmark bot latency per move on the
  dev box and pick defaults; expose as constants in `bot/`.
- Should the bot's name/avatar be a configurable constant? (Propose
  `"🤖 Bot"` for now.)
- Do bot games count toward user profile stats exactly like human games?
  (Proposal: yes — same archival path, with `opponent_type` available for
  later filtering.)