"""
Module-level gateway instance.

This keeps the first integration small. It is not meant to stay global forever;
later work should scope sessions properly and add lifecycle, cleanup, and
multi-instance considerations.
"""

from .game_gateway import GameGateway

game_gateway = GameGateway()


def configure_gateway(
    *,
    game_store=None,
    game_set=None,
    game_delete=None,
) -> GameGateway:
    """
    Replace the module-level gateway with one wired to a specific persistence
    layer. This is optional for now, but it makes multi-instance or test
    setups easier without mutating module globals in ad-hoc ways.
    """
    global game_gateway
    game_gateway = GameGateway(
        game_store=game_store,
        game_set=game_set,
        game_delete=game_delete,
    )
    return game_gateway
