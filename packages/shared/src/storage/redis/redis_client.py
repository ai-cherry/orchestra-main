"""
Redis Client Implementation for AI Orchestration System.

This module provides a Redis client for caching memory items and session data
to improve application performance.
"""

import os
import json
import logging
import pickle
import enum
import traceback
from typing import Any, Dict, List, Optional, Set, Union, TypeVar, Generic, Callable
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


class CircuitState(enum.Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, operations are blocked
    HALF_OPEN = "half_open"  # Testing if service is back online


class RedisClient:
    """
    Redis client for caching data in the AI Orchestration System.

    This class provides methods for caching and retrieving data using Redis,
    with support for TTL (Time To Live) expiration and key namespacing.
    Implements circuit breaker pattern for improved resilience.
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
        circuit_failure_threshold: int = 3,
        circuit_recovery_timeout: int = 30,
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
            circuit_failure_threshold: Number of failures before opening circuit. Defaults to 3.
            circuit_recovery_timeout: Seconds to wait before testing recovery. Defaults to 30.
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
        self._pool = None

        # Circuit breaker settings
        self.circuit_state = CircuitState.CLOSED
        self.circuit_failure_threshold = circuit_failure_threshold
        self.circuit_recovery_timeout = circuit_recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None

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
            self._pool = redis.ConnectionPool(
                host=self._host,
                port=self._port,
                db=self._db,
                password=self._password,
                ssl=self._ssl,
                decode_responses=False,  # We'll handle decoding ourselves
            )

            # Create Redis client using the pool
            self._client = redis.Redis(connection_pool=self._pool)

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

            # Reset circuit breaker state
            self.circuit_state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None

            self._initialized = True
            logger.info(f"Connected to Redis at {self._host}:{self._port}")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise ConnectionError(f"Failed to connect to Redis: {e}")
        except Exception as e:
            logger.error(f"Unexpected error initializing Redis client: {e}")
            raise ConnectionError(f"Failed to connect to Redis: {e}")

    async def close(self) -> None:
        """Close the Redis client and release resources."""
        if self._pool:
            try:
                self._pool.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting Redis pool: {e}")
            finally:
                self._pool = None

        if self._client:
            try:
                self._client.close()
            except Exception as e:
                logger.warning(f"Error closing Redis client: {e}")

        if self._async_client:
            try:
                await self._async_client.close()
            except Exception as e:
                logger.warning(f"Error closing async Redis client: {e}")

        self._client = None
        self._async_client = None
        self._initialized = False
        logger.debug("Redis client closed")

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

    async def _get_client(self) -> AsyncRedis:
        """
        Get the Redis client, checking circuit breaker state.

        Returns:
            Redis async client

        Raises:
            ConnectionError: If circuit breaker is open
        """
        self._check_initialized()

        # Check circuit state
        if self.circuit_state == CircuitState.OPEN:
            # Check if recovery timeout has elapsed
            if (
                self.last_failure_time
                and (datetime.utcnow() - self.last_failure_time).total_seconds()
                > self.circuit_recovery_timeout
            ):
                # Try recovery
                logger.info("Circuit half-open, testing Redis connection")
                self.circuit_state = CircuitState.HALF_OPEN
            else:
                # Circuit still open
                logger.warning("Circuit breaker open, Redis operations suspended")
                raise ConnectionError(
                    "Circuit breaker open, Redis operations suspended"
                )

        return self._async_client

    async def _execute_with_circuit_breaker(self, operation: Callable) -> Any:
        """
        Execute an operation with circuit breaker pattern.

        Args:
            operation: Async callable operation to execute

        Returns:
            Result of the operation

        Raises:
            Various exceptions depending on the operation
        """
        try:
            # Get client and execute operation
            client = await self._get_client()
            result = await operation(client)

            # If we get here in HALF_OPEN state, close the circuit
            if self.circuit_state == CircuitState.HALF_OPEN:
                self.circuit_state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info("Circuit closed, Redis operations resumed")

            return result

        except Exception as e:
            # Track failure
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()

            # Check if we should open the circuit
            if (
                self.circuit_state == CircuitState.CLOSED
                or self.circuit_state == CircuitState.HALF_OPEN
            ) and self.failure_count >= self.circuit_failure_threshold:
                self.circuit_state = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker opened after {self.failure_count} failures"
                )

            # Map exceptions
            if isinstance(e, redis.ConnectionError):
                raise ConnectionError(f"Redis connection error: {e}")
            elif isinstance(e, redis.TimeoutError):
                raise TimeoutError(f"Redis operation timed out: {e}")
            elif isinstance(e, redis.RedisError):
                raise OperationError(f"Redis operation failed: {e}")
            else:
                raise StorageError(f"Redis error: {e}")

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

        async def _operation(client: AsyncRedis) -> bool:
            serialized_value = self._serialize(value)
            await client.set(namespaced_key, serialized_value, ex=ttl)
            return True

        try:
            return await self._execute_with_circuit_breaker(_operation)
        except Exception as e:
            logger.error(f"Error setting key {key}: {e}")
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

        async def _operation(client: AsyncRedis) -> Any:
            # Get value from Redis
            data = await client.get(namespaced_key)

            # Deserialize if we got something
            if data:
                return self._deserialize(data)

            return None

        try:
            return await self._execute_with_circuit_breaker(_operation)
        except Exception as e:
            logger.error(f"Error getting key {key}: {e}")
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

        async def _operation(client: AsyncRedis) -> bool:
            result = await client.delete(namespaced_key)
            return result > 0

        try:
            return await self._execute_with_circuit_breaker(_operation)
        except Exception as e:
            logger.error(f"Error deleting key {key}: {e}")
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

        async def _operation(client: AsyncRedis) -> bool:
            return await client.exists(namespaced_key) > 0

        try:
            return await self._execute_with_circuit_breaker(_operation)
        except Exception as e:
            logger.error(f"Error checking key {key}: {e}")
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

        async def _operation(client: AsyncRedis) -> bool:
            # Serialize each value in the mapping
            serialized_mapping = {k: self._serialize(v) for k, v in mapping.items()}

            # Use pipeline for atomicity
            async with client.pipeline() as pipe:
                await pipe.hset(namespaced_key, mapping=serialized_mapping)
                await pipe.expire(namespaced_key, ttl)
                await pipe.execute()

            return True

        try:
            return await self._execute_with_circuit_breaker(_operation)
        except Exception as e:
            logger.error(f"Error setting hash {key}: {e}")
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

        async def _operation(client: AsyncRedis) -> Dict[str, Any]:
            # Get all hash fields
            hash_data = await client.hgetall(namespaced_key)

            if not hash_data:
                return {}

            # Deserialize each value
            result = {}
            for field, value in hash_data.items():
                field_str = field.decode("utf-8") if isinstance(field, bytes) else field
                result[field_str] = self._deserialize(value)

            return result

        try:
            return await self._execute_with_circuit_breaker(_operation)
        except Exception as e:
            logger.error(f"Error getting hash {key}: {e}")
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

        async def _operation(client: AsyncRedis) -> bool:
            # Use pipeline for atomicity
            async with client.pipeline() as pipe:
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

        try:
            return await self._execute_with_circuit_breaker(_operation)
        except Exception as e:
            logger.error(f"Error setting list {key}: {e}")
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

        async def _operation(client: AsyncRedis) -> List[Any]:
            # Get list values from Redis
            values = await client.lrange(namespaced_key, start, end)

            if not values:
                return []

            # Deserialize each value
            return [self._deserialize(v) for v in values]

        try:
            return await self._execute_with_circuit_breaker(_operation)
        except Exception as e:
            logger.error(f"Error getting list {key}: {e}")
            return []

    async def flush_namespace(self) -> bool:
        """
        Delete all keys with the current namespace.

        Returns:
            True if successful, False otherwise
        """
        self._check_initialized()

        async def _operation(client: AsyncRedis) -> bool:
            # Scan for all keys with the namespace prefix
            cursor = b"0"
            namespace_pattern = f"{self._namespace}*"

            keys_to_delete = []

            # Scan and collect keys
            while cursor:
                cursor, keys = await client.scan(
                    cursor=cursor, match=namespace_pattern, count=100
                )

                cursor = cursor if cursor != b"0" else None

                if keys:
                    keys_to_delete.extend(keys)

            # Delete all found keys if any
            if keys_to_delete:
                await client.delete(*keys_to_delete)
                logger.info(
                    f"Flushed {len(keys_to_delete)} keys with namespace {self._namespace}"
                )

            return True

        try:
            return await self._execute_with_circuit_breaker(_operation)
        except Exception as e:
            logger.error(f"Error flushing namespace {self._namespace}: {e}")
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
        key = f"history:{user_id}"
        if session_id:
            key = f"{key}:{session_id}"

        return await self.set_list(key, history_items, ttl)

    async def get_cached_conversation_history(
        self, user_id: str, session_id: Optional[str] = None
    ) -> List[Any]:
        """
        Get cached conversation history for a user.

        Args:
            user_id: The user ID
            session_id: Optional session ID

        Returns:
            List of history items, or empty list if not found
        """
        key = f"history:{user_id}"
        if session_id:
            key = f"{key}:{session_id}"

        return await self.get_list(key)

    async def invalidate_conversation_history(
        self, user_id: str, session_id: Optional[str] = None
    ) -> bool:
        """
        Invalidate cached conversation history for a user.

        Args:
            user_id: The user ID
            session_id: Optional session ID

        Returns:
            True if successful, False otherwise
        """
        key = f"history:{user_id}"
        if session_id:
            key = f"{key}:{session_id}"

        return await self.delete(key)

    # Session data caching methods

    async def cache_session_data(
        self,
        user_id: str,
        session_id: str,
        data: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Cache session data for a user.

        Args:
            user_id: The user ID
            session_id: The session ID
            data: Session data to cache
            ttl: TTL in seconds. If None, uses default_ttl.

        Returns:
            True if successful, False otherwise
        """
        key = f"session:{user_id}:{session_id}"
        return await self.set(key, data, ttl)

    async def get_cached_session_data(
        self, user_id: str, session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached session data for a user.

        Args:
            user_id: The user ID
            session_id: The session ID

        Returns:
            Session data, or None if not found
        """
        key = f"session:{user_id}:{session_id}"
        return await self.get(key)

    async def invalidate_session_data(self, user_id: str, session_id: str) -> bool:
        """
        Invalidate cached session data for a user.

        Args:
            user_id: The user ID
            session_id: The session ID

        Returns:
            True if successful, False otherwise
        """
        key = f"session:{user_id}:{session_id}"
        return await self.delete(key)

    async def ping(self) -> bool:
        """
        Ping the Redis server to check connectivity.

        Returns:
            True if connected, False otherwise
        """
        try:

            async def _operation(client: AsyncRedis) -> bool:
                await client.ping()
                return True

            return await self._execute_with_circuit_breaker(_operation)
        except Exception as e:
            logger.warning(f"Redis ping failed: {e}")
            return False

    def get_circuit_state(self) -> Dict[str, Any]:
        """
        Get the current circuit breaker state.

        Returns:
            Dictionary with circuit breaker state information
        """
        return {
            "state": self.circuit_state.value,
            "failure_count": self.failure_count,
            "last_failure": self.last_failure_time.isoformat()
            if self.last_failure_time
            else None,
            "threshold": self.circuit_failure_threshold,
            "recovery_timeout": self.circuit_recovery_timeout,
        }
