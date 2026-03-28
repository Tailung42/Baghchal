from channels.generic.websocket import AsyncWebsocketConsumer
import json
from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from .redis import (
    async_get_game,
    async_set_game,
    async_game_exists
)
# TODO: need to clean up game state at some point but when? 
from .game_engine import async_update_game_state, async_cleanup_game_states



class GameStatus:
    WAITING = "waiting"
    ONGOING = "ongoing"
    OVER = "over"

class AsyncGameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        WebSocket consumer for real-time game play only.
        Game creation, joining, and rejoining should be done via HTTP endpoints.
        This consumer only handles:
        - Real-time move updates
        - Game state broadcasts
        - Player disconnect handling
        """
        
        query = parse_qs(self.scope["query_string"].decode())
        self.game_id = query.get("game_id", [None])[0]

        user = self.scope["user"]
        if isinstance(user, AnonymousUser) or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.username = user.username

        try:
            await self.validate_connection()
        except Exception as e:
            await self.close_with_error(f"Connection error: {e}")
            return

        try:
            await self.setup_game_session()
        except Exception as e:
            await self.close_with_error(f"Error setting up game session: {e}")
            return

    async def validate_connection(self):
        await self.accept()
        
        if not self.username:
            raise ValueError("Username not provided")
        if not self.game_id:
            raise ValueError("Game ID not provided")

        self.room_group_name = f"game_{self.game_id}"

        if not await async_game_exists(self.room_group_name):
            raise ValueError(f"Game {self.game_id} does not exist")

        game_state = await async_get_game(self.room_group_name)
        if not game_state:
            raise ValueError("Failed to retrieve game state")

        user_is_player = any(
            player == self.username
            for player in game_state.get("player", {}).values()
        )
        if not user_is_player:
            raise ValueError(f"User {self.username} is not part of game {self.game_id}")


    async def setup_game_session(self):
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        game_state = await async_get_game(self.room_group_name)
        if not game_state:
            raise ValueError("Game state not found")

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "send_game_state", "game_state": game_state},
        )

    async def receive(self, text_data):
        try:
            message = json.loads(text_data).get("message")
            if not message:
                raise ValueError("Invalid message format")

            message_type = message.get("type")

            if message_type == "exitGame":
                await self.handle_exit_game()
            elif message_type == "newMove":
                await self.handle_new_move(message.get("move"))

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            await self.send(text_data=json.dumps(
                {"message": {"type": "error", "error": "Invalid message format"}}
            ))

    async def handle_exit_game(self):
        game_state = await async_get_game(self.room_group_name)
        if game_state:
            for role, player in game_state.get("player", {}).items():
                if player == self.username:
                    game_state["player"][role] = ""
                    break
            await async_set_game(self.room_group_name, game_state)
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "send_game_state", "game_state": game_state},
            )

    async def handle_new_move(self, move):
        if not move:
            await self.send(text_data=json.dumps(
                {"message": {"type": "error", "error": "Invalid move"}}
            ))
            return

        new_game_state = await async_update_game_state( self.room_group_name, move)

        if not new_game_state:
            await self.send(text_data=json.dumps(
                {"message": {"type": "error", "error": "Invalid move"}}
            ))
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "send_game_state", "game_state": new_game_state},
        )

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def send_game_state(self, event):
        try:
            await self.send(text_data=json.dumps(
                {"message": {"type": "update", "game_state": event["game_state"]}}
            ))
        except Exception as e:
            print(f"Error sending game state: {e}")

    async def close_with_error(self, message):
        await self.send(text_data=json.dumps(
            {"message": {"type": "error", "error": message}}
        ))
        await self.close(4000)
        