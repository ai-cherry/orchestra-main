"""
"""
    """Memory storage tiers with different performance characteristics."""
    WARM = "warm"  # Firestore - Millisecond access
    COLD = "cold"  # Qdrant - Vector search optimized

@dataclass
class MemoryMetadata:
    """Metadata for memory entries."""
        """Update access metadata."""
        """Compute content hash for deduplication."""
    """A single memory entry that can be stored across tiers."""
        """Compute content hash after initialization."""
        """Convert to dictionary for serialization."""
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
            created_at=datetime.fromisoformat(metadata_dict.get("created_at", datetime.utcnow().isoformat())),
            updated_at=datetime.fromisoformat(metadata_dict.get("updated_at", datetime.utcnow().isoformat())),
            accessed_at=datetime.fromisoformat(metadata_dict.get("accessed_at", datetime.utcnow().isoformat())),
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
    def __lt__(self, other: "MemorySearchResult") -> bool:
        """Compare by score for sorting."""
    """
    """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """Ensure the backend is initialized before operations."""
                        raise RuntimeError(f"Failed to initialize {self.tier.value} memory backend")

    async def migrate_to_tier(self, entry: MemoryEntry, target_tier: MemoryTier) -> bool:
        """
        """
        """
        """