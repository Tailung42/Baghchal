import {
  createContext,
  useContext,
  useRef,
  useState,
  useEffect,
  useCallback,
} from "react";
import { useNavigate } from "react-router-dom";
import { gameApi } from "../api/client";
import { authStorage } from "../utils/storage";
import { compareGameStates } from "../utils/GameUtils";

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
  const navigate = useNavigate();
  const socketRef = useRef(null);
  const gameIdRef = useRef(null);
  const [gameState, setGameState] = useState(initialGameState);
  const [isConnected, setIsConnected] = useState(false);
  const [gameId, setGameId] = useState(null);
  const [optimisticState, setOptimisticState] = useState(null);

  const connectWebSocket = useCallback((gameId) => {
    if (!gameId) {
      console.error("Cannot connect WebSocket without game ID");
      return;
    }

    // make sure our internal ref/state knows the current id immediately
    gameIdRef.current = gameId;
    setGameId(gameId);

    // Close existing connection
    if (socketRef.current) socketRef.current.close();

    const params = new URLSearchParams({
      game_id: gameId,
    });

    // create a new connection with access token
    const [accessToken, _] = authStorage.getToken();
    const ws = new WebSocket(`${baseSocketUrl}?${params}`, [accessToken]);
    ws.onopen = handleOpen;
    ws.onmessage = handleMessage;
    ws.onclose = handleClose;
    ws.onerror = handleError;
    socketRef.current = ws;
  });

  const createGameHTTP = useCallback(
    async (gameId, playerRole) => {
      try {
        const response = await gameApi.create(gameId, playerRole);
        const data = response.data;
        setGameId(data.game_id);
        setGameState(data.game_state);
        connectWebSocket(data.game_id);
        return data.game_id;
      } catch (error) {
        console.error("Error creating game:", error);
        throw error;
      }
    },
    [connectWebSocket],
  );

  const joinGameHTTP = useCallback(
    async (gameId) => {
      try {
        const response = await gameApi.join(gameId);
        const data = response.data;
        console.log("Joining response: ", response.data);
        setGameId(data.game_id);
        connectWebSocket(data.game_id);
        return data.game_id;
      } catch (error) {
        console.error("Error joining game:", error);
        throw error;
      }
    },
    [connectWebSocket],
  );

  const rejoinGameHTTP = useCallback(
    async (gameId) => {
      try {
        const response = await gameApi.rejoin(gameId);
        const data = response.data;
        setGameId(data.game_id);
        connectWebSocket(data.game_id);
        return data.game_id;
      } catch (error) {
        console.error("Error rejoining game:", error);
        throw error;
      }
    },
    [connectWebSocket],
  );

  const quickMatchHTTP = useCallback(async () => {
    try {
      const response = await gameApi.quickMatch();
      const gameId = response.data.game_id;
      setGameId(gameId);
      connectWebSocket(gameId);
      return gameId;
    } catch (error) {
      console.error("Error finding quick match:", error);
      throw error;
    }
  }, [connectWebSocket]);

  const startBotGameHTTP = useCallback(
    async (playerRole, difficulty) => {
      try {
        const response = await gameApi.startBot(playerRole, difficulty);
        const gameId = response.data.game_id;
        setGameId(gameId);
        connectWebSocket(gameId);
        return gameId;
      } catch (error) {
        console.error("Error starting bot game:", error);
        throw error;
      }
    },
    [connectWebSocket],
  );

  const sendCommand = useCallback((command, payload = {}) => {
    const envelope = JSON.stringify({ command, payload });
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(envelope);
    } else {
      console.warn("WebSocket is not connected. Cannot send command:", command);
    }
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

  const updateOptimisticState = useCallback((newState) => {
    setOptimisticState(newState);
  }, []);

  const clearOptimisticState = useCallback(() => {
    setOptimisticState(null);
  }, []);

  const handleOpen = () => {
    setIsConnected(true);
    console.log("WebSocket connected");
  };

  const handleMessage = (event) => {
    let data;
    try {
      data = JSON.parse(event.data);
    } catch (err) {
      console.warn("WebSocket: failed to parse message", err);
      return;
    }

    // Server envelope: {"event": "<type>", "payload": {...}}
    const eventPayload = data.payload;
    const serverEvent = data.event;

    if (serverEvent === "gameState") {
      const newGameState = eventPayload?.game_state;
      if (newGameState) {
        if (optimisticState && !compareGameStates(optimisticState, newGameState)) {
          console.warn("Server state differs from optimistic state. Reconciliation needed.");
        } else {
          clearOptimisticState();
        }

        setGameState(newGameState);

        const idToUse = (
          newGameState.game_id ||
          gameIdRef.current ||
          gameId ||
          ""
        ).replace("game_", "");

        if (idToUse && !window.location.pathname.includes("/game/")) {
          navigate(`/game/${idToUse}`);
        }
      }
      return;
    }

    if (serverEvent === "error") {
      console.warn("WebSocket server error:", eventPayload?.code, eventPayload?.message);
      return;
    }

    if (serverEvent === "playerLeft" || serverEvent === "playerDisconnected") {
      if (eventPayload?.username === authStorage.getUsername()) {
        disconnect();
      }
      return;
    }

    if (serverEvent === "gameOver") {
      setWinner(eventPayload?.winner || "");
      setWinnerModalOpen(true);
      return;
    }
  };

  const handleClose = () => {
    setIsConnected(false);
    console.log("WebSocket closed");
    setWinnerModalOpen(false);
  };

  const handleError = (error) => {
    console.error("WebSocket error:", error);
    setIsConnected(false);
    setWinnerModalOpen(false);
  };

  const [winnerModalOpen, setWinnerModalOpen] = useState(false);
  const [winner, setWinner] = useState("");

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
        startBotGame: startBotGameHTTP,
        send,
        sendCommand,
        disconnect,
        gameState,
        isConnected,
        gameId,
        optimisticState,
        updateOptimisticState,
        clearOptimisticState,
        winnerModalOpen,
        setWinnerModalOpen,
        winner,
      }}
    >
      {children}
    </WebSocketContext.Provider>
  );
};
