"""
Firestore Memory Manager Implementation for AI Orchestration System.

This module implements the Firestore-backed memory management system
for storing and retrieving memory records in Google Cloud Firestore.
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

# Import Firestore
try:
    from google.cloud import firestore
    from google.cloud.firestore import Client as FirestoreClient
    from google.api_core.exceptions import GoogleAPIError
except ImportError:
    firestore = None
    FirestoreClient = object

    class GoogleAPIError(Exception):
        pass

from packages.shared.src.models.domain_models import MemoryRecord


# Set up logger
logger = logging.getLogger(__name__)


class FirestoreMemoryManager:
    """
    Firestore implementation of memory management for storing and retrieving MemoryRecord objects.

    This class provides methods to interact with Google Cloud Firestore for storing,
    retrieving, and querying memory records. It handles connection management, error handling,
    and provides a high-level API for working with the memory system.
    """

    def __init__(self, project_id: Optional[str] = None, credentials_path: Optional[str] = None):
        """
        Initialize the Firestore memory manager.

        Args:
            project_id: Optional Google Cloud project ID. If not provided, will be read from
                        environment variable GOOGLE_CLOUD_PROJECT or from Application Default Credentials.
            credentials_path: Optional path to service account credentials file. If not provided,
                             will use Application Default Credentials or environment variables.
        """
        self._client = None
        self._project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self._credentials_path = credentials_path or os.environ.get(
            "GOOGLE_APPLICATION_CREDENTIALS")

        # Check if Firestore is available
        if firestore is None:
            logger.error(
                "Firestore library not available. Install with: pip install google-cloud-firestore")
            raise ImportError(
                "Firestore library not available. Install with: pip install google-cloud-firestore")

    def initialize(self) -> None:
        """
        Initialize the connection to Firestore.

        This method establishes a connection to the Firestore database using the
        provided credentials or application default credentials.

        Raises:
            ConnectionError: If connection to Firestore fails
            PermissionError: If the required permissions are not available
        """
        try:
            # Initialize Firestore client
            if self._credentials_path:
                self._client = firestore.Client.from_service_account_json(
                    self._credentials_path)
            else:
                # Use Application Default Credentials
                self._client = firestore.Client(project=self._project_id)

            logger.info("Successfully initialized Firestore memory manager")
        except GoogleAPIError as e:
            logger.error(f"Failed to initialize Firestore client: {e}")
            raise ConnectionError(
                f"Failed to initialize Firestore connection: {e}")
        except PermissionError as e:
            logger.error(f"Insufficient permissions to access Firestore: {e}")
            raise

    def save_record(self, record: MemoryRecord, collection: str) -> None:
        """
        Write the provided MemoryRecord to the specified Firestore collection.

        Args:
            record: The MemoryRecord object to save
            collection: The Firestore collection name to save the record to

        Returns:
            None

        Raises:
            ValueError: If record_id is not provided
            ConnectionError: If Firestore connection fails
            RuntimeError: If any other error occurs during save
        """
        if not self._client:
            raise RuntimeError(
                "Firestore client not initialized. Call initialize() first.")

        if not record.record_id:
            raise ValueError(
                "record_id must be provided for saving to Firestore")

        try:
            # Convert MemoryRecord to dict for Firestore
            record_data = record.dict()

            # Convert datetime to Firestore timestamp
            if record_data.get("timestamp"):
                record_data["timestamp"] = firestore.SERVER_TIMESTAMP

            # Save to Firestore using record_id as document ID
            self._client.collection(collection).document(
                record.record_id).set(record_data)

            logger.info(f"Saved record {record.record_id} to {collection}")
        except GoogleAPIError as e:
            error_msg = f"Failed to save record {record.record_id} to Firestore: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def get_record(self, record_id: str, collection: str) -> MemoryRecord:
        """
        Retrieve a record by its record_id from the specified Firestore collection.

        Args:
            record_id: The ID of the record to retrieve
            collection: The Firestore collection to retrieve from

        Returns:
            A MemoryRecord object with the retrieved data

        Raises:
            ValueError: If the record is not found
            ConnectionError: If Firestore connection fails
            RuntimeError: If any other error occurs during retrieval
        """
        if not self._client:
            raise RuntimeError(
                "Firestore client not initialized. Call initialize() first.")

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

    def query_records(self, filters: dict, collection: str) -> List[MemoryRecord]:
        """
        Retrieve records from Firestore based on provided filters.

        Args:
            filters: Dictionary of field-value pairs to filter by
                    (e.g., {"context": "PayReady", "persona": "Sophia"})
            collection: The Firestore collection to query

        Returns:
            List of MemoryRecord objects matching the filters

        Raises:
            ConnectionError: If Firestore connection fails
            RuntimeError: If any other error occurs during query
        """
        if not self._client:
            raise RuntimeError(
                "Firestore client not initialized. Call initialize() first.")

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
            results = [MemoryRecord(**doc.to_dict()) for doc in docs]

            logger.info(
                f"Queried {collection} with filters {filters}, found {len(results)} records")

            return results
        except GoogleAPIError as e:
            error_msg = f"Failed to query records from Firestore: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
