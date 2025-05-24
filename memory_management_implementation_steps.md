# Memory Management Implementation Steps

This document outlines the specific implementation steps for refactoring the memory management system according to the plan in `memory_management_refactoring_plan.md`.

## Phase 1: Create Standardized Base Classes

### Step 1: Create Storage Exception Hierarchy

Create a new file `packages/shared/src/storage/exceptions.py`:

```python
"""
Storage-related exceptions for the AI Orchestration System.

This module defines a structured exception hierarchy for all storage-related
errors, ensuring consistent error handling across different storage backends.
"""

class StorageError(Exception):
    """Base exception for all storage-related errors."""

    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(message)
        self.original_exception = original_exception


class ConnectionError(StorageError):
    """Exception raised when a connection to the storage backend fails."""
    pass


class ValidationError(StorageError):
    """Exception raised when data validation fails."""
    pass


class OperationError(StorageError):
    """Exception raised when a storage operation fails."""

    def __init__(self, operation: str, message: str, original_exception: Exception = None):
        super().__init__(f"{operation} operation failed: {message}", original_exception)
        self.operation = operation
```

### Step 2: Create Storage Configuration Module

Create a new file `packages/shared/src/storage/config.py`:

```python
"""
Storage configuration for the AI Orchestration System.

This module centralizes storage configuration settings, including collection
names, default settings, and environment-based configuration.
"""

import os
from typing import Dict, Any, Optional

# Default collection names
MEMORY_RECORDS_COLLECTION = "memory_records"
AGENT_DATA_COLLECTION = "agent_data"
USER_SESSIONS_COLLECTION = "user_sessions"
VECTOR_EMBEDDINGS_COLLECTION = "vector_embeddings"

# Environment-based overrides
ENV_PREFIX = "ORCHESTRA_STORAGE_"


def get_collection_name(base_name: str, namespace: Optional[str] = None) -> str:
    """
    Get a collection name, optionally with a namespace prefix.

    Args:
        base_name: Base collection name
        namespace: Optional namespace to prefix (for multi-tenant deployments)

    Returns:
        Collection name, potentially with namespace and/or environment overrides
    """
    # Check for environment override
    env_override = os.environ.get(f"{ENV_PREFIX}{base_name.upper()}")
    if env_override:
        base_name = env_override

    # Add namespace if provided
    if namespace:
        return f"{namespace}_{base_name}"

    return base_name


class StorageConfig:
    """Storage configuration class for centralizing settings."""

    def __init__(
        self,
        namespace: Optional[str] = None,
        collection_overrides: Optional[Dict[str, str]] = None
    ):
        """
        Initialize storage configuration.

        Args:
            namespace: Optional namespace for multi-tenant deployments
            collection_overrides: Optional mapping of collection names to override
        """
        self.namespace = namespace
        self.collection_overrides = collection_overrides or {}

    def get_collection_name(self, base_name: str) -> str:
        """
        Get a collection name with all configuration applied.

        Args:
            base_name: Base collection name

        Returns:
            Final collection name with overrides and namespace applied
        """
        # Apply override if present
        name = self.collection_overrides.get(base_name, base_name)

        # Apply namespace if present
        return get_collection_name(name, self.namespace)
```

### Step 3: Create Base Storage Manager Class

Create a new file `packages/shared/src/storage/base.py`:

