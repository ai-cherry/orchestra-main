#!/usr/bin/env python3
"""
idempotency.py - Idempotency Utilities for MCP

This module provides utilities for implementing idempotent operations in the MCP system.
It includes key generation, result caching, and decorators for making functions idempotent.
"""

import asyncio
import functools
import hashlib
import json
import time
import uuid
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar, Union, cast

# Import Redis with fallback
try:
    import redis.asyncio as redis

    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

from .structured_logging import get_logger

logger = get_logger(__name__)

# Type variables for function decorators
T = TypeVar("T")
R = TypeVar("R")

class IdempotencyKey:
    """Generate and validate idempotency keys."""

    @staticmethod
    def generate() -> str:
        """Generate a new idempotency key.

        Returns:
            A new UUID-based idempotency key
        """
        return str(uuid.uuid4())

    @staticmethod
    def from_request(request_data: Dict[str, Any]) -> str:
        """Generate an idempotency key from request data.

        Args:
            request_data: The request data to generate a key from

        Returns:
            A hash-based idempotency key
        """
        # Sort keys for consistent hashing
        request_str = json.dumps(request_data, sort_keys=True)
        return hashlib.sha256(request_str.encode()).hexdigest()

    @staticmethod
    def from_args(*args: Any, **kwargs: Any) -> str:
        """Generate an idempotency key from function arguments.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            A hash-based idempotency key
        """
        # Convert args and kwargs to a dictionary
        data = {"args": args, "kwargs": kwargs}
        return IdempotencyKey.from_request(data)

    @staticmethod
    def is_valid(key: str) -> bool:
        """Check if an idempotency key is valid.

        Args:
            key: The idempotency key to check

        Returns:
            True if the key is valid
        """
        # UUID format check
        if len(key) == 36 and key.count("-") == 4:
            try:
                uuid.UUID(key)
                return True
            except ValueError:
                pass

        # SHA-256 hash format check (64 hex characters)
        if len(key) == 64 and all(c in "0123456789abcdef" for c in key.lower()):
            return True

        return False

class InMemoryIdempotencyStore:
    """In-memory store for idempotency keys and their results."""

    def __init__(self, ttl_seconds: int = 86400):
        """Initialize the in-memory idempotency store.

        Args:
            ttl_seconds: Time-to-live for keys in seconds (default: 24 hours)
        """
        self.store: Dict[str, Dict[str, Any]] = {}
        self.in_progress: Dict[str, float] = {}
        self.ttl_seconds = ttl_seconds

    async def get_result(self, key: str) -> Optional[Dict[str, Any]]:
        """Get the result for an idempotency key.

        Args:
            key: The idempotency key

        Returns:
            The stored result, or None if not found
        """
        self._cleanup_expired()

        if key in self.store:
            entry = self.store[key]
            # Check if the entry has expired
            if entry["timestamp"] + self.ttl_seconds > time.time():
                return entry["result"]
            # Remove expired entry
            del self.store[key]

        return None

    async def store_result(self, key: str, result: Dict[str, Any]) -> bool:
        """Store the result for an idempotency key.

        Args:
            key: The idempotency key
            result: The result to store

        Returns:
            True if the result was stored
        """
        self.store[key] = {"result": result, "timestamp": time.time()}

        # Remove from in-progress if present
        if key in self.in_progress:
            del self.in_progress[key]

        return True

    async def mark_in_progress(self, key: str) -> bool:
        """Mark an idempotency key as in progress.

        Args:
            key: The idempotency key

        Returns:
            True if the key was marked as in progress, False if already in progress
        """
        self._cleanup_expired()

        # Check if already in progress
        if key in self.in_progress:
            # Check if the in-progress marker has expired
            if self.in_progress[key] + 300 > time.time():
                return False

        # Mark as in progress
        self.in_progress[key] = time.time()
        return True

    async def clear_in_progress(self, key: str) -> bool:
        """Clear the in-progress marker for an idempotency key.

        Args:
            key: The idempotency key

        Returns:
            True if the marker was cleared
        """
        if key in self.in_progress:
            del self.in_progress[key]
        return True

    def _cleanup_expired(self) -> None:
        """Clean up expired entries."""
        now = time.time()

        # Clean up expired results
        expired_keys = [key for key, entry in self.store.items() if entry["timestamp"] + self.ttl_seconds <= now]
        for key in expired_keys:
            del self.store[key]

        # Clean up expired in-progress markers
        expired_markers = [key for key, timestamp in self.in_progress.items() if timestamp + 300 <= now]
        for key in expired_markers:
            del self.in_progress[key]

