"""
Firestore Storage for File Ingestion System.

This module provides Firestore-backed storage for ingestion tasks and file metadata.
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, cast

from google.cloud import firestore
from google.cloud.firestore import AsyncClient
from google.api_core.exceptions import GoogleAPIError

from packages.ingestion.src.models.ingestion_models import (
    IngestionTask,
    ProcessedFile,
    IngestionStatus,
)
from packages.ingestion.src.config.settings import get_settings

# Configure logging
logger = logging.getLogger(__name__)


class FirestoreStorageError(Exception):
    """Exception for Firestore storage-related errors."""

    pass


class FirestoreStorage:
    """
    Firestore storage implementation for ingestion tasks and file metadata.

    This class provides methods for creating, updating, and retrieving
    ingestion tasks and processed file records in Firestore.
    """

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize the Firestore storage.

        Args:
            project_id: Optional Google Cloud project ID. If not provided,
                      will be read from settings or environment.
        """
        settings = get_settings()
        self.project_id = project_id or settings.firestore.project_id
        self.tasks_collection = settings.firestore.ingestion_tasks_collection
        self.files_collection = settings.firestore.processed_files_collection
        self._client = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the Firestore client."""
        if self._initialized:
            return

        try:
            self._client = firestore.AsyncClient(project=self.project_id)
            self._initialized = True
            logger.info("Firestore storage initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore client: {e}")
            raise FirestoreStorageError(f"Failed to initialize Firestore: {e}")

    async def close(self) -> None:
        """Close the Firestore client."""
        if hasattr(self._client, "close") and callable(self._client.close):
            try:
                await self._client.close()
            except Exception as e:
                logger.warning(f"Error closing Firestore client: {e}")

        self._client = None
        self._initialized = False
        logger.debug("Firestore client closed")

    def _check_initialized(self) -> None:
        """Check if the client is initialized and raise error if not."""
        if not self._initialized or not self._client:
            raise FirestoreStorageError("Firestore client not initialized")

    async def create_task(self, task: IngestionTask) -> str:
        """
        Create a new ingestion task in Firestore.

        Args:
            task: The ingestion task to create

        Returns:
            The ID of the created task

        Raises:
            FirestoreStorageError: If creation fails
        """
        self._check_initialized()

        try:
            # Convert to dict for Firestore
            task_data = task.dict()

            # Store in Firestore
            await self._client.collection(self.tasks_collection).document(task.id).set(
                task_data
            )

            logger.debug(f"Created ingestion task {task.id} for user {task.user_id}")
            return task.id
        except Exception as e:
            error_msg = f"Failed to create ingestion task in Firestore: {e}"
            logger.error(error_msg)
            raise FirestoreStorageError(error_msg)

    async def update_task_status(
        self,
        task_id: str,
        status: IngestionStatus,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Update the status of an ingestion task.

        Args:
            task_id: The ID of the task to update
            status: The new status
            error: Optional error message (for failed tasks)
            metadata: Optional metadata to update or add

        Raises:
            FirestoreStorageError: If update fails
        """
        self._check_initialized()

        try:
            # Create update data
            update_data = {"status": status, "updated_at": datetime.utcnow()}

            if error:
                update_data["error"] = error

            if metadata:
                update_data["metadata"] = firestore.firestore.ArrayUnion([metadata])

            # Update the document
            await self._client.collection(self.tasks_collection).document(
                task_id
            ).update(update_data)

            logger.debug(f"Updated ingestion task {task_id} status to {status}")
        except Exception as e:
            error_msg = f"Failed to update ingestion task status in Firestore: {e}"
            logger.error(error_msg)
            raise FirestoreStorageError(error_msg)

    async def get_task(self, task_id: str) -> Optional[IngestionTask]:
        """
        Get an ingestion task by ID.

        Args:
            task_id: The ID of the task to retrieve

        Returns:
            The ingestion task if found, None otherwise

        Raises:
            FirestoreStorageError: If retrieval fails
        """
        self._check_initialized()

        try:
            # Get document from Firestore
            doc = (
                await self._client.collection(self.tasks_collection)
                .document(task_id)
                .get()
            )

            if not doc.exists:
                logger.debug(f"Ingestion task {task_id} not found")
                return None

            # Convert to IngestionTask
            task_data = doc.to_dict()
            return IngestionTask(**task_data)
        except Exception as e:
            error_msg = f"Failed to get ingestion task from Firestore: {e}"
            logger.error(error_msg)
            raise FirestoreStorageError(error_msg)

    async def list_tasks(
        self,
        user_id: Optional[str] = None,
        status: Optional[IngestionStatus] = None,
        limit: int = 20,
    ) -> List[IngestionTask]:
        """
        List ingestion tasks with optional filters.

        Args:
            user_id: Optional user ID to filter by
            status: Optional status to filter by
            limit: Maximum number of tasks to return

        Returns:
            List of ingestion tasks

        Raises:
            FirestoreStorageError: If retrieval fails
        """
        self._check_initialized()

        try:
            # Start with base query
            query = self._client.collection(self.tasks_collection)

            # Apply filters if provided
            if user_id:
                query = query.where("user_id", "==", user_id)

            if status:
                query = query.where("status", "==", status)

            # Order by created_at (descending) and limit results
            query = query.order_by(
                "created_at", direction=firestore.Query.DESCENDING
            ).limit(limit)

            # Execute query
            docs = await query.get()

            # Convert to IngestionTask objects
            tasks = []
            for doc in docs:
                try:
                    task_data = doc.to_dict()
                    tasks.append(IngestionTask(**task_data))
                except Exception as e:
                    logger.warning(f"Error parsing ingestion task: {e}")
                    continue

            return tasks
        except Exception as e:
            error_msg = f"Failed to list ingestion tasks from Firestore: {e}"
            logger.error(error_msg)
            raise FirestoreStorageError(error_msg)

    async def create_file(self, file: ProcessedFile) -> str:
        """
        Create a new processed file record in Firestore.

        Args:
            file: The processed file to create

        Returns:
            The ID of the created file record

        Raises:
            FirestoreStorageError: If creation fails
        """
        self._check_initialized()

        try:
            # Convert to dict for Firestore
            file_data = file.dict()

            # Store in Firestore
            await self._client.collection(self.files_collection).document(file.id).set(
                file_data
            )

            logger.debug(
                f"Created processed file record {file.id} for task {file.task_id}"
            )
            return file.id
        except Exception as e:
            error_msg = f"Failed to create processed file record in Firestore: {e}"
            logger.error(error_msg)
            raise FirestoreStorageError(error_msg)

    async def update_file(self, file_id: str, updates: Dict[str, Any]) -> None:
        """
        Update a processed file record.

        Args:
            file_id: The ID of the file record to update
            updates: Dictionary of fields to update

        Raises:
            FirestoreStorageError: If update fails
        """
        self._check_initialized()

        try:
            # Add updated_at timestamp
            updates["updated_at"] = datetime.utcnow()

            # Update the document
            await self._client.collection(self.files_collection).document(
                file_id
            ).update(updates)

            logger.debug(f"Updated processed file record {file_id}")
        except Exception as e:
            error_msg = f"Failed to update processed file record in Firestore: {e}"
            logger.error(error_msg)
            raise FirestoreStorageError(error_msg)

    async def get_file(self, file_id: str) -> Optional[ProcessedFile]:
        """
        Get a processed file record by ID.

        Args:
            file_id: The ID of the file record to retrieve

        Returns:
            The processed file record if found, None otherwise

        Raises:
            FirestoreStorageError: If retrieval fails
        """
        self._check_initialized()

        try:
            # Get document from Firestore
            doc = (
                await self._client.collection(self.files_collection)
                .document(file_id)
                .get()
            )

            if not doc.exists:
                logger.debug(f"Processed file record {file_id} not found")
                return None

            # Convert to ProcessedFile
            file_data = doc.to_dict()
            return ProcessedFile(**file_data)
        except Exception as e:
            error_msg = f"Failed to get processed file record from Firestore: {e}"
            logger.error(error_msg)
            raise FirestoreStorageError(error_msg)

    async def list_files_for_task(self, task_id: str) -> List[ProcessedFile]:
        """
        List files associated with an ingestion task.

        Args:
            task_id: The ID of the ingestion task

        Returns:
            List of processed file records

        Raises:
            FirestoreStorageError: If retrieval fails
        """
        self._check_initialized()

        try:
            # Query for files with matching task_id
            query = self._client.collection(self.files_collection).where(
                "task_id", "==", task_id
            )

            # Execute query
            docs = await query.get()

            # Convert to ProcessedFile objects
            files = []
            for doc in docs:
                try:
                    file_data = doc.to_dict()
                    files.append(ProcessedFile(**file_data))
                except Exception as e:
                    logger.warning(f"Error parsing processed file record: {e}")
                    continue

            return files
        except Exception as e:
            error_msg = f"Failed to list processed file records from Firestore: {e}"
            logger.error(error_msg)
            raise FirestoreStorageError(error_msg)
