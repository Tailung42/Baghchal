import { useState, useRef, useEffect } from "react";

export function LoadingModal({ isOpen, title, subtext, minDurationMs = 400 }) {
  const [visible, setVisible] = useState(false);
  const shownAtRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      shownAtRef.current = Date.now();
      setVisible(true);
    } else if (shownAtRef.current != null) {
      const elapsed = Date.now() - shownAtRef.current;
      if (elapsed >= minDurationMs) {
        setVisible(false);
        shownAtRef.current = null;
      }
    }
    return () => {
      shownAtRef.current = null;
      setVisible(false);
    };
  }, [isOpen, minDurationMs]);

  if (!visible) return null;

  return (
    <div className="fixed inset-0 flex items-center justify-center z-50 bg-black/60 backdrop-blur-sm">
      <div className="bg-[var(--color-bg-surface)] rounded-xl shadow-2xl max-w-md w-full mx-4 p-8 text-center border border-[var(--color-border-light)]">
        <div className="w-12 h-12 border-4 border-[var(--color-border-light)] border-t-[var(--color-primary)] rounded-full animate-spin mx-auto mb-6" />
        <h2 className="text-2xl font-bold mb-3 text-white">{title}</h2>
        {subtext && <p className="text-gray-400">{subtext}</p>}
      </div>
    </div>
  );
}

export function WaitingModal({ isOpen }) {
  return (
    <LoadingModal
      isOpen={isOpen}
      title="Waiting for player..."
      subtext="Looking for another player to join the game"
    />
  );
}