```python
"""
Base storage manager classes for the AI Orchestration System.

This module provides base classes for both synchronous and asynchronous
storage managers, defining common functionality and interfaces.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TypeVar, Generic, Type

from packages.shared.src.storage.config import StorageConfig
from packages.shared.src.storage.exceptions import StorageError, ConnectionError, OperationError

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for operation result
T = TypeVar('T')


class BaseStorageManager(ABC):
    """
    Base class for all storage managers.

    This abstract class defines common functionality for storage managers,
    including configuration, initialization, and error handling.
    """

    def __init__(
        self,
        config: Optional[StorageConfig] = None,
        log_level: int = logging.INFO
    ):
        """
        Initialize the base storage manager.

        Args:
            config: Optional storage configuration
            log_level: Logging level for this instance
        """
        self.config = config or StorageConfig()
        self._initialized = False
        self._logger = self._setup_logger(log_level)

    def _setup_logger(self, log_level: int) -> logging.Logger:
        """
        Set up a logger instance for this storage manager.

        Args:
            log_level: Logging level to use

        Returns:
            Configured logger instance
        """
        logger_name = f"{__name__}.{self.__class__.__name__}"
        instance_logger = logging.getLogger(logger_name)
        instance_logger.setLevel(log_level)
        return instance_logger

    def _get_collection_name(self, base_name: str) -> str:
        """
        Get a collection name using the configuration.

        Args:
            base_name: Base collection name

        Returns:
            Final collection name with all configuration applied
        """
        return self.config.get_collection_name(base_name)

    def check_initialized(self) -> None:
        """
        Check if the storage manager is initialized.

        Raises:
            RuntimeError: If the storage manager is not initialized
        """
        if not self._initialized:
            raise RuntimeError(
                f"{self.__class__.__name__} not initialized. Call initialize() first."
            )

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the storage manager.

        This method should set up any necessary connections, create
        resources, or perform other initialization tasks.

        Raises:
            ConnectionError: If connection to the storage backend fails
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Close the storage manager and release resources.

        This method should clean up any resources used by the storage manager,
        such as database connections, file handles, etc.
        """
        pass

    def handle_operation_error(
        self,
        operation: str,
        error: Exception,
        message: Optional[str] = None
    ) -> None:
        """
        Handle an operation error in a standardized way.

        Args:
            operation: The name of the operation that failed
            error: The exception that was raised
            message: Optional additional message to include

        Raises:
            OperationError: A standardized operation error
        """
        error_message = message or str(error)
        self._logger.error(f"{operation} failed: {error_message}", exc_info=True)
        raise OperationError(operation, error_message, error)


class AsyncStorageManager(BaseStorageManager):
    """
    Base class for asynchronous storage managers.

    This abstract class extends BaseStorageManager with async-specific
    functionality and interfaces.
    """

    @abstractmethod
    async def initialize_async(self) -> None:
        """
        Initialize the storage manager asynchronously.

        This method should set up any necessary async connections and resources.

        Raises:
            ConnectionError: If connection to the storage backend fails
        """
        pass

    @abstractmethod
    async def close_async(self) -> None:
        """
        Close the storage manager and release resources asynchronously.

        This method should clean up any async resources used by the storage manager.
        """
        pass
```

## Phase 2: Implement Core Storage Logic

### Step 4: Create the Synchronous Firestore Implementation

Create a new file `packages/shared/src/storage/firestore/v2/core.py`:

