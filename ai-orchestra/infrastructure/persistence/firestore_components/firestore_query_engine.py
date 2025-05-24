"""
Handles the construction and execution of queries against Firestore
for memory items. Supports filtering, tagging, and pagination.
"""

import logging
from datetime import datetime, timezone  # Ensure datetime is imported if used for expiry checks here
from typing import Any, AsyncGenerator, Dict, List, Optional

from google.cloud import firestore
from google.cloud.firestore_v1.async_client import AsyncClient as FirestoreAsyncClient
from google.cloud.firestore_v1.async_document import AsyncDocumentSnapshot
from google.cloud.firestore_v1.base_query import AsyncBaseQuery, FieldFilter

# TODO: Replace these with actual imports from your project
from packages.shared.src.models.base_models import MemoryItem

# from ai_orchestra.core.interfaces.enhanced_memory import QueryResult, QueryFilter
from .memory_item_serializer import MemoryItemSerializer  # Assuming it's in the same directory

# Placeholder for actual models - replace these with your actual imports and definitions
# from pydantic import BaseModel, Field # Assuming Pydantic is used

logger = logging.getLogger(__name__)


class FirestoreQueryEngine:
    """
    Constructs and executes queries against Firestore for memory items.
    """

    def __init__(self, firestore_client: FirestoreAsyncClient, collection_name: str, serializer: MemoryItemSerializer):
        """
        Initializes the FirestoreQueryEngine.

        Args:
            firestore_client: An initialized instance of Firestore AsyncClient.
            collection_name: The name of the Firestore collection to query.
            serializer: An instance of MemoryItemSerializer for converting Firestore data.
        """
        if not isinstance(firestore_client, FirestoreAsyncClient):
            raise TypeError("firestore_client must be an instance of FirestoreAsyncClient.")
        if not collection_name or not isinstance(collection_name, str):
            raise ValueError("collection_name must be a non-empty string.")
        if not isinstance(serializer, MemoryItemSerializer):
            raise TypeError("serializer must be an instance of MemoryItemSerializer.")

        self.client: FirestoreAsyncClient = firestore_client
        self.collection_name: str = collection_name
        self._collection_ref = self.client.collection(self.collection_name)
        self.serializer: MemoryItemSerializer = serializer
        logger.info(f"FirestoreQueryEngine initialized for collection: {self.collection_name}")

    def _apply_filters_and_ordering(
        self,
        base_query: AsyncBaseQuery,
        filters: Optional[List[Dict[str, Any]]] = None,
        tags: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        order_direction: str = "ASCENDING",
    ) -> AsyncBaseQuery:
        """Helper to apply common filtering and ordering to a query."""
        query = base_query
        if filters:
            for f in filters:
                query = query.where(filter=FieldFilter(f["field"], f["operator"], f["value"]))
        if tags:
            for tag in tags:
                query = query.where(filter=FieldFilter("tags", "array_contains", tag))
        if order_by:
            direction = (
                firestore.AsyncQuery.DESCENDING
                if order_direction.upper() == "DESCENDING"
                else firestore.AsyncQuery.ASCENDING
            )
            query = query.order_by(order_by, direction=direction)
        return query

    async def execute_query(
        self,
        filters: Optional[List[Dict[str, Any]]] = None,
        tags: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        order_direction: str = "ASCENDING",
        page: int = 1,
        page_size: int = 100,
    ) -> List[MemoryItem]:
        if page < 1:
            raise ValueError("Page number must be 1 or greater.")
        if page_size < 1 or page_size > 1000:  # Firestore limit for array_contains_any, good general limit
            raise ValueError("Page size must be between 1 and 1000.")

        logger.debug(
            f"Executing query on '{self.collection_name}' with filters: {filters}, "
            f"tags: {tags}, order_by: {order_by} {order_direction}, "
            f"page: {page}, page_size: {page_size}"
        )

        try:
            query = self._apply_filters_and_ordering(self._collection_ref, filters, tags, order_by, order_direction)

            # For total count, it's often more performant to do a separate count query if possible,
            # or accept that total_count might be for the non-paginated set.
            # Firestore's .count() aggregator is generally efficient.
            count_query = query  # The query before pagination is applied
            count_snapshot = await count_query.count().get()
            total_count = count_snapshot[0][0].value if count_snapshot else 0

            # Apply pagination using cursors for better performance than offset
            paginated_query = query
            if page > 1:
                # To get a cursor for start_after, we need to fetch the last doc of the previous page
                # This requires executing a query up to the end of the previous page
                offset_docs_query = query.limit((page - 1) * page_size)
                # We only need the last document of this query to act as a cursor
                last_doc_of_prev_page: Optional[AsyncDocumentSnapshot] = None
                async for doc_snap in offset_docs_query.stream():  # Iterate to get to the last one
                    last_doc_of_prev_page = doc_snap

                if last_doc_of_prev_page:
                    paginated_query = paginated_query.start_after(last_doc_of_prev_page)

            paginated_query = paginated_query.limit(page_size)

            docs_stream = paginated_query.stream()
            items: List[MemoryItem] = []
            current_time_utc = datetime.now(timezone.utc)

            async for doc_snapshot in docs_stream:
                if doc_snapshot.exists:
                    firestore_data = doc_snapshot.to_dict()
                    try:
                        item = self.serializer.to_memory_item(doc_snapshot.id, firestore_data)
                        if getattr(item, "expiry", None) and item.expiry < current_time_utc:
                            logger.debug(f"Item '{item.id}' expired, filtering out from query results.")
                            continue
                        items.append(item)
                    except ValueError as ve:
                        logger.warning(
                            f"Skipping item due to deserialization/validation error: {doc_snapshot.id}, error: {ve}"
                        )
                        continue
            logger.info(f"Query returned {len(items)} items for page {page} (total potential: {total_count}).")
            # Return just the list of items, not a QueryResult
            return items

        except Exception as e:
            logger.error(f"Error executing query on '{self.collection_name}': {e}", exc_info=True)
            raise  # Re-raise the original exception or a custom domain error

    async def stream_query_results(
        self,
        filters: Optional[List[Dict[str, Any]]] = None,
        tags: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        order_direction: str = "ASCENDING",
    ) -> AsyncGenerator[MemoryItem, None]:
        logger.debug(
            f"Streaming query results from '{self.collection_name}' with filters: {filters}, "
            f"tags: {tags}, order_by: {order_by} {order_direction}"
        )
        try:
            query = self._apply_filters_and_ordering(self._collection_ref, filters, tags, order_by, order_direction)
            current_time_utc = datetime.now(timezone.utc)

            async for doc_snapshot in query.stream():
                if doc_snapshot.exists:
                    firestore_data = doc_snapshot.to_dict()
                    try:
                        item = self.serializer.to_memory_item(doc_snapshot.id, firestore_data)
                        if getattr(item, "expiry", None) and item.expiry < current_time_utc:
                            logger.debug(f"Streaming: Item '{item.id}' expired, skipping.")
                            continue
                        yield item
                    except ValueError as ve:
                        logger.warning(
                            f"Streaming: Skipping item due to deserialization error: {doc_snapshot.id}, error: {ve}"
                        )
                        continue
        except Exception as e:
            logger.error(f"Error streaming query results from '{self.collection_name}': {e}", exc_info=True)
            raise
