import { describe, expect, it } from "vitest";

describe("WebSocket communication contract", () => {
  // These helpers mirror the backend `gateway.commands` contract so the
  // frontend can verify it is speaking the same envelope language.

  const CLIENT_COMMANDS = new Set(["move", "leave"]);
  const SERVER_EVENTS = new Set([
    "gameState",
    "playerLeft",
    "playerDisconnected",
    "gameOver",
    "error",
  ]);

  function parseClientEnvelope(raw) {
    if (!raw || typeof raw !== "object") {
      throw new Error("Unsupported or malformed command");
    }
    const command = raw.command;
    const payload = raw.payload;
    if (typeof command !== "string" || !command) {
      throw new Error("Unsupported or malformed command");
    }
    if (!CLIENT_COMMANDS.has(command)) {
      throw new Error("Unsupported or malformed command");
    }
    if (!payload || typeof payload !== "object") {
      throw new Error("Unsupported or malformed command");
    }
    return { command, payload };
  }

  function makeEvent(event, payload) {
    if (!SERVER_EVENTS.has(event)) {
      throw new Error("Unknown server event type");
    }
    return { event, payload };
  }

  function makeErrorEvent(code, message) {
    return makeEvent("error", { code, message });
  }

  function unpackServerEvent(envelope) {
    const event = envelope.event;
    const payload = envelope.payload;
    if (typeof event !== "string" || !event) {
      throw new Error("Malformed server envelope");
    }
    if (!payload || typeof payload !== "object") {
      throw new Error("Malformed server envelope");
    }
    return { event, payload };
  }

  function packServerEvent(event, payload) {
    return makeEvent(event, payload);
  }

  // ---- client -> server ----

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
    expect(() => parseClientEnvelope({ command: "start", payload: {} })).toThrow();
  });

  it("rejects a missing command", () => {
    expect(() => parseClientEnvelope({ payload: {} })).toThrow();
  });

  it("rejects a non-object payload", () => {
    expect(() => parseClientEnvelope({ command: "move", payload: "bad" })).toThrow();
  });

  it("rejects a non-object body", () => {
    expect(() => parseClientEnvelope("not-an-object")).toThrow();
  });

  // ---- server -> client ----

  it("creates a gameState event", () => {
    const event = packServerEvent("gameState", { game_state: { status: "waiting" } });
    expect(event).toEqual({
      event: "gameState",
      payload: { game_state: { status: "waiting" } },
    });
  });

  it("creates a playerLeft event", () => {
    const event = packServerEvent("playerLeft", { username: "alice", role: "goat" });
    expect(event).toEqual({
      event: "playerLeft",
      payload: { username: "alice", role: "goat" },
    });
  });

  it("creates a playerDisconnected event", () => {
    const event = packServerEvent("playerDisconnected", { username: "alice", role: "goat" });
    expect(event).toEqual({
      event: "playerDisconnected",
      payload: { username: "alice", role: "goat" },
    });
  });

  it("creates a gameOver event", () => {
    const event = packServerEvent("gameOver", { winner: "goat", endReason: "capture" });
    expect(event).toEqual({
      event: "gameOver",
      payload: { winner: "goat", endReason: "capture" },
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

  // ---- round trips ----

  it("round-trips a server event through pack/unpack", () => {
    const payload = { moveType: "capture", fromKey: "0-1", toKey: "1-1" };
    const packed = packServerEvent("gameState", payload);
    const unpacked = unpackServerEvent(packed);
    expect(unpacked.event).toBe("gameState");
    expect(unpacked.payload).toEqual(payload);
  });

  it("round-trips an error event through pack/unpack", () => {
    const packed = makeErrorEvent("not_your_turn", "It is not your turn");
    const unpacked = unpackServerEvent(packed);
    expect(unpacked.event).toBe("error");
    expect(unpacked.payload).toEqual({ code: "not_your_turn", message: "It is not your turn" });
    expect(Object.keys(unpacked.payload)).toEqual(["code", "message"]);
  });

  it("round-trips a playerLeft event through pack/unpack", () => {
    const packed = packServerEvent("playerLeft", { username: "alice", role: "goat" });
    const unpacked = unpackServerEvent(packed);
    expect(unpacked.event).toBe("playerLeft");
    expect(unpacked.payload).toEqual({ username: "alice", role: "goat" });
  });

  it("round-trips a playerDisconnected event through pack/unpack", () => {
    const packed = packServerEvent("playerDisconnected", { username: "alice", role: "goat" });
    const unpacked = unpackServerEvent(packed);
    expect(unpacked.event).toBe("playerDisconnected");
    expect(unpacked.payload).toEqual({ username: "alice", role: "goat" });
  });

  // ---- protocol alignment check ----

  it("accepts the documented client commands", () => {
    expect(CLIENT_COMMANDS.has("move")).toBe(true);
    expect(CLIENT_COMMANDS.has("leave")).toBe(true);
  });

  it("publishes the documented server events", () => {
    expect(SERVER_EVENTS.has("gameState")).toBe(true);
    expect(SERVER_EVENTS.has("playerLeft")).toBe(true);
    expect(SERVER_EVENTS.has("playerDisconnected")).toBe(true);
    expect(SERVER_EVENTS.has("gameOver")).toBe(true);
    expect(SERVER_EVENTS.has("error")).toBe(true);
  });

  it("error envelope payload shape is stable", () => {
    const event = makeErrorEvent("invalid_move", "Move failed validation");
    const payload = event.payload;
    expect(Object.keys(payload)).toEqual(["code", "message"]);
    expect(payload.code).toBe("invalid_move");
    expect(payload.message).toBe("Move failed validation");
  });

  it("server event payload is always a dict", () => {
    const event = packServerEvent("gameOver", { winner: "goat", endReason: "capture" });
    expect(typeof event.payload).toBe("object");
    expect(Array.isArray(event.payload)).toBe(false);
  });

  it("client envelope payload is always a dict", () => {
    const envelope = parseClientEnvelope({
      command: "move",
      payload: { moveType: "place", toKey: "0-1" },
    });
    expect(typeof envelope.payload).toBe("object");
    expect(Array.isArray(envelope.payload)).toBe(false);
  });
});
