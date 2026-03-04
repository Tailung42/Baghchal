import { useState, useEffect } from "react";
import "./App.css";
import Game from "./routes/Game";
import Layout from "./routes/Layout";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import UserProfile from "./routes/UserProfile";
import Home from "./routes/Home";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { WebSocketProvider } from "./context/WebSocketContext";
import Rules from "./routes/Rules";
import AuthModal from "./components/AuthModal";
import { generateUsername } from "unique-username-generator";
import { GoogleOAuthProvider } from '@react-oauth/google';

const GOOGLE_CLIENT_ID = "611135257481-5tv07uu56cf811lle2cdduubh43gu018.apps.googleusercontent.com";

function AppContent({ authModalOpen, setAuthModalOpen }) {
  const { auth, setGuestId } = useAuth();

  useEffect(() => {
    if (!auth?.isLoggedIn && !auth?.guestId) {
      const guestId = generateUsername("", "", 12);
      setGuestId(guestId);
      console.log("Guest ID:", guestId);
    }
  }, [auth?.isLoggedIn, auth?.guestId, setGuestId]);

  const router = createBrowserRouter([
    {
      path: "/",
      element: (
        <WebSocketProvider>
          <Layout setAuthModalOpen={setAuthModalOpen} />
        </WebSocketProvider>
      ),
      children: [
        {
          index: true,
          element: <Home />,
        },
        {
          path: "user",
          element: <UserProfile />,
        },
        {
          path: "game/:gameId",
          element: <Game />,
        },
        {
          path: "rules",
          element: <Rules />,
        },
      ],
    },
  ]);

  return (
    <>
      <RouterProvider router={router} />
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
      />
    </>
  );
}

function App() {
  const [authModalOpen, setAuthModalOpen] = useState(false);

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <AuthProvider>
        <AppContent authModalOpen={authModalOpen} setAuthModalOpen={setAuthModalOpen} />
      </AuthProvider>
    </GoogleOAuthProvider>
  );
}

export default App;