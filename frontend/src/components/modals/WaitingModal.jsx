import { useState } from "react";
import { LoadingModal } from "./LoadingModal";

export function WaitingModal({ isOpen }) {
  return (
    <LoadingModal
      isOpen={isOpen}
      title="Waiting for player..."
      subtext="Looking for another player to join the game"
    />
  );
}
