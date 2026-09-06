import asyncio

from adrf.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .persistence import views as persistence_views
from .game_engine import GAME_ID_LENGTH


@api_view(["POST"])
@permission_classes([IsAuthenticated])
async def create_game(request):
    """Create a new game and initialize it in Redis"""
    try:
        username = request.user.username
        if not username:
            return Response({"error": "Username required"}, status=400)

        game_id = await persistence_views.create_game(
            username,
            game_id_override=request.data.get("game_id"),
            player_role=request.data.get("player_role", "tiger"),
            game_id_length=GAME_ID_LENGTH,
        )
        return Response({"game_id": game_id}, status=201)

    except ValueError as e:
        return Response({"error": str(e)}, status=400)

    except Exception as e:
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

        joined_id = await persistence_views.join_game(game_id, username)
        return Response({"game_id": joined_id}, status=200)

    except ValueError as e:
        code = 400
        if str(e) == "Game not found":
            code = 404
        elif str(e) in {"Cannot join a game twice", "Game is full, no available roles"}:
            code = 400
        return Response({"error": str(e)}, status=code)
    except Exception as e:
        return Response({"error": f"Failed to join game: {str(e)}"}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
async def rejoin_game(request):
    """Rejoin a game the user was already playing"""
    try:
        username = request.user.username
        game_id = request.data.get("game_id")

        if not game_id or not username:
            return Response({"error": "Game ID and username required"}, status=400)

        await persistence_views.validate_rejoin(game_id, username)
        return Response({"game_id": game_id}, status=200)

    except ValueError:
        return Response({"error": "User is not part of this game"}, status=403)
    except Exception as e:
        return Response({"error": f"Failed to rejoin game: {str(e)}"}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
async def quick_match(request):
    """Find or create a game for quick match"""
    try:
        username = request.user.username
        game_id, created = await persistence_views.quick_match_split(username, game_id_length=GAME_ID_LENGTH)
        status_code = 201 if created else 200
        return Response({"game_id": game_id}, status=status_code)

    except Exception as e:
        return Response({"error": f"Failed to find quick match: {str(e)}"}, status=500)