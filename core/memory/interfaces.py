"""
Memory System Interfaces

Defines the contracts for all memory system components following the
Interface Segregation Principle (ISP) and Dependency Inversion Principle (DIP).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable
import asyncio

class MemoryTier(Enum):
    """
    Memory storage tiers with different performance characteristics.
    
    Each tier represents a trade-off between access speed and storage capacity.
    """
    L0_CPU_CACHE = "l0_cpu_cache"      # ~1ns access time
    L1_PROCESS_MEMORY = "l1_process"    # ~10ns access time
    L2_SHARED_MEMORY = "l2_shared"      # ~100ns access time
    L3_POSTGRESQL = "l3_postgresql"     # ~1ms access time
    L4_WEAVIATE = "l4_weaviate"         # ~10ms access time
    
    @property
    def latency_ns(self) -> int:
        """Expected latency in nanoseconds for this tier."""
        latencies = {
            self.L0_CPU_CACHE: 1,
            self.L1_PROCESS_MEMORY: 10,
            self.L2_SHARED_MEMORY: 100,
            self.L3_POSTGRESQL: 1_000_000,
            self.L4_WEAVIATE: 10_000_000,
        }
        return latencies[self]
    
    @property
    def is_persistent(self) -> bool:
        """Whether this tier provides persistent storage."""
        return self in [self.L3_POSTGRESQL, self.L4_WEAVIATE]

@dataclass(frozen=True)
class MemoryItem:
    """
    Immutable representation of a memory item.
    
    Attributes:
        key: Unique identifier for the memory item
        value: The actual data stored
        metadata: Additional information about the item
        tier: Current storage tier
        created_at: When the item was first created
        accessed_at: Last access timestamp
        access_count: Number of times accessed
        size_bytes: Size of the serialized value
        ttl_seconds: Time-to-live in seconds (None for no expiration)
        checksum: Data integrity checksum
    """
    key: str
    value: Any
    metadata: Dict[str, Any]
    tier: MemoryTier
    created_at: datetime
    accessed_at: datetime
    access_count: int
    size_bytes: int
    ttl_seconds: Optional[int]
    checksum: str
    
    def is_expired(self) -> bool:
        """Check if the item has expired based on TTL."""
        if self.ttl_seconds is None:
            return False
        age_seconds = (datetime.utcnow() - self.created_at).total_seconds()
        return age_seconds > self.ttl_seconds
    
    def with_access_update(self) -> 'MemoryItem':
        """Create a new instance with updated access information."""
        return MemoryItem(
            key=self.key,
            value=self.value,
            metadata=self.metadata,
            tier=self.tier,
            created_at=self.created_at,
            accessed_at=datetime.utcnow(),
            access_count=self.access_count + 1,
            size_bytes=self.size_bytes,
            ttl_seconds=self.ttl_seconds,
            checksum=self.checksum
        )

@dataclass(frozen=True)
class MemoryOperation:
    """
    Represents a memory operation for batch processing.
    
    Attributes:
        operation_type: Type of operation (get, set, delete)
        key: Key to operate on
        value: Value for set operations
        ttl_seconds: TTL for set operations
        tier_hint: Suggested tier for storage
    """
    operation_type: str  # 'get', 'set', 'delete'
    key: str
    value: Optional[Any] = None
    ttl_seconds: Optional[int] = None
    tier_hint: Optional[MemoryTier] = None

@dataclass(frozen=True)
class MemoryResult:
    """
    Result of a memory operation.
    
    Attributes:
        success: Whether the operation succeeded
        value: Retrieved value for get operations
        error: Error message if operation failed
        latency_ms: Operation latency in milliseconds
        tier_accessed: Which tier was accessed
    """
    success: bool
    value: Optional[Any] = None
    error: Optional[str] = None
    latency_ms: float = 0.0
    tier_accessed: Optional[MemoryTier] = None

class IMemoryStorage(ABC):
    """
    Interface for memory storage backends.
    
    Each storage implementation (Redis, PostgreSQL, etc.) must implement
    this interface to ensure compatibility with the memory manager.
    """
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the storage backend connections and resources."""
        pass
    
    @abstractmethod
    async def get(self, key: str) -> Optional[MemoryItem]:
        """
        Retrieve an item from storage.
        
        Args:
            key: The key to retrieve
            
        Returns:
            The memory item if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def set(self, item: MemoryItem) -> bool:
        """
        Store an item in the backend.
        
        Args:
            item: The memory item to store
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete an item from storage.
        
        Args:
            key: The key to delete
            
        Returns:
            True if the item was deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in storage.
        
        Args:
            key: The key to check
            
        Returns:
            True if the key exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_batch(self, keys: List[str]) -> Dict[str, Optional[MemoryItem]]:
        """
        Retrieve multiple items in a single operation.
        
        Args:
            keys: List of keys to retrieve
            
        Returns:
            Dictionary mapping keys to items (None if not found)
        """
        pass
    
    @abstractmethod
    async def set_batch(self, items: List[MemoryItem]) -> Dict[str, bool]:
        """
        Store multiple items in a single operation.
        
        Args:
            items: List of items to store
            
        Returns:
            Dictionary mapping keys to success status
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        pattern: Optional[str] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[MemoryItem]:
        """
        Search for items matching criteria.
        
        Args:
            pattern: Key pattern to match (supports wildcards)
            metadata_filter: Metadata fields to filter by
            limit: Maximum number of results
            
        Returns:
            List of matching items
        """
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dictionary containing storage metrics
        """
        pass
    
    @abstractmethod
    async def cleanup_expired(self) -> int:
        """
        Remove expired items from storage.
        
        Returns:
            Number of items removed
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close storage connections and cleanup resources."""
        pass

