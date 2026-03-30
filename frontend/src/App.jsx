import { useState } from "react";
import "./App.css";
import Game from "./routes/Game";
import Layout from "./routes/Layout";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import UserProfile from "./routes/UserProfile";
import Home from "./routes/Home";
import { AuthProvider } from "./context/AuthContext";
import { WebSocketProvider } from "./context/WebSocketContext";
import Rules from "./routes/Rules";
import AuthModal from "./components/AuthModal";
import { GoogleOAuthProvider } from "@react-oauth/google";

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;
function AppContent({ authModalOpen, setAuthModalOpen }) {
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
        {
          path: ":username",
          element: <UserProfile />,
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
        <AppContent
          authModalOpen={authModalOpen}
          setAuthModalOpen={setAuthModalOpen}
        />
      </AuthProvider>
    </GoogleOAuthProvider>
  );
}

export default App;
