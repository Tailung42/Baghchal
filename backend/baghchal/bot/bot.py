"""
Bot player facade.

Public entry point: ``choose_bot_move(game_state, *, difficulty=...)``.

Pure and synchronous with no I/O, so it can be called straight from the
consumer's event loop without blocking other connections for more than the
configured time budget.
"""

from __future__ import annotations

from typing import Any

from baghchal.game_engine.search import search_best_move

# Difficulty → search limits. Depth raises playing strength; the time budget
# is a safety cap so a single move never stalls the server.
DIFFICULTIES = {
    "easy": {"max_depth": 2, "time_limit_ms": 100},
    "medium": {"max_depth": 4, "time_limit_ms": 400},
    "hard": {"max_depth": 6, "time_limit_ms": 1200},
}
DEFAULT_DIFFICULTY = "medium"


def choose_bot_move(
    game_state: dict[str, Any],
    *,
    difficulty: str = DEFAULT_DIFFICULTY,
    max_depth: int | None = None,
    time_limit_ms: float | None = None,
) -> dict[str, Any] | None:
    """
    Pick the bot's move for the given position.

    ``difficulty`` selects the depth/time defaults; ``max_depth`` and
    ``time_limit_ms`` override them. Returns the chosen move (same wire shape
    as a human move), or None when the game is over / no move is possible.
    """
    config = DIFFICULTIES.get(difficulty, DIFFICULTIES[DEFAULT_DIFFICULTY])
    return search_best_move(
        game_state,
        max_depth=max_depth if max_depth is not None else config["max_depth"],
        time_limit_ms=(
            time_limit_ms if time_limit_ms is not None else config["time_limit_ms"]
        ),
    )