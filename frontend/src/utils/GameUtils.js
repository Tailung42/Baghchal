const getMidKey = (fromKey, toKey) => {
  const [fromRow, fromCol] = fromKey.split("-").map(Number);
  const [toRow, toCol] = toKey.split("-").map(Number);
  const midRow = (fromRow + toRow) / 2;
  const midCol = (fromCol + toCol) / 2;
  return `${midRow}-${midCol}`;
};

const toUserCoord = (key) => {
  if (!key) return "";
  const [r, c] = key.split("-").map(Number);
  return `${r + 1}-${c + 1}`;
};

const deepClone = (obj) => JSON.parse(JSON.stringify(obj));

export const applyMove = (gameState, move) => {
  const newGameState = deepClone(gameState);

  const board = newGameState.board;
  const currentPlayer = newGameState.currentPlayer;
  const moveType = move.moveType;
  const fromKey = move.fromKey;
  const toKey = move.toKey;

  newGameState.isCaptured = false;

  if (moveType === "place") {
    board[toKey] = "goat";
    newGameState.unusedGoat -= 1;
    if (newGameState.unusedGoat === 0) {
      newGameState.phase = "displacement";
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
      newGameState.deadGoatCount += 1;
      newGameState.isCaptured = true;
    }
  }

  const userFrom = toUserCoord(fromKey);
  const userTo = toUserCoord(toKey);

  let historyEntry;
  if (moveType === "place") {
    historyEntry = `${currentPlayer}: placed at ${userTo}`;
  } else {
    historyEntry = `${currentPlayer}: ${userFrom} -> ${userTo}`;
  }

  newGameState.history = [...newGameState.history, historyEntry];

  newGameState.currentPlayer = currentPlayer === "goat" ? "tiger" : "goat";
  newGameState.newPosition = toKey;
  newGameState.previousPosition = fromKey;

  return newGameState;
};

export const compareGameStates = (state1, state2) => {
  if (!state1 || !state2) return false;
  return (
    JSON.stringify(state1.board) === JSON.stringify(state2.board) &&
    state1.currentPlayer === state2.currentPlayer &&
    state1.phase === state2.phase &&
    state1.unusedGoat === state2.unusedGoat &&
    state1.deadGoatCount === state2.deadGoatCount &&
    state1.status === state2.status &&
    state1.winner === state2.winner &&
    state1.newPosition === state2.newPosition &&
    state1.previousPosition === state2.previousPosition
  );
};
