const DIFFICULTY_BADGE_STYLES = {
  easy: "border-success/60 text-success",
  medium: "border-primary/60 text-primary",
  hard: "border-error/60 text-error",
};

const PlayerCard = ({
  username,
  goatPlayer,
  tigerPlayer,
  currentPlayer,
  isBotGame = false,
  botDifficulty = null,
  botThinking = false,
}) => {
  const isPlayerTurn = currentPlayer === username;

  const isPlayerGoat = goatPlayer === username;

  const playerLabel = `You ${isPlayerGoat ? "(🐐)" : "(🐅)"}`;
  const opponentLabel = `${
    isPlayerGoat ? tigerPlayer + "(🐅)" : goatPlayer + "(🐐)"
  }`;
  const turnLabel = isPlayerTurn
    ? "Your turn!"
    : botThinking
      ? "🤖 Bot is thinking..."
      : "Opponent’s turn";
  return (
    <div
      className={`
        px-4 py-2 rounded-lg border-2 transition-all
        max-w-md mx-auto w-full text-center
        ${
          isPlayerTurn
            ? isPlayerGoat
              ? "border-secondary bg-secondary-dark text-text-white -lg "
              : "border-primary bg-primary text-text-white -lg "
            : "border-border-muted bg-bg-dark text-text-light"
        }
      `}
    >
      {/* Matchup */}
      <div className="text-sm font-extrabold truncate text-text-white">
        {playerLabel} <span className="opacity-70">VS</span> {opponentLabel}
        {isBotGame && botDifficulty && (
          <span
            className={`ml-2 inline-block align-middle px-2 py-0.5 rounded-full border text-[10px] font-bold uppercase tracking-wide ${
              DIFFICULTY_BADGE_STYLES[botDifficulty] ||
              "border-border-muted text-text-muted"
            }`}
          >
            {botDifficulty}
          </span>
        )}
      </div>

      {/* Turn status */}
      <div
        className={`
          text-xs font-bold uppercase tracking-wide mt-1
          ${isPlayerTurn ? "text-text-white" : "text-text-muted"}
        `}
      >
        {turnLabel}
      </div>
    </div>
  );
};

export default PlayerCard;
