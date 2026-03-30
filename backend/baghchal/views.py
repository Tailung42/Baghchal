from django.shortcuts import render, HttpResponse
from rest_framework.decorators import permission_classes
from adrf.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import uuid
import random
import asyncio
from .redis import (
    async_get_game,
    async_set_game,
    async_get_all_games,
    async_game_exists,
)
from .game_engine import get_initial_game_state, GameStatus, GAME_ID_LENGTH



# Game endpoints
@api_view(["POST"])
@permission_classes([IsAuthenticated])
async def create_game(request):
    """Create a new game and initialize it in Redis"""
    try:
        username = request.user.username
        game_id = request.data.get("game_id")

        player_role = request.data.get("player_role", "tiger")

        if not game_id:
            game_id = str(uuid.uuid4())[:GAME_ID_LENGTH]

        if not username:
            return Response({"error": "Username required"}, status=400)

        room_group_name = f"game_{game_id}"

        if await async_game_exists(room_group_name):
            return Response({"error": "Game already exists"}, status=400)

        initial_state = get_initial_game_state()
        initial_state["player"][player_role] = username
        initial_state["game_id"] = room_group_name
        asyncio.create_task(async_set_game(room_group_name, initial_state))

        print(f"Created new game: {room_group_name}")
        return Response({"game_id": game_id}, status=201)

    except Exception as e:
        print(f"Error creating game: {e}")
        return Response({"error": f"Failed to create game: {str(e)}"}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
async def join_game(request):
    """Join an existing game"""
    try:
        username = request.user.username
        game_id = request.data.get("game_id")

        if not game_id or not username:
            return Response({"error": "Game ID and username required"}, status=400)

        room_group_name = f"game_{game_id}"
        game_state = await async_get_game(room_group_name)

        if not game_state:
            return Response({"error": "Game not found"}, status=404)

        game_state["game_id"] = room_group_name

        if game_state["status"] == GameStatus.ONGOING:
            return Response(
                {"error": "Cannot join ongoing game as new player"}, status=400
            )

        for role, player in game_state.get("player", {}).items():
            if player == username:
                return Response({"error": "Cannot join a game twice"}, status=400)

        available_role = None
        for role, player in game_state.get("player", {}).items():
            if not player:
                available_role = role
                break

        if not available_role:
            return Response({"error": "Game is full, no available roles"}, status=400)

        game_state["player"][available_role] = username

        if all(game_state["player"].values()):
            game_state["status"] = GameStatus.ONGOING

        asyncio.create_task(async_set_game(room_group_name, game_state))

        print(f"User {username} joined game {room_group_name} as {available_role}")
        return Response({"game_id": game_id}, status=200)

    except Exception as e:
        print(f"Error joining game: {e}")
        return Response({"error": f"Failed to join game: {str(e)}"}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
async def rejoin_game(request):
    """Rejoin a game the user was already playing"""
    try:
        game_id = request.data.get("game_id")
        username = request.user.username

        if not game_id or not username:
            return Response({"error": "Game ID and username required"}, status=400)

        room_group_name = f"game_{game_id}"
        game_state = await async_get_game(room_group_name)

        if not game_state:
            return Response({"error": "Game not found"}, status=404)

        game_state["game_id"] = room_group_name

        user_role = None
        for role, player in game_state.get("player", {}).items():
            if player == username:
                user_role = role
                break

        if not user_role:
            return Response({"error": "User is not part of this game"}, status=403)

        print(f"User {username} rejoined game {room_group_name} as {user_role}")
        return Response({"game_id": game_id}, status=200)

    except Exception as e:
        print(f"Error rejoining game: {e}")
        return Response({"error": f"Failed to rejoin game: {str(e)}"}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
async def quick_match(request):
    """Find or create a game for quick match"""
    try:
        username = request.user.username
        all_games = await async_get_all_games()
        waiting_games = [
            (game_id, game_state)
            for game_id, game_state in all_games.items()
            if game_state.get("status") == GameStatus.WAITING
        ]

        if waiting_games:
            game_id, game_state = random.choice(waiting_games)
            game_id = game_id.replace("game_", "")

            available_role = None
            for role, player in game_state.get("player", {}).items():
                if not player:
                    available_role = role
                    break

            if available_role:
                game_state["player"][available_role] = username
                if all(game_state["player"].values()):
                    game_state["status"] = GameStatus.ONGOING
                game_state["game_id"] = f"game_{game_id}"
                asyncio.create_task(async_set_game(f"game_{game_id}", game_state))

                print(f"User {username} joined quick match game {game_id}")
                return Response({"game_id": game_id}, status=200)

        # No waiting games, create a new one
        game_id = str(uuid.uuid4())[:GAME_ID_LENGTH]
        room_group_name = f"game_{game_id}"
        initial_state = get_initial_game_state()
        initial_state["player"]["tiger"] = username
        initial_state["game_id"] = room_group_name
        asyncio.create_task(async_set_game(room_group_name, initial_state))

        print(f"Created new quick match game: {room_group_name}")
        return Response({"game_id": game_id}, status=201)

    except Exception as e:
        print(f"Error finding quick match: {e}")
        return Response({"error": f"Failed to find quick match: {str(e)}"}, status=500)