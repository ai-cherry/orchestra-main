"""
Firestore adapter for the MemoryManager interface in the AI Orchestration System.

This module provides an adapter that implements the MemoryManager interface
using the new AsyncFirestoreStorageManager, bridging between the domain
models and Firestore storage.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, cast

# Import the MemoryManager interface
from packages.shared.src.memory.memory_manager import MemoryManager, MemoryHealth
from packages.shared.src.models.base_models import MemoryItem, AgentData, PersonaConfig

# Import the storage components
from packages.shared.src.storage.config import StorageConfig
from packages.shared.src.storage.exceptions import StorageError, ValidationError
from packages.shared.src.storage.firestore.constants import (
    MEMORY_ITEMS_COLLECTION, AGENT_DATA_COLLECTION, 
    USER_ID_FIELD, SESSION_ID_FIELD, ITEM_TYPE_FIELD, PERSONA_FIELD
)
from packages.shared.src.storage.firestore.v2.async_core import AsyncFirestoreStorageManager
from packages.shared.src.storage.firestore.v2.models import (
    memory_item_to_document, document_to_memory_item,
    agent_data_to_document, document_to_agent_data
)

# Configure logging
logger = logging.getLogger(__name__)


class FirestoreMemoryManagerV2(MemoryManager):
    """
    Implements the MemoryManager interface using the new Firestore implementation.
    
    This adapter connects the domain models to the Firestore storage layer,
    providing persistent storage for memory items and agent data.
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        credentials_json: Optional[str] = None,
        credentials_path: Optional[str] = None,
        namespace: str = "default",
        log_level: int = logging.INFO
    ):
        """
        Initialize the Firestore memory manager.
        
        Args:
            project_id: Optional Google Cloud project ID
            credentials_json: Optional JSON string containing service account credentials
            credentials_path: Optional path to service account credentials file
            namespace: Optional namespace for memory isolation
            log_level: Logging level for this instance
        """
        config = StorageConfig(namespace=namespace)
        
        self.firestore = AsyncFirestoreStorageManager(
            project_id=project_id,
            credentials_json=credentials_json,
            credentials_path=credentials_path,
            config=config,
            log_level=log_level
        )
        
        self._is_initialized = False
        self._error_count = 0
        self._last_error = None
        
    async def initialize(self) -> None:
        """
        Initialize the memory manager.
        
        This method initializes the underlying Firestore connection.
        
        Raises:
            ConnectionError: If connection to Firestore fails
        """
        if self._is_initialized:
            return
            
        await self.firestore.initialize_async()
        self._is_initialized = True
        logger.info("Firestore memory manager initialized")
        
    async def close(self) -> None:
        """
        Close the memory manager and release resources.
        
        This method closes the underlying Firestore connection.
        """
        if self._is_initialized:
            await self.firestore.close_async()
            self._is_initialized = False
            logger.info("Firestore memory manager closed")
            
    def _check_initialized(self) -> None:
        """
        Check if the memory manager is initialized.
        
        Raises:
            RuntimeError: If the memory manager is not initialized
        """
        if not self._is_initialized:
            raise RuntimeError("Memory manager not initialized. Call initialize() first.")
            
    def _track_error(self, error: Exception) -> None:
        """
        Track error occurrences for health monitoring.
        
        Args:
            error: Exception that occurred
        """
        self._error_count += 1
        self._last_error = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": type(error).__name__,
            "message": str(error),
        }
        logger.debug(f"Tracked memory error: {type(error).__name__}: {str(error)}")
            
    async def add_memory_item(self, item: MemoryItem) -> str:
        """
        Add a memory item to storage.
        
        Args:
            item: The memory item to store
            
        Returns:
            The ID of the created memory item
            
        Raises:
            ValidationError: If the item fails validation
            StorageError: If the storage operation fails
        """
        self._check_initialized()
        
        # Validate required fields
        if not item.user_id:
            raise ValidationError("user_id is required for memory items")
            
        try:
            # Convert to document format
            doc = memory_item_to_document(item)
            doc_id = doc.get("id")
            
            # Store in Firestore
            collection = self.firestore.config.get_collection_name(MEMORY_ITEMS_COLLECTION)
            await self.firestore.set_document(collection, doc_id, doc)
            
            logger.debug(f"Saved memory item {doc_id} for user {item.user_id}")
            return doc_id
            
        except Exception as e:
            self._track_error(e)
            if isinstance(e, (ValidationError, StorageError)):
                raise
            else:
                raise StorageError(f"Failed to add memory item: {e}")
                
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
            # Get from Firestore
            collection = self.firestore.config.get_collection_name(MEMORY_ITEMS_COLLECTION)
            doc = await self.firestore.get_document(collection, item_id)
            
            # Return None if not found
            if not doc:
                return None
                
            # Convert to MemoryItem
            return document_to_memory_item(doc)
            
        except Exception as e:
            self._track_error(e)
            if isinstance(e, StorageError):
                raise
            else:
                raise StorageError(f"Failed to get memory item: {e}")
                
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
            # Set up filters
            query_filters = {
                USER_ID_FIELD: user_id,
                ITEM_TYPE_FIELD: "conversation"
            }
            
            # Add session filter if provided
            if session_id:
                query_filters[SESSION_ID_FIELD] = session_id
                
            # Add any additional filters
            if filters:
                for key, value in filters.items():
                    if key not in query_filters:
                        query_filters[key] = value
                        
            # Query from Firestore
            collection = self.firestore.config.get_collection_name(MEMORY_ITEMS_COLLECTION)
            docs = await self.firestore.query_documents(
                collection=collection,
                filters=query_filters,
                order_by=datetime.now().isoformat(),
                direction="DESCENDING",
                limit=limit
            )
            
            # Convert to MemoryItems
            items = [document_to_memory_item(doc) for doc in docs]
            
            logger.debug(f"Retrieved {len(items)} conversation history items for user {user_id}")
            return items
            
        except Exception as e:
            self._track_error(e)
            if isinstance(e, StorageError):
                raise
            else:
                raise StorageError(f"Failed to get conversation history: {e}")
                
    async def semantic_search(
        self,
        user_id: str,
        query_embedding: List[float],
        persona_context: Optional[PersonaConfig] = None,
        top_k: int = 5,
    ) -> List[MemoryItem]:
        """
        Perform semantic search using vector embeddings.
        
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
            # Set up filters
            query_filters = {USER_ID_FIELD: user_id}
            
            # Add persona filter if provided
            if persona_context and persona_context.name:
                query_filters[PERSONA_FIELD] = persona_context.name
                
            # Query from Firestore
            collection = self.firestore.config.get_collection_name(MEMORY_ITEMS_COLLECTION)
            docs = await self.firestore.query_documents(
                collection=collection,
                filters=query_filters
            )
            
            # Filter to documents with embeddings
            docs_with_embeddings = [doc for doc in docs if doc.get("embedding")]
            
            # Compute similarity (cosine similarity)
            items_with_scores = []
            for doc in docs_with_embeddings:
                embedding = doc.get("embedding")
                if not embedding:
                    continue
                    
                # Ensure embeddings are same length
                if len(embedding) != len(query_embedding):
                    logger.warning(
                        f"Embedding dimension mismatch: {len(embedding)} vs {len(query_embedding)}"
                    )
                    continue
                    
                # Calculate dot product
                dot_product = sum(a * b for a, b in zip(query_embedding, embedding))
                
                # Calculate magnitudes
                mag_doc = sum(a * a for a in embedding) ** 0.5
                mag_query = sum(a * a for a in query_embedding) ** 0.5
                
                # Cosine similarity
                similarity = (
                    dot_product / (mag_doc * mag_query)
                    if mag_doc > 0 and mag_query > 0
                    else 0
                )
                
                # Convert to MemoryItem and add to results
                items_with_scores.append((document_to_memory_item(doc), similarity))
                
            # Sort by similarity (descending) and take top_k
            items_with_scores.sort(key=lambda x: x[1], reverse=True)
            results = [item for item, _ in items_with_scores[:top_k]]
            
            logger.debug(f"Performed semantic search for user {user_id}, found {len(results)} results")
            return results
            
        except Exception as e:
            self._track_error(e)
            if isinstance(e, (ValidationError, StorageError)):
                raise
            else:
                raise StorageError(f"Failed to perform semantic search: {e}")
                
    async def add_raw_agent_data(self, data: AgentData) -> str:
        """
        Store raw agent data.
        
        Args:
            data: The agent data to store
            
        Returns:
            The ID of the stored data
            
        Raises:
            ValidationError: If the data fails validation
            StorageError: If the storage operation fails
        """
        self._check_initialized()
        
        # Validate required fields
        if not data.agent_id:
            raise ValidationError("agent_id is required for agent data")
            
        try:
            # Convert to document format
            doc = agent_data_to_document(data)
            doc_id = doc.get("id")
            
            # Store in Firestore
            collection = self.firestore.config.get_collection_name(AGENT_DATA_COLLECTION)
            await self.firestore.set_document(collection, doc_id, doc)
            
            logger.debug(f"Saved agent data {doc_id} for agent {data.agent_id}")
            return doc_id
            
        except Exception as e:
            self._track_error(e)
            if isinstance(e, (ValidationError, StorageError)):
                raise
            else:
                raise StorageError(f"Failed to add agent data: {e}")
                
    async def check_duplicate(self, item: MemoryItem) -> bool:
        """
        Check if a memory item already exists in storage.
        
        Args:
            item: The memory item to check for duplicates
            
        Returns:
            True if a duplicate exists, False otherwise
            
        Raises:
            StorageError: If the check operation fails
        """
        self._check_initialized()
        
        if not item.text_content:
            return False  # Cannot check duplicates without content
            
        try:
            # Compute the content hash
            from packages.shared.src.storage.firestore.v2.models import compute_content_hash
            content_hash = compute_content_hash(item.text_content)
            
            # Check for matching content hash in metadata
            query_filters = {
                USER_ID_FIELD: item.user_id,
                f"metadata.content_hash": content_hash
            }
            
            # Query from Firestore
            collection = self.firestore.config.get_collection_name(MEMORY_ITEMS_COLLECTION)
            docs = await self.firestore.query_documents(
                collection=collection,
                filters=query_filters,
                limit=1
            )
            
            # Return True if any matches were found
            return len(docs) > 0
            
        except Exception as e:
            self._track_error(e)
            if isinstance(e, StorageError):
                raise
            else:
                raise StorageError(f"Failed to check for duplicates: {e}")
                
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
            query_filters = {
                "expiration": {
                    "end": now
                }
            }
            
            # Get expired items
            collection = self.firestore.config.get_collection_name(MEMORY_ITEMS_COLLECTION)
            expired_docs = await self.firestore.query_documents(
                collection=collection,
                filters=query_filters
            )
            
            # Delete expired items
            count = 0
            for doc in expired_docs:
                doc_id = doc.get("id")
                if doc_id:
                    success = await self.firestore.delete_document(collection, doc_id)
                    if success:
                        count += 1
                        
            logger.info(f"Cleaned up {count} expired memory items")
            return count
            
        except Exception as e:
            self._track_error(e)
            if isinstance(e, StorageError):
                raise
            else:
                raise StorageError(f"Failed to cleanup expired items: {e}")
                
    async def health_check(self) -> MemoryHealth:
        """
        Check the health of the memory system.
        
        Returns:
            MemoryHealth: A dictionary with health status information
        """
        health: MemoryHealth = {
            "status": "healthy",
            "firestore": False,
            "redis": False,  # This implementation doesn't use Redis
            "error_count": self._error_count,
            "details": {
                "provider": "firestore_v2",
                "implementation": self.__class__.__name__
            }
        }
        
        if self._last_error:
            health["last_error"] = self._last_error["timestamp"]
            health["details"]["last_error"] = self._last_error
            
        # Check if initialized
        if not self._is_initialized:
            try:
                await self.initialize()
                health["details"]["initialization"] = "Initialized during health check"
            except Exception as e:
                health["status"] = "error"
                health["details"]["initialization_error"] = str(e)
                return health
                
        # Check Firestore connection
        try:
            firestore_health = await self.firestore.check_health()
            health["firestore"] = firestore_health.get("connection", False)
            health["details"]["firestore"] = firestore_health.get("details", {})
            
            if not health["firestore"]:
                health["status"] = "error"
                
        except Exception as e:
            health["status"] = "error"
            health["details"]["firestore_error"] = str(e)
            
        return health
