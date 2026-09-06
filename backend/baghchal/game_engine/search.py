"""
Negamax search over generated moves.

Alpha-beta pruning with captures-first move ordering, iterative deepening,
and an optional wall-clock budget so the server never blocks on a move.
The search is pure and deterministic for a fixed depth (no clock influence),
which keeps tests exact; the time budget only ever skips uncompleted depths.
"""

from __future__ import annotations

import time
from typing import Any

from .evaluate import INF, evaluate_position
from .game_state import apply_move
from .movegen import generate_moves

# Check the clock every N nodes instead of every node; ``time.monotonic()``
# is cheap but not free and this keeps the overhead near zero.
_TIME_CHECK_INTERVAL = 1024


class _TimeUp(Exception):
    """Raised inside the search when the time budget is exhausted."""


class _SearchContext:
    __slots__ = ("deadline", "nodes")

    def __init__(self, deadline: float | None):
        self.deadline = deadline
        self.nodes = 0


def _check_time(ctx: _SearchContext) -> None:
    if ctx.deadline is None:
        return
    if (ctx.nodes & (_TIME_CHECK_INTERVAL - 1)) == 0 and time.monotonic() >= ctx.deadline:
        raise _TimeUp


def _negamax(
    state: dict[str, Any],
    depth: int,
    alpha: int,
    beta: int,
    ctx: _SearchContext,
    ply: int = 0,
) -> int:
    ctx.nodes += 1
    _check_time(ctx)

    score = evaluate_position(state)
    if abs(score) >= INF:
        # Prefer faster wins and slower losses: the fewer plies from the
        # root, the better a win (and the worse a loss) is. Penalizing by
        # plies-from-root — not remaining depth — is what makes a mate-in-1
        # beat a longer forced win.
        return score - ply if score > 0 else score + ply
    if depth == 0:
        return score

    best = -INF
    for move in generate_moves(state):
        child = apply_move(state, move)
        if child is None:
            continue
        value = -_negamax(child, depth - 1, -beta, -alpha, ctx, ply + 1)
        if value > best:
            best = value
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def _search_at_depth(
    state: dict[str, Any],
    depth: int,
    ctx: _SearchContext,
) -> dict[str, Any] | None:
    """
    Best move for an exact search depth.

    Returns None when the move list is empty (game over) or when the time
    budget was exhausted mid-search (in which case the previous depth's
    result should be kept).
    """
    best_move = None
    best_score = -INF
    alpha = -INF

    for move in generate_moves(state):
        child = apply_move(state, move)
        if child is None:
            continue
        value = -_negamax(child, depth - 1, -INF, -alpha, ctx, 1)
        if value > best_score:
            best_score = value
            best_move = move
        if value > alpha:
            alpha = value

    return best_move


def search_best_move(
    game_state: dict[str, Any],
    *,
    max_depth: int = 4,
    time_limit_ms: float | None = None,
) -> dict[str, Any] | None:
    """
    Find the best move for the player to move.

    Iterative deepening from depth 1 upward; ``time_limit_ms`` caps the whole
    search (pass None for a deterministic fixed-depth search). Returns None
    when the game is already over or no legal moves exist.
    """
    if not isinstance(game_state, dict):
        return None
    if abs(evaluate_position(game_state)) >= INF:
        return None
    if not generate_moves(game_state):
        return None

    deadline = (
        None if time_limit_ms is None else time.monotonic() + time_limit_ms / 1000.0
    )

    best = None
    for depth in range(1, max_depth + 1):
        if deadline is not None and time.monotonic() >= deadline:
            break
        try:
            candidate = _search_at_depth(game_state, depth, _SearchContext(deadline))
        except _TimeUp:
            break
        if candidate is None:
            break
        best = candidate

    return best