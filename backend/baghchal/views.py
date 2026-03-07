from django.shortcuts import render, HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import uuid
import random
from .redis import (
    get_game,
    set_game,
    get_all_games,
    game_exists,
)
from .utils import get_initial_game_state

GAME_ID_LENGTH = 8
GAME_STATUS_WAITING = "waiting"
GAME_STATUS_ONGOING = "ongoing"


def index(request):
    print("hello world")
    return HttpResponse("<h1> hello, world <h1/>")


# Game endpoints
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_game(request):
    """Create a new game and initialize it in Redis"""
    try:
        username = request.user.username
        game_id = request.data.get("game_id")

        player_role = request.data.get("player_role", "tiger")

        if not game_id:
            # raise ValueError("GameId is required to create a game.")
            game_id = str(uuid.uuid4())[:GAME_ID_LENGTH]
            
        if not username:
            return Response({"error": "Username required"}, status=400)

        room_group_name = f"game_{game_id}"

        # Check if game already exists
        if game_exists(room_group_name):
            return Response({"error": "Game already exists"}, status=400)

        # Initialize game state
        initial_state = get_initial_game_state()
        initial_state["player"][player_role] = username
        initial_state["game_id"] = room_group_name
        set_game(room_group_name, initial_state)

        print(f"Created new game: {room_group_name}")
        return Response(
            {
                "game_id": game_id,
            },
            status=201,
        )
    except Exception as e:
        print(f"Error creating game: {e}")
        return Response({"error": f"Failed to create game: {str(e)}"}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def join_game(request):
    """Join an existing game"""
    try:
        username = request.user.username
        game_id = request.data.get("game_id")

        if not game_id or not username:
            return Response({"error": "Game ID and username required"}, status=400)

        room_group_name = f"game_{game_id}"
        game_state = get_game(room_group_name)

        if not game_state:
            return Response({"error": "Game not found"}, status=404)

        # Ensure game_id is set in game_state
        game_state["game_id"] = room_group_name

        # check if the user is already in the game 
        if game_state["status"] == GAME_STATUS_ONGOING:
            return Response(
                {"error": "Cannot join ongoing game as new player"},
                status=400,
            )
        
        # Check if user is already in the game
        for role, player in game_state.get("player", {}).items():
            if player == username:
                return Response(
                    {"error": "Cannot join a game twice"},
                    status=400,)
            

        # Find available role
        available_role = None
        for role, player in game_state.get("player", {}).items():
            if not player:
                available_role = role
                break

        if not available_role:
            return Response(
                {"error": "Game is full, no available roles"},
                status=400,
            )

        # Assign user to available role
        game_state["player"][available_role] = username

        # Update game status if both players are now assigned
        if all(game_state["player"].values()):
            game_state["status"] = GAME_STATUS_ONGOING

        set_game(room_group_name, game_state)

        # # broadcast to any connected clients that state changed (player joined)
        # try:
        #     from asgiref.sync import async_to_sync
        #     from channels.layers import get_channel_layer

        #     channel_layer = get_channel_layer()
        #     async_to_sync(channel_layer.group_send)(
        #         room_group_name,
        #         {"type": "send_game_state", "game_state": game_state},
        #     )
        # except Exception as exc:
        #     # logging failure but don't break the response
        #     print(f"Failed to broadcast join update: {exc}")

        print(f"User {username} joined game {room_group_name} as {available_role}")
        return Response(
            {
                "game_id": game_id,
            },
            status=200,
        )
    except Exception as e:
        print(f"Error joining game: {e}")
        return Response({"error": f"Failed to join game: {str(e)}"}, status=500)



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def rejoin_game(request):



    """Rejoin a game the user was already playing"""
    try:
        game_id = request.data.get("game_id")
        username = request.user.username

        if not game_id or not username:
            return Response({"error": "Game ID and username required"}, status=400)

        room_group_name = f"game_{game_id}"
        game_state = get_game(room_group_name)

        if not game_state:
            return Response({"error": "Game not found"}, status=404)

        # Ensure game_id is set in game_state
        game_state["game_id"] = room_group_name

        # Check if user is a player in this game
        user_role = None
        for role, player in game_state.get("player", {}).items():
            if player == username:
                user_role = role
                break

        if not user_role:
            return Response(
                {"error": "User is not part of this game"},
                status=403,
            )

        print(f"User {username} rejoined game {room_group_name} as {user_role}")
        return Response(
            {
                "game_id": game_id,
            },
            status=200,
        )
    except Exception as e:
        print(f"Error rejoining game: {e}")
        return Response({"error": f"Failed to rejoin game: {str(e)}"}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def quick_match(request):
    """Find or create a game for quick match"""
    try:
        username = request.user.username
        # Get list of waiting games
        all_games = get_all_games()
        waiting_games = [
            (game_id, game_state)
            for game_id, game_state in all_games.items()
            if game_state.get("status") == GAME_STATUS_WAITING
        ]

        if waiting_games:
            # Join an existing waiting game
            game_id, game_state = random.choice(waiting_games)
            game_id = game_id.replace("game_", "")

            # Find available role
            available_role = None
            for role, player in game_state.get("player", {}).items():
                if not player:
                    available_role = role
                    break

            if available_role:
                game_state["player"][available_role] = username
                # Update status to ongoing if both players assigned
                if all(game_state["player"].values()):
                    game_state["status"] = GAME_STATUS_ONGOING
                # Ensure game_id is set
                game_state["game_id"] = f"game_{game_id}"
                set_game(f"game_{game_id}", game_state)

                # broadcast update to existing connection(s)
                try:
                    from asgiref.sync import async_to_sync
                    from channels.layers import get_channel_layer

                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        f"game_{game_id}",
                        {"type": "send_game_state", "game_state": game_state},
                    )
                except Exception as exc:
                    print(f"Failed to broadcast quick-match join: {exc}")

                print(f"User {username} joined quick match game {game_id}")
                return Response(
                    {
                        "game_id": game_id,
                    },
                    status=200,
                )

        # No waiting games, create a new one
        game_id = str(uuid.uuid4())[:GAME_ID_LENGTH]
        room_group_name = f"game_{game_id}"
        initial_state = get_initial_game_state()
        initial_state["player"]["tiger"] = username
        initial_state["game_id"] = room_group_name
        set_game(room_group_name, initial_state)

        print(f"Created new quick match game: {room_group_name}")
        return Response(
            {
                "game_id": game_id,
                "play_as": "tiger",
                "game_state": initial_state,
            },
            status=201,
        )
    except Exception as e:
        print(f"Error finding quick match: {e}")
        return Response({"error": f"Failed to find quick match: {str(e)}"}, status=500)