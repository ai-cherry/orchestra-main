"""
Memory cache management system with configurable eviction policies.

This module provides a cache manager that can be used to manage memory caches
with different eviction policies (LRU, LFU, TTL) and size limits.
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, List, Tuple, Callable, Generic, TypeVar
from datetime import datetime, timedelta
import heapq
from enum import Enum
from core.orchestrator.src.exceptions import MemoryError
import os

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for generic value type
T = TypeVar("T")


class EvictionPolicy(Enum):
    """Eviction policy for cache entries."""

    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live


class CacheStats:
    """Statistics for cache operations."""

    def __init__(self):
        """Initialize cache statistics."""
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.inserts = 0
        self.updates = 0

    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "inserts": self.inserts,
            "updates": self.updates,
            "hit_rate": self.hit_rate(),
        }


class CacheEntry(Generic[T]):
    """Cache entry with metadata for eviction policies."""

    def __init__(self, key: str, value: T, ttl_seconds: Optional[int] = None):
        """
        Initialize a cache entry.

        Args:
            key: Cache entry key
            value: Cache entry value
            ttl_seconds: Optional TTL in seconds
        """
        self.key = key
        self.value = value
        self.created_at = time.time()
        self.last_accessed = self.created_at
        self.access_count = 0
        self.expires_at = (
            self.created_at + ttl_seconds if ttl_seconds is not None else None
        )

    def access(self) -> None:
        """Record an access to this cache entry."""
        self.last_accessed = time.time()
        self.access_count += 1

    def is_expired(self) -> bool:
        """Check if the entry is expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def time_to_live(self) -> Optional[float]:
        """Get the remaining time to live in seconds."""
        if self.expires_at is None:
            return None
        return max(0.0, self.expires_at - time.time())


