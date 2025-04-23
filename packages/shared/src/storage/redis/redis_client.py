"""
Redis Client Implementation for AI Orchestration System.

This module provides a Redis client for caching memory items and session data
to improve application performance.
"""

import os
import json
import logging
import pickle
from typing import Any, Dict, List, Optional, Set, Union, TypeVar, Generic
import asyncio
from datetime import datetime, timedelta

# Import Redis
try:
    import redis
    from redis import Redis
    from redis.asyncio import Redis as AsyncRedis
    from redis.exceptions import RedisError
except ImportError:
    raise ImportError("Redis library not available. Install with: pip install redis")

# Configure logging
logger = logging.getLogger(__name__)

# Type for cached items
T = TypeVar("T")


class RedisClient:
    """
    Redis client for caching data in the AI Orchestration System.

    This class provides methods for caching and retrieving data using Redis,
    with support for TTL (Time To Live) expiration and key namespacing.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db: int = 0,
        password: Optional[str] = None,
        ssl: bool = False,
        namespace: str = "orchestra:",
        default_ttl: int = 3600,  # 1 hour default
    ):
        """
        Initialize the Redis client.

        Args:
            host: Redis host. Defaults to REDIS_HOST env var or "localhost".
            port: Redis port. Defaults to REDIS_PORT env var or 6379.
            db: Redis DB number. Defaults to 0.
            password: Redis password. Defaults to REDIS_PASSWORD env var or None.
            ssl: Whether to use SSL for Redis connection. Defaults to False.
            namespace: Key namespace prefix. Defaults to "orchestra:".
            default_ttl: Default TTL for cached items in seconds. Defaults to 1 hour.
        """
        self._host = host or os.environ.get("REDIS_HOST", "localhost")
        self._port = port or int(os.environ.get("REDIS_PORT", "6379"))
        self._db = db
        self._password = password or os.environ.get("REDIS_PASSWORD")
        self._ssl = ssl
        self._namespace = namespace
        self._default_ttl = default_ttl
        self._client = None
        self._async_client = None
        self._initialized = False

    def initialize(self) -> None:
        """
        Initialize the Redis client.

        Establishes connection to Redis server.

        Raises:
            ConnectionError: If connection to Redis fails
        """
        if self._initialized:
            return

        try:
            # Create Redis pool
            self._client = redis.Redis(
                host=self._host,
                port=self._port,
                db=self._db,
                password=self._password,
                ssl=self._ssl,
                decode_responses=False,  # We'll handle decoding ourselves
            )

            # Create async Redis client
            self._async_client = redis.asyncio.Redis(
                host=self._host,
                port=self._port,
                db=self._db,
                password=self._password,
                ssl=self._ssl,
                decode_responses=False,  # We'll handle decoding ourselves
            )

            # Test connection
            self._client.ping()

            self._initialized = True
            logger.info(f"Connected to Redis at {self._host}:{self._port}")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise ConnectionError(f"Failed to connect to Redis: {e}")
        except Exception as e:
            logger.error(f"Unexpected error initializing Redis client: {e}")
            raise ConnectionError(f"Failed to connect to Redis: {e}")

    def close(self) -> None:
        """Close Redis client connections."""
        try:
            if self._client:
                self._client.close()

            if self._async_client:
                asyncio.get_event_loop().run_until_complete(self._async_client.close())

            self._initialized = False
            logger.debug("Closed Redis connections")
        except Exception as e:
            logger.warning(f"Error closing Redis connections: {e}")

    def _check_initialized(self) -> None:
        """
        Check if the client is initialized and raise error if not.

        Raises:
            RuntimeError: If the client is not initialized
        """
        if not self._initialized or not self._client or not self._async_client:
            raise RuntimeError("Redis client not initialized. Call initialize() first.")

    def _get_namespaced_key(self, key: str) -> str:
        """
        Add namespace prefix to a key.

        Args:
            key: The original key

        Returns:
            Key with namespace prefix
        """
        return f"{self._namespace}{key}"

    def _serialize(self, data: Any) -> bytes:
        """
        Serialize data for storage in Redis.

        Args:
            data: The data to serialize

        Returns:
            Serialized bytes
        """
        try:
            return pickle.dumps(data)
        except Exception as e:
            logger.error(f"Error serializing data: {e}")
            raise ValueError(f"Failed to serialize data for Redis: {e}")

    def _deserialize(self, data: bytes) -> Any:
        """
        Deserialize data from Redis.

        Args:
            data: The serialized bytes

        Returns:
            Deserialized data

        Raises:
            ValueError: If deserialization fails
        """
        if not data:
            return None

        try:
            return pickle.loads(data)
        except Exception as e:
            logger.error(f"Error deserializing data: {e}")
            raise ValueError(f"Failed to deserialize data from Redis: {e}")

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a key-value pair in Redis with optional TTL.

        Args:
            key: The key to set
            value: The value to store
            ttl: TTL in seconds. If None, uses default_ttl.

        Returns:
            True if successful, False otherwise
        """
        self._check_initialized()

        namespaced_key = self._get_namespaced_key(key)
        ttl = ttl if ttl is not None else self._default_ttl

        try:
            serialized_value = self._serialize(value)
            await self._async_client.set(namespaced_key, serialized_value, ex=ttl)
            return True
        except RedisError as e:
            logger.error(f"Redis error setting key {key}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error setting key {key}: {e}")
            return False

    async def get(self, key: str) -> Any:
        """
        Get a value from Redis.

        Args:
            key: The key to get

        Returns:
            The stored value, or None if not found
        """
        self._check_initialized()

        namespaced_key = self._get_namespaced_key(key)

        try:
            # Get value from Redis
            data = await self._async_client.get(namespaced_key)

            # Deserialize if we got something
            if data:
                return self._deserialize(data)

            return None
        except RedisError as e:
            logger.error(f"Redis error getting key {key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting key {key}: {e}")
            return None

    async def delete(self, key: str) -> bool:
        """
        Delete a key from Redis.

        Args:
            key: The key to delete

        Returns:
            True if the key was deleted, False otherwise
        """
        self._check_initialized()

        namespaced_key = self._get_namespaced_key(key)

        try:
            result = await self._async_client.delete(namespaced_key)
            return result > 0
        except RedisError as e:
            logger.error(f"Redis error deleting key {key}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in Redis.

        Args:
            key: The key to check

        Returns:
            True if the key exists, False otherwise
        """
        self._check_initialized()

        namespaced_key = self._get_namespaced_key(key)

        try:
            return await self._async_client.exists(namespaced_key) > 0
        except RedisError as e:
            logger.error(f"Redis error checking key {key}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking key {key}: {e}")
            return False

    async def set_hash(
        self, key: str, mapping: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        """
        Set a hash map in Redis.

        Args:
            key: The key for the hash
            mapping: Dict of field-value pairs
            ttl: TTL in seconds. If None, uses default_ttl.

        Returns:
            True if successful, False otherwise
        """
        self._check_initialized()

        namespaced_key = self._get_namespaced_key(key)
        ttl = ttl if ttl is not None else self._default_ttl

        try:
            # Serialize each value in the mapping
            serialized_mapping = {k: self._serialize(v) for k, v in mapping.items()}

            # Use pipeline for atomicity
            async with self._async_client.pipeline() as pipe:
                await pipe.hset(namespaced_key, mapping=serialized_mapping)
                await pipe.expire(namespaced_key, ttl)
                await pipe.execute()

            return True
        except RedisError as e:
            logger.error(f"Redis error setting hash {key}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error setting hash {key}: {e}")
            return False

    async def get_hash(self, key: str) -> Dict[str, Any]:
        """
        Get a hash map from Redis.

        Args:
            key: The key for the hash

        Returns:
            Dict of field-value pairs, or empty dict if not found
        """
        self._check_initialized()

        namespaced_key = self._get_namespaced_key(key)

        try:
            # Get all hash fields
            hash_data = await self._async_client.hgetall(namespaced_key)

            if not hash_data:
                return {}

            # Deserialize each value
            result = {}
            for field, value in hash_data.items():
                field_str = field.decode("utf-8") if isinstance(field, bytes) else field
                result[field_str] = self._deserialize(value)

            return result
        except RedisError as e:
            logger.error(f"Redis error getting hash {key}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error getting hash {key}: {e}")
            return {}

    async def set_list(
        self, key: str, values: List[Any], ttl: Optional[int] = None
    ) -> bool:
        """
        Set a list in Redis.

        Args:
            key: The key for the list
            values: List of values to store
            ttl: TTL in seconds. If None, uses default_ttl.

        Returns:
            True if successful, False otherwise
        """
        self._check_initialized()

        namespaced_key = self._get_namespaced_key(key)
        ttl = ttl if ttl is not None else self._default_ttl

        try:
            # Use pipeline for atomicity
            async with self._async_client.pipeline() as pipe:
                # Delete any existing list
                await pipe.delete(namespaced_key)

                # Add all values
                if values:
                    serialized_values = [self._serialize(v) for v in values]
                    await pipe.rpush(namespaced_key, *serialized_values)

                # Set expiration
                await pipe.expire(namespaced_key, ttl)
                await pipe.execute()

            return True
        except RedisError as e:
            logger.error(f"Redis error setting list {key}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error setting list {key}: {e}")
            return False

    async def get_list(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """
        Get a list from Redis.

        Args:
            key: The key for the list
            start: Start index (inclusive)
            end: End index (inclusive), -1 means get all

        Returns:
            List of values, or empty list if not found
        """
        self._check_initialized()

        namespaced_key = self._get_namespaced_key(key)

        try:
            # Get list values from Redis
            values = await self._async_client.lrange(namespaced_key, start, end)

            if not values:
                return []

            # Deserialize each value
            return [self._deserialize(v) for v in values]
        except RedisError as e:
            logger.error(f"Redis error getting list {key}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting list {key}: {e}")
            return []

    async def flush_namespace(self) -> bool:
        """
        Delete all keys with the current namespace.

        Returns:
            True if successful, False otherwise
        """
        self._check_initialized()

        try:
            # Scan for all keys with the namespace prefix
            cursor = b"0"
            namespace_pattern = f"{self._namespace}*"

            keys_to_delete = []

            # Scan and collect keys
            while cursor:
                cursor, keys = await self._async_client.scan(
                    cursor=cursor, match=namespace_pattern, count=100
                )

                cursor = cursor if cursor != b"0" else None

                if keys:
                    keys_to_delete.extend(keys)

            # Delete all found keys if any
            if keys_to_delete:
                await self._async_client.delete(*keys_to_delete)
                logger.info(
                    f"Flushed {len(keys_to_delete)} keys with namespace {self._namespace}"
                )

            return True
        except RedisError as e:
            logger.error(f"Redis error flushing namespace {self._namespace}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error flushing namespace {self._namespace}: {e}")
            return False

    # Conversation history caching methods

    async def cache_conversation_history(
        self,
        user_id: str,
        history_items: List[Any],
        session_id: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Cache conversation history for a user.

        Args:
            user_id: The user ID
            history_items: List of history items
            session_id: Optional session ID
            ttl: TTL in seconds. If None, uses default_ttl.

        Returns:
            True if successful, False otherwise
        """
        cache_key = f"history:{user_id}"
        if session_id:
            cache_key += f":{session_id}"

        return await self.set_list(cache_key, history_items, ttl)

    async def get_cached_conversation_history(
        self, user_id: str, session_id: Optional[str] = None, limit: int = 20
    ) -> List[Any]:
        """
        Get cached conversation history for a user.

        Args:
            user_id: The user ID
            session_id: Optional session ID
            limit: Maximum number of items to retrieve

        Returns:
            List of history items, or empty list if not found
        """
        cache_key = f"history:{user_id}"
        if session_id:
            cache_key += f":{session_id}"

        # Use negative indexing to get most recent items
        start = 0 if limit <= 0 else -limit
        return await self.get_list(cache_key, start=start)

    async def invalidate_conversation_history(
        self, user_id: str, session_id: Optional[str] = None
    ) -> bool:
        """
        Invalidate cached conversation history.

        Args:
            user_id: The user ID
            session_id: Optional session ID

        Returns:
            True if successful, False otherwise
        """
        cache_key = f"history:{user_id}"
        if session_id:
            cache_key += f":{session_id}"

        return await self.delete(cache_key)

    # Session caching methods

    async def cache_session_data(
        self,
        user_id: str,
        session_id: str,
        session_data: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Cache session data.

        Args:
            user_id: The user ID
            session_id: The session ID
            session_data: Session data to cache
            ttl: TTL in seconds. If None, uses default_ttl.

        Returns:
            True if successful, False otherwise
        """
        cache_key = f"session:{user_id}:{session_id}"
        return await self.set_hash(cache_key, session_data, ttl)

    async def get_cached_session_data(
        self, user_id: str, session_id: str
    ) -> Dict[str, Any]:
        """
        Get cached session data.

        Args:
            user_id: The user ID
            session_id: The session ID

        Returns:
            Dict of session data, or empty dict if not found
        """
        cache_key = f"session:{user_id}:{session_id}"
        return await self.get_hash(cache_key)

    async def invalidate_session_data(self, user_id: str, session_id: str) -> bool:
        """
        Invalidate cached session data.

        Args:
            user_id: The user ID
            session_id: The session ID

        Returns:
            True if successful, False otherwise
        """
        cache_key = f"session:{user_id}:{session_id}"
        return await self.delete(cache_key)

    # Health check method

    async def ping(self) -> bool:
        """
        Check Redis connection health.

        Returns:
            True if Redis is reachable, False otherwise
        """
        try:
            self._check_initialized()
            return await self._async_client.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
