import { useState, useEffect, useCallback } from "react";
import { useGame } from "../hooks/useGame";
import PrimaryButton from "../components/ui/PrimaryButton";
import SecondaryButton from "../components/ui/SecondaryButton";
import BaseModal from "../components/ui/BaseModal";
import { LoadingModal } from "../components/modals/LoadingModal";
import board from "../assets/images/board.png";

const QUICK_MATCH_TIMEOUT_MS = 90_000;
const JOIN_GAME_TIMEOUT_MS = 60_000;

export default function Home() {
  const [gameModalOpen, setGameModalOpen] = useState(false);
  const [gameMode, setGameMode] = useState("");
  const [isLoadingGame, setIsLoadingGame] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState(null);
  const [createError, setCreateError] = useState("");
  const [joinError, setJoinError] = useState("");
  const [quickError, setQuickError] = useState("");
  const [botError, setBotError] = useState("");

  const { createGame, joinGame, quickMatch, startBotGame } = useGame();

  const openModal = useCallback(
    (mode) => {
      setGameMode(mode);
      setGameModalOpen(true);
      setJoinError("");
      setCreateError("");
      setQuickError("");
      setBotError("");
      setLoadingMessage(null);
    },
    [],
  );

  const setLoading = useCallback((mode) => {
    setIsLoadingGame(true);
    setGameModalOpen(false);
    if (mode === "create") {
      setLoadingMessage({ title: "Creating game...", subtext: "Setting up your game room." });
    } else if (mode === "join") {
      setLoadingMessage({ title: "Joining game...", subtext: "Connecting you to the game room." });
    } else if (mode === "quick") {
      setLoadingMessage({ title: "Finding a match...", subtext: "Looking for another player to join the game." });
    } else if (mode === "bot") {
      setLoadingMessage({ title: "Starting bot game...", subtext: "Waking up the bot and setting up the board." });
    }
  }, []);

  const handleCreate = useCallback(
    async (gameId, playerRole) => {
      setLoading("create");
      setCreateError("");
      try {
        await createGame(gameId, playerRole);
        // The WebSocket `gameState` event navigates to /game/:id once the
        // server responds, so the loading overlay stays up until then.
      } catch (error) {
        setCreateError(error.response?.data?.error || "Failed to create game");
        setIsLoadingGame(false);
        setLoadingMessage(null);
      }
    },
    [createGame, setLoading],
  );

  const handleJoin = useCallback(
    async (joinId) => {
      setLoading("join");
      setJoinError("");
      try {
        await Promise.race([
          joinGame(joinId),
          new Promise((_, reject) =>
            setTimeout(
              () => reject(new Error("JOIN_GAME_TIMEOUT")),
              JOIN_GAME_TIMEOUT_MS,
            ),
          ),
        ]);
        // The WebSocket `gameState` event navigates to /game/:id once the
        // server responds, so the loading overlay stays up until then.
      } catch (error) {
        if (error.message === "JOIN_GAME_TIMEOUT") {
          setJoinError("Took too long to join. Please try again.");
        } else {
          setJoinError(error.response?.data?.error || "Failed to join game");
        }
        setIsLoadingGame(false);
        setLoadingMessage(null);
      }
    },
    [joinGame, setLoading],
  );

  const handleQuick = useCallback(
    async () => {
      setLoading("quick");
      setQuickError("");
      try {
        await Promise.race([
          quickMatch(),
          new Promise((_, reject) =>
            setTimeout(
              () => reject(new Error("QUICK_MATCH_TIMEOUT")),
              QUICK_MATCH_TIMEOUT_MS,
            ),
          ),
        ]);
        // The WebSocket `gameState` event navigates to /game/:id once the
        // server responds, so the loading overlay stays up until then.
      } catch (error) {
        if (error.message === "QUICK_MATCH_TIMEOUT") {
          setQuickError("Took too long to find a match. Please try again.");
        } else {
          setQuickError(error.response?.data?.error || "Failed to find a match");
        }
        setIsLoadingGame(false);
        setLoadingMessage(null);
      }
    },
    [quickMatch, setLoading],
  );

  const handleBot = useCallback(
    async (playerRole, difficulty) => {
      setLoading("bot");
      setBotError("");
      try {
        await startBotGame(playerRole, difficulty);
        // The WebSocket `gameState` event navigates to /game/:id once the
        // server responds, so the loading overlay stays up until then.
      } catch (error) {
        setBotError(error.response?.data?.error || "Failed to start bot game");
        setIsLoadingGame(false);
        setLoadingMessage(null);
      }
    },
    [startBotGame, setLoading],
  );

  // When a create/join fails, re-open the modal so the user can see the
  // error and retry. Quick-match and bot errors show inline on the page.
  useEffect(() => {
    if (
      (createError && gameMode === "create") ||
      (joinError && gameMode === "join")
    ) {
      setGameModalOpen(true);
    }
  }, [createError, joinError, gameMode]);

  return (
    <div className=" md:pl-10 font-sans bg-bg-dark text-text-light min-h-screen overflow-x-hidden">
      <div className="max-w-7xl mx-auto px-5 py-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center min-h-[90vh]">
          {/* Content Side */}
          <div className="space-y-8 text-center lg:text-left">
            <div>
              <h1 className="text-6xl md:text-7xl font-bold text-white mb-4 tracking-tight leading-none">
                Bagh Chal
              </h1>
              <p className="text-2xl text-text-muted font-light">
                The Ancient Game of Strategy
              </p>
            </div>

            <p className="text-lg text-text-muted leading-relaxed max-w-lg mx-auto lg:mx-0">
              Experience the legendary Nepali board game where cunning tigers
              hunt and strategic goats defend. A timeless battle of wits that
              has captivated minds across the Himalayas for centuries.
            </p>

            <div className="space-y-3 max-w-sm mx-auto lg:mx-0">
              <PrimaryButton onClick={() => openModal("create")}>
                <span>🎯</span>
                <span className="text-xl">Create Game</span>
              </PrimaryButton>

              <SecondaryButton onClick={() => openModal("join")}>
                <span>🤝</span>
                <span className="text-xl">Join Game</span>
              </SecondaryButton>

              <PrimaryButton onClick={handleQuick}>
                <span>⚡</span>
                <span className="text-xl">Quick Match</span>
              </PrimaryButton>

              <SecondaryButton onClick={() => openModal("bot")}>
                <span>🤖</span>
                <span className="text-xl">Play vs Bot</span>
              </SecondaryButton>
            </div>

            {(quickError || botError) && (
              <p className="text-red-400 text-sm text-center max-w-sm mx-auto">
                {quickError || botError}
              </p>
            )}

            <div className="flex gap-10 pt-5 justify-center lg:justify-start">
              <div>
                <div className="text-3xl font-bold text-text-white">4</div>
                <div className="text-sm text-text-muted uppercase tracking-wide">
                  Tigers
                </div>
              </div>
              <div>
                <div className="text-3xl font-bold text-text-white">20</div>
                <div className="text-sm text-text-muted uppercase tracking-wide">
                  Goats
                </div>
              </div>
              <div>
                <div className="text-3xl font-bold text-text-white">∞</div>
                <div className="text-sm text-text-muted uppercase tracking-wide">
                  Strategy
                </div>
              </div>
            </div>
          </div>

          {/* Board Side */}
          <div className="flex justify-center lg:justify-end">
            <div className="relative bg-bg-surface p-10 rounded-xl border border-border-muted shadow-2xl">
              <img
                src={board}
                alt="Bagh Chal Board"
                className="w-full max-w-md rounded"
              />
              <div className="absolute -top-3 -right-3 bg-primary text-text-white text-xs px-4 py-1 rounded-full font-semibold uppercase tracking-wide">
                Traditional
              </div>
              <div className="absolute -bottom-3 -left-3 bg-bg-surface border-2 border-primary text-text-light text-xs px-4 py-1 rounded-full font-semibold uppercase tracking-wide">
                Strategic
              </div>
            </div>
          </div>
        </div>
      </div>

      <LoadingModal
        isOpen={isLoadingGame}
        title={loadingMessage?.title}
        subtext={loadingMessage?.subtext}
      />

      <GameModal
        isOpen={gameModalOpen}
        onClose={() => {
          setGameModalOpen(false);
          setJoinError("");
          setCreateError("");
          setQuickError("");
          setBotError("");
          setLoadingMessage(null);
        }}
        mode={gameMode}
        isLoading={isLoadingGame}
        onCreate={handleCreate}
        onJoin={handleJoin}
        onBot={handleBot}
        joinError={joinError}
        createError={createError}
      />
    </div>
  );
}