```python
"""
Core Firestore storage implementation for the AI Orchestration System.

This module provides a synchronous implementation of Firestore storage
operations, serving as the foundation for higher-level interfaces.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, TypeVar, Generic, Type, cast

# Import Firestore
try:
    from google.cloud import firestore
    from google.cloud.firestore import Client as FirestoreClient
    from google.api_core.exceptions import GoogleAPIError
    from google.oauth2 import service_account
except ImportError:
    raise ImportError(
        "Firestore library not available. Install with: pip install google-cloud-firestore"
    )

from packages.shared.src.storage.base import BaseStorageManager
from packages.shared.src.storage.config import StorageConfig, MEMORY_RECORDS_COLLECTION, AGENT_DATA_COLLECTION
from packages.shared.src.storage.exceptions import StorageError, ConnectionError, ValidationError, OperationError

# Type variable for document data
T = TypeVar('T')


class FirestoreStorageManager(BaseStorageManager):
    """
    Synchronous Firestore storage manager implementation.

    This class provides core functionality for interacting with Google Cloud Firestore,
    handling connection management, document operations, and error handling.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        credentials_json: Optional[str] = None,
        credentials_path: Optional[str] = None,
        config: Optional[StorageConfig] = None,
        log_level: int = logging.INFO
    ):
        """
        Initialize the Firestore storage manager.

        Args:
            project_id: Optional Google Cloud project ID
            credentials_json: Optional JSON string containing service account credentials
            credentials_path: Optional path to service account credentials file
            config: Optional storage configuration
            log_level: Logging level for this instance
        """
        super().__init__(config, log_level)

        self._client = None
        self._project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self._credentials_json = credentials_json
        self._credentials_path = credentials_path or os.environ.get(
            "GOOGLE_APPLICATION_CREDENTIALS"
        )
        self._credentials = None

    def initialize(self) -> None:
        """
        Initialize the connection to Firestore.

        This method establishes a connection to the Firestore database using the
        provided credentials or application default credentials.

        Raises:
            ConnectionError: If connection to Firestore fails
            ValueError: If required configuration is missing
        """
        if self._initialized:
            return

        try:
            # Validate project_id
            if not self._project_id:
                raise ValueError("Google Cloud project ID is required")

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

            # Initialize Firestore client
            if self._credentials:
                self._client = firestore.Client(
                    project=self._project_id, credentials=self._credentials
                )
            else:
                # Use Application Default Credentials
                self._client = firestore.Client(project=self._project_id)

            self._initialized = True
            self._logger.info(f"Successfully initialized Firestore connection to project {self._project_id}")

        except GoogleAPIError as e:
            self._logger.error(f"Failed to initialize Firestore: {e}")
            raise ConnectionError(f"Failed to connect to Firestore: {e}", e)
        except ValueError as e:
            self._logger.error(f"Invalid configuration: {e}")
            raise
        except Exception as e:
            self._logger.error(f"Unexpected error initializing Firestore: {e}")
            raise ConnectionError(f"Failed to initialize Firestore: {e}", e)

    def close(self) -> None:
        """
        Close the connection to Firestore.

        This method cleans up resources used by the Firestore client.
        """
        if self._client and hasattr(self._client, "close") and callable(getattr(self._client, "close")):
            try:
                self._client.close()
                self._logger.debug("Closed Firestore client")
            except Exception as e:
                self._logger.warning(f"Error closing Firestore client: {e}")

        self._client = None
        self._initialized = False

    def get_document(self, collection: str, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document from Firestore.

        Args:
            collection: Collection name
            document_id: Document ID

        Returns:
            Document data as a dictionary, or None if not found

        Raises:
            OperationError: If the retrieval fails
        """
        self.check_initialized()

        try:
            # Get the document
            doc_ref = self._client.collection(collection).document(document_id)
            doc = doc_ref.get()

            # Return data if document exists
            if doc.exists:
                return doc.to_dict()
            return None

        except GoogleAPIError as e:
            self.handle_operation_error("get_document", e)
        except Exception as e:
            self.handle_operation_error("get_document", e)

    def set_document(
        self,
        collection: str,
        document_id: str,
        data: Dict[str, Any],
        merge: bool = False
    ) -> None:
        """
        Set a document in Firestore.

        Args:
            collection: Collection name
            document_id: Document ID
            data: Document data
            merge: Whether to merge with existing data or overwrite

        Raises:
            OperationError: If the operation fails
        """
        self.check_initialized()

        try:
            # Set the document
            doc_ref = self._client.collection(collection).document(document_id)
            doc_ref.set(data, merge=merge)

        except GoogleAPIError as e:
            self.handle_operation_error("set_document", e)
        except Exception as e:
            self.handle_operation_error("set_document", e)

    def delete_document(self, collection: str, document_id: str) -> bool:
        """
        Delete a document from Firestore.

        Args:
            collection: Collection name
            document_id: Document ID

        Returns:
            True if the document was deleted, False if it didn't exist

        Raises:
            OperationError: If the operation fails
        """
        self.check_initialized()

        try:
            # Get document reference
            doc_ref = self._client.collection(collection).document(document_id)

            # Check if document exists
            doc = doc_ref.get()
            if not doc.exists:
                return False

            # Delete the document
            doc_ref.delete()
            return True

        except GoogleAPIError as e:
            self.handle_operation_error("delete_document", e)
        except Exception as e:
            self.handle_operation_error("delete_document", e)

    def query_documents(
        self,
        collection: str,
        filters: Dict[str, Any],
        order_by: Optional[str] = None,
        direction: str = "ASCENDING",
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query documents from Firestore.

        Args:
            collection: Collection name
            filters: Dictionary of field-value pairs to filter by
            order_by: Optional field to order by
            direction: Sort direction ("ASCENDING" or "DESCENDING")
            limit: Maximum number of results to return

        Returns:
            List of document data dictionaries

        Raises:
            OperationError: If the query fails
            ValueError: If filter parameters are invalid
        """
        self.check_initialized()

        try:
            # Start with collection reference
            query = self._client.collection(collection)

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

            # Execute query
            docs = query.stream()

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

        except GoogleAPIError as e:
            self.handle_operation_error("query_documents", e)
        except Exception as e:
            self.handle_operation_error("query_documents", e)

    def batch_operation(
        self,
        operations: List[Dict[str, Any]],
        batch_size: int = 400
    ) -> int:
        """
        Perform a batch operation on Firestore.

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

        try:
            count = 0
            batch = self._client.batch()

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

                doc_ref = self._client.collection(collection).document(document_id)

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
                    batch.commit()
                    batch = self._client.batch()

            # Commit any remaining operations
            if count % batch_size != 0:
                batch.commit()

            return count

        except GoogleAPIError as e:
            self.handle_operation_error("batch_operation", e)
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            self.handle_operation_error("batch_operation", e)
```

