import threading
from .gameState import get_game, set_game, get_all_games, delete_game
from baghchal.models import Game


def get_initial_game_state():
    """Returns the initial state of BaghChal game."""
    return {
        "board": {"0-0": "tiger", "0-4": "tiger", "4-0": "tiger", "4-4": "tiger"},
        "currentPlayer": "goat",
        "phase": "placement",  # can be displacement',  'placement
        "unusedGoat": 20,
        "deadGoatCount": 0,
        "status": "waiting",  # can be 'waiting', 'ongoing', 'over'
        "winner": None,  # can be goat or tiger
        "newPosition": "",
        "previousPosition": "",
        "isCaptured": False,
        "player": {
            "goat": "",  # username
            "tiger": "",  # username
        },
        "history": [],
    }


def update_game_state(room_name, move):
    """applies the move to the game state of id :room_name if the move is valid"""
    game_state = get_game(room_name)
    if not game_state:
        return None
        
    board = game_state["board"]

    current_player = game_state["currentPlayer"]
    move_type = move["moveType"]
    from_key = move.get("fromKey")
    to_key = move.get("toKey")

    if not isvalid_move(game_state, move):
        return None

    # update board with the move
    game_state["isCaptured"] = False

    if move_type == "place":
        board[to_key] = "goat"
        game_state["unusedGoat"] -= 1
        if game_state["unusedGoat"] == 0:
            game_state["phase"] = "displacement"

    elif move_type == "displace":
        piece = board.pop(from_key)
        board[to_key] = piece

    elif move_type == "capture":
        piece = board.pop(from_key)
        board[to_key] = piece
        mid_key = get_mid_key(from_key, to_key)
        if board.get(mid_key) == "goat":
            board.pop(mid_key)
            game_state["deadGoatCount"] += 1
            game_state["isCaptured"] = True

    # add move to the history
    user_from = to_user_coord(from_key)
    user_to = to_user_coord(to_key)

    if move_type == "place":
        history_entry = f"{current_player}: placed at {user_to}"
    else:
        history_entry = f"{current_player}: {user_from} -> {user_to}"

    game_state["history"].append(history_entry)

    # switch player
    game_state["currentPlayer"] = "tiger" if current_player == "goat" else "goat"
    game_state["newPosition"] = to_key
    game_state["previousPosition"] = from_key

    check_game_over(game_state)
    
    # Save the updated state back to Redis
    set_game(room_name, game_state)

    return game_state


def isvalid_move(game_state, move):
    """Checks if a move is valid for given game state"""

    board = game_state["board"]
    move_type = move["moveType"]
    from_key = move.get("fromKey")
    to_key = move.get("toKey")
    current_player = move.get("currentPlayer")

    # if there isn't already another piece in the bhard
    if move_type == "place":
        return to_key not in board

    # if the player is actually clicking their own key and moving to empty place
    if move_type in ("displace", "capture"):
        return board.get(from_key) == current_player and to_key not in board

    return False


def check_game_over(game_state):
    board = game_state["board"]
    dead_goats = game_state["deadGoatCount"]

    # Tiger win condition
    if dead_goats >= 5:
        game_state["status"] = "over"
        game_state["winner"] = "tiger"
        print("tiger won!!!")
        return

    # Goat win condition
    tigers = [position for position, piece in board.items() if piece == "tiger"]
    if all(is_blocked(pos, board) for pos in tigers):
        game_state["status"] = "over"
        game_state["winner"] = "goat"
        print("goat won!!!")
        return True

    return False


def is_blocked(pos, board):
    possible_moves = get_possible_tiger_moves(pos)
    for move in possible_moves:
        if move not in board:  # even if one move is empty tiger is not blocked
            return False
    if can_capture(pos, board):
        return False  # not blocked until it can capture
    return True


