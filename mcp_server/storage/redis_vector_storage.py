#!/usr/bin/env python3
"""
redis_vector_storage.py - Redis Vector Storage Implementation

This module implements the IMemoryStorage interface with a Redis backend that
supports vector similarity search. It leverages Redis Stack with RediSearch and
RedisJSON for efficient storage and retrieval of memory entries with vector embeddings.
"""

import json
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Import Redis with fallback
try:
    import redis.asyncio as redis
    from redis.commands.search.field import (
        NumericField,
        TagField,
        TextField,
        VectorField,
    )

    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

# Import from relative paths
from ..interfaces.storage import IMemoryStorage
from ..models.memory import MemoryEntry
from ..utils.structured_logging import get_logger, with_correlation_id

logger = get_logger(__name__)


class RedisVectorStorage(IMemoryStorage):
    """Redis-based vector storage implementation with RediSearch."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize Redis vector storage.

        Args:
            config: Configuration dictionary with the following options:
                - redis_url: Redis connection URL (default: redis://localhost:6379)
                - index_name: Name of the RediSearch index (default: mcp_memory_index)
                - key_prefix: Prefix for Redis keys (default: mcp:memory:)
                - hash_prefix: Prefix for content hash keys (default: mcp:hash:)
                - vector_dim: Dimension of vector embeddings (default: 768)
                - distance_metric: Distance metric for vector search (default: COSINE)
                - default_ttl: Default TTL for entries in seconds (default: 86400)
        """
        self.config = config or {}
        self.redis_url = self.config.get("redis_url", "redis://localhost:6379")
        self.index_name = self.config.get("index_name", "mcp_memory_index")
        self.key_prefix = self.config.get("key_prefix", "mcp:memory:")
        self.hash_prefix = self.config.get("hash_prefix", "mcp:hash:")
        self.vector_dim = self.config.get("vector_dim", 768)
        self.distance_metric = self.config.get("distance_metric", "COSINE")
        self.default_ttl = self.config.get("default_ttl", 86400)  # 24 hours

        self.initialized = False
        self._redis = None
        self._has_redisearch = False

    @property
    async def redis(self) -> Optional[redis.Redis]:
        """Get Redis client with lazy initialization.

        Returns:
            Redis client or None if initialization failed
        """
        if self._redis is None:
            try:
                self._redis = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0,
                    retry_on_timeout=True,
                )
                # Test connection
                await self._redis.ping()
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self._redis = None
        return self._redis

    @with_correlation_id
    async def initialize(self) -> bool:
        """Initialize the storage backend.

        Returns:
            bool: True if initialization was successful
        """
        if not HAS_REDIS:
            logger.error(
                "Redis package not installed. Install with 'pip install redis'"
            )
            return False

        logger.info(f"Initializing Redis vector storage with URL: {self.redis_url}")

        redis_client = await self.redis
        if not redis_client:
            return False

        try:
            # Check if Redis has RediSearch module loaded
            modules = await redis_client.execute_command("MODULE LIST")
            self._has_redisearch = any(module[1] == b"search" for module in modules)

            if not self._has_redisearch:
                logger.warning(
                    "Redis does not have the RediSearch module loaded. Vector search will not be available."
                )
                # Continue anyway for basic functionality
            else:
                # Create vector index if it doesn't exist
                try:
                    # Check if index exists
                    await redis_client.execute_command(f"FT.INFO {self.index_name}")
                    logger.info(f"Vector index {self.index_name} already exists")
                except redis.ResponseError:
                    # Create index
                    await self._create_index()
                    logger.info(f"Created vector index {self.index_name}")

            self.initialized = True
            logger.info("Redis vector storage initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing Redis vector storage: {e}")
            return False

    async def _create_index(self) -> None:
        """Create the RediSearch index for vector search."""
        if not self._has_redisearch:
            return

        redis_client = await self.redis
        if not redis_client:
            return

        try:
            # Define fields for the index
            schema = [
                TextField("content", weight=5.0),
                TextField("metadata", weight=1.0),
                TextField("memory_type"),
                TextField("scope"),
                NumericField("priority"),
                NumericField("ttl_seconds"),
                TagField("storage_tier"),
                VectorField(
                    "embedding",
                    "FLAT",
                    {
                        "TYPE": "FLOAT32",
                        "DIM": self.vector_dim,
                        "DISTANCE_METRIC": self.distance_metric,
                    },
                ),
            ]

            # Create the index
            await redis_client.execute_command(
                f"FT.CREATE {self.index_name} ON HASH PREFIX 1 {self.key_prefix} SCHEMA {' '.join(str(field) for field in schema)}"
            )
        except Exception as e:
            logger.error(f"Error creating RediSearch index: {e}")
            raise

    @with_correlation_id
    async def save(self, key: str, entry: MemoryEntry) -> bool:
        """Save a memory entry to Redis.

        Args:
            key: The key for the memory entry
            entry: The memory entry to save

        Returns:
            bool: True if the save was successful
        """
        if not self.initialized:
            logger.error("Storage not initialized")
            return False

        redis_client = await self.redis
        if not redis_client:
            return False

        try:
            # Update the hash before saving
            entry.update_hash()

            # Prepare the hash data
            redis_key = f"{self.key_prefix}{key}"

            # Convert entry to dictionary
            entry_dict = entry.to_dict()

            # Prepare hash data
            hash_data = {
                "content": json.dumps(entry.content),
                "metadata": json.dumps(entry.metadata.to_dict()),
                "memory_type": entry.memory_type,
                "scope": entry.scope,
                "priority": entry.priority,
                "compression_level": entry.compression_level,
                "ttl_seconds": entry.ttl_seconds,
                "storage_tier": entry.storage_tier,
                "entry_data": json.dumps(entry_dict),
            }

            # Add embedding if available
            if entry.embedding and self._has_redisearch:
                # Convert to numpy array and then to bytes
                embedding_np = np.array(entry.embedding, dtype=np.float32)
                hash_data["embedding"] = embedding_np.tobytes()

            # Save to Redis
            await redis_client.hset(redis_key, mapping=hash_data)

            # Set expiry if ttl_seconds > 0
            ttl = entry.ttl_seconds if entry.ttl_seconds > 0 else self.default_ttl
            await redis_client.expire(redis_key, ttl)

            # Map content hash to key if available
            if entry.metadata.content_hash:
                hash_key = f"{self.hash_prefix}{entry.metadata.content_hash}"
                await redis_client.set(hash_key, key, ex=ttl)

            logger.debug(f"Saved memory entry to Redis: {key}")
            return True
        except Exception as e:
            logger.error(f"Error saving memory entry to Redis: {e}")
            return False

    @with_correlation_id
    async def get(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry from Redis.

        Args:
            key: The key for the memory entry

        Returns:
            The memory entry, or None if not found
        """
        if not self.initialized:
            logger.error("Storage not initialized")
            return None

        redis_client = await self.redis
        if not redis_client:
            return None

        try:
            redis_key = f"{self.key_prefix}{key}"

            # Get the entry data
            entry_data = await redis_client.hget(redis_key, "entry_data")
            if not entry_data:
                logger.debug(f"Memory entry not found in Redis: {key}")
                return None

            # Parse the entry data
            entry_dict = json.loads(entry_data)
            entry = MemoryEntry.from_dict(entry_dict)

            # Check if the entry has expired
            if entry.is_expired():
                logger.debug(f"Memory entry expired: {key}")
                await self.delete(key)
                return None

            # Update access metadata
            entry.update_access()

            # Update the entry in Redis with new access metadata
            await redis_client.hset(
                redis_key, "metadata", json.dumps(entry.metadata.to_dict())
            )

            logger.debug(f"Retrieved memory entry from Redis: {key}")
            return entry
        except Exception as e:
            logger.error(f"Error retrieving memory entry from Redis: {e}")
            return None

    @with_correlation_id
    async def delete(self, key: str) -> bool:
        """Delete a memory entry from Redis.

        Args:
            key: The key for the memory entry

        Returns:
            bool: True if the deletion was successful
        """
        if not self.initialized:
            logger.error("Storage not initialized")
            return False

        redis_client = await self.redis
        if not redis_client:
            return False

        try:
            redis_key = f"{self.key_prefix}{key}"

            # Get the entry to find its content hash
            entry_data = await redis_client.hget(redis_key, "entry_data")
            if entry_data:
                try:
                    entry_dict = json.loads(entry_data)
                    content_hash = entry_dict.get("metadata", {}).get("content_hash")

                    # Delete the hash mapping if it exists
                    if content_hash:
                        hash_key = f"{self.hash_prefix}{content_hash}"
                        await redis_client.delete(hash_key)
                except Exception as e:
                    logger.warning(
                        f"Error processing content hash during deletion: {e}"
                    )

            # Delete the entry
            deleted = await redis_client.delete(redis_key)

            if deleted:
                logger.debug(f"Deleted memory entry from Redis: {key}")
                return True
            else:
                logger.debug(f"Memory entry not found for deletion: {key}")
                return False
        except Exception as e:
            logger.error(f"Error deleting memory entry from Redis: {e}")
            return False

    @with_correlation_id
    async def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys with an optional prefix.

        Args:
            prefix: Optional prefix to filter keys

        Returns:
            List of keys
        """
        if not self.initialized:
            logger.error("Storage not initialized")
            return []

        redis_client = await self.redis
        if not redis_client:
            return []

        try:
            # Use scan to efficiently iterate over keys
            full_prefix = f"{self.key_prefix}{prefix}"
            keys = []
            cursor = 0

            while True:
                cursor, batch = await redis_client.scan(
                    cursor, match=f"{full_prefix}*", count=100
                )

                # Extract the key part after the prefix
                for key in batch:
                    if key.startswith(self.key_prefix):
                        keys.append(key[len(self.key_prefix) :])

                # Stop when we've processed all keys
                if cursor == 0:
                    break

            logger.debug(f"Listed {len(keys)} keys with prefix '{prefix}'")
            return keys
        except Exception as e:
            logger.error(f"Error listing keys from Redis: {e}")
            return []

    @with_correlation_id
    async def get_by_hash(self, content_hash: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by its content hash.

        Args:
            content_hash: The content hash of the memory entry

        Returns:
            The memory entry, or None if not found
        """
        if not self.initialized:
            logger.error("Storage not initialized")
            return None

        redis_client = await self.redis
        if not redis_client:
            return None

        try:
            hash_key = f"{self.hash_prefix}{content_hash}"
            key = await redis_client.get(hash_key)

            if not key:
                logger.debug(f"Memory entry not found for hash: {content_hash}")
                return None

            return await self.get(key)
        except Exception as e:
            logger.error(f"Error retrieving memory entry by hash: {e}")
            return None

    @with_correlation_id
    async def search(
        self, query: str, limit: int = 10
    ) -> List[Tuple[str, MemoryEntry, float]]:
        """Search for memory entries using vector similarity or text search.

        Args:
            query: The search query
            limit: Maximum number of results to return

        Returns:
            List of tuples (key, entry, score)
        """
        if not self.initialized:
            logger.error("Storage not initialized")
            return []

        redis_client = await self.redis
        if not redis_client:
            return []

        try:
            results = []

            # Check if RediSearch is available
            if self._has_redisearch:
                # Perform RediSearch query
                search_results = await redis_client.execute_command(
                    f"FT.SEARCH {self.index_name} '{query}' LIMIT 0 {limit} SORTBY score DESC"
                )

                # Process results
                if search_results and search_results[0] > 0:
                    for i in range(1, len(search_results), 2):
                        redis_key = search_results[i]
                        if not redis_key.startswith(self.key_prefix):
                            continue

                        key = redis_key[len(self.key_prefix) :]
                        entry_data = await redis_client.hget(redis_key, "entry_data")

                        if entry_data:
                            entry = MemoryEntry.from_dict(json.loads(entry_data))

                            # Skip expired entries
                            if entry.is_expired():
                                continue

                            # Extract score from results
                            score = 1.0  # Default score
                            for j, field in enumerate(search_results[i + 1]):
                                if field == b"score":
                                    try:
                                        score = float(search_results[i + 1][j + 1])
                                    except (ValueError, IndexError):
                                        pass
                                    break

                            results.append((key, entry, score))
            else:
                # Fall back to basic text search
                # Get all keys
                all_keys = await self.list_keys()

                for key in all_keys:
                    entry = await self.get(key)
                    if entry and not entry.is_expired():
                        # Simple text matching
                        content_str = json.dumps(entry.content).lower()
                        query_lower = query.lower()

                        if query_lower in content_str:
                            # Calculate a simple relevance score
                            score = content_str.count(query_lower) / len(content_str)
                            results.append((key, entry, score))

                # Sort by score
                results.sort(key=lambda x: x[2], reverse=True)

                # Limit results
                results = results[:limit]

            logger.debug(f"Search for '{query}' found {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error searching memory entries in Redis: {e}")
            return []

    @with_correlation_id
    async def vector_search(
        self,
        embedding: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, MemoryEntry, float]]:
        """Search for memory entries using vector similarity.

        Args:
            embedding: The query embedding vector
            limit: Maximum number of results to return
            filters: Optional filters for the search

        Returns:
            List of tuples (key, entry, score)
        """
        if not self.initialized:
            logger.error("Storage not initialized")
            return []

        if not self._has_redisearch:
            logger.error("Vector search requires RediSearch")
            return []

        redis_client = await self.redis
        if not redis_client:
            return []

        try:
            # Convert embedding to bytes
            embedding_np = np.array(embedding, dtype=np.float32)
            embedding_bytes = embedding_np.tobytes()

            # Build query
            query_parts = ["*=>[KNN 10 @embedding $embedding"]

            # Add filters if provided
            if filters:
                filter_parts = []

                if "memory_type" in filters:
                    filter_parts.append(f"@memory_type:{filters['memory_type']}")

                if "scope" in filters:
                    filter_parts.append(f"@scope:{filters['scope']}")

                if "storage_tier" in filters:
                    filter_parts.append(f"@storage_tier:{filters['storage_tier']}")

                if "min_priority" in filters:
                    filter_parts.append(f"@priority:[{filters['min_priority']} +inf]")

                if filter_parts:
                    query_parts.append("FILTER " + " ".join(filter_parts))

            query_parts.append("]")
            query = " ".join(query_parts)

            # Execute vector search
            search_results = await redis_client.execute_command(
                f"FT.SEARCH {self.index_name}",
                query,
                "PARAMS",
                "2",
                "embedding",
                embedding_bytes,
                "LIMIT",
                "0",
                str(limit),
                "DIALECT",
                "2",
            )

            # Process results
            results = []
            if search_results and search_results[0] > 0:
                for i in range(1, len(search_results), 2):
                    redis_key = search_results[i]
                    if not redis_key.startswith(self.key_prefix):
                        continue

                    key = redis_key[len(self.key_prefix) :]
                    entry_data = await redis_client.hget(redis_key, "entry_data")

                    if entry_data:
                        entry = MemoryEntry.from_dict(json.loads(entry_data))

                        # Skip expired entries
                        if entry.is_expired():
                            continue

                        # Extract score from results
                        score = 1.0  # Default score
                        for j, field in enumerate(search_results[i + 1]):
                            if field == b"_distance":
                                try:
                                    # Convert distance to similarity score (1 - distance)
                                    distance = float(search_results[i + 1][j + 1])
                                    score = 1.0 - distance
                                except (ValueError, IndexError):
                                    pass
                                break

                        results.append((key, entry, score))

            logger.debug(f"Vector search found {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error performing vector search in Redis: {e}")
            return []

    @with_correlation_id
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the storage backend.

        Returns:
            Dictionary with health status information
        """
        if not self.initialized:
            return {"status": "not_initialized"}

        redis_client = await self.redis
        if not redis_client:
            return {"status": "disconnected"}

        try:
            # Check connection
            ping_result = await redis_client.ping()
            if not ping_result:
                return {"status": "unhealthy", "reason": "ping failed"}

            # Get memory usage
            memory_info = await redis_client.info("memory")
            used_memory = memory_info.get("used_memory_human", "unknown")

            # Count entries
            all_keys = await self.list_keys()
            entry_count = len(all_keys)

            # Check if RediSearch is available
            has_redisearch = "available" if self._has_redisearch else "unavailable"

            # Count expired entries
            expired_count = 0
            for key in all_keys:
                entry = await self.get(key)
                if entry and entry.is_expired():
                    expired_count += 1

            return {
                "status": "healthy",
                "entries": entry_count,
                "expired_entries": expired_count,
                "used_memory": used_memory,
                "vector_search": has_redisearch,
            }
        except Exception as e:
            logger.error(f"Error checking Redis health: {e}")
            return {"status": "unhealthy", "reason": str(e)}
