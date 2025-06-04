"""
"""
        """Dummy RedisCache class for when the real one is not available."""
            return {"status": "unavailable"}

# Configure logging
logger = logging.getLogger(__name__)

# Global Redis cache instance
_redis_cache = None

# @lru_cache()
def create_redis_cache(settings: Settings = Depends(get_settings)) -> RedisCache:
    """
    """
        logger.warning("Redis client package not available, caching will be disabled")
        return RedisCache()

    # Create Redis client with settings
    return RedisCache(settings=settings)

async def get_redis_cache(settings: Settings = Depends(get_settings)) -> RedisCache:
    """
    """
                logger.info("Redis cache initialized")
            except Exception:

                pass
                logger.error(f"Failed to initialize Redis cache: {e}")

    return _redis_cache

async def initialize_redis_cache(settings: Settings = None) -> None:
    """
    """
        logger.info("Initializing Redis cache")
        await _redis_cache.initialize()

        # Perform a health check
        health_info = await _redis_cache.health_check()
        logger.info(f"Redis cache health check: {health_info}")
    else:
        logger.info("Redis caching is disabled or not configured")

async def close_redis_cache() -> None:
    """
    """
        logger.info("Closing Redis cache")
        await _redis_cache.close()
        _redis_cache = None

class _DummyCache:
    """A simplistic in-memory stub to satisfy dependency injection."""
        return {"status": "unavailable", "enabled": False}

_dummy_cache = _DummyCache()

def get_redis_cache():
    """Return a dummy cache implementation for environments without Redis."""