class CacheManager(Generic[T]):
    """
    Cache manager with configurable eviction policies and size limits.

    Supports LRU, LFU, and TTL eviction policies, as well as size limits.
    """

    def __init__(
        self,
        max_size: int = 1000,
        eviction_policy: EvictionPolicy = EvictionPolicy.LRU,
        default_ttl_seconds: Optional[int] = None,
        cleanup_interval: int = 60,
        name: str = "default",
    ):
        """
        Initialize the cache manager.

        Args:
            max_size: Maximum number of entries in the cache
            eviction_policy: Policy to use when the cache is full
            default_ttl_seconds: Default TTL for entries in seconds
            cleanup_interval: Interval between cleanup runs in seconds
            name: Name for this cache manager instance
        """
        self.name = name
        self.max_size = max_size
        self.eviction_policy = eviction_policy
        self.default_ttl_seconds = default_ttl_seconds
        self.cleanup_interval = cleanup_interval

        # The main cache storage
        self._cache: Dict[str, CacheEntry[T]] = {}

        # Statistics
        self.stats = CacheStats()

        # Thread safety
        self._lock = threading.RLock()

        # Last cleanup time
        self._last_cleanup = time.time()

        logger.info(
            f"Initialized cache manager '{name}' with max_size={max_size}, "
            f"eviction_policy={eviction_policy.value}, default_ttl={default_ttl_seconds}s"
        )

    def get(self, key: str) -> Optional[T]:
        """
        Get a value from the cache.

        Args:
            key: The key to look up

        Returns:
            The cached value, or None if not found or expired
        """
        with self._lock:
            # Check if we need to run cleanup
            self._check_cleanup()

            # Try to get the entry
            entry = self._cache.get(key)

            # If not found or expired, return None
            if entry is None or entry.is_expired():
                self.stats.misses += 1

                # If expired, remove it
                if entry is not None and entry.is_expired():
                    self._remove_entry(key)

                return None

            # Record the access
            entry.access()
            self.stats.hits += 1

            return entry.value

    def put(self, key: str, value: T, ttl_seconds: Optional[int] = None) -> None:
        """
        Put a value in the cache.

        Args:
            key: The key to store the value under
            value: The value to store
            ttl_seconds: Optional TTL in seconds, overrides the default
        """
        with self._lock:
            # Check if we need to run cleanup
            self._check_cleanup()

            # If the key exists, update it
            if key in self._cache:
                self._cache[key].value = value
                self._cache[key].access()

                # Update TTL if provided
                if ttl_seconds is not None:
                    self._cache[key].expires_at = time.time() + ttl_seconds

                self.stats.updates += 1
                return

            # If the cache is full, evict entries
            if len(self._cache) >= self.max_size:
                self._evict_entries()

            # Use the provided TTL or the default
            effective_ttl = (
                ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
            )

            # Create a new entry
            self._cache[key] = CacheEntry(key, value, effective_ttl)
            self.stats.inserts += 1

    def remove(self, key: str) -> bool:
        """
        Remove a value from the cache.

        Args:
            key: The key to remove

        Returns:
            True if the key was found and removed, False otherwise
        """
        with self._lock:
            return self._remove_entry(key)

    def clear(self) -> None:
        """Clear all entries from the cache."""
        with self._lock:
            self._cache.clear()
            logger.info(f"Cleared cache '{self.name}'")

    def contains(self, key: str) -> bool:
        """
        Check if a key exists in the cache.

        Args:
            key: The key to check

        Returns:
            True if the key exists and is not expired, False otherwise
        """
        with self._lock:
            entry = self._cache.get(key)
            return entry is not None and not entry.is_expired()

    def size(self) -> int:
        """
        Get the current size of the cache.

        Returns:
            Number of entries in the cache
        """
        with self._lock:
            return len(self._cache)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            stats = self.stats.to_dict()
            stats["size"] = len(self._cache)
            stats["max_size"] = self.max_size
            stats["eviction_policy"] = self.eviction_policy.value
            return stats

    def get_keys(self) -> List[str]:
        """
        Get all keys in the cache.

        Returns:
            List of keys in the cache
        """
        with self._lock:
            return list(self._cache.keys())

    def get_with_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a value from the cache with its metadata.

        Args:
            key: The key to look up

        Returns:
            Dictionary with value and metadata, or None if not found or expired
        """
        with self._lock:
            entry = self._cache.get(key)

            if entry is None or entry.is_expired():
                return None

            # Record the access
            entry.access()

            return {
                "key": entry.key,
                "value": entry.value,
                "created_at": entry.created_at,
                "last_accessed": entry.last_accessed,
                "access_count": entry.access_count,
                "expires_at": entry.expires_at,
                "ttl": entry.time_to_live(),
            }

    def cleanup(self) -> int:
        """
        Run cleanup to remove expired entries.

        Returns:
            Number of entries removed
        """
        with self._lock:
            return self._cleanup()

    def _check_cleanup(self) -> None:
        """Check if cleanup should be run and run it if needed."""
        current_time = time.time()

        if current_time - self._last_cleanup > self.cleanup_interval:
            self._cleanup()
            self._last_cleanup = current_time

    def _cleanup(self) -> int:
        """
        Remove expired entries.

        Returns:
            Number of entries removed
        """
        to_remove = []

        # Find expired entries
        for key, entry in self._cache.items():
            if entry.is_expired():
                to_remove.append(key)

        # Remove them
        for key in to_remove:
            self._remove_entry(key)

        if to_remove:
            logger.debug(
                f"Cleaned up {len(to_remove)} expired entries from cache '{self.name}'"
            )

        return len(to_remove)

    def _remove_entry(self, key: str) -> bool:
        """
        Remove an entry from the cache.

        Args:
            key: The key to remove

        Returns:
            True if the key was found and removed, False otherwise
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def _evict_entries(self, count: int = 1) -> None:
        """
        Evict entries according to the configured policy.

        Args:
            count: Number of entries to evict
        """
        if not self._cache:
            return

        # Apply the appropriate eviction policy
        if self.eviction_policy == EvictionPolicy.LRU:
            self._evict_lru(count)
        elif self.eviction_policy == EvictionPolicy.LFU:
            self._evict_lfu(count)
        elif self.eviction_policy == EvictionPolicy.TTL:
            self._evict_ttl(count)

    def _evict_lru(self, count: int) -> None:
        """
        Evict least recently used entries.

        Args:
            count: Number of entries to evict
        """
        # Sort by last accessed time (ascending)
        entries = sorted(self._cache.items(), key=lambda x: x[1].last_accessed)

        # Evict the oldest entries
        for i in range(min(count, len(entries))):
            key = entries[i][0]
            self._remove_entry(key)
            self.stats.evictions += 1

        if count > 0:
            logger.debug(
                f"Evicted {min(count, len(entries))} entries using LRU policy from cache '{self.name}'"
            )

    def _evict_lfu(self, count: int) -> None:
        """
        Evict least frequently used entries.

        Args:
            count: Number of entries to evict
        """
        # Sort by access count (ascending)
        entries = sorted(self._cache.items(), key=lambda x: x[1].access_count)

        # Evict the least frequently used entries
        for i in range(min(count, len(entries))):
            key = entries[i][0]
            self._remove_entry(key)
            self.stats.evictions += 1

        if count > 0:
            logger.debug(
                f"Evicted {min(count, len(entries))} entries using LFU policy from cache '{self.name}'"
            )

    def _evict_ttl(self, count: int) -> None:
        """
        Evict entries with the shortest remaining TTL.

        Args:
            count: Number of entries to evict
        """

        # Sort by TTL (ascending), putting entries with no TTL at the end
        def ttl_key(item):
            entry = item[1]
            ttl = entry.time_to_live()
            return ttl if ttl is not None else float("inf")

        entries = sorted(self._cache.items(), key=ttl_key)

        # Evict the entries with the shortest TTL
        for i in range(min(count, len(entries))):
            key = entries[i][0]
            self._remove_entry(key)
            self.stats.evictions += 1

        if count > 0:
            logger.debug(
                f"Evicted {min(count, len(entries))} entries using TTL policy from cache '{self.name}'"
            )


