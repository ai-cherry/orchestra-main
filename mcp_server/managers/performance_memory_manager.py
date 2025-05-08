"""
Performance-optimized memory manager for the MCP server.

This module provides a memory manager implementation that prioritizes performance
over other considerations, making it suitable for development and single-user deployments.
"""

from typing import Dict, List, Optional, Any, Union, Tuple
import time
import json
import logging
import asyncio
from ..interfaces.memory_manager import IMemoryManager
from ..models.memory import MemoryEntry, MemoryMetadata, MemoryType, MemoryScope, CompressionLevel, StorageTier
from ..storage.in_memory_storage import InMemoryStorage

logger = logging.getLogger(__name__)

class PerformanceMemoryManager(IMemoryManager):
    """Memory manager optimized for performance.
    
    This implementation prioritizes speed and simplicity over advanced features:
    - Uses in-memory storage with optional persistence
    - Maintains a local in-process cache for ultra-fast access
    - Skips compression for faster processing
    - Uses simplified search implementation
    
    Attributes:
        config: Configuration dictionary
        storage: The underlying storage implementation
        cache: Local in-process cache for ultra-fast access
        max_cache_items: Maximum number of items to keep in cache
        cache_ttl: Time-to-live for cache entries in seconds
        cache_last_cleanup: Timestamp of the last cache cleanup
        cache_cleanup_interval: Interval between cache cleanups in seconds
        _lock: Asyncio lock for thread-safe operations
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize with performance-focused configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.storage = InMemoryStorage(config)
        self.cache: Dict[str, Dict[str, Any]] = {}  # Local in-process cache for ultra-fast access
        self.max_cache_items = self.config.get("max_cache_items", 1000)  # Limit cache size
        self.cache_ttl = self.config.get("cache_ttl", 300)  # 5 minutes default
        self.cache_last_cleanup = time.time()
        self.cache_cleanup_interval = 60  # Clean expired items every minute
        self._lock = asyncio.Lock()  # For thread-safe operations
        self._initialized = False
        logger.info("Initialized PerformanceMemoryManager with cache_ttl=%s seconds, max_items=%s",
                   self.cache_ttl, self.max_cache_items)
    
    async def initialize(self) -> bool:
        """Initialize the memory manager.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        logger.info("Initializing PerformanceMemoryManager")
        try:
            result = await self.storage.initialize()
            if result:
                self._initialized = True
                logger.info("PerformanceMemoryManager initialized successfully")
            else:
                logger.error("Failed to initialize storage backend")
            return result
        except Exception as e:
            logger.error("Error initializing memory manager: %s", str(e))
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
    
    async def store(self, key: str, content: Any, tool_name: str,
                   ttl_seconds: int = 3600) -> bool:
        """Store content with optimized parameters.
        
        Args:
            key: The key to store the content under
            content: The content to store
            tool_name: The name of the tool storing the content
            ttl_seconds: Time-to-live in seconds (default: 1 hour)
            
        Returns:
            bool: True if storage was successful, False otherwise
        """
        if not await self._check_initialized():
            logger.error("Cannot store: memory manager not initialized")
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
                content_hash=None  # Will be computed during save
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
                storage_tier=StorageTier.HOT
            )
            
            # Update local cache with thread safety
            async with self._lock:
                # Check if we need to evict items from cache
                if len(self.cache) >= self.max_cache_items:
                    await self._evict_cache_items()
                
                # Add to cache
                self.cache[key] = {
                    "content": content,
                    "expires_at": time.time() + min(ttl_seconds, self.cache_ttl)
                }
                
                # Clean cache if needed
                await self._clean_cache_if_needed()
            
            # Store in persistent storage
            try:
                return await self.storage.save(key, entry)
            except Exception as e:
                logger.error("Failed to save to storage: %s", str(e))
                return False
                
        except Exception as e:
            logger.error("Error storing content: %s", str(e))
            return False
    
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve content with cache optimization.
        
        Args:
            key: The key to retrieve content for
            
        Returns:
            Optional[Any]: The content if found, None otherwise
        """
        if not await self._check_initialized():
            logger.error("Cannot retrieve: memory manager not initialized")
            return None
            
        logger.debug("Retrieving content for key '%s'", key)
        
        try:
            # Check local cache first
            async with self._lock:
                if key in self.cache:
                    cache_item = self.cache[key]
                    if cache_item["expires_at"] > time.time():
                        logger.debug("Cache hit for key '%s'", key)
                        return cache_item["content"]
                    else:
                        # Expired item, remove from cache
                        logger.debug("Cache expired for key '%s'", key)
                        del self.cache[key]
            
            # Not in cache, retrieve from storage
            logger.debug("Cache miss for key '%s', retrieving from storage", key)
            try:
                entry = await self.storage.get(key)
                if entry is None:
                    logger.debug("Key '%s' not found in storage", key)
                    return None
                
                # Update cache
                async with self._lock:
                    self.cache[key] = {
                        "content": entry.content,
                        "expires_at": time.time() + min(entry.ttl_seconds, self.cache_ttl)
                    }
                
                return entry.content
            except Exception as e:
                logger.error("Error retrieving from storage: %s", str(e))
                return None
                
        except Exception as e:
            logger.error("Error retrieving content: %s", str(e))
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete content from memory.
        
        Args:
            key: The key to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        if not await self._check_initialized():
            logger.error("Cannot delete: memory manager not initialized")
            return False
            
        logger.debug("Deleting key '%s'", key)
        
        try:
            # Remove from cache
            async with self._lock:
                if key in self.cache:
                    del self.cache[key]
            
            # Remove from storage
            try:
                return await self.storage.delete(key)
            except Exception as e:
                logger.error("Error deleting from storage: %s", str(e))
                return False
                
        except Exception as e:
            logger.error("Error deleting content: %s", str(e))
            return False
    
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Simple search implementation for development.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of search results
        """
        if not await self._check_initialized():
            logger.error("Cannot search: memory manager not initialized")
            return []
            
        logger.debug("Searching for '%s' with limit %d", query, limit)
        
        try:
            # For now, just return all items that contain the query string
            results = []
            
            try:
                keys = await self.storage.list_keys()
            except Exception as e:
                logger.error("Error listing keys: %s", str(e))
                return []
            
            for key in keys:
                try:
                    entry = await self.storage.get(key)
                    if entry:
                        # Simple string matching for now
                        try:
                            content_str = json.dumps(entry.content)
                            if query.lower() in content_str.lower():
                                results.append({
                                    "key": key,
                                    "content": entry.content,
                                    "score": 1.0  # Simple relevance score
                                })
                                
                                if len(results) >= limit:
                                    break
                        except Exception as e:
                            logger.error("Error processing entry for key '%s': %s", key, str(e))
                except Exception as e:
                    logger.error("Error retrieving entry for key '%s': %s", key, str(e))
            
            logger.debug("Found %d results for query '%s'", len(results), query)
            return results
                
        except Exception as e:
            logger.error("Error searching content: %s", str(e))
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Check memory system health.
        
        Returns:
            Dict[str, Any]: Health check results
        """
        logger.debug("Performing health check")
        
        try:
            if not self._initialized:
                return {
                    "status": "not_initialized",
                    "cache_items": len(self.cache),
                    "storage": {"status": "unknown"}
                }
                
            try:
                storage_health = await self.storage.health_check()
            except Exception as e:
                logger.error("Error checking storage health: %s", str(e))
                storage_health = {"status": "error", "error": str(e)}
                
            return {
                "status": "healthy" if storage_health.get("status") == "healthy" else "degraded",
                "cache_items": len(self.cache),
                "cache_max_items": self.max_cache_items,
                "cache_usage_percent": (len(self.cache) / self.max_cache_items) * 100 if self.max_cache_items > 0 else 0,
                "storage": storage_health
            }
                
        except Exception as e:
            logger.error("Error performing health check: %s", str(e))
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _evict_cache_items(self) -> None:
        """Evict items from cache when it reaches the size limit."""
        if len(self.cache) < self.max_cache_items:
            return
            
        # Sort by expiration time and remove oldest items
        items_to_keep = self.max_cache_items * 0.8  # Keep 80% of max capacity
        items_to_remove = len(self.cache) - int(items_to_keep)
        
        if items_to_remove <= 0:
            return
            
        logger.debug("Evicting %d items from cache", items_to_remove)
        
        # Sort keys by expiration time (oldest first)
        sorted_keys = sorted(
            self.cache.keys(),
            key=lambda k: self.cache[k].get("expires_at", 0)
        )
        
        # Remove oldest items
        for key in sorted_keys[:items_to_remove]:
            del self.cache[key]
            
        logger.debug("Cache eviction complete, new size: %d", len(self.cache))
    
    async def _clean_cache_if_needed(self) -> None:
        """Clean expired cache items if needed."""
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