import { useEffect, useState, useRef } from "react";
import { useBlocker } from "react-router-dom";

export function useGameNavigation({ isInGame, isConnected, isGameInProgress, joinGame, rejoinGame, exitGame }) {
  const [showLeaveConfirmation, setShowLeaveConfirmation] = useState(false);
  const [pendingNavigation, setPendingNavigation] = useState(null);
  const intentionalDisconnect = useRef(false);

  const blocker = useBlocker(
    ({ currentLocation, nextLocation }) =>
      isGameInProgress() && currentLocation.pathname !== nextLocation.pathname,
  );

  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (isGameInProgress()) {
        e.preventDefault();
        e.returnValue = "Game is in progress. Are you sure you want to leave?";
        return e.returnValue;
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [isGameInProgress]);

  useEffect(() => {
    if (blocker.state === "blocked") {
      setShowLeaveConfirmation(true);
      setPendingNavigation(() => blocker.proceed);
    }
  }, [blocker]);

  const handleLeaveConfirm = () => {
    setShowLeaveConfirmation(false);
    if (pendingNavigation) {
      pendingNavigation();
      intentionalDisconnect.current = true;
      exitGame();
      setPendingNavigation(null);
    }
  };

  const handleLeaveCancel = () => {
    setShowLeaveConfirmation(false);
    if (blocker.state === "blocked") {
      blocker.reset();
    }
    setPendingNavigation(null);
  };

  const handleGameEnd = () => {
    if (blocker.state === "blocked") {
      blocker.reset();
    }
  };

  return {
    blocker,
    showLeaveConfirmation,
    handleLeaveConfirm,
    handleLeaveCancel,
    handleGameEnd,
    intentionalDisconnect,
  };
}
