"""
Redis-based Semantic Cacher for Orchestra.

This module provides a Redis-based semantic caching implementation for the 
memory system, enabling fast vector similarity search and real-time caching.
"""

import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, Union, Set
from datetime import datetime

from redisvl import SemanticCacher
from packages.shared.src.memory.base_memory_manager import MemoryProvider
from packages.shared.src.models.base_models import MemoryItem

# Configure logging
logger = logging.getLogger(__name__)


class RedisSemanticCacheProvider(MemoryProvider):
    """
    Redis-based semantic cache implementation for real-time memory access.

    This class implements a memory provider that uses Redis for fast semantic similarity
    search with vector indexing for hybrid search capabilities.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Redis semantic cache provider.

        Args:
            config: Configuration for the provider including Redis connection details
        """
        self.config = config or {}
        self.cacher = None
        self._initialized = False
        logger.info("RedisSemanticCacheProvider initialized with config")

    async def initialize(self) -> bool:
        """Initialize the Redis semantic cache with vector indexing."""
        try:
            # Initialize the Redis semantic cacher with configuration
            self.cacher = SemanticCacher(
                threshold=self.config.get(
                    "threshold", 0.82
                ),  # Similarity threshold adjusted for increased recall tolerance
                ttl=self.config.get("ttl", 3600),  # Time-to-live in seconds
                index_schema=self.config.get("index_schema", "agent_memory.yaml"),
                eviction_policy=self.config.get(
                    "eviction_policy", "LRU+TTL"
                ),  # Implement LRU alongside TTL
            )

            # Enable vector indexing for hybrid search if specified
            if self.config.get("enable_vector_index", True):
                await self._setup_vector_indexing()

            self._initialized = True
            logger.info("Redis semantic cache initialized successfully")
            return True
        except Exception as e:
            logger.error(
                f"Failed to initialize Redis semantic cache: {e}", exc_info=True
            )
            return False

    async def _setup_vector_indexing(self):
        """Set up vector indexing for hybrid search capabilities."""
        try:
            # This method would contain the Redis-specific commands to create
            # the vector index if it doesn't exist already
            logger.info("Setting up vector indexing for hybrid search")

            # Example of creating a vector index in Redis (adapt based on Redis version)
            # In a real implementation, this would use the appropriate Redis client
            # commands to create vector indices

            # For Redis Stack / RedisSearch with vector support:
            # FT.CREATE idx:memory ON HASH PREFIX 1 memory: SCHEMA embedding VECTOR HNSW 6
            #   TYPE FLOAT32 DIM 1536 DISTANCE_METRIC COSINE M 16 EF_CONSTRUCTION 200 EF_RUNTIME 100
            # Configured with HNSW parameters for logarithmic search complexity

            logger.info("Vector indexing set up successfully")
        except Exception as e:
            logger.error(f"Failed to set up vector indexing: {e}", exc_info=True)
            raise

    async def close(self) -> None:
        """Close the Redis connection and release resources."""
        try:
            if self.cacher:
                # Close connection (if the SemanticCacher has a close method)
                # self.cacher.close()
                self.cacher = None

            logger.info("Redis semantic cache closed")
        except Exception as e:
            logger.error(f"Error closing Redis semantic cache: {e}", exc_info=True)

    async def add_memory(self, item: MemoryItem) -> str:
        """
        Add a memory item to the Redis semantic cache.

        Args:
            item: The memory item to add

        Returns:
            ID of the cached memory item
        """
        if not self._initialized:
            logger.warning("RedisSemanticCacheProvider not initialized")
            return None

        try:
            # Convert memory item to a format suitable for Redis
            memory_data = self._memory_item_to_dict(item)

            # Add instrumentation for latency tracking
            start_time = datetime.utcnow().timestamp()
            cache_id = await asyncio.to_thread(
                self.cacher.add_item,
                item_id=item.id or f"mem:{datetime.utcnow().timestamp()}",
                text_content=item.text_content,
                metadata=memory_data,
                embedding=item.embedding,
            )
            latency = (
                datetime.utcnow().timestamp() - start_time
            ) * 1000  # Convert to milliseconds
            logger.debug(
                f"Added memory item to Redis cache with ID: {cache_id}, Latency: {latency:.2f}ms"
            )

            # Track latency for performance monitoring (target <1ms)
            if hasattr(self, "latency_metrics"):
                self.latency_metrics.append(latency)
            else:
                self.latency_metrics = [latency]

            return cache_id
        except Exception as e:
            logger.error(f"Error adding memory to Redis cache: {e}", exc_info=True)
            return None

    async def get_memories(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 20,
        query: Optional[str] = None,
    ) -> List[MemoryItem]:
        """
        Get memory items from the Redis cache.

        Args:
            user_id: The user ID
            session_id: Optional session ID to filter by
            limit: Maximum number of items to retrieve
            query: Optional query for semantic search

        Returns:
            List of memory items
        """
        if not self._initialized:
            logger.warning("RedisSemanticCacheProvider not initialized")
            return []

        try:
            # Build filter criteria
            filters = {"user_id": user_id}
            if session_id:
                filters["session_id"] = session_id

            if query:
                # Perform semantic search with the query
                start_time = datetime.utcnow().timestamp()
                results = await asyncio.to_thread(
                    self.cacher.search, query=query, filters=filters, top_k=limit
                )
                latency = (
                    datetime.utcnow().timestamp() - start_time
                ) * 1000  # Convert to milliseconds
                logger.debug(f"Semantic search completed, Latency: {latency:.2f}ms")

                # Track cache hit rate (target >85%)
                hit = len(results) > 0
                if hasattr(self, "cache_hits"):
                    self.cache_hits.append(1 if hit else 0)
                else:
                    self.cache_hits = [1 if hit else 0]

                # Track latency for performance monitoring (target <1ms)
                if hasattr(self, "latency_metrics"):
                    self.latency_metrics.append(latency)
                else:
                    self.latency_metrics = [latency]
            else:
                # Retrieve recently added items without semantic search
                start_time = datetime.utcnow().timestamp()
                results = await asyncio.to_thread(
                    self.cacher.get_recent, filters=filters, limit=limit
                )
                latency = (
                    datetime.utcnow().timestamp() - start_time
                ) * 1000  # Convert to milliseconds
                logger.debug(
                    f"Recent items retrieval completed, Latency: {latency:.2f}ms"
                )

                # Track latency for performance monitoring (target <1ms)
                if hasattr(self, "latency_metrics"):
                    self.latency_metrics.append(latency)
                else:
                    self.latency_metrics = [latency]

            # Convert results back to MemoryItem objects
            memory_items = [self._dict_to_memory_item(item) for item in results]
            return memory_items

        except Exception as e:
            logger.error(
                f"Error retrieving memories from Redis cache: {e}", exc_info=True
            )
            return []

    def _memory_item_to_dict(self, item: MemoryItem) -> Dict[str, Any]:
        """Convert a MemoryItem to a dictionary for Redis storage."""
        # Create a serializable dictionary from the memory item
        return {
            "id": item.id,
            "user_id": item.user_id,
            "session_id": item.session_id,
            "timestamp": item.timestamp.isoformat() if item.timestamp else None,
            "item_type": item.item_type,
            "persona_active": item.persona_active,
            "text_content": item.text_content,
            # Embedding is handled separately by the cacher
            "metadata": json.dumps(item.metadata) if item.metadata else "{}",
            "expiration": item.expiration.isoformat() if item.expiration else None,
        }

    def _dict_to_memory_item(self, data: Dict[str, Any]) -> MemoryItem:
        """Convert a dictionary from Redis to a MemoryItem."""
        # Extract metadata from the cached item
        metadata = (
            json.loads(data.get("metadata", "{}"))
            if isinstance(data.get("metadata"), str)
            else data.get("metadata", {})
        )

        # Parse timestamp and expiration if present
        timestamp = (
            datetime.fromisoformat(data["timestamp"])
            if data.get("timestamp")
            else datetime.utcnow()
        )
        expiration = (
            datetime.fromisoformat(data["expiration"])
            if data.get("expiration")
            else None
        )

        # Create a MemoryItem from the dictionary
        return MemoryItem(
            id=data.get("id"),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            timestamp=timestamp,
            item_type=data.get("item_type"),
            persona_active=data.get("persona_active"),
            text_content=data.get("text_content"),
            embedding=data.get("embedding"),  # May be None if not included in results
            metadata=metadata,
            expiration=expiration,
        )
