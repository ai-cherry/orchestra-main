"""
In-Memory Storage Implementation

High-performance in-memory storage for L0 (CPU cache) and L1 (process memory) tiers.
Implements various eviction policies and optimizations for speed.
"""

import asyncio
import time
import hashlib
import pickle
import lz4.frame
from collections import OrderedDict, defaultdict
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import heapq
import logging
from threading import RLock

from ...interfaces import IMemoryStorage, MemoryItem, MemoryTier
from ...exceptions import (
    MemoryStorageError,
    MemoryCapacityError,
    MemorySerializationError,
    MemoryValidationError
)

logger = logging.getLogger(__name__)

class EvictionPolicy:
    """Base class for eviction policies."""
    
    def __init__(self, max_items: int):
        self.max_items = max_items
    
    def on_access(self, key: str) -> None:
        """Called when an item is accessed."""
        pass
    
    def on_insert(self, key: str) -> None:
        """Called when an item is inserted."""
        pass
    
    def get_eviction_candidate(self) -> Optional[str]:
        """Get the next item to evict."""
        raise NotImplementedError
    
    def remove(self, key: str) -> None:
        """Remove a key from tracking."""
        pass

class LRUPolicy(EvictionPolicy):
    """Least Recently Used eviction policy."""
    
    def __init__(self, max_items: int):
        super().__init__(max_items)
        self.access_order = OrderedDict()
    
    def on_access(self, key: str) -> None:
        """Move key to end (most recent)."""
        if key in self.access_order:
            self.access_order.move_to_end(key)
    
    def on_insert(self, key: str) -> None:
        """Add key as most recent."""
        self.access_order[key] = True
    
    def get_eviction_candidate(self) -> Optional[str]:
        """Get least recently used key."""
        if self.access_order:
            return next(iter(self.access_order))
        return None
    
    def remove(self, key: str) -> None:
        """Remove key from tracking."""
        self.access_order.pop(key, None)

class LFUPolicy(EvictionPolicy):
    """Least Frequently Used eviction policy."""
    
    def __init__(self, max_items: int):
        super().__init__(max_items)
        self.frequency = defaultdict(int)
        self.freq_lists = defaultdict(set)
        self.min_freq = 0
    
    def on_access(self, key: str) -> None:
        """Increment frequency count."""
        freq = self.frequency[key]
        self.frequency[key] = freq + 1
        
        # Move to higher frequency list
        if freq > 0:
            self.freq_lists[freq].discard(key)
            if not self.freq_lists[freq] and self.min_freq == freq:
                self.min_freq += 1
        
        self.freq_lists[freq + 1].add(key)
    
    def on_insert(self, key: str) -> None:
        """Add key with frequency 1."""
        self.frequency[key] = 1
        self.freq_lists[1].add(key)
        self.min_freq = 1
    
    def get_eviction_candidate(self) -> Optional[str]:
        """Get least frequently used key."""
        if self.min_freq in self.freq_lists and self.freq_lists[self.min_freq]:
            return next(iter(self.freq_lists[self.min_freq]))
        return None
    
    def remove(self, key: str) -> None:
        """Remove key from tracking."""
        freq = self.frequency.pop(key, 0)
        if freq > 0:
            self.freq_lists[freq].discard(key)

class FIFOPolicy(EvictionPolicy):
    """First In First Out eviction policy."""
    
    def __init__(self, max_items: int):
        super().__init__(max_items)
        self.queue = []
    
    def on_insert(self, key: str) -> None:
        """Add key to queue."""
        self.queue.append(key)
    
    def get_eviction_candidate(self) -> Optional[str]:
        """Get oldest key."""
        return self.queue[0] if self.queue else None
    
    def remove(self, key: str) -> None:
        """Remove key from queue."""
        try:
            self.queue.remove(key)
        except ValueError:
            pass

