"""
Manages Time-To-Live (TTL) and expiry logic for memory items stored in Firestore.
Includes functionality for checking item expiry and pruning expired documents.
"""
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, AsyncGenerator

from google.cloud.firestore_v1.async_client import AsyncClient as FirestoreAsyncClient
from google.cloud.firestore_v1.base_query import AsyncBaseQuery, FieldFilter
from google.cloud.firestore_v1.async_document import AsyncDocumentReference, AsyncDocumentSnapshot
from google.api_core.exceptions import DeadlineExceeded, ServiceUnavailable, ResourceExhausted

# TODO: Replace these with actual imports from your project
# from packages.shared.src.models.base_models import MemoryItem 
# from ai_orchestra.core.events.memory_events import MemoryEvent, EventType, get_event_bus

# Placeholder for MemoryEvent and EventType if not readily available
class PlaceholderMemoryEvent: # TODO: Replace with actual MemoryEvent
    def __init__(self, event_type: Any, key: str, **kwargs: Any):
        self.event_type = event_type
        self.key = key
        self.metadata = kwargs

class PlaceholderEventType: # TODO: Replace with actual EventType enum/class
    MEMORY_ITEM_EXPIRED = "MemoryItemExpired"
    MEMORY_ITEM_DELETED = "MemoryItemDeleted" # If pruning also publishes general delete

class PlaceholderEventBus: # TODO: Replace with actual EventBus interface/implementation
    async def publish(self, event: PlaceholderMemoryEvent) -> None:
        logger.info(f"Event published: type={event.event_type}, key={event.key}, metadata={event.metadata}")

def get_placeholder_event_bus() -> PlaceholderEventBus: # TODO: Replace with actual get_event_bus()
    return PlaceholderEventBus()


logger = logging.getLogger(__name__)

