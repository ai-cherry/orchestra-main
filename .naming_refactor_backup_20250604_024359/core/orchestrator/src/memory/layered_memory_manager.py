# TODO: Consider adding connection pooling configuration
"""
"""
    """
    """
        """Initialize the layered memory manager."""
        import os
        self.redis_url = redis_url or os.environ.get("REDIS_URL", f"redis://localhost:6379")  # Standard Redis config
        self.redis_pool = None  # Will be initialized in connect()

        # Initialize MongoDB for mid-term and long-term memory
        self.mongodb_client = mongodb.Client(project=self.project_id)

        # Initialize Vector Search for semantic search
        self.vector_index_endpoint = vector_index_endpoint
        self.vector_deployed_index_id = vector_deployed_index_id
        self.vector_search_initialized = False

        # Memory expiration settings (in seconds)
        self.short_term_expiry = 60 * 60  # 1 hour
        self.mid_term_expiry = 60 * 60 * 24 * 7  # 1 week
        # Long-term memory doesn't expire

    async def connect(self):
        """Connect to Redis and initialize Vector Search."""
        """Disconnect from Redis."""
        """
        """
                raise ValueError("Embedding is required for LONG_TERM memory")

            # Store in MongoDB without expiration
            self._store_in_mongodb(memory_entry)

        return memory_id

    async def retrieve_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """
        """
        """
        """
        """
        """
        """Store a memory in Redis with expiration."""
        key = f"memory:{memory.id}"
        value = memory.model_dump_json()

        # Store in Redis with expiration
        await self.redis_pool.set(key, value, ex=self.short_term_expiry)

        # Add to agent's memory set
        await self.redis_pool.sadd(f"agent:{self.agent_id}:memories", memory.id)

        # Add to conversation's memory set if conversation_id is provided
        if self.conversation_id:
            await self.redis_pool.sadd(f"conversation:{self.conversation_id}:memories", memory.id)

    async def _retrieve_from_redis(self, memory_id: str) -> Optional[MemoryEntry]:
        """Retrieve a memory from Redis."""
        key = f"memory:{memory_id}"
        value = await self.redis_pool.get(key)

        if value:
            return MemoryEntry.model_validate_json(value)

        return None

    async def _search_in_redis(
        self, query: str, limit: int, metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[MemorySearchResult]:
        """
        """
            memory_ids = await self.redis_pool.smembers(f"conversation:{self.conversation_id}:memories")
        else:
            memory_ids = await self.redis_pool.smembers(f"agent:{self.agent_id}:memories")

        # Retrieve each memory and check if it matches the query
        for memory_id in memory_ids:
            memory = await self._retrieve_from_redis(memory_id)
            if not memory:
                continue

            # Apply metadata filter if provided
            if metadata_filter and not self._matches_metadata_filter(memory.metadata, metadata_filter):
                continue

            # Simple text matching (could be improved)
            if query.lower() in memory.content.lower():
                # Calculate a simple relevance score based on string matching
                relevance = self._calculate_text_relevance(query, memory.content)

                results.append(
                    MemorySearchResult(
                        memory=memory,
                        relevance=relevance,
                    )
                )

        # Sort by relevance and limit results
        results.sort(key=lambda x: x.relevance, reverse=True)
        return results[:limit]

    async def _delete_from_redis(self, memory_id: str) -> bool:
        """Delete a memory from Redis."""
        key = f"memory:{memory_id}"

        # Check if memory exists
        exists = await self.redis_pool.exists(key)
        if not exists:
            return False

        # Delete the memory
        await self.redis_pool.delete(key)

        # Remove from agent's memory set
        await self.redis_pool.srem(f"agent:{self.agent_id}:memories", memory_id)

        # Remove from conversation's memory set if conversation_id is provided
        if self.conversation_id:
            await self.redis_pool.srem(f"conversation:{self.conversation_id}:memories", memory_id)

        return True

    # Private methods for MongoDB operations

    def _store_in_mongodb(self, memory: MemoryEntry, ttl_seconds: Optional[int] = None) -> None:
        """Store a memory in MongoDB with optional TTL."""
        memory_dict = memory.model_dump(exclude={"embedding"})

        # Add TTL if provided
        if ttl_seconds:
            memory_dict["expiry_time"] = datetime.utcnow().timestamp() + ttl_seconds

        # Store in MongoDB
        self.mongodb_client.collection("memories").document(memory.id).set(memory_dict)

    def _retrieve_from_mongodb(self, memory_id: str) -> Optional[MemoryEntry]:
        """Retrieve a memory from MongoDB."""
        doc_ref = self.mongodb_client.collection("memories").document(memory_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        # Convert MongoDB document to MemoryEntry
        memory_data = doc.to_dict()

        # Check if memory has expired
        if "expiry_time" in memory_data:
            if memory_data["expiry_time"] < datetime.utcnow().timestamp():
                # Memory has expired, delete it
                doc_ref.delete()
                return None

            # Remove expiry_time from data before converting to MemoryEntry
            del memory_data["expiry_time"]

        return MemoryEntry(**memory_data)

    def _search_in_mongodb(
        self,
        query: str,
        memory_type: MemoryType,
        limit: int,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[MemorySearchResult]:
        """
        """
            self.mongodb_client.collection("memories")
            .where("memory_type", "==", memory_type.value)
            .where("agent_id", "==", self.agent_id)
        )

        # Add conversation_id filter if provided
        if self.conversation_id:
            mongodb_query = mongodb_query.where("conversation_id", "==", self.conversation_id)

        # Execute query
        docs = mongodb_query.limit(limit * 2).stream()  # Get more than needed for filtering

        # Process results
        for doc in docs:
            memory_data = doc.to_dict()

            # Check if memory has expired
            if "expiry_time" in memory_data:
                if memory_data["expiry_time"] < datetime.utcnow().timestamp():
                    # Memory has expired, delete it
                    doc.reference.delete()
                    continue

                # Remove expiry_time from data before converting to MemoryEntry
                del memory_data["expiry_time"]

            # Apply metadata filter if provided
            if metadata_filter and not self._matches_metadata_filter(memory_data.get("metadata", {}), metadata_filter):
                continue

            # Simple text matching (could be improved)
            if query.lower() in memory_data.get("content", "").lower():
                # Calculate a simple relevance score based on string matching
                relevance = self._calculate_text_relevance(query, memory_data.get("content", ""))

                memory = MemoryEntry(**memory_data)
                results.append(
                    MemorySearchResult(
                        memory=memory,
                        relevance=relevance,
                    )
                )

        # Sort by relevance and limit results
        results.sort(key=lambda x: x.relevance, reverse=True)
        return results[:limit]

    def _delete_from_mongodb(self, memory_id: str) -> bool:
        """Delete a memory from MongoDB."""
        doc_ref = self.mongodb_client.collection("memories").document(memory_id)
        doc = doc_ref.get()

        if not doc.exists:
            return False

        doc_ref.delete()
        return True

    # Private methods for Vector Search operations

    async def _store_in_vector_search(self, memory: MemoryEntry) -> None:
        """
        """
        logger.info(f"Storing embedding for memory {memory.id} in Vector Search")

    async def _search_in_vector_search(
        self,
        embedding: List[float],
        limit: int,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[MemorySearchResult]:
        """
        """
        """
        """
        logger.info(f"Deleting embedding for memory {memory_id} from Vector Search")
        return True

    # Utility methods

    def _matches_metadata_filter(self, metadata: Dict[str, Any], metadata_filter: Dict[str, Any]) -> bool:
        """Check if metadata matches the filter."""
        """
        """