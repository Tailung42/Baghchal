import { describe, it, expect } from "vitest";
import { applyMove, compareGameStates } from "./GameUtils";

describe("applyMove", () => {
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
    status: "ongoing",
    winner: null,
    newPosition: "",
    previousPosition: "",
    player: { goat: "player1", tiger: "player2" },
    history: [],
    isCaptured: false,
  };

  describe("place move", () => {
    it("should place a goat and decrement unusedGoat", () => {
      const move = {
        moveType: "place",
        fromKey: null,
        toKey: "2-2",
      };

      const result = applyMove(initialGameState, move);

      expect(result.board["2-2"]).toBe("goat");
      expect(result.unusedGoat).toBe(19);
      expect(result.history).toContain("goat: placed at 3-3");
    });

    it("should switch to tiger after placing", () => {
      const move = {
        moveType: "place",
        fromKey: null,
        toKey: "1-1",
      };

      const result = applyMove(initialGameState, move);

      expect(result.currentPlayer).toBe("tiger");
    });

    it("should change phase to displacement when unusedGoat reaches 0", () => {
      const state = { ...initialGameState, unusedGoat: 1 };
      const move = {
        moveType: "place",
        fromKey: null,
        toKey: "2-2",
      };

      const result = applyMove(state, move);

      expect(result.phase).toBe("displacement");
    });

    it("should set newPosition and previousPosition", () => {
      const move = {
        moveType: "place",
        fromKey: null,
        toKey: "2-2",
      };

      const result = applyMove(initialGameState, move);

      expect(result.newPosition).toBe("2-2");
      expect(result.previousPosition).toBe(null);
    });
  });

  describe("displace move", () => {
    it("should move a piece from one position to another", () => {
      const state = {
        ...initialGameState,
        board: {
          ...initialGameState.board,
          "2-2": "goat",
        },
      };
      const move = {
        moveType: "displace",
        fromKey: "2-2",
        toKey: "2-3",
      };

      const result = applyMove(state, move);

      expect(result.board["2-2"]).toBeUndefined();
      expect(result.board["2-3"]).toBe("goat");
    });

    it("should switch player after displace", () => {
      const state = {
        ...initialGameState,
        board: { ...initialGameState.board, "2-2": "goat" },
      };
      const move = {
        moveType: "displace",
        fromKey: "2-2",
        toKey: "2-3",
      };

      const result = applyMove(state, move);

      expect(result.currentPlayer).toBe("tiger");
    });

    it("should add history entry for displace move", () => {
      const state = {
        ...initialGameState,
        board: { ...initialGameState.board, "2-2": "goat" },
      };
      const move = {
        moveType: "displace",
        fromKey: "2-2",
        toKey: "2-3",
      };

      const result = applyMove(state, move);

      expect(result.history).toContain("goat: 3-3 -> 3-4");
    });
  });

  describe("capture move", () => {
    it("should move tiger and capture goat in between", () => {
      const state = {
        ...initialGameState,
        currentPlayer: "tiger",
        phase: "displacement",
        board: {
          "0-0": "tiger",
          "0-4": "tiger",
          "1-1": "goat",
          "4-0": "tiger",
          "4-4": "tiger",
        },
      };
      const move = {
        moveType: "capture",
        fromKey: "0-0",
        toKey: "2-2",
      };

      const result = applyMove(state, move);

      expect(result.board["0-0"]).toBeUndefined();
      expect(result.board["2-2"]).toBe("tiger");
      expect(result.board["1-1"]).toBeUndefined();
      expect(result.deadGoatCount).toBe(1);
      expect(result.isCaptured).toBe(true);
    });

    it("should switch to goat after capture", () => {
      const state = {
        ...initialGameState,
        currentPlayer: "tiger",
        phase: "displacement",
        board: {
          "0-0": "tiger",
          "0-4": "tiger",
          "2-1": "goat",
          "4-0": "tiger",
          "4-4": "tiger",
        },
      };
      const move = {
        moveType: "capture",
        fromKey: "0-0",
        toKey: "2-0",
      };

      const result = applyMove(state, move);

      expect(result.currentPlayer).toBe("goat");
    });
  });

  describe("does not mutate original state", () => {
    it("should return a new object", () => {
      const move = {
        moveType: "place",
        fromKey: null,
        toKey: "2-2",
      };

      const result = applyMove(initialGameState, move);

      expect(result).not.toBe(initialGameState);
      expect(initialGameState.board["2-2"]).toBeUndefined();
    });
  });
});

describe("compareGameStates", () => {
  const baseState = {
    board: { "0-0": "tiger" },
    currentPlayer: "goat",
    phase: "placement",
    unusedGoat: 20,
    deadGoatCount: 0,
    status: "ongoing",
    winner: null,
    newPosition: "",
    previousPosition: "",
  };

  it("should return true for identical states", () => {
    expect(compareGameStates(baseState, baseState)).toBe(true);
  });

  it("should return true for states with same values", () => {
    const state2 = {
      board: { "0-0": "tiger" },
      currentPlayer: "goat",
      phase: "placement",
      unusedGoat: 20,
      deadGoatCount: 0,
      status: "ongoing",
      winner: null,
      newPosition: "",
      previousPosition: "",
    };
    expect(compareGameStates(baseState, state2)).toBe(true);
  });

  it("should return false when boards differ", () => {
    const differentBoard = {
      ...baseState,
      board: { "0-0": "tiger", "2-2": "goat" },
    };
    expect(compareGameStates(baseState, differentBoard)).toBe(false);
  });

  it("should return false when currentPlayer differs", () => {
    const differentPlayer = { ...baseState, currentPlayer: "tiger" };
    expect(compareGameStates(baseState, differentPlayer)).toBe(false);
  });

  it("should return false when phase differs", () => {
    const differentPhase = { ...baseState, phase: "displacement" };
    expect(compareGameStates(baseState, differentPhase)).toBe(false);
  });

  it("should return false when unusedGoat differs", () => {
    const differentUnused = { ...baseState, unusedGoat: 15 };
    expect(compareGameStates(baseState, differentUnused)).toBe(false);
  });

  it("should return false when deadGoatCount differs", () => {
    const differentDead = { ...baseState, deadGoatCount: 1 };
    expect(compareGameStates(baseState, differentDead)).toBe(false);
  });

  it("should return false when status differs", () => {
    const differentStatus = { ...baseState, status: "over" };
    expect(compareGameStates(baseState, differentStatus)).toBe(false);
  });

  it("should return false when winner differs", () => {
    const differentWinner = { ...baseState, winner: "tiger" };
    expect(compareGameStates(baseState, differentWinner)).toBe(false);
  });

  it("should return false when positions differ", () => {
    const differentPositions = {
      ...baseState,
      newPosition: "2-2",
      previousPosition: "1-1",
    };
    expect(compareGameStates(baseState, differentPositions)).toBe(false);
  });

  it("should return false for null states", () => {
    expect(compareGameStates(null, baseState)).toBe(false);
    expect(compareGameStates(baseState, null)).toBe(false);
    expect(compareGameStates(null, null)).toBe(false);
  });
});
