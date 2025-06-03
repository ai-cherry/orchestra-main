"""
"""
    """Base class for eviction policies."""
        """Called when an item is accessed."""
        """Called when an item is inserted."""
        """Get the next item to evict."""
        """Remove a key from tracking."""
    """Least Recently Used eviction policy."""
        """Move key to end (most recent)."""
        """Add key as most recent."""
        """Get least recently used key."""
        """Remove key from tracking."""
    """Least Frequently Used eviction policy."""
        """Increment frequency count."""
        """Add key with frequency 1."""
        """Get least frequently used key."""
        """Remove key from tracking."""
    """First In First Out eviction policy."""
        """Add key to queue."""
        """Get oldest key."""
        """Remove key from queue."""
    """
    """
        eviction_policy: str = "lru",
        compression_enabled: bool = True,
        compression_threshold: int = 1024  # Compress items larger than 1KB
    ):
        self.tier = tier
        self.max_size_bytes = max_size_bytes
        self.max_items = max_items
        self.compression_enabled = compression_enabled
        self.compression_threshold = compression_threshold
        
        # Storage
        self._storage: Dict[str, Tuple[bytes, MemoryItem]] = {}
        self._lock = RLock()
        
        # Eviction policy
        self._eviction_policy = self._create_eviction_policy(eviction_policy)
        
        # Metrics
        self._current_size_bytes = 0
        self._hit_count = 0
        self._miss_count = 0
        self._eviction_count = 0
        
        # TTL tracking
        self._ttl_heap: List[Tuple[float, str]] = []
        
        logger.info(
            f"Initialized InMemoryStorage for tier {tier.value} with "
            f"max_size={max_size_bytes}, max_items={max_items}, "
            f"policy={eviction_policy}"
        )
    
    def _create_eviction_policy(self, policy_name: str) -> EvictionPolicy:
        """Create eviction policy instance."""
            "lru": LRUPolicy,
            "lfu": LFUPolicy,
            "fifo": FIFOPolicy,
        }
        
        if policy_name not in policies:
            raise MemoryValidationError(
                validation_type="eviction_policy",
                field="policy",
                value=policy_name,
                constraint=f"Must be one of: {', '.join(policies.keys())}"
            )
        
        return policies[policy_name](self.max_items)
    
    async def initialize(self) -> None:
        """Initialize storage (no-op for in-memory)."""
    
    async def get(self, key: str) -> Optional[MemoryItem]:
        """Retrieve an item from memory."""
        """Store an item in memory."""
            logger.error(f"Failed to set item {item.key}: {str(e)}")
            raise MemoryStorageError(
                operation="set",
                storage_backend="inmemory",
                reason=str(e),
                key=item.key,
                cause=e
            )
    
    async def delete(self, key: str) -> bool:
        """Delete an item from memory."""
        """Check if a key exists."""
        """Get multiple items."""
        """Set multiple items."""
                logger.error(f"Failed to set item {item.key} in batch: {str(e)}")
                results[item.key] = False
        return results
    
    async def search(
        self,
        pattern: Optional[str] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[MemoryItem]:
        """Search for items matching criteria."""
        """Get storage statistics."""
                "tier": self.tier.value,
                "total_items": total_items,
                "total_size_bytes": self._current_size_bytes,
                "max_size_bytes": self.max_size_bytes,
                "max_items": self.max_items,
                "utilization_percent": (self._current_size_bytes / self.max_size_bytes) * 100,
                "hit_count": self._hit_count,
                "miss_count": self._miss_count,
                "hit_rate": hit_rate * 100,
                "eviction_count": self._eviction_count,
                "compression_enabled": self.compression_enabled,
            }
    
    async def cleanup_expired(self) -> int:
        """Remove expired items."""
            logger.info(f"Cleaned up {expired_count} expired items from {self.tier.value}")
        
        return expired_count
    
    async def close(self) -> None:
        """Close storage (no-op for in-memory)."""
    
    # Private helper methods
    
    def _serialize_item(self, item: MemoryItem) -> bytes:
        """Serialize and optionally compress an item."""
                "key": item.key,
                "value": item.value,
                "metadata": item.metadata,
                "tier": item.tier.value,
                "created_at": item.created_at.isoformat(),
                "accessed_at": item.accessed_at.isoformat(),
                "access_count": item.access_count,
                "size_bytes": item.size_bytes,
                "ttl_seconds": item.ttl_seconds,
                "checksum": item.checksum,
            }
            
            # Serialize with pickle
            serialized = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
            
            # Compress if enabled and above threshold
            if self.compression_enabled and len(serialized) > self.compression_threshold:
                serialized = lz4.frame.compress(serialized)
            
            return serialized
            
        except Exception:

            
            pass
            raise MemorySerializationError(
                operation="serialize",
                key=item.key,
                value_type=type(item.value).__name__,
                reason=str(e),
                cause=e
            )
    
    async def _ensure_capacity(self, required_size: int, key: str) -> bool:
        """Ensure there's enough capacity for a new item."""
        """Check if key matches pattern (supports * wildcard)."""
        """Check if metadata matches filter."""