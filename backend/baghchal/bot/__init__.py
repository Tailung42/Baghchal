"""
Bot package.

The bot is a server-side player that chooses moves with the game engine's
search (``baghchal.game_engine.search``) over generated legal moves. It is
pure Python with no Django/Channels/Redis dependencies.
"""

from .bot import DEFAULT_DIFFICULTY, DIFFICULTIES, choose_bot_move

__all__ = [
    "choose_bot_move",
    "DIFFICULTIES",
    "DEFAULT_DIFFICULTY",
]