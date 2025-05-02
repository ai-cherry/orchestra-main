"""
Ports for the Memory System in the Hexagonal Architecture.

This module defines the interfaces (ports) for the memory system,
following the hexagonal architecture pattern to clearly separate
domain logic from infrastructure concerns.
"""

import abc
from typing import Dict, List, Optional, Any

from packages.shared.src.models.base_models import MemoryItem, AgentData
from packages.shared.src.memory.memory_types import MemoryHealth


class MemoryStoragePort(abc.ABC):
    """
    Port interface for memory storage operations.

    This interface defines the contract that any storage adapter must implement,
    regardless of the underlying technology (Firestore, PostgreSQL, Redis, etc.).
    """

    @abc.abstractmethod
    async def initialize(self) -> None:
        """Initialize the storage connection."""
        pass

    @abc.abstractmethod
    async def close(self) -> None:
        """Close the storage connection."""
        pass

    @abc.abstractmethod
    async def save_item(self, item: MemoryItem) -> str:
        """
        Save a memory item to storage.

        Args:
            item: The memory item to save

        Returns:
            The ID of the saved item
        """
        pass

    @abc.abstractmethod
    async def retrieve_item(self, item_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory item by ID.

        Args:
            item_id: The ID of the item to retrieve

        Returns:
            The memory item, or None if not found
        """
        pass

    @abc.abstractmethod
    async def query_items(
        self,
        user_id: str,
        filters: Dict[str, Any],
        limit: int,
    ) -> List[MemoryItem]:
        """
        Query memory items based on filters.

        Args:
            user_id: The ID of the user
            filters: Filters to apply to the query
            limit: Maximum number of items to return

        Returns:
            List of memory items matching the query
        """
        pass

    @abc.abstractmethod
    async def save_agent_data(self, data: AgentData) -> str:
        """
        Save agent data to storage.

        Args:
            data: The agent data to save

        Returns:
            The ID of the saved data
        """
        pass

    @abc.abstractmethod
    async def delete_items(self, filter_criteria: Dict[str, Any]) -> int:
        """
        Delete items matching the given criteria.

        Args:
            filter_criteria: Criteria for items to delete

        Returns:
            Number of items deleted
        """
        pass

    @abc.abstractmethod
    async def check_health(self) -> MemoryHealth:
        """
        Check the health of the storage system.

        Returns:
            Health status information
        """
        pass