class FirestoreExpiryManager:
    """
    Manages TTL and expiry for Firestore-based memory items.
    """

    def __init__(self, 
                 firestore_client: FirestoreAsyncClient, 
                 collection_name: str,
                 event_bus: Optional[PlaceholderEventBus] = None): # TODO: Replace PlaceholderEventBus with actual type
        """
        Initializes the FirestoreExpiryManager.

        Args:
            firestore_client: An initialized instance of Firestore AsyncClient.
            collection_name: The name of the Firestore collection where items are stored.
            event_bus: An instance of the system's event bus for publishing expiry events.
        """
        if not isinstance(firestore_client, FirestoreAsyncClient):
            raise TypeError("firestore_client must be an instance of FirestoreAsyncClient.")
        if not collection_name or not isinstance(collection_name, str):
            raise ValueError("collection_name must be a non-empty string.")
        
        self.client: FirestoreAsyncClient = firestore_client
        self.collection_name: str = collection_name
        self._collection_ref = self.client.collection(self.collection_name)
        self.event_bus = event_bus or get_placeholder_event_bus() # TODO: Replace with actual get_event_bus()
        logger.info(f"FirestoreExpiryManager initialized for collection: {self.collection_name}")

    def calculate_expiry_timestamp(self, ttl_seconds: Optional[int]) -> Optional[datetime]:
        """
        Calculates a future expiry timestamp based on a TTL.

        Args:
            ttl_seconds: Time-to-live in seconds from now. If None, no expiry.

        Returns:
            A timezone-aware datetime object representing the expiry time (in UTC),
            or None if ttl_seconds is None.
        """
        if ttl_seconds is None:
            return None
        if not isinstance(ttl_seconds, int) or ttl_seconds < 0:
            raise ValueError("ttl_seconds must be a non-negative integer.")
        
        return datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

    async def is_item_expired(self, doc_snapshot: AsyncDocumentSnapshot, auto_delete: bool = False) -> bool:
        """
        Checks if a Firestore document snapshot represents an expired item.
        Optionally deletes the item if it's found to be expired.

        Args:
            doc_snapshot: The Firestore AsyncDocumentSnapshot to check.
            auto_delete: If True and the item is expired, attempt to delete it.

        Returns:
            True if the item is expired, False otherwise.
        """
        if not doc_snapshot.exists:
            return False # Non-existent item cannot be expired in this context

        data = doc_snapshot.to_dict()
        if data is None: # Should not happen if doc_snapshot.exists is True, but good practice
            logger.warning(f"Document snapshot for {doc_snapshot.id} has no data despite existing.")
            return False
            
        expiry_timestamp = data.get("expiry")

        if expiry_timestamp:
            # Ensure expiry_timestamp is a datetime object (Firestore client usually handles this)
            if isinstance(expiry_timestamp, str):
                try:
                    # Handle ISO format strings, common if not stored as Firestore Timestamp
                    dt_str = expiry_timestamp.upper().replace("Z", "+00:00")
                    expiry_timestamp = datetime.fromisoformat(dt_str)
                except ValueError:
                    logger.warning(f"Invalid expiry date format for item {doc_snapshot.id}: {expiry_timestamp}")
                    return False # Treat as not expired if format is wrong
            
            if not isinstance(expiry_timestamp, datetime):
                 logger.warning(f"Expiry field for item {doc_snapshot.id} is not a datetime object: {type(expiry_timestamp)}")
                 return False

            # Ensure UTC for comparison
            if expiry_timestamp.tzinfo is None:
                expiry_timestamp = expiry_timestamp.replace(tzinfo=timezone.utc)
            else:
                expiry_timestamp = expiry_timestamp.astimezone(timezone.utc)

            if datetime.now(timezone.utc) > expiry_timestamp:
                logger.debug(f"Item '{doc_snapshot.id}' is expired (expiry: {expiry_timestamp}).")
                if auto_delete:
                    logger.info(f"Auto-deleting expired item '{doc_snapshot.id}'.")
                    try:
                        await doc_snapshot.reference.delete()
                        await self.event_bus.publish(
                            PlaceholderMemoryEvent(PlaceholderEventType.MEMORY_ITEM_EXPIRED, key=doc_snapshot.id, reason="auto-deleted")
                        )
                    except Exception as e:
                        logger.error(f"Error auto-deleting expired item '{doc_snapshot.id}': {e}", exc_info=True)
                return True
        return False

    async def prune_expired_items(self, query_page_size: int = 200, delete_batch_size: int = 400) -> Dict[str, Any]:
        """
        Finds and deletes all expired items from the collection using batch operations.

        Args:
            query_page_size: Not directly used in this Firestore query version, but kept for API consistency if needed later.
            delete_batch_size: Number of documents to delete in each Firestore batch write.
                               Max 500, using a lower default for safety.
        Returns:
            A dictionary containing statistics about the pruning operation.
        """
        if delete_batch_size <= 0 or delete_batch_size > 500:
            delete_batch_size = 400 # Default to a safe value
            logger.warning("delete_batch_size adjusted to 400 (valid range 1-500).")

        logger.info(f"Starting pruning of expired items from '{self.collection_name}'.")
        start_time = time.monotonic()
        
        deleted_count = 0
        total_queried_for_expiry = 0
        
        current_time_utc = datetime.now(timezone.utc)
        
        # Query for potentially expired items (those with an 'expiry' field less than now)
        # This query requires a single-field index on `expiry` in Firestore for optimal performance.
        query: AsyncBaseQuery = self._collection_ref.where(filter=FieldFilter("expiry", "<", current_time_utc))
        
        doc_stream = query.stream() # This streams all documents matching the query
        
        batch = self.client.batch()
        current_batch_operation_count = 0
        
        async for doc_snapshot in doc_stream:
            total_queried_for_expiry += 1
            # The query already ensures these items are expired based on Firestore's server time understanding of `current_time_utc`.
            # No need for an additional `is_item_expired` check on each `doc_snapshot` here.
            
            batch.delete(doc_snapshot.reference)
            current_batch_operation_count += 1
            deleted_count += 1 # Increment deleted_count as we add to batch
            
            if current_batch_operation_count >= delete_batch_size:
                try:
                    await batch.commit()
                    logger.info(f"Committed batch of {current_batch_operation_count} deletions. Total deleted so far: {deleted_count}")
                    await self.event_bus.publish(
                        PlaceholderMemoryEvent(PlaceholderEventType.MEMORY_ITEM_EXPIRED, key="batch_prune", count=current_batch_operation_count)
                    )
                except (DeadlineExceeded, ServiceUnavailable, ResourceExhausted) as e:
                    logger.warning(f"Transient error during batch commit, review failed operations: {e}")
                    # For simplicity, we don't retry the failed batch here. Production code might need retry for batch commit.
                except Exception as e:
                    logger.error(f"Error committing batch delete: {e}", exc_info=True)
                finally:
                    batch = self.client.batch() # Start a new batch regardless of previous commit success/failure
                    current_batch_operation_count = 0

        # Commit any remaining items in the last batch
        if current_batch_operation_count > 0:
            try:
                await batch.commit()
                logger.info(f"Committed final batch of {current_batch_operation_count} deletions. Total deleted: {deleted_count}")
                await self.event_bus.publish(
                    PlaceholderMemoryEvent(PlaceholderEventType.MEMORY_ITEM_EXPIRED, key="final_batch_prune", count=current_batch_operation_count)
                )
            except Exception as e:
                logger.error(f"Error committing final batch delete: {e}", exc_info=True)

        end_time = time.monotonic()
        duration_seconds = round(end_time - start_time, 2)
        
        stats = {
            "total_queried_with_expiry_clause": total_queried_for_expiry,
            "total_deleted": deleted_count,
            "duration_seconds": duration_seconds,
            "collection_name": self.collection_name
        }
        logger.info(f"Expired item pruning finished. Stats: {stats}")
        return stats 