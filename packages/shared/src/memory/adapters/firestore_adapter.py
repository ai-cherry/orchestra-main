"""
Firestore adapter for the Memory Storage Port.

This module implements the MemoryStoragePort interface using Google Cloud Firestore,
following the hexagonal architecture pattern to isolate infrastructure concerns.
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from google.cloud import firestore
from google.cloud.firestore import AsyncClient
from google.api_core.exceptions import GoogleAPIError
from google.oauth2 import service_account

from packages.shared.src.models.base_models import MemoryItem, AgentData
from packages.shared.src.memory.ports import MemoryStoragePort
from packages.shared.src.memory.exceptions import (
    MemoryConnectionError,
    MemoryItemNotFound,
    MemoryQueryError,
    MemoryWriteError,
    MemoryValidationError,
)
from packages.shared.src.memory.memory_types import MemoryHealth
from packages.shared.src.storage.config import StorageConfig

# Configure logging
logger = logging.getLogger(__name__)

# Collection names
MEMORY_ITEMS_COLLECTION = "memory_items"
AGENT_DATA_COLLECTION = "agent_data"


class FirestoreStorageAdapter(MemoryStoragePort):
    """
    Firestore implementation of the MemoryStoragePort.

    This adapter handles all Firestore-specific details while conforming
    to the port interface, providing a clean separation between domain logic
    and infrastructure concerns.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        credentials_json: Optional[str] = None,
        credentials_path: Optional[str] = None,
        namespace: str = "default",
        config: Optional[StorageConfig] = None,
    ):
        """
        Initialize the Firestore adapter.

        Args:
            project_id: Google Cloud project ID
            credentials_json: Service account credentials as JSON string
            credentials_path: Path to service account credentials file
            namespace: Namespace for collection names
            config: Storage configuration
        """
        self._project_id = project_id
        self._credentials_json = credentials_json
        self._credentials_path = credentials_path
        self._namespace = namespace
        self._config = config or StorageConfig(
            namespace=namespace,
            environment="development",
        )

        # Will be initialized in initialize()
        self._credentials = None
        self._client = None
        self._async_client = None
        self._initialized = False
        self._error_count = 0
        self._last_error = None

        logger.debug(
            f"FirestoreStorageAdapter initialized with project ID: {project_id}")

    async def initialize(self) -> None:
        """
        Initialize the Firestore connection.

        Raises:
            MemoryConnectionError: If connection to Firestore fails
        """
        if self._initialized:
            return

        try:
            # Set up credentials
            if self._credentials_json:
                # Parse the JSON string and create credentials
                service_account_info = json.loads(self._credentials_json)
                self._credentials = service_account.Credentials.from_service_account_info(
                    service_account_info
                )
            elif self._credentials_path:
                # Load credentials from file
                self._credentials = service_account.Credentials.from_service_account_file(
                    self._credentials_path
                )

            # Initialize Firestore clients
            if self._credentials:
                self._client = firestore.Client(
                    project=self._project_id, credentials=self._credentials
                )
                self._async_client = firestore.AsyncClient(
                    project=self._project_id, credentials=self._credentials
                )
            else:
                # Use Application Default Credentials
                self._client = firestore.Client(project=self._project_id)
                self._async_client = firestore.AsyncClient(
                    project=self._project_id)

            self._initialized = True
            logger.info(
                f"FirestoreStorageAdapter successfully connected to project {self._project_id}")

        except GoogleAPIError as e:
            error_msg = f"Failed to connect to Firestore: {e}"
            logger.error(error_msg)
            raise MemoryConnectionError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error initializing Firestore: {e}"
            logger.error(error_msg)
            raise MemoryConnectionError(error_msg)

    async def close(self) -> None:
        """Close the Firestore connection."""
        # Firestore client does not require explicit closing
        self._initialized = False
        logger.info("FirestoreStorageAdapter connection closed")

    def _check_initialized(self) -> None:
        """
        Check if the adapter is initialized.

        Raises:
            MemoryConnectionError: If the adapter is not initialized
        """
        if not self._initialized:
            raise MemoryConnectionError(
                "FirestoreStorageAdapter is not initialized")

    def _get_collection_name(self, base_name: str) -> str:
        """
        Get the full collection name with namespace.

        Args:
            base_name: Base collection name

        Returns:
            Full collection name with namespace
        """
        return f"{base_name}_{self._namespace}"

    async def save_item(self, item: MemoryItem) -> str:
        """
        Save a memory item to Firestore.

        Args:
            item: Memory item to save

        Returns:
            ID of the saved item

        Raises:
            MemoryWriteError: If the save operation fails
            MemoryValidationError: If the item validation fails
        """
        self._check_initialized()

        # Validate item
        if not item.id:
            raise MemoryValidationError("Memory item must have an ID")

        if not item.user_id:
            raise MemoryValidationError("Memory item must have a user ID")

        try:
            # Convert MemoryItem to dict for Firestore
            # Note: This keeps infrastructure concerns in the adapter
            item_data = item.model_dump()

            # Add TTL field for automatic expiration if configured
            if hasattr(self._config, "item_ttl_days") and self._config.item_ttl_days > 0:
                expiry_date = datetime.now() + timedelta(days=self._config.item_ttl_days)
                item_data["ttl"] = expiry_date

            # Convert datetime to Firestore timestamp
            if "timestamp" in item_data:
                item_data["timestamp"] = firestore.SERVER_TIMESTAMP

            # Save to Firestore
            collection_name = self._get_collection_name(
                MEMORY_ITEMS_COLLECTION)
            doc_ref = self._async_client.collection(
                collection_name).document(item.id)
            await doc_ref.set(item_data)

            logger.debug(f"Saved memory item {item.id} to Firestore")
            return item.id

        except GoogleAPIError as e:
            error_msg = f"Failed to save memory item to Firestore: {e}"
            logger.error(error_msg)
            self._track_error(e)
            raise MemoryWriteError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error saving memory item: {e}"
            logger.error(error_msg)
            self._track_error(e)
            raise MemoryWriteError(error_msg)

    async def retrieve_item(self, item_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory item from Firestore.

        Args:
            item_id: ID of the item to retrieve

        Returns:
            The memory item, or None if not found

        Raises:
            MemoryQueryError: If the retrieval operation fails
        """
        self._check_initialized()

        try:
            # Get document from Firestore
            collection_name = self._get_collection_name(
                MEMORY_ITEMS_COLLECTION)
            doc_ref = self._async_client.collection(
                collection_name).document(item_id)
            doc = await doc_ref.get()

            if not doc.exists:
                return None

            # Convert Firestore document to MemoryItem
            # Note: This keeps infrastructure concerns in the adapter
            doc_data = doc.to_dict()
            return MemoryItem.model_validate(doc_data)

        except GoogleAPIError as e:
            error_msg = f"Failed to retrieve memory item from Firestore: {e}"
            logger.error(error_msg)
            self._track_error(e)
            raise MemoryQueryError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error retrieving memory item: {e}"
            logger.error(error_msg)
            self._track_error(e)
            raise MemoryQueryError(error_msg)

    async def query_items(
        self,
        user_id: str,
        filters: Dict[str, Any],
        limit: int,
    ) -> List[MemoryItem]:
        """
        Query memory items from Firestore.

        Args:
            user_id: User ID to filter by
            filters: Additional filters to apply
            limit: Maximum number of items to return

        Returns:
            List of memory items matching the query

        Raises:
            MemoryQueryError: If the query operation fails
        """
        self._check_initialized()

        try:
            # Construct base query
            collection_name = self._get_collection_name(
                MEMORY_ITEMS_COLLECTION)
            query = self._async_client.collection(
                collection_name).where("user_id", "==", user_id)

            # Apply additional filters
            for key, value in filters.items():
                if isinstance(value, dict) and ("start" in value or "end" in value):
                    if "start" in value:
                        query = query.where(key, ">=", value["start"])
                    if "end" in value:
                        query = query.where(key, "<=", value["end"])
                else:
                    query = query.where(key, "==", value)

            # Apply limit and order
            query = query.order_by(
                "timestamp", direction=firestore.Query.DESCENDING).limit(limit)

            # Execute query
            docs = await query.get()

            # Convert to MemoryItems
            result = []
            for doc in docs:
                try:
                    doc_data = doc.to_dict()
                    if doc_data:
                        memory_item = MemoryItem.model_validate(doc_data)
                        result.append(memory_item)
                except Exception as e:
                    logger.warning(f"Error parsing document {doc.id}: {e}")
                    continue

            logger.debug(
                f"Retrieved {len(result)} memory items for user {user_id}")
            return result

        except GoogleAPIError as e:
            error_msg = f"Failed to query memory items from Firestore: {e}"
            logger.error(error_msg)
            self._track_error(e)
            raise MemoryQueryError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error querying memory items: {e}"
            logger.error(error_msg)
            self._track_error(e)
            raise MemoryQueryError(error_msg)

    async def save_agent_data(self, data: AgentData) -> str:
        """
        Save agent data to Firestore.

        Args:
            data: Agent data to save

        Returns:
            ID of the saved data

        Raises:
            MemoryWriteError: If the save operation fails
            MemoryValidationError: If the data validation fails
        """
        self._check_initialized()

        # Validate data
        if not data.id:
            raise MemoryValidationError("Agent data must have an ID")

        if not data.agent_id:
            raise MemoryValidationError("Agent data must have an agent ID")

        try:
            # Convert AgentData to dict for Firestore
            data_dict = data.model_dump()

            # Save to Firestore
            collection_name = self._get_collection_name(AGENT_DATA_COLLECTION)
            doc_ref = self._async_client.collection(
                collection_name).document(data.id)
            await doc_ref.set(data_dict)

            logger.debug(
                f"Saved agent data {data.id} for agent {data.agent_id} to Firestore")
            return data.id

        except GoogleAPIError as e:
            error_msg = f"Failed to save agent data to Firestore: {e}"
            logger.error(error_msg)
            self._track_error(e)
            raise MemoryWriteError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error saving agent data: {e}"
            logger.error(error_msg)
            self._track_error(e)
            raise MemoryWriteError(error_msg)

    async def delete_items(self, filter_criteria: Dict[str, Any]) -> int:
        """
        Delete items matching the given criteria.

        Args:
            filter_criteria: Criteria for items to delete

        Returns:
            Number of items deleted

        Raises:
            MemoryWriteError: If the delete operation fails
        """
        self._check_initialized()

        try:
            # Construct query to find documents to delete
            collection_name = self._get_collection_name(
                MEMORY_ITEMS_COLLECTION)
            query = self._async_client.collection(collection_name)

            for key, value in filter_criteria.items():
                query = query.where(key, "==", value)

            # Execute query
            docs = await query.get()

            # Delete documents in batch
            batch = self._async_client.batch()
            count = 0

            for doc in docs:
                batch.delete(doc.reference)
                count += 1

                # Commit batch in chunks to avoid hitting Firestore limits
                if count % 400 == 0:  # Firestore limit is 500, using 400 as safety margin
                    await batch.commit()
                    batch = self._async_client.batch()

            # Commit any remaining operations
            if count % 400 != 0:
                await batch.commit()

            logger.debug(f"Deleted {count} memory items from Firestore")
            return count

        except GoogleAPIError as e:
            error_msg = f"Failed to delete memory items from Firestore: {e}"
            logger.error(error_msg)
            self._track_error(e)
            raise MemoryWriteError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error deleting memory items: {e}"
            logger.error(error_msg)
            self._track_error(e)
            raise MemoryWriteError(error_msg)

    async def check_health(self) -> MemoryHealth:
        """
        Check the health of the Firestore connection.

        Returns:
            Health status information
        """
        health = {
            "status": "healthy" if self._initialized else "not_initialized",
            "firestore": self._initialized,
            "error_count": self._error_count,
            "details": {
                "adapter": "FirestoreStorageAdapter",
                "namespace": self._namespace,
                "project_id": self._project_id,
            }
        }

        if self._last_error:
            health["last_error"] = str(self._last_error)

        # Try a simple read operation to verify connection
        if self._initialized:
            try:
                collection_name = self._get_collection_name(
                    MEMORY_ITEMS_COLLECTION)
                await self._async_client.collection(collection_name).limit(1).get()
                health["details"]["connection_verified"] = True
            except Exception as e:
                health["status"] = "error"
                health["details"]["connection_error"] = str(e)
                health["details"]["connection_verified"] = False

        return health

    def _track_error(self, error: Exception) -> None:
        """
        Track an error for health monitoring.

        Args:
            error: The error to track
        """
        self._error_count += 1
        self._last_error = error
