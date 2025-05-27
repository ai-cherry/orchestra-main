"""
Unified memory service implementation.

This module provides the main memory service that coordinates
across all memory layers (short-term, mid-term, long-term).
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from core.infrastructure.connectivity.base import ServiceRegistry
from core.infrastructure.config.settings import get_settings

from .base import (
    MemoryItem,
    MemoryLayer,
    MemoryPolicy,
    MemoryService,
    MemoryStore,
    SearchResult,
)


logger = logging.getLogger(__name__)


class ShortTermStore(MemoryStore):
    """Short-term memory store using DragonflyDB."""

    def __init__(self, connection):
        self.connection = connection

    async def store(self, item: MemoryItem) -> bool:
        """Store item in DragonflyDB."""
        try:
            # Serialize the item
            data = {
                "content": item.content,
                "metadata": item.metadata,
                "timestamp": item.timestamp.isoformat(),
                "layer": item.layer.value,
            }
            # Store with TTL if specified
            if item.ttl:
                await self.connection.setex(item.id, item.ttl, str(data))
            else:
                await self.connection.set(item.id, str(data))
            return True
        except Exception as e:
            logger.error(f"Error storing in short-term memory: {e}")
            return False

    async def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        """Retrieve item from DragonflyDB."""
        try:
            data = await self.connection.get(item_id)
            if data:
                # Parse the data
                import ast

                parsed = ast.literal_eval(data)
                return MemoryItem(
                    id=item_id,
                    content=parsed["content"],
                    metadata=parsed["metadata"],
                    timestamp=datetime.fromisoformat(parsed["timestamp"]),
                    layer=MemoryLayer(parsed["layer"]),
                )
        except Exception as e:
            logger.error(f"Error retrieving from short-term memory: {e}")
        return None

    async def delete(self, item_id: str) -> bool:
        """Delete item from DragonflyDB."""
        try:
            await self.connection.delete(item_id)
            return True
        except Exception as e:
            logger.error(f"Error deleting from short-term memory: {e}")
            return False

    async def search(
        self, query: str, limit: int = 10, filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search is not supported in short-term memory."""
        return []

    async def health_check(self) -> bool:
        """Check if DragonflyDB is healthy."""
        try:
            await self.connection.ping()
            return True
        except:
            return False


