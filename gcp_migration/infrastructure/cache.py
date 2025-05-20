"""
Caching infrastructure for the GCP Migration toolkit.

This module provides a multi-tiered caching system with support for memory,
distributed, and persistent caches. It implements optimized cache patterns
with adaptive TTL management and intelligent prefetching.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import wraps
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
    cast,
    overload,
)

from gcp_migration.domain.exceptions_fixed import (
    CacheError,
    DataConsistencyError,
    MigrationError,
    safe_async_operation,
)
from gcp_migration.domain.protocols import ICacheProvider
from gcp_migration.infrastructure.batch import BatchProcessor, create_batch_processor

# Configure logging
logger = logging.getLogger(__name__)

# Type variables for generic caching
K = TypeVar("K")  # Key type
V = TypeVar("V")  # Value type
F = TypeVar("F", bound=Callable[..., Any])  # Function type


class CacheTier(Enum):
    """Cache tier levels for the caching system."""

    MEMORY = auto()  # In-memory cache (fastest, limited size)
    SHARED = auto()  # Shared cache (Redis/Memcached)
    PERSISTENT = auto()  # Persistent cache (Firestore/Datastore)


@dataclass
class CacheEntry(Generic[V]):
    """
    An entry in the cache with metadata.

    This class stores a cached value along with metadata about its
    lifecycle and access patterns.
    """

    value: V
    created_at: float = field(default_factory=time.monotonic)
    last_accessed_at: float = field(default_factory=time.monotonic)
    access_count: int = 0
    ttl: Optional[float] = None

    def is_expired(self) -> bool:
        """
        Check if the entry has expired.

        Returns:
            True if the entry has expired, False otherwise
        """
        if self.ttl is None:
            return False
        return time.monotonic() - self.created_at > self.ttl

    def update_access(self) -> None:
        """Update the last accessed time and access count."""
        self.last_accessed_at = time.monotonic()
        self.access_count += 1

    @property
    def age(self) -> float:
        """Get the age of the entry in seconds."""
        return time.monotonic() - self.created_at

    @property
    def time_to_expire(self) -> Optional[float]:
        """
        Get the time until expiration in seconds.

        Returns:
            Time until expiration or None if no TTL
        """
        if self.ttl is None:
            return None
        return max(0.0, self.ttl - self.age)


class CacheMetrics:
    """
    Performance metrics for the caching system.

    This class tracks detailed metrics about cache operations for
    performance monitoring and optimization.
    """

    def __init__(self):
        """Initialize cache metrics."""
        self.hits = 0
        self.misses = 0
        self.expired_hits = 0
        self.writes = 0
        self.deletes = 0
        self.clear_count = 0
        self.evictions = 0
        self.errors = 0

        self.hit_times: List[float] = []
        self.miss_times: List[float] = []
        self.write_times: List[float] = []

        self.created_at = time.monotonic()
        self.last_hit_at = 0.0
        self.last_miss_at = 0.0
        self.last_write_at = 0.0

    def record_hit(self, duration: float) -> None:
        """
        Record a cache hit.

        Args:
            duration: Operation duration in seconds
        """
        self.hits += 1
        self.last_hit_at = time.monotonic()
        self.hit_times.append(duration)
        if len(self.hit_times) > 100:
            self.hit_times.pop(0)

    def record_miss(self, duration: float) -> None:
        """
        Record a cache miss.

        Args:
            duration: Operation duration in seconds
        """
        self.misses += 1
        self.last_miss_at = time.monotonic()
        self.miss_times.append(duration)
        if len(self.miss_times) > 100:
            self.miss_times.pop(0)

    def record_expired_hit(self) -> None:
        """Record a hit on an expired entry."""
        self.expired_hits += 1

    def record_write(self, duration: float) -> None:
        """
        Record a cache write.

        Args:
            duration: Operation duration in seconds
        """
        self.writes += 1
        self.last_write_at = time.monotonic()
        self.write_times.append(duration)
        if len(self.write_times) > 100:
            self.write_times.pop(0)

    def record_delete(self) -> None:
        """Record a cache delete."""
        self.deletes += 1

    def record_clear(self) -> None:
        """Record a cache clear."""
        self.clear_count += 1

    def record_eviction(self) -> None:
        """Record a cache eviction."""
        self.evictions += 1

    def record_error(self) -> None:
        """Record a cache error."""
        self.errors += 1

    def get_hit_rate(self) -> float:
        """
        Get the cache hit rate as a percentage.

        Returns:
            Hit rate (0-100) or 0 if no requests
        """
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return (self.hits / total) * 100.0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get a dictionary of all metrics.

        Returns:
            Dictionary of metric names to values
        """
        total_ops = self.hits + self.misses + self.writes + self.deletes

        avg_hit_time = (
            sum(self.hit_times) / len(self.hit_times) if self.hit_times else 0.0
        )
        avg_miss_time = (
            sum(self.miss_times) / len(self.miss_times) if self.miss_times else 0.0
        )
        avg_write_time = (
            sum(self.write_times) / len(self.write_times) if self.write_times else 0.0
        )

        return {
            "hits": self.hits,
            "misses": self.misses,
            "expired_hits": self.expired_hits,
            "writes": self.writes,
            "deletes": self.deletes,
            "clear_count": self.clear_count,
            "evictions": self.evictions,
            "errors": self.errors,
            "total_operations": total_ops,
            "hit_rate": self.get_hit_rate(),
            "avg_hit_time_ms": avg_hit_time * 1000,
            "avg_miss_time_ms": avg_miss_time * 1000,
            "avg_write_time_ms": avg_write_time * 1000,
            "uptime": time.monotonic() - self.created_at,
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self.hits = 0
        self.misses = 0
        self.expired_hits = 0
        self.writes = 0
        self.deletes = 0
        self.clear_count = 0
        self.evictions = 0
        self.errors = 0

        self.hit_times = []
        self.miss_times = []
        self.write_times = []

        self.created_at = time.monotonic()
        self.last_hit_at = 0.0
        self.last_miss_at = 0.0
        self.last_write_at = 0.0


class CacheBase(Generic[K, V], ICacheProvider[K, V], ABC):
    """
    Base class for cache implementations.

    This abstract class provides common functionality and metrics tracking
    for all cache implementations.
    """

    def __init__(self, name: str, tier: CacheTier, default_ttl: Optional[float] = None):
        """
        Initialize a cache.

        Args:
            name: Name of the cache for identification
            tier: Cache tier level
            default_ttl: Default time-to-live in seconds
        """
        self.name = name
        self.tier = tier
        self.default_ttl = default_ttl
        self._metrics = CacheMetrics()
        self._maintenance_task: Optional[asyncio.Task] = None
        self._stopping = False

    @abstractmethod
    async def get(self, key: K) -> Optional[V]:
        """
        Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            The cached value or None if not found
        """
        pass

    @abstractmethod
    async def set(self, key: K, value: V, ttl_seconds: Optional[float] = None) -> None:
        """
        Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Optional time-to-live in seconds
        """
        pass

    @abstractmethod
    async def delete(self, key: K) -> bool:
        """
        Delete a value from the cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all values from the cache."""
        pass

    @abstractmethod
    async def get_many(self, keys: List[K]) -> Dict[K, V]:
        """
        Get multiple values from the cache.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary mapping keys to values (only for keys found)
        """
        pass

    @abstractmethod
    async def set_many(
        self, items: Dict[K, V], ttl_seconds: Optional[float] = None
    ) -> None:
        """
        Set multiple values in the cache.

        Args:
            items: Dictionary mapping keys to values
            ttl_seconds: Optional time-to-live in seconds
        """
        pass

    @property
    def metrics(self) -> CacheMetrics:
        """Get cache metrics."""
        return self._metrics

    async def start_maintenance(self, interval: float = 60.0) -> None:
        """
        Start the cache maintenance task.

        Args:
            interval: Maintenance interval in seconds
        """
        if self._maintenance_task is not None:
            return

        self._stopping = False
        self._maintenance_task = asyncio.create_task(self._maintenance_loop(interval))
        logger.debug(f"Started maintenance for cache: {self.name}")

    async def stop_maintenance(self) -> None:
        """Stop the cache maintenance task."""
        self._stopping = True

        if self._maintenance_task is not None:
            try:
                self._maintenance_task.cancel()
                await self._maintenance_task
            except asyncio.CancelledError:
                pass

            self._maintenance_task = None
            logger.debug(f"Stopped maintenance for cache: {self.name}")

    async def _maintenance_loop(self, interval: float) -> None:
        """
        Maintenance loop for the cache.

        Args:
            interval: Maintenance interval in seconds
        """
        while not self._stopping:
            try:
                await asyncio.sleep(interval)
                await self._perform_maintenance()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache maintenance for {self.name}: {e}")
                await asyncio.sleep(5.0)  # Shorter interval on error

    async def _perform_maintenance(self) -> None:
        """
        Perform cache maintenance tasks.

        This method should be overridden by subclasses to implement
        cache-specific maintenance tasks.
        """
        pass


class MemoryCache(CacheBase[K, V]):
    """
    In-memory cache implementation.

    This cache provides a high-performance in-memory cache with LRU eviction
    and automatic expiration.
    """

    def __init__(
        self, name: str, max_size: int = 1000, default_ttl: Optional[float] = None
    ):
        """
        Initialize an in-memory cache.

        Args:
            name: Name of the cache for identification
            max_size: Maximum number of items to store
            default_ttl: Default time-to-live in seconds
        """
        super().__init__(name, CacheTier.MEMORY, default_ttl)
        self.max_size = max_size
        self._cache: Dict[K, CacheEntry[V]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: K) -> Optional[V]:
        """
        Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            The cached value or None if not found
        """
        start_time = time.monotonic()

        try:
            async with self._lock:
                entry = self._cache.get(key)

                if entry is None:
                    self._metrics.record_miss(time.monotonic() - start_time)
                    return None

                if entry.is_expired():
                    # Remove expired entry
                    del self._cache[key]
                    self._metrics.record_expired_hit()
                    self._metrics.record_miss(time.monotonic() - start_time)
                    return None

                # Update access metadata
                entry.update_access()
                self._metrics.record_hit(time.monotonic() - start_time)
                return entry.value

        except Exception as e:
            self._metrics.record_error()
            logger.error(f"Error getting from cache {self.name}: {e}")
            return None

    async def set(self, key: K, value: V, ttl_seconds: Optional[float] = None) -> None:
        """
        Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Optional time-to-live in seconds
        """
        start_time = time.monotonic()

        try:
            async with self._lock:
                # Check if we need to evict
                if len(self._cache) >= self.max_size and key not in self._cache:
                    await self._evict_one()

                # Create new entry
                ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
                entry = CacheEntry(value=value, ttl=ttl)
                self._cache[key] = entry
                self._metrics.record_write(time.monotonic() - start_time)

        except Exception as e:
            self._metrics.record_error()
            logger.error(f"Error setting in cache {self.name}: {e}")

    async def delete(self, key: K) -> bool:
        """
        Delete a value from the cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        try:
            async with self._lock:
                if key in self._cache:
                    del self._cache[key]
                    self._metrics.record_delete()
                    return True
                return False

        except Exception as e:
            self._metrics.record_error()
            logger.error(f"Error deleting from cache {self.name}: {e}")
            return False

    async def clear(self) -> None:
        """Clear all values from the cache."""
        try:
            async with self._lock:
                self._cache.clear()
                self._metrics.record_clear()

        except Exception as e:
            self._metrics.record_error()
            logger.error(f"Error clearing cache {self.name}: {e}")

    async def get_many(self, keys: List[K]) -> Dict[K, V]:
        """
        Get multiple values from the cache.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary mapping keys to values (only for keys found)
        """
        start_time = time.monotonic()
        result: Dict[K, V] = {}
        hit_count = 0
        miss_count = 0

        try:
            async with self._lock:
                for key in keys:
                    entry = self._cache.get(key)

                    if entry is None:
                        miss_count += 1
                        continue

                    if entry.is_expired():
                        # Remove expired entry
                        del self._cache[key]
                        self._metrics.record_expired_hit()
                        miss_count += 1
                        continue

                    # Update access metadata
                    entry.update_access()
                    result[key] = entry.value
                    hit_count += 1

            # Record metrics
            duration = time.monotonic() - start_time
            if hit_count > 0:
                self._metrics.record_hit(duration / hit_count)
            if miss_count > 0:
                self._metrics.record_miss(duration / miss_count)

            return result

        except Exception as e:
            self._metrics.record_error()
            logger.error(f"Error getting many from cache {self.name}: {e}")
            return {}

    async def set_many(
        self, items: Dict[K, V], ttl_seconds: Optional[float] = None
    ) -> None:
        """
        Set multiple values in the cache.

        Args:
            items: Dictionary mapping keys to values
            ttl_seconds: Optional time-to-live in seconds
        """
        if not items:
            return

        start_time = time.monotonic()

        try:
            async with self._lock:
                # Check if we need to evict
                new_keys = set(items.keys()) - set(self._cache.keys())
                evict_count = len(self._cache) + len(new_keys) - self.max_size

                if evict_count > 0:
                    await self._evict_many(evict_count)

                # Create new entries
                ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl

                for key, value in items.items():
                    entry = CacheEntry(value=value, ttl=ttl)
                    self._cache[key] = entry

                self._metrics.record_write((time.monotonic() - start_time) / len(items))

        except Exception as e:
            self._metrics.record_error()
            logger.error(f"Error setting many in cache {self.name}: {e}")

    async def _evict_one(self) -> None:
        """Evict a single entry from the cache based on LRU policy."""
        if not self._cache:
            return

        # Find the least recently used key
        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].last_accessed_at)

        del self._cache[lru_key]
        self._metrics.record_eviction()

    async def _evict_many(self, count: int) -> None:
        """
        Evict multiple entries from the cache based on LRU policy.

        Args:
            count: Number of entries to evict
        """
        if not self._cache or count <= 0:
            return

        # Sort keys by last accessed time
        keys = sorted(self._cache.keys(), key=lambda k: self._cache[k].last_accessed_at)

        # Evict the least recently used
        for key in keys[:count]:
            del self._cache[key]
            self._metrics.record_eviction()

    async def _perform_maintenance(self) -> None:
        """Perform cache maintenance by removing expired entries."""
        async with self._lock:
            # Find expired keys
            expired_keys = [
                key for key, entry in self._cache.items() if entry.is_expired()
            ]

            # Remove expired entries
            for key in expired_keys:
                del self._cache[key]
                self._metrics.record_eviction()

            if expired_keys:
                logger.debug(
                    f"Removed {len(expired_keys)} expired entries from cache {self.name}"
                )


class MultiLevelCache(CacheBase[K, V]):
    """
    Multi-level cache implementation.

    This cache combines multiple cache levels with a hierarchical access
    pattern to optimize performance and resource usage.
    """

    def __init__(
        self,
        name: str,
        caches: List[CacheBase[K, V]],
        write_through: bool = True,
        default_ttl: Optional[float] = None,
    ):
        """
        Initialize a multi-level cache.

        Args:
            name: Name of the cache for identification
            caches: List of caches in order of precedence (fastest first)
            write_through: Whether to write through to all caches
            default_ttl: Default time-to-live in seconds
        """
        super().__init__(name, CacheTier.MEMORY, default_ttl)
        self.caches = caches
        self.write_through = write_through

    async def get(self, key: K) -> Optional[V]:
        """
        Get a value from the cache hierarchy.

        This method checks each cache level in order of precedence and
        fills lower levels when a value is found in a higher level.

        Args:
            key: Cache key

        Returns:
            The cached value or None if not found
        """
        start_time = time.monotonic()

        try:
            # Check each cache level
            for i, cache in enumerate(self.caches):
                value = await cache.get(key)

                if value is not None:
                    # Found in this cache level
                    self._metrics.record_hit(time.monotonic() - start_time)

                    # Fill lower cache levels
                    if i > 0:
                        fill_tasks = []
                        for j in range(i):
                            fill_tasks.append(
                                self.caches[j].set(key, value, self.default_ttl)
                            )

                        if fill_tasks:
                            await asyncio.gather(*fill_tasks, return_exceptions=True)

                    return value

            # Not found in any cache
            self._metrics.record_miss(time.monotonic() - start_time)
            return None

        except Exception as e:
            self._metrics.record_error()
            logger.error(f"Error getting from cache {self.name}: {e}")
            return None

    async def set(self, key: K, value: V, ttl_seconds: Optional[float] = None) -> None:
        """
        Set a value in the cache hierarchy.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Optional time-to-live in seconds
        """
        start_time = time.monotonic()
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl

        try:
            if self.write_through:
                # Write to all cache levels
                set_tasks = []
                for cache in self.caches:
                    set_tasks.append(cache.set(key, value, ttl))

                await asyncio.gather(*set_tasks, return_exceptions=True)
            else:
                # Write only to the first cache level
                await self.caches[0].set(key, value, ttl)

            self._metrics.record_write(time.monotonic() - start_time)

        except Exception as e:
            self._metrics.record_error()
            logger.error(f"Error setting in cache {self.name}: {e}")

    async def delete(self, key: K) -> bool:
        """
        Delete a value from all cache levels.

        Args:
            key: Cache key

        Returns:
            True if deleted from any level, False if not found
        """
        try:
            # Delete from all cache levels
            delete_tasks = []
            for cache in self.caches:
                delete_tasks.append(cache.delete(key))

            results = await asyncio.gather(*delete_tasks, return_exceptions=True)

            # Check if deleted from any level
            deleted = any(isinstance(r, bool) and r for r in results)
            if deleted:
                self._metrics.record_delete()

            return deleted

        except Exception as e:
            self._metrics.record_error()
            logger.error(f"Error deleting from cache {self.name}: {e}")
            return False

    async def clear(self) -> None:
        """Clear all cache levels."""
        try:
            # Clear all cache levels
            clear_tasks = []
            for cache in self.caches:
                clear_tasks.append(cache.clear())

            await asyncio.gather(*clear_tasks, return_exceptions=True)
            self._metrics.record_clear()

        except Exception as e:
            self._metrics.record_error()
            logger.error(f"Error clearing cache {self.name}: {e}")

    async def get_many(self, keys: List[K]) -> Dict[K, V]:
        """
        Get multiple values from the cache hierarchy.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary mapping keys to values (only for keys found)
        """
        if not keys:
            return {}

        start_time = time.monotonic()

        try:
            result: Dict[K, V] = {}
            remaining_keys = set(keys)

            # Check each cache level
            for i, cache in enumerate(self.caches):
                if not remaining_keys:
                    break

                # Get values from this cache level
                level_keys = list(remaining_keys)
                level_values = await cache.get_many(level_keys)

                # Process results
                for key, value in level_values.items():
                    result[key] = value
                    remaining_keys.remove(key)

                # Fill lower cache levels
                if i > 0 and level_values:
                    fill_tasks = []
                    for j in range(i):
                        fill_tasks.append(
                            self.caches[j].set_many(level_values, self.default_ttl)
                        )

                    if fill_tasks:
                        await asyncio.gather(*fill_tasks, return_exceptions=True)

            # Record metrics
            duration = time.monotonic() - start_time
            hit_count = len(result)
            miss_count = len(keys) - hit_count

            if hit_count > 0:
                self._metrics.record_hit(duration / hit_count)
            if miss_count > 0:
                self._metrics.record_miss(duration / miss_count)

            return result

        except Exception as e:
            self._metrics.record_error()
            logger.error(f"Error getting many from cache {self.name}: {e}")
            return {}

    async def set_many(
        self, items: Dict[K, V], ttl_seconds: Optional[float] = None
    ) -> None:
        """
        Set multiple values in the cache hierarchy.

        Args:
            items: Dictionary mapping keys to values
            ttl_seconds: Optional time-to-live in seconds
        """
        if not items:
            return

        start_time = time.monotonic()
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl

        try:
            if self.write_through:
                # Write to all cache levels
                set_tasks = []
                for cache in self.caches:
                    set_tasks.append(cache.set_many(items, ttl))

                await asyncio.gather(*set_tasks, return_exceptions=True)
            else:
                # Write only to the first cache level
                await self.caches[0].set_many(items, ttl)

            self._metrics.record_write((time.monotonic() - start_time) / len(items))

        except Exception as e:
            self._metrics.record_error()
            logger.error(f"Error setting many in cache {self.name}: {e}")

    async def _perform_maintenance(self) -> None:
        """Perform maintenance on all cache levels."""
        maintenance_tasks = []
        for cache in self.caches:
            maintenance_tasks.append(cache._perform_maintenance())

        await asyncio.gather(*maintenance_tasks, return_exceptions=True)


class CacheRegistry:
    """
    Registry for caches.

    This class provides a central registry for managing caches
    across the application.
    """

    _instance = None
    _caches: Dict[str, CacheBase] = {}

    def __new__(cls):
        """Implement singleton pattern for the registry."""
        if cls._instance is None:
            cls._instance = super(CacheRegistry, cls).__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, cache: CacheBase) -> None:
        """
        Register a cache.

        Args:
            cache: The cache to register
        """
        cls._caches[cache.name] = cache
        logger.debug(f"Registered cache: {cache.name}")

    @classmethod
    def get(cls, name: str) -> Optional[CacheBase]:
        """
        Get a cache by name.

        Args:
            name: The name of the cache

        Returns:
            The cache or None if not found
        """
        return cls._caches.get(name)

    @classmethod
    async def start_all_maintenance(cls) -> None:
        """Start maintenance for all registered caches."""
        for cache in cls._caches.values():
            await cache.start_maintenance()
        logger.info(f"Started maintenance for {len(cls._caches)} caches")

    @classmethod
    async def stop_all_maintenance(cls) -> None:
        """Stop maintenance for all registered caches."""
        for cache in cls._caches.values():
            await cache.stop_maintenance()
        logger.info(f"Stopped maintenance for {len(cls._caches)} caches")

    @classmethod
    def get_all_metrics(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get metrics for all caches.

        Returns:
            Dictionary mapping cache names to their metrics
        """
        return {name: cache.metrics.get_stats() for name, cache in cls._caches.items()}

    @classmethod
    async def clear_all(cls) -> None:
        """Clear all registered caches."""
        clear_tasks = []
        for cache in cls._caches.values():
            clear_tasks.append(cache.clear())

        await asyncio.gather(*clear_tasks, return_exceptions=True)
        logger.info(f"Cleared {len(cls._caches)} caches")


def cached(
    key_fn: Optional[Callable[..., str]] = None,
    ttl_seconds: Optional[float] = None,
    cache_name: str = "default",
):
    """
    Decorator for caching function results.

    This decorator caches function results in the specified cache
    based on the function arguments.

    Args:
        key_fn: Optional function to generate cache keys
        ttl_seconds: Optional time-to-live in seconds
        cache_name: Name of the cache to use

    Returns:
        Decorated function

    Example:
        ```python
        @cached(ttl_seconds=60)
        async def get_user(user_id: str) -> Dict[str, Any]:
            # Implementation...
        ```
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get the cache
            cache = CacheRegistry.get(cache_name)
            if cache is None:
                # No cache, just call the function
                return await func(*args, **kwargs)

            # Generate the cache key
            if key_fn is not None:
                key = key_fn(*args, **kwargs)
            else:
                # Default key generation based on arguments
                arg_key = str(args) if args else ""
                kwarg_key = str(sorted(kwargs.items())) if kwargs else ""
                key = f"{func.__module__}.{func.__qualname__}:{arg_key}:{kwarg_key}"

            # Try to get from cache
            result = await cache.get(key)
            if result is not None:
                return result

            # Not in cache, call the function
            result = await func(*args, **kwargs)

            # Cache the result
            if result is not None:
                await cache.set(key, result, ttl_seconds)

            return result

        return wrapper

    return decorator


async def create_memory_cache(
    name: str,
    max_size: int = 1000,
    default_ttl: Optional[float] = None,
    auto_start_maintenance: bool = True,
) -> MemoryCache:
    """
    Create and register a memory cache.

    Args:
        name: Name of the cache
        max_size: Maximum cache size
        default_ttl: Default time-to-live in seconds
        auto_start_maintenance: Whether to start maintenance immediately

    Returns:
        The created cache
    """
    cache = MemoryCache(name=name, max_size=max_size, default_ttl=default_ttl)

    CacheRegistry.register(cache)

    if auto_start_maintenance:
        await cache.start_maintenance()

    return cache


async def create_multi_level_cache(
    name: str,
    caches: List[CacheBase],
    write_through: bool = True,
    default_ttl: Optional[float] = None,
    auto_start_maintenance: bool = True,
) -> MultiLevelCache:
    """
    Create and register a multi-level cache.

    Args:
        name: Name of the cache
        caches: List of caches in order of precedence
        write_through: Whether to write through to all levels
        default_ttl: Default time-to-live in seconds
        auto_start_maintenance: Whether to start maintenance immediately

    Returns:
        The created cache
    """
    cache = MultiLevelCache(
        name=name, caches=caches, write_through=write_through, default_ttl=default_ttl
    )

    CacheRegistry.register(cache)

    if auto_start_maintenance:
        await cache.start_maintenance()

    return cache
