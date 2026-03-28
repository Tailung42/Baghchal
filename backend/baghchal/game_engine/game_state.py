"""
provides game state, validates and applies move
"""

from .board import check_goat_win, check_tiger_win, get_mid_key


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


def is_valid_move(game_state, move):
    board = game_state["board"]
    move_type = move["moveType"]
    from_key = move.get("fromKey")
    to_key = move.get("toKey")
    current_player = move.get("currentPlayer")

    if move_type == "place":
        return to_key not in board

    if move_type in ("displace", "capture"):
        return board.get(from_key) == current_player and to_key not in board

    return False


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
    import copy

    new_state = copy.deepcopy(game_state)
    board = new_state["board"]
    current_player = new_state["currentPlayer"]
    move_type = move["moveType"]
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
