"""
Game state management using Redis for persistence and multi-instance support.
"""
import json
import os

import redis.asyncio as aioredis

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# Initialize Redis client
async_redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)

# Key prefix for all game states
GAME_KEY_PREFIX = "game:"


async def async_get_game(game_id: str) -> dict | None:
    """
    Retrieve a game state from Redis.
    
    Args:
        game_id: The game ID to retrieve
        
    Returns:
        Dictionary with game state, or None if not found
    """

    try:
        key = f"{GAME_KEY_PREFIX}{game_id}"
        data = await async_redis_client.get(key)
        return json.loads(data) if data else None
    except Exception as e:
        print(f"Error getting game: {e}")
        return None

async def async_set_game(game_id: str, game_state: dict) -> bool:
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
        await async_redis_client.set(key, json.dumps(game_state))
        return True
    except Exception as e:
        print(f"Error setting game: {e}")
        return False
    
async def async_delete_game(game_id: str) -> bool:
    """
    Delete a game state from Redis.
    
    Args:
        game_id: The game ID to delete
        
    Returns:
        True if key was deleted, False if key didn't exist
    """
    try:
        key = f"{GAME_KEY_PREFIX}{game_id}"
        result = await async_redis_client.delete(key)
        return result > 0
    except Exception as e:
        print(f"Error deleting game: {e}")
        return False
    
async def async_get_all_games() -> dict[str, dict]:
    """
    Retrieve all game states from Redis.
    
    Returns:
        Dictionary mapping game IDs to their states
    """
    try:
        pattern = f"{GAME_KEY_PREFIX}*"
        keys = await async_redis_client.keys(pattern)
        games = {}
        for key in keys:
            game_id = key.replace(GAME_KEY_PREFIX, "")
            data = await async_redis_client.get(key)
            if data:
                games[game_id] = json.loads(data)
        return games
    except Exception as e:
        print(f"Error retrieving all games from Redis: {e}")
        return {}

async def async_game_exists(game_id: str) -> bool:
    """
    Check if a game exists in Redis.
    
    Args:
        game_id: The game ID to check
        
    Returns:
        True if game exists, False otherwise
    """
    try:
        key = f"{GAME_KEY_PREFIX}{game_id}"
        return await async_redis_client.exists(key) > 0
    except Exception as e:
        print(f"Error checking game exists: {e}")
        return False