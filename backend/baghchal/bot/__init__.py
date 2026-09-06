"""
Bot package.

The bot is a server-side player that chooses moves with the game engine's
search (``baghchal.game_engine.search``) over generated legal moves. It is
pure Python with no Django/Channels/Redis dependencies.
"""

from .bot import DEFAULT_DIFFICULTY, DIFFICULTIES, choose_bot_move

# Server-side opponent identity used in the player map and history.
BOT_USERNAME = "🤖 Bot"

# Artificial delay before the bot replies, so the human sees the board
# settle ("bot is thinking") instead of an instant answer.
BOT_REPLY_DELAY_MS = 500.0

__all__ = [
    "choose_bot_move",
    "DIFFICULTIES",
    "DEFAULT_DIFFICULTY",
    "BOT_USERNAME",
    "BOT_REPLY_DELAY_MS",
]