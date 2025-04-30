r"""
Concrete Memory Manager Implementation for AI Orchestration System.

This module provides a concrete implementation of the MemoryManager interface
that uses Firestore for persistent storage and Redis for caching.
"""

import os
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import asyncio

from packages.shared.src.memory.base_memory_manager import BaseMemoryManager # New import
from packages.shared.src.memory.memory_interface import MemoryInterface # New import
from .memory_types import MemoryHealth # Updated import
from packages.shared.src.models.base_models import MemoryItem, AgentData, PersonaConfig
from packages.shared.src.storage.firestore.firestore_memory import (
    FirestoreMemoryManager,
    StorageError,
    ValidationError,
)
from packages.shared.src.storage.redis.redis_client import RedisClient

# Configure logging
logger = logging.getLogger(__name__)


class FirestoreV1MemoryManager(BaseMemoryManager): # Renamed class and changed base
    """
    Firestore V1 memory manager implementation using Firestore and Redis.

    This class provides a concrete implementation of the BaseMemoryManager interface
    that uses Firestore V1 for persistent storage and Redis for caching.
    """

    def __init__(
        self,
        firestore_memory: FirestoreMemoryManager, # Injected instance
        redis_host: Optional[str] = None,
        redis_port: Optional[int] = None,
        redis_password: Optional[str] = None,
        cache_ttl: int = 3600,  # 1 hour default
    ):
        """
        Initialize the Firestore V1 memory manager.

        Args:
            firestore_memory: An initialized FirestoreMemoryManager instance.
            redis_host: Optional Redis host.
            redis_port: Optional Redis port.
            redis_password: Optional Redis password.
            cache_ttl: Cache TTL in seconds. Defaults to 1 hour.
        """
        # Use injected Firestore instance
        self._firestore = firestore_memory

        self._redis = RedisClient(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            default_ttl=cache_ttl,
        )

        self._cache_ttl = cache_ttl
        self._initialized = False # Keep for Redis initialization status
        self._redis_available = False

        # Track errors for health monitoring
        self._error_count = 0
        self._last_error = None
        self._max_errors_before_unhealthy = 5

    def initialize(self) -> None:
        """
        Initialize the Firestore V1 memory manager.

        This method initializes the Redis backend. Firestore is assumed to be
        initialized before being injected. If Redis initialization fails,
        the manager will operate without caching.
        """
        if self._initialized:
            return

        # Try to initialize Redis (optional)
        try:
            self._redis.initialize()
            self._redis_available = True
            logger.info("Redis cache initialized for FirestoreV1MemoryManager")
        except Exception as e:
            self._redis_available = False
            logger.warning(
                f"Redis cache initialization failed for FirestoreV1MemoryManager: {e}. Operating without caching."
            )

        self._initialized = True

    def close(self) -> None:
        """
        Close the memory manager and release resources.

        This method closes both the Firestore and Redis backends.
        """
        try:
            if self._firestore:
                self._firestore.close()
                logger.debug("Closed Firestore connection")
        except Exception as e:
            logger.warning(f"Error closing Firestore connection: {e}")

        try:
            if self._redis and self._redis_available:
                self._redis.close()
                logger.debug("Closed Redis connection")
        except Exception as e:
            logger.warning(f"Error closing Redis connection: {e}")

        self._initialized = False
        self._redis_available = False

    def _check_initialized(self) -> None:
        """
        Check if the memory manager is initialized.

        Raises:
            RuntimeError: If the memory manager is not initialized
        """
        if not self._initialized:
            raise RuntimeError(
                "Memory manager not initialized. Call initialize() first."
            )

    def _track_error(self, error: Exception) -> None:
        """
        Track error occurrences for health monitoring.

        Args:
            error: Exception that occurred
        """
        self._error_count += 1
        self._last_error = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": type(error).__name__,
            "message": str(error),
        }
        logger.debug(f"Tracked memory error: {type(error).__name__}: {str(error)}")

    async def add_memory_item(self, item: MemoryItem) -> str:
        """
        Add a memory item to storage.

        Args:
            item: The memory item to store

        Returns:
            The ID of the created memory item

        Raises:
            ValidationError: If the item fails validation
            StorageError: If the storage operation fails
        """
        self._check_initialized()

        # Generate ID if not provided
        if not item.id:
            item.id = str(uuid.uuid4())

        # Store in Firestore
        try:
            item_id = await self._firestore.add_memory_item(item)
        except Exception as e:
            self._track_error(e)
            raise

        # Cache in Redis if available
        if self._redis_available and item.item_type == "conversation":
            try:
                # Get current cached history
                cache_key = f"history:{item.user_id}"
                if item.session_id:
                    cache_key += f":{item.session_id}"

                history = await self._redis.get_cached_conversation_history(
                    user_id=item.user_id, session_id=item.session_id
                )

                # Add new item and update cache
                history.append(item)
                await self._redis.cache_conversation_history(
                    user_id=item.user_id,
                    history_items=history,
                    session_id=item.session_id,
                    ttl=self._cache_ttl,
                )

                logger.debug(f"Cached memory item {item_id} for user {item.user_id}")
            except Exception as e:
                # Log error but continue (Redis is optional)
                logger.warning(f"Failed to cache memory item: {e}")
                self._track_error(e)

        return item_id

    async def get_memory_item(self, item_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a specific memory item by ID.

        Args:
            item_id: The ID of the item to retrieve

        Returns:
            The memory item if found, None otherwise

        Raises:
            StorageError: If the retrieval operation fails
        """
        self._check_initialized()

        # Get from Firestore (no caching for individual items)
        try:
            return await self._firestore.get_memory_item(item_id)
        except Exception as e:
            if not str(e).startswith(
                "Item not found"
            ):  # Don't track "not found" as an error
                self._track_error(e)
            raise

    async def get_conversation_history(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[MemoryItem]:
        """
        Retrieve conversation history for a user.

        Args:
            user_id: The user ID to get history for
            session_id: Optional session ID to filter by
            limit: Maximum number of items to retrieve
            filters: Optional filters to apply

        Returns:
            List of memory items representing the conversation history

        Raises:
            StorageError: If the retrieval operation fails
        """
        self._check_initialized()

        # Try to get from Redis cache if available and no custom filters
        if self._redis_available and not filters:
            try:
                cached_history = await self._redis.get_cached_conversation_history(
                    user_id=user_id, session_id=session_id, limit=limit
                )

                if cached_history:
                    logger.debug(
                        f"Retrieved cached conversation history for user {user_id}"
                    )
                    return cached_history
            except Exception as e:
                # Log error but continue with Firestore (Redis is optional)
                logger.warning(f"Failed to get cached conversation history: {e}")
                self._track_error(e)

        # Get from Firestore
        try:
            history = await self._firestore.get_conversation_history(
                user_id=user_id, session_id=session_id, limit=limit, filters=filters
            )
        except Exception as e:
            self._track_error(e)
            raise

        # Cache in Redis if available and no custom filters
        if self._redis_available and not filters:
            try:
                await self._redis.cache_conversation_history(
                    user_id=user_id,
                    history_items=history,
                    session_id=session_id,
                    ttl=self._cache_ttl,
                )
                logger.debug(f"Cached conversation history for user {user_id}")
            except Exception as e:
                # Log error but continue (Redis is optional)
                logger.warning(f"Failed to cache conversation history: {e}")
                self._track_error(e)

        return history

    async def semantic_search(
        self,
        user_id: str,
        query_embedding: List[float],
        persona_context: Optional[PersonaConfig] = None,
        top_k: int = 5,
    ) -> List[MemoryItem]:
        """
        Perform semantic search using vector embeddings.

        Args:
            user_id: The user ID to search memories for
            query_embedding: The vector embedding of the query
            persona_context: Optional persona context for personalized results
            top_k: Maximum number of results to return

        Returns:
            List of memory items ordered by relevance

        Raises:
            ValidationError: If the query embedding has invalid dimensions
            StorageError: If the search operation fails
        """
        self._check_initialized()

        # Semantic search is always performed on Firestore (no caching)
        try:
            return await self._firestore.semantic_search(
                user_id=user_id,
                query_embedding=query_embedding,
                persona_context=persona_context,
                top_k=top_k,
            )
        except Exception as e:
            self._track_error(e)
            raise

    async def add_raw_agent_data(self, data: AgentData) -> str:
        """
        Store raw agent data.

        Args:
            data: The agent data to store

        Returns:
            The ID of the stored data

        Raises:
            ValidationError: If the data fails validation
            StorageError: If the storage operation fails
        """
        self._check_initialized()

        # Store in Firestore (no caching for agent data)
        try:
            return await self._firestore.add_raw_agent_data(data)
        except Exception as e:
            self._track_error(e)
            raise

    async def check_duplicate(self, item: MemoryItem) -> bool:
        """
        Check if a memory item already exists in storage.

        Args:
            item: The memory item to check for duplicates

        Returns:
            True if a duplicate exists, False otherwise

        Raises:
            StorageError: If the check operation fails
        """
        self._check_initialized()

        # Check in Firestore (no caching for duplicate check)
        try:
            return await self._firestore.check_duplicate(item)
        except Exception as e:
            self._track_error(e)
            raise

    async def cleanup_expired_items(self) -> int:
        """
        Remove expired items from storage.

        Returns:
            Number of items removed

        Raises:
            StorageError: If the cleanup operation fails
        """
        self._check_initialized()

        # Clean up in Firestore
        try:
            count = await self._firestore.cleanup_expired_items()
        except Exception as e:
            self._track_error(e)
            raise

        # Clear Redis cache if available
        if self._redis_available:
            try:
                # Since we don't know which items were expired, flush the entire cache
                await self._redis.flush_namespace()
                logger.info("Flushed Redis cache after cleanup")
            except Exception as e:
                # Log error but continue (Redis is optional)
                logger.warning(f"Failed to flush Redis cache: {e}")
                self._track_error(e)

        return count

    async def health_check(self) -> MemoryHealth:
        """
        Check the health of storage backends.

        This method performs comprehensive health checks on both Firestore
        and Redis backends, providing detailed status information.

        Returns:
            MemoryHealth: Dictionary with detailed health status information
        """
        health: MemoryHealth = {
            "status": "healthy",
            "firestore": False,
            "redis": False,
            "error_count": self._error_count,
            "details": {},
        }

        if self._last_error:
            health["last_error"] = self._last_error["timestamp"]
            health["details"]["last_error"] = self._last_error

        # Check if initialized
        if not self._initialized:
            health["status"] = "unhealthy"
            health["details"]["initialization"] = "Memory manager not initialized"
            return health

        # Check Firestore
        firestore_ok = False
        try:
            # Check Firestore by getting a non-existent item (should return None or raise "not found")
            await self._firestore.get_memory_item("health-check-non-existent")
            firestore_ok = True
        except Exception as e:
            # If it's just a "not found" error, that's actually good
            if str(e).startswith("Item not found"):
                firestore_ok = True
                health["details"][
                    "firestore_check"
                ] = "Successfully verified item not found"
            else:
                health["details"]["firestore_error"] = str(e)
                logger.warning(f"Firestore health check failed: {e}")

        health["firestore"] = firestore_ok

        # Check Redis if available
        redis_ok = False
        if self._redis_available:
            try:
                # Check Redis with ping
                redis_ok = await self._redis.ping()
                if redis_ok:
                    health["details"]["redis_check"] = "Ping successful"
            except Exception as e:
                health["details"]["redis_error"] = str(e)
                logger.warning(f"Redis health check failed: {e}")
        else:
            health["details"]["redis"] = "Redis not configured"

        health["redis"] = redis_ok

        # Determine overall health status
        if not firestore_ok:
            health["status"] = "unhealthy"
        elif self._redis_available and not redis_ok:
            health["status"] = "degraded"
        elif self._error_count >= self._max_errors_before_unhealthy:
            health["status"] = "degraded"
            health["details"][
                "reason"
            ] = f"High error rate ({self._error_count} errors)"

        return health
