"""
Ingestion API Module for File Ingestion System.

This module provides API endpoints and utilities for creating and managing
ingestion tasks through the chat interface.
"""

import re
import logging
import uuid
from typing import Dict, List, Optional, Any, Union, Tuple, Pattern
from datetime import datetime

from fastapi import HTTPException, Request

from packages.ingestion.src.models.ingestion_models import (
    IngestionTask,
    IngestionStatus,
    PubSubMessage,
    IngestionResult,
)
from packages.ingestion.src.storage.firestore_storage import FirestoreStorage
from packages.ingestion.src.storage.pubsub_client import PubSubClient
from packages.ingestion.src.config.settings import get_settings

# Configure logging
logger = logging.getLogger(__name__)


class IngestionAPIError(Exception):
    """Exception for ingestion API-related errors."""

    pass


class IngestionAPI:
    """
    Ingestion API implementation.

    This class provides methods for creating and managing ingestion tasks
    through the chat interface.
    """

    # Regular expression pattern for ingestion commands
    INGESTION_PATTERN: Pattern = re.compile(
        r"(?:please\s+)?"  # Optional "please"
        r"(?:ingest|process|import)\s+"  # Command verbs
        r"(?:this\s+)?"  # Optional "this"
        r"(?:file|document|pdf|doc)?\s*"  # Optional file type
        r"(?:from\s+)?"  # Optional "from"
        r"(https?://\S+)"  # URL (capture group 1)
        r"(?:\s+.*)?",  # Optional additional text
        re.IGNORECASE,
    )

    def __init__(self):
        """Initialize the ingestion API with required components."""
        self.settings = get_settings()
        self.firestore = FirestoreStorage()
        self.pubsub = PubSubClient()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the API components."""
        if self._initialized:
            return

        try:
            # Initialize storage components
            await self.firestore.initialize()
            await self.pubsub.initialize()

            self._initialized = True
            logger.info("Ingestion API initialized")
        except Exception as e:
            logger.error(f"Failed to initialize ingestion API: {e}")
            raise IngestionAPIError(f"Failed to initialize ingestion API: {e}")

    async def close(self) -> None:
        """Close the API components."""
        try:
            await self.firestore.close()
            await self.pubsub.close()

            self._initialized = False
            logger.debug("Ingestion API closed")
        except Exception as e:
            logger.error(f"Error closing ingestion API: {e}")

    def _check_initialized(self) -> None:
        """Check if the API is initialized and raise error if not."""
        if not self._initialized:
            raise IngestionAPIError("Ingestion API not initialized")

    @classmethod
    def extract_url_from_message(cls, message: str) -> Optional[str]:
        """
        Extract URL from an ingestion command message.

        Args:
            message: The message to extract URL from

        Returns:
            Extracted URL or None if no URL found
        """
        match = cls.INGESTION_PATTERN.search(message)
        if match:
            return match.group(1)
        return None

    async def create_ingestion_task(
        self,
        url: str,
        user_id: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, IngestionResult]:
        """
        Create a new ingestion task and publish it to Pub/Sub.

        Args:
            url: URL of the file to ingest
            user_id: ID of the user creating the task
            session_id: Optional session ID
            metadata: Optional metadata for the task

        Returns:
            Tuple of (task_id, ingestion_result)

        Raises:
            IngestionAPIError: If task creation fails
        """
        self._check_initialized()

        try:
            # Create task ID
            task_id = str(uuid.uuid4())

            # Create task record
            task = IngestionTask(
                id=task_id,
                user_id=user_id,
                session_id=session_id,
                source_url=url,
                status=IngestionStatus.PENDING,
                metadata=metadata or {},
            )

            # Store task in Firestore
            await self.firestore.create_task(task)

            # Create Pub/Sub message
            pubsub_message = PubSubMessage(
                task_id=task_id,
                user_id=user_id,
                session_id=session_id,
                source_url=url,
                metadata=metadata or {},
            )

            # Publish to Pub/Sub
            await self.pubsub.publish_task(pubsub_message)

            # Create result
            result = IngestionResult(
                task_id=task_id,
                status=IngestionStatus.PENDING,
                message=f"Started ingesting file from {url}",
                details={
                    "source_url": url,
                    "user_id": user_id,
                    "session_id": session_id,
                },
                created_at=task.created_at,
                updated_at=task.updated_at,
            )

            logger.info(f"Created ingestion task {task_id} for URL {url}")
            return task_id, result
        except Exception as e:
            logger.error(f"Failed to create ingestion task for URL {url}: {e}")
            raise IngestionAPIError(f"Failed to create ingestion task: {e}")

    async def get_task_status(self, task_id: str) -> IngestionResult:
        """
        Get the status of an ingestion task.

        Args:
            task_id: ID of the task to get status for

        Returns:
            Ingestion result with status information

        Raises:
            IngestionAPIError: If status retrieval fails
        """
        self._check_initialized()

        try:
            # Get task from Firestore
            task = await self.firestore.get_task(task_id)

            if not task:
                raise IngestionAPIError(f"Task {task_id} not found")

            # Get associated files
            files = await self.firestore.list_files_for_task(task_id)

            # Create details with file information
            details = {
                "source_url": str(task.source_url),
                "user_id": task.user_id,
                "session_id": task.session_id,
                "files": [
                    {
                        "id": file.id,
                        "filename": file.original_filename,
                        "size_bytes": file.size_bytes,
                        "detected_type": str(file.detected_type),
                        "status": str(file.status),
                    }
                    for file in files
                ],
            }

            # Add error if present
            if task.error:
                details["error"] = task.error

            # Create status message based on status
            message = self._create_status_message(task.status, task.error, len(files))

            # Create result
            result = IngestionResult(
                task_id=task_id,
                status=task.status,
                message=message,
                details=details,
                created_at=task.created_at,
                updated_at=task.updated_at,
            )

            return result
        except IngestionAPIError:
            raise
        except Exception as e:
            logger.error(f"Failed to get task status for {task_id}: {e}")
            raise IngestionAPIError(f"Failed to get task status: {e}")

    async def list_user_tasks(
        self, user_id: str, limit: int = 10, status: Optional[IngestionStatus] = None
    ) -> List[IngestionResult]:
        """
        List ingestion tasks for a user.

        Args:
            user_id: ID of the user
            limit: Maximum number of tasks to return
            status: Optional status to filter by

        Returns:
            List of ingestion results

        Raises:
            IngestionAPIError: If task listing fails
        """
        self._check_initialized()

        try:
            # List tasks from Firestore
            tasks = await self.firestore.list_tasks(user_id, status, limit)

            # Convert to results
            results = []
            for task in tasks:
                # Create basic message
                message = self._create_status_message(task.status, task.error)

                # Create result
                result = IngestionResult(
                    task_id=task.id,
                    status=task.status,
                    message=message,
                    details={
                        "source_url": str(task.source_url),
                        "user_id": task.user_id,
                        "session_id": task.session_id,
                    },
                    created_at=task.created_at,
                    updated_at=task.updated_at,
                )

                results.append(result)

            return results
        except Exception as e:
            logger.error(f"Failed to list tasks for user {user_id}: {e}")
            raise IngestionAPIError(f"Failed to list tasks: {e}")

    def _create_status_message(
        self, status: IngestionStatus, error: Optional[str] = None, file_count: int = 0
    ) -> str:
        """
        Create a status message based on status and error.

        Args:
            status: The ingestion status
            error: Optional error message
            file_count: Number of associated files

        Returns:
            Status message
        """
        if status == IngestionStatus.PENDING:
            return "Ingestion task is pending processing."
        elif status == IngestionStatus.DOWNLOADING:
            return "Downloading file..."
        elif status == IngestionStatus.DOWNLOADED:
            return "File downloaded, preparing for processing."
        elif status == IngestionStatus.PROCESSING:
            return "Processing file content..."
        elif status == IngestionStatus.PROCESSED:
            if file_count == 1:
                return "File has been successfully processed and is now searchable."
            else:
                return f"{file_count} files have been successfully processed and are now searchable."
        elif status == IngestionStatus.FAILED:
            if error:
                return f"Ingestion failed: {error}"
            else:
                return "Ingestion failed due to an unknown error."
        else:
            return f"Ingestion status: {status}"

    async def process_chat_command(
        self, message: str, user_id: str, session_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Process an ingestion command from a chat message.

        This method extracts URLs from messages and creates ingestion tasks
        if the message contains an ingestion command.

        Args:
            message: The chat message
            user_id: ID of the user
            session_id: Optional session ID

        Returns:
            Response data if message is an ingestion command, None otherwise
        """
        self._check_initialized()

        # Extract URL from message
        url = self.extract_url_from_message(message)

        if not url:
            # Not an ingestion command
            return None

        try:
            # Create ingestion task
            task_id, result = await self.create_ingestion_task(
                url=url, user_id=user_id, session_id=session_id
            )

            # Create response data
            response_data = {
                "type": "ingestion_task",
                "task_id": task_id,
                "status": result.status,
                "message": result.message,
                "details": result.details,
            }

            return response_data
        except Exception as e:
            logger.error(f"Error processing ingestion command: {e}")

            # Return error response
            return {
                "type": "ingestion_error",
                "message": f"Failed to process ingestion command: {str(e)}",
                "details": {"url": url},
            }

    @staticmethod
    async def create_api() -> "IngestionAPI":
        """
        Create and initialize a new API instance.

        Returns:
            Initialized ingestion API
        """
        api = IngestionAPI()
        await api.initialize()
        return api
