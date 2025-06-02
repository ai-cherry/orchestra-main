"""
Unified Memory Manager Implementation

The main orchestrator that manages all memory tiers, handles tier promotion/demotion,
and provides a unified interface for memory operations.
"""

import asyncio
import hashlib
import time
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
import logging
from contextlib import asynccontextmanager
import json
from collections import defaultdict

from ..interfaces import (
    IMemoryManager,
    IMemoryStorage,
    IMemoryOptimizer,
    IMemoryMetrics,
    MemoryTier,
    MemoryItem,
    MemoryOperation,
    MemoryResult
)
from ..config import MemoryConfig, get_config
from ..exceptions import (
    MemoryException,
    MemoryNotFoundError,
    MemoryStorageError,
    MemoryTierError,
    MemoryValidationError,
    MemoryExceptionHandler
)
from .storage import MemoryStorageFactory
from .optimizer import MemoryOptimizer
from .metrics import MemoryMetricsCollector

logger = logging.getLogger(__name__)

class UnifiedMemoryManager(IMemoryManager):
    """
    Production-ready unified memory management system.
    
    This manager orchestrates multiple storage tiers, handles automatic
    tier promotion/demotion, implements predictive prefetching, and
    provides comprehensive metrics and monitoring.
    
    Features:
    - Multi-tier storage orchestration
    - Automatic tier optimization based on access patterns
    - Predictive prefetching for improved performance
    - Comprehensive metrics and monitoring
    - Batch operations support
    - Semantic search capabilities
    - Graceful error handling and recovery
    """
    
    def __init__(
        self,
        config: Optional[MemoryConfig] = None,
        optimizer: Optional[IMemoryOptimizer] = None,
        metrics_collector: Optional[IMemoryMetrics] = None
    ):
        """
        Initialize the unified memory manager.
        
        Args:
            config: Memory system configuration (uses global config if None)
            optimizer: Memory optimizer instance (creates default if None)
            metrics_collector: Metrics collector instance (creates default if None)
        """
        self.config = config or get_config()
        self.optimizer = optimizer or MemoryOptimizer(self.config.optimization)
        self.metrics = metrics_collector or MemoryMetricsCollector(self.config.metrics)
        
        # Storage backends for each tier
        self._storages: Dict[MemoryTier, IMemoryStorage] = {}
        
        # Tier access order for retrieval
        self._tier_hierarchy = [
            MemoryTier.L0_CPU_CACHE,
            MemoryTier.L1_PROCESS_MEMORY,
            MemoryTier.L2_SHARED_MEMORY,
            MemoryTier.L3_POSTGRESQL,
            MemoryTier.L4_WEAVIATE
        ]
        
        # Background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        
        # Operation semaphore for concurrency control
        self._operation_semaphore = asyncio.Semaphore(
            self.config.max_concurrent_operations
        )
        
        # Prefetch queue
        self._prefetch_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        
        logger.info(
            f"Initialized UnifiedMemoryManager with {len(self._tier_hierarchy)} tiers"
        )
    
    async def initialize(self) -> None:
        """Initialize all components and start background tasks."""
        logger.info("Initializing UnifiedMemoryManager...")
        
        try:
            # Create storage instances for all enabled tiers
            self._storages = await self._initialize_storages()
            
            # Initialize components
            await self.optimizer.initialize(self._storages)
            await self.metrics.initialize()
            
            # Start background tasks
            self._start_background_tasks()
            
            logger.info(
                f"UnifiedMemoryManager initialized with {len(self._storages)} active tiers"
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize memory manager: {str(e)}")
            await self.close()
            raise
    
    async def _initialize_storages(self) -> Dict[MemoryTier, IMemoryStorage]:
        """Initialize all storage backends."""
        storages = {}
        
        for tier in self._tier_hierarchy:
            tier_config = self.config.tiers.get(tier.value)
            if not tier_config or not tier_config.enabled:
                logger.info(f"Tier {tier.value} is disabled, skipping initialization")
                continue
            
            try:
                # Create storage instance
                storage = MemoryStorageFactory.create_storage(tier, self.config)
                await storage.initialize()
                storages[tier] = storage
                logger.info(f"Initialized storage for tier {tier.value}")
                
            except Exception as e:
                logger.error(f"Failed to initialize tier {tier.value}: {str(e)}")
                # Continue with other tiers
        
        if not storages:
            raise MemoryStorageError(
                operation="initialize",
                storage_backend="all",
                reason="No storage tiers could be initialized"
            )
        
        return storages
    
    def _start_background_tasks(self) -> None:
        """Start background maintenance tasks."""
        # Optimization task
        if self.config.optimization.enabled:
            self._background_tasks.append(
                asyncio.create_task(self._optimization_loop())
            )
        
        # Cleanup task
        self._background_tasks.append(
            asyncio.create_task(self._cleanup_loop())
        )
        
        # Prefetch task
        if self.config.optimization.prefetch_enabled:
            self._background_tasks.append(
                asyncio.create_task(self._prefetch_loop())
            )
        
        # Metrics export task
        if self.config.metrics.enabled:
            self._background_tasks.append(
                asyncio.create_task(self._metrics_export_loop())
            )
        
        logger.info(f"Started {len(self._background_tasks)} background tasks")
    
    async def get(
        self,
        key: str,
        default: Optional[Any] = None
    ) -> Optional[Any]:
        """
        Retrieve a value from memory.
        
        Searches through tiers in order until the item is found.
        Automatically promotes frequently accessed items to faster tiers.
        """
        if not key:
            raise MemoryValidationError(
                validation_type="key",
                field="key",
                value=key,
                constraint="Key cannot be empty"
            )
        
        start_time = time.time()
        
        async with self._operation_semaphore:
            try:
                # Search through tiers
                for tier in self._tier_hierarchy:
                    if tier not in self._storages:
                        continue
                    
                    storage = self._storages[tier]
                    item = await storage.get(key)
                    
                    if item:
                        # Record metrics
                        latency_ms = (time.time() - start_time) * 1000
                        await self.metrics.record_access(
                            key=key,
                            tier=tier,
                            hit=True,
                            latency_ms=latency_ms
                        )
                        
                        # Check if item should be promoted
                        target_tier = await self.optimizer.should_promote(item)
                        if target_tier and target_tier != tier:
                            asyncio.create_task(
                                self._promote_item(item, tier, target_tier)
                            )
                        
                        # Queue prefetch candidates
                        if self.config.optimization.prefetch_enabled:
                            asyncio.create_task(self._queue_prefetch(key))
                        
                        return item.value
                
                # Not found in any tier
                latency_ms = (time.time() - start_time) * 1000
                await self.metrics.record_access(
                    key=key,
                    tier=None,
                    hit=False,
                    latency_ms=latency_ms
                )
                
                return default
                
            except Exception as e:
                await self.metrics.record_operation(
                    operation="get",
                    success=False,
                    latency_ms=(time.time() - start_time) * 1000,
                    error=str(e)
                )
                
                if MemoryExceptionHandler.is_retryable(e):
                    # Retry once for retryable errors
                    await asyncio.sleep(0.1)
                    return await self.get(key, default)
                
                raise
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        tier_hint: Optional[MemoryTier] = None
    ) -> bool:
        """
        Store a value in memory.
        
        Automatically determines the best tier based on value characteristics
        and access patterns, unless a tier hint is provided.
        """
        if not key:
            raise MemoryValidationError(
                validation_type="key",
                field="key",
                value=key,
                constraint="Key cannot be empty"
            )
        
        start_time = time.time()
        
        async with self._operation_semaphore:
            try:
                # Create memory item
                item = self._create_memory_item(key, value, ttl_seconds)
                
                # Determine target tier
                if tier_hint and tier_hint in self._storages:
                    target_tier = tier_hint
                else:
                    target_tier = await self._determine_tier(item)
                
                # Store in target tier
                storage = self._storages[target_tier]
                success = await storage.set(item)
                
                if success:
                    # Record metrics
                    latency_ms = (time.time() - start_time) * 1000
                    await self.metrics.record_operation(
                        operation="set",
                        success=True,
                        latency_ms=latency_ms
                    )
                    
                    # Store in higher tiers if it's hot data
                    if target_tier in [MemoryTier.L3_POSTGRESQL, MemoryTier.L4_WEAVIATE]:
                        access_probability = await self.optimizer.predict_access(
                            key, [datetime.utcnow()]
                        )
                        if access_probability > 0.8:
                            # Also store in L2 for faster access
                            if MemoryTier.L2_SHARED_MEMORY in self._storages:
                                asyncio.create_task(
                                    self._storages[MemoryTier.L2_SHARED_MEMORY].set(item)
                                )
                
                return success
                
            except Exception as e:
                await self.metrics.record_operation(
                    operation="set",
                    success=False,
                    latency_ms=(time.time() - start_time) * 1000,
                    error=str(e)
                )
                raise
    
    async def delete(self, key: str) -> bool:
        """Delete a value from all tiers."""
        if not key:
            raise MemoryValidationError(
                validation_type="key",
                field="key",
                value=key,
                constraint="Key cannot be empty"
            )
        
        start_time = time.time()
        deleted = False
        
        async with self._operation_semaphore:
            try:
                # Delete from all tiers
                delete_tasks = []
                for tier, storage in self._storages.items():
                    delete_tasks.append(storage.delete(key))
                
                # Wait for all deletions
                results = await asyncio.gather(*delete_tasks, return_exceptions=True)
                
                # Check if deleted from any tier
                for result in results:
                    if isinstance(result, bool) and result:
                        deleted = True
                
                # Record metrics
                latency_ms = (time.time() - start_time) * 1000
                await self.metrics.record_operation(
                    operation="delete",
                    success=True,
                    latency_ms=latency_ms
                )
                
                return deleted
                
            except Exception as e:
                await self.metrics.record_operation(
                    operation="delete",
                    success=False,
                    latency_ms=(time.time() - start_time) * 1000,
                    error=str(e)
                )
                raise
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in any tier."""
        if not key:
            return False
        
        # Check tiers in order
        for tier in self._tier_hierarchy:
            if tier not in self._storages:
                continue
            
            if await self._storages[tier].exists(key):
                return True
        
        return False
    
    async def batch_operations(
        self,
        operations: List[MemoryOperation]
    ) -> List[MemoryResult]:
        """Execute multiple operations efficiently."""
        if not operations:
            return []
        
        start_time = time.time()
        results = []
        
        # Group operations by type for efficiency
        get_ops = []
        set_ops = []
        delete_ops = []
        
        for op in operations:
            if op.operation_type == "get":
                get_ops.append(op)
            elif op.operation_type == "set":
                set_ops.append(op)
            elif op.operation_type == "delete":
                delete_ops.append(op)
        
        try:
            # Process gets
            if get_ops:
                get_results = await self._batch_get(get_ops)
                results.extend(get_results)
            
            # Process sets
            if set_ops:
                set_results = await self._batch_set(set_ops)
                results.extend(set_results)
            
            # Process deletes
            if delete_ops:
                delete_results = await self._batch_delete(delete_ops)
                results.extend(delete_results)
            
            # Record metrics
            latency_ms = (time.time() - start_time) * 1000
            success_count = sum(1 for r in results if r.success)
            
            await self.metrics.record_operation(
                operation="batch",
                success=success_count == len(operations),
                latency_ms=latency_ms
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Batch operation failed: {str(e)}")
            # Return partial results
            return results
    
    async def search(
        self,
        pattern: Optional[str] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        semantic_query: Optional[str] = None,
        limit: int = 100
    ) -> List[MemoryItem]:
        """
        Search for items across all tiers.
        
        Supports pattern matching, metadata filtering, and semantic search.
        """
        start_time = time.time()
        all_results = []
        seen_keys = set()
        
        try:
            # Search each tier
            search_tasks = []
            
            for tier, storage in self._storages.items():
                # Skip semantic search for non-vector tiers
                if semantic_query and tier != MemoryTier.L4_WEAVIATE:
                    continue
                
                search_tasks.append(
                    storage.search(pattern, metadata_filter, limit)
                )
            
            # Gather results
            tier_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Merge results, avoiding duplicates
            for results in tier_results:
                if isinstance(results, list):
                    for item in results:
                        if item.key not in seen_keys:
                            all_results.append(item)
                            seen_keys.add(item.key)
                            
                            if len(all_results) >= limit:
                                break
                
                if len(all_results) >= limit:
                    break
            
            # Sort by access count (most accessed first)
            all_results.sort(key=lambda x: x.access_count, reverse=True)
            
            # Record metrics
            latency_ms = (time.time() - start_time) * 1000
            await self.metrics.record_operation(
                operation="search",
                success=True,
                latency_ms=latency_ms
            )
            
            return all_results[:limit]
            
        except Exception as e:
            await self.metrics.record_operation(
                operation="search",
                success=False,
                latency_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
            raise
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory system statistics."""
        stats = {
            "config": {
                "environment": self.config.environment.value,
                "total_tiers": len(self._storages),
                "optimization_enabled": self.config.optimization.enabled,
                "metrics_enabled": self.config.metrics.enabled,
            },
            "tiers": {},
            "metrics": await self.metrics.export_metrics(),
            "optimizer": await self.optimizer.get_stats() if hasattr(self.optimizer, 'get_stats') else {}
        }
        
        # Get stats from each tier
        for tier, storage in self._storages.items():
            tier_stats = await storage.get_stats()
            stats["tiers"][tier.value] = tier_stats
        
        # Calculate totals
        total_items = sum(
            s.get("total_items", 0) for s in stats["tiers"].values()
        )
        total_size = sum(
            s.get("total_size_bytes", 0) for s in stats["tiers"].values()
        )
        
        stats["totals"] = {
            "total_items": total_items,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
        }
        
        return stats
    
    async def optimize(self) -> Dict[str, int]:
        """Run optimization pass on all stored items."""
        logger.info("Running manual optimization pass...")
        
        promoted = 0
        demoted = 0
        
        try:
            # Analyze items in each tier
            for tier, storage in self._storages.items():
                # Skip top tier (can't promote) and bottom tier (can't demote)
                if tier == MemoryTier.L0_CPU_CACHE:
                    continue
                
                # Get sample of items
                items = await storage.search(limit=1000)
                
                # Analyze each item
                recommendations = await self.optimizer.analyze_access_patterns(items)
                
                for key, target_tier in recommendations.items():
                    if target_tier != tier:
                        # Find the item
                        item = next((i for i in items if i.key == key), None)
                        if item:
                            if target_tier.value < tier.value:  # Promotion
                                await self._promote_item(item, tier, target_tier)
                                promoted += 1
                            else:  # Demotion
                                await self._demote_item(item, tier, target_tier)
                                demoted += 1
            
            logger.info(f"Optimization complete: promoted={promoted}, demoted={demoted}")
            
            return {
                "promoted": promoted,
                "demoted": demoted
            }
            
        except Exception as e:
            logger.error(f"Optimization failed: {str(e)}")
            return {
                "promoted": promoted,
                "demoted": demoted
            }
    
    async def cleanup(self) -> int:
        """Clean up expired items from all tiers."""
        logger.info("Running cleanup...")
        
        total_cleaned = 0
        
        try:
            # Cleanup each tier
            cleanup_tasks = []
            for tier, storage in self._storages.items():
                cleanup_tasks.append(storage.cleanup_expired())
            
            # Wait for all cleanups
            results = await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            
            # Sum results
            for result in results:
                if isinstance(result, int):
                    total_cleaned += result
            
            logger.info(f"Cleanup complete: removed {total_cleaned} expired items")
            
            return total_cleaned
            
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            return total_cleaned
    
    async def close(self) -> None:
        """Gracefully shutdown the memory manager."""
        logger.info("Shutting down UnifiedMemoryManager...")
        
        # Signal shutdown to background tasks
        self._shutdown_event.set()
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Close all storages
        close_tasks = []
        for storage in self._storages.values():
            close_tasks.append(storage.close())
        
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)
        
        logger.info("UnifiedMemoryManager shutdown complete")
    
    # Private helper methods
    
    def _create_memory_item(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> MemoryItem:
        """Create a MemoryItem instance."""
        # Calculate checksum
        value_bytes = json.dumps(value, sort_keys=True).encode() if not isinstance(value, bytes) else value
        checksum = hashlib.sha256(value_bytes).hexdigest()
        
        # Use default TTL if not specified
        if ttl_seconds is None:
            ttl_seconds = self.config.default_ttl_seconds
        
        return MemoryItem(
            key=key,
            value=value,
            metadata={},
            tier=MemoryTier.L1_PROCESS_MEMORY,  # Default, will be updated
            created_at=datetime.utcnow(),
            accessed_at=datetime.utcnow(),
            access_count=0,
            size_bytes=len(value_bytes),
            ttl_seconds=ttl_seconds,
            checksum=checksum
        )
    
    async def _determine_tier(self, item: MemoryItem) -> MemoryTier:
        """Determine the best tier for an item based on its characteristics."""
        # Size-based tiering
        if item.size_bytes < 1024:  # < 1KB
            if MemoryTier.L1_PROCESS_MEMORY in self._storages:
                return MemoryTier.L1_PROCESS_MEMORY
        elif item.size_bytes < 1024 * 100:  # < 100KB
            if MemoryTier.L2_SHARED_MEMORY in self._storages:
                return MemoryTier.L2_SHARED_MEMORY
        elif item.size_bytes < 1024 * 1024:  # < 1MB
            if MemoryTier.L3_POSTGRESQL in self._storages:
                return MemoryTier.L3_POSTGRESQL
        
        # Default to lowest available tier
        for tier in reversed(self._tier_hierarchy):
            if tier in self._storages:
                return tier
        
        # Should never reach here
        return MemoryTier.L3_POSTGRESQL
    
    async def _promote_item(
        self,
        item: MemoryItem,
        from_tier: MemoryTier,
        to_tier: MemoryTier
    ) -> None:
        """Promote an item to a faster tier."""
        try:
            logger.debug(f"Promoting {item.key} from {from_tier.value} to {to_tier.value}")
            
            # Store in new tier
            if to_tier in self._storages:
                await self._storages[to_tier].set(item)
                
                # Delete from old tier (optional, could keep copies)
                if self.config.optimization.get("delete_on_promotion", True):
                    await self._storages[from_tier].delete(item.key)
                
                # Record metric
                await self.metrics.record_tier_migration(
                    key=item.key,
                    from_tier=from_tier,
                    to_tier=to_tier,
                    reason="promotion"
                )
                
        except Exception as e:
            logger.error(f"Failed to promote item {item.key}: {str(e)}")
    
    async def _demote_item(
        self,
        item: MemoryItem,
        from_tier: MemoryTier,
        to_tier: MemoryTier
    ) -> None:
        """Demote an item to a slower tier."""
        try:
            logger.debug(f"Demoting {item.key} from {from_tier.value} to {to_tier.value}")
            
            # Store in new tier
            if to_tier in self._storages:
                await self._storages[to_tier].set(item)
                
                # Delete from old tier
                await self._storages[from_tier].delete(item.key)
                
                # Record metric
                await self.metrics.record_tier_migration(
                    key=item.key,
                    from_tier=from_tier,
                    to_tier=to_tier,
                    reason="demotion"
                )
                
        except Exception as e:
            logger.error(f"Failed to demote item {item.key}: {str(e)}")
    
    async def _queue_prefetch(self, key: str) -> None:
        """Queue related keys for prefetching."""
        try:
            candidates = await self.optimizer.get_prefetch_candidates(
                key,
                limit=self.config.optimization.prefetch_limit
            )
            
            for candidate in candidates:
                if not self._prefetch_queue.full():
                    await self._prefetch_queue.put(candidate)
                    
        except Exception as e:
            logger.debug(f"Failed to queue prefetch for {key}: {str(e)}")
    
    async def _batch_get(
        self,
        operations: List[MemoryOperation]
    ) -> List[MemoryResult]:
        """Process batch get operations."""
        results = []
        keys = [op.key for op in operations]
        
        # Try each tier
        for tier in self._tier_hierarchy:
            if tier not in self._storages:
                continue
            
            # Batch get from tier
            tier_results = await self._storages[tier].get_batch(keys)
            
            # Process results
            for op in operations:
                if op.key in tier_results and tier_results[op.key]:
                    item = tier_results[op.key]
                    results.append(MemoryResult(
                        success=True,
                        value=item.value,
                        tier_accessed=tier
                    ))
                    # Remove from keys to search
                    keys.remove(op.key)
        
        # Add not found results
        for key in keys:
            results.append(MemoryResult(
                success=False,
                error="Not found"
            ))
        
        return results
    
    async def _batch_set(
        self,
        operations: List[MemoryOperation]
    ) -> List[MemoryResult]:
        """Process batch set operations."""
        results = []
        
        # Create items
        items = []
        for op in operations:
            item = self._create_memory_item(
                op.key,
                op.value,
                op.ttl_seconds
            )
            items.append(item)
        
        # Determine tiers
        tier_items = defaultdict(list)
        for i, item in enumerate(items):
            tier = operations[i].tier_hint or await self._determine_tier(item)
            tier_items[tier].append(item)
        
        # Batch set to each tier
        for tier, tier_batch in tier_items.items():
            if tier in self._storages:
                set_results = await self._storages[tier].set_batch(tier_batch)
                
                for item in tier_batch:
                    results.append(MemoryResult(
                        success=set_results.get(item.key, False),
                        tier_accessed=tier
                    ))
        
        return results
    
    async def _batch_delete(
        self,
        operations: List[MemoryOperation]
    ) -> List[MemoryResult]:
        """Process batch delete operations."""
        results = []
        
        for op in operations:
            deleted = await self.delete(op.key)
            results.append(MemoryResult(success=deleted))
        
        return results
    
    # Background task loops
    
    async def _optimization_loop(self) -> None:
        """Background task for continuous optimization."""
        interval = self.config.optimization.optimization_interval_seconds
        
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(interval)
                
                if not self._shutdown_event.is_set():
                    await self.optimize()
                    
            except Exception as e:
                logger.error(f"Optimization loop error: {str(e)}")
    
    async def _cleanup_loop(self) -> None:
        """Background task for cleaning expired items."""
        interval = self.config.optimization.cleanup_interval_seconds
        
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(interval)
                
                if not self._shutdown_event.is_set():
                    await self.cleanup()
                    
            except Exception as e:
                logger.error(f"Cleanup loop error: {str(e)}")
    
    async def _prefetch_loop(self) -> None:
        """Background task for prefetching items."""
        while not self._shutdown_event.is_set():
            try:
                # Get next prefetch candidate
                key = await asyncio.wait_for(
                    self._prefetch_queue.get(),
                    timeout=1.0
                )
                
                # Check if already cached in fast tier
                if not await self._is_in_fast_tier(key):
                    # Fetch and promote
                    value = await self.get(key)
                    if value is not None:
                        logger.debug(f"Prefetched {key}")
                        
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.debug(f"Prefetch loop error: {str(e)}")
    
    async def _metrics_export_loop(self) -> None:
        """Background task for exporting metrics."""
        interval = 60  # Export every minute
        
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(interval)
                
                if not self._shutdown_event.is_set():
                    metrics = await self.metrics.export_metrics()
                    logger.debug(f"Exported metrics: {metrics}")
                    
            except Exception as e:
                logger.error(f"Metrics export loop error: {str(e)}")
    
    async def _is_in_fast_tier(self, key: str) -> bool:
        """Check if key exists in a fast tier (L0-L2)."""
        fast_tiers = [
            MemoryTier.L0_CPU_CACHE,
            MemoryTier.L1_PROCESS_MEMORY,
            MemoryTier.L2_SHARED_MEMORY
        ]