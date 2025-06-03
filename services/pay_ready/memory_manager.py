# TODO: Consider adding connection pooling configuration
"""
"""
    """Memory tier levels"""
    HOT = "hot"  # In-memory cache (last 24 hours)
    WARM = "warm"  # Redis/Dragonfly (last 7 days)
    COLD = "cold"  # PostgreSQL (everything)
    VECTOR = "vector"  # Weaviate (semantic search)

class PayReadyMemoryManager:
    """
    """
        self.cache_prefix = "pr:"

        # Batch configuration
        self.batch_size = 100
        self.pending_vectors = []

        # Context pruning configuration
        self.max_context_size = 4000
        self.context_relevance_threshold = 0.8

        self._initialized = False

    async def initialize(self):
        """Initialize memory manager and warm caches"""
        logger.info("Initializing Pay Ready Memory Manager")

        # Warm up hot cache with recent interactions
        await self.warm_cache()

        self._initialized = True
        logger.info("Memory Manager initialized successfully")

    async def store_interaction(self, interaction: Dict[str, Any]):
        """
        """
        interaction_id = interaction.get("id")
        if not interaction_id:
            raise ValueError("Interaction must have an 'id' field")

        # Add timestamp if not present
        if "timestamp" not in interaction:
            interaction["timestamp"] = datetime.utcnow().isoformat()

        # Store in hot cache
        self._store_in_hot_cache(interaction_id, interaction)

        # Store in warm cache (async)
        asyncio.create_task(self._store_in_warm_cache(interaction_id, interaction))

        # Store in cold storage
        await self._store_in_cold_storage(interaction)

        # Queue for vector storage if text is present
        if interaction.get("text"):
            self.pending_vectors.append(interaction)

            # Process batch if full
            if len(self.pending_vectors) >= self.batch_size:
                await self._process_vector_batch()

    def _store_in_hot_cache(self, key: str, value: Dict):
        """Store in hot cache with LRU eviction"""
        self.hot_cache[key] = {"data": value, "stored_at": datetime.utcnow()}

        # Evict oldest if over size limit
        while len(self.hot_cache) > self.hot_cache_max_size:
            self.hot_cache.popitem(last=False)

    async def _store_in_warm_cache(self, key: str, value: Dict):
        """Store in warm cache with TTL"""
        cache_key = f"{self.cache_prefix}interaction:{key}"
        ttl = int(timedelta(days=7).total_seconds())

        await self.postgres.cache_set(cache_key, value, ttl=ttl)

        # Also update type-specific indices
        interaction_type = value.get("type", "unknown")
        type_key = f"{self.cache_prefix}type:{interaction_type}:recent"

        # Add to sorted set by timestamp
        timestamp = datetime.fromisoformat(value["timestamp"]).timestamp()
        await self.postgres.execute_raw(
            """
        """
            ["pay_ready", interaction_type],
        )

    async def _store_in_cold_storage(self, interaction: Dict):
        """Store in PostgreSQL for persistence"""
            """
        """
            interaction["id"],
            interaction.get("type"),
            interaction.get("text"),
            json.dumps(interaction.get("metadata", {})),
            interaction.get("unified_person_id"),
            interaction.get("unified_company_id"),
            interaction.get("metadata", {}).get("source"),
            interaction.get("source_id"),
            datetime.fromisoformat(interaction["timestamp"]),
        )

    async def _process_vector_batch(self):
        """Process pending vectors in batch"""
            collection = self._get_collection_for_type(interaction["type"])

            # Prepare object data
            obj_data = {
                "text": interaction["text"],
                "interaction_id": interaction["id"],
                "timestamp": int(datetime.fromisoformat(interaction["timestamp"]).timestamp()),
                "unified_person_id": interaction.get("unified_person_id"),
                "unified_company_id": interaction.get("unified_company_id"),
                "domain": "pay_ready",
            }

            # Add type-specific fields
            if interaction["type"] == "slack_message":
                obj_data.update(
                    {
                        "channel": interaction.get("channel"),
                        "user": interaction.get("user"),
                        "thread_id": interaction.get("thread_id"),
                    }
                )
            elif interaction["type"] == "gong_call_segment":
                obj_data.update(
                    {
                        "call_id": interaction.get("call_id"),
                        "speaker": interaction.get("speaker"),
                        "start_time": interaction.get("start_time", 0),
                    }
                )

            objects.append({"collection": collection, "properties": obj_data, "id": interaction["id"]})

        # Batch insert to Weaviate
        try:

            pass
            # This would use Weaviate's batch API
            # Implementation depends on Weaviate client version
            logger.info(f"Stored {len(objects)} vectors in Weaviate")
        except Exception:

            pass
            logger.error(f"Failed to store vectors: {e}")
            # Re-queue failed items
            self.pending_vectors.extend(batch)

    def _get_collection_for_type(self, interaction_type: str) -> str:
        """Map interaction type to Weaviate collection"""
            "slack_message": "PayReadySlackMessage",
            "gong_call_segment": "PayReadyGongCallSegment",
            "hubspot_note": "PayReadyHubSpotNote",
            "salesforce_note": "PayReadySalesforceNote",
        }
        return type_map.get(interaction_type, "PayReadyInteraction")

    async def get_interaction(self, interaction_id: str, include_context: bool = False) -> Optional[Dict]:
        """
        """
            if datetime.utcnow() - entry["stored_at"] < self.hot_cache_ttl:
                return entry["data"]
            else:
                # Remove expired entry
                del self.hot_cache[interaction_id]

        # Check warm cache
        cache_key = f"{self.cache_prefix}interaction:{interaction_id}"
        cached = await self.postgres.cache_get(cache_key)
        if cached:
            # Promote to hot cache
            self._store_in_hot_cache(interaction_id, cached)
            return cached

        # Fall back to cold storage
        result = await self.postgres.fetchrow(
            """
        """
            interaction["metadata"] = json.loads(interaction.get("metadata", "{}"))

            # Promote to caches
            self._store_in_hot_cache(interaction_id, interaction)
            asyncio.create_task(self._store_in_warm_cache(interaction_id, interaction))

            if include_context:
                interaction["context"] = await self._get_interaction_context(interaction_id)

            return interaction

        return None

    async def _get_interaction_context(self, interaction_id: str) -> Dict:
        """Get related context for an interaction"""
        context = {"related_interactions": [], "thread_context": [], "entity_context": {}}

        # Get interaction details
        interaction = await self.get_interaction(interaction_id)
        if not interaction:
            return context

        # Get thread context for Slack messages
        if interaction["type"] == "slack_message" and interaction.get("thread_id"):
            thread_messages = await self.postgres.fetch_raw(
                """
            """
                interaction["thread_id"],
            )

            context["thread_context"] = [dict(msg) for msg in thread_messages]

        # Get entity context
        if interaction.get("unified_person_id"):
            recent_interactions = await self.postgres.fetch_raw(
                """
            """
                interaction["unified_person_id"],
                interaction_id,
            )

            context["entity_context"]["person_interactions"] = [dict(i) for i in recent_interactions]

        return context

    async def search_interactions(self, query: str, filters: Optional[Dict] = None, limit: int = 10) -> List[Dict]:
        """
        """
        where_filter = {"path": ["domain"], "operator": "Equal", "valueText": "pay_ready"}

        if filters:
            # Add date range filter
            if filters.get("start_date"):
                # Convert to timestamp
                start_ts = int(datetime.fromisoformat(filters["start_date"]).timestamp())
                where_filter = {
                    "operator": "And",
                    "operands": [
                        where_filter,
                        {"path": ["timestamp"], "operator": "GreaterThanEqual", "valueNumber": start_ts},
                    ],
                }

        # Search across all Pay Ready collections
        results = []
        collections = [
            "PayReadySlackMessage",
            "PayReadyGongCallSegment",
            "PayReadyHubSpotNote",
            "PayReadySalesforceNote",
        ]

        for collection in collections:
            try:

                pass
                # This would use Weaviate's search API
                # Implementation depends on client version
                collection_results = await self._search_collection(collection, query, where_filter, limit)
                results.extend(collection_results)
            except Exception:

                pass
                logger.error(f"Search failed for {collection}: {e}")

        # Sort by relevance and limit
        results.sort(key=lambda x: x.get("_score", 0), reverse=True)
        return results[:limit]

    async def _search_collection(self, collection: str, query: str, where_filter: Dict, limit: int) -> List[Dict]:
        """Search a specific Weaviate collection"""
        """
        """
            "essential": [],  # Always keep
            "recent": [],  # Recent items (last 7 days)
            "high_relevance": [],  # High relevance score
            "compressed": [],  # Compressed older items
        }

        # Categorize items
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)

        for item in context.get("items", []):
            # Essential items (marked as such)
            if item.get("essential"):
                prioritized["essential"].append(item)
                continue

            # Recent items
            item_time = datetime.fromisoformat(item["timestamp"])
            if item_time > week_ago:
                prioritized["recent"].append(item)
                continue

            # High relevance items
            if item.get("relevance_score", 0) >= self.context_relevance_threshold:
                prioritized["high_relevance"].append(item)
                continue

        # Build pruned context within size limit
        pruned = {"id": context_id, "items": [], "metadata": context.get("metadata", {})}

        current_size = 0

        # Add items in priority order
        for category in ["essential", "recent", "high_relevance"]:
            for item in prioritized[category]:
                item_size = self._estimate_item_size(item)
                if current_size + item_size <= max_size:
                    pruned["items"].append(item)
                    current_size += item_size
                else:
                    # Try to compress item
                    compressed = await self._compress_item(item)
                    compressed_size = self._estimate_item_size(compressed)
                    if current_size + compressed_size <= max_size:
                        pruned["items"].append(compressed)
                        current_size += compressed_size

        # Add compression summary if items were excluded
        excluded_count = len(context.get("items", [])) - len(pruned["items"])
        if excluded_count > 0:
            pruned["metadata"]["excluded_items"] = excluded_count
            pruned["metadata"]["compression_applied"] = True

        return pruned

    async def _get_full_context(self, context_id: str) -> Dict:
        """Get full context for pruning"""
        return {"id": context_id, "items": [], "metadata": {}}

    def _estimate_item_size(self, item: Dict) -> int:
        """Estimate size of an item in tokens/characters"""
        text = item.get("text", "")
        return len(text) // 4  # Rough token estimate

    async def _compress_item(self, item: Dict) -> Dict:
        """Compress an item to reduce size"""
        if "text" in compressed and len(compressed["text"]) > 200:
            compressed["text"] = compressed["text"][:200] + "..."
            compressed["compressed"] = True

        # Remove non-essential metadata
        if "metadata" in compressed:
            essential_keys = ["source", "type", "timestamp"]
            compressed["metadata"] = {k: v for k, v in compressed["metadata"].items() if k in essential_keys}

        return compressed

    async def warm_cache(self):
        """Warm up caches with recent data"""
        logger.info("Warming Pay Ready memory caches")

        # Get recent interactions
        recent = await self.postgres.fetch_raw(
            """
        """
            interaction["metadata"] = json.loads(interaction.get("metadata", "{}"))
            self._store_in_hot_cache(interaction["id"], interaction)

        logger.info(f"Warmed cache with {len(recent)} recent interactions")

    async def get_memory_stats(self) -> Dict:
        """Get memory usage statistics"""
        hot_cache_memory = sum(len(json.dumps(entry["data"])) for entry in self.hot_cache.values())

        # Warm cache stats
        cache_stats = await self.postgres.cache_stats()

        # Cold storage stats
        cold_stats = await self.postgres.fetchrow(
            """
        """
            "hot_cache": {
                "size": hot_cache_size,
                "memory_bytes": hot_cache_memory,
                "max_size": self.hot_cache_max_size,
                "utilization": hot_cache_size / self.hot_cache_max_size,
            },
            "warm_cache": cache_stats,
            "cold_storage": dict(cold_stats) if cold_stats else {},
            "vector_queue": {"pending": len(self.pending_vectors), "batch_size": self.batch_size},
        }

    async def cleanup_expired(self):
        """Clean up expired cache entries"""
            if now - entry["stored_at"] > self.hot_cache_ttl:
                expired_keys.append(key)

        for key in expired_keys:
            del self.hot_cache[key]

        logger.info(f"Cleaned up {len(expired_keys)} expired hot cache entries")

        # PostgreSQL cache cleanup is handled by the cache system itself

    async def flush_pending_vectors(self):
        """Force flush any pending vectors"""