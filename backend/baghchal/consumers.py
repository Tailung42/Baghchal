from channels.generic.websocket import WebsocketConsumer
import json
from asgiref.sync import async_to_sync
from urllib.parse import parse_qs

from .core.gameState import (
    get_game,
    set_game,
    delete_game,
    get_all_games,
    game_exists,
)
from .core.utils import get_initial_game_state, update_game_state, cleanup_game_states
import random
import uuid

GAME_ID_LENGTH = 8


class GameStatus:
    WAITING = "waiting"
    ONGOING = "ongoing"
    OVER = "over"


class Mode:
    CREATE = "create"
    JOIN = "join"
    QUICK = "quick"


class GameConsumer(WebsocketConsumer):
    def connect(self):
        # store completed game and remove abandoned ones
        cleanup_game_states()

        # get connection paameters for game
        query = parse_qs(self.scope["query_string"].decode())
        self.game_id = query.get("game_id", [None])[0]
        self.mode = query.get("mode", [None])[0]
        self.play_as = query.get("play_as", [None])[0]
        self.username = query.get("username", [None])[0]

        try:
            self.handle_connection_attempt()

        except Exception as e:
            message = f"Error connecting:{e}"
            print(message)
            self.close_with_error(message)

        try:
            self.handle_player_join()
            
        except Exception as e:
            message = f"Error joining player: {e}"
            print(message)
            self.close_with_error(message)
            return

    def receive(self, text_data):
        try:
            message = (json.loads(text_data))["message"]
            if not hasattr(self, "room_group_name"):
                print("Error: No room group name set")
                return

            # remove user from game if exit game received
            if message["type"] == "exitGame":
                print(f"{self.username} exited the game")
                gamestate = get_game(self.room_group_name)
                if gamestate:
                    for role, player in gamestate["player"].items():
                        if player == self.username:
                            gamestate["player"][role] = ""
                    set_game(self.room_group_name, gamestate)

            # TODO: inform other player that opponent has left the game

            # apply the new move
            elif message["type"] == "newMove":
                move = message["move"]
                new_game_state = update_game_state(self.room_group_name, move)

                # send error message for invaid move
                if not new_game_state:
                    self.send(
                        text_data=json.dumps(
                            {"message": {"type": "error", "error": "Invalid move"}}
                        )
                    )
                    return

                # Broadcast updated state to all players in the game
                event = {"type": "send_game_state", "game_state": new_game_state}
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name, event
                )

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error processing message: {e}")
            self.send(
                text_data=json.dumps(
                    {"message": {"type": "error", "error": "Invalid message format"}}
                )
            )

    def disconnect(self, close_code):
        print(f"WebSocket disconnected with code: {close_code}")

        # Leave room group
        if hasattr(self, "room_group_name"):
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name, self.channel_name
            )

    def handle_connection_attempt(self):

        print(
            f"Connection attempt - Mode: {self.mode}, Game ID: {self.game_id}, Play as: {self.play_as}"
        )

        # Validate connection parameters
        if not self.username:
            raise ValueError("Error: Username not  provided")
        if not self.mode:
            raise ValueError("Error: No mode specified")
        if self.mode != "quick" and not self.game_id:
            raise ValueError("Error: Invalid game ID for non-quick mode")

        self.accept()
        print("WebSocket connection accepted")

    def handle_player_join(self):

        if self.mode == Mode.CREATE:
            # Set room group name for create mode
            self.room_group_name = f"game_{self.game_id}"
            if game_exists(self.room_group_name):
                raise ValueError("Error: Game already exists")
            set_game(self.room_group_name, get_initial_game_state())
            print(f"Created new game: {self.room_group_name}")

        elif self.mode == Mode.JOIN:
            self.room_group_name = f"game_{self.game_id}"
            game_state = get_game(self.room_group_name)

            if not game_state:
                raise ValueError("No Game available for joining")

            # if status is ongoing and user is a player in it, REJOIN
            if game_state["status"] == GameStatus.ONGOING:
                for k, v in game_state.get("player").items():
                    if v == self.username:
                        self.play_as = k
                        break
                else:
                    # if User not part of the game
                    raise ValueError("Can not rejoin, user not part of game")
            print(f"Joining existing game: {self.room_group_name}")

        elif self.mode == Mode.QUICK:
            # get a list of games whose status is waiting
            all_games = get_all_games()
            waiting_games = [
                (game_id, game_state)
                for game_id, game_state in all_games.items()
                if game_state.get("status") == GameStatus.WAITING
            ]

            if waiting_games:
                self.room_group_name = random.choice(waiting_games)[0]
                print(f"Joining waiting game: {self.room_group_name}")
            else:
                # Create new game for quick mode
                new_game_id = str(uuid.uuid4())[:GAME_ID_LENGTH]
                self.room_group_name = f"game_{new_game_id}"
                set_game(self.room_group_name, get_initial_game_state())
                print(f"Created new quick game: {self.room_group_name}")

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        self.send_initial_game_state()

    def send_initial_game_state(self):
        # Send initial game state to the connected player
        try:
            initial_state = get_game(self.room_group_name)
            if not initial_state:
                raise ValueError("Game state not found")
                
            # add game_id of the game inside itself
            initial_state["game_id"] = self.room_group_name

            # Handle player assignment (for all modes except REJOIN which already set play_as)
            if self.play_as:
                # CREATE mode or REJOIN mode - role already specified
                initial_state["player"][self.play_as] = self.username
            else:
                # JOIN or QUICK mode - assign to first available slot
                for role, player in initial_state["player"].items():
                    if not player:
                        self.play_as = role
                        initial_state["player"][role] = self.username
                        break

            # Update status to ongoing if both players are now connected
            if (
                all(initial_state["player"].values())
                and initial_state["status"] == GameStatus.WAITING
            ):
                initial_state["status"] = GameStatus.ONGOING

            # Save updated state back to Redis
            set_game(self.room_group_name, initial_state)

            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    "type": "send_game_state",
                    "game_state": initial_state,
                },
            )
            print(
                f"Sent initial game state to player: {self.username} as {self.play_as}"
            )

        except Exception as e:
            print(f"Error sending initial state: {e}")

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
        self.send(
            text_data=json.dumps({"message": {"type": "error", "error": message}})
        )
        self.close(4000)
