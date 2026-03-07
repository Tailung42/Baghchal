import { useState, useEffect, useRef } from "react";
import { useGame } from "../hooks/useGame";
import { useUsername } from "../hooks/useUsername";
import Board from "../components/Board";
import { useParams, useNavigate, useBlocker } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import useSound from "use-sound";
import moveSound from "../assets/sounds/move_sound.mp3";
import captureSound from "../assets/sounds/capture_sound.mp3";
import PlayerCard from "../components/PlayerCard";
import GameStatusIndicator from "../components/GameStatusIndicator";
import BaseModal from "../components/ui/BaseModal";

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
  } = useGame();
  const navigate = useNavigate();
  const [modalOpen, setModalOpen] = useState(false);
  const [winner, setWinner] = useState("");
  const [showLeaveConfirmation, setShowLeaveConfirmation] = useState(false);
  const [pendingNavigation, setPendingNavigation] = useState(null);
  const [playMoveSound] = useSound(moveSound);
  const [playCaptureSound] = useSound(captureSound);

  let { gameId } = useParams();
  gameId = gameId.replace("game_", "");

  // Block in-app navigation
  const blocker = useBlocker(
    ({ currentLocation, nextLocation }) =>
      isGameInProgress() && currentLocation.pathname !== nextLocation.pathname,
  );

  // Block page close, refresh, or external navigation
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (isGameInProgress()) {
        e.preventDefault();
        e.returnValue = "Game is in progress. Are you sure you want to leave?";
        return e.returnValue;
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [isGameInProgress]);

  // Handle in-app navigation blocking
  useEffect(() => {
    if (blocker.state === "blocked") {
      setShowLeaveConfirmation(true);
      setPendingNavigation(() => blocker.proceed);
    }
  }, [blocker]);

  // Handle joining via url or reconnecting after an accidental disconnect.
  // We guard against rejoining when we purposely called `exitGame` (e.g. user
  // clicked "leave" or finished a match).  A ref tracks that intent.
  const intentionalDisconnect = useRef(false);

  useEffect(() => {
    if (isLoading) return;

    if (gameId && !isConnected && !intentionalDisconnect.current) {
      if (isInGame) {
        console.log("Rejoining Game");
        rejoinGame(gameId).then(() => (intentionalDisconnect.current = false));
      } else {
        console.log("Joining game");
        joinGame(gameId).then(() => (intentionalDisconnect.current = false));
      }
    }
  }, [isLoading, isConnected, joinGame, rejoinGame]);

  // Handle game state changes (sounds and winner modal)
  useEffect(() => {
    if (!gameState) return;

    // play move sound if a piece's position has changed
    if (
      gameState.newPosition &&
      gameState.newPosition != gameState.previousPosition
    ) {
      if (gameState.isCaptured === true) {
        playCaptureSound();
      } else {
        playMoveSound();
      }
    }

    if (gameState.status === "over") {
      setWinner(gameState.winner);
      setModalOpen(true);

      // clear any outstanding blocker so users can leave without extra prompts
      if (blocker.state === "blocked") {
        blocker.reset();
      }
    }
  }, [gameState, playMoveSound, playCaptureSound, blocker]);

  // Ensure user is authenticated
  useEffect(() => {
    if (!(auth?.user || auth?.guest)) {
      navigate("/");
    }
  }, [auth, navigate]);

  const handleMoveSend = (move) => {
    sendMove(move);
  };

  const handleLeaveConfirm = () => {
    setShowLeaveConfirmation(false);
    if (pendingNavigation) {
      pendingNavigation();
      // prevent the join effect from firing while we're explicitly leaving
      intentionalDisconnect.current = true;
      exitGame();
      setPendingNavigation(null);
    }
  };

  const handleLeaveCancel = () => {
    setShowLeaveConfirmation(false);
    if (blocker.state === "blocked") {
      blocker.reset();
    }
    setPendingNavigation(null);
  };

  const handleWinnerModelClick = () => {
    // clear any active navigation blocker so we're not prompted when leaving
    if (blocker.state === "blocked") {
      blocker.reset();
    }

    // avoid rejoining after we close the game socket
    intentionalDisconnect.current = true;

    setModalOpen(false);
    exitGame();
    navigate("/");
    console.log("navigating home after game is over");
  };

  if (!isConnected || !gameState) {
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
        {/* Player Cards Row */}
        <div className="px-2 py-2">
          <PlayerCard
            username={username}
            goatPlayer={gameState.player["goat"]}
            tigerPlayer={gameState.player["tiger"]}
            currentPlayer={gameState.player[gameState.currentPlayer]}
            gameState={gameState}
          />
        </div>

        {/* Board */}
        <div className="flex-1 flex justify-center items-center min-h-0">
          <Board
            board={gameState.board}
            currentPlayer={gameState.currentPlayer}
            phase={gameState.phase}
            onMoveSend={handleMoveSend}
            player={gameState.player}
            gameState={gameState}
            newPosition={gameState.newPosition}
            previousPosition={gameState.previousPosition}
          />
        </div>
      </div>

      {/* Game Status Sidebar */}
      <div className="w-full lg:w-60 flex-shrink-0 border-t lg:border-t-0 lg:border-l border-[var(--color-border-light)] bg-[var(--color-bg-surface)] lg:h-full shadow-2xl">
        <GameStatusIndicator
          gameState={gameState}
          moveHistory={gameState.history}
        />
      </div>

      <WinnerModal
        winner={winner}
        isOpen={modalOpen}
        onClick={handleWinnerModelClick}
      />
      <WaitingModal isOpen={gameState?.status === "waiting"} />
      <LeaveConfirmationModal
        isOpen={showLeaveConfirmation}
        onConfirm={handleLeaveConfirm}
        onCancel={handleLeaveCancel}
      />
    </div>
  );
};