class IMemoryOptimizer(ABC):
    """
    Interface for memory optimization strategies.
    
    Implementations determine when and how to move items between tiers
    based on access patterns and system resources.
    """
    
    @abstractmethod
    async def analyze_access_patterns(
        self,
        items: List[MemoryItem]
    ) -> Dict[str, MemoryTier]:
        """
        Analyze access patterns and recommend tier placement.
        
        Args:
            items: List of items to analyze
            
        Returns:
            Dictionary mapping keys to recommended tiers
        """
        pass
    
    @abstractmethod
    async def should_promote(self, item: MemoryItem) -> Optional[MemoryTier]:
        """
        Determine if an item should be promoted to a faster tier.
        
        Args:
            item: The item to evaluate
            
        Returns:
            Target tier if promotion is recommended, None otherwise
        """
        pass
    
    @abstractmethod
    async def should_demote(self, item: MemoryItem) -> Optional[MemoryTier]:
        """
        Determine if an item should be demoted to a slower tier.
        
        Args:
            item: The item to evaluate
            
        Returns:
            Target tier if demotion is recommended, None otherwise
        """
        pass
    
    @abstractmethod
    async def predict_access(
        self,
        key: str,
        history: List[datetime]
    ) -> float:
        """
        Predict the probability of future access.
        
        Args:
            key: The key to predict for
            history: List of past access timestamps
            
        Returns:
            Probability of access in the next time window (0.0 to 1.0)
        """
        pass
    
    @abstractmethod
    async def get_prefetch_candidates(
        self,
        accessed_key: str,
        limit: int = 10
    ) -> List[str]:
        """
        Get keys that should be prefetched based on access patterns.
        
        Args:
            accessed_key: The key that was just accessed
            limit: Maximum number of candidates
            
        Returns:
            List of keys to prefetch
        """
        pass