class RedisIdempotencyStore:
    """Redis-based store for idempotency keys and their results."""

    def __init__(
        self,
        redis_client: redis.Redis,
        ttl_seconds: int = 86400,
        prefix: str = "idempotency:",
    ):
        """Initialize the Redis idempotency store.

        Args:
            redis_client: Redis client
            ttl_seconds: Time-to-live for keys in seconds (default: 24 hours)
            prefix: Prefix for Redis keys
        """
        if not HAS_REDIS:
            raise ImportError("Redis package not installed. Install with 'pip install redis'")

        self.redis = redis_client
        self.ttl_seconds = ttl_seconds
        self.prefix = prefix

    async def get_result(self, key: str) -> Optional[Dict[str, Any]]:
        """Get the result for an idempotency key.

        Args:
            key: The idempotency key

        Returns:
            The stored result, or None if not found
        """
        try:
            result_json = await self.redis.get(f"{self.prefix}{key}")
            if result_json:
                return json.loads(result_json)
            return None
        except Exception as e:
            logger.error(f"Error getting idempotency result: {e}")
            return None

    async def store_result(self, key: str, result: Dict[str, Any]) -> bool:
        """Store the result for an idempotency key.

        Args:
            key: The idempotency key
            result: The result to store

        Returns:
            True if the result was stored
        """
        try:
            result_json = json.dumps(result)
            await self.redis.set(f"{self.prefix}{key}", result_json, ex=self.ttl_seconds)

            # Clear in-progress marker
            await self.clear_in_progress(key)

            return True
        except Exception as e:
            logger.error(f"Error storing idempotency result: {e}")
            return False

    async def mark_in_progress(self, key: str) -> bool:
        """Mark an idempotency key as in progress.

        Args:
            key: The idempotency key

        Returns:
            True if the key was marked as in progress, False if already in progress
        """
        try:
            # Use a short TTL for in-progress markers to prevent deadlocks
            in_progress_key = f"{self.prefix}{key}:in_progress"
            result = await self.redis.set(in_progress_key, "1", ex=300, nx=True)
            return bool(result)
        except Exception as e:
            logger.error(f"Error marking idempotency key as in progress: {e}")
            return False

    async def clear_in_progress(self, key: str) -> bool:
        """Clear the in-progress marker for an idempotency key.

        Args:
            key: The idempotency key

        Returns:
            True if the marker was cleared
        """
        try:
            in_progress_key = f"{self.prefix}{key}:in_progress"
            await self.redis.delete(in_progress_key)
            return True
        except Exception as e:
            logger.error(f"Error clearing in-progress marker: {e}")
            return False