export default Game;

function WinnerModal({ winner, isOpen, onClick }) {
  // always register the effect; check isOpen inside it to avoid
  // conditional hook rules
  useEffect(() => {
    if (!isOpen) return;
    const navigate_home_key_handler = (event) => {
      if (event.key == "Enter") {
        onClick();
      }
    };
    addEventListener("keydown", navigate_home_key_handler);

    return () => {
      removeEventListener("keydown", navigate_home_key_handler);
    };
  }, [isOpen, onClick]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 flex items-center justify-center z-50 bg-black/60 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClick();
        }
      }}
    >
      <div className="bg-[var(--color-bg-surface)] rounded-xl shadow-2xl max-w-md w-full mx-4 p-8 text-center border border-[var(--color-border-light)]">
        <div className="text-6xl mb-4">🎉</div>
        <h2 className="text-3xl font-bold mb-3 text-white">Game Over!</h2>
        <p className="mb-8 text-xl text-gray-300">{winner} wins!</p>
        <button
          onClick={onClick}
          className="bg-[var(--color-primary)] hover:bg-[var(--color-primary-dark)] px-8 py-3 rounded-lg text-white font-semibold transition-all transform hover:scale-[1.02] active:scale-[0.98] shadow-lg"
        >
          Return Home
        </button>
      </div>
    </div>
  );
}

const WaitingModal = ({ isOpen }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 flex items-center justify-center z-50 bg-black/60 backdrop-blur-sm">
      <div className="bg-[var(--color-bg-surface)] rounded-xl shadow-2xl max-w-md w-full mx-4 p-8 text-center border border-[var(--color-border-light)]">
        <div className="w-12 h-12 border-4 border-[var(--color-border-light)] border-t-[var(--color-primary)] rounded-full animate-spin mx-auto mb-6"></div>
        <h2 className="text-2xl font-bold mb-3 text-white">
          Waiting for player...
        </h2>
        <p className="text-gray-400">
          Looking for another player to join the game
        </p>
      </div>
    </div>
  );
};

const LeaveConfirmationModal = ({ isOpen, onConfirm, onCancel }) => {
  // handle confirm and cancel with keyboard
  useEffect(() => {
    const confirm_key_handler = (event) => {
      if (event.key == "Enter") {
        event.preventDefault();
        // console.log("confirm exit");
        onConfirm();
      } else if (event.key == "Escape") onCancel();
    };
    if (isOpen) addEventListener("keydown", confirm_key_handler);

    return () => removeEventListener("keydown", confirm_key_handler);
  }, [isOpen, onConfirm, onCancel]);

  return (
    <BaseModal isOpen={isOpen} onClose={onCancel} title="Leave Game?">
      <div className="space-y-6">
        <p className="text-gray-300 text-lg">
          Are you sure you want to leave? The game is still in progress and you
          may lose your current match.
        </p>
        <div className="flex gap-4 justify-end">
          <button
            onClick={onCancel}
            className="px-6 py-2.5 rounded-lg text-white font-semibold bg-[var(--color-border-light)] hover:bg-[var(--color-border-muted)] transition-all"
          >
            Stay in Game
          </button>
          <button
            onClick={onConfirm}
            className="px-6 py-2.5 rounded-lg text-white font-semibold bg-[var(--color-primary)] hover:bg-[var(--color-primary-dark)] transition-all"
          >
            Leave Game
          </button>
        </div>
      </div>
    </BaseModal>
  );
};
