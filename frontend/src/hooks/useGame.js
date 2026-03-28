import { useCallback } from "react";
import applyMove from "../utils/applyMove";
import { useWebSocket } from "../context/WebSocketContext";
import { gameStorage } from "../utils/storage";

export function useGame() {
  const {
    createGame: createGameHTTP,
    joinGame: joinGameHTTP,
    rejoinGame: rejoinGameHTTP,
    quickMatch: quickMatchHTTP,
    send,
    disconnect,
    gameState,
    setGameState,
    isConnected,
  } = useWebSocket();

  const createGame = useCallback(
    async (gameId, playerRole) => {
      try {
        await createGameHTTP(gameId, playerRole);
        gameStorage.setGame(gameId);
      } catch (error) {
        console.error("Failed to create game:", error);
        throw error;
      }
    },
    [createGameHTTP],
  );

  const joinGame = useCallback(
    async (gameId) => {
      try {
        await joinGameHTTP(gameId);
        gameStorage.setGame(gameId);
      } catch (error) {
        console.error("Failed to join game:", error);
        throw error;
      }
    },
    [joinGameHTTP],
  );

  const rejoinGame = useCallback(
    async (gameId) => {
      try {
        await rejoinGameHTTP(gameId);
        gameStorage.setGame(gameId);
      } catch (error) {
        console.error("Failed to rejoin game:", error);
        throw error;
      }
    },
    [rejoinGameHTTP],
  );

  const quickMatch = useCallback(async () => {
    try {
      const gameId = await quickMatchHTTP();
      gameStorage.setGame(gameId);
    } catch (error) {
      console.error("Failed to find quick match:", error);
      throw error;
    }
  }, [quickMatchHTTP]);

  const sendMove = useCallback(
    (move) => {
      // Optimistically update the local game state before the server responds.
      // This eliminates the perceived lag from the round-trip to the server.
      const optimisticState = applyMove(gameState, move);
      if (optimisticState) {
        setGameState(optimisticState);
      }
      send(JSON.stringify({ message: { type: "newMove", move } }));
    },
    [send, gameState, setGameState],
  );

  const exitGame = useCallback(() => {
    gameStorage.removeGame();
    send(JSON.stringify({ message: { type: "exitGame" } }));
    disconnect();
  }, [send, disconnect]);

  const isGameInProgress = useCallback(() => {
    return gameState?.status !== "over" && gameState?.status !== "waiting";
  }, [gameState]);

  return {
    isInGame: gameStorage.isInGame,
    gameState,
    isConnected,
    createGame,
    joinGame,
    rejoinGame,
    quickMatch,
    sendMove,
    exitGame,
    isGameInProgress,
  };
}
