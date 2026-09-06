"""
provides game state, validates and applies move
"""

import copy

from .board import check_goat_win, check_tiger_win, get_mid_key
from .movegen import generate_moves


def get_initial_game_state():
    return {
        "board": {"0-0": "tiger", "0-4": "tiger", "4-0": "tiger", "4-4": "tiger"},
        "currentPlayer": "goat",
        "phase": "placement",
        "unusedGoat": 20,
        "deadGoatCount": 0,
        "status": "waiting",
        "winner": None,
        "newPosition": "",
        "previousPosition": "",
        "isCaptured": False,
        "player": {
            "goat": "",
            "tiger": "",
        },
        "history": [],
    }


def to_user_coord(key):
    if not key:
        return ""
    r, c = map(int, key.split("-"))
    return f"{r + 1}-{c + 1}"


def _canonical_move(move, game_state):
    """
    Normalize a candidate move for comparison against generated moves.

    The frontend sends ``fromKey: null`` on place moves and omits
    ``pieceType`` when it is undefined, while older payloads omit
    ``currentPlayer`` entirely. Normalizing all of these to one shape keeps
    validation strict without being brittle about key presence. Returns a
    hashable tuple so generated moves can live in a set.
    """
    move_type = move.get("moveType")
    return (
        move_type,
        move.get("currentPlayer") or game_state.get("currentPlayer"),
        None if move_type == "place" else move.get("fromKey"),
        move.get("toKey"),
    )


def is_valid_move(game_state, move):
    """
    A move is valid if and only if it is one of the generated legal moves.

    This enforces turn ownership, phase rules, adjacency, and capture
    semantics in one place: whatever ``generate_moves`` produces is legal
    and nothing else is.
    """
    if not isinstance(move, dict):
        return False
    if move.get("moveType") not in ("place", "displace", "capture"):
        return False

    candidate = _canonical_move(move, game_state)
    return candidate in {
        _canonical_move(m, game_state) for m in generate_moves(game_state)
    }


def check_game_over(game_state):
    board = game_state["board"]
    dead_goats = game_state["deadGoatCount"]

    if check_tiger_win(dead_goats):
        game_state["status"] = "over"
        game_state["winner"] = "tiger"
        return True

    if check_goat_win(board):
        game_state["status"] = "over"
        game_state["winner"] = "goat"
        return True

    return False


def apply_move(game_state, move):
    if not isinstance(move, dict):
        return None

    new_state = copy.deepcopy(game_state)
    board = new_state["board"]
    current_player = new_state["currentPlayer"]
    move_type = move.get("moveType")
    from_key = move.get("fromKey")
    to_key = move.get("toKey")

    if not is_valid_move(new_state, move):
        return None

    new_state["isCaptured"] = False

    if move_type == "place":
        board[to_key] = "goat"
        new_state["unusedGoat"] -= 1
        if new_state["unusedGoat"] == 0:
            new_state["phase"] = "displacement"

    elif move_type == "displace":
        piece = board.pop(from_key)
        board[to_key] = piece

    elif move_type == "capture":
        piece = board.pop(from_key)
        board[to_key] = piece
        mid_key = get_mid_key(from_key, to_key)
        if board.get(mid_key) == "goat":
            board.pop(mid_key)
            new_state["deadGoatCount"] += 1
            new_state["isCaptured"] = True

    user_from = to_user_coord(from_key)
    user_to = to_user_coord(to_key)

    if move_type == "place":
        history_entry = f"{current_player}: placed at {user_to}"
    else:
        history_entry = f"{current_player}: {user_from} -> {user_to}"

    new_state["history"].append(history_entry)

    new_state["currentPlayer"] = "tiger" if current_player == "goat" else "goat"
    new_state["newPosition"] = to_key
    new_state["previousPosition"] = from_key

    return new_state
