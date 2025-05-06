"""
Firestore adapter for the MemoryManager interface in the AI Orchestration System.

This module provides an adapter that implements the MemoryManager interface
using the new AsyncFirestoreStorageManager, bridging between the domain
models and Firestore storage.
"""

import logging
import traceback
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, cast, deque
from collections import deque

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
        
        # Enhanced error tracking
        self._error_count = 0
        self._max_errors = 100  # Maximum number of errors to track
        self._errors = deque(maxlen=self._max_errors)  # Track multiple errors
        self._max_errors_before_unhealthy = 5
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
        
        # Track error details
        error_info = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc()
        }
        
        self._errors.append(error_info)
        self._last_error = error_info
        logger.warning(f"Error in FirestoreMemoryManagerV2: {error}")
            
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
        Perform semantic search using vector embeddings with optimized implementation.
        
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
            # Check if numpy is available for optimized vector operations
            try:
                import numpy as np
                NUMPY_AVAILABLE = True
            except ImportError:
                NUMPY_AVAILABLE = False
                
            # Set up filters
            query_filters = {USER_ID_FIELD: user_id}
            
            # Add persona filter if provided
            if persona_context and persona_context.name:
                query_filters[PERSONA_FIELD] = persona_context.name
                
            # Use pagination to avoid loading all documents at once
            page_size = 100  # Process in smaller batches
            results_with_scores = []
            
            # Convert query embedding to numpy array if available
            if NUMPY_AVAILABLE:
                query_np = np.array(query_embedding)
                query_magnitude = np.linalg.norm(query_np)
            else:
                query_magnitude = sum(x * x for x in query_embedding) ** 0.5
            
            # Process documents in batches
            collection = self.firestore.config.get_collection_name(MEMORY_ITEMS_COLLECTION)
            cursor = None
            
            # Use a semaphore to limit concurrent processing
            semaphore = asyncio.Semaphore(10)
            
            while True:
                # Get next batch of documents
                docs = await self.firestore.query_documents(
                    collection=collection,
                    filters=query_filters,
                    limit=page_size,
                    cursor=cursor
                )
                
                if not docs:
                    break
                    
                # Update cursor for next batch
                cursor = docs[-1]
                
                # Filter to documents with embeddings
                docs_with_embeddings = [doc for doc in docs if doc.get("embedding")]
                
                # Process documents concurrently with limited concurrency
                async def process_doc(doc):
                    async with semaphore:
                        embedding = doc.get("embedding")
                        if not embedding or len(embedding) != len(query_embedding):
                            return None
                            
                        # Calculate similarity using numpy if available
                        if NUMPY_AVAILABLE:
                            doc_np = np.array(embedding)
                            doc_magnitude = np.linalg.norm(doc_np)
                            if doc_magnitude > 0 and query_magnitude > 0:
                                similarity = np.dot(query_np, doc_np) / (doc_magnitude * query_magnitude)
                            else:
                                similarity = 0
                        else:
                            # Fallback to pure Python
                            dot_product = sum(a * b for a, b in zip(query_embedding, embedding))
                            doc_magnitude = sum(a * a for a in embedding) ** 0.5
                            similarity = (
                                dot_product / (doc_magnitude * query_magnitude)
                                if doc_magnitude > 0 and query_magnitude > 0
                                else 0
                            )
                        
                        # Return result if similarity is positive
                        if similarity > 0:
                            return (document_to_memory_item(doc), similarity)
                        return None
                
                # Process batch concurrently
                batch_results = await asyncio.gather(*[process_doc(doc) for doc in docs_with_embeddings])
                
                # Filter out None results and add to overall results
                results_with_scores.extend([result for result in batch_results if result])
                
                # If we have enough results or this was the last batch, stop
                if len(results_with_scores) >= top_k * 2 or len(docs) < page_size:
                    break
            
            # Sort by similarity (descending) and take top_k
            results_with_scores.sort(key=lambda x: x[1], reverse=True)
            results = [item for item, _ in results_with_scores[:top_k]]
            
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
        
        This method performs comprehensive health checks on the Firestore
        backend, providing detailed status information.
        
        Returns:
            MemoryHealth: Dictionary with detailed health status information
        """
        health: MemoryHealth = {
            "status": "healthy",
            "firestore": False,
            "redis": False,  # This implementation doesn't use Redis
            "error_count": self._error_count,
            "details": {
                "version": "v2",
                "timestamp": datetime.utcnow().isoformat(),
                "provider": "firestore_v2",
                "implementation": self.__class__.__name__
            },
        }
        
        # Add recent errors
        if self._errors:
            health["details"]["recent_errors"] = list(self._errors)[-5:]  # Last 5 errors
        
        if self._last_error:
            health["last_error"] = self._last_error["timestamp"]
            health["details"]["last_error"] = self._last_error
            
        # Check if initialized
        if not self._is_initialized:
            try:
                await self.initialize()
                health["details"]["initialization"] = "Initialized during health check"
            except Exception as e:
                health["status"] = "unhealthy"
                health["details"]["initialization_error"] = str(e)
                return health
                
        # Check Firestore connection
        try:
            # Try a simple operation to verify connection
            start_time = time.time()
            await self.firestore.ping()
            latency = time.time() - start_time
            
            health["firestore"] = True
            health["details"]["firestore_latency_ms"] = round(latency * 1000, 2)
            
        except Exception as e:
            health["status"] = "unhealthy"
            health["details"]["firestore_error"] = str(e)
            logger.warning(f"Firestore health check failed: {e}")
        
        # Add operation statistics
        try:
            # Get collection stats
            collection = self.firestore.config.get_collection_name(MEMORY_ITEMS_COLLECTION)
            count = await self.firestore.count_documents(collection)
            
            health["details"]["item_count"] = count
        except Exception as e:
            health["details"]["stats_error"] = str(e)
            logger.warning(f"Failed to get collection stats: {e}")
        
        # Add connection pool stats
        try:
            pool_size = len(self.firestore._client_pool)
            health["details"]["connection_pool_size"] = pool_size
        except Exception:
            pass
        
        # Determine overall health status
        if not health["firestore"]:
            health["status"] = "unhealthy"
        elif self._error_count >= self._max_errors_before_unhealthy:
            health["status"] = "degraded"
            health["details"]["reason"] = f"High error rate ({self._error_count} errors)"
        
        return health
