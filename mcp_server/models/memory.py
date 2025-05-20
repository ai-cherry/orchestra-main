#!/usr/bin/env python3
"""
memory.py - MCP Memory Models

This module defines the standardized data models for the MCP memory system.
These models provide a consistent representation of memory entries and metadata
across all storage implementations and tool adapters.
"""

import time
import json
import hashlib
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


class MemoryType(str, Enum):
    """Memory type classification."""

    SHARED = "shared"  # Memory shared across tools
    TOOL_SPECIFIC = "tool_specific"  # Memory specific to a single tool
    CONTEXT = "context"  # Current context information
    HISTORY = "history"  # Conversation or operation history
    KNOWLEDGE = "knowledge"  # Long-term knowledge base content


class MemoryScope(str, Enum):
    """Memory scope classification."""

    SESSION = "session"  # Valid for current session only
    GLOBAL = "global"  # Globally available across sessions
    PROJECT = "project"  # Specific to a project or workspace
    USER = "user"  # Specific to a user


class CompressionLevel(int, Enum):
    """Memory compression levels."""

    NONE = 0
    LIGHT = 1
    MEDIUM = 2
    HIGH = 3
    EXTREME = 4
    REFERENCE_ONLY = 5


class StorageTier(str, Enum):
    """Memory storage tiers with implementation mapping."""

    HOT = "hot"  # Real-time layer (Redis)
    WARM = "warm"  # Recent but not critical (Redis with longer TTL)
    COLD = "cold"  # Historical content (AlloyDB/PostgreSQL)


@dataclass
class MemoryMetadata:
    """Metadata for memory entries."""

    source_tool: str  # Tool that created the memory
    last_modified: float  # Timestamp of last modification
    access_count: int = 0  # Number of times accessed
    context_relevance: float = 0.5  # Relevance score for context
    last_accessed: float = field(default_factory=time.time)  # Last access time
    version: int = 1  # Version number for conflict resolution
    sync_status: Dict[str, int] = field(default_factory=dict)  # Sync status per tool
    content_hash: Optional[str] = None  # Hash of content for integrity checks
    embedding_model: Optional[str] = None  # Model used for vector embeddings
    tags: List[str] = field(default_factory=list)  # Tags for categorization

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "source_tool": self.source_tool,
            "last_modified": self.last_modified,
            "access_count": self.access_count,
            "context_relevance": self.context_relevance,
            "last_accessed": self.last_accessed,
            "version": self.version,
            "sync_status": self.sync_status,
            "content_hash": self.content_hash,
            "embedding_model": self.embedding_model,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryMetadata":
        """Create metadata from dictionary."""
        return cls(
            source_tool=data["source_tool"],
            last_modified=data["last_modified"],
            access_count=data.get("access_count", 0),
            context_relevance=data.get("context_relevance", 0.5),
            last_accessed=data.get("last_accessed", time.time()),
            version=data.get("version", 1),
            sync_status=data.get("sync_status", {}),
            content_hash=data.get("content_hash"),
            embedding_model=data.get("embedding_model"),
            tags=data.get("tags", []),
        )


@dataclass
class MemoryEntry:
    """Unified memory entry conforming to the schema."""

    memory_type: MemoryType  # Type of memory entry
    scope: MemoryScope  # Scope of memory entry
    priority: int  # Priority (higher values = more important)
    compression_level: CompressionLevel  # Level of compression applied
    ttl_seconds: int  # Time-to-live in seconds
    content: Any  # Actual content (string, dict, etc.)
    metadata: MemoryMetadata  # Associated metadata
    storage_tier: StorageTier = StorageTier.HOT  # Storage tier for tiered access
    embedding: Optional[List[float]] = None  # Vector embedding for semantic search

    def to_dict(self) -> Dict[str, Any]:
        """Convert the memory entry to a dictionary."""
        return {
            "memory_type": self.memory_type,
            "scope": self.scope,
            "priority": self.priority,
            "compression_level": self.compression_level,
            "ttl_seconds": self.ttl_seconds,
            "content": self.content,
            "metadata": self.metadata.to_dict(),
            "storage_tier": self.storage_tier,
            "embedding": self.embedding,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Create a memory entry from a dictionary."""
        metadata = MemoryMetadata.from_dict(data["metadata"])

        return cls(
            memory_type=data["memory_type"],
            scope=data["scope"],
            priority=data["priority"],
            compression_level=data["compression_level"],
            ttl_seconds=data["ttl_seconds"],
            content=data["content"],
            metadata=metadata,
            storage_tier=data.get("storage_tier", StorageTier.HOT),
            embedding=data.get("embedding"),
        )

    def is_expired(self) -> bool:
        """Check if the memory entry has expired."""
        age = time.time() - self.metadata.last_modified
        return age > self.ttl_seconds

    def update_access(self) -> None:
        """Update the access metadata."""
        self.metadata.access_count += 1
        self.metadata.last_accessed = time.time()

    def compute_hash(self) -> str:
        """Compute a hash of the content."""
        content_str = json.dumps(self.content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def update_hash(self) -> None:
        """Update the content hash."""
        self.metadata.content_hash = self.compute_hash()
