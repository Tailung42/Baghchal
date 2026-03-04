import { useCallback } from 'react';
import { useWebSocket } from '../context/WebSocketContext';

export function useGame() {
  const { connect, send, disconnect, gameState, isConnected } = useWebSocket();

  const joinGame = useCallback((gameId) => {
    connect(gameId, 'join');
  }, [connect]);

  const createGame = useCallback(() => {
    connect('', 'create');
  }, [connect]);

  const quickMatch = useCallback(() => {
    connect('', 'quick');
  }, [connect]);

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
    joinGame,
    createGame,
    quickMatch,
    sendMove,
    exitGame,
    isGameInProgress,
  };
}
