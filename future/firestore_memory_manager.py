"""
Firestore Memory Manager Implementation for AI Orchestration System.

DEPRECATED: This module is deprecated and will be removed in a future release.

This legacy Firestore memory manager implementation has been replaced by the 
new V2 implementation with improved architecture and error handling.

Please use packages.shared.src.storage.firestore.v2.adapter.FirestoreMemoryManagerV2 instead,
which provides:
- Better separation of concerns between storage and memory management
- More consistent error handling
- Async-first API design
- Improved performance and reliability
- Centralized configuration management

Example migration:
from future.firestore_memory_manager import FirestoreMemoryManager  # Old
# Change to:
from packages.shared.src.storage.firestore.v2 import FirestoreMemoryManagerV2  # New

This module implements the Firestore-backed memory management system
for storing and retrieving memory records in Google Cloud Firestore.
"""

import os
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

# Import Firestore
try:
    from google.cloud import firestore
    from google.cloud.firestore import Client as FirestoreClient
    from google.api_core.exceptions import GoogleAPIError
    from google.oauth2 import service_account
except ImportError:
    firestore = None
    FirestoreClient = object
    service_account = None

    class GoogleAPIError(Exception):
        pass

from packages.shared.src.models.domain_models import MemoryRecord
from packages.shared.src.memory.memory_manager import MemoryHealth


# Set up logger
logger = logging.getLogger(__name__)

# Define collection names
MEMORY_RECORDS_COLLECTION = "memory_records"
AGENT_DATA_COLLECTION = "agent_data"
USER_SESSIONS_COLLECTION = "user_sessions"


class StorageError(Exception):
    """Base exception for storage-related errors."""
    pass


class ValidationError(Exception):
    """Exception for validation errors in storage operations."""
    pass


