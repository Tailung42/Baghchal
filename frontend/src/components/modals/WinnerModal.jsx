import { useEffect } from "react";

export function WinnerModal({ winner, isOpen, onClick }) {
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (event) => {
      if (event.key === "Enter") {
        onClick();
      }
    };
    addEventListener("keydown", handleKeyDown);

    return () => {
      removeEventListener("keydown", handleKeyDown);
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
