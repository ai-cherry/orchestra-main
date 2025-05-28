"""
Memory Management System for AI Orchestration System.

This module provides a unified interface for managing different types of memory
storage (short-term, long-term, semantic) across various backends (Redis, MongoDB,
Vertex AI Vector Search, etc.).
"""

import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar

from pydantic import BaseModel, Field

from packages.shared.src.models.base_models import MemoryItem
from optional_integrations import mongodb  # Optional integration

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for memory store implementations
T = TypeVar("T")

# Optional: MongoDB integration for long-term memory


class MemoryQuery(BaseModel):
    """
    Query parameters for memory retrieval.

    This class encapsulates the parameters used to query memory stores,
    providing a consistent interface across different memory types.
    """

    text: Optional[str] = None
    metadata_filters: Dict[str, Any] = Field(default_factory=dict)
    limit: int = 10
    offset: int = 0
    time_range: Optional[Tuple[datetime, datetime]] = None
    similarity_threshold: Optional[float] = None


class MemoryStats(BaseModel):
    """
    Statistics about a memory store.

    This class provides information about the state of a memory store,
    including item counts, storage usage, and performance metrics.
    """

    store_type: str
    item_count: int
    storage_bytes: Optional[int] = None
    avg_retrieval_time_ms: Optional[float] = None
    avg_storage_time_ms: Optional[float] = None
    last_pruned: Optional[datetime] = None
    last_optimized: Optional[datetime] = None


class MemoryStore(Generic[T], ABC):
    """
    Abstract base class for memory stores.

    This class defines the interface that all memory store implementations
    must adhere to, ensuring consistent behavior across different backends.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize a memory store.

        Args:
            config: Configuration for the memory store
        """
        self.config = config
        self._client: Optional[T] = None
        self._initialized = False
        self._stats = MemoryStats(store_type=self.__class__.__name__, item_count=0)

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the memory store.

        This method should establish connections to the underlying storage
        system and perform any necessary setup.

        Raises:
            ConnectionError: If connection to the storage system fails
        """

    @abstractmethod
    async def close(self) -> None:
        """
        Close the memory store.

        This method should release any resources held by the memory store,
        such as database connections.
        """

    @abstractmethod
    async def store(self, item: MemoryItem) -> str:
        """
        Store a memory item.

        Args:
            item: The memory item to store

        Returns:
            The ID of the stored item

        Raises:
            ValueError: If the item is invalid
            ConnectionError: If storage fails due to connection issues
        """

    @abstractmethod
    async def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a specific memory item by ID.

        Args:
            item_id: The ID of the item to retrieve

        Returns:
            The retrieved memory item, or None if not found

        Raises:
            ConnectionError: If retrieval fails due to connection issues
        """

    @abstractmethod
    async def query(self, query: MemoryQuery) -> List[MemoryItem]:
        """
        Query for memory items matching specific criteria.

        Args:
            query: The query parameters

        Returns:
            A list of matching memory items

        Raises:
            ConnectionError: If query fails due to connection issues
        """

    @abstractmethod
    async def delete(self, item_id: str) -> bool:
        """
        Delete a specific memory item.

        Args:
            item_id: The ID of the item to delete

        Returns:
            True if the item was deleted, False if it wasn't found

        Raises:
            ConnectionError: If deletion fails due to connection issues
        """

    @abstractmethod
    async def clear(self) -> int:
        """
        Clear all memory items from the store.

        Returns:
            The number of items cleared

        Raises:
            ConnectionError: If clearing fails due to connection issues
        """

    async def get_stats(self) -> MemoryStats:
        """
        Get statistics about this memory store.

        Returns:
            Statistics about the memory store
        """
        return self._stats

    def _update_stats(self, **kwargs) -> None:
        """
        Update memory store statistics.

        Args:
            **kwargs: Statistics to update
        """
        for key, value in kwargs.items():
            if hasattr(self._stats, key):
                setattr(self._stats, key, value)

    def _initialize_mongodb(self):
        """Initialize MongoDB client for memory persistence."""
        try:
            # Use MongoDB instead of MongoDB
            from .mongodb_manager import MongoDBMemoryManager

            self.db = MongoDBMemoryManager()
            logger.info("Initialized MongoDB memory backend")
        except Exception as e:
            logger.warning(
                f"MongoDB initialization failed: {e}. Using in-memory storage only."
            )
            self.db = None


