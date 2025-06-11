"""
"""
    """
    """
        """
        """
        self.max_cache_items = self.config.get("max_cache_items", 1000)  # Limit cache size
        self.cache_ttl = self.config.get("cache_ttl", 300)  # 5 minutes default
        self.cache_last_cleanup = time.time()
        self.cache_cleanup_interval = 60  # Clean expired items every minute

        # Thread safety
        self._lock = threading.RLock()  # For thread-safe operations
        self._initialized = False

        # Performance monitoring
        self.perf = performance_monitor or get_performance_monitor()

        # Stats tracking
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "operations": 0,
            "errors": 0,
            "store_count": 0,
            "retrieve_count": 0,
            "delete_count": 0,
            "search_count": 0,
        }

        logger.info(
            "Initialized PerformanceMemoryManager with cache_ttl=%s seconds, max_items=%s",
            self.cache_ttl,
            self.max_cache_items,
        )

    async def initialize(self) -> bool:
        """
        """
        logger.info("Initializing PerformanceMemoryManager")
        try:

            pass
            # Initialize the underlying storage
            await self.storage.initialize()

            # Initialize the adapter (this is a synchronous operation but we keep the method async for interface compatibility)
            result = self.storage_adapter.initialize()

            if result:
                self._initialized = True
                logger.info("PerformanceMemoryManager initialized successfully")
            else:
                logger.error("Failed to initialize storage backend")

            duration = time.time() - start_time
            self.perf.record_operation("memory_manager.initialize", duration)
            return result
        except Exception:

            pass
            logger.error("Error initializing memory manager: %s", str(e))
            duration = time.time() - start_time
            self.perf.record_operation("memory_manager.initialize.error", duration)
            return False

    async def _check_initialized(self) -> bool:
        """
        """
                logger.error("Failed to initialize on demand: %s", str(e))
                return False
        return True

    async def store(self, key: str, content: Any, tool_name: str, ttl_seconds: int = 3600) -> bool:
        """
        """
        self.stats["operations"] += 1
        self.stats["store_count"] += 1

        if not await self._check_initialized():
            logger.error("Cannot store: memory manager not initialized")
            self.stats["errors"] += 1
            return False


        try:


            pass
            # Create metadata
            metadata = MemoryMetadata(
                source_tool=tool_name,
                last_modified=time.time(),
                access_count=0,
                context_relevance=1.0,  # Assume maximum relevance for performance
                last_accessed=time.time(),
                version=1,
                sync_status={},
                content_hash=None,  # Will be computed during save
            )

            # Create memory entry with performance-optimized defaults
            entry = MemoryEntry(
                memory_type=MemoryType.SHARED,
                scope=MemoryScope.SESSION,
                priority=1,  # High priority
                compression_level=CompressionLevel.NONE,  # No compression for speed
                ttl_seconds=ttl_seconds,
                content=content,
                metadata=metadata,
                storage_tier=StorageTier.HOT,
            )

            # Update local cache with thread safety
            with self._lock:
                # Check if we need to evict items from cache
                if len(self.cache) >= self.max_cache_items:
                    self._evict_cache_items()

                # Add to cache
                self.cache[key] = {
                    "content": content,
                    "expires_at": time.time() + min(ttl_seconds, self.cache_ttl),
                }

                # Clean cache if needed
                self._clean_cache_if_needed()

            # Store in persistent storage
            try:

                pass
                # Store using the synchronous adapter
                result = self.storage_adapter.store(key, entry)
                duration = time.time() - start_time
                self.perf.record_operation("memory_manager.store", duration)
                return result
            except Exception:

                pass
                logger.error("Failed to save to storage: %s", str(e))
                self.stats["errors"] += 1
                duration = time.time() - start_time
                self.perf.record_operation("memory_manager.store.error", duration)
                return False

        except Exception:


            pass
            logger.error("Error storing content: %s", str(e))
            self.stats["errors"] += 1
            duration = time.time() - start_time
            self.perf.record_operation("memory_manager.store.error", duration)
            return False

    async def retrieve(self, key: str) -> Optional[Any]:
        """
        """
        self.stats["operations"] += 1
        self.stats["retrieve_count"] += 1

        if not await self._check_initialized():
            logger.error("Cannot retrieve: memory manager not initialized")
            self.stats["errors"] += 1
            return None


        try:


            pass
            # Check local cache first
            with self._lock:
                if key in self.cache:
                    cache_item = self.cache[key]
                    if cache_item["expires_at"] > time.time():
                        self.stats["cache_hits"] += 1
                        return cache_item["content"]
                    else:
                        # Expired item, remove from cache
                        del self.cache[key]
                        self.stats["cache_misses"] += 1

            # Not in cache, retrieve from storage
            self.stats["cache_misses"] += 1

            try:


                pass
                # Use synchronous adapter to get the content
                entry = self.storage_adapter.retrieve(key)
                if entry is None:
                    duration = time.time() - start_time
                    self.perf.record_operation("memory_manager.retrieve.miss", duration)
                    return None

                # Update cache
                with self._lock:
                    # Check if entry has content field (it should be a MemoryEntry)
                    if hasattr(entry, "content"):
                        content = entry.content
                        ttl = getattr(entry, "ttl_seconds", self.cache_ttl)
                    else:
                        # If it's not a MemoryEntry, use it directly
                        content = entry
                        ttl = self.cache_ttl

                    self.cache[key] = {
                        "content": content,
                        "expires_at": time.time() + min(ttl, self.cache_ttl),
                    }

                duration = time.time() - start_time
                self.perf.record_operation("memory_manager.retrieve.hit", duration)
                return content
            except Exception:

                pass
                logger.error("Error retrieving from storage: %s", str(e))
                self.stats["errors"] += 1
                duration = time.time() - start_time
                self.perf.record_operation("memory_manager.retrieve.error", duration)
                return None

        except Exception:


            pass
            logger.error("Error retrieving content: %s", str(e))
            self.stats["errors"] += 1
            duration = time.time() - start_time
            self.perf.record_operation("memory_manager.retrieve.error", duration)
            return None

    async def delete(self, key: str) -> bool:
        """
        """
        self.stats["operations"] += 1
        self.stats["delete_count"] += 1

        if not await self._check_initialized():
            logger.error("Cannot delete: memory manager not initialized")
            self.stats["errors"] += 1
            return False


        try:


            pass
            # Remove from cache
            with self._lock:
                if key in self.cache:
                    del self.cache[key]

            # Remove from storage
            try:

                pass
                result = self.storage_adapter.delete(key)
                duration = time.time() - start_time
                self.perf.record_operation("memory_manager.delete", duration)
                return result
            except Exception:

                pass
                logger.error("Error deleting from storage: %s", str(e))
                self.stats["errors"] += 1
                duration = time.time() - start_time
                self.perf.record_operation("memory_manager.delete.error", duration)
                return False

        except Exception:


            pass
            logger.error("Error deleting content: %s", str(e))
            self.stats["errors"] += 1
            duration = time.time() - start_time
            self.perf.record_operation("memory_manager.delete.error", duration)
            return False

    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        """
        self.stats["operations"] += 1
        self.stats["search_count"] += 1

        if not await self._check_initialized():
            logger.error("Cannot search: memory manager not initialized")
            self.stats["errors"] += 1
            return []


        try:


            pass
            # Use the storage adapter's search capabilities
            try:

                pass
                # Leverage the optimized search in our storage
                results = self.storage_adapter.search(query, limit=limit)

                # Format the results consistently
                formatted_results = []
                for item in results:
                    # Extract the key and content
                    key = item.get("_key", "unknown")

                    # Handle different result formats
                    if "value" in item:
                        content = item["value"]
                    elif "_key" in item:
                        # Remove the key from the content
                        content_dict = dict(item)
                        content_dict.pop("_key", None)
                        content = content_dict
                    else:
                        content = item

                    formatted_results.append(
                        {
                            "key": key,
                            "content": content,
                            "score": 1.0,  # Simple relevance score for now
                        }
                    )

                duration = time.time() - start_time
                self.perf.record_operation("memory_manager.search", duration)
                return formatted_results

            except Exception:


                pass
                logger.error("Error using storage search: %s", str(e))
                self.stats["errors"] += 1
                duration = time.time() - start_time
                self.perf.record_operation("memory_manager.search.error", duration)
                return []

        except Exception:


            pass
            logger.error("Error searching content: %s", str(e))
            self.stats["errors"] += 1
            duration = time.time() - start_time
            self.perf.record_operation("memory_manager.search.error", duration)
            return []

    async def health_check(self) -> Dict[str, Any]:
        """
        """

        try:


            pass
            if not self._initialized:
                return {
                    "status": "not_initialized",
                    "cache_items": len(self.cache),
                    "storage": {"status": "unknown"},
                    "stats": self.stats,
                }

            try:


                pass
                # Use the synchronous adapter
                storage_health = self.storage_adapter.get_health()
            except Exception:

                pass
                logger.error("Error checking storage health: %s", str(e))
                storage_health = {"status": "error", "error": str(e)}

            result = {
                "status": ("healthy" if storage_health.get("status") == "healthy" else "degraded"),
                "cache_items": len(self.cache),
                "cache_max_items": self.max_cache_items,
                "cache_usage_percent": (
                    (len(self.cache) / self.max_cache_items) * 100 if self.max_cache_items > 0 else 0
                ),
                "storage": storage_health,
                "stats": self.stats,
            }

            duration = time.time() - start_time
            self.perf.record_operation("memory_manager.health_check", duration)
            return result

        except Exception:


            pass
            logger.error("Error performing health check: %s", str(e))
            duration = time.time() - start_time
            self.perf.record_operation("memory_manager.health_check.error", duration)
            return {"status": "error", "error": str(e), "stats": self.stats}

    def _evict_cache_items(self) -> None:
        """
        """

        # Sort keys by expiration time (oldest first)
        sorted_keys = sorted(self.cache.keys(), key=lambda k: self.cache[k].get("expires_at", 0))

        # Remove oldest items
        for key in sorted_keys[:items_to_remove]:
            del self.cache[key]


    def _clean_cache_if_needed(self) -> None:
        """
        """
            keys_to_remove = []
            for key, item in self.cache.items():
                if item["expires_at"] <= current_time:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self.cache[key]

            self.cache_last_cleanup = current_time
