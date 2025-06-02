"""Multi-layer caching system for Factory AI integration.

This module implements a high-performance caching system with three layers:
- L1: In-memory cache (LRU)
- L2: Redis distributed cache
- L3: PostgreSQL persistent cache

The system is designed to achieve an 85% cache hit rate target.
"""

import asyncio
import json
import logging
import time
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple, Union

import aioredis
import asyncpg
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CacheEntry(BaseModel):
    """Model for cache entries."""

    key: str
    value: Any
    created_at: float = Field(default_factory=time.time)
    expires_at: Optional[float] = None
    access_count: int = 0
    last_accessed: float = Field(default_factory=time.time)


class CacheMetrics(BaseModel):
    """Cache performance metrics."""

    l1_hits: int = 0
    l1_misses: int = 0
    l2_hits: int = 0
    l2_misses: int = 0
    l3_hits: int = 0
    l3_misses: int = 0
    total_requests: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate overall cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        total_hits = self.l1_hits + self.l2_hits + self.l3_hits
        return (total_hits / self.total_requests) * 100

    @property
    def l1_hit_rate(self) -> float:
        """Calculate L1 cache hit rate."""
        l1_requests = self.l1_hits + self.l1_misses
        if l1_requests == 0:
            return 0.0
        return (self.l1_hits / l1_requests) * 100


class L1Cache:
    """Ultra-fast in-memory cache with LRU eviction.

    This cache provides the fastest access times but limited capacity.
    Uses OrderedDict for O(1) access and LRU eviction.
    """

    def __init__(self, max_size: int = 1000, ttl: int = 300):
        """Initialize L1 cache.

        Args:
            max_size: Maximum number of entries
            ttl: Default time-to-live in seconds
        """
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.max_size = max_size
        self.default_ttl = ttl
        self.hits = 0
        self.misses = 0
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from L1 cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        async with self._lock:
            if key not in self.cache:
                self.misses += 1
                return None

            entry = self.cache[key]

            # Check expiration
            if entry.expires_at and time.time() > entry.expires_at:
                del self.cache[key]
                self.misses += 1
                return None

            # Update access info and move to end (most recently used)
            entry.access_count += 1
            entry.last_accessed = time.time()
            self.cache.move_to_end(key)

            self.hits += 1
            return entry.value

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in L1 cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL override in seconds
        """
        async with self._lock:
            # Evict oldest if at capacity
            if len(self.cache) >= self.max_size and key not in self.cache:
                self.cache.popitem(last=False)

            # Create or update entry
            expires_at = None
            if ttl is not None or self.default_ttl:
                expires_at = time.time() + (ttl or self.default_ttl)

            entry = CacheEntry(key=key, value=value, expires_at=expires_at)

            self.cache[key] = entry
            self.cache.move_to_end(key)

    async def delete(self, key: str) -> bool:
        """Delete entry from L1 cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    async def clear(self) -> None:
        """Clear all entries from L1 cache."""
        async with self._lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    def get_metrics(self) -> Dict[str, Any]:
        """Get L1 cache metrics."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": (self.hits / max(self.hits + self.misses, 1)) * 100,
        }


class L2Cache:
    """Distributed Redis cache for shared state.

    This cache provides fast access with distributed capabilities,
    allowing multiple instances to share cached data.
    """

    def __init__(self, redis_url: str, ttl: int = 3600):
        """Initialize L2 cache.

        Args:
            redis_url: Redis connection URL
            ttl: Default time-to-live in seconds
        """
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.default_ttl = ttl
        self.hits = 0
        self.misses = 0

    async def connect(self) -> None:
        """Connect to Redis."""
        self.redis = await aioredis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from L2 cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self.redis:
            return None

        try:
            value = await self.redis.get(f"factory:cache:{key}")
            if value:
                self.hits += 1
                # Deserialize JSON
                return json.loads(value)
            else:
                self.misses += 1
                return None
        except Exception as e:
            logger.error(f"L2 cache get error: {e}")
            self.misses += 1
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in L2 cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL override in seconds
        """
        if not self.redis:
            return

        try:
            # Serialize to JSON
            serialized = json.dumps(value)
            cache_key = f"factory:cache:{key}"

            if ttl is not None or self.default_ttl:
                await self.redis.setex(cache_key, ttl or self.default_ttl, serialized)
            else:
                await self.redis.set(cache_key, serialized)

        except Exception as e:
            logger.error(f"L2 cache set error: {e}")

    async def delete(self, key: str) -> bool:
        """Delete entry from L2 cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        if not self.redis:
            return False

        try:
            result = await self.redis.delete(f"factory:cache:{key}")
            return result > 0
        except Exception as e:
            logger.error(f"L2 cache delete error: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Clear entries matching pattern.

        Args:
            pattern: Redis key pattern

        Returns:
            Number of keys deleted
        """
        if not self.redis:
            return 0

        try:
            keys = []
            async for key in self.redis.scan_iter(match=f"factory:cache:{pattern}"):
                keys.append(key)

            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"L2 cache clear pattern error: {e}")
            return 0

    def get_metrics(self) -> Dict[str, Any]:
        """Get L2 cache metrics."""
        return {
            "connected": self.redis is not None,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": (self.hits / max(self.hits + self.misses, 1)) * 100,
        }


