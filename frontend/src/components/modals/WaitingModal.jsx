export function WaitingModal({ isOpen }) {
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
}