class IdempotencyManager:
    """Manager for idempotent operations."""

    def __init__(
        self,
        store: Optional[Union[InMemoryIdempotencyStore, RedisIdempotencyStore]] = None,
        ttl_seconds: int = 86400,
    ):
        """Initialize the idempotency manager.

        Args:
            store: The idempotency store to use
            ttl_seconds: Time-to-live for keys in seconds (default: 24 hours)
        """
        self.store = store or InMemoryIdempotencyStore(ttl_seconds)
        self.ttl_seconds = ttl_seconds

    @staticmethod
    def create_with_redis(
        redis_url: str, ttl_seconds: int = 86400, prefix: str = "idempotency:"
    ) -> "IdempotencyManager":
        """Create an idempotency manager with a Redis store.

        Args:
            redis_url: Redis connection URL
            ttl_seconds: Time-to-live for keys in seconds
            prefix: Prefix for Redis keys

        Returns:
            An idempotency manager with a Redis store

        Raises:
            ImportError: If Redis is not installed
        """
        if not HAS_REDIS:
            raise ImportError("Redis package not installed. Install with 'pip install redis'")

        redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            retry_on_timeout=True,
        )

        store = RedisIdempotencyStore(redis_client, ttl_seconds, prefix)
        return IdempotencyManager(store, ttl_seconds)

    async def execute_idempotent(self, key: str, func: Callable[..., Awaitable[R]], *args: Any, **kwargs: Any) -> R:
        """Execute a function idempotently.

        Args:
            key: The idempotency key
            func: The function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            The function result

        Raises:
            Exception: If the function raises an exception
        """
        # Check if we already have a result
        existing_result = await self.store.get_result(key)
        if existing_result:
            logger.info(f"Using cached result for idempotency key: {key}")
            return cast(R, existing_result.get("result"))

        # Try to mark as in progress
        if not await self.store.mark_in_progress(key):
            # Another process is already handling this request
            logger.info(f"Request with key {key} is already being processed")

            # Wait and check for result
            for i in range(10):  # Try 10 times with exponential backoff
                await asyncio.sleep(0.5 * (2**i))  # Exponential backoff
                result = await self.store.get_result(key)
                if result:
                    return cast(R, result.get("result"))

            # If we still don't have a result, proceed anyway
            logger.warning(f"No result found after waiting for idempotency key: {key}")
            await self.store.clear_in_progress(key)

        try:
            # Execute the function
            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()

            # Store the result
            await self.store.store_result(
                key,
                {
                    "result": result,
                    "timestamp": datetime.now().isoformat(),
                    "execution_time": end_time - start_time,
                },
            )

            return result
        except Exception as e:
            # Store the error
            await self.store.store_result(
                key,
                {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            # Re-raise the exception
            raise
        finally:
            # Clear in-progress marker
            await self.store.clear_in_progress(key)

def idempotent(
    store: Optional[Union[InMemoryIdempotencyStore, RedisIdempotencyStore]] = None,
    key_func: Optional[Callable[..., str]] = None,
    ttl_seconds: int = 86400,
) -> Callable[[Callable[..., Awaitable[R]]], Callable[..., Awaitable[R]]]:
    """Decorator to make an async function idempotent.

    Args:
        store: The idempotency store to use
        key_func: Function to generate idempotency keys from arguments
        ttl_seconds: Time-to-live for keys in seconds

    Returns:
        A decorator function
    """
    idempotency_manager = IdempotencyManager(store, ttl_seconds)

    def decorator(func: Callable[..., Awaitable[R]]) -> Callable[..., Awaitable[R]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> R:
            # Extract idempotency key from kwargs or generate one
            idempotency_key = kwargs.pop("idempotency_key", None)

            if not idempotency_key:
                if key_func:
                    # Use the provided key function
                    idempotency_key = key_func(*args, **kwargs)
                else:
                    # Generate from arguments
                    idempotency_key = IdempotencyKey.from_args(*args, **kwargs)

            return await idempotency_manager.execute_idempotent(idempotency_key, func, *args, **kwargs)

        return wrapper

    return decorator

# Singleton instance for global use
_default_manager: Optional[IdempotencyManager] = None

def get_idempotency_manager() -> IdempotencyManager:
    """Get the default IdempotencyManager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = IdempotencyManager()
    return _default_manager

def configure_idempotency(
    redis_url: Optional[str] = None,
    ttl_seconds: int = 86400,
    prefix: str = "idempotency:",
) -> None:
    """Configure the default idempotency manager.

    Args:
        redis_url: Redis connection URL, or None for in-memory storage
        ttl_seconds: Time-to-live for keys in seconds
        prefix: Prefix for Redis keys
    """
    global _default_manager

    if redis_url and HAS_REDIS:
        _default_manager = IdempotencyManager.create_with_redis(redis_url, ttl_seconds, prefix)
    else:
        _default_manager = IdempotencyManager(InMemoryIdempotencyStore(ttl_seconds), ttl_seconds)

    logger.info(f"Configured idempotency manager with TTL: {ttl_seconds} seconds")

# Convenience decorator using the default manager
def default_idempotent(
    key_func: Optional[Callable[..., str]] = None,
) -> Callable[[Callable[..., Awaitable[R]]], Callable[..., Awaitable[R]]]:
    """Decorator to make an async function idempotent using the default manager.

    Args:
        key_func: Function to generate idempotency keys from arguments

    Returns:
        A decorator function
    """
    return idempotent(get_idempotency_manager().store, key_func)
