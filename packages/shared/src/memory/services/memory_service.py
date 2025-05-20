"""
Memory Service for AI Orchestration System.

This module provides a memory service that encapsulates business logic related
to memory operations, following the hexagonal architecture pattern by depending
on the storage port interface rather than concrete implementations.
"""

import logging
from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime, timedelta

from packages.shared.src.models.base_models import MemoryItem, AgentData, PersonaConfig
from packages.shared.src.memory.ports import MemoryStoragePort
from packages.shared.src.memory.exceptions import (
    MemoryException,
    MemoryStorageException,
    MemoryItemNotFound,
    MemoryValidationError,
)
from packages.shared.src.memory.memory_types import MemoryHealth

# Configure logging
logger = logging.getLogger(__name__)


class MemoryService:
    """
    Service for memory-related business logic.

    This class encapsulates business logic related to memory operations,
    using the port interface to interact with storage implementations.
    It follows the hexagonal architecture pattern by depending on the
    abstraction (port) rather than concrete implementations.
    """

    def __init__(self, storage_port: MemoryStoragePort):
        """
        Initialize the memory service.

        Args:
            storage_port: Port for storage operations
        """
        self._storage = storage_port
        self._initialized = False
        logger.debug("MemoryService initialized")

    async def initialize(self) -> None:
        """
        Initialize the memory service.

        Initializes the underlying storage port.
        """
        if not self._initialized:
            await self._storage.initialize()
            self._initialized = True
            logger.info("MemoryService initialization complete")

    async def close(self) -> None:
        """
        Close the memory service.

        Closes the underlying storage port.
        """
        if self._initialized:
            await self._storage.close()
            self._initialized = False
            logger.info("MemoryService closed")

    def _check_initialized(self) -> None:
        """
        Check if the service is initialized.

        Raises:
            MemoryException: If the service is not initialized
        """
        if not self._initialized:
            raise MemoryException("MemoryService is not initialized")

    async def add_memory_item(self, item: MemoryItem) -> str:
        """
        Add a memory item.

        Args:
            item: The memory item to add

        Returns:
            The ID of the added item

        Raises:
            MemoryValidationError: If the item fails validation
            MemoryStorageException: If the storage operation fails
        """
        self._check_initialized()

        # Generate an ID if not provided
        if not item.id:
            item.id = f"mem_{uuid.uuid4().hex}"

        # Set timestamp if not provided
        if not item.timestamp:
            item.timestamp = datetime.utcnow()

        # Business rule: Validate memory item fields
        if not item.user_id:
            raise MemoryValidationError("Memory item must have a user ID")

        if not item.item_type:
            raise MemoryValidationError("Memory item must have a type")

        if not item.text_content and item.item_type == "conversation":
            raise MemoryValidationError(
                "Conversation memory items must have text content"
            )

        # Save to storage
        return await self._storage.save_item(item)

    async def get_memory_item(self, item_id: str) -> MemoryItem:
        """
        Get a memory item by ID.

        Args:
            item_id: The ID of the item to get

        Returns:
            The memory item

        Raises:
            MemoryItemNotFound: If the item is not found
            MemoryStorageException: If the storage operation fails
        """
        self._check_initialized()

        item = await self._storage.retrieve_item(item_id)

        if not item:
            raise MemoryItemNotFound(f"Memory item {item_id} not found")

        return item

    async def get_conversation_history(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 20,
        persona_name: Optional[str] = None,
    ) -> List[MemoryItem]:
        """
        Get conversation history for a user.

        Args:
            user_id: The ID of the user
            session_id: Optional session ID to filter by
            limit: Maximum number of items to return
            persona_name: Optional persona name to filter by

        Returns:
            List of memory items

        Raises:
            MemoryValidationError: If the parameters fail validation
            MemoryStorageException: If the storage operation fails
        """
        self._check_initialized()

        # Business rule: Basic validation
        if not user_id:
            raise MemoryValidationError("User ID is required")

        if limit < 1:
            raise MemoryValidationError("Limit must be positive")

        # Business rule: Apply the maximum limit
        MAX_LIMIT = 100
        if limit > MAX_LIMIT:
            logger.warning(
                f"Limiting conversation history request to {MAX_LIMIT} items (requested {limit})"
            )
            limit = MAX_LIMIT

        # Prepare filters
        filters = {"item_type": "conversation"}

        if session_id:
            filters["session_id"] = session_id

        if persona_name:
            filters["persona_active"] = persona_name

        # Query storage
        return await self._storage.query_items(user_id, filters, limit)

    async def perform_semantic_search(
        self,
        user_id: str,
        query_embedding: List[float],
        persona_context: Optional[PersonaConfig] = None,
        top_k: int = 5,
    ) -> List[MemoryItem]:
        """
        Perform semantic search across memory items.

        Note: This is a higher-level business operation that may require
        specialized storage capabilities. It demonstrates how domain logic
        can be separated from storage concerns.

        Args:
            user_id: The ID of the user
            query_embedding: Query embedding vector
            persona_context: Optional persona context
            top_k: Number of results to return

        Returns:
            List of memory items sorted by relevance

        Raises:
            MemoryValidationError: If the parameters fail validation
            MemoryStorageException: If the storage operation fails
            NotImplementedError: If semantic search is not supported by the storage
        """
        self._check_initialized()

        # Business rule: Basic validation
        if not user_id:
            raise MemoryValidationError("User ID is required")

        if not query_embedding:
            raise MemoryValidationError("Query embedding is required")

        if top_k < 1:
            raise MemoryValidationError("top_k must be positive")

        # Prepare filters for items with embeddings
        filters = {
            # This is a conceptual filter, actual implementation depends on storage
            "embedding": {"exists": True}
        }

        if persona_context:
            filters["persona_active"] = persona_context.name

        # Note: In a real implementation, we would retrieve items with embeddings
        # and compute similarity scores. This requires specialized storage support
        # or implementation in this service.

        # For now, we'll throw a NotImplementedError to indicate that this higher-level
        # business logic is not fully implemented
        raise NotImplementedError(
            "Semantic search not implemented in this version of MemoryService"
        )

    async def add_agent_data(self, data: AgentData) -> str:
        """
        Add agent data.

        Args:
            data: The agent data to add

        Returns:
            The ID of the added data

        Raises:
            MemoryValidationError: If the data fails validation
            MemoryStorageException: If the storage operation fails
        """
        self._check_initialized()

        # Generate an ID if not provided
        if not data.id:
            data.id = f"agent_{uuid.uuid4().hex}"

        # Set timestamp if not provided
        if not data.timestamp:
            data.timestamp = datetime.utcnow()

        # Business rule: Validate agent data fields
        if not data.agent_id:
            raise MemoryValidationError("Agent data must have an agent ID")

        if not data.data_type:
            raise MemoryValidationError("Agent data must have a type")

        # Save to storage
        return await self._storage.save_agent_data(data)

    async def check_duplicate(self, item: MemoryItem) -> bool:
        """
        Check if a memory item is a duplicate.

        This is a business operation that looks for similar content
        to detect and prevent duplicates.

        Args:
            item: The memory item to check

        Returns:
            True if the item is a duplicate, False otherwise

        Raises:
            MemoryStorageException: If the storage operation fails
        """
        self._check_initialized()

        # Business rule: We consider an item a duplicate if:
        # 1. It has the same user_id and item_type
        # 2. It has the same text_content (if it's a conversation item)
        # 3. It was created within the last 5 minutes

        if not item.text_content:
            return False  # Can't check for duplicates without content

        # Get recent items for this user and type
        filters = {
            "item_type": item.item_type,
            # Recent items only (conceptual filter, implementation depends on storage)
            "timestamp": {"start": datetime.utcnow() - timedelta(minutes=5)},
        }

        recent_items = await self._storage.query_items(item.user_id, filters, 20)

        # Check for content similarity
        for existing_item in recent_items:
            if (
                existing_item.text_content == item.text_content
                and existing_item.persona_active == item.persona_active
            ):
                return True

        return False

    async def cleanup_expired_items(self) -> int:
        """
        Remove expired items.

        This is a maintenance operation that should be called periodically.

        Returns:
            Number of items deleted

        Raises:
            MemoryStorageException: If the storage operation fails
        """
        self._check_initialized()

        # Business rule: Remove items that have passed their TTL
        filter_criteria = {
            # Conceptual filter, implementation depends on storage
            "ttl": {"end": datetime.utcnow()}
        }

        return await self._storage.delete_items(filter_criteria)

    async def check_health(self) -> MemoryHealth:
        """
        Check the health of the memory system.

        Returns:
            Health status information
        """
        if not self._initialized:
            return {
                "status": "not_initialized",
                "details": {"message": "MemoryService is not initialized"},
            }

        # Get health from storage
        return await self._storage.check_health()
