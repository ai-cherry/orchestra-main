"""
Memory Manager Interface for AI Orchestration System.

# AI-CONTEXT: This file defines the core memory manager interface used throughout the system.
# AI-CONTEXT: See MEMORY_CONTEXT.md in this directory for architectural details.
# AI-CONTEXT: The memory system stores conversation history, user preferences, and other contextual information.
# AI-CONTEXT: Implementations include InMemoryMemoryManagerStub and PatrickMemoryManager.

This module provides the abstract base class for memory managers,
defining the interface that all concrete implementations must follow.
Memory managers are responsible for storing and retrieving conversation
history, user preferences, and other contextual information.
"""

from abc import ABC, abstractmethod
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional, Union, TypedDict

from packages.shared.src.models.base_models import AgentData, MemoryItem, PersonaConfig


# Set up logger
logger = logging.getLogger(__name__)


# Type definition for memory health status
class MemoryHealth(TypedDict, total=False):
    """Type definition for memory system health status."""

    status: str  # 'healthy', 'degraded', or 'unhealthy'
    firestore: bool  # Firestore connection status
    redis: bool  # Redis connection status
    error_count: int  # Number of recent errors
    last_error: Optional[str]  # Last error message or timestamp
    details: Dict[str, Any]  # Additional details about the health status


class MemoryManager(ABC):
    """
    Abstract base class for memory management implementations.

    This class defines the contract that all memory manager implementations
    must adhere to, ensuring consistent behavior across different storage backends.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the memory manager.

        This method should set up any necessary connections, create
        resources, or perform other initialization tasks.

        Raises:
            ConnectionError: If connection to the storage backend fails
            PermissionError: If the required permissions are not available
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Close the memory manager and release resources.

        This method should clean up any resources used by the memory manager,
        such as database connections, file handles, etc.
        """
        pass

    @abstractmethod
    async def add_memory_item(self, item: MemoryItem) -> str:
        """
        Add a memory item to storage.

        Args:
            item: The memory item to store

        Returns:
            The ID of the created memory item

        Raises:
            ValidationError: If the item fails validation
            StorageError: If the storage operation fails
        """
        pass

    @abstractmethod
    async def get_memory_item(self, item_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a specific memory item by ID.

        Args:
            item_id: The ID of the item to retrieve

        Returns:
            The memory item if found, None otherwise

        Raises:
            StorageError: If the retrieval operation fails
        """
        pass

    @abstractmethod
    async def get_conversation_history(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[MemoryItem]:
        """
        Retrieve conversation history for a user.

        Args:
            user_id: The user ID to get history for
            session_id: Optional session ID to filter by
            limit: Maximum number of items to retrieve
            filters: Optional filters to apply

        Returns:
            List of memory items representing the conversation history

        Raises:
            StorageError: If the retrieval operation fails
        """
        pass

    @abstractmethod
    async def semantic_search(
        self,
        user_id: str,
        query_embedding: List[float],
        persona_context: Optional[PersonaConfig] = None,
        top_k: int = 5,
    ) -> List[MemoryItem]:
        """
        Perform semantic search using vector embeddings.

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
        pass

    @abstractmethod
    async def add_raw_agent_data(self, data: AgentData) -> str:
        """
        Store raw agent data.

        Args:
            data: The agent data to store

        Returns:
            The ID of the stored data

        Raises:
            ValidationError: If the data fails validation
            StorageError: If the storage operation fails
        """
        pass

    @abstractmethod
    async def check_duplicate(self, item: MemoryItem) -> bool:
        """
        Check if a memory item already exists in storage.

        Args:
            item: The memory item to check for duplicates

        Returns:
            True if a duplicate exists, False otherwise

        Raises:
            StorageError: If the check operation fails
        """
        pass

    @abstractmethod
    async def cleanup_expired_items(self) -> int:
        """
        Remove expired items from storage.

        Returns:
            Number of items removed

        Raises:
            StorageError: If the cleanup operation fails
        """
        pass

    @abstractmethod
    async def health_check(self) -> MemoryHealth:
        """
        Check the health of the memory system.

        This method should perform checks on the underlying storage systems
        and return a detailed health status report.

        Returns:
            MemoryHealth: A dictionary with health status information

        Raises:
            Exception: If the health check itself fails
        """
        pass

# Import the InMemoryMemoryManagerStub implementation and rename it for compatibility
from packages.shared.src.memory.stubs import InMemoryMemoryManagerStub as InMemoryMemoryManager

# Also import concrete implementations for convenience
try:
    from packages.shared.src.memory.concrete_memory_manager import ConcreteMemoryManager
except ImportError:
    logger.debug("ConcreteMemoryManager not available, skipping import.")

# Import Firestore adapter if available
try:
    from packages.shared.src.memory.firestore_adapter import FirestoreMemoryAdapter
except ImportError:
    logger.debug("FirestoreMemoryAdapter not available, skipping import.")
