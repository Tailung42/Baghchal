import { createContext, useContext, useRef, useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { gameApi } from "../api/client";

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
  // store the current game id in a ref so that callbacks can access it even
  // if state hasn't updated yet
  const gameIdRef = useRef(null);
  const [gameState, setGameState] = useState(initialGameState);
  const [isConnected, setIsConnected] = useState(false);
  const [gameId, setGameId] = useState(null);

  const getUsername = useCallback(() => {
    return auth.isLoggedIn ? auth.user?.username : auth.guestId;
  }, [auth]);

  const connectWebSocket = useCallback((gid) => {
    if (!gid) {
      console.error("Cannot connect WebSocket without game ID");
      return;
    }

    // make sure our internal ref/state knows the current id immediately
    gameIdRef.current = gid;
    setGameId(gid);

    // Close existing connection
    if (socketRef.current) socketRef.current.close();

    const username = getUsername();
    const params = new URLSearchParams({
      game_id: gid,
      username: username,
    });

    const ws = new WebSocket(`${baseSocketUrl}?${params}`);
    ws.onopen = handleOpen;
    ws.onmessage = handleMessage;
    ws.onclose = handleClose;
    ws.onerror = handleError;
    socketRef.current = ws;
  }, [getUsername]);

  const createGameHTTP = useCallback(async (gameId, playerRole) => {
    try {
      const username = getUsername();
      const response = await gameApi.create(gameId, username, playerRole);
      const data = response.data;
      setGameId(data.game_id);
      setGameState(data.game_state);
      connectWebSocket(data.game_id);
      return data.game_id;
    } catch (error) {
      console.error("Error creating game:", error);
      throw error;
    }
  }, [getUsername, connectWebSocket]);

  const joinGameHTTP = useCallback(async (gameId, playerRole) => {
    try {
      const username = getUsername();
      const response = await gameApi.join(gameId, username, playerRole);
      const data = response.data;
      setGameId(data.game_id);
      setGameState(data.game_state);
      connectWebSocket(data.game_id);
      return data.game_id;
    } catch (error) {
      console.error("Error joining game:", error);
      throw error;
    }
  }, [getUsername, connectWebSocket]);

  const rejoinGameHTTP = useCallback(async (gid) => {
    try {
      const username = getUsername();
      const response = await gameApi.rejoin(gid, username);
      const data = response.data;
      setGameId(data.game_id);
      setGameState(data.game_state);
      connectWebSocket(data.game_id);
      return data.game_id;
    } catch (error) {
      console.error("Error rejoining game:", error);
      throw error;
    }
  }, [getUsername, connectWebSocket]);

  const quickMatchHTTP = useCallback(async () => {
    try {
      const username = getUsername();
      const response = await gameApi.quickMatch(username);
      const data = response.data;
      setGameId(data.game_id);
      setGameState(data.game_state);
      connectWebSocket(data.game_id);
      return data.game_id;
    } catch (error) {
      console.error("Error finding quick match:", error);
      throw error;
    }
  }, [getUsername, connectWebSocket]);

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

  const handleOpen = () => {
    setIsConnected(true);
    console.log("WebSocket connected");
  };

  const handleMessage = (event) => {
    const data = JSON.parse(event.data);
    const newGameState = data.message?.game_state;

    if (newGameState) {
      setGameState(newGameState);

      // determine which id to navigate with (use the value from the
      // payload first since the local state may not yet have updated)
      const idToUse =
        (newGameState.game_id || gameIdRef.current || gameId || "").replace(
          "game_",
          ""
        );

      if (idToUse && !window.location.pathname.includes("/game/")) {
        navigate(`/game/${idToUse}`);
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
        createGame: createGameHTTP,
        joinGame: joinGameHTTP,
        rejoinGame: rejoinGameHTTP,
        quickMatch: quickMatchHTTP,
        send,
        disconnect,
        gameState,
        isConnected,
        gameId,
      }}
    >
      {children}
    </WebSocketContext.Provider>
  );
};