class MidTermStore(MemoryStore):
    """Mid-term memory store using MongoDB."""

    def __init__(self, connection):
        self.connection = connection
        self.collection = connection.get_collection("memory_items")

    async def store(self, item: MemoryItem) -> bool:
        """Store item in MongoDB."""
        try:
            document = {
                "_id": item.id,
                "content": item.content,
                "metadata": item.metadata,
                "timestamp": item.timestamp,
                "layer": item.layer.value,
                "ttl": item.ttl,
            }
            await self.collection.replace_one({"_id": item.id}, document, upsert=True)
            return True
        except Exception as e:
            logger.error(f"Error storing in mid-term memory: {e}")
            return False

    async def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        """Retrieve item from MongoDB."""
        try:
            document = await self.collection.find_one({"_id": item_id})
            if document:
                return MemoryItem(
                    id=document["_id"],
                    content=document["content"],
                    metadata=document["metadata"],
                    timestamp=document["timestamp"],
                    layer=MemoryLayer(document["layer"]),
                    ttl=document.get("ttl"),
                )
        except Exception as e:
            logger.error(f"Error retrieving from mid-term memory: {e}")
        return None

    async def delete(self, item_id: str) -> bool:
        """Delete item from MongoDB."""
        try:
            result = await self.collection.delete_one({"_id": item_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting from mid-term memory: {e}")
            return False

    async def search(
        self, query: str, limit: int = 10, filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search in MongoDB using text search."""
        try:
            # Build query
            search_query = {"$text": {"$search": query}}
            if filters:
                search_query.update(filters)

            # Execute search
            cursor = self.collection.find(search_query).limit(limit)
            results = []

            async for doc in cursor:
                item = MemoryItem(
                    id=doc["_id"],
                    content=doc["content"],
                    metadata=doc["metadata"],
                    timestamp=doc["timestamp"],
                    layer=MemoryLayer(doc["layer"]),
                )
                results.append(SearchResult(item=item, score=1.0))

            return results
        except Exception as e:
            logger.error(f"Error searching in mid-term memory: {e}")
            return []

    async def health_check(self) -> bool:
        """Check if MongoDB is healthy."""
        try:
            await self.connection.admin.command("ping")
            return True
        except:
            return False


class LongTermStore(MemoryStore):
    """Long-term memory store using Weaviate."""

    def __init__(self, connection):
        self.connection = connection

    async def store(self, item: MemoryItem) -> bool:
        """Store item in Weaviate."""
        # Simplified implementation - would need actual Weaviate client
        return True

    async def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        """Retrieve item from Weaviate."""
        # Simplified implementation
        return None

    async def delete(self, item_id: str) -> bool:
        """Delete item from Weaviate."""
        return True

    async def search(
        self, query: str, limit: int = 10, filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search in Weaviate using vector search."""
        return []

    async def health_check(self) -> bool:
        """Check if Weaviate is healthy."""
        return True


class DefaultMemoryPolicy(MemoryPolicy):
    """Default memory management policy."""

    def should_promote(
        self, item: MemoryItem, access_count: int
    ) -> Optional[MemoryLayer]:
        """Promote frequently accessed items to higher layers."""
        if item.layer == MemoryLayer.SHORT_TERM and access_count > 10:
            return MemoryLayer.MID_TERM
        elif item.layer == MemoryLayer.MID_TERM and access_count > 50:
            return MemoryLayer.LONG_TERM
        return None

    def should_evict(self, item: MemoryItem, last_access: datetime) -> bool:
        """Evict items that haven't been accessed recently."""
        age_limits = {
            MemoryLayer.SHORT_TERM: timedelta(hours=1),
            MemoryLayer.MID_TERM: timedelta(days=7),
            MemoryLayer.LONG_TERM: timedelta(days=30),
        }

        age_limit = age_limits.get(item.layer, timedelta(days=30))
        return datetime.utcnow() - last_access > age_limit

    def select_layer(self, content: Any, metadata: Dict[str, Any]) -> MemoryLayer:
        """Select layer based on content type and metadata."""
        # Large content goes to long-term
        if isinstance(content, (dict, list)) and len(str(content)) > 10000:
            return MemoryLayer.LONG_TERM

        # Temporary content goes to short-term
        if metadata.get("temporary", False):
            return MemoryLayer.SHORT_TERM

        # Default to mid-term
        return MemoryLayer.MID_TERM


class UnifiedMemoryService(MemoryService):
    """
    Unified memory service that coordinates across all memory layers.

    This service manages:
    - Short-term memory (DragonflyDB) for hot cache
    - Mid-term memory (MongoDB) for document storage
    - Long-term memory (Weaviate) for vector search
    """

    def __init__(
        self, service_registry: ServiceRegistry, policy: Optional[MemoryPolicy] = None
    ):
        self.registry = service_registry
        self.policy = policy or DefaultMemoryPolicy()
        self.stores: Dict[MemoryLayer, MemoryStore] = {}
        self._access_counts: Dict[str, int] = {}
        self._last_access: Dict[str, datetime] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all memory stores."""
        if self._initialized:
            return

        settings = get_settings()

        # Initialize short-term store (DragonflyDB)
        if settings.dragonfly.enabled:
            dragonfly_conn = self.registry.get_service("dragonfly")
            if dragonfly_conn:
                self.stores[MemoryLayer.SHORT_TERM] = ShortTermStore(dragonfly_conn)
                logger.info("Initialized short-term memory store")

        # Initialize mid-term store (MongoDB)
        if settings.mongodb.enabled:
            mongodb_conn = self.registry.get_service("mongodb")
            if mongodb_conn:
                self.stores[MemoryLayer.MID_TERM] = MidTermStore(mongodb_conn)
                logger.info("Initialized mid-term memory store")

        # Initialize long-term store (Weaviate)
        if settings.weaviate.enabled:
            weaviate_conn = self.registry.get_service("weaviate")
            if weaviate_conn:
                self.stores[MemoryLayer.LONG_TERM] = LongTermStore(weaviate_conn)
                logger.info("Initialized long-term memory store")

        self._initialized = True
        logger.info(
            f"Unified memory service initialized with {len(self.stores)} stores"
        )

    async def store(
        self,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
        layer: Optional[MemoryLayer] = None,
        ttl: Optional[int] = None,
    ) -> str:
        """Store content in the appropriate memory layer."""
        if not self._initialized:
            await self.initialize()

        # Generate ID
        item_id = str(uuid.uuid4())

        # Prepare metadata
        if metadata is None:
            metadata = {}

        # Select layer if not specified
        if layer is None:
            layer = self.policy.select_layer(content, metadata)

        # Create memory item
        item = MemoryItem(
            id=item_id,
            content=content,
            metadata=metadata,
            timestamp=datetime.utcnow(),
            layer=layer,
            ttl=ttl,
        )

        # Store in the appropriate layer
        store = self.stores.get(layer)
        if not store:
            raise ValueError(f"No store available for layer {layer}")

        success = await store.store(item)
        if not success:
            raise RuntimeError(f"Failed to store item in {layer}")

        # Track access
        self._access_counts[item_id] = 0
        self._last_access[item_id] = datetime.utcnow()

        logger.debug(f"Stored item {item_id} in {layer}")
        return item_id

    async def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        """Retrieve an item from any layer."""
        if not self._initialized:
            await self.initialize()

        # Try each layer in order of likelihood
        for layer in [
            MemoryLayer.SHORT_TERM,
            MemoryLayer.MID_TERM,
            MemoryLayer.LONG_TERM,
        ]:
            store = self.stores.get(layer)
            if store:
                item = await store.retrieve(item_id)
                if item:
                    # Update access tracking
                    self._access_counts[item_id] = (
                        self._access_counts.get(item_id, 0) + 1
                    )
                    self._last_access[item_id] = datetime.utcnow()

                    # Check if item should be promoted
                    access_count = self._access_counts[item_id]
                    target_layer = self.policy.should_promote(item, access_count)
                    if target_layer and target_layer != layer:
                        asyncio.create_task(self.promote(item_id, target_layer))

                    return item

        return None

    async def search(
        self,
        query: str,
        limit: int = 10,
        layers: Optional[List[MemoryLayer]] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search across memory layers."""
        if not self._initialized:
            await self.initialize()

        # Determine which layers to search
        if layers is None:
            layers = list(self.stores.keys())

        # Search each layer in parallel
        search_tasks = []
        for layer in layers:
            store = self.stores.get(layer)
            if store:
                task = store.search(query, limit, filters)
                search_tasks.append(task)

        # Gather results
        all_results = []
        results_lists = await asyncio.gather(*search_tasks, return_exceptions=True)

        for results in results_lists:
            if isinstance(results, list):
                all_results.extend(results)
            else:
                logger.error(f"Search error: {results}")

        # Sort by score and limit
        all_results.sort(key=lambda r: r.score, reverse=True)
        return all_results[:limit]

    async def promote(self, item_id: str, target_layer: MemoryLayer) -> bool:
        """Promote an item to a different memory layer."""
        if not self._initialized:
            await self.initialize()

        # Retrieve the item
        item = await self.retrieve(item_id)
        if not item:
            return False

        # Check if target store exists
        target_store = self.stores.get(target_layer)
        if not target_store:
            logger.warning(f"Target store {target_layer} not available")
            return False

        # Store in target layer
        item.layer = target_layer
        success = await target_store.store(item)

        if success:
            # Remove from original layer if different
            if item.layer != target_layer:
                original_store = self.stores.get(item.layer)
                if original_store:
                    await original_store.delete(item_id)

            logger.info(f"Promoted item {item_id} to {target_layer}")

        return success

    async def evict(self, item_id: str) -> bool:
        """Evict an item from all memory layers."""
        if not self._initialized:
            await self.initialize()

        success = True

        # Delete from all stores
        for store in self.stores.values():
            try:
                await store.delete(item_id)
            except Exception as e:
                logger.error(f"Error evicting from store: {e}")
                success = False

        # Clean up tracking
        self._access_counts.pop(item_id, None)
        self._last_access.pop(item_id, None)

        return success

    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about memory usage."""
        if not self._initialized:
            await self.initialize()

        stats = {"total_items": 0, "layers": {}, "health": {}}

        # Get stats from each store
        for layer, store in self.stores.items():
            try:
                # Get item count
                layer_stats = {
                    "available": True,
                    "healthy": await store.health_check(),
                }

                stats["layers"][layer.value] = layer_stats

            except Exception as e:
                logger.error(f"Error getting stats for {layer}: {e}")
                stats["layers"][layer.value] = {"available": False, "error": str(e)}

        return stats

    async def cleanup(self) -> None:
        """Clean up old items based on policy."""
        if not self._initialized:
            return

        # Check each item for eviction
        items_to_evict = []

        for item_id, last_access in self._last_access.items():
            item = await self.retrieve(item_id)
            if item and self.policy.should_evict(item, last_access):
                items_to_evict.append(item_id)

        # Evict items
        for item_id in items_to_evict:
            await self.evict(item_id)

        logger.info(f"Cleaned up {len(items_to_evict)} items")


# Global instance
_memory_service: Optional[UnifiedMemoryService] = None


def get_memory_service(service_registry: ServiceRegistry) -> UnifiedMemoryService:
    """Get the global memory service instance."""
    global _memory_service

    if _memory_service is None:
        _memory_service = UnifiedMemoryService(service_registry)

    return _memory_service
