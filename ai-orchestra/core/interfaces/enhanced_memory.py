"""
Enhanced Memory Provider interface.

This module defines the interface for enhanced memory providers with
extended capabilities for metadata, tagging, relationships, and querying.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional


class MemoryItem:
    """Base class for items stored in enhanced memory providers."""

    def __init__(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.content = content
        self.metadata = metadata or {}
        self.tags = tags or []
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or self.created_at


class EnhancedMemoryProvider(ABC):
    """
    Interface for enhanced memory providers with extended capabilities.
    """

    @abstractmethod
    async def store(self, item: MemoryItem) -> str:
        """
        Store an item in memory and return its ID.

        Args:
            item: The memory item to store

        Returns:
            The ID of the stored item
        """

    @abstractmethod
    async def retrieve(self, id: str) -> Optional[MemoryItem]:
        """
        Retrieve an item by its ID.

        Args:
            id: The ID of the item to retrieve

        Returns:
            The memory item if found, None otherwise
        """

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """
        Delete an item by its ID.

        Args:
            id: The ID of the item to delete

        Returns:
            True if the item was deleted, False otherwise
        """

    @abstractmethod
    async def update(self, id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an item's properties.

        Args:
            id: The ID of the item to update
            updates: Dictionary of properties to update

        Returns:
            True if the item was updated, False otherwise
        """

    @abstractmethod
    async def query(
        self, filters: Dict[str, Any], limit: Optional[int] = None
    ) -> List[MemoryItem]:
        """
        Query memory items based on filters.

        Args:
            filters: Dictionary of field criteria
            limit: Maximum number of results to return

        Returns:
            List of matching memory items
        """