### Step 5: Create the Async Firestore Implementation

Create a new file `packages/shared/src/storage/firestore/v2/async_core.py`:

```python
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
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, TypeVar, Generic, Type, cast

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
from packages.shared.src.storage.config import StorageConfig, MEMORY_RECORDS_COLLECTION, AGENT_DATA_COLLECTION
from packages.shared.src.storage.exceptions import StorageError, ConnectionError, ValidationError, OperationError
from packages.shared.src.storage.firestore.v2.core import FirestoreStorageManager

# Type variable for document data
T = TypeVar('T')


class AsyncFirestoreStorageManager(AsyncStorageManager):
    """
    Asynchronous Firestore storage manager implementation.

    This class provides asynchronous functionality for interacting with Google Cloud Firestore,
    using the native Firestore async client where possible.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        credentials_json: Optional[str] = None,
        credentials_path: Optional[str] = None,
        config: Optional[StorageConfig] = None,
        log_level: int = logging.INFO
    ):
        """
        Initialize the async Firestore storage manager.

        Args:
            project_id: Optional Google Cloud project ID
            credentials_json: Optional JSON string containing service account credentials
            credentials_path: Optional path to service account credentials file
            config: Optional storage configuration
            log_level: Logging level for this instance
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
        Initialize the connection to Firestore asynchronously.

        This method establishes connections to both synchronous and asynchronous
        Firestore clients.

        Raises:
            ConnectionError: If connection to Firestore fails
            ValueError: If required configuration is missing
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

            # Initialize Firestore async client
            if self._credentials:
                self._async_client = firestore.AsyncClient(
                    project=self._project_id, credentials=self._credentials
                )
            else:
                # Use Application Default Credentials
                self._async_client = firestore.AsyncClient(project=self._project_id)

            self._initialized = True
            self._logger.info(f"Successfully initialized async Firestore connection to project {self._project_id}")

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
        Close the connection to Firestore asynchronously.

        This method cleans up resources used by both sync and async Firestore clients.
        """
        # Close the sync manager
        await asyncio.to_thread(self._sync_manager.close)

        # Close the async client
        if self._async_client:
            try:
                await self._async_client.close()
                self._logger.debug("Closed async Firestore client")
            except Exception as e:
                self._logger.warning(f"Error closing async Firestore client: {e}")

        self._async_client = None
        self._initialized = False

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

        try:
            # Get the document using the async client
            doc_ref = self._async_client.collection(collection).document(document_id)
            doc = await doc_ref.get()

            # Return data if document exists
            if doc.exists:
                return doc.to_dict()
            return None

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

        try:
            # Set the document using the async client
            doc_ref = self._async_client.collection(collection).document(document_id)
            await doc_ref.set(data, merge=merge)

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

        try:
            # Get document reference using the async client
            doc_ref = self._async_client.collection(collection).document(document_id)

            # Check if document exists
            doc = await doc_ref.get()
            if not doc.exists:
                return False

            # Delete the document
            await doc_ref.delete()
            return True

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
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query documents from Firestore asynchronously.

        Args:
            collection: Collection name
            filters: Dictionary of field-value pairs to filter by
            order_by: Optional field to order by
            direction: Sort direction ("ASCENDING" or "DESCENDING")
            limit: Maximum number of results to return

        Returns:
```
