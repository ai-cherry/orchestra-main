"""
Performance-optimized memory manager for the MCP server.

This module provides a memory manager implementation that prioritizes performance
over other considerations, making it suitable for development and single-user deployments.
It includes advanced features like local caching, statistics tracking, and
optimized access patterns.
"""

import logging
import threading
import time
from typing import Any, Dict, List, Optional

from ..interfaces.memory_manager import IMemoryManager
from ..models.memory import CompressionLevel, MemoryEntry, MemoryMetadata, MemoryScope, MemoryType, StorageTier
from ..storage.optimized_memory_storage import OptimizedMemoryStorage
from ..storage.sync_storage_adapter import SyncStorageAdapter
from ..utils.performance_monitor import get_performance_monitor

logger = logging.getLogger(__name__)


class PerformanceMemoryManager(IMemoryManager):
    """Memory manager optimized for performance.

    This implementation prioritizes speed and simplicity over advanced features:
    - Uses optimized in-memory storage with optional persistence
    - Maintains a local in-process cache for ultra-fast access
    - Intelligently manages memory to avoid excessive resource usage
    - Provides comprehensive statistics for monitoring and debugging

    Attributes:
        config: Configuration dictionary
        storage: The underlying storage implementation
        storage_adapter: Synchronous adapter for the async storage
        cache: Local in-process cache for ultra-fast access
        max_cache_items: Maximum number of items to keep in cache
        cache_ttl: Time-to-live for cache entries in seconds
        cache_last_cleanup: Timestamp of the last cache cleanup
        cache_cleanup_interval: Interval between cache cleanups in seconds
        _lock: Thread lock for thread-safe operations
        perf: Performance monitoring utility
        stats: Statistics dictionary for tracking operations
    """

    def __init__(self, config: Dict[str, Any] = None, storage=None, performance_monitor=None):
        """Initialize with performance-focused configuration.

        Args:
            config: Optional configuration dictionary
            storage: Optional storage implementation
            performance_monitor: Optional performance monitor
        """
        self.config = config or {}

        # Initialize the storage backend
        if storage is None:
            # Create a new optimized storage instance
            self.storage = OptimizedMemoryStorage(config)
        else:
            # Use the provided storage
            self.storage = storage

        # Create a sync adapter for the storage
        self.storage_adapter = SyncStorageAdapter(self.storage)

        # Initialize cache
        self.cache: Dict[str, Dict[str, Any]] = {}  # Local in-process cache for ultra-fast access
        self.max_cache_items = self.config.get("max_cache_items", 1000)  # Limit cache size
        self.cache_ttl = self.config.get("cache_ttl", 300)  # 5 minutes default
        self.cache_last_cleanup = time.time()
        self.cache_cleanup_interval = 60  # Clean expired items every minute

        # Thread safety
        self._lock = threading.RLock()  # For thread-safe operations
        self._initialized = False

        # Performance monitoring
        self.perf = performance_monitor or get_performance_monitor()

        # Stats tracking
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "operations": 0,
            "errors": 0,
            "store_count": 0,
            "retrieve_count": 0,
            "delete_count": 0,
            "search_count": 0,
        }

        logger.info(
            "Initialized PerformanceMemoryManager with cache_ttl=%s seconds, max_items=%s",
            self.cache_ttl,
            self.max_cache_items,
        )

    async def initialize(self) -> bool:
        """Initialize the memory manager.

        Returns:
            bool: True if initialization was successful, False otherwise
        """
        start_time = time.time()
        logger.info("Initializing PerformanceMemoryManager")
        try:
            # Initialize the underlying storage
            await self.storage.initialize()

            # Initialize the adapter (this is a synchronous operation but we keep the method async for interface compatibility)
            result = self.storage_adapter.initialize()

            if result:
                self._initialized = True
                logger.info("PerformanceMemoryManager initialized successfully")
            else:
                logger.error("Failed to initialize storage backend")

            duration = time.time() - start_time
            self.perf.record_operation("memory_manager.initialize", duration)
            return result
        except Exception as e:
            logger.error("Error initializing memory manager: %s", str(e))
            duration = time.time() - start_time
            self.perf.record_operation("memory_manager.initialize.error", duration)
            return False

    async def _check_initialized(self) -> bool:
        """Check if the memory manager is initialized.

        Returns:
            bool: True if initialized, False otherwise
        """
        if not self._initialized:
            try:
                return await self.initialize()
            except Exception as e:
                logger.error("Failed to initialize on demand: %s", str(e))
                return False
        return True

    async def store(self, key: str, content: Any, tool_name: str, ttl_seconds: int = 3600) -> bool:
        """Store content with optimized parameters.

        Args:
            key: The key to store the content under
            content: The content to store
            tool_name: The name of the tool storing the content
            ttl_seconds: Time-to-live in seconds (default: 1 hour)

        Returns:
            bool: True if storage was successful, False otherwise
        """
        start_time = time.time()
        self.stats["operations"] += 1
        self.stats["store_count"] += 1

        if not await self._check_initialized():
            logger.error("Cannot store: memory manager not initialized")
            self.stats["errors"] += 1
            return False

        logger.debug("Storing content under key '%s' from tool '%s'", key, tool_name)

        try:
            # Create metadata
            metadata = MemoryMetadata(
                source_tool=tool_name,
                last_modified=time.time(),
                access_count=0,
                context_relevance=1.0,  # Assume maximum relevance for performance
                last_accessed=time.time(),
                version=1,
                sync_status={},
                content_hash=None,  # Will be computed during save
            )

            # Create memory entry with performance-optimized defaults
            entry = MemoryEntry(
                memory_type=MemoryType.SHARED,
                scope=MemoryScope.SESSION,
                priority=1,  # High priority
                compression_level=CompressionLevel.NONE,  # No compression for speed
                ttl_seconds=ttl_seconds,
                content=content,
                metadata=metadata,
                storage_tier=StorageTier.HOT,
            )

            # Update local cache with thread safety
            with self._lock:
                # Check if we need to evict items from cache
                if len(self.cache) >= self.max_cache_items:
                    self._evict_cache_items()

                # Add to cache
                self.cache[key] = {
                    "content": content,
                    "expires_at": time.time() + min(ttl_seconds, self.cache_ttl),
                }

                # Clean cache if needed
                self._clean_cache_if_needed()

            # Store in persistent storage
            try:
                # Store using the synchronous adapter
                result = self.storage_adapter.store(key, entry)
                duration = time.time() - start_time
                self.perf.record_operation("memory_manager.store", duration)
                return result
            except Exception as e:
                logger.error("Failed to save to storage: %s", str(e))
                self.stats["errors"] += 1
                duration = time.time() - start_time
                self.perf.record_operation("memory_manager.store.error", duration)
                return False

        except Exception as e:
            logger.error("Error storing content: %s", str(e))
            self.stats["errors"] += 1
            duration = time.time() - start_time
            self.perf.record_operation("memory_manager.store.error", duration)
            return False

    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve content with cache optimization.

        Args:
            key: The key to retrieve content for

        Returns:
            Optional[Any]: The content if found, None otherwise
        """
        start_time = time.time()
        self.stats["operations"] += 1
        self.stats["retrieve_count"] += 1

        if not await self._check_initialized():
            logger.error("Cannot retrieve: memory manager not initialized")
            self.stats["errors"] += 1
            return None

        logger.debug("Retrieving content for key '%s'", key)

        try:
            # Check local cache first
            with self._lock:
                if key in self.cache:
                    cache_item = self.cache[key]
                    if cache_item["expires_at"] > time.time():
                        logger.debug("Cache hit for key '%s'", key)
                        self.stats["cache_hits"] += 1
                        return cache_item["content"]
                    else:
                        # Expired item, remove from cache
                        logger.debug("Cache expired for key '%s'", key)
                        del self.cache[key]
                        self.stats["cache_misses"] += 1

            # Not in cache, retrieve from storage
            logger.debug("Cache miss for key '%s', retrieving from storage", key)
            self.stats["cache_misses"] += 1

            try:
                # Use synchronous adapter to get the content
                entry = self.storage_adapter.retrieve(key)
                if entry is None:
                    logger.debug("Key '%s' not found in storage", key)
                    duration = time.time() - start_time
                    self.perf.record_operation("memory_manager.retrieve.miss", duration)
                    return None

                # Update cache
                with self._lock:
                    # Check if entry has content field (it should be a MemoryEntry)
                    if hasattr(entry, "content"):
                        content = entry.content
                        ttl = getattr(entry, "ttl_seconds", self.cache_ttl)
                    else:
                        # If it's not a MemoryEntry, use it directly
                        content = entry
                        ttl = self.cache_ttl

                    self.cache[key] = {
                        "content": content,
                        "expires_at": time.time() + min(ttl, self.cache_ttl),
                    }

                duration = time.time() - start_time
                self.perf.record_operation("memory_manager.retrieve.hit", duration)
                return content
            except Exception as e:
                logger.error("Error retrieving from storage: %s", str(e))
                self.stats["errors"] += 1
                duration = time.time() - start_time
                self.perf.record_operation("memory_manager.retrieve.error", duration)
                return None

        except Exception as e:
            logger.error("Error retrieving content: %s", str(e))
            self.stats["errors"] += 1
            duration = time.time() - start_time
            self.perf.record_operation("memory_manager.retrieve.error", duration)
            return None

    async def delete(self, key: str) -> bool:
        """Delete content from memory.

        Args:
            key: The key to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        start_time = time.time()
        self.stats["operations"] += 1
        self.stats["delete_count"] += 1

        if not await self._check_initialized():
            logger.error("Cannot delete: memory manager not initialized")
            self.stats["errors"] += 1
            return False

        logger.debug("Deleting key '%s'", key)

        try:
            # Remove from cache
            with self._lock:
                if key in self.cache:
                    del self.cache[key]

            # Remove from storage
            try:
                result = self.storage_adapter.delete(key)
                duration = time.time() - start_time
                self.perf.record_operation("memory_manager.delete", duration)
                return result
            except Exception as e:
                logger.error("Error deleting from storage: %s", str(e))
                self.stats["errors"] += 1
                duration = time.time() - start_time
                self.perf.record_operation("memory_manager.delete.error", duration)
                return False

        except Exception as e:
            logger.error("Error deleting content: %s", str(e))
            self.stats["errors"] += 1
            duration = time.time() - start_time
            self.perf.record_operation("memory_manager.delete.error", duration)
            return False

    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Advanced search implementation using optimized storage.

        Args:
            query: The search query
            limit: Maximum number of results to return

        Returns:
            List[Dict[str, Any]]: List of search results
        """
        start_time = time.time()
        self.stats["operations"] += 1
        self.stats["search_count"] += 1

        if not await self._check_initialized():
            logger.error("Cannot search: memory manager not initialized")
            self.stats["errors"] += 1
            return []

        logger.debug("Searching for '%s' with limit %d", query, limit)

        try:
            # Use the storage adapter's search capabilities
            try:
                # Leverage the optimized search in our storage
                results = self.storage_adapter.search(query, limit=limit)

                # Format the results consistently
                formatted_results = []
                for item in results:
                    # Extract the key and content
                    key = item.get("_key", "unknown")

                    # Handle different result formats
                    if "value" in item:
                        content = item["value"]
                    elif "_key" in item:
                        # Remove the key from the content
                        content_dict = dict(item)
                        content_dict.pop("_key", None)
                        content = content_dict
                    else:
                        content = item

                    formatted_results.append(
                        {
                            "key": key,
                            "content": content,
                            "score": 1.0,  # Simple relevance score for now
                        }
                    )

                duration = time.time() - start_time
                self.perf.record_operation("memory_manager.search", duration)
                logger.debug("Found %d results for query '%s'", len(formatted_results), query)
                return formatted_results

            except Exception as e:
                logger.error("Error using storage search: %s", str(e))
                self.stats["errors"] += 1
                duration = time.time() - start_time
                self.perf.record_operation("memory_manager.search.error", duration)
                return []

        except Exception as e:
            logger.error("Error searching content: %s", str(e))
            self.stats["errors"] += 1
            duration = time.time() - start_time
            self.perf.record_operation("memory_manager.search.error", duration)
            return []

    async def health_check(self) -> Dict[str, Any]:
        """Check memory system health.

        Returns:
            Dict[str, Any]: Health check results
        """
        start_time = time.time()
        logger.debug("Performing health check")

        try:
            if not self._initialized:
                return {
                    "status": "not_initialized",
                    "cache_items": len(self.cache),
                    "storage": {"status": "unknown"},
                    "stats": self.stats,
                }

            try:
                # Use the synchronous adapter
                storage_health = self.storage_adapter.get_health()
            except Exception as e:
                logger.error("Error checking storage health: %s", str(e))
                storage_health = {"status": "error", "error": str(e)}

            result = {
                "status": ("healthy" if storage_health.get("status") == "healthy" else "degraded"),
                "cache_items": len(self.cache),
                "cache_max_items": self.max_cache_items,
                "cache_usage_percent": (
                    (len(self.cache) / self.max_cache_items) * 100 if self.max_cache_items > 0 else 0
                ),
                "storage": storage_health,
                "stats": self.stats,
            }

            duration = time.time() - start_time
            self.perf.record_operation("memory_manager.health_check", duration)
            return result

        except Exception as e:
            logger.error("Error performing health check: %s", str(e))
            duration = time.time() - start_time
            self.perf.record_operation("memory_manager.health_check.error", duration)
            return {"status": "error", "error": str(e), "stats": self.stats}

    def _evict_cache_items(self) -> None:
        """Evict items from cache when it reaches the size limit.

        This is a synchronous method as it's called with the lock held.
        """
        if len(self.cache) < self.max_cache_items:
            return

        # Sort by expiration time and remove oldest items
        items_to_keep = self.max_cache_items * 0.8  # Keep 80% of max capacity
        items_to_remove = len(self.cache) - int(items_to_keep)

        if items_to_remove <= 0:
            return

        logger.debug("Evicting %d items from cache", items_to_remove)

        # Sort keys by expiration time (oldest first)
        sorted_keys = sorted(self.cache.keys(), key=lambda k: self.cache[k].get("expires_at", 0))

        # Remove oldest items
        for key in sorted_keys[:items_to_remove]:
            del self.cache[key]

        logger.debug("Cache eviction complete, new size: %d", len(self.cache))

    def _clean_cache_if_needed(self) -> None:
        """Clean expired cache items if needed.

        This is a synchronous method as it's called with the lock held.
        """
        current_time = time.time()
        if current_time - self.cache_last_cleanup > self.cache_cleanup_interval:
            # Time to clean up
            logger.debug("Cleaning cache")
            keys_to_remove = []
            for key, item in self.cache.items():
                if item["expires_at"] <= current_time:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self.cache[key]

            self.cache_last_cleanup = current_time
            logger.debug("Removed %d expired items from cache", len(keys_to_remove))
