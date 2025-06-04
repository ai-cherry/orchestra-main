# TODO: Consider adding connection pooling configuration
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
        logger.info(f"Initialized {len(self._stores)} memory stores")

    async def close(self) -> None:
        """
        """

        self._stores = {}
        self._initialized = False

    def _create_store(self, layer: MemoryLayer) -> MemoryStore:
        """
        """
            config["ttl"] = layer.ttl

        # Create store based on type
        if layer.store_type == MemoryType.REDIS:
            return RedisMemoryStore(config)
        elif layer.store_type == MemoryType.mongodb:
            return FirestoreMemoryStore(config)
        elif layer.store_type == MemoryType.IN_MEMORY:
            from core.conductor.src.agents.memory.in_memory import InMemoryStore

            return InMemoryStore(config)
        elif layer.store_type == MemoryType.PGVECTOR:
            from core.conductor.src.agents.memory.pgvector import PGVectorStore

            return PGVectorStore(config)
        elif layer.store_type == MemoryType.OPENAI_VECTOR:
            from core.conductor.src.agents.memory.vertex import VertexVectorMemoryStore

            return VertexVectorMemoryStore(config)
        else:
            raise ValueError(f"Unknown memory store type: {layer.store_type}")

    async def store(self, item: MemoryItem, layer_name: Optional[str] = None) -> str:
        """
        """
                raise ValueError("No memory layers configured")

            return item_id

        # Store in a specific layer
        if layer_name not in self._stores:
            raise ValueError(f"Unknown memory layer: {layer_name}")

        store = self._stores[layer_name]
        return await store.store(item)

    async def retrieve(self, item_id: str, layer_name: Optional[str] = None) -> Optional[MemoryItem]:
        """
        """
                raise ValueError(f"Unknown memory layer: {layer_name}")

            store = self._stores[layer_name]
            return await store.retrieve(item_id)

        # Try to retrieve from each layer in priority order
        for layer in sorted(self.layers, key=lambda l: l.priority, reverse=True):
            store = self._stores[layer.name]
            item = await store.retrieve(item_id)

            if item is not None:
                return item

        # Not found in any layer
        return None

    async def query(self, query: MemoryQuery, layer_name: Optional[str] = None) -> List[MemoryItem]:
        """
        """
                raise ValueError(f"Unknown memory layer: {layer_name}")

            store = self._stores[layer_name]
            return await store.query(query)

        # Query all layers and combine results
        all_results = []
        tasks = []

        for layer in self.layers:
            store = self._stores[layer.name]
            task = asyncio.create_task(store.query(query))
            tasks.append((layer, task))

        # Wait for all queries to complete
        for layer, task in tasks:
            try:

                pass
                results = await task
                # Add layer info to metadata
                for item in results:
                    if item.metadata is None:
                        item.metadata = {}
                    item.metadata["memory_layer"] = layer.name

                all_results.extend(results)
            except Exception:

                pass
                logger.error(f"Error querying layer {layer.name}: {e}")

        # Sort by timestamp (newest first) and apply limit
        all_results.sort(key=lambda x: x.timestamp, reverse=True)

        return all_results[: query.limit]

    async def delete(self, item_id: str, layer_name: Optional[str] = None) -> bool:
        """
        """
                raise ValueError(f"Unknown memory layer: {layer_name}")

            store = self._stores[layer_name]
            return await store.delete(item_id)

        # Delete from all layers
        deleted = False

        for layer_name, store in self._stores.items():
            try:

                pass
                if await store.delete(item_id):
                    deleted = True
            except Exception:

                pass
                logger.error(f"Error deleting from layer {layer_name}: {e}")

        return deleted

    async def clear(self, layer_name: Optional[str] = None) -> int:
        """
        """
                raise ValueError(f"Unknown memory layer: {layer_name}")

            store = self._stores[layer_name]
            return await store.clear()

        # Clear all layers
        total_cleared = 0

        for layer_name, store in self._stores.items():
            try:

                pass
                cleared = await store.clear()
                total_cleared += cleared
            except Exception:

                pass
                logger.error(f"Error clearing layer {layer_name}: {e}")

        return total_cleared

    async def recall_relevant(self, text: str, limit: int = 10) -> List[MemoryItem]:
        """
        """
                        item.metadata["memory_layer"] = layer.name
                        item.metadata["retrieval_type"] = "semantic"

                    vector_results.extend(results)
                except Exception:

                    pass
                    logger.error(f"Error querying vector layer {layer.name}: {e}")

        # If we have enough vector results, return them
        if len(vector_results) >= limit:
            return vector_results[:limit]

        # Otherwise, supplement with keyword search in other stores
        remaining = limit - len(vector_results)
        keyword_results = []

        for layer in self.layers:
            if layer.store_type not in [MemoryType.PGVECTOR, MemoryType.OPENAI_VECTOR]:
                store = self._stores[layer.name]
                query = MemoryQuery(text=text, limit=remaining)

                try:


                    pass
                    results = await store.query(query)
                    for item in results:
                        if item.metadata is None:
                            item.metadata = {}
                        item.metadata["memory_layer"] = layer.name
                        item.metadata["retrieval_type"] = "keyword"

                    keyword_results.extend(results)
                except Exception:

                    pass
                    logger.error(f"Error querying layer {layer.name}: {e}")

        # Combine and return results
        combined_results = vector_results + keyword_results
        return combined_results[:limit]

    async def remember_conversation(
        self,
        text: str,
        user_id: str,
        conversation_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        """
                "user_id": user_id,
                "conversation_id": conversation_id,
                "type": "conversation",
                **(metadata or {}),
            },
        )

        # Store in all layers
        return await self.store(item)

    async def get_conversation_history(self, conversation_id: str, limit: int = 50) -> List[MemoryItem]:
        """
        """
                "conversation_id": conversation_id,
                "type": "conversation",
            },
            limit=limit,
        )

        return await self.query(query)

def create_default_memory_manager() -> LayeredMemoryManager:
    """
    """
            name="short_term",
            store_type=MemoryType.REDIS,
            priority=3,  # Highest priority
            ttl=60 * 60 * 24,  # 1 day TTL
            config={"host": "localhost", "port": 6379, "db": 0},
        ),
        MemoryLayer(
            name="long_term",
            store_type=MemoryType.mongodb,
            priority=2,
            config={"collection": "memory"},
        ),
        MemoryLayer(
            name="semantic",
            store_type=MemoryType.OPENAI_VECTOR,
            priority=1,
            config={
                "location": "us-west4",
                "index_name": "memory-index",
                "embedding_model": "textembedding-gecko@latest",
            },
        ),
    ]

    return LayeredMemoryManager(layers)

# Singleton instance
_memory_manager: Optional[LayeredMemoryManager] = None

async def get_memory_manager() -> LayeredMemoryManager:
    """
    """