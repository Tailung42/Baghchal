import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useGame } from "../hooks/useGame";
import { useUsername } from "../hooks/useUsername";
import { useAuth } from "../hooks/useAuth";
import { useGameSounds } from "../hooks/useGameSounds";
import { useGameNavigation } from "../hooks/useGameNavigation";
import { useJoinGame } from "../hooks/useJoinGame";
import { applyMove } from "../utils/GameUtils";
import Board from "../components/Board";
import PlayerCard from "../components/PlayerCard";
import GameStatusIndicator from "../components/GameStatusIndicator";
import { WinnerModal } from "../components/modals/WinnerModal";
import { WaitingModal } from "../components/modals/WaitingModal";
import { LeaveConfirmationModal } from "../components/modals/LeaveConfirmationModal";
import { useWebSocket } from "../context/WebSocketContext";

const Game = () => {
  const { username } = useUsername();
  const { auth, isLoading } = useAuth();
  const {
    gameState,
    isConnected,
    isInGame,
    joinGame,
    rejoinGame,
    sendMove,
    exitGame,
    isGameInProgress,
    optimisticState,
    updateOptimisticState,
  } = useGame();

  const { winnerModalOpen, setWinnerModalOpen } = useWebSocket();

  const navigate = useNavigate();
  let { gameId } = useParams();

  const [modalOpen, setModalOpen] = useState(false);
  const [lastMoveKey, setLastMoveKey] = useState(null);

  const { playMove } = useGameSounds();

  const {
    showLeaveConfirmation,
    handleLeaveConfirm,
    handleLeaveCancel,
    handleGameEnd,
  } = useGameNavigation({
    isInGame,
    isConnected,
    isGameInProgress,
    joinGame,
    rejoinGame,
    exitGame,
  });

  useJoinGame({
    gameId,
    isLoading,
    isConnected,
    isInGame,
    joinGame,
    rejoinGame,
  });

  useEffect(() => {
    if (!(auth?.user || auth?.guest)) {
      navigate("/");
    }
  }, [auth, navigate]);

  useEffect(() => {
    if (!gameState) return;

    if (gameState.status === "over") {
      setWinner(gameState.winner);
      setModalOpen(true);
      handleGameEnd();
    }
  }, [gameState, handleGameEnd]);

  useEffect(() => {
    if (!gameState?.newPosition || gameState.newPosition === gameState.previousPosition) return;

    const moveKey = `${gameState.newPosition}-${gameState.previousPosition}-${gameState.currentPlayer}`;
    if (moveKey === lastMoveKey) {
      setLastMoveKey(null);
      return;
    }

    playMove(gameState.isCaptured);
  }, [gameState?.newPosition, gameState?.previousPosition, gameState?.currentPlayer, gameState?.isCaptured]);

  const handleMoveSend = (move) => {
    const newState = applyMove(gameState, move);
    const moveKey = `${newState.newPosition}-${newState.previousPosition}-${newState.currentPlayer}`;
    setLastMoveKey(moveKey);
    playMove(newState.isCaptured);
    updateOptimisticState(newState);
    sendMove(move);
  };

  const handleWinnerModelClick = () => {
    setModalOpen(false);
    setWinnerModalOpen(false);
    exitGame();
    navigate("/");
  };

  const displayState = optimisticState || gameState;

  if (!isConnected || !displayState) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-[var(--color-bg-dark)]">
        <div className="text-center space-y-4">
          <div className="w-12 h-12 border-4 border-[var(--color-border-light)] border-t-[var(--color-primary)] rounded-full animate-spin mx-auto"></div>
          <div className="text-gray-300 font-light text-lg">
            {!isConnected ? "Connecting to game..." : "Loading game state..."}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full w-full flex flex-col lg:flex-row justify-center bg-[var(--color-bg-dark)] overflow-hidden">
      <div className="flex-1 flex flex-col min-h-0 md:pt-0">
        <div className="px-2 py-2">
          <PlayerCard
            username={username}
            goatPlayer={displayState.player["goat"]}
            tigerPlayer={displayState.player["tiger"]}
            currentPlayer={displayState.player[displayState.currentPlayer]}
            gameState={displayState}
          />
        </div>

        <div className="flex-1 flex justify-center items-center min-h-0">
          <Board
            board={displayState.board}
            turn={displayState.currentPlayer}
            phase={displayState.phase}
            onMoveSend={handleMoveSend}
            player={displayState.player}
            gameState={displayState}
            newPosition={displayState.newPosition}
            previousPosition={displayState.previousPosition}
          />
        </div>
      </div>

      <div className="w-full lg:w-60 flex-shrink-0 border-t lg:border-t-0 lg:border-l border-[var(--color-border-light)] bg-[var(--color-bg-surface)] lg:h-full shadow-2xl">
        <GameStatusIndicator
          gameState={displayState}
          moveHistory={displayState.history}
        />
      </div>

      <WinnerModal
        winner={gameState?.winner || ""}
        isOpen={modalOpen}
        onClick={handleWinnerModelClick}
      />
      <WaitingModal isOpen={displayState?.status === "waiting"} />
      <LeaveConfirmationModal
        isOpen={showLeaveConfirmation}
        onConfirm={handleLeaveConfirm}
        onCancel={handleLeaveCancel}
      />
    </div>
  );
};

export default Game;
