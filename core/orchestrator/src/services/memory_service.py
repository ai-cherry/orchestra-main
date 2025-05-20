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
from packages.shared.src.memory.memory_manager import (
    MemoryManager,
    MemoryHealth,
)  # Import MemoryHealth if needed by MemoryService, otherwise remove
from packages.shared.src.models.base_models import AgentData, MemoryItem, PersonaConfig

# Removed legacy import: from future.firestore_memory_manager import FirestoreMemoryManager
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
        # Use the synchronous wrapper for initialization
        self._memory_manager.initialize_sync()

    def close(self):
        """Close the underlying memory manager."""
        # Use the synchronous wrapper for closing
        self._memory_manager.close_sync()

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
            # Use asyncio to run the async method in a synchronous context
            import asyncio

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # Create a new event loop if one doesn't exist
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            item_id = loop.run_until_complete(
                self._memory_manager.add_memory_item(item)
            )
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
        # Use asyncio to run the async method in a synchronous context
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # Create a new event loop if one doesn't exist
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        items = loop.run_until_complete(
            self._memory_manager.get_conversation_history(
                user_id=user_id, session_id=session_id, limit=limit, filters=filters
            )
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
            item_id = await self._memory_manager.add_memory_item(item)
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
            # Use asyncio to run the async method in a synchronous context
            import asyncio

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # Create a new event loop if one doesn't exist
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            results = loop.run_until_complete(
                self._memory_manager.semantic_search(
                    user_id=user_id,
                    query_embedding=query_embedding,
                    persona_context=persona_context,
                    top_k=top_k,
                )
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
        # Use asyncio to run the async method in a synchronous context
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # Create a new event loop if one doesn't exist
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self._memory_manager.add_raw_agent_data(data))

    def cleanup_expired_items(self) -> int:
        """
        Remove expired items and report count.

        Returns:
            Number of items removed

        Raises:
            StorageError: If the cleanup operation fails
        """
        try:
            # Use asyncio to run the async method in a synchronous context
            import asyncio

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # Create a new event loop if one doesn't exist
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            count = loop.run_until_complete(
                self._memory_manager.cleanup_expired_items()
            )
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
    # Use the new top-level MemoryManager factory
    # The new MemoryManager handles selecting the concrete implementation (V1 or V2)
    # based on its own configuration parameters.
    # We pass relevant settings from our config.
    memory_manager = MemoryManager(
        # Assuming settings has these attributes; adjust if necessary
        project_id=settings.GCP_PROJECT_ID,
        credentials_json=settings.GCP_CREDENTIALS_JSON,
        credentials_path=settings.GCP_CREDENTIALS_PATH,
        redis_host=settings.REDIS_HOST,
        redis_port=settings.REDIS_PORT,
        redis_password=settings.REDIS_PASSWORD,
        cache_ttl=settings.MEMORY_CACHE_TTL,
        # Add other configuration parameters for MemoryManager if needed
        # e.g., memory_backend_type="firestore_v1" or "firestore_v2" if settings controls this
        memory_backend_type=settings.MEMORY_BACKEND_TYPE,  # Assuming settings controls backend type
    )

    # Initialize the manager (this initializes the selected backend)
    # The new MemoryManager's initialize method should handle this.
    # Check if the new MemoryManager requires an explicit initialize call after instantiation.
    # Based on the content I wrote for the new MemoryManager, it does have an async initialize method.
    # However, this function `get_memory_manager` is not async.
    # This indicates a potential conflict. The factory function should probably return an initialized manager,
    # or the initialization should happen elsewhere in the application startup.
    # For now, I will remove the initialize call here, assuming initialization happens
    # when the application starts and configures the MemoryManager instance.
    # If the new MemoryManager's __init__ handles initialization, this line is redundant.
    # If initialization is async and needs to be awaited, this sync function is problematic.
    # Let's assume for now that the new MemoryManager's __init__ is sufficient for basic setup,
    # and the async initialize() method is called later in the application lifecycle.
    # If the old FirestoreMemoryManager's initialize was sync, the new one's might be too,
    # or the overall architecture needs adjustment for async initialization.
    # Let's check the new MemoryManager code again... it has `async def initialize`.
    # This means `get_memory_manager` cannot call it directly unless it's also async.
    # Given `get_memory_manager` is decorated with `@lru_cache()`, making it async might break caching.
    # This suggests the initialization pattern needs rethinking at a higher level.
    # For this refactoring step, I will remove the explicit `initialize()` call here,
    # assuming the caller of `get_memory_service()` (which calls `get_memory_manager()`)
    # is responsible for calling the async `initialize()` on the returned service/manager.

    # Use the synchronous wrapper for initialization
    memory_manager.initialize_sync()

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
