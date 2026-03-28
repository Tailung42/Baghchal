import { useCallback } from "react";
import useSound from "use-sound";
import moveSound from "../assets/sounds/move_sound.mp3";
import captureSound from "../assets/sounds/capture_sound.mp3";

export function useGameSounds() {
  const [playMoveSound] = useSound(moveSound);
  const [playCaptureSound] = useSound(captureSound);

  const playMove = useCallback((isCaptured) => {
    if (isCaptured) {
      playCaptureSound();
    } else {
      playMoveSound();
    }
  }, [playMoveSound, playCaptureSound]);

  return { playMove, playMoveSound, playCaptureSound };
}
