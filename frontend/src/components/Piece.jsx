import { useState } from "react";
import goat from "../assets/images/goat.png";
import tiger from "../assets/images/tiger.png";

const Piece = ({
  x,
  y,
  row,
  col,
  radius,
  pieceType = null,
  isSelected = false,
  isHighlighted = false,
  isPreviousPosition = false,
  isNewPosition = false,
  onClick,
  onHover,
}) => {
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseEnter = () => {
    setIsHovered(true);
    onHover(row, col, true);
  };

  const handleMouseLeave = () => {
    setIsHovered(false);
    onHover(row, col, false);
  };

  // Circle styles based on state
  const getCircleStyle = () => {
    let fill = "var(--color-piece-bg)"; // Matches board background
    let stroke = "var(--color-piece-stroke)"; // Dark brown
    let strokeWidth = 2;

    if (isSelected) {
      stroke = "var(--color-piece-selected)"; // Brand red
      strokeWidth = 4;
    } else if (isNewPosition) {
      stroke = "var(--color-piece-new)"; // Bright green
      strokeWidth = 4;
    } else if (isPreviousPosition) {
      stroke = "var(--color-piece-previous)"; // Amber
      strokeWidth = 4;
    } else if (isHighlighted) {
      stroke = "var(--color-piece-highlighted)"; // Green
      strokeWidth = 3;
    } else if (isHovered) {
      strokeWidth = 3;
      fill = "var(--color-piece-hover-fill)"; // Lighter warm tone
      stroke = "var(--color-piece-stroke-hover)"; // Medium brown
    }

    return {
      fill,
      stroke,
      strokeWidth,
      cursor: "pointer",
    };
  };

  // Render piece image if present
  const renderPiece = () => {
    if (!pieceType) return null;

    const imageSize = radius * 1.8;
    const imageX = x - imageSize / 2;
    const imageY = y - imageSize / 2;

    return (
      <image
        x={imageX}
        y={imageY}
        width={imageSize}
        height={imageSize}
        href={pieceType === "tiger" ? tiger : goat}
        style={{
          pointerEvents: "none",
          filter: "drop-shadow(0 2px 4px rgba(0,0,0,0.3))",
        }}
      />
    );
  };

  return (
    <g>
      {/* Base circle */}
      <circle
        cx={x}
        cy={y}
        r={radius}
        style={getCircleStyle()}
        onClick={() => {
          onClick(row, col, pieceType);
        }}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        data-row={row}
        data-col={col}
      />
      {/* Piece (tiger or goat) */}
      {renderPiece()}
    </g>
  );
};

export default Piece;
