"""
Memory management system for the orchestration system.
"""

import os
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from google.cloud import firestore
from google.oauth2 import service_account
from loguru import logger

from packages.shared.src.models.base_models import MemoryItem


class MemoryManager(ABC):
    """Abstract base class for memory management."""

    @abstractmethod
    async def store(self, memory_item: MemoryItem) -> str:
        """Store a memory item and return its ID."""

    @abstractmethod
    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve a memory item by ID."""

    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """Search for memory items matching a query."""

    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """Delete a memory item by ID."""


class InMemoryMemoryManager(MemoryManager):
    """Simple in-memory implementation of MemoryManager."""

    def __init__(self):
        self._storage: Dict[str, MemoryItem] = {}

    async def store(self, memory_item: MemoryItem) -> str:
        """Store a memory item in memory."""
        if not memory_item.id:
            memory_item.id = f"mem_{int(time.time() * 1000)}"

        self._storage[memory_item.id] = memory_item
        return memory_item.id

    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve a memory item from storage."""
        return self._storage.get(memory_id)

    async def search(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """Simple search implementation (case-insensitive substring matching)."""
        results = []
        query = query.lower()

        for item in self._storage.values():
            if query in item.content.lower():
                results.append(item)
                if len(results) >= limit:
                    break

        return results

    async def delete(self, memory_id: str) -> bool:
        """Delete a memory item if it exists."""
        if memory_id in self._storage:
            del self._storage[memory_id]
            return True
        return False


class FirestoreMemoryManager(MemoryManager):
    """Firestore implementation of MemoryManager for GCP integration."""

    def __init__(self, collection_name: str = "memories", credentials_path: Optional[str] = None):
        """
        Initialize the FirestoreMemoryManager.

        Args:
            collection_name: The Firestore collection to use
            credentials_path: Path to the GCP service account credentials file.
                              If not provided, will use environment variable GOOGLE_APPLICATION_CREDENTIALS
        """
        try:
            # If credentials path is provided, use it to authenticate
            if credentials_path and os.path.exists(credentials_path):
                credentials = service_account.Credentials.from_service_account_file(credentials_path)
                self.db = firestore.Client(credentials=credentials)
                logger.info(f"Initialized Firestore client with credentials from {credentials_path}")
            else:
                # Otherwise, rely on default authentication (GOOGLE_APPLICATION_CREDENTIALS env var)
                self.db = firestore.Client()
                logger.info("Initialized Firestore client with default credentials")

            self.collection = self.db.collection(collection_name)
            logger.info(f"Using Firestore collection: {collection_name}")
        except Exception as e:
            logger.error(f"Error initializing Firestore client: {str(e)}")
            raise

    async def store(self, memory_item: MemoryItem) -> str:
        """Store a memory item in Firestore."""
        try:
            if not memory_item.id:
                memory_item.id = f"mem_{int(time.time() * 1000)}"

            # Convert the memory item to a dictionary for Firestore
            memory_dict = memory_item.model_dump()

            # Store in Firestore
            doc_ref = self.collection.document(memory_item.id)
            doc_ref.set(memory_dict)

            logger.debug(f"Stored memory item with ID: {memory_item.id}")
            return memory_item.id
        except Exception as e:
            logger.error(f"Error storing memory item in Firestore: {str(e)}")
            raise

    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve a memory item from Firestore by ID."""
        try:
            doc_ref = self.collection.document(memory_id)
            doc = doc_ref.get()

            if doc.exists:
                return MemoryItem(**doc.to_dict())
            else:
                logger.debug(f"Memory item not found with ID: {memory_id}")
                return None
        except Exception as e:
            logger.error(f"Error retrieving memory item from Firestore: {str(e)}")
            raise

    async def search(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """
        Search for memory items in Firestore.
        Note: This is a simple implementation. For more advanced searches,
        consider adding a proper search index or using a specialized service like Algolia.
        """
        try:
            results = []
            # Simple search: get all items and filter (not efficient for large collections)
            query_lower = query.lower()

            # Get all documents from collection
            # Limit to prevent excessive reads
            docs = self.collection.limit(100).stream()

            for doc in docs:
                data = doc.to_dict()
                if query_lower in data.get("content", "").lower():
                    results.append(MemoryItem(**data))
                    if len(results) >= limit:
                        break

            return results
        except Exception as e:
            logger.error(f"Error searching memory items in Firestore: {str(e)}")
            raise

    async def delete(self, memory_id: str) -> bool:
        """Delete a memory item from Firestore by ID."""
        try:
            doc_ref = self.collection.document(memory_id)
            doc = doc_ref.get()

            if doc.exists:
                doc_ref.delete()
                logger.debug(f"Deleted memory item with ID: {memory_id}")
                return True
            else:
                logger.debug(f"Memory item not found with ID: {memory_id}")
                return False
        except Exception as e:
            logger.error(f"Error deleting memory item from Firestore: {str(e)}")
            raise


class MemoryManagerFactory:
    """Factory class to create the appropriate MemoryManager based on configuration."""

    @staticmethod
    def create(memory_type: str = "in-memory", **kwargs) -> MemoryManager:
        """
        Create a memory manager instance based on the specified type.

        Args:
            memory_type: Type of memory manager to create ('in-memory' or 'firestore')
            **kwargs: Additional arguments to pass to the memory manager constructor

        Returns:
            An instance of MemoryManager

        Raises:
            ValueError: If the memory_type is not recognized
        """
        if memory_type.lower() == "in-memory":
            return InMemoryMemoryManager()
        elif memory_type.lower() == "firestore":
            collection = kwargs.get("collection_name", "memories")
            creds_path = kwargs.get("credentials_path", os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
            return FirestoreMemoryManager(collection_name=collection, credentials_path=creds_path)
        else:
            raise ValueError(f"Unknown memory manager type: {memory_type}")