class FirestoreMemoryManager:
    """
    Firestore implementation of memory management for storing and retrieving MemoryRecord objects.

    This class provides methods to interact with Google Cloud Firestore for storing,
    retrieving, and querying memory records. It handles connection management, error handling,
    and provides a high-level API for working with the memory system.
    """

    def __init__(
        self, 
        project_id: Optional[str] = None, 
        credentials_json: Optional[str] = None,
        credentials_path: Optional[str] = None
    ):
        """
        Initialize the Firestore memory manager.

        Args:
            project_id: Optional Google Cloud project ID. If not provided, will be read from
                        environment variable GOOGLE_CLOUD_PROJECT or from Application Default Credentials.
            credentials_json: Optional JSON string containing service account credentials.
            credentials_path: Optional path to service account credentials file. If not provided,
                             will use Application Default Credentials or environment variables.
        """
        self._client = None
        self._project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self._credentials_json = credentials_json
        self._credentials_path = credentials_path or os.environ.get(
            "GOOGLE_APPLICATION_CREDENTIALS")
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
            # Check if Firestore is available
            if firestore is None:
                logger.error(
                    "Firestore library not available. Install with: pip install google-cloud-firestore")
                raise ImportError(
                    "Firestore library not available. Install with: pip install google-cloud-firestore")

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
        if hasattr(self._client, "close") and callable(getattr(self._client, "close")):
            try:
                self._client.close()
                logger.debug("Closed Firestore client")
            except Exception as e:
                logger.warning(f"Error closing Firestore client: {e}")

        self._client = None
        self._initialized = False

    def _check_initialized(self) -> None:
        """
        Check if the client is initialized and raise error if not.

        Raises:
            RuntimeError: If the client is not initialized
        """
        if not self._initialized or not self._client:
            raise RuntimeError(
                "Firestore client not initialized. Call initialize() first.")

    def save_record(self, record: MemoryRecord, collection: str = MEMORY_RECORDS_COLLECTION) -> str:
        """
        Write the provided MemoryRecord to the specified Firestore collection.

        Args:
            record: The MemoryRecord object to save
            collection: The Firestore collection name to save the record to, defaults to MEMORY_RECORDS_COLLECTION

        Returns:
            The ID of the saved record

        Raises:
            ValueError: If record_id is not provided
            ConnectionError: If Firestore connection fails
            RuntimeError: If any other error occurs during save
        """
        self._check_initialized()

        if not record.record_id:
            raise ValueError(
                "record_id must be provided for saving to Firestore")

        try:
            # Convert MemoryRecord to dict for Firestore
            record_data = record.dict()

            # Convert datetime to Firestore timestamp if needed
            if record_data.get("timestamp"):
                # Keep the original timestamp as is, don't use SERVER_TIMESTAMP
                # as that would overwrite the record's timestamp
                pass

            # Save to Firestore using record_id as document ID
            self._client.collection(collection).document(
                record.record_id).set(record_data)

            logger.info(f"Saved record {record.record_id} to {collection}")
            return record.record_id
        except GoogleAPIError as e:
            error_msg = f"Failed to save record {record.record_id} to Firestore: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error saving record: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def get_record(self, record_id: str, collection: str = MEMORY_RECORDS_COLLECTION) -> MemoryRecord:
        """
        Retrieve a record by its record_id from the specified Firestore collection.

        Args:
            record_id: The ID of the record to retrieve
            collection: The Firestore collection to retrieve from, defaults to MEMORY_RECORDS_COLLECTION

        Returns:
            A MemoryRecord object with the retrieved data

        Raises:
            ValueError: If the record is not found
            ConnectionError: If Firestore connection fails
            RuntimeError: If any other error occurs during retrieval
        """
        self._check_initialized()

        try:
            # Retrieve document from Firestore
            doc_ref = self._client.collection(collection).document(record_id)
            doc = doc_ref.get()

            if not doc.exists:
                raise ValueError(
                    f"Record {record_id} not found in collection {collection}")

            # Convert Firestore document to MemoryRecord
            record_data = doc.to_dict()

            logger.info(f"Retrieved record {record_id} from {collection}")

            # Create and return MemoryRecord object
            return MemoryRecord(**record_data)
        except GoogleAPIError as e:
            error_msg = f"Failed to retrieve record {record_id} from Firestore: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except ValueError:
            # Re-raise ValueError for not found records
            raise
        except Exception as e:
            error_msg = f"Unexpected error retrieving record: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def query_records(self, filters: Dict[str, Any], collection: str = MEMORY_RECORDS_COLLECTION) -> List[MemoryRecord]:
        """
        Retrieve records from Firestore based on provided filters.

        Args:
            filters: Dictionary of field-value pairs to filter by
                    (e.g., {"context": "PayReady", "persona": "Sophia"})
            collection: The Firestore collection to query, defaults to MEMORY_RECORDS_COLLECTION

        Returns:
            List of MemoryRecord objects matching the filters

        Raises:
            ConnectionError: If Firestore connection fails
            RuntimeError: If any other error occurs during query
        """
        self._check_initialized()

        try:
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

            # Execute query
            docs = query.stream()

            # Convert results to MemoryRecord objects
            results = []
            for doc in docs:
                try:
                    doc_data = doc.to_dict()
                    results.append(MemoryRecord(**doc_data))
                except Exception as e:
                    logger.warning(f"Error parsing document {doc.id}: {e}")
                    continue

            logger.info(
                f"Queried {collection} with filters {filters}, found {len(results)} records")

            return results
        except GoogleAPIError as e:
            error_msg = f"Failed to query records from Firestore: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error querying records: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def delete_record(self, record_id: str, collection: str = MEMORY_RECORDS_COLLECTION) -> bool:
        """
        Delete a record from Firestore by its ID.

        Args:
            record_id: The ID of the record to delete
            collection: The Firestore collection to delete from, defaults to MEMORY_RECORDS_COLLECTION

        Returns:
            True if the record was deleted, False if not found

        Raises:
            RuntimeError: If any error occurs during deletion
        """
        self._check_initialized()

        try:
            # Get document reference
            doc_ref = self._client.collection(collection).document(record_id)
            
            # Check if document exists
            doc = doc_ref.get()
            if not doc.exists:
                logger.warning(f"Record {record_id} not found for deletion in {collection}")
                return False
                
            # Delete the document
            doc_ref.delete()
            logger.info(f"Deleted record {record_id} from {collection}")
            return True
        except GoogleAPIError as e:
            error_msg = f"Failed to delete record {record_id} from Firestore: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error deleting record: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def batch_save_records(self, records: List[MemoryRecord], collection: str = MEMORY_RECORDS_COLLECTION) -> int:
        """
        Save multiple records to Firestore in a batch operation.

        Args:
            records: List of MemoryRecord objects to save
            collection: The Firestore collection to save to, defaults to MEMORY_RECORDS_COLLECTION

        Returns:
            Number of records successfully saved

        Raises:
            RuntimeError: If any error occurs during the batch operation
        """
        self._check_initialized()

        if not records:
            return 0

        try:
            batch = self._client.batch()
            count = 0

            for record in records:
                if not record.record_id:
                    logger.warning("Skipping record with no record_id in batch save")
                    continue

                # Convert to dict
                record_data = record.dict()
                
                # Add to batch
                doc_ref = self._client.collection(collection).document(record.record_id)
                batch.set(doc_ref, record_data)
                count += 1

                # Firestore has a limit of 500 operations per batch
                if count % 400 == 0:
                    batch.commit()
                    batch = self._client.batch()

            # Commit any remaining operations
            if count % 400 != 0:
                batch.commit()

            logger.info(f"Batch saved {count} records to {collection}")
            return count
        except GoogleAPIError as e:
            error_msg = f"Failed to batch save records to Firestore: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during batch save: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
            
    def health_check(self) -> MemoryHealth:
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
                self.get_record(test_id)
            except ValueError:
                # Not found is actually good - means connection works
                health["firestore"] = True
                health["details"]["firestore_check"] = "Successfully verified connectivity"
            except Exception as e:
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
