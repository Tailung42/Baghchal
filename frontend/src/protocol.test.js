import { describe, it, expect, vi } from "vitest";

describe("WebSocket protocol contract", () => {
  function parseClientEnvelope(raw) {
    if (!raw || typeof raw !== "object") {
      throw new Error("Unsupported or malformed command");
    }
    const command = raw.command;
    const payload = raw.payload;
    if (typeof command !== "string" || !command) {
      throw new Error("Unsupported or malformed command");
    }
    if (!["move", "leave"].includes(command)) {
      throw new Error("Unsupported or malformed command");
    }
    if (!payload || typeof payload !== "object") {
      throw new Error("Unsupported or malformed command");
    }
    return { command, payload };
  }

  function makeEvent(event, payload) {
    const allowed = ["gameState", "playerLeft", "playerDisconnected", "gameOver", "error"];
    if (!allowed.includes(event)) {
      throw new Error("Unknown server event type");
    }
    return { event, payload };
  }

  function makeErrorEvent(code, message) {
    return makeEvent("error", { code, message });
  }

  it("parses a move command", () => {
    const envelope = parseClientEnvelope({
      command: "move",
      payload: { moveType: "place", toKey: "0-1" },
    });
    expect(envelope.command).toBe("move");
    expect(envelope.payload).toEqual({ moveType: "place", toKey: "0-1" });
  });

  it("parses a leave command", () => {
    const envelope = parseClientEnvelope({ command: "leave", payload: {} });
    expect(envelope.command).toBe("leave");
    expect(envelope.payload).toEqual({});
  });

  it("rejects an unsupported command", () => {
    expect(() => parseClientEnvelope({ command: "ping", payload: {} })).toThrow();
  });

  it("rejects a non-object payload", () => {
    expect(() => parseClientEnvelope({ command: "move", payload: "bad" })).toThrow();
  });

  it("creates a gameState event", () => {
    const event = makeEvent("gameState", { game_state: { status: "ongoing" } });
    expect(event).toEqual({
      event: "gameState",
      payload: { game_state: { status: "ongoing" } },
    });
  });

  it("creates a playerLeft event", () => {
    const event = makeEvent("playerLeft", { username: "alice", role: "goat" });
    expect(event).toEqual({
      event: "playerLeft",
      payload: { username: "alice", role: "goat" },
    });
  });

  it("creates a playerDisconnected event", () => {
    const event = makeEvent("playerDisconnected", { username: "alice", role: "goat" });
    expect(event).toEqual({
      event: "playerDisconnected",
      payload: { username: "alice", role: "goat" },
    });
  });

  it("creates an error event", () => {
    const event = makeErrorEvent("invalid_move", "Move failed validation");
    expect(event).toEqual({
      event: "error",
      payload: { code: "invalid_move", message: "Move failed validation" },
    });
  });

  it("rejects an unknown server event", () => {
    expect(() => makeEvent("unknown", {})).toThrow();
  });
});
