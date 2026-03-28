import { useEffect } from "react";
import BaseModal from "../ui/BaseModal";

export function LeaveConfirmationModal({ isOpen, onConfirm, onCancel }) {
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        onConfirm();
      } else if (event.key === "Escape") {
        onCancel();
      }
    };
    if (isOpen) {
      addEventListener("keydown", handleKeyDown);
    }

    return () => removeEventListener("keydown", handleKeyDown);
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
}