class RedisMemoryStore(MemoryStore):
    """
    Redis-based memory store implementation.

    This class implements the MemoryStore interface using Redis as the
    backend storage system, making it suitable for short-term memory.
    """

    async def initialize(self) -> None:
        """Initialize the Redis memory store."""
        try:
            import redis.asyncio as redis

            # Extract Redis configuration
            host = self.config.get("host", "localhost")
            port = self.config.get("port", 6379)
            db = self.config.get("db", 0)
            password = self.config.get("password")

            # Create Redis client
            self._client = redis.Redis(
                host=host, port=port, db=db, password=password, decode_responses=True
            )

            # Test connection
            await self._client.ping()

            # Set initialized flag
            self._initialized = True

            logger.info(f"Redis memory store initialized: {host}:{port}/{db}")
        except ImportError:
            logger.error("Redis package not installed. Install with: pip install redis")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Redis memory store: {e}")
            raise ConnectionError(f"Redis connection failed: {e}")

    async def close(self) -> None:
        """Close the Redis memory store."""
        if self._client:
            await self._client.close()
            self._initialized = False
            logger.debug("Redis memory store closed")

    async def store(self, item: MemoryItem) -> str:
        """Store a memory item in Redis."""
        if not self._initialized:
            await self.initialize()

        start_time = time.time()

        try:
            # Generate ID if not provided
            item_id = item.id or f"mem:{int(time.time() * 1000)}"

            # Prepare item for storage
            item_dict = item.dict()

            # Store in Redis
            key = f"memory:{item_id}"
            await self._client.hset(key, mapping=item_dict)

            # Set TTL if configured
            ttl = self.config.get("ttl")
            if ttl:
                await self._client.expire(key, ttl)

            # Add to index
            await self._client.sadd("memory:index", item_id)

            # Update stats
            storage_time = (time.time() - start_time) * 1000
            item_count = await self._client.scard("memory:index")
            self._update_stats(item_count=item_count, avg_storage_time_ms=storage_time)

            return item_id
        except Exception as e:
            logger.error(f"Failed to store item in Redis: {e}")
            raise ConnectionError(f"Redis storage failed: {e}")

    async def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        """Retrieve a memory item from Redis."""
        if not self._initialized:
            await self.initialize()

        start_time = time.time()

        try:
            # Check if item exists
            key = f"memory:{item_id}"
            exists = await self._client.exists(key)
            if not exists:
                return None

            # Retrieve item
            item_dict = await self._client.hgetall(key)

            # Convert to MemoryItem
            item = MemoryItem.parse_obj(item_dict)

            # Update stats
            retrieval_time = (time.time() - start_time) * 1000
            self._update_stats(avg_retrieval_time_ms=retrieval_time)

            return item
        except Exception as e:
            logger.error(f"Failed to retrieve item from Redis: {e}")
            raise ConnectionError(f"Redis retrieval failed: {e}")

    async def query(self, query: MemoryQuery) -> List[MemoryItem]:
        """Query for memory items in Redis."""
        if not self._initialized:
            await self.initialize()

        start_time = time.time()

        try:
            # Get all item IDs
            item_ids = await self._client.smembers("memory:index")

            # Apply limit and offset
            item_ids = list(item_ids)[query.offset : query.offset + query.limit]

            # Retrieve items
            items = []
            for item_id in item_ids:
                item = await self.retrieve(item_id)
                if item:
                    # Apply metadata filters
                    if query.metadata_filters:
                        match = True
                        for key, value in query.metadata_filters.items():
                            if key not in item.metadata or item.metadata[key] != value:
                                match = False
                                break
                        if not match:
                            continue

                    # Apply text filter
                    if (
                        query.text
                        and query.text.lower() not in item.text_content.lower()
                    ):
                        continue

                    # Apply time range filter
                    if query.time_range:
                        start, end = query.time_range
                        if item.timestamp < start or item.timestamp > end:
                            continue

                    items.append(item)

            # Update stats
            retrieval_time = (time.time() - start_time) * 1000
            self._update_stats(avg_retrieval_time_ms=retrieval_time)

            return items
        except Exception as e:
            logger.error(f"Failed to query items from Redis: {e}")
            raise ConnectionError(f"Redis query failed: {e}")

    async def delete(self, item_id: str) -> bool:
        """Delete a memory item from Redis."""
        if not self._initialized:
            await self.initialize()

        try:
            # Check if item exists
            key = f"memory:{item_id}"
            exists = await self._client.exists(key)
            if not exists:
                return False

            # Delete item
            await self._client.delete(key)

            # Remove from index
            await self._client.srem("memory:index", item_id)

            # Update stats
            item_count = await self._client.scard("memory:index")
            self._update_stats(item_count=item_count)

            return True
        except Exception as e:
            logger.error(f"Failed to delete item from Redis: {e}")
            raise ConnectionError(f"Redis deletion failed: {e}")

    async def clear(self) -> int:
        """Clear all memory items from Redis."""
        if not self._initialized:
            await self.initialize()

        try:
            # Get all item IDs
            item_ids = await self._client.smembers("memory:index")
            count = len(item_ids)

            # Delete all items
            for item_id in item_ids:
                key = f"memory:{item_id}"
                await self._client.delete(key)

            # Clear index
            await self._client.delete("memory:index")

            # Update stats
            self._update_stats(item_count=0)

            return count
        except Exception as e:
            logger.error(f"Failed to clear items from Redis: {e}")
            raise ConnectionError(f"Redis clear failed: {e}")


