"""
contains board rules: capture and move connection, win conditions and blocking logic

"""

def get_mid_key(from_key, to_key):
    from_row, from_col = map(int, from_key.split("-"))
    to_row, to_col = map(int, to_key.split("-"))
    mid_row = (from_row + to_row) // 2
    mid_col = (from_col + to_col) // 2
    return f"{mid_row}-{mid_col}"


MOVE_CONNECTIONS = {
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
    "4-0": ["3-0", "3-1", "4-1"],
    "4-1": ["3-1", "4-0", "4-2"],
    "4-2": ["3-1", "3-2", "3-3", "4-1", "4-3"],
    "4-3": ["3-3", "4-2", "4-4"],
    "4-4": ["3-3", "3-4", "4-3"],
}

CAPTURE_CONNECTIONS = {
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


def get_possible_tiger_moves(position):
    return MOVE_CONNECTIONS[position]


def can_capture(pos, board):
    capture_positions = CAPTURE_CONNECTIONS.get(pos, [])
    for cap_pos in capture_positions:
        if (
            board.get(cap_pos) is None
            and board.get(get_mid_key(pos, cap_pos)) == "goat"
        ):
            return True
    return False


def is_blocked(pos, board):
    possible_moves = get_possible_tiger_moves(pos)
    for move in possible_moves:
        if move not in board:
            return False
    if can_capture(pos, board):
        return False
    return True


def check_tiger_win(dead_goats):
    return dead_goats >= 5


def check_goat_win(board):
    tigers = [position for position, piece in board.items() if piece == "tiger"]
    return all(is_blocked(pos, board) for pos in tigers)
