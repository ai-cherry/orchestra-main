"""
Base abstract interfaces for the three-tier memory system.

This module defines the core abstractions for memory storage, retrieval,
and management across different tiers with performance-first design.
"""

import asyncio
import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4


class MemoryTier(Enum):
    """Memory storage tiers with different performance characteristics."""

    HOT = "hot"  # DragonflyDB - Sub-millisecond access
    WARM = "warm"  # Firestore - Millisecond access
    COLD = "cold"  # Qdrant - Vector search optimized


@dataclass
class MemoryMetadata:
    """Metadata for memory entries."""

    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    accessed_at: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    tier: MemoryTier = MemoryTier.HOT
    ttl_seconds: int = 3600  # Default 1 hour
    tags: List[str] = field(default_factory=list)
    source: Optional[str] = None
    content_hash: Optional[str] = None

    def update_access(self) -> None:
        """Update access metadata."""
        self.accessed_at = datetime.utcnow()
        self.access_count += 1

    def compute_hash(self, content: Any) -> str:
        """Compute content hash for deduplication."""
        content_str = json.dumps(content, sort_keys=True)
        self.content_hash = hashlib.sha256(content_str.encode()).hexdigest()
        return self.content_hash


@dataclass
class MemoryEntry:
    """A single memory entry that can be stored across tiers."""

    key: str
    content: Any  # Can be text, dict, list, etc.
    metadata: MemoryMetadata = field(default_factory=MemoryMetadata)
    embedding: Optional[List[float]] = None

    def __post_init__(self):
        """Compute content hash after initialization."""
        if not self.metadata.content_hash:
            self.metadata.compute_hash(self.content)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "key": self.key,
            "content": self.content,
            "metadata": {
                "id": self.metadata.id,
                "created_at": self.metadata.created_at.isoformat(),
                "updated_at": self.metadata.updated_at.isoformat(),
                "accessed_at": self.metadata.accessed_at.isoformat(),
                "access_count": self.metadata.access_count,
                "tier": self.metadata.tier.value,
                "ttl_seconds": self.metadata.ttl_seconds,
                "tags": self.metadata.tags,
                "source": self.metadata.source,
                "content_hash": self.metadata.content_hash,
            },
            "embedding": self.embedding,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Create from dictionary."""
        metadata_dict = data.get("metadata", {})
        metadata = MemoryMetadata(
            id=metadata_dict.get("id", str(uuid4())),
            created_at=datetime.fromisoformat(
                metadata_dict.get("created_at", datetime.utcnow().isoformat())
            ),
            updated_at=datetime.fromisoformat(
                metadata_dict.get("updated_at", datetime.utcnow().isoformat())
            ),
            accessed_at=datetime.fromisoformat(
                metadata_dict.get("accessed_at", datetime.utcnow().isoformat())
            ),
            access_count=metadata_dict.get("access_count", 0),
            tier=MemoryTier(metadata_dict.get("tier", MemoryTier.HOT.value)),
            ttl_seconds=metadata_dict.get("ttl_seconds", 3600),
            tags=metadata_dict.get("tags", []),
            source=metadata_dict.get("source"),
            content_hash=metadata_dict.get("content_hash"),
        )

        return cls(
            key=data["key"],
            content=data["content"],
            metadata=metadata,
            embedding=data.get("embedding"),
        )


@dataclass
class MemorySearchResult:
    """Result from memory search operations."""

    entry: MemoryEntry
    score: float  # Relevance score (0-1)
    tier: MemoryTier

    def __lt__(self, other: "MemorySearchResult") -> bool:
        """Compare by score for sorting."""
        return self.score < other.score


class BaseMemory(ABC):
    """
    Abstract base class for memory implementations.

    All implementations must be async and performance-optimized.
    """

    def __init__(self, tier: MemoryTier, config: Optional[Dict[str, Any]] = None):
        """
        Initialize memory backend.

        Args:
            tier: The memory tier this implementation handles
            config: Configuration dictionary
        """
        self.tier = tier
        self.config = config or {}
        self._initialized = False
        self._lock = asyncio.Lock()

    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the memory backend.

        Returns:
            bool: True if initialization successful
        """

    @abstractmethod
    async def save(self, entry: MemoryEntry) -> bool:
        """
        Save a memory entry.

        Args:
            entry: The memory entry to save

        Returns:
            bool: True if save successful
        """

    @abstractmethod
    async def get(self, key: str) -> Optional[MemoryEntry]:
        """
        Retrieve a memory entry by key.

        Args:
            key: The entry key

        Returns:
            MemoryEntry or None if not found
        """

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a memory entry.

        Args:
            key: The entry key

        Returns:
            bool: True if deletion successful
        """

    @abstractmethod
    async def search(
        self,
        query: Union[str, List[float]],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[MemorySearchResult]:
        """
        Search for memory entries.

        Args:
            query: Text query or embedding vector
            limit: Maximum results to return
            filters: Optional filters (tags, date range, etc.)

        Returns:
            List of search results sorted by relevance
        """

    @abstractmethod
    async def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """
        List all keys with optional prefix filter.

        Args:
            prefix: Optional key prefix

        Returns:
            List of keys
        """

    @abstractmethod
    async def batch_save(self, entries: List[MemoryEntry]) -> Dict[str, bool]:
        """
        Save multiple entries in batch for performance.

        Args:
            entries: List of memory entries

        Returns:
            Dict mapping keys to success status
        """

    @abstractmethod
    async def batch_get(self, keys: List[str]) -> Dict[str, Optional[MemoryEntry]]:
        """
        Retrieve multiple entries in batch.

        Args:
            keys: List of keys to retrieve

        Returns:
            Dict mapping keys to entries (None if not found)
        """

    @abstractmethod
    async def clear(self, prefix: Optional[str] = None) -> int:
        """
        Clear all entries or those matching prefix.

        Args:
            prefix: Optional key prefix

        Returns:
            Number of entries cleared
        """

    @abstractmethod
    async def stats(self) -> Dict[str, Any]:
        """
        Get memory statistics.

        Returns:
            Dict with stats (size, count, performance metrics, etc.)
        """

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of the memory backend.

        Returns:
            Dict with health status and diagnostics
        """

    async def ensure_initialized(self) -> None:
        """Ensure the backend is initialized before operations."""
        if not self._initialized:
            async with self._lock:
                if not self._initialized:
                    self._initialized = await self.initialize()
                    if not self._initialized:
                        raise RuntimeError(
                            f"Failed to initialize {self.tier.value} memory backend"
                        )

    async def migrate_to_tier(
        self, entry: MemoryEntry, target_tier: MemoryTier
    ) -> bool:
        """
        Migrate an entry to a different tier.

        Args:
            entry: The memory entry
            target_tier: Target memory tier

        Returns:
            bool: True if migration successful
        """
        # This is a placeholder - actual implementation would coordinate with other tiers
        entry.metadata.tier = target_tier
        entry.metadata.updated_at = datetime.utcnow()
        return await self.save(entry)

    def should_migrate(self, entry: MemoryEntry) -> Optional[MemoryTier]:
        """
        Determine if an entry should be migrated to another tier.

        Args:
            entry: The memory entry

        Returns:
            Target tier or None if no migration needed
        """
        # Simple age-based migration logic
        age_seconds = (datetime.utcnow() - entry.metadata.accessed_at).total_seconds()

        if self.tier == MemoryTier.HOT and age_seconds > 3600:  # 1 hour
            return MemoryTier.WARM
        elif self.tier == MemoryTier.WARM and age_seconds > 86400:  # 1 day
            return MemoryTier.COLD

        return None
