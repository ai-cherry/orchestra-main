# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
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
    """Memory storage tiers with implementation mapping."""
    HOT = "hot"  # Real-time layer (Redis)
    WARM = "warm"  # Recent but not critical (Redis with longer TTL)
    COLD = "cold"  # Historical content (AlloyDB/PostgreSQL)

@dataclass
class MemoryMetadata:
    """Metadata for memory entries."""
        """Convert metadata to dictionary."""
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
        """Convert the memory entry to a dictionary."""
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
        """Update the access metadata."""
        """Compute a hash of the content."""
        """Update the content hash."""