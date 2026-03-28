import threading
import asyncio
from datetime import datetime
from ..redis import async_get_game, async_set_game, async_get_all_games, async_delete_game
from .game_state import apply_move, check_game_over
from baghchal.models import Game
from core.models import User


async def async_update_game_state(room_name, move):
    game_state = await async_get_game(room_name)
    if not game_state:
        return None
    
    new_game_state = apply_move(game_state, move)
    if new_game_state is None:
        return None

    if check_game_over(new_game_state):
        asyncio.create_task(async_store_game(room_name, new_game_state))
        asyncio.create_task(async_delete_game(room_name))
    else:
        asyncio.create_task(async_set_game(room_name, new_game_state))

    return new_game_state


async def async_cleanup_game_states():
    games = await async_get_all_games()
    for game_id, game_state in games.items():
        if game_state.get("status") == "over":
            asyncio.create_task(async_store_game(game_id, game_state))
            asyncio.create_task(async_schedule_game_removal(game_id, 30))

        elif not any(game_state.get("player", {}).values()):
            asyncio.create_task(async_schedule_game_removal(game_id))

        elif game_state.get("status") == "ongoing":
            players = game_state.get("player", {})
            if not players.get("goat") or not players.get("tiger"):
                pass


async def async_schedule_game_removal(game_id, delay=0):
    def remove_game():
        print("Removing Game: ", game_id)
        asyncio.create_task(async_delete_game(game_id))

    timer = threading.Timer(delay, remove_game)
    timer.daemon = True
    timer.start()


async def async_store_game(game_id, game_state):
    print(f"stored game: {game_id}")

    winner_role = game_state["winner"]
    dead_goats = game_state["deadGoatCount"]
    
    goat_user = await asyncio.to_thread(get_user_by_username, game_state["player"]["goat"])
    tiger_user = await asyncio.to_thread(get_user_by_username, game_state["player"]["tiger"])

    game = Game(
        game_id=game_id,
        goat_player=goat_user,
        tiger_player=tiger_user,
        winner_role=winner_role,
        total_moves=len(game_state["history"]),
        goats_captured=dead_goats,
        created_at=datetime.now()
    )
    await asyncio.to_thread(game.save)


def get_user_by_username(username):
    try: 
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        raise ValueError(f"Unable to get the user with username: {username}")
