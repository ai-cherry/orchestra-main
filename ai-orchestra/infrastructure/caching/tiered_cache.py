"""
Tiered caching strategy for AI Orchestra.

This module provides a tiered caching implementation with in-memory L1 cache
and Redis L2 cache for improved performance and reduced latency.
"""

import hashlib
import json
import logging
import time
from functools import wraps
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
)

from ...core.config import get_settings
from ...utils.logging import log_error, log_event

# For type hints with generic cache value types
T = TypeVar("T")
V = TypeVar("V")

logger = logging.getLogger(__name__)


class CacheRecord(Generic[T]):
    """
    Record stored in cache with metadata.

    This class represents a cache record with value and metadata like
    creation time and access count for implementing advanced cache
    eviction policies.
    """

    def __init__(self, value: T, ttl_seconds: int = 0):
        """
        Initialize a cache record.

        Args:
            value: The cached value
            ttl_seconds: Time-to-live in seconds (0 for no expiration)
        """
        self.value = value
        self.created_at = time.time()
        self.last_accessed_at = self.created_at
        self.access_count = 0
        self.ttl_seconds = ttl_seconds

    def is_expired(self) -> bool:
        """
        Check if the record is expired.

        Returns:
            True if expired, False otherwise
        """
        if self.ttl_seconds <= 0:
            return False

        return time.time() - self.created_at > self.ttl_seconds

    def update_access_stats(self) -> None:
        """Update access statistics."""
        self.last_accessed_at = time.time()
        self.access_count += 1


class MemoryCache(Generic[T]):
    """
    In-memory cache implementation (L1 cache).

    This class provides a fast in-memory cache with support for different
    eviction policies and automatic cleanup of expired entries.
    """

    def __init__(
        self,
        max_size: int = 1000,
        cleanup_interval: int = 60,  # Cleanup interval in seconds
    ):
        """
        Initialize the memory cache.

        Args:
            max_size: Maximum number of items to store
            cleanup_interval: Interval for cleaning up expired items
        """
        self.max_size = max_size
        self.cleanup_interval = cleanup_interval
        self.data: Dict[str, CacheRecord[T]] = {}
        self.last_cleanup = time.time()

        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    async def get(self, key: str) -> Optional[T]:
        """
        Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            The cached value, or None if not found or expired
        """
        # Check if cleanup is needed
        self._maybe_cleanup()

        # Try to get the record
        record = self.data.get(key)

        # Return None if not found or expired
        if record is None or record.is_expired():
            if record is not None and record.is_expired():
                # Remove expired record
                del self.data[key]

            self.misses += 1
            return None

        # Update access stats and return value
        record.update_access_stats()
        self.hits += 1
        return record.value

    async def set(self, key: str, value: T, ttl_seconds: int = 0) -> None:
        """
        Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live in seconds (0 for no expiration)
        """
        # Check if we need to evict items
        if len(self.data) >= self.max_size and key not in self.data:
            self._evict()

        # Create and store the record
        record = CacheRecord(value, ttl_seconds)
        self.data[key] = record

    async def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        if key in self.data:
            del self.data[key]
            return True

        return False

    async def clear(self) -> None:
        """Clear all cached values."""
        self.data.clear()
        self.last_cleanup = time.time()

    def _maybe_cleanup(self) -> None:
        """Clean up expired items if needed."""
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup()
            self.last_cleanup = current_time

    def _cleanup(self) -> None:
        """Remove all expired items."""
        expired_keys = [key for key, record in self.data.items() if record.is_expired()]

        for key in expired_keys:
            del self.data[key]
            self.evictions += 1

    def _evict(self) -> None:
        """Evict items based on LRU policy."""
        if not self.data:
            return

        # Find the least recently used item
        lru_key = min(self.data.keys(), key=lambda k: self.data[k].last_accessed_at)

        # Remove it
        del self.data[lru_key]
        self.evictions += 1

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0

        return {
            "size": len(self.data),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "evictions": self.evictions,
        }


