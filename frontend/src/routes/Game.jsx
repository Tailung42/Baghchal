import { useState, useEffect, useContext } from "react";
import { useWebSocket } from "../context/WebSocketContext";
import Board from "../components/Board";
import { useParams, useNavigate, useBlocker, replace } from "react-router-dom";
import { AuthContext } from "../context/AuthContext";
import useSound from "use-sound";
import moveSound from "../assets/sounds/move_sound.mp3";
import captureSound from "../assets/sounds/capture_sound.mp3";
import PlayerCard from "../components/PlayerCard";
import GameStatusIndicator from "../components/GameStatusIndicator";
import BaseModal from "../components/ui/BaseModal";

const Game = () => {
  const { auth } = useContext(AuthContext);
  const { send, gameState, isConnected, connect, disconnect } = useWebSocket();
  const navigate = useNavigate();
  const [modalOpen, setModalOpen] = useState(false);
  const [winner, setWinner] = useState("");
  const [showLeaveConfirmation, setShowLeaveConfirmation] = useState(false);
  const [pendingNavigation, setPendingNavigation] = useState(null);
  const [playMoveSound] = useSound(moveSound);
  const [playCaptureSound] = useSound(captureSound);

  let { gameId } = useParams();
  gameId = gameId.replace("game_", "");

  const isGameInProgress = () => {
    return gameState?.status !== "over" && gameState?.status !== "waiting";
  };

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
        e.returnValue = "Game is in i. Are you sure you want to leave?";
        return e.returnValue;
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    // cleanup
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [gameState, isGameInProgress]);

  // Handle in-app navigation blocking
  useEffect(() => {
    if (blocker.state === "blocked") {
      setShowLeaveConfirmation(true);
      setPendingNavigation(() => blocker.proceed);
    }
  }, [blocker]);

  // handle joining via url
  useEffect(() => {
    if (gameId && !isConnected) {
      connect(gameId, "join");
    }
  }, []);

  useEffect(() => {
    if (!gameState) return;

    // play move sound  if a piece's position has changed
    if (
      gameState.newPosition &&
      gameState.newPosition != gameState.previousPosition
    ) {
      if (gameState.isCaptured === true) {
        playCaptureSound();
      } else {
        console.log("moved");
        playMoveSound();
      }
    }
    if (gameState.status === "over") {
      setWinner(gameState.winner);
      setModalOpen(true);
    }
  }, [
    gameState,
    gameId,
    isConnected,
    connect,
    playMoveSound,
    playCaptureSound,
  ]);

  useEffect(() => {
    if (!(auth.user || auth.guestId)) {
      navigate("/", (replace = true));
    }
  }, [auth, navigate]);

  const handleMoveSend = (move) => {
    console.log("sending move ", move);
    send(
      JSON.stringify({
        message: {
          type: "newMove",
          move: move,
        },
      }),
    );
  };

  const handleLeaveConfirm = () => {
    setShowLeaveConfirmation(false);
    if (pendingNavigation) {
      pendingNavigation();
      send(JSON.stringify({ message: { type: "exitGame" } }));
      disconnect();
      setPendingNavigation(null);
    }
  };
  k;
  const handleLeaveCancel = () => {
    setShowLeaveConfirmation(false);
    if (blocker.state === "blocked") {
      blocker.reset();
    }
    setPendingNavigation(null);
  };

  const handleWinnerModelClick = () => {
    setModalOpen(false);
    send(JSON.stringify({ message: { type: "exitGame" } }));
    disconnect();
    navigate("/");
  };

  if (!isConnected || !gameState) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-[#262522]">
        <div className="text-center space-y-4">
          <div className="w-12 h-12 border-4 border-[#3a3835] border-t-[#f95e5e] rounded-full animate-spin mx-auto"></div>
          <div className="text-gray-300 font-light text-lg">
            {!isConnected ? "Connecting to game..." : "Loading game state..."}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full w-full flex flex-col lg:flex-row justify-center bg-[#262522] overflow-hidden">
      <div className="flex-1 flex flex-col min-h-0 md:pt-0">
        {/* Player Cards Row */}
        <div className="px-2 py-2">
          <PlayerCard
            username={auth.user?.username || auth.guestId}
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
      <div className="w-full lg:w-60 flex-shrink-0 border-t lg:border-t-0 lg:border-l border-[#3a3835] bg-[#2f2d2a] lg:h-full shadow-2xl">
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
  if (!isOpen) return null;

  useEffect(() => {
    const navigate_home_key_handler = (event) => {
      if (event.key == "Enter") {
        onClick();
      }
    };
    if (isOpen) addEventListener("keydown", navigate_home_key_handler);

    return () => {
      removeEventListener("keydown", navigate_home_key_handler);
    };
  }, [isOpen]);

  return (
    <div
      className="fixed inset-0 flex items-center justify-center z-50 bg-black/60 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClick();
        }
      }}
    >
      <div className="bg-[#2f2d2a] rounded-xl shadow-2xl max-w-md w-full mx-4 p-8 text-center border border-[#3a3835]">
        <div className="text-6xl mb-4">🎉</div>
        <h2 className="text-3xl font-bold mb-3 text-white">Game Over!</h2>
        <p className="mb-8 text-xl text-gray-300">{winner} wins!</p>
        <button
          onClick={onClick}
          className="bg-[#f95e5e] hover:bg-[#d94545] px-8 py-3 rounded-lg text-white font-semibold transition-all transform hover:scale-[1.02] active:scale-[0.98] shadow-lg"
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
      <div className="bg-[#2f2d2a] rounded-xl shadow-2xl max-w-md w-full mx-4 p-8 text-center border border-[#3a3835]">
        <div className="w-12 h-12 border-4 border-[#3a3835] border-t-[#f95e5e] rounded-full animate-spin mx-auto mb-6"></div>
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
  }, [isOpen]);

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
            className="px-6 py-2.5 rounded-lg text-white font-semibold bg-[#3a3835] hover:bg-[#4a4845] transition-all"
          >
            Stay in Game
          </button>
          <button
            onClick={onConfirm}
            className="px-6 py-2.5 rounded-lg text-white font-semibold bg-[#f95e5e] hover:bg-[#d94545] transition-all"
          >
            Leave Game
          </button>
        </div>
      </div>
    </BaseModal>
  );
};