# Global registry for cache managers
_cache_managers: Dict[str, CacheManager] = {}
_cache_managers_lock = threading.RLock()


def get_cache_manager(
    name: str = "default",
    max_size: int = 1000,
    eviction_policy: EvictionPolicy = EvictionPolicy.LRU,
    default_ttl_seconds: Optional[int] = None,
    cleanup_interval: int = 60,
    create_if_missing: bool = True,
) -> CacheManager:
    """
    Get a named cache manager instance.

    Args:
        name: Name of the cache manager
        max_size: Maximum size for a new cache manager
        eviction_policy: Eviction policy for a new cache manager
        default_ttl_seconds: Default TTL for a new cache manager
        cleanup_interval: Cleanup interval for a new cache manager
        create_if_missing: Whether to create the cache manager if it doesn't exist

    Returns:
        The cache manager instance

    Raises:
        MemoryError: If the cache manager doesn't exist and create_if_missing is False
    """
    with _cache_managers_lock:
        if name in _cache_managers:
            return _cache_managers[name]

        if not create_if_missing:
            raise MemoryError(f"Cache manager '{name}' not found")

        cache_manager = CacheManager(
            max_size=max_size,
            eviction_policy=eviction_policy,
            default_ttl_seconds=default_ttl_seconds,
            cleanup_interval=cleanup_interval,
            name=name,
        )

        _cache_managers[name] = cache_manager
        return cache_manager


def remove_cache_manager(name: str) -> bool:
    """
    Remove a cache manager from the registry.

    Args:
        name: Name of the cache manager to remove

    Returns:
        True if the cache manager was found and removed, False otherwise
    """
    with _cache_managers_lock:
        if name in _cache_managers:
            del _cache_managers[name]
            return True
        return False


def clear_all_cache_managers() -> None:
    """Clear all cache managers in the registry."""
    with _cache_managers_lock:
        for cache_manager in _cache_managers.values():
            cache_manager.clear()

        logger.info(f"Cleared all cache managers ({len(_cache_managers)})")


class ExternalServiceIntegration:
    """
    Handles integrations with external services like DeepSeek, Grok AI, Perplexity, ElevenLabs, OpenRouter, and Figma.
    """

    def __init__(self):
        self.services = {
            "deepseek": os.getenv("DEEPSEEK_API_KEY"),
            "grok_ai": os.getenv("GROK_API_KEY"),
            "perplexity": os.getenv("PERPLEXITY_API_KEY"),
            "elevenlabs": os.getenv("ELEVENLABS_API_KEY"),
            "openrouter": os.getenv("OPENROUTER_API_KEY"),
            "figma": {
                "pat": os.getenv("FIGMA_PAT"),
                "project_id": os.getenv("FIGMA_PROJECT_ID"),
            },
        }

    def is_service_available(self, service_name: str) -> bool:
        """Check if a service is available based on its API key."""
        return bool(self.services.get(service_name))

    def get_service_key(self, service_name: str) -> Optional[str]:
        """Retrieve the API key for a given service."""
        return self.services.get(service_name)

    def use_service(self, service_name: str, payload: Dict[str, Any]) -> Any:
        """
        Use the specified service with the provided payload.

        Args:
            service_name: The name of the service to use.
            payload: The data to send to the service.

        Returns:
            The response from the service.
        """
        if not self.is_service_available(service_name):
            raise ValueError(
                f"Service {service_name} is not available or API key is missing."
            )

        # Example: Implement service-specific logic here
        if service_name == "figma":
            return self._sync_figma_design(payload)

        # Placeholder for other services
        return {"status": "success", "service": service_name, "payload": payload}

    def _sync_figma_design(self, payload: Dict[str, Any]) -> Any:
        """Sync design tokens with Figma."""
        figma_pat = self.services["figma"].get("pat")
        project_id = self.services["figma"].get("project_id")

        if not figma_pat or not project_id:
            raise ValueError("Figma PAT or Project ID is missing.")

        # Example: Simulate syncing with Figma
        logger.info(f"Syncing design tokens with Figma project {project_id}.")
        return {"status": "success", "project_id": project_id}


# Example usage
if __name__ == "__main__":
    integration = ExternalServiceIntegration()

    # Check if OpenRouter is available
    if integration.is_service_available("openrouter"):
        logger.info("OpenRouter is available.")

    # Use Figma integration
    try:
        response = integration.use_service("figma", {"design_tokens": "example_data"})
        logger.info(f"Figma sync response: {response}")
    except ValueError as e:
        logger.error(e)
