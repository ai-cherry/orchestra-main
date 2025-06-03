# TODO: Consider adding connection pooling configuration
"""
"""
    """
    """
        """
        """
            f"Initialized UnifiedMemoryManager with {len(self._tier_hierarchy)} tiers"
        )
    
    async def initialize(self) -> None:
        """Initialize all components and start background tasks."""
        logger.info("Initializing UnifiedMemoryManager...")
        
        try:

        
            pass
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
            
        except Exception:

            
            pass
            logger.error(f"Failed to initialize memory manager: {str(e)}")
            await self.close()
            raise
    
    async def _initialize_storages(self) -> Dict[MemoryTier, IMemoryStorage]:
        """Initialize all storage backends."""
                logger.info(f"Tier {tier.value} is disabled, skipping initialization")
                continue
            
            try:

            
                pass
                # Create storage instance
                storage = MemoryStorageFactory.create_storage(tier, self.config)
                await storage.initialize()
                storages[tier] = storage
                logger.info(f"Initialized storage for tier {tier.value}")
                
            except Exception:

                
                pass
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
        logger.info(f"Started {len(self._background_tasks)} background tasks")
    
    async def get(
        self,
        key: str,
        default: Optional[Any] = None
    ) -> Optional[Any]:
        """
        """
                validation_type="key",
                field="key",
                value=key,
                constraint="Key cannot be empty"
            )
        
        start_time = time.time()
        
        async with self._operation_semaphore:
            try:

                pass
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
                
            except Exception:

                
                pass
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
        """
                validation_type="key",
                field="key",
                value=key,
                constraint="Key cannot be empty"
            )
        
        start_time = time.time()
        
        async with self._operation_semaphore:
            try:

                pass
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
                
            except Exception:

                
                pass
                await self.metrics.record_operation(
                    operation="set",
                    success=False,
                    latency_ms=(time.time() - start_time) * 1000,
                    error=str(e)
                )
                raise
    
    async def delete(self, key: str) -> bool:
        """Delete a value from all tiers."""
                validation_type="key",
                field="key",
                value=key,
                constraint="Key cannot be empty"
            )
        
        start_time = time.time()
        deleted = False
        
        async with self._operation_semaphore:
            try:

                pass
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
                
            except Exception:

                
                pass
                await self.metrics.record_operation(
                    operation="delete",
                    success=False,
                    latency_ms=(time.time() - start_time) * 1000,
                    error=str(e)
                )
                raise
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in any tier."""
        """Execute multiple operations efficiently."""
            if op.operation_type == "get":
                get_ops.append(op)
            elif op.operation_type == "set":
                set_ops.append(op)
            elif op.operation_type == "delete":
                delete_ops.append(op)
        
        try:

        
            pass
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
            
        except Exception:

            
            pass
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
        """
                operation="search",
                success=True,
                latency_ms=latency_ms
            )
            
            return all_results[:limit]
            
        except Exception:

            
            pass
            await self.metrics.record_operation(
                operation="search",
                success=False,
                latency_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
            raise
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory system statistics."""
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

        
            pass
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
            
        except Exception:

            
            pass
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

        
            pass
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
            
        except Exception:

            
            pass
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
        # TODO: Consider using list comprehension for better performance

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
        """Determine the best tier for an item based on its characteristics."""
        """Promote an item to a faster tier."""
            
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
                
        except Exception:

                
            pass
            logger.error(f"Failed to promote item {item.key}: {str(e)}")
    
    async def _demote_item(
        self,
        item: MemoryItem,
        from_tier: MemoryTier,
        to_tier: MemoryTier
    ) -> None:
        """Demote an item to a slower tier."""
            
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
                
        except Exception:

                
            pass
            logger.error(f"Failed to demote item {item.key}: {str(e)}")
    
    async def _queue_prefetch(self, key: str) -> None:
        """Queue related keys for prefetching."""
    
    async def _batch_get(
        self,
        operations: List[MemoryOperation]
    ) -> List[MemoryResult]:
        """Process batch get operations."""
                error="Not found"
            ))
        
        return results
    
    async def _batch_set(
        self,
        operations: List[MemoryOperation]
    ) -> List[MemoryResult]:
        """Process batch set operations."""
        """Process batch delete operations."""
        """Background task for continuous optimization."""
                logger.error(f"Optimization loop error: {str(e)}")
    
    async def _cleanup_loop(self) -> None:
        """Background task for cleaning expired items."""
                logger.error(f"Cleanup loop error: {str(e)}")
    
    async def _prefetch_loop(self) -> None:
        """Background task for prefetching items."""
                        
            except Exception:

                        
                pass
                continue
            except Exception:

                pass
    
    async def _metrics_export_loop(self) -> None:
        """Background task for exporting metrics."""
                    
            except Exception:

                    
                pass
                logger.error(f"Metrics export loop error: {str(e)}")
    
    async def _is_in_fast_tier(self, key: str) -> bool:
        """Check if key exists in a fast tier (L0-L2)."""