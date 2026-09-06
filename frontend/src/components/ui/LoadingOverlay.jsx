import { useEffect, useRef } from "react";

function LoadingOverlay({ isOpen }) {
  const layerRef = useRef(null);

  useEffect(() => {
    if (!isOpen) return;

    const overlay = layerRef.current;
    if (!overlay) return;

    const preventDefault = (event) => {
      if (overlay && overlay.contains(event.target)) {
        return;
      }
      event.preventDefault();
      event.stopPropagation();
    };

    document.addEventListener("mousedown", preventDefault, true);
    document.addEventListener("keydown", preventDefault, true);
    document.body.style.overflow = "hidden";
    overlay?.focus();

    return () => {
      document.removeEventListener("mousedown", preventDefault, true);
      document.removeEventListener("keydown", preventDefault, true);
      document.body.style.overflow = "";
      overlay?.blur();
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      ref={layerRef}
      className="fixed inset-0 flex items-center justify-center z-[70] bg-black/85 backdrop-blur-sm focus:outline-none"
      tabIndex={-1}
      role="dialog"
      aria-modal="true"
      aria-busy="true"
    >
      <div className="flex flex-col items-center gap-4 text-center">
        <div className="w-12 h-12 border-4 border-[var(--color-border-light)] border-t-[var(--color-primary)] rounded-full animate-spin"></div>
        <p className="text-lg font-semibold text-white">Please wait...</p>
      </div>
    </div>
  );
}

export default LoadingOverlay;
