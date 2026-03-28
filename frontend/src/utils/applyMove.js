/**
 * Client-side move applicator that mirrors backend apply_move logic.
 * Used for optimistic UI updates to avoid waiting for server round-trip.
 *
 * Mirrors: backend/baghchal/utils.py :: apply_move()
 */

/**
 * Calculates the middle key between two board positions for capture validation.
 * @param {string} fromKey - e.g. "0-0"
 * @param {string} toKey - e.g. "2-2"
 * @returns {string} middle key e.g. "1-1"
 */
const getMidKey = (fromKey, toKey) => {
  const [fromRow, fromCol] = fromKey.split("-").map(Number);
  const [toRow, toCol] = toKey.split("-").map(Number);
  const midRow = (fromRow + toRow) / 2;
  const midCol = (fromCol + toCol) / 2;
  return `${midRow}-${midCol}`;
};

/**
 * Applies a validated move to the game state and returns a new state.
 * Returns null if the move type is unrecognized.
 *
 * @param {object} gameState - Current game state
 * @param {object} move - Move object { moveType, fromKey, toKey, currentPlayer }
 * @returns {object|null} New game state after applying the move, or null on failure
 */
const applyMove = (gameState, move) => {
  // Deep copy to avoid mutating existing state
  const newState = JSON.parse(JSON.stringify(gameState));

  const board = newState.board;
  const currentPlayer = newState.currentPlayer;
  const { moveType, fromKey, toKey } = move;

  newState.isCaptured = false;

  if (moveType === "place") {
    board[toKey] = "goat";
    newState.unusedGoat -= 1;
    if (newState.unusedGoat === 0) {
      newState.phase = "displacement";
    }
  } else if (moveType === "displace") {
    const piece = board[fromKey];
    delete board[fromKey];
    board[toKey] = piece;
  } else if (moveType === "capture") {
    const piece = board[fromKey];
    delete board[fromKey];
    board[toKey] = piece;
    const midKey = getMidKey(fromKey, toKey);
    if (board[midKey] === "goat") {
      delete board[midKey];
      newState.deadGoatCount += 1;
      newState.isCaptured = true;
    }
  } else {
    return null;
  }

  // Switch player
  newState.currentPlayer = currentPlayer === "goat" ? "tiger" : "goat";
  newState.newPosition = toKey;
  newState.previousPosition = fromKey || null;

  return newState;
};

export default applyMove;
