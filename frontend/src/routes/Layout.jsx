import { useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { useNavigate } from "react-router-dom";
import { Outlet } from "react-router-dom";
import { useUsername } from "../hooks/useUsername";
function Layout({ setAuthModalOpen }) {
  return (
    <div className="flex h-screen w-screen bg-bg-dark overflow-hidden">
      <SideBar setAuthModalOpen={setAuthModalOpen} />
      <main className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Mobile top padding to account for fixed navbar */}
        <div className="md:hidden h-12 shrink-0"></div>
        {/* Scrollable content area */}
        <div className="flex-1 overflow-y-auto md:pt-5">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

export default Layout;

function SideBar({ setAuthModalOpen }) {
  const { username } = useUsername();
  const { auth, logout } = useAuth();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const navigate = useNavigate();

  const handleLoginToggle = () => {
    if (!auth?.user) {
      setAuthModalOpen(true);
    } else {
      logout();
    }
    setIsMobileMenuOpen(false);
  };

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  return (
    <>
      {/* Mobile Navigation Bar */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-50 bg-bg-surface border-b border-border-muted px-2 flex items-center justify-between shadow-lg">
        <button
          onClick={toggleMobileMenu}
          className="p-2 text-text-muted hover:text-text-white focus:outline-none transition-colors"
        >
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            {isMobileMenuOpen ? (
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            ) : (
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            )}
          </svg>
        </button>

        <div
          onClick={() => {
            navigate("/");
            setIsMobileMenuOpen(false);
          }}
          className="text-xl font-bold text-text-white cursor-pointer hover:text-primary transition-colors"
        >
          Bagh Chal
        </div>

        <div className="w-10"></div>
      </div>

      {/* Mobile Sidebar Overlay */}
      {isMobileMenuOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={`
          h-screen bg-bg-surface border-r border-border-muted z-50 flex flex-col shadow-2xl
          md:relative md:translate-x-0 md:h-full
          fixed w-50 top-0 left-0 bottom-0 transform transition-transform duration-300 ease-in-out
          ${isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"}
          md:block
        `}
      >
        {/* Mobile Close Button */}
        <button
          onClick={() => setIsMobileMenuOpen(false)}
          className="md:hidden absolute top-4 left-4 p-2 text-text-muted hover:text-text-white transition-colors z-10"
        >
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>

        {/* Top Section */}
        <div className="flex-1 p-4 overflow-y-auto min-h-0">
          {/* Logo/Home Button */}
          <div className="text-center mb-10 mt-8 md:mt-0">
            <button
              onClick={() => {
                navigate("/");
                setIsMobileMenuOpen(false);
              }}
              className="text-3xl font-bold text-text-white mb-2 hover:text-primary transition-colors tracking-tight"
            >
              Bagh Chal
            </button>
            <div className="w-33 h-1 bg-primary mx-auto rounded"></div>
          </div>

          {/* User Profile Section */}
          <div className="bg-bg-dark rounded-xl px-1 py-3 mb-8 border border-border-muted shadow-lg">
            <div className="text-center">
              <div className="w-15 h-15 bg-primary rounded-full mx-auto mb-4 flex items-center justify-center text-text-white text-2xl font-bold shadow-lg">
                {username?.[0]?.toUpperCase() || "G"}
              </div>

              <div className=" text-text-white font-bold text-l mb-1">
                {username}
              </div>

              <div className="text-text-muted text-sm">
                {auth.user ? "" : "Guest"}
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="space-y-2">
            <button
              onClick={() => {
                navigate("/");
                setIsMobileMenuOpen(false);
              }}
              className="w-full flex items-center gap-3 text-text-light text-base font-semibold hover:text-text-white hover:bg-bg-dark px-4 py-3 rounded-lg transition-all group"
            >
              <span className="text-xl">🏠</span>
              <span>Home</span>
            </button>

            <button
              onClick={() => {
                navigate("/rules");
                setIsMobileMenuOpen(false);
              }}
              className="w-full flex items-center gap-3 text-text-light text-base font-semibold hover:text-text-white hover:bg-bg-dark px-4 py-3 rounded-lg transition-all group"
            >
              <span className="text-xl">📖</span>
              <span>Rules</span>
            </button>
          </nav>

          {/* Game Stats */}
          {/* <div className="mt-5 pt-5 border-t border-[#3a3835]">
            <div className="text-gray-500 text-xs uppercase tracking-wide mb-4 font-semibold">
              Quick Stats
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-[#262522] rounded-lg p-3 border border-[#3a3835]">
                <div className="text-2xl font-bold text-white">-</div>
                <div className="text-xs text-gray-500 uppercase tracking-wide">
                  Wins
                </div>
              </div>
              <div className="bg-[#262522] rounded-lg p-3 border border-[#3a3835]">
                <div className="text-2xl font-bold text-white">-</div>
                <div className="text-xs text-gray-500 uppercase tracking-wide">
                  Games
                </div>
              </div>
            </div>
          </div> */}
        </div>

        {/* Bottom Section - Login/Logout Button */}
        <div className=" absolute bottom-2 px-4 py-2 w-full border-t-2 border-border-muted shrink-0">
          <button
            onClick={handleLoginToggle}
            className="w-full bg-primary text-text-white px-6 py-3 rounded-lg hover:bg-primary-dark transition-all font-semibold shadow-lg hover:shadow-xl transform hover:scale-[1.02] active:scale-[0.98]"
          >
            {auth.user ? "Logout" : "Login"}
          </button>
        </div>
      </div>
    </>
  );
}
