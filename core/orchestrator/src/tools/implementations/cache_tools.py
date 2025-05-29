"""
Cache tool implementations using Redis/DragonflyDB
"""

import os
from typing import Optional

import redis

# Initialize Redis client
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=True,
)


async def cache_get(key: str) -> Optional[str]:
    """Get value from cache."""
    try:
        value = redis_client.get(key)
        return value
    except Exception as e:
        raise Exception(f"Cache get error: {str(e)}")


async def cache_set(key: str, value: str, ttl: int = 3600) -> bool:
    """Set value in cache with TTL."""
    try:
        if ttl > 0:
            redis_client.setex(key, ttl, value)
        else:
            redis_client.set(key, value)
        return True
    except Exception as e:
        raise Exception(f"Cache set error: {str(e)}")


async def cache_delete(key: str) -> bool:
    """Delete key from cache."""
    try:
        result = redis_client.delete(key)
        return result > 0
    except Exception as e:
        raise Exception(f"Cache delete error: {str(e)}")
