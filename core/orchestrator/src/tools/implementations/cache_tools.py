"""
"""
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=True,
)

async def cache_get(key: str) -> Optional[str]:
    """Get value from cache."""
        raise Exception(f"Cache get error: {str(e)}")

async def cache_set(key: str, value: str, ttl: int = 3600) -> bool:
    """Set value in cache with TTL."""
        raise Exception(f"Cache set error: {str(e)}")

async def cache_delete(key: str) -> bool:
    """Delete key from cache."""
        raise Exception(f"Cache delete error: {str(e)}")