class RedisCache(Generic[T]):
    """
    Redis-based cache implementation (L2 cache).

    This class provides a distributed cache using Redis for sharing
    cache data across multiple instances and persisting between restarts.
    """

    def __init__(
        self,
        prefix: str = "cache:",
        serialize: Callable[[T], str] = None,
        deserialize: Callable[[str], T] = None,
        default_ttl: int = 300,  # 5 minutes
    ):
        """
        Initialize the Redis cache.

        Args:
            prefix: Key prefix for namespacing
            serialize: Function to serialize values (default: json.dumps)
            deserialize: Function to deserialize values (default: json.loads)
            default_ttl: Default TTL in seconds
        """
        self.prefix = prefix
        self.serialize = serialize or (lambda v: json.dumps(v))
        self.deserialize = deserialize or (lambda v: json.loads(v))
        self.default_ttl = default_ttl

        # Don't import here to avoid circular import
        # The actual Redis client will be fetched on demand
        self._redis_client = None

        # Statistics
        self.hits = 0
        self.misses = 0

    async def _get_redis(self):
        """Get the Redis client."""
        if self._redis_client is None:
            # Import here to avoid circular imports
            from ..caching.optimized_redis_pool import (
                PoolType,
                get_optimized_redis_client,
            )

            # Get a Redis client optimized for caching
            self._redis_client = await get_optimized_redis_client(pool_type=PoolType.CACHE)

        return self._redis_client

    def _get_full_key(self, key: str) -> str:
        """
        Get the full Redis key with prefix.

        Args:
            key: Cache key

        Returns:
            Full Redis key
        """
        return f"{self.prefix}{key}"

    async def get(self, key: str) -> Optional[T]:
        """
        Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            The cached value, or None if not found
        """
        redis_client = await self._get_redis()
        full_key = self._get_full_key(key)

        # Get the value from Redis
        value_str = await redis_client.get(full_key)

        if value_str is None:
            self.misses += 1
            return None

        # Deserialize and return
        try:
            value = self.deserialize(value_str)
            self.hits += 1
            return value
        except Exception as e:
            log_error(logger, "redis_cache_deserialize", e, {"key": key})
            self.misses += 1
            return None

    async def set(self, key: str, value: T, ttl_seconds: Optional[int] = None) -> bool:
        """
        Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live in seconds

        Returns:
            True if successful, False otherwise
        """
        redis_client = await self._get_redis()
        full_key = self._get_full_key(key)
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl

        # Serialize the value
        try:
            value_str = self.serialize(value)
        except Exception as e:
            log_error(logger, "redis_cache_serialize", e, {"key": key})
            return False

        # Set in Redis with TTL
        result = await redis_client.set(full_key, value_str, ex=ttl)
        return result

    async def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        redis_client = await self._get_redis()
        full_key = self._get_full_key(key)

        # Delete from Redis
        result = await redis_client.delete(full_key)
        return result > 0

    async def clear(self, pattern: str = "*") -> int:
        """
        Clear all cached values matching pattern.

        Args:
            pattern: Key pattern to match

        Returns:
            Number of keys deleted
        """
        redis_client = await self._get_redis()
        full_pattern = self._get_full_key(pattern)

        # Get all matching keys
        keys = await redis_client.keys(full_pattern)

        if not keys:
            return 0

        # Delete all matching keys
        return await redis_client.batch_delete(keys)

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        redis_client = await self._get_redis()
        pattern = self._get_full_key("*")

        # Count keys
        keys = await redis_client.keys(pattern)
        key_count = len(keys)

        # Get Redis metrics
        redis_metrics = await redis_client.get_metrics()

        # Calculate hit rate
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0

        return {
            "keys": key_count,
            "prefix": self.prefix,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "redis_metrics": redis_metrics,
        }