class InMemoryStorage(IMemoryStorage):
    """
    High-performance in-memory storage implementation.
    
    Features:
    - Multiple eviction policies (LRU, LFU, FIFO)
    - Optional compression with LZ4
    - Thread-safe operations
    - Memory usage tracking
    - TTL support
    """
    
    def __init__(
        self,
        tier: MemoryTier,
        max_size_bytes: int,
        max_items: int,
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
        policies = {
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
        logger.debug(f"InMemoryStorage initialized for tier {self.tier.value}")
    
    async def get(self, key: str) -> Optional[MemoryItem]:
        """Retrieve an item from memory."""
        with self._lock:
            # Check if exists
            if key not in self._storage:
                self._miss_count += 1
                return None
            
            # Get item
            serialized, item = self._storage[key]
            
            # Check TTL
            if item.is_expired():
                await self.delete(key)
                self._miss_count += 1
                return None
            
            # Update access info
            updated_item = item.with_access_update()
            self._storage[key] = (serialized, updated_item)
            
            # Update eviction policy
            self._eviction_policy.on_access(key)
            
            self._hit_count += 1
            return updated_item
    
    async def set(self, item: MemoryItem) -> bool:
        """Store an item in memory."""
        try:
            # Serialize and optionally compress
            serialized = self._serialize_item(item)
            item_size = len(serialized)
            
            with self._lock:
                # Check capacity
                if await self._ensure_capacity(item_size, item.key):
                    # Store item
                    self._storage[item.key] = (serialized, item)
                    self._current_size_bytes += item_size
                    
                    # Update eviction policy
                    self._eviction_policy.on_insert(item.key)
                    
                    # Track TTL if set
                    if item.ttl_seconds:
                        expiry_time = time.time() + item.ttl_seconds
                        heapq.heappush(self._ttl_heap, (expiry_time, item.key))
                    
                    return True
                else:
                    raise MemoryCapacityError(
                        tier=self.tier.value,
                        current_size=self._current_size_bytes,
                        max_size=self.max_size_bytes,
                        requested_size=item_size
                    )
                    
        except Exception as e:
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
        with self._lock:
            if key in self._storage:
                serialized, _ = self._storage[key]
                self._current_size_bytes -= len(serialized)
                del self._storage[key]
                self._eviction_policy.remove(key)
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        with self._lock:
            if key not in self._storage:
                return False
            
            # Check TTL
            _, item = self._storage[key]
            if item.is_expired():
                await self.delete(key)
                return False
            
            return True
    
    async def get_batch(self, keys: List[str]) -> Dict[str, Optional[MemoryItem]]:
        """Get multiple items."""
        results = {}
        for key in keys:
            results[key] = await self.get(key)
        return results
    
    async def set_batch(self, items: List[MemoryItem]) -> Dict[str, bool]:
        """Set multiple items."""
        results = {}
        for item in items:
            try:
                results[item.key] = await self.set(item)
            except Exception as e:
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
        results = []
        
        with self._lock:
            for key, (_, item) in self._storage.items():
                # Skip expired items
                if item.is_expired():
                    continue
                
                # Check pattern match
                if pattern and not self._match_pattern(key, pattern):
                    continue
                
                # Check metadata filter
                if metadata_filter and not self._match_metadata(item.metadata, metadata_filter):
                    continue
                
                results.append(item)
                
                if len(results) >= limit:
                    break
        
        return results
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        with self._lock:
            total_items = len(self._storage)
            hit_rate = (
                self._hit_count / (self._hit_count + self._miss_count)
                if (self._hit_count + self._miss_count) > 0
                else 0.0
            )
            
            return {
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
        current_time = time.time()
        expired_count = 0
        
        with self._lock:
            # Process TTL heap
            while self._ttl_heap and self._ttl_heap[0][0] <= current_time:
                _, key = heapq.heappop(self._ttl_heap)
                if key in self._storage:
                    _, item = self._storage[key]
                    if item.is_expired():
                        await self.delete(key)
                        expired_count += 1
        
        if expired_count > 0:
            logger.info(f"Cleaned up {expired_count} expired items from {self.tier.value}")
        
        return expired_count
    
    async def close(self) -> None:
        """Close storage (no-op for in-memory)."""
        logger.debug(f"Closing InMemoryStorage for tier {self.tier.value}")
    
    # Private helper methods
    
    def _serialize_item(self, item: MemoryItem) -> bytes:
        """Serialize and optionally compress an item."""
        try:
            # Create a dict representation for serialization
            data = {
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
            
        except Exception as e:
            raise MemorySerializationError(
                operation="serialize",
                key=item.key,
                value_type=type(item.value).__name__,
                reason=str(e),
                cause=e
            )
    
    async def _ensure_capacity(self, required_size: int, key: str) -> bool:
        """Ensure there's enough capacity for a new item."""
        # If key already exists, subtract its current size
        current_item_size = 0
        if key in self._storage:
            current_item_size = len(self._storage[key][0])
        
        needed_size = required_size - current_item_size
        
        # Check if we need to evict items
        while (
            (self._current_size_bytes + needed_size > self.max_size_bytes) or
            (len(self._storage) >= self.max_items and key not in self._storage)
        ):
            # Get eviction candidate
            evict_key = self._eviction_policy.get_eviction_candidate()
            if not evict_key or evict_key == key:
                return False
            
            # Evict item
            await self.delete(evict_key)
            self._eviction_count += 1
        
        return True
    
    def _match_pattern(self, key: str, pattern: str) -> bool:
        """Check if key matches pattern (supports * wildcard)."""
        import fnmatch
        return fnmatch.fnmatch(key, pattern)
    
    def _match_metadata(self, metadata: Dict[str, Any], filter: Dict[str, Any]) -> bool:
        """Check if metadata matches filter."""
        for key, value in filter.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True