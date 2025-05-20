"""
Firestore Memory Manager Implementation for AI Orchestration System.

This module implements the Firestore-backed memory management system
for storing and retrieving memory records in Google Cloud Firestore.
It provides the cloud-native implementation for production environments.
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from fastapi import Depends

# Import Firestore
try:
    from google.cloud import firestore
    from google.cloud.firestore import Client as FirestoreClient
    from google.api_core.exceptions import GoogleAPIError

    FIRESTORE_AVAILABLE = True
except ImportError:
    firestore = None
    FirestoreClient = object
    GoogleAPIError = Exception
    FIRESTORE_AVAILABLE = False

from packages.shared.src.models.domain_models import MemoryRecord
from packages.shared.src.memory.memory_manager import MemoryManager
from core.orchestrator.src.config.settings import Settings, get_settings

# Set up logger
logger = logging.getLogger(__name__)


class FirestoreMemoryManager(MemoryManager):
    """
    Firestore implementation of memory management for storing and retrieving MemoryRecord objects.

    This class provides methods to interact with Google Cloud Firestore for storing,
    retrieving, and querying memory records. It handles connection management, error handling,
    and provides a high-level API for working with the memory system.
    """

    def __init__(
        self,
        settings: Settings = Depends(get_settings),
        namespace: Optional[str] = None,
    ):
        """
        Initialize the Firestore memory manager.

        Args:
            settings: Application settings
            namespace: Namespace for Firestore collections (defaults to FIRESTORE_NAMESPACE from settings)
        """
        self._client = None
        self._initialized = False
        self.settings = settings

        # Get configuration from settings
        gcp_info = settings.get_gcp_credentials_info()
        self._project_id = gcp_info["project_id"]
        self._credentials_path = gcp_info["credentials_path"]
        self._service_account_json = gcp_info["service_account_json"]

        # Set namespace for collection prefixes
        self._namespace = namespace or settings.FIRESTORE_NAMESPACE

        # Check if Firestore is available
        if not FIRESTORE_AVAILABLE:
            logger.error(
                "Firestore library not available. Install with: pip install google-cloud-firestore"
            )
            raise ImportError(
                "Firestore library not available. Install with: pip install google-cloud-firestore"
            )

    async def initialize(self) -> None:
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
            # Run the synchronous Firestore initialization in a thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._initialize_sync)

            self._initialized = True
            logger.info("Successfully initialized Firestore memory manager")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore client: {e}")
            raise ConnectionError(f"Failed to initialize Firestore connection: {e}")

    def _initialize_sync(self) -> None:
        """Synchronous initialization for Firestore client"""
        # Initialize Firestore client
        if self._service_account_json:
            # Create client from service account JSON string
            import json
            import tempfile

            # Create temporary file for service account JSON
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
                tmp.write(self._service_account_json)
                tmp_path = tmp.name

            try:
                self._client = firestore.Client.from_service_account_json(tmp_path)
            finally:
                # Clean up temporary file
                os.unlink(tmp_path)

        elif self._credentials_path:
            # Create client from service account file
            self._client = firestore.Client.from_service_account_json(
                self._credentials_path
            )
        else:
            # Use Application Default Credentials
            self._client = firestore.Client(project=self._project_id)

    async def close(self) -> None:
        """
        Close the Firestore client connection.

        Release resources and perform cleanup.
        """
        if self._client:
            # Firestore client doesn't have an explicit close method,
            # but we can set it to None to help with garbage collection
            self._client = None
            self._initialized = False
            logger.info("Closed Firestore memory manager connection")

    def _get_collection_name(self, collection_type: str) -> str:
        """Get formatted collection name with namespace"""
        return f"{self._namespace}-{collection_type}"

    async def add_memory(self, memory: MemoryRecord) -> str:
        """
        Add a memory record to Firestore.

        Args:
            memory: MemoryRecord to store

        Returns:
            The record_id of the stored memory

        Raises:
            ValueError: If record_id is not provided
            ConnectionError: If Firestore connection fails
        """
        if not self._initialized:
            await self.initialize()

        if not memory.record_id:
            raise ValueError("record_id must be provided for saving to Firestore")

        collection_name = self._get_collection_name("memory")

        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, lambda: self._save_record_sync(memory, collection_name)
            )

            return memory.record_id
        except Exception as e:
            error_msg = f"Failed to save memory {memory.record_id} to Firestore: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def _save_record_sync(self, record: MemoryRecord, collection: str) -> None:
        """Synchronous implementation of record saving"""
        # Convert MemoryRecord to dict for Firestore
        record_data = record.dict()

        # Add TTL field for automatic expiration if configured
        if (
            hasattr(self.settings, "FIRESTORE_TTL_DAYS")
            and self.settings.FIRESTORE_TTL_DAYS > 0
        ):
            expiry_date = datetime.now() + timedelta(
                days=self.settings.FIRESTORE_TTL_DAYS
            )
            record_data["ttl"] = expiry_date

        # Convert datetime to Firestore timestamp
        if record_data.get("timestamp"):
            record_data["timestamp"] = firestore.SERVER_TIMESTAMP

        # Save to Firestore using record_id as document ID
        self._client.collection(collection).document(record.record_id).set(record_data)
        logger.debug(f"Saved record {record.record_id} to {collection}")

    async def get_memory(self, id: str) -> Optional[MemoryRecord]:
        """
        Retrieve a memory record by its ID.

        Args:
            id: ID of the memory record to retrieve

        Returns:
            MemoryRecord if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()

        collection_name = self._get_collection_name("memory")

        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            record = await loop.run_in_executor(
                None, lambda: self._get_record_sync(id, collection_name)
            )
            return record
        except ValueError:
            # Record not found
            return None
        except Exception as e:
            logger.error(f"Error retrieving memory {id}: {e}")
            return None

    def _get_record_sync(self, record_id: str, collection: str) -> MemoryRecord:
        """Synchronous implementation of record retrieval"""
        # Retrieve document from Firestore
        doc_ref = self._client.collection(collection).document(record_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise ValueError(f"Record {record_id} not found in collection {collection}")

        # Convert Firestore document to MemoryRecord
        record_data = doc.to_dict()
        return MemoryRecord(**record_data)

    async def search_memories(
        self, query: Dict[str, Any], limit: int = 10
    ) -> List[MemoryRecord]:
        """
        Search for memory records matching the query criteria.

        Args:
            query: Dictionary of field-value pairs to filter by
            limit: Maximum number of records to return (default: 10)

        Returns:
            List of matching MemoryRecord objects
        """
        if not self._initialized:
            await self.initialize()

        collection_name = self._get_collection_name("memory")

        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            records = await loop.run_in_executor(
                None, lambda: self._query_records_sync(query, collection_name, limit)
            )
            return records
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []

    def _query_records_sync(
        self, filters: dict, collection: str, limit: int = 10
    ) -> List[MemoryRecord]:
        """Synchronous implementation of record querying"""
        # Start with base query
        query = self._client.collection(collection)

        # Add filters
        for key, value in filters.items():
            if key == "timestamp" and isinstance(value, dict):
                # Handle timestamp range queries
                if "start" in value:
                    query = query.where(key, ">=", value["start"])
                if "end" in value:
                    query = query.where(key, "<=", value["end"])
            else:
                # Standard equality filter
                query = query.where(key, "==", value)

        # Add limit
        query = query.limit(limit)

        # Execute query
        docs = query.stream()

        # Convert results to MemoryRecord objects
        results = [MemoryRecord(**doc.to_dict()) for doc in docs]
        return results

    async def get_conversation_history(
        self, user_id: str, limit: int = 20
    ) -> List[MemoryRecord]:
        """
        Get conversation history for a specific user.

        Args:
            user_id: ID of the user whose conversation history to retrieve
            limit: Maximum number of records to return (default: 20)

        Returns:
            List of conversation memory records, sorted by timestamp (newest first)
        """
        query = {"user_id": user_id, "item_type": "conversation"}

        memories = await self.search_memories(query, limit)

        # Sort by timestamp, newest first
        return sorted(memories, key=lambda m: m.timestamp or datetime.min, reverse=True)

    async def clear_user_memories(self, user_id: str) -> int:
        """
        Clear all memories associated with a user.

        Args:
            user_id: ID of the user whose memories to clear

        Returns:
            Number of memories cleared
        """
        if not self._initialized:
            await self.initialize()

        collection_name = self._get_collection_name("memory")

        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            count = await loop.run_in_executor(
                None, lambda: self._clear_user_memories_sync(user_id, collection_name)
            )
            return count
        except Exception as e:
            logger.error(f"Error clearing memories for user {user_id}: {e}")
            return 0

    def _clear_user_memories_sync(self, user_id: str, collection: str) -> int:
        """Synchronous implementation of memory clearing"""
        # Query for all documents with matching user_id
        query = self._client.collection(collection).where("user_id", "==", user_id)
        docs = query.stream()

        # Delete each document
        count = 0
        for doc in docs:
            doc.reference.delete()
            count += 1

        return count

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the Firestore connection.

        Returns:
            Dictionary with health status information
        """
        if not self._initialized:
            try:
                await self.initialize()
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Failed to initialize Firestore connection: {e}",
                    "initialized": False,
                }

        try:
            # Try to read a test document to verify connection
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._client.collection("__healthcheck__")
                .document("test")
                .get(),
            )

            return {
                "status": "healthy",
                "message": "Firestore connection is healthy",
                "initialized": self._initialized,
                "namespace": self._namespace,
                "project_id": self._project_id,
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Firestore health check failed: {e}",
                "initialized": self._initialized,
                "namespace": self._namespace,
                "project_id": self._project_id,
            }
