"""
Redis LRU Cache for Memory Management.

This module provides a Redis-backed Least Recently Used (LRU) cache
implementation for efficient memory management in the AI Orchestration System.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

import redis
from redis.exceptions import RedisError

from packages.shared.src.models.base_models import MemoryItem
from packages.shared.src.storage.exceptions import StorageError, ConnectionError, OperationError

# Set up logger
logger = logging.getLogger(__name__)


class RedisLRUCache:
    """
    Redis-backed LRU (Least Recently Used) cache implementation.
    
    This class provides a Redis Memorystore-backed LRU cache for efficient
    memory management. It automatically handles key expiration, memory
    pressure management, and statistics tracking.
    """
    
    def __init__(
        self,
        redis_host: str,
        redis_port: int = 6379,
        redis_password: Optional[str] = None,
        max_memory_mb: int = 512,  # Default Redis max memory (512MB)
        max_memory_policy: str = "allkeys-lru",  # Redis eviction policy
        default_ttl: int = 86400,  # Default TTL (1 day in seconds)
        namespace: str = "memory",
        connect_timeout: int = 5,
    ):
        """
        Initialize the Redis LRU cache.
        
        Args:
            redis_host: Redis server hostname
            redis_port: Redis server port
            redis_password: Optional Redis password
            max_memory_mb: Maximum memory in MB for Redis
            max_memory_policy: Redis memory eviction policy
            default_ttl: Default TTL for cache entries in seconds
            namespace: Namespace prefix for all Redis keys
            connect_timeout: Connection timeout in seconds
        """
        self._redis_host = redis_host
        self._redis_port = redis_port
        self._redis_password = redis_password
        self._max_memory_mb = max_memory_mb
        self._max_memory_policy = max_memory_policy
        self._default_ttl = default_ttl
        self._namespace = namespace
        self._connect_timeout = connect_timeout
        
        # Redis client
        self._redis = None
        self._connected = False
        
        # Statistics
        self._hit_count = 0
        self._miss_count = 0
        self._eviction_count = 0
        self._last_stats_time = time.time()
        
    async def connect(self) -> None:
        """Connect to Redis and configure it."""
        try:
            # Create Redis client
            self._redis = redis.Redis(
                host=self._redis_host,
                port=self._redis_port,
                password=self._redis_password,
                socket_timeout=self._connect_timeout,
                socket_connect_timeout=self._connect_timeout,
                decode_responses=True,
            )
            
            # Test connection
            self._redis.ping()
            
            # Configure Redis
            if self._max_memory_mb > 0:
                # Set maximum memory
                self._redis.config_set('maxmemory', f'{self._max_memory_mb}mb')
                # Set eviction policy
                self._redis.config_set('maxmemory-policy', self._max_memory_policy)
                
            # Reset statistics
            await self.reset_stats()
            
            self._connected = True
            logger.info(f"Connected to Redis at {self._redis_host}:{self._redis_port}")
            
        except redis.exceptions.ConnectionError as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect to Redis: {e}", e)
            
        except redis.exceptions.RedisError as e:
            self._connected = False
            raise StorageError(f"Redis error during connection: {e}", e)
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._redis:
            self._redis.close()
            self._connected = False
            logger.info("Disconnected from Redis")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            The cached value or None if not found
        """
        if not self._connected:
            raise ConnectionError("Not connected to Redis")
            
        redis_key = self._make_key(key)
        
        try:
            # Get the value
            value = self._redis.get(redis_key)
            
            if value:
                # Update access time (touch the key) by resetting its TTL
                self._redis.expire(redis_key, self._default_ttl)
                # Record hit
                self._hit_count += 1
                return self._deserialize_value(value)
            else:
                # Record miss
                self._miss_count += 1
                return None
                
        except RedisError as e:
            logger.error(f"Redis error during get: {e}")
            raise StorageError(f"Redis error during get: {e}", e)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
            ttl: Optional TTL in seconds (default: self._default_ttl)
            
        Returns:
            True if successful, False otherwise
        """
        if not self._connected:
            raise ConnectionError("Not connected to Redis")
            
        redis_key = self._make_key(key)
        ttl = ttl if ttl is not None else self._default_ttl
        
        try:
            # Serialize the value
            serialized = self._serialize_value(value)
            
            # Set with expiration
            result = self._redis.setex(
                name=redis_key,
                time=ttl,
                value=serialized
            )
            
            return bool(result)
            
        except RedisError as e:
            logger.error(f"Redis error during set: {e}")
            raise StorageError(f"Redis error during set: {e}", e)
    
    async def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            True if key was deleted, False if key didn't exist
        """
        if not self._connected:
            raise ConnectionError("Not connected to Redis")
            
        redis_key = self._make_key(key)
        
        try:
            # Delete the key
            result = self._redis.delete(redis_key)
            
            # Returns number of keys deleted (0 or 1)
            return bool(result)
            
        except RedisError as e:
            logger.error(f"Redis error during delete: {e}")
            raise StorageError(f"Redis error during delete: {e}", e)
    
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: The cache key
            
        Returns:
            True if key exists, False otherwise
        """
        if not self._connected:
            raise ConnectionError("Not connected to Redis")
            
        redis_key = self._make_key(key)
        
        try:
            # Check if key exists
            return bool(self._redis.exists(redis_key))
            
        except RedisError as e:
            logger.error(f"Redis error during exists: {e}")
            raise StorageError(f"Redis error during exists: {e}", e)
    
    async def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get memory usage statistics.
        
        Returns:
            Dictionary with memory usage information
        """
        if not self._connected:
            raise ConnectionError("Not connected to Redis")
            
        try:
            # Get memory info
            info = self._redis.info(section="memory")
            
            # Calculate hit rate
            total_ops = self._hit_count + self._miss_count
            hit_rate = self._hit_count / total_ops if total_ops > 0 else 0
            
            # Get eviction stats
            stats = self._redis.info(section="stats")
            evicted_keys = stats.get("evicted_keys", 0)
            
            # Track evictions since last call
            new_evictions = evicted_keys - self._eviction_count
            self._eviction_count = evicted_keys
            
            # Calculate eviction rate (evictions per second)
            now = time.time()
            time_diff = now - self._last_stats_time
            eviction_rate = new_evictions / time_diff if time_diff > 0 else 0
            self._last_stats_time = now
            
            return {
                "used_memory_mb": int(info.get("used_memory", 0)) / (1024 * 1024),
                "max_memory_mb": self._max_memory_mb,
                "memory_usage_pct": int(info.get("used_memory", 0)) / (self._max_memory_mb * 1024 * 1024) if self._max_memory_mb > 0 else 0,
                "hit_count": self._hit_count,
                "miss_count": self._miss_count,
                "hit_rate": hit_rate,
                "total_evictions": evicted_keys,
                "eviction_rate": eviction_rate,
                "keys_count": self._redis.dbsize(),
                "fragmentation_ratio": info.get("mem_fragmentation_ratio", 0),
            }
            
        except RedisError as e:
            logger.error(f"Redis error during get_memory_usage: {e}")
            raise StorageError(f"Redis error during get_memory_usage: {e}", e)
    
    async def flush_all(self) -> bool:
        """
        Flush all keys from the cache.
        
        Returns:
            True if successful
        """
        if not self._connected:
            raise ConnectionError("Not connected to Redis")
            
        try:
            # Only flush keys with our namespace
            pattern = f"{self._namespace}:*"
            cursor = 0
            while True:
                cursor, keys = self._redis.scan(cursor, pattern)
                if keys:
                    self._redis.delete(*keys)
                if cursor == 0:
                    break
                    
            # Reset statistics
            await self.reset_stats()
            
            return True
            
        except RedisError as e:
            logger.error(f"Redis error during flush_all: {e}")
            raise StorageError(f"Redis error during flush_all: {e}", e)
    
    async def reset_stats(self) -> None:
        """Reset cache statistics."""
        self._hit_count = 0
        self._miss_count = 0
        self._eviction_count = 0
        self._last_stats_time = time.time()
    
    async def store_memory_item(self, item: MemoryItem) -> bool:
        """
        Store a memory item in the cache.
        
        Args:
            item: The memory item to store
            
        Returns:
            True if successful, False otherwise
        """
        if not item.id:
            raise ValueError("Memory item must have an ID")
            
        # Set primary key for the item
        success = await self.set(f"item:{item.id}", item.dict())
        
        if success and item.user_id:
            # Add to user index
            index_key = f"user:{item.user_id}"
            await self._add_to_index(index_key, item.id)
            
            # Add to session index if available
            if item.session_id:
                session_key = f"session:{item.user_id}:{item.session_id}"
                await self._add_to_index(session_key, item.id)
                
        return success
    
    async def get_memory_item(self, item_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory item from the cache.
        
        Args:
            item_id: The ID of the memory item
            
        Returns:
            The memory item or None if not found
        """
        item_dict = await self.get(f"item:{item_id}")
        
        if item_dict:
            return MemoryItem(**item_dict)
        
        return None
    
    async def get_user_items(
        self, 
        user_id: str, 
        limit: int = 50
    ) -> List[MemoryItem]:
        """
        Retrieve memory items for a user.
        
        Args:
            user_id: The user ID
            limit: Maximum number of items to retrieve
            
        Returns:
            List of memory items
        """
        index_key = f"user:{user_id}"
        item_ids = await self._get_from_index(index_key, limit)
        
        items = []
        for item_id in item_ids:
            item = await self.get_memory_item(item_id)
            if item:
                items.append(item)
                
        return items
    
    async def get_session_items(
        self, 
        user_id: str, 
        session_id: str, 
        limit: int = 50
    ) -> List[MemoryItem]:
        """
        Retrieve memory items for a user's session.
        
        Args:
            user_id: The user ID
            session_id: The session ID
            limit: Maximum number of items to retrieve
            
        Returns:
            List of memory items
        """
        index_key = f"session:{user_id}:{session_id}"
        item_ids = await self._get_from_index(index_key, limit)
        
        items = []
        for item_id in item_ids:
            item = await self.get_memory_item(item_id)
            if item:
                items.append(item)
                
        return items
    
    async def delete_memory_item(self, item_id: str) -> bool:
        """
        Delete a memory item from the cache.
        
        Args:
            item_id: The ID of the memory item
            
        Returns:
            True if item was deleted, False otherwise
        """
        # Get the item first to remove from indexes
        item = await self.get_memory_item(item_id)
        
        if item and item.user_id:
            # Remove from user index
            index_key = f"user:{item.user_id}"
            await self._remove_from_index(index_key, item_id)
            
            # Remove from session index if available
            if item.session_id:
                session_key = f"session:{item.user_id}:{item.session_id}"
                await self._remove_from_index(session_key, item_id)
                
        # Delete the item
        return await self.delete(f"item:{item_id}")
    
    async def _add_to_index(self, index_key: str, item_id: str) -> None:
        """
        Add an item ID to an index.
        
        Args:
            index_key: The index key
            item_id: The item ID to add
        """
        if not self._connected:
            raise ConnectionError("Not connected to Redis")
            
        redis_key = self._make_key(index_key)
        
        try:
            # Add to sorted set with score as current timestamp
            score = time.time()
            self._redis.zadd(redis_key, {item_id: score})
            
            # Ensure the index itself has a TTL
            self._redis.expire(redis_key, self._default_ttl)
            
        except RedisError as e:
            logger.error(f"Redis error during _add_to_index: {e}")
            raise StorageError(f"Redis error during _add_to_index: {e}", e)
    
    async def _remove_from_index(self, index_key: str, item_id: str) -> None:
        """
        Remove an item ID from an index.
        
        Args:
            index_key: The index key
            item_id: The item ID to remove
        """
        if not self._connected:
            raise ConnectionError("Not connected to Redis")
            
        redis_key = self._make_key(index_key)
        
        try:
            # Remove from sorted set
            self._redis.zrem(redis_key, item_id)
            
        except RedisError as e:
            logger.error(f"Redis error during _remove_from_index: {e}")
            raise StorageError(f"Redis error during _remove_from_index: {e}", e)
    
    async def _get_from_index(self, index_key: str, limit: int) -> List[str]:
        """
        Get item IDs from an index, most recent first.
        
        Args:
            index_key: The index key
            limit: Maximum number of items to retrieve
            
        Returns:
            List of item IDs
        """
        if not self._connected:
            raise ConnectionError("Not connected to Redis")
            
        redis_key = self._make_key(index_key)
        
        try:
            # Get IDs from sorted set (highest score = most recent first)
            results = self._redis.zrevrange(redis_key, 0, limit - 1)
            return [result for result in results]
            
        except RedisError as e:
            logger.error(f"Redis error during _get_from_index: {e}")
            raise StorageError(f"Redis error during _get_from_index: {e}", e)
    
    def _make_key(self, key: str) -> str:
        """
        Make a Redis key with namespace.
        
        Args:
            key: The original key
            
        Returns:
            Namespaced Redis key
        """
        return f"{self._namespace}:{key}"
    
    def _serialize_value(self, value: Any) -> str:
        """
        Serialize a value for Redis storage.
        
        Args:
            value: The value to serialize
            
        Returns:
            Serialized value as string
        """
        if isinstance(value, (str, int, float, bool)):
            return json.dumps(value)
        elif isinstance(value, dict):
            return json.dumps(value)
        elif isinstance(value, list):
            return json.dumps(value)
        else:
            return json.dumps(str(value))
    
    def _deserialize_value(self, value: str) -> Any:
        """
        Deserialize a value from Redis storage.
        
        Args:
            value: The serialized value
            
        Returns:
            Deserialized value
        """
        if not value:
            return None
            
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