class IMemoryMetrics(ABC):
    """
    Interface for memory system metrics collection.
    
    Implementations track performance, usage, and health metrics
    for monitoring and optimization.
    """
    
    @abstractmethod
    async def record_access(
        self,
        key: str,
        tier: MemoryTier,
        hit: bool,
        latency_ms: float
    ) -> None:
        """
        Record a memory access event.
        
        Args:
            key: The accessed key
            tier: Which tier was accessed
            hit: Whether it was a cache hit
            latency_ms: Access latency in milliseconds
        """
        pass
    
    @abstractmethod
    async def record_operation(
        self,
        operation: str,
        success: bool,
        latency_ms: float,
        error: Optional[str] = None
    ) -> None:
        """
        Record a memory operation.
        
        Args:
            operation: Operation type (get, set, delete, etc.)
            success: Whether the operation succeeded
            latency_ms: Operation latency
            error: Error message if failed
        """
        pass
    
    @abstractmethod
    async def record_tier_migration(
        self,
        key: str,
        from_tier: MemoryTier,
        to_tier: MemoryTier,
        reason: str
    ) -> None:
        """
        Record a tier migration event.
        
        Args:
            key: The migrated key
            from_tier: Source tier
            to_tier: Destination tier
            reason: Reason for migration
        """
        pass
    
    @abstractmethod
    async def get_hit_rate(
        self,
        tier: Optional[MemoryTier] = None,
        time_window_seconds: int = 300
    ) -> float:
        """
        Get cache hit rate.
        
        Args:
            tier: Specific tier or None for overall
            time_window_seconds: Time window to calculate over
            
        Returns:
            Hit rate as a percentage (0.0 to 100.0)
        """
        pass
    
    @abstractmethod
    async def get_latency_percentiles(
        self,
        operation: Optional[str] = None,
        percentiles: List[float] = None
    ) -> Dict[float, float]:
        """
        Get latency percentiles.
        
        Args:
            operation: Specific operation or None for all
            percentiles: List of percentiles (default: [50, 90, 95, 99])
            
        Returns:
            Dictionary mapping percentiles to latencies in ms
        """
        pass
    
    @abstractmethod
    async def get_tier_distribution(self) -> Dict[MemoryTier, int]:
        """
        Get distribution of items across tiers.
        
        Returns:
            Dictionary mapping tiers to item counts
        """
        pass
    
    @abstractmethod
    async def export_metrics(self) -> Dict[str, Any]:
        """
        Export all metrics for external monitoring.
        
        Returns:
            Dictionary of all current metrics
        """
        pass

class IMemoryManager(ABC):
    """
    Main interface for the unified memory management system.
    
    This is the primary interface that applications interact with.
    It orchestrates storage backends, optimization, and metrics.
    """
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the memory manager and all its components."""
        pass
    
    @abstractmethod
    async def get(
        self,
        key: str,
        default: Optional[Any] = None
    ) -> Optional[Any]:
        """
        Retrieve a value from memory.
        
        Args:
            key: The key to retrieve
            default: Default value if not found
            
        Returns:
            The stored value or default
        """
        pass
    
    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        tier_hint: Optional[MemoryTier] = None
    ) -> bool:
        """
        Store a value in memory.
        
        Args:
            key: The key to store under
            value: The value to store
            ttl_seconds: Time-to-live in seconds
            tier_hint: Suggested storage tier
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a value from memory.
        
        Args:
            key: The key to delete
            
        Returns:
            True if the key existed and was deleted
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists.
        
        Args:
            key: The key to check
            
        Returns:
            True if the key exists
        """
        pass
    
    @abstractmethod
    async def batch_operations(
        self,
        operations: List[MemoryOperation]
    ) -> List[MemoryResult]:
        """
        Execute multiple operations atomically.
        
        Args:
            operations: List of operations to execute
            
        Returns:
            List of results corresponding to each operation
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        pattern: Optional[str] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        semantic_query: Optional[str] = None,
        limit: int = 100
    ) -> List[MemoryItem]:
        """
        Search for items across all tiers.
        
        Args:
            pattern: Key pattern to match
            metadata_filter: Metadata fields to filter by
            semantic_query: Semantic search query (for vector search)
            limit: Maximum number of results
            
        Returns:
            List of matching items
        """
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive memory system statistics.
        
        Returns:
            Dictionary containing all system metrics
        """
        pass
    
    @abstractmethod
    async def optimize(self) -> Dict[str, int]:
        """
        Run optimization pass on all stored items.
        
        Returns:
            Dictionary with counts of promoted/demoted items
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> int:
        """
        Clean up expired items and optimize storage.
        
        Returns:
            Number of items cleaned up
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Gracefully shutdown the memory manager."""
        pass

# Type aliases for cleaner function signatures
MemoryCallback = Callable[[MemoryItem], Awaitable[None]]
MemoryPredicate = Callable[[MemoryItem], bool]
MemoryTransform = Callable[[Any], Any]