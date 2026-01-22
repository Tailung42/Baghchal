import { useState, useEffect } from "react";
import { useWebSocket } from "../context/WebSocketContext";
import PrimaryButton from "../components/ui/PrimaryButton";
import SecondaryButton from "../components/ui/SecondaryButton";
import BaseModal from "../components/ui/BaseModal";
import board from "../assets/images/board.png";

export default function Home() {
  const [gameModalOpen, setGameModalOpen] = useState(false);
  const [gameMode, setGameMode] = useState("");

  const handleClick = (mode) => {
    setGameMode(mode);
    setGameModalOpen(true);
  };

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
              <PrimaryButton onClick={() => handleClick("create")}>
                <span>🎯</span>
                <span className="text-xl">Create Game</span>
              </PrimaryButton>

              <SecondaryButton onClick={() => handleClick("join")}>
                <span>🤝</span>
                <span className="text-xl">Join Game</span>
              </SecondaryButton>

              <PrimaryButton onClick={() => handleClick("quick")}>
                <span>⚡</span>
                <span className="text-xl">Quick Match</span>
              </PrimaryButton>
            </div>

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

      <Modal
        isOpen={gameModalOpen}
        onClose={() => setGameModalOpen(false)}
        mode={gameMode}
      />
    </div>
  );
}

const Modal = ({ isOpen, onClose, mode }) => {
  // ? is this the correct place to write constant?
  const GameIdLength = 8;
  const { connect } = useWebSocket();
  const [gameId, setGameId] = useState(() => crypto.randomUUID());
  const [joinId, setJoinId] = useState("");
  const [playerRole, setPlayerRole] = useState("tiger");

  const generateGameId = () => {
    return crypto.randomUUID().substring(0, GameIdLength);
  };

  useEffect(() => {
    if (mode === "create") {
      setGameId(generateGameId());
      setPlayerRole("tiger"); // default value for create mode
    } else if (mode === "quick") {
      handleQuick();
    }
  }, [mode]);

  const handleCreate = () => {
    connect(gameId, "create", playerRole);
  };

  const handleJoin = () => {
    console.log("Joining game:", joinId);
    connect(joinId.trim(), "join");
  };

  const handleQuick = () => {
    console.log("Searching for quick game");
    connect("", "quick");
  };

  const handleCopy = async (e) => {
    try {
      await navigator.clipboard.writeText(gameId);
      const button = e.target;
      const originalText = button.textContent;
      button.textContent = "Copied!";
      setTimeout(() => {
        button.textContent = originalText;
      }, 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  const titleConfig = {
    create: "🎯Create Game",
    join: "🤝Join Game",
    quick: "⚡ Quick Match",
  };

  const title = titleConfig[mode];

  return (
    <BaseModal isOpen={isOpen} onClose={onClose} title={title}>
      {/* Create Mode  */}
      {mode === "create" && (
        <div className="space-y-6">
          <p className="text-gray-400 mb-5">
            Share this Game ID with a friend:
          </p>

          <div className="bg-[#1a1a1a] p-4 rounded-lg border border-[#3a3835] flex justify-between items-center gap-3">
            <span className="font-mono text-gray-200 break-all text-sm">
              {gameId}
            </span>
            <button
              onClick={handleCopy}
              className="text-gray-200 border border-gray-600 hover:bg-gray-800 px-4 py-2 rounded-md transition-all text-sm font-semibold whitespace-nowrap"
            >
              Copy
            </button>
          </div>

          <div>
            <label className="block text-gray-300 mb-2 text-sm font-semibold">
              Choose your role:
            </label>
            <select
              value={playerRole}
              onChange={(e) => setPlayerRole(e.target.value)}
              className="w-full p-3 bg-[#1a1a1a] border border-[#3a3835] text-gray-200 rounded-lg focus:outline-none focus:border-[#f95e5e] transition-all"
            >
              <option value="tiger">🐅 Tiger (Hunter)</option>
              <option value="goat">🐐 Goat (Defender)</option>
            </select>
          </div>

          <PrimaryButton onClick={handleCreate}>Create Game Room</PrimaryButton>
        </div>
      )}

      {/* Join mode  */}
      {mode === "join" && (
        <div className="space-y-6">
          <p className="text-gray-400 mb-5">Enter the Game ID to join:</p>

          <input
            type="text"
            value={joinId}
            onChange={(e) => setJoinId(e.target.value)}
            className="w-full p-4 rounded-lg bg-[#1a1a1a] border border-[#3a3835] text-gray-200 placeholder-gray-600 focus:outline-none focus:border-[#f95e5e] transition-all"
            placeholder="Paste Game ID here..."
          />

          <PrimaryButton
            onClick={handleJoin}
            className={!joinId.trim() ? "opacity-50 cursor-not-allowed" : ""}
          >
            Join Game
          </PrimaryButton>
        </div>
      )}

      {/* Quick mode  */}
      {mode === "quick" && (
        <div className="text-center py-10">
          <div className="w-12 h-12 border-4 border-[#3a3835] border-t-[#f95e5e] rounded-full animate-spin mx-auto mb-5"></div>
          <p className="text-gray-400 mb-2">Looking for a quick match...</p>
          <p className="text-gray-500 text-sm">
            We'll match you with another player shortly
          </p>
        </div>
      )}
    </BaseModal>
  );
};
