"""
Ingestion Worker Module for File Ingestion System.

This module provides the core worker functionality for processing
ingestion tasks from the Pub/Sub queue, including downloading files,
extracting text, generating embeddings, and storing them.
"""

import os
import logging
import json
import asyncio
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import uuid

from packages.ingestion.src.models.ingestion_models import (
    IngestionTask,
    ProcessedFile,
    TextChunk,
    IngestionStatus,
    FileType,
    PubSubMessage,
)
from packages.ingestion.src.storage.firestore_storage import FirestoreStorage
from packages.ingestion.src.storage.gcs_storage import GCSStorage
from packages.ingestion.src.storage.postgres_storage import PostgresStorage
from packages.ingestion.src.storage.pubsub_client import PubSubClient
from packages.ingestion.src.processor.text_extractor import TextExtractor
from packages.ingestion.src.processor.embedding_generator import EmbeddingGenerator
from packages.ingestion.src.config.settings import get_settings

# Configure logging
logger = logging.getLogger(__name__)


class IngestionWorkerError(Exception):
    """Exception for ingestion worker-related errors."""

    pass


class IngestionWorker:
    """
    Ingestion worker implementation.

    This class provides methods for processing ingestion tasks
    from the Pub/Sub queue, including file download, text extraction,
    embedding generation, and storage.
    """

    def __init__(self):
        """Initialize the ingestion worker with required components."""
        self.settings = get_settings()
        self.firestore = FirestoreStorage()
        self.gcs = GCSStorage()
        self.postgres = PostgresStorage()
        self.pubsub = PubSubClient()
        self.extractor = TextExtractor()
        self.embedding_generator = EmbeddingGenerator()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all components."""
        if self._initialized:
            return

        try:
            # Initialize storage components
            await self.firestore.initialize()
            await self.gcs.initialize()
            await self.postgres.initialize()
            await self.pubsub.initialize()
            await self.embedding_generator.initialize()

            self._initialized = True
            logger.info("Ingestion worker initialized")
        except Exception as e:
            logger.error(f"Failed to initialize ingestion worker: {e}")
            raise IngestionWorkerError(f"Failed to initialize ingestion worker: {e}")

    async def close(self) -> None:
        """Close all components."""
        try:
            await self.firestore.close()
            await self.gcs.close()
            await self.postgres.close()
            await self.pubsub.close()

            self._initialized = False
            logger.debug("Ingestion worker closed")
        except Exception as e:
            logger.error(f"Error closing ingestion worker: {e}")

    def _check_initialized(self) -> None:
        """Check if the worker is initialized and raise error if not."""
        if not self._initialized:
            raise IngestionWorkerError("Ingestion worker not initialized")

    async def process_message(self, message: Dict[str, Any]) -> bool:
        """
        Process a Pub/Sub message.

        Args:
            message: The Pub/Sub message to process

        Returns:
            True if the message was processed successfully, False otherwise
        """
        self._check_initialized()

        try:
            # Extract message data
            data = message.get("data", {})
            if not data or not isinstance(data, dict):
                logger.error("Invalid message format, missing or invalid data")
                return False

            # Extract task information
            task_id = data.get("task_id")
            user_id = data.get("user_id")
            session_id = data.get("session_id")
            source_url = data.get("source_url")

            if not task_id or not user_id or not source_url:
                logger.error("Missing required fields in message")
                return False

            # Load task from Firestore
            task = await self.firestore.get_task(task_id)
            if not task:
                # Create task if it doesn't exist
                task = IngestionTask(
                    id=task_id,
                    user_id=user_id,
                    session_id=session_id,
                    source_url=source_url,
                    status=IngestionStatus.PENDING,
                    metadata=data.get("metadata", {}),
                )
                await self.firestore.create_task(task)

            # Process task
            success = await self.process_task(task)

            return success
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return False

    async def process_task(self, task: IngestionTask) -> bool:
        """
        Process an ingestion task.

        Args:
            task: The ingestion task to process

        Returns:
            True if the task was processed successfully, False otherwise
        """
        self._check_initialized()

        try:
            # Update task status to downloading
            await self.firestore.update_task_status(
                task.id, IngestionStatus.DOWNLOADING
            )

            # Download file
            try:
                local_path, filename = await self.gcs.download_from_url(
                    task.source_url, task.id, max_size_mb=self.settings.max_file_size_mb
                )
            except Exception as e:
                logger.error(f"Failed to download file from {task.source_url}: {e}")
                await self.firestore.update_task_status(
                    task.id, IngestionStatus.FAILED, error=f"Download failed: {str(e)}"
                )
                return False

            # Update task status to downloaded
            await self.firestore.update_task_status(task.id, IngestionStatus.DOWNLOADED)

            # Upload raw file to GCS
            try:
                gcs_raw_path = await self.gcs.upload_raw_file(
                    local_path, task.id, filename
                )
            except Exception as e:
                logger.error(f"Failed to upload raw file to GCS: {e}")
                await self.firestore.update_task_status(
                    task.id, IngestionStatus.FAILED, error=f"Upload failed: {str(e)}"
                )
                return False

            # Update task status to processing
            await self.firestore.update_task_status(task.id, IngestionStatus.PROCESSING)

            # Create processed file record
            file_id = str(uuid.uuid4())
            file_record = ProcessedFile(
                id=file_id,
                task_id=task.id,
                user_id=task.user_id,
                original_filename=filename,
                size_bytes=os.path.getsize(local_path),
                status=IngestionStatus.PROCESSING,
                gcs_raw_path=gcs_raw_path,
            )
            await self.firestore.create_file(file_record)

            # Extract text from file
            try:
                text, file_type = await self.extractor.extract_text(local_path)

                # Update file record with detected type
                await self.firestore.update_file(
                    file_id,
                    {"detected_type": file_type, "status": IngestionStatus.PROCESSING},
                )
            except Exception as e:
                logger.error(f"Failed to extract text from file: {e}")
                await self.firestore.update_task_status(
                    task.id,
                    IngestionStatus.FAILED,
                    error=f"Text extraction failed: {str(e)}",
                )
                await self.firestore.update_file(
                    file_id,
                    {
                        "status": IngestionStatus.FAILED,
                        "error": f"Text extraction failed: {str(e)}",
                    },
                )
                return False

            # Upload extracted text to GCS
            try:
                gcs_text_path = await self.gcs.upload_text_content(
                    text, task.id, f"{filename}_extracted"
                )

                # Update file record with text path
                await self.firestore.update_file(
                    file_id, {"gcs_text_path": gcs_text_path}
                )
            except Exception as e:
                logger.error(f"Failed to upload extracted text to GCS: {e}")
                # Continue processing even if text upload fails
                logger.warning("Continuing processing despite text upload failure")

            # Generate chunks from text
            try:
                chunks = await self.extractor.chunk_text(
                    text,
                    chunk_size=self.settings.max_chunk_size,
                    overlap=self.settings.chunk_overlap,
                )
            except Exception as e:
                logger.error(f"Failed to chunk text: {e}")
                await self.firestore.update_task_status(
                    task.id,
                    IngestionStatus.FAILED,
                    error=f"Text chunking failed: {str(e)}",
                )
                await self.firestore.update_file(
                    file_id,
                    {
                        "status": IngestionStatus.FAILED,
                        "error": f"Text chunking failed: {str(e)}",
                    },
                )
                return False

            # Generate embeddings for chunks
            try:
                embeddings = await self.embedding_generator.generate_embeddings_batch(
                    chunks
                )

                if len(embeddings) != len(chunks):
                    raise ValueError(
                        f"Number of embeddings ({len(embeddings)}) "
                        f"doesn't match number of chunks ({len(chunks)})"
                    )
            except Exception as e:
                logger.error(f"Failed to generate embeddings: {e}")
                await self.firestore.update_task_status(
                    task.id,
                    IngestionStatus.FAILED,
                    error=f"Embedding generation failed: {str(e)}",
                )
                await self.firestore.update_file(
                    file_id,
                    {
                        "status": IngestionStatus.FAILED,
                        "error": f"Embedding generation failed: {str(e)}",
                    },
                )
                return False

            # Create and store text chunks with embeddings
            try:
                text_chunks = []
                for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
                    chunk = TextChunk(
                        file_id=file_id,
                        task_id=task.id,
                        user_id=task.user_id,
                        chunk_number=i,
                        text_content=chunk_text,
                        embedding=embedding,
                        metadata={
                            "source_url": str(task.source_url),
                            "filename": filename,
                            "file_type": str(file_type),
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                        },
                    )
                    text_chunks.append(chunk)

                # Store embeddings in batches
                await self.postgres.store_embeddings(text_chunks)
            except Exception as e:
                logger.error(f"Failed to store embeddings: {e}")
                await self.firestore.update_task_status(
                    task.id,
                    IngestionStatus.FAILED,
                    error=f"Embedding storage failed: {str(e)}",
                )
                await self.firestore.update_file(
                    file_id,
                    {
                        "status": IngestionStatus.FAILED,
                        "error": f"Embedding storage failed: {str(e)}",
                    },
                )
                return False

            # Mark file as processed
            await self.firestore.update_file(
                file_id, {"status": IngestionStatus.PROCESSED}
            )

            # Mark task as processed
            await self.firestore.update_task_status(
                task.id,
                IngestionStatus.PROCESSED,
                metadata={
                    "completed_at": datetime.utcnow().isoformat(),
                    "chunks_count": len(chunks),
                    "file_id": file_id,
                },
            )

            # Clean up temporary file
            if os.path.exists(local_path):
                os.unlink(local_path)

            logger.info(
                f"Successfully processed task {task.id}, "
                f"file: {filename}, chunks: {len(chunks)}"
            )

            # Notify user about completion (through chat system)
            # TODO: Add notification mechanism

            return True
        except Exception as e:
            logger.error(f"Error processing task {task.id}: {e}")

            # Update task status to failed
            await self.firestore.update_task_status(
                task.id, IngestionStatus.FAILED, error=f"Processing failed: {str(e)}"
            )

            return False

    async def poll_for_tasks(self, max_messages: int = 10) -> int:
        """
        Poll for ingestion tasks from Pub/Sub.

        Args:
            max_messages: Maximum number of messages to process in one poll

        Returns:
            Number of messages successfully processed
        """
        self._check_initialized()

        # Process messages using the process_message callback
        processed_count = await self.pubsub.process_messages(
            callback=self.process_message, max_messages=max_messages
        )

        return processed_count

    async def run_worker(self, poll_interval: int = 30, max_messages: int = 10) -> None:
        """
        Run the worker in a continuous loop.

        Args:
            poll_interval: Seconds to wait between polling for messages
            max_messages: Maximum number of messages to process in one poll
        """
        self._check_initialized()

        logger.info(f"Starting ingestion worker with poll interval {poll_interval}s")

        try:
            while True:
                try:
                    # Poll for messages
                    processed = await self.poll_for_tasks(max_messages)

                    if processed > 0:
                        logger.info(f"Processed {processed} ingestion tasks")

                    # Wait before next poll
                    await asyncio.sleep(poll_interval)
                except Exception as e:
                    logger.error(f"Error in worker poll cycle: {e}")
                    # Continue running despite errors
                    await asyncio.sleep(poll_interval)
        except asyncio.CancelledError:
            logger.info("Worker task cancelled")
        except Exception as e:
            logger.error(f"Fatal error in worker: {e}")
            raise
        finally:
            await self.close()

    @staticmethod
    async def create_worker() -> "IngestionWorker":
        """
        Create and initialize a new worker instance.

        Returns:
            Initialized ingestion worker
        """
        worker = IngestionWorker()
        await worker.initialize()
        return worker
