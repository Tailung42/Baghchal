import { createContext, useContext, useRef, useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

const initialGameState = {
  board: {
    "0-0": "tiger",
    "0-4": "tiger",
    "4-0": "tiger",
    "4-4": "tiger",
  },
  currentPlayer: "goat",
  phase: "placement",
  unusedGoat: 20,
  deadGoatCount: 0,
  status: "waiting",
  winner: null,
  newPosition: "",
  previousPosition: "",
  player: {
    goat: "",
    tiger: "",
  },
};

export const WebSocketContext = createContext(null);
export const useWebSocket = () => useContext(WebSocketContext);

const baseSocketUrl = import.meta.env.VITE_BASE_WS_URL;

export const WebSocketProvider = ({ children }) => {
  const { auth } = useAuth();
  const navigate = useNavigate();
  const socketRef = useRef(null);
  const [gameState, setGameState] = useState(initialGameState);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionParams, setConnectionParams] = useState(null);

  const connect = useCallback((gameId = "", mode = "", playAs = "") => {
    setConnectionParams({ gameId: gameId, mode: mode, playAs: playAs });
  }, []);

  const send = useCallback((message) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(message);
    } else {
      console.warn("WebSocket is not connected. Cannot send message:", message);
    }
  }, []);

  const disconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
    setIsConnected(false);
  }, []);

  useEffect(() => {
    if (!connectionParams?.mode) {
      return;
    }
    // close existing websocket
    if (socketRef.current) socketRef.current.close();
    const username = auth.isLoggedIn ? auth.user?.username : auth.guestId;
    const params = new URLSearchParams({
      game_id: connectionParams.gameId,
      mode: connectionParams.mode,
      play_as: connectionParams.playAs,
      username: username,
    });

    // establish a connection to the server (ie. create instance)
    const ws = new WebSocket(`${baseSocketUrl}?${params}`);

    ws.onopen = handleOpen;
    ws.onmessage = handleMessage;
    ws.onclose = handleClose;
    ws.onerror = handleError;

    socketRef.current = ws;
  }, [connectionParams]);

  const handleOpen = () => {
    setIsConnected(true);
    console.log("WebSocket connected");
  };

  const handleMessage = (event) => {
    const data = JSON.parse(event.data);
    const newGameState = data.message?.game_state;

    if (newGameState) {
      setGameState(newGameState);
      if (!window.location.pathname.includes("/game/")) {
        navigate(`/game/${newGameState.game_id}`);
      }
    }
  };

  const handleClose = () => {
    setIsConnected(false);
    console.log("WebSocket closed");
  };

  const handleError = (error) => {
    console.error("WebSocket error:", error);
    setIsConnected(false);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, []);

  return (
    <WebSocketContext.Provider
      value={{
        connect,
        send,
        disconnect,
        gameState,
        isConnected,
      }}
    >
      {children}
    </WebSocketContext.Provider>
  );
};
