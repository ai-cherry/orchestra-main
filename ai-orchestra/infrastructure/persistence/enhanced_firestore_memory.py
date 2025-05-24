"""
WARNING: This file is strictly a facade for Firestore-based enhanced memory.
- Do NOT add any business logic, type definitions, or placeholder classes here.
- All logic must be delegated to specialized components in firestore_components/.
- All type definitions and interfaces must be imported from their actual modules.

Refactored Firestore implementation of the EnhancedMemoryProvider interface.
This class acts as a facade, delegating operations to specialized
firestore_components for CRUD, querying, serialization, expiry, and batch processing.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ai_orchestra.core.events.memory_events import (
    MemoryEventBus,
    MemoryItemAccessedEvent,
    MemoryItemCreatedEvent,
    MemoryItemDeletedEvent,
)
from ai_orchestra.core.interfaces.enhanced_memory import EnhancedMemoryProvider

from core.orchestrator.src.config.settings import Settings
from packages.shared.src.models.base_models import MemoryItem

from .firestore_components.firestore_batch_processor import FirestoreBatchProcessor
from .firestore_components.firestore_client_manager import FirestoreClientManager
from .firestore_components.firestore_crud_operations import FirestoreCrudOperations
from .firestore_components.firestore_expiry_manager import FirestoreExpiryManager
from .firestore_components.firestore_query_engine import FirestoreQueryEngine
from .firestore_components.memory_item_serializer import MemoryItemSerializer

logger = logging.getLogger(__name__)


class EnhancedFirestoreMemoryProvider(EnhancedMemoryProvider):
    """
    Facade for Firestore-based enhanced memory, delegating to specialized components.
    """

    DEFAULT_COLLECTION_NAME = "enhanced_memory_items"

    def __init__(self, settings: Settings, collection_name: Optional[str] = None):
        self._settings = settings
        self._collection_name = collection_name or self.DEFAULT_COLLECTION_NAME

        self._client_manager: Optional[FirestoreClientManager] = None
        self._crud_ops: Optional[FirestoreCrudOperations] = None
        self._serializer: Optional[MemoryItemSerializer] = None
        self._query_engine: Optional[FirestoreQueryEngine] = None
        self._expiry_manager: Optional[FirestoreExpiryManager] = None
        self._batch_processor: Optional[FirestoreBatchProcessor] = None
        self._event_bus = MemoryEventBus()

        self._is_initialized = False
        logger.info(
            f"EnhancedFirestoreMemoryProvider configured for collection '{self._collection_name}'. Call initialize() to connect."
        )

    async def initialize(self):
        if self._is_initialized:
            logger.info("EnhancedFirestoreMemoryProvider already initialized.")
            return

        logger.info("Initializing EnhancedFirestoreMemoryProvider components...")
        self._client_manager = FirestoreClientManager(app_settings=self._settings)
        firestore_client = await self._client_manager.get_client()

        self._serializer = MemoryItemSerializer()
        self._crud_ops = FirestoreCrudOperations(firestore_client, self._collection_name)
        self._query_engine = FirestoreQueryEngine(firestore_client, self._collection_name, self._serializer)
        self._expiry_manager = FirestoreExpiryManager(firestore_client, self._collection_name, self._event_bus)
        self._batch_processor = FirestoreBatchProcessor(firestore_client, self._collection_name)

        self._is_initialized = True
        logger.info("EnhancedFirestoreMemoryProvider components initialized successfully.")

    async def close(self):
        if self._client_manager:
            await self._client_manager.close_client()
            logger.info("EnhancedFirestoreMemoryProvider connections closed.")
        self._is_initialized = False

    def _ensure_initialized(self):
        if not self._is_initialized:
            raise RuntimeError("EnhancedFirestoreMemoryProvider is not initialized. Call initialize() first.")

    async def store_item(self, item: MemoryItem, ttl: Optional[int] = None) -> bool:
        self._ensure_initialized()
        assert (
            self._crud_ops and self._serializer and self._expiry_manager and self._event_bus
        ), "CRUD ops, serializer, expiry_manager, or event_bus not initialized"

        firestore_data = self._serializer.to_firestore(item)

        calculated_expiry = None
        if ttl is not None:
            calculated_expiry = self._expiry_manager.calculate_expiry_timestamp(ttl)
        elif getattr(item, "expiry", None):
            calculated_expiry = item.expiry  # Use item's own expiry if explicitly set
        # elif hasattr(item, 'default_ttl_seconds') and item.default_ttl_seconds:
        #      calculated_expiry = self._expiry_manager.calculate_expiry_timestamp(item.default_ttl_seconds)

        if calculated_expiry:
            firestore_data["expiry"] = self._serializer._ensure_utc(calculated_expiry)
        else:
            firestore_data.pop("expiry", None)

        success = await self._crud_ops.create_or_update_item(item.id, firestore_data)
        if success:
            await self._event_bus.publish(MemoryItemCreatedEvent(item_id=item.id))
        return success

    async def retrieve_item(self, id: str) -> Optional[MemoryItem]:
        self._ensure_initialized()
        assert (
            self._crud_ops and self._serializer and self._expiry_manager and self._event_bus
        ), "CRUD ops, serializer, expiry_manager, or event_bus not initialized"

        firestore_data = await self._crud_ops.get_item(id)
        if not firestore_data:
            return None

        expiry_timestamp_from_db = firestore_data.get("expiry")
        if expiry_timestamp_from_db:
            expiry_dt = self._serializer._to_datetime(expiry_timestamp_from_db)
            if expiry_dt and expiry_dt < datetime.now(timezone.utc):
                logger.info(f"Item '{id}' found but is expired. Auto-deleting.")
                await self._crud_ops.delete_item(id)
                await self._event_bus.publish(MemoryItemDeletedEvent(item_id=id))
                return None

        item = self._serializer.to_memory_item(id, firestore_data)
        await self._event_bus.publish(MemoryItemAccessedEvent(item_id=id))
        return item

    async def delete_item(self, id: str) -> bool:
        self._ensure_initialized()
        assert self._crud_ops and self._event_bus, "CRUD ops or event_bus not initialized"
        success = await self._crud_ops.delete_item(id)
        if success:
            await self._event_bus.publish(MemoryItemDeletedEvent(item_id=id))
        return success

    async def item_exists(self, id: str) -> bool:
        self._ensure_initialized()
        assert (
            self._crud_ops and self._serializer and self._expiry_manager
        ), "CRUD ops, serializer or expiry_manager not initialized"

        firestore_data = await self._crud_ops.get_item(id)
        if not firestore_data:
            return False

        expiry_timestamp_from_db = firestore_data.get("expiry")
        if expiry_timestamp_from_db:
            expiry_dt = self._serializer._to_datetime(expiry_timestamp_from_db)
            if expiry_dt and expiry_dt < datetime.now(timezone.utc):
                # Optionally log that it exists but is expired, but for item_exists, it effectively doesn't.
                return False

        return True

    async def query_items(
        self,
        filters: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        page_size: int = 100,
        order_direction: str = "ASCENDING",
    ) -> List[MemoryItem]:
        self._ensure_initialized()
        assert self._query_engine is not None, "Query engine not initialized"
        items = []
        async for item in self._query_engine.stream_query_results(
            filters=filters, tags=tags, order_by=order_by, order_direction=order_direction
        ):
            items.append(item)
        return items

    async def batch_store_items(self, items: List[MemoryItem], merge: bool = False) -> Dict[str, int]:
        self._ensure_initialized()
        assert (
            self._batch_processor is not None and self._serializer is not None and self._expiry_manager is not None
        ), "Batch processor, serializer, or expiry manager not initialized"

        items_data: Dict[str, Dict[str, Any]] = {}
        for item in items:
            firestore_data = self._serializer.to_firestore(item)
            calculated_expiry = getattr(item, "expiry", None)
            if calculated_expiry:
                firestore_data["expiry"] = self._serializer._ensure_utc(calculated_expiry)
            elif "expiry" in firestore_data:
                del firestore_data["expiry"]
            items_data[item.id] = firestore_data

        return await self._batch_processor.batch_set_items(items_data, merge=merge)

    async def batch_delete_items(self, item_ids: List[str]) -> Dict[str, int]:
        self._ensure_initialized()
        assert (
            self._batch_processor is not None and self._event_bus is not None
        ), "Batch processor or event_bus not initialized"
        result = await self._batch_processor.batch_delete_items(item_ids)
        if result.get("successful", 0) > 0:
            # Emit individual delete events for each id for auditability
            for item_id in item_ids:
                await self._event_bus.publish(MemoryItemDeletedEvent(item_id=item_id))
        return result

    async def prune_all_expired_items(self) -> Dict[str, Any]:
        self._ensure_initialized()
        assert self._expiry_manager is not None, "Expiry manager not initialized"
        # The expiry manager handles its own event publishing internally during prune
        return await self._expiry_manager.prune_expired_items()

    # Implementation of EnhancedMemoryProvider interface methods

    async def store(self, item: MemoryItem) -> str:
        await self.store_item(item)
        return item.id

    async def retrieve(self, id: str) -> Optional[MemoryItem]:
        return await self.retrieve_item(id)

    async def delete(self, id: str) -> bool:
        return await self.delete_item(id)

    async def update(self, id: str, updates: Dict[str, Any]) -> bool:
        self._ensure_initialized()
        assert self._crud_ops is not None
        return await self._crud_ops.update_item(id, updates)

    async def query(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[MemoryItem]:
        return await self.query_items(filters=filters, page_size=limit or 100)