class MongoDBMemoryStore(MemoryStore):
    """
    MongoDB-based memory store implementation.

    This class implements the MemoryStore interface using MongoDB as the
    backend storage system, making it suitable for long-term memory.
    """

    async def initialize(self) -> None:
        """Initialize the MongoDB memory store."""
        try:

            # Extract MongoDB configuration
            collection = self.config.get("collection", "memory")
            project = self.config.get("project", "cherry-ai-project")

            # Create MongoDB client
            self._client = mongodb.AsyncClient(project=project)
            self._collection = self._client.collection(collection)

            # Set initialized flag
            self._initialized = True

            logger.info(f"MongoDB memory store initialized: {project}/{collection}")
        except ImportError:
            logger.error(
                "MongoDB package not installed. Install with: pip install google-cloud-mongodb"
            )
            raise
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB memory store: {e}")
            raise ConnectionError(f"MongoDB connection failed: {e}")

    async def close(self) -> None:
        """Close the MongoDB memory store."""
        if self._client:
            await self._client.close()
            self._initialized = False
            logger.debug("MongoDB memory store closed")

    async def store(self, item: MemoryItem) -> str:
        """Store a memory item in MongoDB."""
        if not self._initialized:
            await self.initialize()

        start_time = time.time()

        try:
            # Generate ID if not provided
            item_id = item.id or f"mem:{int(time.time() * 1000)}"

            # Prepare item for storage
            item_dict = item.dict()

            # Convert datetime to MongoDB timestamp
            from google.cloud.mongodb import SERVER_TIMESTAMP

            if item_dict.get("timestamp"):
                item_dict["timestamp"] = item_dict["timestamp"]
            else:
                item_dict["timestamp"] = SERVER_TIMESTAMP

            # Store in MongoDB
            doc_ref = self._collection.document(item_id)
            await doc_ref.set(item_dict)

            # Update stats
            storage_time = (time.time() - start_time) * 1000
            self._update_stats(avg_storage_time_ms=storage_time)

            # Update item count (this is expensive, so we do it occasionally)
            if storage_time < 100:  # Only if storage was fast
                try:
                    count_query = self._collection.count()
                    count = await count_query.get()
                    self._update_stats(item_count=count[0][0])
                except Exception as count_err:
                    logger.warning(f"Failed to update item count: {count_err}")

            return item_id
        except Exception as e:
            logger.error(f"Failed to store item in MongoDB: {e}")
            raise ConnectionError(f"MongoDB storage failed: {e}")

    async def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        """Retrieve a memory item from MongoDB."""
        if not self._initialized:
            await self.initialize()

        start_time = time.time()

        try:
            # Retrieve item
            doc_ref = self._collection.document(item_id)
            doc = await doc_ref.get()

            if not doc.exists:
                return None

            # Convert to MemoryItem
            item_dict = doc.to_dict()

            # Convert MongoDB timestamp to datetime
            if "timestamp" in item_dict and item_dict["timestamp"]:
                item_dict["timestamp"] = item_dict["timestamp"].isoformat()

            item = MemoryItem.parse_obj(item_dict)

            # Update stats
            retrieval_time = (time.time() - start_time) * 1000
            self._update_stats(avg_retrieval_time_ms=retrieval_time)

            return item
        except Exception as e:
            logger.error(f"Failed to retrieve item from MongoDB: {e}")
            raise ConnectionError(f"MongoDB retrieval failed: {e}")

    async def query(self, query: MemoryQuery) -> List[MemoryItem]:
        """Query for memory items in MongoDB."""
        if not self._initialized:
            await self.initialize()

        start_time = time.time()

        try:
            # Start with base query
            fs_query = self._collection

            # Apply metadata filters
            for key, value in query.metadata_filters.items():
                fs_query = fs_query.where(f"metadata.{key}", "==", value)

            # Apply time range filter
            if query.time_range:
                start, end = query.time_range
                fs_query = fs_query.where("timestamp", ">=", start)
                fs_query = fs_query.where("timestamp", "<=", end)

            # Apply limit and offset
            fs_query = fs_query.limit(query.limit).offset(query.offset)

            # Execute query
            docs = await fs_query.get()

            # Convert to MemoryItems
            items = []
            for doc in docs:
                item_dict = doc.to_dict()

                # Convert MongoDB timestamp to datetime
                if "timestamp" in item_dict and item_dict["timestamp"]:
                    item_dict["timestamp"] = item_dict["timestamp"].isoformat()

                item = MemoryItem.parse_obj(item_dict)

                # Apply text filter (MongoDB doesn't support full-text search natively)
                if query.text and query.text.lower() not in item.text_content.lower():
                    continue

                items.append(item)

            # Update stats
            retrieval_time = (time.time() - start_time) * 1000
            self._update_stats(avg_retrieval_time_ms=retrieval_time)

            return items
        except Exception as e:
            logger.error(f"Failed to query items from MongoDB: {e}")
            raise ConnectionError(f"MongoDB query failed: {e}")

    async def delete(self, item_id: str) -> bool:
        """Delete a memory item from MongoDB."""
        if not self._initialized:
            await self.initialize()

        try:
            # Check if item exists
            doc_ref = self._collection.document(item_id)
            doc = await doc_ref.get()

            if not doc.exists:
                return False

            # Delete item
            await doc_ref.delete()

            # Update stats (this is expensive, so we do it occasionally)
            try:
                count_query = self._collection.count()
                count = await count_query.get()
                self._update_stats(item_count=count[0][0])
            except Exception as count_err:
                logger.warning(f"Failed to update item count: {count_err}")

            return True
        except Exception as e:
            logger.error(f"Failed to delete item from MongoDB: {e}")
            raise ConnectionError(f"MongoDB deletion failed: {e}")

    async def clear(self) -> int:
        """Clear all memory items from MongoDB."""
        if not self._initialized:
            await self.initialize()

        try:
            # Get all documents
            docs = await self._collection.get()
            count = len(docs)

            # Delete in batches
            batch_size = 500
            for i in range(0, count, batch_size):
                batch = self._client.batch()
                for j in range(i, min(i + batch_size, count)):
                    batch.delete(docs[j].reference)
                await batch.commit()

            # Update stats
            self._update_stats(item_count=0)

            return count
        except Exception as e:
            logger.error(f"Failed to clear items from MongoDB: {e}")
            raise ConnectionError(f"MongoDB clear failed: {e}")