def get_possible_tiger_moves(position):
    move_connections = {
        # Row 0
        "0-0": ["0-1", "1-0", "1-1"],
        "0-1": ["0-0", "0-2", "1-1"],
        "0-2": ["0-1", "0-3", "1-1", "1-2", "1-3"],
        "0-3": ["0-2", "0-4", "1-3"],
        "0-4": ["0-3", "1-3", "1-4"],
        "1-0": ["0-0", "1-1", "2-0"],
        "1-1": ["0-0", "0-1", "0-2", "1-0", "1-2", "2-0", "2-1", "2-2"],
        "1-2": ["0-2", "1-1", "1-3", "2-2"],
        "1-3": ["0-2", "0-3", "0-4", "1-2", "1-4", "2-2", "2-3", "2-4"],
        "1-4": ["0-4", "1-3", "2-4"],
        "2-0": ["1-0", "1-1", "2-1", "3-0", "3-1"],
        "2-1": ["1-1", "2-0", "2-2", "3-1"],
        "2-2": ["1-1", "1-2", "1-3", "2-1", "2-3", "3-1", "3-2", "3-3"],
        "2-3": ["1-3", "2-2", "2-4", "3-3"],
        "2-4": ["1-3", "1-4", "2-3", "3-3", "3-4"],
        "3-0": ["2-0", "3-1", "4-0"],
        "3-1": ["2-0", "2-1", "2-2", "3-0", "3-2", "4-0", "4-1", "4-2"],
        "3-2": ["2-2", "3-1", "3-3", "4-2"],
        "3-3": ["2-2", "2-3", "2-4", "3-2", "3-4", "4-2", "4-3", "4-4"],
        "3-4": ["2-4", "3-3", "4-4"],
        # Row 4
        "4-0": ["3-0", "3-1", "4-1"],
        "4-1": ["3-1", "4-0", "4-2"],
        "4-2": ["3-1", "3-2", "3-3", "4-1", "4-3"],
        "4-3": ["3-3", "4-2", "4-4"],
        "4-4": ["3-3", "3-4", "4-3"],
    }

    return move_connections[position]


def can_capture(pos, board):
    capture_connections = {
        "0-0": ["0-2", "2-0", "2-2"],
        "0-1": ["0-3", "2-1"],
        "0-2": ["0-0", "0-4", "2-0", "2-2", "2-4"],
        "0-3": ["0-1", "2-3"],
        "0-4": ["0-2", "2-2", "2-4"],
        "1-0": ["1-2", "3-0"],
        "1-1": ["1-3", "3-1", "3-3"],
        "1-2": ["1-0", "1-4", "3-2"],
        "1-3": ["1-1", "3-1", "3-3"],
        "1-4": ["1-2", "3-4"],
        "2-0": ["0-0", "0-2", "2-2", "4-0", "4-2"],
        "2-1": ["0-1", "2-3", "4-1"],
        "2-2": ["0-0", "0-2", "0-4", "2-0", "2-4", "4-0", "4-2", "4-4"],
        "2-3": ["0-3", "2-1", "4-3"],
        "2-4": ["0-2", "0-4", "2-2", "4-2", "4-4"],
        "3-0": ["1-0", "3-2"],
        "3-1": ["1-1", "1-3", "3-3"],
        "3-2": ["1-2", "3-0", "3-4"],
        "3-3": ["1-1", "1-3", "3-1"],
        "3-4": ["1-4", "3-2"],
        "4-0": ["2-0", "2-2", "4-2"],
        "4-1": ["2-1", "4-3"],
        "4-2": ["2-0", "2-2", "2-4", "4-0", "4-4"],
        "4-3": ["2-3", "4-1"],
        "4-4": ["2-2", "2-4", "4-2"],
    }

    capture_positions = capture_connections[pos]
    # for each capture position:
    #     if the position is empty and middle piece is goat:
    # return true else return false
    for cap_pos in capture_positions:
        if (
            board.get(cap_pos) == None
            and board.get(get_mid_key(pos, cap_pos)) == "goat"
        ):
            return True
    return False


def cleanup_game_states():
    """Removes completed or abandoned games from Redis"""
    games = get_all_games()
    for game_id, game_state in games.items():
        # Remove finished games after delay
        # TODO: store the game to the database
        if game_state.get("status") == "over":
            schedule_game_removal(game_id, 30)

        # Remove truly abandoned games (no players at all)
        elif not any(game_state.get("player", {}).values()):
            schedule_game_removal(game_id)

        # one player left during ongoing game
        elif game_state.get("status") == "ongoing":
            players = game_state.get("player", {})
            if not players.get("goat") or not players.get("tiger"):
                # TODO: I don't know what feature to implement
                pass


def schedule_game_removal(game_id, delay=0):
    """Schedule a game for removal from Redis after delay seconds"""
    def remove_game():
        print("Removing Game: ", game_id)
        delete_game(game_id)

    # Run deletion in background thread
    timer = threading.Timer(delay, remove_game)
    timer.daemon = True
    timer.start()


def get_mid_key(from_key, to_key):
    from_row, from_col = map(int, from_key.split("-"))
    to_row, to_col = map(int, to_key.split("-"))
    mid_row = (from_row + to_row) // 2
    mid_col = (from_col + to_col) // 2
    return f"{mid_row}-{mid_col}"


def to_user_coord(key):
    """Convert internal 0-4 board key to user-facing 1-5"""
    if not key:
        return ""
    r, c = map(int, key.split("-"))
    return f"{r + 1}-{c + 1}"


def store_game(game_id, gamestate):
    game = Game(
        game_id=game_id,
        goat_player=gamestate["player"]["goat"],
        tiger_player=gamestate["player"]["tiger"],
        winning_layer=gamestate["winner"],
        move_data=gamestate["winner"],
    )
    game.save()
    print("Game stored: ", game_id)
