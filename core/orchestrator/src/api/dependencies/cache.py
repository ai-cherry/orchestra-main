"""
Redis cache dependency for AI Orchestration System.

This module provides the dependency injection function for the Redis cache,
supporting connection to Redis in local development or Cloud Memorystore
in cloud environments.
"""

import logging
from functools import lru_cache
from typing import Any, Dict, Optional

from fastapi import Depends

from core.orchestrator.src.config.settings import Settings, get_settings

# Try to import RedisCache - fall back gracefully if not available
try:
    from packages.shared.src.cache.redis_client import RedisCache

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

    # Create a dummy RedisCache class for type hints
    class RedisCache:
        """Dummy RedisCache class for when the real one is not available."""

        async def initialize(self) -> bool:
            return False

        async def close(self) -> None:
            pass

        async def get(self, key: str) -> Optional[Any]:
            return None

        async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
            return False

        async def delete(self, key: str) -> bool:
            return False

        async def exists(self, key: str) -> bool:
            return False

        async def health_check(self) -> Dict[str, Any]:
            return {"status": "unavailable"}


# Configure logging
logger = logging.getLogger(__name__)

# Global Redis cache instance
_redis_cache = None


@lru_cache()
def create_redis_cache(settings: Settings = Depends(get_settings)) -> RedisCache:
    """
    Create a Redis cache instance based on settings.

    Args:
        settings: Application settings

    Returns:
        A RedisCache instance (not initialized)
    """
    if not REDIS_AVAILABLE:
        logger.warning("Redis client package not available, caching will be disabled")
        return RedisCache()

    # Create Redis client with settings
    return RedisCache(settings=settings)


async def get_redis_cache(settings: Settings = Depends(get_settings)) -> RedisCache:
    """
    Get an initialized Redis cache instance.

    This dependency function creates and initializes a Redis cache
    if one doesn't exist, or returns the existing one.

    Args:
        settings: Application settings

    Returns:
        An initialized RedisCache
    """
    global _redis_cache

    # Create the cache if it doesn't exist
    if _redis_cache is None:
        _redis_cache = create_redis_cache(settings)

        if settings.REDIS_CACHE_ENABLED and settings.REDIS_HOST:
            try:
                # Initialize the cache
                await _redis_cache.initialize()
                logger.info("Redis cache initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Redis cache: {e}")

    return _redis_cache


async def initialize_redis_cache(settings: Settings = None) -> None:
    """
    Initialize the Redis cache during application startup.

    Args:
        settings: Optional application settings
    """
    global _redis_cache

    if settings is None:
        settings = get_settings()

    # Create the cache if it doesn't exist
    if _redis_cache is None:
        _redis_cache = create_redis_cache(settings)

    # Initialize only if Redis caching is enabled
    if settings.REDIS_CACHE_ENABLED and settings.REDIS_HOST:
        logger.info("Initializing Redis cache")
        await _redis_cache.initialize()

        # Perform a health check
        health_info = await _redis_cache.health_check()
        logger.info(f"Redis cache health check: {health_info}")
    else:
        logger.info("Redis caching is disabled or not configured")


async def close_redis_cache() -> None:
    """
    Close the Redis cache during application shutdown.
    """
    global _redis_cache

    if _redis_cache is not None:
        logger.info("Closing Redis cache")
        await _redis_cache.close()
        _redis_cache = None
