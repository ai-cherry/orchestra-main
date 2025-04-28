"""
DEPRECATED: This implementation is deprecated and will be removed in a future release.

Please use the FirestoreMemoryManagerV2 implementation at v2/adapter.py instead, which provides:
- Improved error handling and recovery
- Better type safety and validation
- Enhanced performance with optimized queries
- More robust health checks
- Better integration with monitoring systems

Example migration:
from packages.shared.src.storage.firestore.firestore_memory import FirestoreMemoryManager
# Change to:
from packages.shared.src.storage.firestore.v2.adapter import FirestoreMemoryManagerV2

Firestore Memory Manager Implementation for AI Orchestration System.

This module provides a Firestore-backed implementation of the MemoryManager
interface for persistent storage of memory items and agent data.
"""

import os
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, cast
import asyncio
from functools import wraps

# Import Firestore
try:
    from google.cloud import firestore
    from google.cloud.firestore import Client as FirestoreClient
    from google.cloud.firestore import AsyncClient as AsyncFirestoreClient
    from google.api_core.exceptions import GoogleAPIError
    from google.oauth2 import service_account
except ImportError:
    raise ImportError(
        "Firestore library not available. Install with: pip install google-cloud-firestore"
    )

from packages.shared.src.memory.memory_manager import MemoryManager, MemoryHealth
from packages.shared.src.models.base_models import MemoryItem, AgentData, PersonaConfig

# Set up logger
logger = logging.getLogger(__name__)

# Define collection names
MEMORY_ITEMS_COLLECTION = "memory_items"
AGENT_DATA_COLLECTION = "agent_data"
USER_SESSIONS_COLLECTION = "user_sessions"


class StorageError(Exception):
    """Base exception for storage-related errors."""

    pass


class ValidationError(Exception):
    """Exception for validation errors in storage operations."""

    pass


