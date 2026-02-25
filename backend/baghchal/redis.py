"""
Game state management using Redis for persistence and multi-instance support.
"""
import json
import redis
import os

# Initialize Redis client
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_DB = int(os.environ.get('REDIS_DB', 0))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True
)

# Key prefix for all game states
GAME_KEY_PREFIX = "game:"


def get_game(game_id: str) -> dict | None:
    """
    Retrieve a game state from Redis.
    
    Args:
        game_id: The game ID to retrieve
        
    Returns:
        Dictionary with game state, or None if not found
    """
    try:
        key = f"{GAME_KEY_PREFIX}{game_id}"
        data = redis_client.get(key)
        if data is not None:
            return json.loads(data)
        return None
    except Exception as e:
        print(f"Error getting game state from Redis: {e}")
        return None


def set_game(game_id: str, game_state: dict, ttl: int | None = None) -> bool:
    """
    Store a game state in Redis.
    
    Args:
        game_id: The game ID
        game_state: The game state dictionary
        ttl: Optional TTL in seconds for the key
        
    Returns:
        True if successful, False otherwise
    """
    try:
        key = f"{GAME_KEY_PREFIX}{game_id}"
        redis_client.set(key, json.dumps(game_state))
        if ttl:
            redis_client.expire(key, ttl)
        return True
    except Exception as e:
        print(f"Error setting game state in Redis: {e}")
        return False


def delete_game(game_id: str) -> bool:
    """
    Delete a game state from Redis.
    
    Args:
        game_id: The game ID to delete
        
    Returns:
        True if key was deleted, False if key didn't exist
    """
    try:
        key = f"{GAME_KEY_PREFIX}{game_id}"
        result = redis_client.delete(key)
        return result > 0
    except Exception as e:
        print(f"Error deleting game state from Redis: {e}")
        return False


def get_all_games() -> dict[str, dict]:
    """
    Retrieve all game states from Redis.
    
    Returns:
        Dictionary mapping game IDs to their states
    """
    try:
        pattern = f"{GAME_KEY_PREFIX}*"
        keys = redis_client.keys(pattern)
        games = {}
        for key in keys:
            game_id = key.replace(GAME_KEY_PREFIX, "")
            data = redis_client.get(key)
            if data:
                games[game_id] = json.loads(data)
        return games
    except Exception as e:
        print(f"Error retrieving all games from Redis: {e}")
        return {}


def game_exists(game_id: str) -> bool:
    """
    Check if a game exists in Redis.
    
    Args:
        game_id: The game ID to check
        
    Returns:
        True if game exists, False otherwise
    """
    try:
        key = f"{GAME_KEY_PREFIX}{game_id}"
        return redis_client.exists(key) > 0
    except Exception as e:
        print(f"Error checking if game exists: {e}")
        return False
