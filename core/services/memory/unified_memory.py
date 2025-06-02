"""
Unified memory service implementation.

This module provides the main memory service that coordinates
across all memory layers (short-term, mid-term, long-term).
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Literal  # Added Literal

import weaviate  # For Weaviate client types
import weaviate.classes.query as wvcq  # For Weaviate Client v4 query classes like Filter

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
                await self.connection.setex(item.id, item.ttl, json.dumps(data))  # Use json.dumps
            else:
                await self.connection.set(item.id, json.dumps(data))  # Use json.dumps
            return True
        except Exception as e:
            logger.error(f"Error storing in short-term memory: {e}")
            return False

    async def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        """Retrieve item from DragonflyDB."""
        try:
            data_str = await self.connection.get(item_id)
            if data_str:
                parsed = json.loads(data_str)  # Use json.loads
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

    async def search(self, query: str, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search is not supported in short-term memory."""
        return []

    async def health_check(self) -> bool:
        """Check if DragonflyDB is healthy."""
        try:
            await self.connection.ping()
            return True
        except Exception as e:  # Broad exception for connection issues
            logger.error(f"Short-term store health check failed: {e}")
            return False

class MidTermStore(MemoryStore):
    """Mid-term memory store using MongoDB."""

    def __init__(self, connection):  # connection is expected to be a MongoDB database object
        self.db_connection = connection
        # Ensure collection name is configurable or a sensible default
        settings = get_settings()
        self.collection_name = getattr(settings.mongodb, "collection_name", "memory_items")
        self.collection = self.db_connection[self.collection_name]

    async def store(self, item: MemoryItem) -> bool:
        """Store item in MongoDB."""
        try:
            document = {
                "_id": item.id,
                "content": item.content,
                "metadata": item.metadata,
                "timestamp": item.timestamp,  # Store as BSON date
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

    async def search(self, query: str, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search in MongoDB using text search."""
        try:
            # Build query
            search_query: Dict[str, Any] = {"$text": {"$search": query}}
            if filters:  # Assuming filters are MongoDB compatible
                search_query.update(filters)

            # Execute search
            # Ensure text index exists on 'content' or relevant fields in MongoDB
            cursor = self.collection.find(search_query).limit(limit)
            # Add sort by text score: .sort([("score", {"$meta": "textScore"})])
            # Requires text index and projection of score.

            results = []
            async for doc in cursor:
                item = MemoryItem(
                    id=doc["_id"],
                    content=doc["content"],
                    metadata=doc["metadata"],
                    timestamp=doc["timestamp"],
                    layer=MemoryLayer(doc["layer"]),
                )
                # MongoDB text search score can be accessed via {"$meta": "textScore"}
                # For simplicity, using 1.0. A real score would be better.
                score = doc.get("score", 1.0)  # if $meta textScore is projected
                results.append(SearchResult(item=item, score=score))

            return results
        except Exception as e:
            logger.error(f"Error searching in mid-term memory: {e}")
            return []

    async def health_check(self) -> bool:
        """Check if MongoDB is healthy."""
        try:
            await self.db_connection.command("ping")  # Use the database object for ping
            return True
        except Exception:  # Broad exception for connection issues
            return False

class LongTermStore(MemoryStore):
    """Long-term memory store using Weaviate."""

    def __init__(self, connection: weaviate.WeaviateClient, class_name: str = "MemoryItem"):
        self.client = connection
        self.class_name = class_name
        logger.info(f"LongTermStore initialized for Weaviate class: {self.class_name}")

    async def store(self, item: MemoryItem) -> bool:
        """Store item in Weaviate."""
        try:
            properties = {
                "content": item.content,
                "metadata_json": json.dumps(item.metadata or {}),
                "timestamp_iso": item.timestamp.isoformat(),
                "layer": item.layer.value,
                "item_id": item.id,
            }
            collection = self.client.collections.get(self.class_name)
            vector_to_use = item.metadata.get("vector") if item.metadata else None

            uuid_generated = collection.data.insert(properties=properties, vector=vector_to_use)
            logger.debug(f"Stored item {item.id} in Weaviate ({self.class_name}) with Weaviate UUID {uuid_generated}")
            return True
        except Exception as e:
            logger.error(f"Error storing item {item.id} in Weaviate ({self.class_name}): {e}", exc_info=True)
            return False

    async def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        """Retrieve item from Weaviate using its original item_id."""
        try:
            collection = self.client.collections.get(self.class_name)
            response = collection.query.fetch_objects(
                filters=wvcq.Filter.by_property("item_id").equal(item_id), limit=1
            )
            if response.objects:
                obj = response.objects[0]
                metadata = json.loads(obj.properties.get("metadata_json", "{}"))
                metadata["weaviate_uuid"] = str(obj.uuid)
                return MemoryItem(
                    id=obj.properties.get("item_id", item_id),
                    content=obj.properties.get("content"),
                    metadata=metadata,
                    timestamp=datetime.fromisoformat(obj.properties.get("timestamp_iso")),
                    layer=MemoryLayer(obj.properties.get("layer")),
                )
            logger.warning(f"Item {item_id} not found in Weaviate ({self.class_name})")
        except Exception as e:
            logger.error(f"Error retrieving item {item_id} from Weaviate ({self.class_name}): {e}", exc_info=True)
        return None

    async def delete(self, item_id: str) -> bool:
        """Delete item from Weaviate using its original item_id."""
        try:
            collection = self.client.collections.get(self.class_name)
            query_response = collection.query.fetch_objects(
                filters=wvcq.Filter.by_property("item_id").equal(item_id),
                limit=1,
                return_metadata=wvcq.MetadataQuery(uuid=True),
            )
            if not query_response.objects:
                logger.warning(f"Item {item_id} not found for deletion in Weaviate ({self.class_name}).")
                return False
            weaviate_uuid = query_response.objects[0].uuid
            collection.data.delete_by_id(uuid=weaviate_uuid)
            logger.debug(
                f"Attempted deletion of item {item_id} (Weaviate UUID {weaviate_uuid}) from {self.class_name}."
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting item {item_id} from Weaviate ({self.class_name}): {e}", exc_info=True)
            return False

    async def search(
        self,
        query_text: str,
        limit: int = 10,
        filters: Optional[wvcq.Filter] = None,  # Expects a Weaviate Filter object
        search_type: Literal["semantic", "hybrid", "keyword"] = "hybrid",
        alpha: float = 0.5,
        vector: Optional[List[float]] = None,
        query_properties: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """Search in Weaviate using specified search type."""
        try:
            collection = self.client.collections.get(self.class_name)
            response = None
            common_params: Dict[str, Any] = {  # Define type for common_params
                "limit": limit,
                "filters": filters,
                "return_properties": None,
                "return_metadata": wvcq.MetadataQuery(score=True, explain_score=True, uuid=True),
                "include_vector": False,
            }

            if search_type == "semantic":
                if vector:
                    response = collection.query.near_vector(near_vector=vector, **common_params)
                else:
                    response = collection.query.near_text(query=query_text, **common_params)
            elif search_type == "hybrid":
                response = collection.query.hybrid(
                    query=query_text, alpha=alpha, vector=vector, query_properties=query_properties, **common_params
                )
            elif search_type == "keyword":
                response = collection.query.hybrid(
                    query=query_text,
                    alpha=0.0,
                    query_properties=query_properties or ["content", "metadata_json"],
                    **common_params,
                )
            else:
                logger.warning(f"Unsupported search_type '{search_type}' for LongTermStore. Defaulting to hybrid.")
                response = collection.query.hybrid(query=query_text, alpha=alpha, **common_params)

            results = []
            if response and response.objects:
                for obj in response.objects:
                    metadata = json.loads(obj.properties.get("metadata_json", "{}"))
                    metadata["weaviate_uuid"] = str(obj.uuid)
                    item = MemoryItem(
                        id=obj.properties.get("item_id"),
                        content=obj.properties.get("content"),
                        metadata=metadata,
                        timestamp=datetime.fromisoformat(obj.properties.get("timestamp_iso")),
                        layer=MemoryLayer(obj.properties.get("layer")),
                    )
                    score = obj.metadata.score if obj.metadata and obj.metadata.score is not None else 0.0
                    results.append(SearchResult(item=item, score=score))
            return results
        except Exception as e:
            logger.error(
                f"Error searching in Weaviate ({self.class_name}) with type '{search_type}': {e}", exc_info=True
            )
            return []

    async def health_check(self) -> bool:
        """Check if Weaviate is healthy."""
        try:
            return self.client.is_ready()
        except Exception as e:
            logger.error(f"Weaviate health check failed: {e}")
            return False

class DefaultMemoryPolicy(MemoryPolicy):
    """Default memory management policy."""

    def should_promote(self, item: MemoryItem, access_count: int) -> Optional[MemoryLayer]:
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
            MemoryLayer.LONG_TERM: timedelta(days=30),  # Or never evict from long-term based on time
        }
        # If item has its own TTL, prioritize that for short/mid term
        if item.ttl and item.layer != MemoryLayer.LONG_TERM:
            # This logic assumes last_access is creation time if ttl is set from creation
            # A more robust TTL would be handled by the store itself (e.g. Redis EXPIRE)
            # For now, we'll compare with timestamp for TTL items.
            return datetime.utcnow() - item.timestamp > timedelta(seconds=item.ttl)

        age_limit = age_limits.get(item.layer, timedelta(days=36500))  # Default to very long for safety
        return datetime.utcnow() - last_access > age_limit

    def select_layer(self, content: Any, metadata: Dict[str, Any]) -> MemoryLayer:
        """Select layer based on content type and metadata."""
        if metadata.get("target_layer"):
            try:
                return MemoryLayer[metadata["target_layer"].upper()]
            except KeyError:
                logger.warning(f"Invalid target_layer '{metadata['target_layer']}' specified. Using default policy.")

        if metadata.get("temporary", False) or metadata.get("is_cache", False):
            return MemoryLayer.SHORT_TERM

        # Example: if content is large or explicitly marked for vectorization
        if isinstance(content, (dict, list)) and len(json.dumps(content)) > 1024 * 5:  # 5KB
            return MemoryLayer.LONG_TERM
        if metadata.get("vectorize", False) or metadata.get("semantic_search_candidate", False):
            return MemoryLayer.LONG_TERM

        return MemoryLayer.MID_TERM

class UnifiedMemoryService(MemoryService):
    """
    Unified memory service that coordinates across all memory layers.
    """

    def __init__(self, service_registry: ServiceRegistry, policy: Optional[MemoryPolicy] = None):
        self.registry = service_registry
        self.policy = policy or DefaultMemoryPolicy()
        self.stores: Dict[MemoryLayer, MemoryStore] = {}
        self._access_counts: Dict[str, int] = {}  # In-memory, consider persistent tracking for scale
        self._last_access: Dict[str, datetime] = {}  # In-memory
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all memory stores."""
        if self._initialized:
            return

        settings = get_settings()

        if settings.dragonfly.enabled:
            dragonfly_conn = self.registry.get_service("dragonfly")
            if dragonfly_conn:
                self.stores[MemoryLayer.SHORT_TERM] = ShortTermStore(dragonfly_conn)
                logger.info("Initialized short-term memory store (DragonflyDB)")

        if settings.mongodb.enabled:
            mongodb_db_obj = self.registry.get_service("mongodb")  # Expects a Database object
            if mongodb_db_obj:
                self.stores[MemoryLayer.MID_TERM] = MidTermStore(mongodb_db_obj)
                logger.info("Initialized mid-term memory store (MongoDB)")

        if settings.weaviate.enabled:
            weaviate_client_conn = self.registry.get_service("weaviate_client")  # Expects a WeaviateClient
            weaviate_class_name = getattr(settings.weaviate, "class_name", "MemoryItem")
            if weaviate_client_conn:
                self.stores[MemoryLayer.LONG_TERM] = LongTermStore(weaviate_client_conn, class_name=weaviate_class_name)
                logger.info(f"Initialized long-term memory store (Weaviate class: '{weaviate_class_name}')")

        self._initialized = True
        logger.info(f"Unified memory service initialized with {len(self.stores)} stores: {list(self.stores.keys())}")

    async def store(
        self,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
        layer: Optional[MemoryLayer] = None,
        ttl: Optional[int] = None,
        item_id: Optional[str] = None,  # Allow providing an ID
        vector: Optional[List[float]] = None,  # Allow providing a vector
    ) -> str:
        """Store content in the appropriate memory layer."""
        if not self._initialized:
            await self.initialize()
        item_id = item_id or str(uuid.uuid4())
        metadata = metadata or {}
        if vector:
            metadata["vector"] = vector  # Pass vector via metadata to LongTermStore

        effective_layer = layer or self.policy.select_layer(content, metadata)

        item = MemoryItem(
            id=item_id, content=content, metadata=metadata, timestamp=datetime.utcnow(), layer=effective_layer, ttl=ttl
        )

        store = self.stores.get(effective_layer)
        if not store:
            raise ValueError(f"No store available for layer {effective_layer}")

        success = await store.store(item)
        if not success:
            raise RuntimeError(f"Failed to store item {item_id} in {effective_layer}")

        self._access_counts[item_id] = 0
        self._last_access[item_id] = datetime.utcnow()
        logger.debug(f"Stored item {item_id} in {effective_layer}")
        return item_id

    async def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        """Retrieve an item from any layer, handling promotion."""
        if not self._initialized:
            await self.initialize()

        # Define search order for retrieval
        # Typically, we'd check hotter caches first.
        retrieval_order = [MemoryLayer.SHORT_TERM, MemoryLayer.MID_TERM, MemoryLayer.LONG_TERM]

        for current_layer_enum in retrieval_order:
            store = self.stores.get(current_layer_enum)
            if store:
                item = await store.retrieve(item_id)
                if item:
                    self._access_counts[item_id] = self._access_counts.get(item_id, 0) + 1
                    self._last_access[item_id] = datetime.utcnow()

                    # Policy check for promotion
                    target_promote_layer = self.policy.should_promote(item, self._access_counts[item_id])
                    if target_promote_layer and target_promote_layer != item.layer:
                        # Non-blocking promotion
                        asyncio.create_task(self.promote(item_id, target_promote_layer, original_item=item))
                    return item
        return None

    def _translate_simple_filters_to_weaviate(self, simple_filters: Optional[Dict[str, Any]]) -> Optional[wvcq.Filter]:
        """
        Translates a simple dictionary of filters into Weaviate's Filter object structure.
        Key format: "path.to.property__operator" (e.g., "metadata.category__eq").
        Supported operators: eq, neq, gt, gte, lt, lte, like, is_none, contains_any, contains_all.
        """
        if not simple_filters:
            return None

        conditions = []
        for key_op, value in simple_filters.items():
            parts = key_op.split("__")
            if len(parts) < 2:
                logger.warning(f"Invalid filter key format '{key_op}'. Skipping. Expected 'path__operator'.")
                continue

            path_str = parts[0]
            operator = parts[-1].lower()  # Last part is operator
            if len(parts) > 2:  # Path contained double underscores
                path_str = "__".join(parts[:-1])

            path_list = path_str.split(".")

            try:
                prop_filter_starter = (
                    wvcq.Filter.by_property(path_list[0]) if len(path_list) == 1 else wvcq.Filter.by_property(path_list)
                )

                if operator == "eq":
                    conditions.append(prop_filter_starter.equal(value))
                elif operator == "neq":
                    conditions.append(prop_filter_starter.not_equal(value))
                elif operator == "gt":
                    conditions.append(prop_filter_starter.greater_than(value))
                elif operator == "gte":
                    conditions.append(prop_filter_starter.greater_equal(value))
                elif operator == "lt":
                    conditions.append(prop_filter_starter.less_than(value))
                elif operator == "lte":
                    conditions.append(prop_filter_starter.less_equal(value))
                elif operator == "like":
                    if not isinstance(value, str):
                        logger.warning(
                            f"'like' operator for '{path_str}' requires a string value. Got {type(value)}. Skipping."
                        )
                        continue
                    conditions.append(prop_filter_starter.like(value))
                elif operator == "is_none":
                    if not isinstance(value, bool):
                        logger.warning(
                            f"'is_none' operator for '{path_str}' requires a boolean value. Got {type(value)}. Skipping."
                        )
                        continue
                    conditions.append(wvcq.Filter.by_property(path_list).is_none(value))  # is_none is different
                elif operator == "contains_any":
                    if not isinstance(value, list):
                        logger.warning(
                            f"'contains_any' operator for '{path_str}' requires a list value. Got {type(value)}. Skipping."
                        )
                        continue
                    conditions.append(prop_filter_starter.contains_any(value))
                elif operator == "contains_all":
                    if not isinstance(value, list):
                        logger.warning(
                            f"'contains_all' operator for '{path_str}' requires a list value. Got {type(value)}. Skipping."
                        )
                        continue
                    conditions.append(prop_filter_starter.contains_all(value))
                else:
                    logger.warning(
                        f"Unsupported Weaviate filter operator '{operator}' for path '{path_str}'. Skipping."
                    )
            except Exception as e:
                logger.error(f"Error translating filter '{key_op}': {value} - {e}", exc_info=True)

        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return wvcq.Filter.all_of(conditions)

    async def search(
        self,
        query: str,
        limit: int = 10,
        layers: Optional[List[MemoryLayer]] = None,
        filters: Optional[Dict[str, Any]] = None,
        search_type: Literal["semantic", "keyword", "hybrid"] = "hybrid",
        alpha: float = 0.5,
        query_vector: Optional[List[float]] = None,
        weaviate_query_properties: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """Search across memory layers with specified search type and filters."""
        if not self._initialized:
            await self.initialize()

        target_layers: List[MemoryLayer] = layers or []
        if not target_layers:
            if search_type == "semantic" or search_type == "hybrid":
                if MemoryLayer.LONG_TERM in self.stores:
                    target_layers.append(MemoryLayer.LONG_TERM)
                if (
                    search_type == "hybrid" and MemoryLayer.MID_TERM in self.stores
                ):  # Optionally include mid-term for hybrid's keyword part
                    target_layers.append(MemoryLayer.MID_TERM)
            elif search_type == "keyword":
                if MemoryLayer.MID_TERM in self.stores:
                    target_layers.append(MemoryLayer.MID_TERM)
                if MemoryLayer.LONG_TERM in self.stores:
                    target_layers.append(MemoryLayer.LONG_TERM)  # Weaviate can also do keyword
            if not target_layers:
                target_layers = list(self.stores.keys())

        logger.debug(f"Searching in layers: {target_layers} for query '{query}' with type '{search_type}'")

        search_tasks = []
        for layer_enum in target_layers:
            store = self.stores.get(layer_enum)
            if not store:
                continue

            if isinstance(store, LongTermStore):
                weaviate_native_filters = self._translate_simple_filters_to_weaviate(filters)
                task = store.search(
                    query_text=query,
                    limit=limit,
                    filters=weaviate_native_filters,
                    search_type=search_type,
                    alpha=alpha,
                    vector=query_vector,
                    query_properties=weaviate_query_properties,
                )
            elif isinstance(store, MidTermStore):
                # MongoDB uses dict-based filters directly for $text search context
                # Or requires a different translation for its find() query filter document.
                mongo_filters = filters  # Assuming simple filters are for MongoDB if it's the target
                if search_type != "keyword" and layer_enum == MemoryLayer.MID_TERM:  # Only keyword search for Mongo
                    logger.debug(f"Skipping non-keyword search for MidTermStore on layer {layer_enum}")
                    continue
                task = store.search(query, limit, mongo_filters)
            elif isinstance(store, ShortTermStore):
                continue  # ShortTermStore does not support search
            else:  # Generic store, pass filters as is
                task = store.search(query, limit, filters)
            search_tasks.append(task)

        all_results: List[SearchResult] = []
        if search_tasks:
            results_lists = await asyncio.gather(*search_tasks, return_exceptions=True)
            for results_list_or_exception in results_lists:
                if isinstance(results_list_or_exception, list):
                    all_results.extend(results_list_or_exception)
                elif isinstance(results_list_or_exception, Exception):
                    logger.error(f"Search error in one of the layers: {results_list_or_exception}", exc_info=True)

        unique_results_dict: Dict[str, SearchResult] = {}
        for res in all_results:
            if (
                res.item.id not in unique_results_dict
                or (
                    res.score is not None
                    and unique_results_dict[res.item.id].score is not None
                    and res.score > unique_results_dict[res.item.id].score
                )
                or (res.score is not None and unique_results_dict[res.item.id].score is None)
            ):  # Prefer scored results
                unique_results_dict[res.item.id] = res

        final_results = sorted(list(unique_results_dict.values()), key=lambda r: r.score or 0.0, reverse=True)
        return final_results[:limit]

    async def promote(
        self, item_id: str, target_layer: MemoryLayer, original_item: Optional[MemoryItem] = None
    ) -> bool:
        """Promote an item to a different memory layer. original_item can be passed to avoid re-retrieval."""
        if not self._initialized:
            await self.initialize()

        item_to_promote = original_item
        if not item_to_promote:
            item_to_promote = await self.retrieve(item_id)  # retrieve already updates access counts

        if not item_to_promote:
            logger.warning(f"Item {item_id} not found, cannot promote.")
            return False

        current_layer = item_to_promote.layer
        if current_layer == target_layer:
            logger.debug(f"Item {item_id} is already in target layer {target_layer}. No promotion needed.")
            return True

        target_store = self.stores.get(target_layer)
        if not target_store:
            logger.warning(f"Target store for layer {target_layer} not available for promotion.")
            return False

        item_to_promote.layer = target_layer  # Update layer before storing
        # Preserve original TTL if promoting to short-term, otherwise clear it unless explicitly set for new layer
        if target_layer != MemoryLayer.SHORT_TERM:
            item_to_promote.ttl = None

        success = await target_store.store(item_to_promote)

        if success:
            logger.info(f"Promoted item {item_id} from {current_layer} to {target_layer}.")
            # Optionally remove from original layer if it's a "move" not a "copy then delete"
            # Current policy implies it's a copy, original might get evicted by its own policy.
            # If it should be a strict move, delete from original_store here.
            # original_store = self.stores.get(current_layer)
            # if original_store and current_layer != MemoryLayer.LONG_TERM: # Avoid deleting from LTS usually
            #    await original_store.delete(item_id)
        else:
            logger.error(f"Failed to store item {item_id} in target layer {target_layer} during promotion.")
        return success

    async def evict(self, item_id: str) -> bool:
        """Evict an item from all memory layers."""
        if not self._initialized:
            await self.initialize()
        deleted_any = False
        for layer, store in self.stores.items():
            try:
                if await store.delete(item_id):
                    logger.debug(f"Evicted item {item_id} from {layer.value}")
                    deleted_any = True
            except Exception as e:
                logger.error(f"Error evicting item {item_id} from {layer.value}: {e}", exc_info=True)

        if item_id in self._access_counts:
            del self._access_counts[item_id]
        if item_id in self._last_access:
            del self._last_access[item_id]

        if deleted_any:
            logger.info(f"Evicted item {item_id} from relevant stores.")
        return deleted_any

    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about memory usage and health of each layer."""
        if not self._initialized:
            await self.initialize()
        stats = {"layers": {}}
        for layer, store in self.stores.items():
            try:
                is_healthy = await store.health_check()
                # Item count might be expensive; consider if it's always needed or sampled
                # For now, not including item count per layer to keep health check fast
                stats["layers"][layer.value] = {
                    "available": True,
                    "healthy": is_healthy,
                    # "item_count": await store.count() # If a count method exists
                }
            except Exception as e:
                logger.error(f"Error getting stats for {layer.value}: {e}", exc_info=True)
                stats["layers"][layer.value] = {"available": False, "healthy": False, "error": str(e)}

        stats["overall_access_tracked_items"] = len(self._access_counts)
        return stats

    async def cleanup(self) -> None:
        """Clean up old items based on policy."""
        if not self._initialized:
            return
        items_to_evict = []
        # Create a copy of keys for safe iteration if _last_access can be modified by retrieve->promote
        for item_id, last_access_dt in list(self._last_access.items()):
            # Retrieve item to get its current layer for policy check
            # This also updates its last_access if retrieved, so policy should use the passed last_access_dt
            item = await self.retrieve(item_id)  # This might trigger promotion
            if item:  # Re-fetch to get potentially updated layer after promotion
                current_item_state = await self.retrieve(item_id)  # Could be None if evicted by another process
                if current_item_state and self.policy.should_evict(current_item_state, last_access_dt):
                    items_to_evict.append(item_id)
            elif (datetime.utcnow() - last_access_dt) > timedelta(days=30):  # Fallback for untracked/deleted items
                items_to_evict.append(item_id)

        evicted_count = 0
        for item_id_to_evict in items_to_evict:
            if await self.evict(item_id_to_evict):
                evicted_count += 1
        if evicted_count > 0:
            logger.info(f"Memory cleanup: Evicted {evicted_count} items based on policy.")

_memory_service: Optional[UnifiedMemoryService] = None

def get_memory_service(service_registry: ServiceRegistry) -> UnifiedMemoryService:
    """Get the global memory service instance."""
    global _memory_service
    if _memory_service is None:
        logger.info("Creating new UnifiedMemoryService instance.")
        _memory_service = UnifiedMemoryService(service_registry)
    elif _memory_service.registry is not service_registry:
        logger.warning("UnifiedMemoryService re-initialized with a new service registry.")
        _memory_service = UnifiedMemoryService(service_registry)
        _memory_service._initialized = False  # Force re-initialization of stores

    return _memory_service