const GameModal = ({
  isOpen,
  onClose,
  mode,
  isLoading,
  onCreate,
  onJoin,
  onBot,
  joinError,
  createError,
}) => {
  const GameIdLength = 8;
  const [gameId, setGameId] = useState(null);
  const [joinId, setJoinId] = useState("");
  const [playerRole, setPlayerRole] = useState("tiger");
  const [botDifficulty, setBotDifficulty] = useState("medium");
  const [copied, setCopied] = useState(false);

  const generateGameId = () => {
    let gameid = crypto.randomUUID().substring(0, GameIdLength);
    console.log("Generating Game: ", gameid);
    return gameid;
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(gameId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  useEffect(() => {
    if (mode === "create") {
      setGameId(generateGameId());
      setPlayerRole("tiger");
    }
  }, [mode]);

  const titleConfig = {
    create: "🎯Create Game",
    join: "🤝Join Game",
    bot: "🤖 Play vs Bot",
  };

  if (!isOpen) return null;

  return (
    <BaseModal isOpen={isOpen} onClose={onClose} title={titleConfig[mode]}>
      {/* Create Mode */}
      {mode === "create" && (
        <div className="space-y-6">
          <p className="text-gray-400 mb-5">
            Share this Game ID with a friend:
          </p>

          <div className="bg-[var(--color-bg-surface-dark)] p-4 rounded-lg border border-[var(--color-border-light)] flex justify-between items-center gap-3">
            <span className="font-mono text-gray-200 break-all text-sm">
              {gameId}
            </span>
            <button
              onClick={handleCopy}
              className="text-gray-200 border border-gray-600 hover:bg-gray-800 px-4 py-2 rounded-md transition-all text-sm font-semibold whitespace-nowrap"
            >
              {copied ? "Copied!" : "Copy"}
            </button>
          </div>

          <div>
            <label className="block text-gray-300 mb-2 text-sm font-semibold">
              Choose your role:
            </label>
            <select
              value={playerRole}
              onChange={(e) => setPlayerRole(e.target.value)}
              className="w-full p-3 bg-[var(--color-bg-surface-dark)] border border-[var(--color-border-light)] text-gray-200 rounded-lg focus:outline-none focus:border-[var(--color-primary)] transition-all"
            >
              <option value="tiger">🐅 Tiger (Hunter)</option>
              <option value="goat">🐐 Goat (Defender)</option>
            </select>
          </div>

          {createError && <p className="text-red-400 text-sm">{createError}</p>}

          <PrimaryButton
            onClick={() => onCreate(gameId, playerRole)}
            loading={isLoading}
            disabled={isLoading}
          >
            {isLoading ? "Creating..." : "Create Game Room"}
          </PrimaryButton>
        </div>
      )}

      {/* Join mode */}
      {mode === "join" && (
        <div className="space-y-6">
          <p className="text-gray-400 mb-5">Enter the Game ID to join:</p>

          <input
            type="text"
            value={joinId}
            onChange={(e) => setJoinId(e.target.value)}
            className="w-full p-4 rounded-lg bg-[var(--color-bg-surface-dark)] border border-[var(--color-border-light)] text-gray-200 placeholder-gray-600 focus:outline-none focus:border-[var(--color-primary)] transition-all"
            placeholder="Paste Game ID here..."
          />

          {joinError && <p className="text-red-400 text-sm">{joinError}</p>}

          <PrimaryButton
            onClick={() => onJoin(joinId.trim())}
            loading={isLoading}
            disabled={isLoading || !joinId.trim()}
            className={!joinId.trim() && !isLoading ? "opacity-50 cursor-not-allowed" : ""}
          >
            Join Game
          </PrimaryButton>
        </div>
      )}

      {/* Bot mode */}
      {mode === "bot" && (
        <div className="space-y-6">
          <p className="text-gray-400 mb-5">
            Play against the server bot. Pick your side and how hard it
            should fight:
          </p>

          <div>
            <label className="block text-gray-300 mb-2 text-sm font-semibold">
              Choose your role:
            </label>
            <select
              value={playerRole}
              onChange={(e) => setPlayerRole(e.target.value)}
              className="w-full p-3 bg-[var(--color-bg-surface-dark)] border border-[var(--color-border-light)] text-gray-200 rounded-lg focus:outline-none focus:border-[var(--color-primary)] transition-all"
            >
              <option value="tiger">🐅 Tiger (Hunter)</option>
              <option value="goat">🐐 Goat (Defender)</option>
            </select>
          </div>

          <div>
            <label className="block text-gray-300 mb-2 text-sm font-semibold">
              Bot difficulty:
            </label>
            <select
              value={botDifficulty}
              onChange={(e) => setBotDifficulty(e.target.value)}
              className="w-full p-3 bg-[var(--color-bg-surface-dark)] border border-[var(--color-border-light)] text-gray-200 rounded-lg focus:outline-none focus:border-[var(--color-primary)] transition-all"
            >
              <option value="easy">Easy — makes quick decisions</option>
              <option value="medium">Medium — balanced play</option>
              <option value="hard">Hard — sees moves ahead</option>
            </select>
          </div>

          <PrimaryButton
            onClick={() => onBot(playerRole, botDifficulty)}
            loading={isLoading}
            disabled={isLoading}
          >
            {isLoading ? "Starting..." : "Start Bot Game"}
          </PrimaryButton>
        </div>
      )}

    </BaseModal>
  );
};
