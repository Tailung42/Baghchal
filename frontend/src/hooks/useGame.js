import { useCallback } from 'react';
import { useWebSocket } from '../context/WebSocketContext';

export function useGame() {
  const { 
    createGame: createGameHTTP,
    joinGame: joinGameHTTP,
    rejoinGame: rejoinGameHTTP,
    quickMatch: quickMatchHTTP,
    send, 
    disconnect, 
    gameState, 
    isConnected 
  } = useWebSocket();

  const createGame = useCallback(async (gameId, playerRole) => {
    try {
      await createGameHTTP(gameId, playerRole);
    } catch (error) {
      console.error('Failed to create game:', error);
      throw error;
    }
  }, [createGameHTTP]);

  const joinGame = useCallback(async (gameId) => {
    try {
      await joinGameHTTP(gameId);
    } catch (error) {
      console.error('Failed to join game:', error);
      throw error;
    }
  }, [joinGameHTTP]);

  const rejoinGame = useCallback(async (gameId) => {
    try {
      await rejoinGameHTTP(gameId);
    } catch (error) {
      console.error('Failed to rejoin game:', error);
      throw error;
    }
  }, [rejoinGameHTTP]);

  const quickMatch = useCallback(async () => {
    try {
      await quickMatchHTTP();
    } catch (error) {
      console.error('Failed to find quick match:', error);
      throw error;
    }
  }, [quickMatchHTTP]);

  const sendMove = useCallback((move) => {
    send(JSON.stringify({ message: { type: 'newMove', move } }));
  }, [send]);

  const exitGame = useCallback(() => {
    send(JSON.stringify({ message: { type: 'exitGame' } }));
    disconnect();
  }, [send, disconnect]);

  const isGameInProgress = useCallback(() => {
    return gameState?.status !== 'over' && gameState?.status !== 'waiting';
  }, [gameState]);

  return {
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