class TieredCache(Generic[T]):
    """
    Tiered cache implementation.

    This class provides a tiered caching strategy with memory cache (L1)
    and Redis cache (L2) for improved performance and reliability.
    """

    def __init__(
        self,
        prefix: str = "cache:",
        l1_max_size: int = 1000,
        l1_cleanup_interval: int = 60,
        l2_default_ttl: int = 300,
        serialize: Callable[[T], str] = None,
        deserialize: Callable[[str], T] = None,
        cache_warming_keys: Optional[List[str]] = None,
    ):
        """
        Initialize the tiered cache.

        Args:
            prefix: Key prefix for namespacing
            l1_max_size: Maximum L1 cache size
            l1_cleanup_interval: L1 cache cleanup interval
            l2_default_ttl: Default L2 cache TTL
            serialize: Function to serialize values
            deserialize: Function to deserialize values
            cache_warming_keys: Keys to warm up on initialization
        """
        self.l1_cache = MemoryCache[T](
            max_size=l1_max_size,
            cleanup_interval=l1_cleanup_interval,
        )

        self.l2_cache = RedisCache[T](
            prefix=prefix,
            serialize=serialize,
            deserialize=deserialize,
            default_ttl=l2_default_ttl,
        )

        self.cache_warming_keys = cache_warming_keys or []

        # Statistics
        self.l1_hits = 0
        self.l2_hits = 0
        self.misses = 0

    async def get(self, key: str) -> Optional[T]:
        """
        Get a value from the tiered cache.

        This method checks L1 first, then L2 if not found in L1.
        If found in L2 but not L1, it populates L1 for future requests.

        Args:
            key: Cache key

        Returns:
            The cached value, or None if not found
        """
        # Try L1 cache first
        value = await self.l1_cache.get(key)

        if value is not None:
            # L1 hit
            self.l1_hits += 1
            return value

        # Try L2 cache
        value = await self.l2_cache.get(key)

        if value is not None:
            # L2 hit - populate L1 for future requests
            await self.l1_cache.set(key, value)
            self.l2_hits += 1
            return value

        # Cache miss
        self.misses += 1
        return None

    async def set(
        self,
        key: str,
        value: T,
        l1_ttl_seconds: int = 0,
        l2_ttl_seconds: Optional[int] = None,
    ) -> None:
        """
        Set a value in the tiered cache.

        This method sets the value in both L1 and L2 caches.

        Args:
            key: Cache key
            value: Value to cache
            l1_ttl_seconds: L1 cache TTL in seconds
            l2_ttl_seconds: L2 cache TTL in seconds
        """
        # Set in L1 cache
        await self.l1_cache.set(key, value, ttl_seconds=l1_ttl_seconds)

        # Set in L2 cache
        await self.l2_cache.set(key, value, ttl_seconds=l2_ttl_seconds)

    async def delete(self, key: str) -> bool:
        """
        Delete a value from the tiered cache.

        This method deletes the value from both L1 and L2 caches.

        Args:
            key: Cache key

        Returns:
            True if deleted from either cache, False otherwise
        """
        # Delete from both caches
        l1_result = await self.l1_cache.delete(key)
        l2_result = await self.l2_cache.delete(key)

        # Return True if deleted from either cache
        return l1_result or l2_result

    async def clear(self) -> None:
        """Clear both caches."""
        await self.l1_cache.clear()
        await self.l2_cache.clear()

    async def warm_up(self, keys: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Warm up the L1 cache with values from L2.

        Args:
            keys: Keys to warm up (defaults to self.cache_warming_keys)

        Returns:
            Dictionary mapping keys to success status
        """
        keys_to_warm = keys or self.cache_warming_keys
        results: Dict[str, bool] = {}

        for key in keys_to_warm:
            # Get from L2 and populate L1
            value = await self.l2_cache.get(key)

            if value is not None:
                await self.l1_cache.set(key, value)
                results[key] = True
            else:
                results[key] = False

        return results

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        l1_stats = self.l1_cache.get_stats()
        l2_stats = await self.l2_cache.get_stats()

        # Calculate overall stats
        total_requests = self.l1_hits + self.l2_hits + self.misses
        hit_rate = (self.l1_hits + self.l2_hits) / total_requests if total_requests > 0 else 0
        l1_hit_rate = self.l1_hits / total_requests if total_requests > 0 else 0
        l2_hit_rate = self.l2_hits / total_requests if total_requests > 0 else 0

        return {
            "l1_cache": l1_stats,
            "l2_cache": l2_stats,
            "total_hits": self.l1_hits + self.l2_hits,
            "l1_hits": self.l1_hits,
            "l2_hits": self.l2_hits,
            "misses": self.misses,
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "l1_hit_rate": l1_hit_rate,
            "l2_hit_rate": l2_hit_rate,
        }


# Utility functions for caching


def generate_cache_key(prefix: str, args: tuple, kwargs: Dict[str, Any], namespace: Optional[str] = None) -> str:
    """
    Generate a cache key from function arguments.

    Args:
        prefix: Key prefix (usually function name)
        args: Positional arguments
        kwargs: Keyword arguments
        namespace: Optional namespace

    Returns:
        Cache key
    """
    # Create a string representation of args and kwargs
    args_str = json.dumps(args, sort_keys=True, default=str)
    kwargs_str = json.dumps(kwargs, sort_keys=True, default=str)

    # Create a hash of the arguments
    args_hash = hashlib.md5(f"{args_str}:{kwargs_str}".encode()).hexdigest()

    # Create the full key
    if namespace:
        return f"{namespace}:{prefix}:{args_hash}"
    else:
        return f"{prefix}:{args_hash}"


def cached(
    ttl_seconds: int = 300,
    l1_ttl_seconds: int = 60,
    namespace: Optional[str] = None,
    key_builder: Optional[Callable[..., str]] = None,
):
    """
    Decorator for caching function results.

    Args:
        ttl_seconds: Cache TTL in seconds (L2 cache)
        l1_ttl_seconds: L1 cache TTL in seconds
        namespace: Cache namespace
        key_builder: Custom key builder function

    Returns:
        Decorator function
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get the cache instance singleton
            cache = get_tiered_cache()

            # Generate cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = generate_cache_key(func.__name__, args, kwargs, namespace)

            # Try to get from cache
            cached_result = await cache.get(cache_key)

            if cached_result is not None:
                return cached_result

            # Call the original function
            result = await func(*args, **kwargs)

            # Cache the result
            await cache.set(
                cache_key,
                result,
                l1_ttl_seconds=l1_ttl_seconds,
                l2_ttl_seconds=ttl_seconds,
            )

            return result

        # Add a method to invalidate the cache for specific args
        async def invalidate(*args, **kwargs):
            cache = get_tiered_cache()

            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = generate_cache_key(func.__name__, args, kwargs, namespace)

            await cache.delete(cache_key)

        wrapper.invalidate = invalidate

        return wrapper

    return decorator


# Cache instance singleton
_GLOBAL_CACHE_INSTANCE = None


def get_tiered_cache() -> TieredCache:
    """
    Get the global tiered cache instance.

    This function returns a singleton instance of the tiered cache.

    Returns:
        Global tiered cache instance
    """
    global _GLOBAL_CACHE_INSTANCE

    if _GLOBAL_CACHE_INSTANCE is None:
        config = get_settings()
        _GLOBAL_CACHE_INSTANCE = TieredCache(
            prefix=f"ai-orchestra:{config.env}:",
            l1_max_size=config.cache.memory_max_size,
            l1_cleanup_interval=config.cache.memory_cleanup_interval,
            l2_default_ttl=config.cache.redis_default_ttl,
            cache_warming_keys=config.cache.warming_keys,
        )

    return _GLOBAL_CACHE_INSTANCE


# Strongly typed model cache for Pydantic models
class ModelCache(Generic[T]):
    """
    Typed cache for Pydantic models.

    This class provides a strongly typed cache interface for Pydantic models
    with automatic serialization and deserialization.
    """

    def __init__(
        self,
        model_class: Type[T],
        prefix: str,
        l1_max_size: int = 1000,
        l2_default_ttl: int = 300,
    ):
        """
        Initialize the model cache.

        Args:
            model_class: Pydantic model class
            prefix: Cache key prefix
            l1_max_size: Maximum L1 cache size
            l2_default_ttl: Default L2 cache TTL
        """
        self.model_class = model_class

        def serialize(obj: T) -> str:
            return obj.json()

        def deserialize(data: str) -> T:
            return model_class.parse_raw(data)

        self.cache = TieredCache[T](
            prefix=prefix,
            l1_max_size=l1_max_size,
            l2_default_ttl=l2_default_ttl,
            serialize=serialize,
            deserialize=deserialize,
        )

    async def get(self, key: str) -> Optional[T]:
        """
        Get a model from the cache.

        Args:
            key: Cache key

        Returns:
            The cached model, or None if not found
        """
        return await self.cache.get(key)

    async def set(
        self,
        key: str,
        value: T,
        l1_ttl_seconds: int = 0,
        l2_ttl_seconds: Optional[int] = None,
    ) -> None:
        """
        Set a model in the cache.

        Args:
            key: Cache key
            value: Model to cache
            l1_ttl_seconds: L1 cache TTL in seconds
            l2_ttl_seconds: L2 cache TTL in seconds
        """
        await self.cache.set(key, value, l1_ttl_seconds=l1_ttl_seconds, l2_ttl_seconds=l2_ttl_seconds)

    async def delete(self, key: str) -> bool:
        """
        Delete a model from the cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise
        """
        return await self.cache.delete(key)


# Semantic cache for similarity-based retrieval
class SemanticCache:
    """
    Semantic cache for similarity-based retrieval.

    This class provides a cache that retrieves values based on semantic
    similarity of the query rather than exact key matches.
    """

    def __init__(
        self,
        prefix: str = "semantic:",
        similarity_threshold: float = 0.85,
        max_cache_size: int = 1000,
        ttl_seconds: int = 3600,  # 1 hour
    ):
        """
        Initialize the semantic cache.

        Args:
            prefix: Cache key prefix
            similarity_threshold: Threshold for considering a cache hit
            max_cache_size: Maximum cache size
            ttl_seconds: Default TTL in seconds
        """
        self.prefix = prefix
        self.similarity_threshold = similarity_threshold
        self.max_cache_size = max_cache_size
        self.ttl_seconds = ttl_seconds

        # Don't import at module level to avoid circular imports
        from ..gcp.vertex_ai_service import VertexAIService

        self.ai_service = VertexAIService()

        # Initialize the cache
        self.cache = TieredCache[Dict[str, Any]](
            prefix=prefix,
            l1_max_size=max_cache_size,
            l2_default_ttl=ttl_seconds,
        )

        # Storage for query embeddings
        self.query_embeddings: Dict[str, List[float]] = {}

    async def get(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Get a result from the semantic cache based on query similarity.

        Args:
            query: The query string

        Returns:
            Cached result if a similar query exists, None otherwise
        """
        # Get the embedding for the query
        query_embedding = await self.ai_service.get_embedding(query)

        # Find the most similar cached query
        most_similar_key = None
        highest_similarity = 0.0

        # Get all keys from L1 cache (faster than checking Redis)
        # In a real implementation, we'd use a vector database for this
        for key in list(self.query_embeddings.keys()):
            cached_embedding = self.query_embeddings.get(key)

            if cached_embedding:
                similarity = self._cosine_similarity(query_embedding, cached_embedding)

                if similarity > highest_similarity:
                    highest_similarity = similarity
                    most_similar_key = key

        # Check if the similarity exceeds the threshold
        if most_similar_key and highest_similarity >= self.similarity_threshold:
            # Get the result from the cache
            result = await self.cache.get(most_similar_key)

            if result:
                log_event(
                    logger=logger,
                    category="semantic_cache",
                    action="hit",
                    data={
                        "query": query,
                        "matched_query": most_similar_key,
                        "similarity": highest_similarity,
                    },
                )

                return result

        log_event(
            logger=logger,
            category="semantic_cache",
            action="miss",
            data={"query": query},
        )

        return None

    async def set(self, query: str, result: Dict[str, Any]) -> None:
        """
        Set a result in the semantic cache.

        Args:
            query: The query string
            result: The result to cache
        """
        # Get the embedding for the query
        query_embedding = await self.ai_service.get_embedding(query)

        # Store the embedding
        self.query_embeddings[query] = query_embedding

        # Store the result
        await self.cache.set(
            query,
            result,
            l1_ttl_seconds=self.ttl_seconds,
            l2_ttl_seconds=self.ttl_seconds,
        )

        # Limit the size of the embeddings dictionary
        if len(self.query_embeddings) > self.max_cache_size:
            # Remove the oldest entry
            oldest_key = next(iter(self.query_embeddings))
            del self.query_embeddings[oldest_key]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity (-1 to 1)
        """
        # Check if vectors are valid
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))

        # Calculate magnitudes
        mag1 = sum(a * a for a in vec1) ** 0.5
        mag2 = sum(b * b for b in vec2) ** 0.5

        # Avoid division by zero
        if mag1 == 0 or mag2 == 0:
            return 0.0

        # Return cosine similarity
        return dot_product / (mag1 * mag2)
