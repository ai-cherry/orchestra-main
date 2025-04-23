"""
Memory Service for AI Orchestration System.

This module provides a central point of access to the memory management system,
abstracting the underlying implementation and providing dependency injection.
"""

import logging
import os
from datetime import datetime
from functools import lru_cache
from typing import Dict, List, Optional, Any

from core.orchestrator.src.services.event_bus import get_event_bus
# Import the settings instance directly
from core.orchestrator.src.config.config import settings
from packages.shared.src.memory.memory_manager import MemoryManager
from packages.shared.src.models.base_models import AgentData, MemoryItem, PersonaConfig
from future.firestore_memory_manager import FirestoreMemoryManager
# Removed incorrect import: from packages.shared.src.storage.enhanced_firestore_stub import EnhancedFirestoreManager

# Configure logging
logger = logging.getLogger(__name__)


class MemoryService:
    """
    Service for memory operations in the orchestration system.

    This class wraps the MemoryManager interface to provide additional
    orchestration-specific functionality, such as event publishing
    and persona-aware operations.
    """

    def __init__(self, memory_manager: MemoryManager):
        """
        Initialize the memory service with a memory manager.

        Args:
            memory_manager: The memory manager implementation to use
        """
        self._memory_manager = memory_manager
        self._event_bus = get_event_bus()
        logger.info(
            f"MemoryService initialized with {memory_manager.__class__.__name__}"
        )

    def initialize(self):
        """Initialize the underlying memory manager."""
        self._memory_manager.initialize()

    def close(self):
        """Close the underlying memory manager."""
        self._memory_manager.close()

    def add_memory_item(self, item: MemoryItem) -> str:
        """
        Add a memory item and publish an event.

        Args:
            item: The memory item to add

        Returns:
            The ID of the added item

        Raises:
            ValidationError: If the item fails validation
            StorageError: If the storage operation fails
        """
        # First store the item - this is the critical operation
        try:
            item_id = self._memory_manager.add_memory_item(item)
        except Exception as e:
            logger.error(f"Failed to add memory item: {e}")
            # Re-raise to notify caller
            raise

        # Then try to publish the event, but don't let event failures affect the main flow
        try:
            self._event_bus.publish(
                "memory_item_added",
                {
                    "item_id": item_id,
                    "item_type": item.item_type,
                    "user_id": item.user_id,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to publish memory_item_added event: {e}")
            # We don't re-raise here since the primary operation (storing the item) succeeded

        return item_id

    def get_conversation_history(
        self,
        user_id: str,
        persona_name: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[MemoryItem]:
        """
        Get conversation history, optionally filtered by persona.

        Args:
            user_id: The user ID to get history for
            persona_name: Optional persona name to filter by
            session_id: Optional session ID to filter by
            limit: Maximum number of items to retrieve

        Returns:
            List of conversation memory items
        """
        # Create filter if needed
        filters = None
        if persona_name:
            filters = {"persona_active": persona_name}

        # Get conversation history
        items = self._memory_manager.get_conversation_history(
            user_id=user_id, session_id=session_id, limit=limit, filters=filters
        )

        return items

    async def add_memory_item_async(self, item: MemoryItem) -> str:
        """
        Add a memory item and publish an event asynchronously.

        This is the async variant of add_memory_item, suitable for
        use with asynchronous handlers and flows.

        Args:
            item: The memory item to add

        Returns:
            The ID of the added item

        Raises:
            ValidationError: If the item fails validation
            StorageError: If the storage operation fails
        """
        # First store the item - this is the critical operation
        try:
            item_id = self._memory_manager.add_memory_item(item)
        except Exception as e:
            logger.error(f"Failed to add memory item asynchronously: {e}")
            # Re-raise to notify caller
            raise

        # Then try to publish the event asynchronously
        try:
            await self._event_bus.publish_async(
                "memory_item_added",
                {
                    "item_id": item_id,
                    "item_type": item.item_type,
                    "user_id": item.user_id,
                    "async": True,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to publish async memory_item_added event: {e}")
            # We don't re-raise here since the primary operation (storing the item) succeeded

        return item_id

    def semantic_search(
        self,
        user_id: str,
        query_embedding: List[float],
        persona_context: Optional[PersonaConfig] = None,
        top_k: int = 5,
    ) -> List[MemoryItem]:
        """
        Perform semantic search with tracking.

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
        # Perform search - this is the critical operation
        try:
            results = self._memory_manager.semantic_search(
                user_id=user_id,
                query_embedding=query_embedding,
                persona_context=persona_context,
                top_k=top_k,
            )
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            # Re-raise since this is the primary operation
            raise

        # Publish event, but don't let event failures affect the main flow
        if results:
            try:
                self._event_bus.publish(
                    "semantic_search_performed",
                    {
                        "user_id": user_id,
                        "results_count": len(results),
                        "persona_id": persona_context.name if persona_context else None,
                    },
                )
            except Exception as e:
                logger.warning(
                    f"Failed to publish semantic_search_performed event: {e}"
                )
                # We don't re-raise here since the primary operation (search) succeeded

        return results

    def add_raw_agent_data(self, data: AgentData) -> str:
        """
        Process raw agent data.

        Args:
            data: The agent data to process

        Returns:
            The ID of the processed data
        """
        return self._memory_manager.add_raw_agent_data(data)

    def cleanup_expired_items(self) -> int:
        """
        Remove expired items and report count.

        Returns:
            Number of items removed

        Raises:
            StorageError: If the cleanup operation fails
        """
        try:
            count = self._memory_manager.cleanup_expired_items()
        except Exception as e:
            logger.error(f"Failed to cleanup expired items: {e}")
            # Re-raise since this is the primary operation
            raise

        # Publish event if items were removed, but don't let event failures affect the main flow
        if count > 0:
            try:
                self._event_bus.publish(
                    "expired_items_cleaned",
                    {"count": count, "timestamp": datetime.utcnow().isoformat()},
                )
            except Exception as e:
                logger.warning(f"Failed to publish expired_items_cleaned event: {e}")
                # We don't re-raise here since the primary operation (cleanup) succeeded

        return count

    def get_memory_manager(self) -> MemoryManager:
        """
        Get the underlying memory manager.

        This method provides direct access to the memory manager
        for operations not covered by the service.

        Returns:
            The memory manager instance
        """
        return self._memory_manager


@lru_cache()
def get_memory_manager() -> MemoryManager:
    """
    Get a configured memory manager instance.

    This function provides dependency injection for the memory manager,
    creating the appropriate implementation based on configuration.
    It uses lru_cache to ensure only one instance is created.

    Returns:
        A configured memory manager instance
    """
    # Access the global settings instance directly
    # settings = get_settings() # Removed this line

    # Determine which implementation to use
    # Removed conditional logic for EnhancedFirestoreManager
    # if settings.USE_ENHANCED_MEMORY and EnhancedFirestoreManager is not None:
    #     logger.info("Using EnhancedFirestoreManager")
    #
    #     # Use the enhanced implementation with batched writes
    #     memory_manager = EnhancedFirestoreManager(
    #         storage_path=settings.MEMORY_STORAGE_PATH,
    #         auto_save=True,
    #         save_interval=settings.MEMORY_BATCH_SIZE,
    #     )
    # else:
    logger.info("Using FirestoreMemoryManager")

    # Use the basic implementation
    memory_manager = FirestoreMemoryManager(
        storage_path=settings.MEMORY_STORAGE_PATH
    )

    # Initialize the manager
    memory_manager.initialize()

    return memory_manager


@lru_cache()
def get_memory_service() -> MemoryService:
    """
    Get a configured memory service instance.

    This function provides dependency injection for the memory service,
    creating an instance with the appropriate memory manager.
    It uses lru_cache to ensure only one instance is created.

    Returns:
        A configured memory service instance
    """
    memory_manager = get_memory_manager()
    memory_service = MemoryService(memory_manager)

    return memory_service
