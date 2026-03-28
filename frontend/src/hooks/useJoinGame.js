import { useEffect, useRef } from "react";

export function useJoinGame({ gameId, isLoading, isConnected, isInGame, joinGame, rejoinGame }) {
  const intentionalDisconnect = useRef(false);

  useEffect(() => {
    if (isLoading || !gameId || isConnected || intentionalDisconnect.current) {
      return;
    }

    if (isInGame()) {
      console.log("rejoin attempt");
      rejoinGame(gameId).then(() => {
        intentionalDisconnect.current = false;
      });
    } else {
      console.log("join attempt");
      joinGame(gameId).then(() => {
        intentionalDisconnect.current = false;
      });
    }
  }, [isLoading, gameId, isConnected, isInGame, joinGame, rejoinGame]);

  return { intentionalDisconnect };
}