class FirestoreMemoryManager(MemoryManager):
    """
    Firestore implementation of memory management for storing and retrieving memory items.

    This class provides a Firestore-backed implementation of the MemoryManager
    interface, enabling persistent storage of memory items and agent data.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        credentials_json: Optional[str] = None,
        credentials_path: Optional[str] = None,
    ):
        """
        Initialize the Firestore memory manager.

        Args:
            project_id: Optional Google Cloud project ID. If not provided, will be read from
                      environment variable GOOGLE_CLOUD_PROJECT.
            credentials_json: Optional JSON string containing service account credentials.
            credentials_path: Optional path to service account credentials file.

        Note:
            Authentication priority:
            1. credentials_json if provided
            2. credentials_path if provided
            3. GOOGLE_APPLICATION_CREDENTIALS environment variable
            4. Application Default Credentials
        """
        self._client = None
        self._async_client = None
        self._project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self._credentials_json = credentials_json
        self._credentials_path = credentials_path or os.environ.get(
            "GOOGLE_APPLICATION_CREDENTIALS"
        )
        self._credentials = None
        self._initialized = False

    def initialize(self) -> None:
        """
        Initialize the connection to Firestore.

        This method establishes a connection to the Firestore database using the
        provided credentials or application default credentials.

        Raises:
            ConnectionError: If connection to Firestore fails
            PermissionError: If the required permissions are not available
        """
        if self._initialized:
            return

        try:
            # Set up credentials
            if self._credentials_json:
                # Parse the JSON string and create credentials
                service_account_info = json.loads(self._credentials_json)
                self._credentials = (
                    service_account.Credentials.from_service_account_info(
                        service_account_info
                    )
                )
            elif self._credentials_path:
                # Load credentials from file
                self._credentials = (
                    service_account.Credentials.from_service_account_file(
                        self._credentials_path
                    )
                )

            # Initialize Firestore client
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
                self._async_client = firestore.AsyncClient(project=self._project_id)

            self._initialized = True
            logger.info("Successfully initialized Firestore memory manager")
        except GoogleAPIError as e:
            logger.error(f"Failed to initialize Firestore client: {e}")
            raise ConnectionError(f"Failed to initialize Firestore connection: {e}")
        except PermissionError as e:
            logger.error(f"Insufficient permissions to access Firestore: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing Firestore: {e}")
            raise ConnectionError(f"Failed to initialize Firestore: {e}")

    def close(self) -> None:
        """
        Close the memory manager and release resources.

        This method cleans up resources used by the Firestore client.
        """
        if hasattr(self._client, "close") and callable(self._client.close):
            try:
                self._client.close()
                logger.debug("Closed Firestore client")
            except Exception as e:
                logger.warning(f"Error closing Firestore client: {e}")

        if hasattr(self._async_client, "close") and callable(self._async_client.close):
            try:
                asyncio.get_event_loop().run_until_complete(self._async_client.close())
                logger.debug("Closed async Firestore client")
            except Exception as e:
                logger.warning(f"Error closing async Firestore client: {e}")

        self._client = None
        self._async_client = None
        self._initialized = False

    def _check_initialized(self) -> None:
        """
        Check if the client is initialized and raise error if not.

        Raises:
            RuntimeError: If the client is not initialized
        """
        if not self._initialized or not self._client or not self._async_client:
            raise RuntimeError(
                "Firestore client not initialized. Call initialize() first."
            )

    async def add_memory_item(self, item: MemoryItem) -> str:
        """
        Add a memory item to Firestore storage.

        Args:
            item: The memory item to store

        Returns:
            The ID of the created memory item

        Raises:
            ValidationError: If the item fails validation
            StorageError: If the storage operation fails
        """
        self._check_initialized()

        # Generate an ID if not provided
        if not item.id:
            item.id = str(uuid.uuid4())

        # Validate required fields
        if not item.user_id:
            raise ValidationError("user_id is required for memory items")

        try:
            # Convert to dict for Firestore
            item_data = item.dict()

            # Store in Firestore
            await self._async_client.collection(MEMORY_ITEMS_COLLECTION).document(
                item.id
            ).set(item_data)

            logger.debug(f"Saved memory item {item.id} for user {item.user_id}")
            return item.id
        except GoogleAPIError as e:
            error_msg = f"Failed to save memory item to Firestore: {e}"
            logger.error(error_msg)
            raise StorageError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error saving memory item: {e}"
            logger.error(error_msg)
            raise StorageError(error_msg)

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

        try:
            # Get document from Firestore
            doc_ref = self._async_client.collection(MEMORY_ITEMS_COLLECTION).document(
                item_id
            )
            doc = await doc_ref.get()

            if not doc.exists:
                logger.debug(f"Memory item {item_id} not found")
                return None

            # Convert to MemoryItem
            item_data = doc.to_dict()
            return MemoryItem(**item_data)
        except GoogleAPIError as e:
            error_msg = f"Failed to retrieve memory item {item_id} from Firestore: {e}"
            logger.error(error_msg)
            raise StorageError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error retrieving memory item: {e}"
            logger.error(error_msg)
            raise StorageError(error_msg)

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

        try:
            # Start with base query
            query = (
                self._async_client.collection(MEMORY_ITEMS_COLLECTION)
                .where("user_id", "==", user_id)
                .where("item_type", "==", "conversation")
            )

            # Add session filter if provided
            if session_id:
                query = query.where("session_id", "==", session_id)

            # Add additional filters if provided
            if filters:
                for key, value in filters.items():
                    # Skip user_id and item_type as they're already included
                    if key not in ["user_id", "item_type"]:
                        query = query.where(key, "==", value)

            # Order by timestamp (descending) and limit results
            query = query.order_by(
                "timestamp", direction=firestore.Query.DESCENDING
            ).limit(limit)

            # Execute query
            docs = await query.get()

            # Convert to MemoryItem objects
            items = []
            for doc in docs:
                try:
                    item_data = doc.to_dict()
                    items.append(MemoryItem(**item_data))
                except Exception as e:
                    logger.warning(f"Error parsing memory item: {e}")
                    continue

            logger.debug(
                f"Retrieved {len(items)} conversation history items for user {user_id}"
            )
            return items
        except GoogleAPIError as e:
            error_msg = f"Failed to retrieve conversation history from Firestore: {e}"
            logger.error(error_msg)
            raise StorageError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error retrieving conversation history: {e}"
            logger.error(error_msg)
            raise StorageError(error_msg)

    async def semantic_search(
        self,
        user_id: str,
        query_embedding: List[float],
        persona_context: Optional[PersonaConfig] = None,
        top_k: int = 5,
    ) -> List[MemoryItem]:
        """
        Perform semantic search using vector embeddings.

        Note: This is a basic implementation. For production, consider using
        a vector database or Firestore's native vector search capabilities when available.

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

        if not query_embedding:
            raise ValidationError("Query embedding cannot be empty")

        try:
            # Get memory items for the user
            query = self._async_client.collection(MEMORY_ITEMS_COLLECTION).where(
                "user_id", "==", user_id
            )

            # Add persona filter if provided
            if persona_context and persona_context.name:
                query = query.where("persona_active", "==", persona_context.name)

            # Execute query
            docs = await query.get()

            # Filter items with embeddings
            items_with_embedding = []
            for doc in docs:
                try:
                    item_data = doc.to_dict()
                    if item_data.get("embedding"):
                        items_with_embedding.append(MemoryItem(**item_data))
                except Exception as e:
                    logger.warning(f"Error parsing memory item: {e}")
                    continue

            # Compute similarities (cosine similarity)
            # Note: In a production system, use a proper vector database for this
            items_with_scores = []
            for item in items_with_embedding:
                if not item.embedding:
                    continue

                # Ensure embeddings are same length
                if len(item.embedding) != len(query_embedding):
                    logger.warning(
                        f"Embedding dimension mismatch: {len(item.embedding)} vs {len(query_embedding)}"
                    )
                    continue

                # Calculate dot product
                dot_product = sum(
                    a * b for a, b in zip(query_embedding, item.embedding)
                )

                # Calculate magnitudes
                mag_item = sum(a * a for a in item.embedding) ** 0.5
                mag_query = sum(a * a for a in query_embedding) ** 0.5

                # Cosine similarity
                similarity = (
                    dot_product / (mag_item * mag_query)
                    if mag_item > 0 and mag_query > 0
                    else 0
                )

                items_with_scores.append((item, similarity))

            # Sort by similarity (descending) and take top_k
            items_with_scores.sort(key=lambda x: x[1], reverse=True)
            top_items = [item for item, _ in items_with_scores[:top_k]]

            logger.debug(
                f"Performed semantic search for user {user_id}, found {len(top_items)} results"
            )
            return top_items
        except GoogleAPIError as e:
            error_msg = f"Failed to perform semantic search in Firestore: {e}"
            logger.error(error_msg)
            raise StorageError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during semantic search: {e}"
            logger.error(error_msg)
            raise StorageError(error_msg)

    async def add_raw_agent_data(self, data: AgentData) -> str:
        """
        Store raw agent data in Firestore.

        Args:
            data: The agent data to store

        Returns:
            The ID of the stored data

        Raises:
            ValidationError: If the data fails validation
            StorageError: If the storage operation fails
        """
        self._check_initialized()

        # Generate an ID if not provided
        if not data.id:
            data.id = str(uuid.uuid4())

        # Validate required fields
        if not data.agent_id:
            raise ValidationError("agent_id is required for agent data")

        try:
            # Convert to dict for Firestore
            data_dict = data.dict()

            # Store in Firestore
            await self._async_client.collection(AGENT_DATA_COLLECTION).document(
                data.id
            ).set(data_dict)

            logger.debug(f"Saved agent data {data.id} for agent {data.agent_id}")
            return data.id
        except GoogleAPIError as e:
            error_msg = f"Failed to save agent data to Firestore: {e}"
            logger.error(error_msg)
            raise StorageError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error saving agent data: {e}"
            logger.error(error_msg)
            raise StorageError(error_msg)

    async def check_duplicate(self, item: MemoryItem) -> bool:
        """
        Check if a memory item already exists in Firestore.

        Args:
            item: The memory item to check for duplicates

        Returns:
            True if a duplicate exists, False otherwise

        Raises:
            StorageError: If the check operation fails
        """
        self._check_initialized()

        if not item.text_content:
            return False  # Cannot check for duplicates without content

        try:
            # Query for items with same user_id and text_content
            query = (
                self._async_client.collection(MEMORY_ITEMS_COLLECTION)
                .where("user_id", "==", item.user_id)
                .where("text_content", "==", item.text_content)
            )

            # Execute query
            docs = await query.get()

            # Check if any documents exist
            has_duplicates = len(list(docs)) > 0

            if has_duplicates:
                logger.debug(f"Found duplicate memory item for user {item.user_id}")

            return has_duplicates
        except GoogleAPIError as e:
            error_msg = f"Failed to check for duplicates in Firestore: {e}"
            logger.error(error_msg)
            raise StorageError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error checking for duplicates: {e}"
            logger.error(error_msg)
            raise StorageError(error_msg)

    async def cleanup_expired_items(self) -> int:
        """
        Remove expired items from storage.

        Returns:
            Number of items removed

        Raises:
            StorageError: If the cleanup operation fails
        """
        self._check_initialized()

        try:
            # Get current time
            now = datetime.utcnow()

            # Query for expired items
            query = self._async_client.collection(MEMORY_ITEMS_COLLECTION).where(
                "expiration", "<", now
            )

            # Execute query
            docs = await query.get()

            # Delete expired items
            batch = self._async_client.batch()
            count = 0

            for doc in docs:
                batch.delete(doc.reference)
                count += 1

                # Firestore has a limit of 500 operations per batch
                if count % 400 == 0:
                    await batch.commit()
                    batch = self._async_client.batch()

            # Commit any remaining deletes
            if count % 400 != 0:
                await batch.commit()

            logger.info(f"Cleaned up {count} expired memory items")
            return count
        except GoogleAPIError as e:
            error_msg = f"Failed to cleanup expired items in Firestore: {e}"
            logger.error(error_msg)
            raise StorageError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during cleanup: {e}"
            logger.error(error_msg)
            raise StorageError(error_msg)
            
    async def health_check(self) -> MemoryHealth:
        """
        Perform a health check on the Firestore connection.
        
        Returns:
            Dictionary with health status information
        """
        health: MemoryHealth = {
            "status": "healthy",
            "firestore": False,
            "error_count": 0,
            "details": {}
        }
        
        if not self._initialized:
            try:
                self.initialize()
                health["details"]["initialization"] = "Initialized during health check"
            except Exception as e:
                health["status"] = "error"
                health["details"]["initialization_error"] = str(e)
                return health
                
        try:
            # Try to read a test document to verify connection
            test_id = "health-check-non-existent"
            try:
                # Should return None or raise "not found" which is fine
                await self.get_memory_item(test_id)
                health["firestore"] = True
            except Exception as e:
                # If it's just a "not found" error, that's actually good
                if "not found" in str(e).lower():
                    health["firestore"] = True
                    health["details"]["firestore_check"] = "Successfully verified item not found"
                else:
                    health["details"]["firestore_error"] = str(e)
                    health["status"] = "error"
            
            return health
        except Exception as e:
            return {
                "status": "error",
                "firestore": False,
                "error_count": 1,
                "last_error": str(e),
                "details": {
                    "message": f"Firestore health check failed: {e}"
                }
            }
