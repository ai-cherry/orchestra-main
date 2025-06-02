"""
Base memory service interface.

This module provides the abstract interface for the layered memory system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TypeVar

T = TypeVar("T")

class MemoryLayer(Enum):
    """Memory layer types."""

    SHORT_TERM = "short_term"  # Hot cache (DragonflyDB)
    MID_TERM = "mid_term"  # Document store (MongoDB)
    LONG_TERM = "long_term"  # Vector store (Weaviate)

@dataclass
class MemoryItem:
    """Base class for items stored in memory."""

    id: str
    content: Any
    metadata: Dict[str, Any]
    timestamp: datetime
    layer: MemoryLayer
    ttl: Optional[int] = None  # Time to live in seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "layer": self.layer.value,
            "ttl": self.ttl,
        }

@dataclass
class SearchResult:
    """Result from a memory search operation."""

    item: MemoryItem
    score: float
    source: MemoryLayer

class MemoryStore(ABC):
    """Abstract base class for memory stores."""

    def __init__(self, layer: MemoryLayer):
        self.layer = layer

    @abstractmethod
    async def store(self, item: MemoryItem) -> bool:
        """Store an item in memory."""
        pass

    @abstractmethod
    async def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        """Retrieve an item by ID."""
        pass

    @abstractmethod
    async def delete(self, item_id: str) -> bool:
        """Delete an item by ID."""
        pass

    @abstractmethod
    async def search(self, query: str, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Search for items matching the query."""
        pass

    @abstractmethod
    async def list_items(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[MemoryItem]:
        """List items with pagination."""
        pass

    @abstractmethod
    async def clear(self) -> int:
        """Clear all items from this store."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the store is healthy."""
        pass

class MemoryService(ABC):
    """Abstract base class for the unified memory service."""

    @abstractmethod
    async def store(
        self,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
        layer: Optional[MemoryLayer] = None,
        ttl: Optional[int] = None,
    ) -> str:
        """
        Store content in the appropriate memory layer.

        Args:
            content: The content to store
            metadata: Optional metadata
            layer: Specific layer to use (auto-selected if None)
            ttl: Time to live in seconds

        Returns:
            The ID of the stored item
        """
        pass

    @abstractmethod
    async def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        """
        Retrieve an item from any layer.

        Args:
            item_id: The ID of the item to retrieve

        Returns:
            The memory item if found, None otherwise
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 10,
        layers: Optional[List[MemoryLayer]] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        Search across memory layers.

        Args:
            query: The search query
            limit: Maximum number of results
            layers: Specific layers to search (all if None)
            filters: Additional filters

        Returns:
            List of search results sorted by relevance
        """
        pass

    @abstractmethod
    async def promote(self, item_id: str, target_layer: MemoryLayer) -> bool:
        """
        Promote an item to a different memory layer.

        Args:
            item_id: The ID of the item to promote
            target_layer: The target memory layer

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def evict(self, item_id: str) -> bool:
        """
        Evict an item from all memory layers.

        Args:
            item_id: The ID of the item to evict

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about memory usage.

        Returns:
            Dictionary with stats for each layer
        """
        pass

class MemoryPolicy(ABC):
    """Abstract base class for memory management policies."""

    @abstractmethod
    def should_promote(self, item: MemoryItem, access_count: int) -> Optional[MemoryLayer]:
        """Determine if an item should be promoted to another layer."""
        pass

    @abstractmethod
    def should_evict(self, item: MemoryItem, last_access: datetime) -> bool:
        """Determine if an item should be evicted."""
        pass

    @abstractmethod
    def select_layer(self, content: Any, metadata: Dict[str, Any]) -> MemoryLayer:
        """Select the appropriate layer for new content."""
        pass
