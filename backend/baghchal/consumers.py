from channels.generic.websocket import WebsocketConsumer
import json
from asgiref.sync import async_to_sync
from urllib.parse import parse_qs

from .redis import (
    get_game,
    set_game,
    delete_game,
    get_all_games,
    game_exists,
)
from .utils import get_initial_game_state, update_game_state, cleanup_game_states


class GameStatus:
    WAITING = "waiting"
    ONGOING = "ongoing"
    OVER = "over"


class GameConsumer(WebsocketConsumer):
    """
    WebSocket consumer for real-time game play only.
    Game creation, joining, and rejoining should be done via HTTP endpoints.
    This consumer only handles:
    - Real-time move updates
    - Game state broadcasts
    - Player disconnect handling
    """

    def connect(self):
        # Store completed games and remove abandoned ones
        cleanup_game_states()

        # Get connection parameters (game must already exist from HTTP endpoint)
        query = parse_qs(self.scope["query_string"].decode())
        self.game_id = query.get("game_id", [None])[0]
        self.username = query.get("username", [None])[0]

        try:
            self.validate_connection()
        except Exception as e:
            message = f"Connection error: {e}"
            print(message)
            self.close_with_error(message)
            return

        try:
            self.setup_game_session()
        except Exception as e:
            message = f"Error setting up game session: {e}"
            print(message)
            self.close_with_error(message)
            return

    def validate_connection(self):
        """Validate connection parameters"""
        if not self.username:
            raise ValueError("Username not provided")
        if not self.game_id:
            raise ValueError("Game ID not provided")

        self.room_group_name = f"game_{self.game_id}"

        # Verify game exists (should be created via HTTP endpoint)
        if not game_exists(self.room_group_name):
            raise ValueError(f"Game {self.game_id} does not exist")

        game_state = get_game(self.room_group_name)
        if not game_state:
            raise ValueError("Failed to retrieve game state")

        # Verify user is a player in this game
        user_is_player = False
        for role, player in game_state.get("player", {}).items():
            if player == self.username:
                user_is_player = True
                break

        if not user_is_player:
            raise ValueError(f"User {self.username} is not part of game {self.game_id}")

        self.accept()
        print(f"WebSocket connection accepted for {self.username} in game {self.game_id}")

    def setup_game_session(self):
        """Set up game session and send initial state"""
        # Join room group for broadcasting
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        # Get current game state and send to player
        game_state = get_game(self.room_group_name)
        if not game_state:
            raise ValueError("Game state not found")

        print(f"Sending initial game state to {self.username}")
        self.send(
            text_data=json.dumps(
                {"message": {"type": "update", "game_state": game_state}}
            )
        )

    def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            message = json.loads(text_data).get("message")
            if not message:
                raise ValueError("Invalid message format")

            message_type = message.get("type")

            # Handle game exit
            if message_type == "exitGame":
                self.handle_exit_game()

            # Handle new moves
            elif message_type == "newMove":
                self.handle_new_move(message.get("move"))

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error processing message: {e}")
            self.send(
                text_data=json.dumps(
                    {"message": {"type": "error", "error": "Invalid message format"}}
                )
            )

    def handle_exit_game(self):
        """Handle player exiting the game"""
        print(f"{self.username} exited the game")
        game_state = get_game(self.room_group_name)
        if game_state:
            # Clear player slot
            for role, player in game_state.get("player", {}).items():
                if player == self.username:
                    game_state["player"][role] = ""
                    break
            set_game(self.room_group_name, game_state)
            # Broadcast updated state
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {"type": "send_game_state", "game_state": game_state},
            )

    def handle_new_move(self, move):
        """Handle and validate new move"""
        if not move:
            self.send(
                text_data=json.dumps(
                    {"message": {"type": "error", "error": "Invalid move"}}
                )
            )
            return

        new_game_state = update_game_state(self.room_group_name, move)

        if not new_game_state:
            self.send(
                text_data=json.dumps(
                    {"message": {"type": "error", "error": "Invalid move"}}
                )
            )
            return

        # Broadcast updated state to all players in the game
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {"type": "send_game_state", "game_state": new_game_state},
        )

    def disconnect(self, close_code):
        """Handle WebSocket disconnect"""
        print(f"Player {self.username} disconnected from {self.game_id} (code: {close_code})")

        # Leave room group
        if hasattr(self, "room_group_name"):
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name, self.channel_name
            )

    def send_game_state(self, event):
        """Handle group message to send game state update"""
        try:
            self.send(
                text_data=json.dumps(
                    {"message": {"type": "update", "game_state": event["game_state"]}}
                )
            )
        except Exception as e:
            print(f"Error sending game state: {e}")

    def close_with_error(self, message):
        """Close connection with error message"""
        self.send(
            text_data=json.dumps({"message": {"type": "error", "error": message}})
        )
        self.close(4000)
