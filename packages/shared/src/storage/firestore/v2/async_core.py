"""
Asynchronous Firestore storage implementation for the AI Orchestration System.

This module provides an asynchronous implementation of Firestore storage
operations, using native async clients where possible and falling back to
thread pools for synchronous operations.
"""

import asyncio
import json
import logging
import os
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, TypeVar, Generic, Type, cast, Callable, Awaitable

# Import Firestore
try:
    from google.cloud import firestore
    from google.cloud.firestore import AsyncClient
    from google.api_core.exceptions import GoogleAPIError
    from google.oauth2 import service_account
except ImportError:
    raise ImportError(
        "Firestore library not available. Install with: pip install google-cloud-firestore"
    )

from packages.shared.src.storage.base import AsyncStorageManager
from packages.shared.src.storage.config import StorageConfig
from packages.shared.src.storage.exceptions import StorageError, ConnectionError, ValidationError, OperationError
from packages.shared.src.storage.firestore.constants import (
    MEMORY_ITEMS_COLLECTION, AGENT_DATA_COLLECTION, MAX_BATCH_SIZE
)
from packages.shared.src.storage.firestore.v2.core import FirestoreStorageManager

# Type variable for document data
T = TypeVar('T')


class AsyncFirestoreStorageManager(AsyncStorageManager):
    """
    Asynchronous Firestore storage manager implementation with connection pooling.
    
    This class provides asynchronous functionality for interacting with Google Cloud Firestore,
    using the native Firestore async client where possible, with proper connection pooling
    for improved stability and performance.
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        credentials_json: Optional[str] = None,
        credentials_path: Optional[str] = None,
        config: Optional[StorageConfig] = None,
        log_level: int = logging.INFO,
        connection_pool_size: int = 10,
    ):
        """
        Initialize the async Firestore storage manager.
        
        Args:
            project_id: Optional Google Cloud project ID
            credentials_json: Optional JSON string containing service account credentials
            credentials_path: Optional path to service account credentials file
            config: Optional storage configuration
            log_level: Logging level for this instance
            connection_pool_size: Maximum size of the connection pool
        """
        super().__init__(config, log_level)
        
        self._async_client = None
        self._sync_manager = FirestoreStorageManager(
            project_id=project_id,
            credentials_json=credentials_json,
            credentials_path=credentials_path,
            config=config,
            log_level=log_level
        )
        self._project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self._credentials_json = credentials_json
        self._credentials_path = credentials_path or os.environ.get(
            "GOOGLE_APPLICATION_CREDENTIALS"
        )
        self._credentials = None
        
        # Connection pool settings
        self._connection_pool_size = connection_pool_size
        self._client_pool: List[AsyncClient] = []
        self._pool_lock = asyncio.Lock()
        self._pool_semaphore = asyncio.Semaphore(connection_pool_size)
        
    def initialize(self) -> None:
        """
        Initialize the connection to Firestore (synchronous).
        
        This is a pass-through to the synchronous manager's initialize method.
        Consider using initialize_async for asynchronous code.
        
        Raises:
            ConnectionError: If connection to Firestore fails
            ValueError: If required configuration is missing
        """
        self._sync_manager.initialize()
        self._initialized = self._sync_manager._initialized
        
    async def initialize_async(self) -> None:
        """
        Initialize the Firestore async client.
        
        This method initializes the Firestore async client and creates
        the connection pool.
        
        Raises:
            ConnectionError: If connection to Firestore fails
        """
        if self._initialized:
            return
            
        # Initialize the sync manager
        await asyncio.to_thread(self._sync_manager.initialize)
        
        try:
            # Validate project_id
            if not self._project_id:
                raise ValueError("Google Cloud project ID is required")
                
            # Set up credentials (reusing from sync manager if possible)
            if self._sync_manager._credentials:
                self._credentials = self._sync_manager._credentials
            elif self._credentials_json:
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
                
            # Create connection pool
            async with self._pool_lock:
                for _ in range(self._connection_pool_size):
                    client = AsyncClient(
                        project=self._project_id,
                        credentials=self._credentials
                    )
                    self._client_pool.append(client)
                    
            # Create a client for operations that don't use the pool
            self._async_client = AsyncClient(
                project=self._project_id,
                credentials=self._credentials
            )
                
            self._initialized = True
            self._logger.info(f"Initialized Firestore async client with connection pool size {self._connection_pool_size}")
            
        except GoogleAPIError as e:
            self._logger.error(f"Failed to initialize async Firestore: {e}")
            raise ConnectionError(f"Failed to connect to async Firestore: {e}", e)
        except ValueError as e:
            self._logger.error(f"Invalid configuration: {e}")
            raise
        except Exception as e:
            self._logger.error(f"Unexpected error initializing async Firestore: {e}")
            raise ConnectionError(f"Failed to initialize async Firestore: {e}", e)
            
    def close(self) -> None:
        """
        Close the connection to Firestore (synchronous).
        
        This is a pass-through to the synchronous manager's close method.
        Consider using close_async for asynchronous code.
        """
        self._sync_manager.close()
        
        # Also close the async client if it exists
        try:
            if self._async_client:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._async_client.close())
                else:
                    loop.run_until_complete(self._async_client.close())
        except Exception as e:
            self._logger.warning(f"Error closing async Firestore client: {e}")
            
        self._async_client = None
        self._initialized = False
        
    async def close_async(self) -> None:
        """
        Close the Firestore async client and release resources.
        """
        # Close the sync manager
        await asyncio.to_thread(self._sync_manager.close)
        
        # Close all clients in the pool
        async with self._pool_lock:
            for client in self._client_pool:
                try:
                    await client.close()
                except Exception as e:
                    self._logger.warning(f"Error closing pooled client: {e}")
            self._client_pool.clear()
            
        # Close the main client
        if self._async_client:
            try:
                await self._async_client.close()
            except Exception as e:
                self._logger.warning(f"Error closing async client: {e}")
            self._async_client = None
            
        self._logger.debug("Closed Firestore async client")
        self._initialized = False
        
    async def _get_client(self) -> AsyncClient:
        """
        Get a client from the pool.
        
        Returns:
            Firestore AsyncClient
            
        Raises:
            ConnectionError: If no clients are available
        """
        if not self._initialized:
            raise ConnectionError("Firestore client not initialized")
            
        async with self._pool_semaphore:
            async with self._pool_lock:
                if not self._client_pool:
                    # Create a new client if pool is empty
                    client = AsyncClient(
                        project=self._project_id,
                        credentials=self._credentials
                    )
                    return client
                else:
                    return self._client_pool.pop()
                    
    async def _release_client(self, client: AsyncClient) -> None:
        """
        Return a client to the pool.
        
        Args:
            client: Firestore AsyncClient to return to the pool
        """
        if client is self._async_client:
            # Don't return the main client to the pool
            return
            
        async with self._pool_lock:
            if len(self._client_pool) < self._connection_pool_size:
                self._client_pool.append(client)
            else:
                # Pool is full, close the client
                try:
                    await client.close()
                except Exception as e:
                    self._logger.warning(f"Error closing excess client: {e}")
                    
    T = TypeVar('T')
    
    async def execute_with_client(self, operation: Callable[[AsyncClient], Awaitable[T]]) -> T:
        """
        Execute an operation with a client from the pool.
        
        Args:
            operation: Async callable that takes a client and returns a result
            
        Returns:
            Result of the operation
            
        Raises:
            ConnectionError: If connection to Firestore fails
            OperationError: If the operation fails
        """
        client = None
        try:
            client = await self._get_client()
            return await operation(client)
        except Exception as e:
            if isinstance(e, GoogleAPIError):
                raise OperationError(f"Firestore operation failed: {e}")
            else:
                raise ConnectionError(f"Failed to connect to Firestore: {e}")
        finally:
            if client:
                await self._release_client(client)
                
    async def get_document(self, collection: str, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document from Firestore asynchronously.
        
        Args:
            collection: Collection name
            document_id: Document ID
            
        Returns:
            Document data as a dictionary, or None if not found
            
        Raises:
            OperationError: If the retrieval fails
        """
        self.check_initialized()
        
        async def _operation(client: AsyncClient) -> Optional[Dict[str, Any]]:
            doc_ref = client.collection(collection).document(document_id)
            doc = await doc_ref.get()
            
            # Return data if document exists
            if doc.exists:
                return doc.to_dict()
            return None
            
        try:
            return await self.execute_with_client(_operation)
        except GoogleAPIError as e:
            self.handle_operation_error("get_document", e)
        except Exception as e:
            self.handle_operation_error("get_document", e)
            
    async def set_document(
        self, 
        collection: str, 
        document_id: str, 
        data: Dict[str, Any],
        merge: bool = False
    ) -> None:
        """
        Set a document in Firestore asynchronously.
        
        Args:
            collection: Collection name
            document_id: Document ID
            data: Document data
            merge: Whether to merge with existing data or overwrite
            
        Raises:
            OperationError: If the operation fails
        """
        self.check_initialized()
        
        async def _operation(client: AsyncClient) -> None:
            doc_ref = client.collection(collection).document(document_id)
            await doc_ref.set(data, merge=merge)
            
        try:
            await self.execute_with_client(_operation)
        except GoogleAPIError as e:
            self.handle_operation_error("set_document", e)
        except Exception as e:
            self.handle_operation_error("set_document", e)
            
    async def delete_document(self, collection: str, document_id: str) -> bool:
        """
        Delete a document from Firestore asynchronously.
        
        Args:
            collection: Collection name
            document_id: Document ID
            
        Returns:
            True if the document was deleted, False if it didn't exist
            
        Raises:
            OperationError: If the operation fails
        """
        self.check_initialized()
        
        async def _operation(client: AsyncClient) -> bool:
            doc_ref = client.collection(collection).document(document_id)
            
            # Check if document exists
            doc = await doc_ref.get()
            if not doc.exists:
                return False
                
            # Delete the document
            await doc_ref.delete()
            return True
            
        try:
            return await self.execute_with_client(_operation)
        except GoogleAPIError as e:
            self.handle_operation_error("delete_document", e)
        except Exception as e:
            self.handle_operation_error("delete_document", e)
            
    async def query_documents(
        self, 
        collection: str, 
        filters: Dict[str, Any],
        order_by: Optional[str] = None,
        direction: str = "ASCENDING",
        limit: Optional[int] = None,
        cursor: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Query documents from Firestore asynchronously.
        
        Args:
            collection: Collection name
            filters: Dictionary of field-value pairs to filter by
            order_by: Optional field to order by
            direction: Sort direction ("ASCENDING" or "DESCENDING")
            limit: Maximum number of results to return
            cursor: Optional cursor for pagination
            
        Returns:
            List of document data dictionaries
            
        Raises:
            OperationError: If the query fails
            ValueError: If filter parameters are invalid
        """
        self.check_initialized()
        
        async def _operation(client: AsyncClient) -> List[Dict[str, Any]]:
            # Start with collection reference
            query = client.collection(collection)
            
            # Add filters
            for key, value in filters.items():
                # Check for range queries (dict with "start" and/or "end")
                if isinstance(value, dict) and ("start" in value or "end" in value):
                    if "start" in value:
                        query = query.where(key, ">=", value["start"])
                    if "end" in value:
                        query = query.where(key, "<=", value["end"])
                else:
                    # Standard equality filter
                    query = query.where(key, "==", value)
                    
            # Add ordering if specified
            if order_by:
                # Determine direction
                dir_value = firestore.Query.ASCENDING
                if direction.upper() == "DESCENDING":
                    dir_value = firestore.Query.DESCENDING
                    
                query = query.order_by(order_by, direction=dir_value)
                
            # Add limit if specified
            if limit:
                query = query.limit(limit)
                
            # Add cursor if specified
            if cursor:
                query = query.start_after(cursor)
                
            # Execute query
            docs = await query.get()
            
            # Convert to list of dictionaries
            results = []
            for doc in docs:
                try:
                    doc_data = doc.to_dict()
                    if doc_data:
                        doc_data["id"] = doc.id  # Add document ID to data
                        results.append(doc_data)
                except Exception as e:
                    self._logger.warning(f"Error parsing document {doc.id}: {e}")
                    continue
                    
            return results
            
        try:
            return await self.execute_with_client(_operation)
        except GoogleAPIError as e:
            self.handle_operation_error("query_documents", e)
        except Exception as e:
            self.handle_operation_error("query_documents", e)
            
    async def batch_operation(
        self,
        operations: List[Dict[str, Any]],
        batch_size: int = MAX_BATCH_SIZE
    ) -> int:
        """
        Perform a batch operation on Firestore asynchronously.
        
        Args:
            operations: List of operation dictionaries with:
                - type: "set", "update", or "delete"
                - collection: Collection name
                - document_id: Document ID
                - data: Document data (for "set" and "update")
                - merge: Whether to merge (for "set", optional)
            batch_size: Maximum batch size (Firestore limit is 500)
            
        Returns:
            Number of successful operations
            
        Raises:
            OperationError: If the batch operation fails
            ValueError: If operation parameters are invalid
        """
        self.check_initialized()
        
        if not operations:
            return 0
            
        async def _operation(client: AsyncClient) -> int:
            count = 0
            batch = client.batch()
            
            for op in operations:
                # Validate operation
                op_type = op.get("type")
                if op_type not in ["set", "update", "delete"]:
                    raise ValueError(f"Invalid operation type: {op_type}")
                    
                # Get document reference
                collection = op.get("collection")
                document_id = op.get("document_id")
                if not collection or not document_id:
                    raise ValueError("Collection and document_id are required")
                    
                doc_ref = client.collection(collection).document(document_id)
                
                # Perform operation
                if op_type == "set":
                    data = op.get("data")
                    if not data:
                        raise ValueError("Data is required for 'set' operations")
                    merge = op.get("merge", False)
                    batch.set(doc_ref, data, merge=merge)
                    
                elif op_type == "update":
                    data = op.get("data")
                    if not data:
                        raise ValueError("Data is required for 'update' operations")
                    batch.update(doc_ref, data)
                    
                elif op_type == "delete":
                    batch.delete(doc_ref)
                    
                count += 1
                
                # Commit batch if we hit the batch size
                if count % batch_size == 0:
                    await batch.commit()
                    batch = client.batch()
                    
            # Commit any remaining operations
            if count % batch_size != 0:
                await batch.commit()
                
            return count
            
        try:
            return await self.execute_with_client(_operation)
        except GoogleAPIError as e:
            self.handle_operation_error("batch_operation", e)
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            self.handle_operation_error("batch_operation", e)
            
    async def count_documents(self, collection: str, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count documents in a collection.
        
        Args:
            collection: Collection name
            filters: Optional dictionary of field-value pairs to filter by
            
        Returns:
            Number of documents matching the filters
            
        Raises:
            OperationError: If the count operation fails
        """
        self.check_initialized()
        
        async def _operation(client: AsyncClient) -> int:
            # Start with collection reference
            query = client.collection(collection)
            
            # Add filters if provided
            if filters:
                for key, value in filters.items():
                    # Check for range queries (dict with "start" and/or "end")
                    if isinstance(value, dict) and ("start" in value or "end" in value):
                        if "start" in value:
                            query = query.where(key, ">=", value["start"])
                        if "end" in value:
                            query = query.where(key, "<=", value["end"])
                    else:
                        # Standard equality filter
                        query = query.where(key, "==", value)
            
            # Execute count query
            snapshot = await query.count().get()
            return snapshot.count
            
        try:
            return await self.execute_with_client(_operation)
        except GoogleAPIError as e:
            self.handle_operation_error("count_documents", e)
            return 0
        except Exception as e:
            self.handle_operation_error("count_documents", e)
            return 0
            
    async def ping(self) -> bool:
        """
        Ping the Firestore service to check connectivity.
        
        Returns:
            True if connection is healthy, False otherwise
        """
        self.check_initialized()
        
        async def _operation(client: AsyncClient) -> bool:
            # Try to get a non-existent document to test connection
            doc_ref = client.collection("_ping_test").document("_ping_doc")
            await doc_ref.get()
            return True
            
        try:
            return await self.execute_with_client(_operation)
        except Exception as e:
            self._logger.warning(f"Ping failed: {e}")
            return False
            
    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health of the Firestore connection asynchronously.
        
        Returns:
            Dictionary with health status information
        """
        health = {
            "status": "healthy",
            "connection": False,
            "details": {
                "pool_size": len(self._client_pool) if self._initialized else 0,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        if not self._initialized:
            try:
                await self.initialize_async()
                health["details"]["initialization"] = "Initialized during health check"
            except Exception as e:
                health["status"] = "error"
                health["details"]["initialization_error"] = str(e)
                return health
                
        try:
            # Try to ping Firestore
            connection_healthy = await self.ping()
            health["connection"] = connection_healthy
            
            if not connection_healthy:
                health["status"] = "error"
                health["details"]["connection_check"] = "Failed to connect to Firestore"
            else:
                health["details"]["connection_check"] = "Successfully verified connectivity"
            
            return health
        except Exception as e:
            return {
                "status": "error",
                "connection": False,
                "details": {
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
            }
