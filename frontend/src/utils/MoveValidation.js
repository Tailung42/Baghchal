const moveConnections = {
  // Row 0
  "0-0": ["0-1", "1-0", "1-1"], // diagonal to 1-1
  "0-1": ["0-0", "0-2", "1-1"], // vertical to 1-1
  "0-2": ["0-1", "0-3", "1-1", "1-2", "1-3"], // diagonals to 1-1, 1-3 and vertical to 1-2
  "0-3": ["0-2", "0-4", "1-3"], // vertical to 1-3
  "0-4": ["0-3", "1-3", "1-4"], // diagonal to 1-3

  // Row 1
  "1-0": ["0-0", "1-1", "2-0"],
  "1-1": ["0-0", "0-1", "0-2", "1-0", "1-2", "2-0", "2-1", "2-2"], // center connections
  "1-2": ["0-2", "1-1", "1-3", "2-2"], // vertical connections
  "1-3": ["0-2", "0-3", "0-4", "1-2", "1-4", "2-2", "2-3", "2-4"], // center connections
  "1-4": ["0-4", "1-3", "2-4"], // diagonal to 2-3

  // Row 2 (center row)
  "2-0": ["1-0", "1-1", "2-1", "3-0", "3-1"], // diagonal to 1-1, 3-1
  "2-1": ["1-1", "2-0", "2-2", "3-1"],
  "2-2": ["1-1", "1-2", "1-3", "2-1", "2-3", "3-1", "3-2", "3-3"], // center point - all adjacent
  "2-3": ["1-3", "2-2", "2-4", "3-3"], // connections
  "2-4": ["1-3", "1-4", "2-3", "3-3", "3-4"], // diagonal to 1-3, 3-3

  // Row 3
  "3-0": ["2-0", "3-1", "4-0"], // diagonal to 2-1, 4-1
  "3-1": ["2-0", "2-1", "2-2", "3-0", "3-2", "4-0", "4-1", "4-2"], // center connections
  "3-2": ["2-2", "3-1", "3-3", "4-2"], // vertical connections
  "3-3": ["2-2", "2-3", "2-4", "3-2", "3-4", "4-2", "4-3", "4-4"], // center connections
  "3-4": ["2-4", "3-3", "4-4"], // diagonal to 2-3, 4-3

  // Row 4
  "4-0": ["3-0", "3-1", "4-1"], // diagonal to 3-1
  "4-1": ["3-1", "4-0", "4-2"], // vertical to 3-1
  "4-2": ["3-1", "3-2", "3-3", "4-1", "4-3"], // diagonals to 3-1, 3-3 and vertical to 3-2
  "4-3": ["3-3", "4-2", "4-4"],
  "4-4": ["3-3", "3-4", "4-3"], // diagonal to 3-3
};

const captureConnections = {
  "0-0": ["0-2", "2-0", "2-2"],
  "0-1": ["0-3", "2-1"],
  "0-2": ["0-0", "0-4", "2-0", "2-2", "2-4"], // added 2-0, 2-4
  "0-3": ["0-1", "2-3"],
  "0-4": ["0-2", "2-2", "2-4"],

  "1-0": ["1-2", "3-0"],
  "1-1": ["1-3", "3-1", "3-3"], // added 3-3
  "1-2": ["1-0", "1-4", "3-2"], // can capture horizontally across center
  "1-3": ["1-1", "3-1", "3-3"], // added 3-1
  "1-4": ["1-2", "3-4"],

  "2-0": ["0-0", "0-2", "2-2", "4-0", "4-2"], // added 0-2, 4-2
  "2-1": ["0-1", "2-3", "4-1"], // added 2-3 (horizontal capture)
  "2-2": ["0-0", "0-2", "0-4", "2-0", "2-4", "4-0", "4-2", "4-4"],
  "2-3": ["0-3", "2-1", "4-3"], // added 2-1 (horizontal capture)
  "2-4": ["0-2", "0-4", "2-2", "4-2", "4-4"], // added 0-2, 4-2

  "3-0": ["1-0", "3-2"],
  "3-1": ["1-1", "1-3", "3-3"], // added 1-3
  "3-2": ["1-2", "3-0", "3-4"], // can capture vertically across center
  "3-3": ["1-1", "1-3", "3-1"], // added 1-1
  "3-4": ["1-4", "3-2"],

  "4-0": ["2-0", "2-2", "4-2"],
  "4-1": ["2-1", "4-3"],
  "4-2": ["2-0", "2-2", "2-4", "4-0", "4-4"], // added 2-0, 2-4
  "4-3": ["2-3", "4-1"],
  "4-4": ["2-2", "2-4", "4-2"],
};

const ValidateMove = (fromKey, toKey, pieceType, GameBoard) => {
  if (GameBoard[toKey]) {
    return null;
  }
  if (!fromKey) {
    return null;
  }
  if (moveConnections[fromKey].includes(toKey)) {
    console.log("displace");
    return "displace";
  }

  // for capture moves
  if (pieceType == "tiger" && captureConnections[fromKey].includes(toKey)) {
    return isValidCapture(fromKey, toKey, GameBoard);
  }
};

const isValidCapture = (fromKey, toKey, GameBoard) => {
  const [fromRow, fromCol] = fromKey.split("-").map(Number);
  const [toRow, toCol] = toKey.split("-").map(Number);
  const midRow = (fromRow + toRow) / 2;
  const midCol = (fromCol + toCol) / 2;
  const midKey = `${midRow}-${midCol}`;

  if (GameBoard[midKey] === "goat") {
    console.log("capture");
    return "capture";
  }
};

export default ValidateMove;
