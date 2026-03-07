import { useState, useEffect, useRef } from "react";
import Piece from "./Piece";
import ValidateMove from "../utils/MoveValidation";
import { useAuth } from "../hooks/useAuth";
import { useUsername } from "../hooks/useUsername";

const Board = ({
  board,
  turn,
  phase,
  onMoveSend,
  player,
  newPosition,
  previousPosition,
}) => {
  const { username } = useUsername();
  const { auth } = useAuth();
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 400, height: 400 });

  const boardSize = 4;

  // Calculate responsive dimensions
  const containerPadding = 0;
  const availableSize =
    Math.min(dimensions.width, dimensions.height) - containerPadding;
  const cellSize = availableSize / 5;
  const pieceRadius = Math.max(cellSize * 0.25, 8);
  const padding = cellSize / 2;
  const svgSize = availableSize;

  const [boardState, setboardState] = useState({
    selectedPiece: null,
    activePiece: null,
  });

  // Handle window resize and container size changes
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const container = containerRef.current;
        const rect = container.getBoundingClientRect();

        const containerWidth = rect.width;
        const containerHeight = rect.height;

        const maxSize = Math.min(containerWidth, containerHeight);

        setDimensions({
          width: maxSize,
          height: maxSize,
        });
      }
    };

    const timer = setTimeout(updateDimensions, 0);

    window.addEventListener("resize", updateDimensions);

    let resizeObserver;
    if (window.ResizeObserver && containerRef.current) {
      resizeObserver = new ResizeObserver(updateDimensions);
      resizeObserver.observe(containerRef.current);
    }

    return () => {
      clearTimeout(timer);
      window.removeEventListener("resize", updateDimensions);
      if (resizeObserver) {
        resizeObserver.disconnect();
      }
    };
  }, []);

  // handle piece clicks
  const handlePieceClick = (row, col, pieceType) => {
    if (!(player[turn] === username)) return;

    const pieceKey = `${row}-${col}`;
    handleSelection(row, col, pieceType);

    const fromKey = boardState.activePiece;
    const toKey = pieceKey;
    const moveType =
      ValidateMove(fromKey, toKey, board[boardState.activePiece], board) ||
      (phase == "placement" && !board[pieceKey] && turn == "goat"
        ? "place"
        : "");

    if (moveType) {
      const move = {
        moveType: moveType,
        currentPlayer: turn,
        pieceType: board[boardState.activePiece],
        fromKey: fromKey,
        toKey: toKey,
      };
      setboardState((prev) => ({
        ...prev,
        selectedPiece: null,
        activePiece: null,
      }));
      onMoveSend(move);
    }
  };

  // Todo: implement handle piece hover
  const handlePieceHover = (row, col, isEntering) => {};

  // draw grid lines
  const renderGridLines = () => {
    const lines = [];
    const strokeWidth = Math.max(2, cellSize * 0.012);

    for (let row = 0; row <= boardSize; row++) {
      const y = padding + row * cellSize;
      lines.push(
        <line
          key={`h-${row}`}
          x1={padding}
          y1={y}
          x2={padding + boardSize * cellSize}
          y2={y}
          stroke="var(--color-stroke-board)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />,
      );
    }
    for (let col = 0; col <= boardSize; col++) {
      const x = padding + col * cellSize;
      lines.push(
        <line
          key={`v-${col}`}
          x1={x}
          y1={padding}
          x2={x}
          y2={padding + boardSize * cellSize}
          stroke="var(--color-stroke-board)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />,
      );
    }
    return lines;
  };

  // draw diagonals
  const renderDiagonalLines = () => {
    const lines = [];
    const startX = padding;
    const startY = padding;
    const endX = padding + boardSize * cellSize;
    const endY = padding + boardSize * cellSize;
    const centerX = padding + 2 * cellSize;
    const centerY = padding + 2 * cellSize;

    const strokeWidth = Math.max(1.5, cellSize * 0.01);

    // main diagonals
    lines.push(
      <line
        key="main-diag-1"
        x1={startX}
        y1={startY}
        x2={endX}
        y2={endY}
        stroke="var(--color-stroke-board)"
        strokeWidth={strokeWidth}
        strokeLinecap="round"
      />,
    );
    lines.push(
      <line
        key="main-diag-2"
        x1={endX}
        y1={startY}
        x2={startX}
        y2={endY}
        stroke="var(--color-stroke-board)"
        strokeWidth={strokeWidth}
        strokeLinecap="round"
      />,
    );

    // quadrant diagonals
    const quadrants = [
      { x1: startX, y1: startY, x2: centerX, y2: centerY },
      { x1: centerX, y1: startY, x2: endX, y2: centerY },
      { x1: startX, y1: centerY, x2: centerX, y2: endY },
      { x1: centerX, y1: centerY, x2: endX, y2: endY },
    ];

    quadrants.forEach((quad, index) => {
      lines.push(
        <line
          key={`quad-diag-1-${index}`}
          x1={quad.x1}
          y1={quad.y1}
          x2={quad.x2}
          y2={quad.y2}
          stroke="var(--color-stroke-board)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />,
      );
      lines.push(
        <line
          key={`quad-diag-2-${index}`}
          x1={quad.x2}
          y1={quad.y1}
          x2={quad.x1}
          y2={quad.y2}
          stroke="var(--color-stroke-board)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />,
      );
    });

    return lines;
  };

  // render all the pieces on board
  const renderPieces = () => {
    const pieces = [];
    for (let row = 0; row <= boardSize; row++) {
      for (let col = 0; col <= boardSize; col++) {
        const x = padding + col * cellSize;
        const y = padding + row * cellSize;
        const pieceKey = `${row}-${col}`;
        const pieceType = board[pieceKey] || null;

        pieces.push(
          <Piece
            key={pieceKey}
            x={x}
            y={y}
            row={row}
            col={col}
            radius={pieceRadius}
            pieceType={pieceType}
            isSelected={boardState.selectedPiece === pieceKey}
            onClick={handlePieceClick}
            onHover={handlePieceHover}
            isPreviousPosition={previousPosition === pieceKey}
            isNewPosition={newPosition === pieceKey}
          />,
        );
      }
    }
    return pieces;
  };

  // handle selection logic
  const handleSelection = (row, col, pieceType) => {
    const pieceKey = `${row}-${col}`;

    const isValidSelection = (pieceKey, pieceType) => {
      // goat logic
      if (turn === "goat") {
        if (phase === "placement" && pieceType === null) {
          return true;
        } else if (phase === "displacement" && pieceType == "goat") {
          setboardState((prev) => ({ ...prev, activePiece: pieceKey }));
          return true;
        } else if (
          phase == "displacement" &&
          board[boardState.activePiece] === "goat" &&
          !pieceType
        ) {
          return true;
        }
      }
      // tiger logic
      if (turn === "tiger") {
        if (pieceType === "tiger") {
          setboardState((prev) => ({ ...prev, activePiece: pieceKey }));
          return true;
        } else if (!pieceType && board[boardState.activePiece] === "tiger") {
          return true;
        }
      }
      return false;
    };

    if (isValidSelection(pieceKey, pieceType)) {
      if (boardState.selectedPiece === pieceKey) {
        setboardState((prev) => ({
          ...prev,
          selectedPiece: null,
          activePiece: null,
        }));
        console.log(
          `disselected Piece at (${row}, ${col}) with piece: ${pieceType}`,
        );
      } else {
        setboardState((prev) => ({
          ...prev,
          selectedPiece: pieceKey,
        }));
        console.log(
          `selected Piece at (${row}, ${col}) with piece: ${pieceType}`,
        );
      }
    }
  };

  return (
    <div
      ref={containerRef}
      className="h-full w-full aspect-square flex items-center justify-center p-2 md:p-4"
    >
      <div
        className="relative"
        style={{
          width: svgSize + containerPadding,
          height: svgSize + containerPadding,
          maxWidth: "100%",
          maxHeight: "100%",
        }}
      >
        {/* Decorative corner accents */}
        <div className="absolute -top-2 -left-2 w-6 h-6 border-t-2 border-l-2 border-primary rounded-tl-lg"></div>
        <div className="absolute -top-2 -right-2 w-6 h-6 border-t-2 border-r-2 border-primary rounded-tr-lg"></div>
        <div className="absolute -bottom-2 -left-2 w-6 h-6 border-b-2 border-l-2 border-primary rounded-bl-lg"></div>
        <div className="absolute -bottom-2 -right-2 w-6 h-6 border-b-2 border-r-2 border-primary rounded-br-lg"></div>

        <div
          className="border-2 border-border-muted rounded-lg shadow-2xl bg-bg-board overflow-hidden"
          style={{
            width: svgSize + containerPadding,
            height: svgSize + containerPadding,
            maxWidth: "100%",
            maxHeight: "100%",
          }}
        >
          <svg
            width={svgSize}
            height={svgSize}
            className="w-full h-full"
            viewBox={`0 0 ${svgSize} ${svgSize}`}
            style={{
              display: "block",
              margin: containerPadding / 2,
            }}
          >
            {/* Background pattern for texture */}
            <defs>
              <pattern
                id="woodGrain"
                x="0"
                y="0"
                width="100"
                height="100"
                patternUnits="userSpaceOnUse"
              >
                <rect width="100" height="100" fill="#e8dcc8" />
                <path
                  d="M0,10 Q25,15 50,10 T100,10"
                  stroke="#d4c4a8"
                  strokeWidth="0.5"
                  fill="none"
                  opacity="0.3"
                />
                <path
                  d="M0,30 Q25,35 50,30 T100,30"
                  stroke="#d4c4a8"
                  strokeWidth="0.5"
                  fill="none"
                  opacity="0.3"
                />
                <path
                  d="M0,50 Q25,55 50,50 T100,50"
                  stroke="#d4c4a8"
                  strokeWidth="0.5"
                  fill="none"
                  opacity="0.3"
                />
                <path
                  d="M0,70 Q25,75 50,70 T100,70"
                  stroke="#d4c4a8"
                  strokeWidth="0.5"
                  fill="none"
                  opacity="0.3"
                />
                <path
                  d="M0,90 Q25,95 50,90 T100,90"
                  stroke="#d4c4a8"
                  strokeWidth="0.5"
                  fill="none"
                  opacity="0.3"
                />
              </pattern>
            </defs>
            <rect width={svgSize} height={svgSize} fill="url(#woodGrain)" />

            <g>{renderGridLines()}</g>
            <g>{renderDiagonalLines()}</g>
            <g>{renderPieces()}</g>
          </svg>
        </div>
      </div>
    </div>
  );
};

export default Board;