class L3Cache:
    """Persistent cache in PostgreSQL for long-term storage.

    This cache provides persistent storage with query capabilities,
    suitable for less frequently accessed but important data.
    """

    def __init__(self, db_pool: asyncpg.Pool, cleanup_interval: int = 86400):
        """Initialize L3 cache.

        Args:
            db_pool: AsyncPG connection pool
            cleanup_interval: Cleanup interval in seconds
        """
        self.db_pool = db_pool
        self.cleanup_interval = cleanup_interval
        self.hits = 0
        self.misses = 0
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start background cleanup task."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def get(self, key: str) -> Optional[Any]:
        """Get value from L3 cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    SELECT value, expires_at
                    FROM factory_cache_entries
                    WHERE key = $1
                    AND (expires_at IS NULL OR expires_at > NOW())
                """
                record = await conn.fetchrow(query, key)

                if record:
                    # Update access info
                    update_query = """
                        UPDATE factory_cache_entries
                        SET access_count = access_count + 1,
                            last_accessed = NOW()
                        WHERE key = $1
                    """
                    await conn.execute(update_query, key)

                    self.hits += 1
                    return record["value"]
                else:
                    self.misses += 1
                    return None

        except Exception as e:
            logger.error(f"L3 cache get error: {e}")
            self.misses += 1
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in L3 cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL in seconds
        """
        try:
            async with self.db_pool.acquire() as conn:
                expires_at = None
                if ttl:
                    expires_at = datetime.utcnow() + timedelta(seconds=ttl)

                query = """
                    INSERT INTO factory_cache_entries
                    (key, value, expires_at)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (key) DO UPDATE SET
                        value = $2,
                        expires_at = $3,
                        created_at = NOW(),
                        access_count = 0
                """
                await conn.execute(query, key, json.dumps(value), expires_at)

        except Exception as e:
            logger.error(f"L3 cache set error: {e}")

    async def delete(self, key: str) -> bool:
        """Delete entry from L3 cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        try:
            async with self.db_pool.acquire() as conn:
                query = "DELETE FROM factory_cache_entries WHERE key = $1"
                result = await conn.execute(query, key)
                return result.split()[-1] != "0"
        except Exception as e:
            logger.error(f"L3 cache delete error: {e}")
            return False

    async def cleanup_expired(self) -> int:
        """Clean up expired entries.

        Returns:
            Number of entries cleaned up
        """
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    DELETE FROM factory_cache_entries
                    WHERE expires_at IS NOT NULL AND expires_at < NOW()
                """
                result = await conn.execute(query)
                count = int(result.split()[-1])
                logger.info(f"Cleaned up {count} expired L3 cache entries")
                return count
        except Exception as e:
            logger.error(f"L3 cache cleanup error: {e}")
            return 0

    async def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get L3 cache metrics."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": (self.hits / max(self.hits + self.misses, 1)) * 100,
        }


class CacheManager:
    """Unified cache manager with multi-layer caching.

    Implements a write-through, read-through caching strategy:
    - Writes go to all layers
    - Reads check L1 → L2 → L3 → Source
    - Automatic cache warming for frequently accessed data
    """

    def __init__(
        self,
        l1_config: Dict[str, Any],
        l2_config: Dict[str, Any],
        l3_config: Dict[str, Any],
    ):
        """Initialize cache manager.

        Args:
            l1_config: L1 cache configuration
            l2_config: L2 cache configuration (must include redis_url)
            l3_config: L3 cache configuration (must include db_pool)
        """
        # Initialize cache layers
        self.l1 = L1Cache(max_size=l1_config.get("max_size", 1000), ttl=l1_config.get("ttl", 300))

        self.l2 = L2Cache(redis_url=l2_config["redis_url"], ttl=l2_config.get("ttl", 3600))

        self.l3 = L3Cache(db_pool=l3_config["db_pool"], cleanup_interval=l3_config.get("cleanup_interval", 86400))

        self.metrics = CacheMetrics()
        self._warm_cache_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Start cache manager and connect to backends."""
        await self.l2.connect()
        await self.l3.start()
        self._running = True
        self._warm_cache_task = asyncio.create_task(self._warm_cache_loop())
        logger.info("CacheManager started")

    async def stop(self) -> None:
        """Stop cache manager and cleanup."""
        self._running = False

        if self._warm_cache_task:
            self._warm_cache_task.cancel()
            try:
                await self._warm_cache_task
            except asyncio.CancelledError:
                pass

        await self.l2.disconnect()
        await self.l3.stop()
        logger.info("CacheManager stopped")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (read-through).

        Checks layers in order: L1 → L2 → L3

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        self.metrics.total_requests += 1

        # Check L1
        value = await self.l1.get(key)
        if value is not None:
            self.metrics.l1_hits += 1
            return value
        self.metrics.l1_misses += 1

        # Check L2
        value = await self.l2.get(key)
        if value is not None:
            self.metrics.l2_hits += 1
            # Populate L1
            await self.l1.set(key, value)
            return value
        self.metrics.l2_misses += 1

        # Check L3
        value = await self.l3.get(key)
        if value is not None:
            self.metrics.l3_hits += 1
            # Populate L1 and L2
            await self.l1.set(key, value)
            await self.l2.set(key, value)
            return value
        self.metrics.l3_misses += 1

        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache (write-through).

        Writes to all layers for consistency.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL in seconds
        """
        # Write to all layers concurrently
        await asyncio.gather(
            self.l1.set(key, value, ttl),
            self.l2.set(key, value, ttl),
            self.l3.set(key, value, ttl),
            return_exceptions=True,
        )

    async def delete(self, key: str) -> None:
        """Delete value from all cache layers.

        Args:
            key: Cache key
        """
        # Delete from all layers concurrently
        await asyncio.gather(self.l1.delete(key), self.l2.delete(key), self.l3.delete(key), return_exceptions=True)

    async def invalidate_pattern(self, pattern: str) -> None:
        """Invalidate cache entries matching pattern.

        Args:
            pattern: Pattern to match (e.g., "user:*")
        """
        # L1 doesn't support patterns, so clear all
        # In production, you might want to iterate and check
        await self.l1.clear()

        # L2 supports Redis patterns
        await self.l2.clear_pattern(pattern)

        # L3 would need custom implementation
        # For now, log a warning
        logger.warning(f"L3 pattern invalidation not implemented for: {pattern}")

    async def warm_cache(self, keys: list[str]) -> None:
        """Pre-populate cache with frequently accessed keys.

        Args:
            keys: List of keys to warm
        """
        for key in keys:
            # This will populate L1 and L2 from L3 if available
            await self.get(key)

    async def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive cache metrics.

        Returns:
            Dictionary containing metrics for all layers
        """
        return {
            "overall": {
                "total_requests": self.metrics.total_requests,
                "hit_rate": self.metrics.hit_rate,
                "l1_hit_rate": self.metrics.l1_hit_rate,
            },
            "l1": self.l1.get_metrics(),
            "l2": self.l2.get_metrics(),
            "l3": self.l3.get_metrics(),
            "target_hit_rate": 85.0,
            "meets_target": self.metrics.hit_rate >= 85.0,
        }

    async def _warm_cache_loop(self) -> None:
        """Background task to warm cache with frequently accessed data."""
        while self._running:
            try:
                # Wait before warming
                await asyncio.sleep(300)  # 5 minutes

                # Get frequently accessed keys from L3
                async with self.l3.db_pool.acquire() as conn:
                    query = """
                        SELECT key
                        FROM factory_cache_entries
                        WHERE access_count > 10
                        ORDER BY access_count DESC
                        LIMIT 100
                    """
                    records = await conn.fetch(query)

                    if records:
                        keys = [record["key"] for record in records]
                        await self.warm_cache(keys)
                        logger.info(f"Warmed cache with {len(keys)} frequently accessed keys")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache warming error: {e}")


# Factory function for easy initialization
async def create_cache_manager(config: Dict[str, Any]) -> CacheManager:
    """Create and initialize a cache manager.

    Args:
        config: Configuration dictionary with cache settings

    Returns:
        Initialized CacheManager instance

    Example:
        ```python
        config = {
            "l1": {"max_size": 1000, "ttl": 300},
            "l2": {"redis_url": "redis://localhost:6379", "ttl": 3600},
            "l3": {"db_pool": db_pool, "cleanup_interval": 86400}
        }
        cache_manager = await create_cache_manager(config)
        ```
    """
    manager = CacheManager(l1_config=config.get("l1", {}), l2_config=config["l2"], l3_config=config["l3"])
    await manager.start()
    return manager
