const BaseModal = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/85 flex items-center justify-center z-50 p-5"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div
        className="bg-bg-surface p-10 rounded-xl max-w-lg w-full border border-border-muted max-h-[90vh] overflow-y-auto"
      >
        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center gap-3">
            <h2 className="text-3xl font-bold text-text-white capitalize">
              {title}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-text-muted hover:text-text-light hover:bg-border-muted w-8 h-8 rounded flex items-center justify-center text-2xl transition-all"
          >
            ×
          </button>
        </div>
        {children}
      </div>
    </div>
  );
};

export default BaseModal;
