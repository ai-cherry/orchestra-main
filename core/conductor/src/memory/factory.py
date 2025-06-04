# TODO: Consider adding connection pooling configuration
"""
"""
    """Factory for creating memory instances."""
        """
        """
            logger.error(f"Error creating memory manager: {e}")
            return None

    @staticmethod
    def create_memory_from_memory_config(
        memory_config: MemoryConfig,
    ) -> Optional[LayeredMemoryManager]:
        """
        """
            logger.error(f"Error creating memory manager: {e}")
            return None

    @staticmethod
    def create_redis_memory(
        host: str = "localhost",
        port: int = 6379,
        password: Optional[str] = None,
        db: int = 0,
        ttl: int = 3600,
        prefix: str = "cherry_ai:",
    ) -> RedisMemory:
        """
        """
        collection_name: str = "cherry_ai_memory",
        ttl: Optional[int] = None,
        client=None,
    ) -> MongoDBMemory:
        """
        """
        location: str = "us-west4",
        index_name: str = "cherry_ai-memory-index",
        embedding_model: str = "textembedding-gecko@003",
        collection_name: str = "vertex_memory",
        client=None,
        mongodb_client=None,
    ) -> VertexMemory:
        """
        """
        """
        """
            config["redis"] = short_term_config

        # Add MongoDB configuration
        mongodb_config = {}
        if mid_term_config:
            mongodb_config["mid_term_collection"] = mid_term_config.get("collection_name", "cherry_ai_mid_term")
            mongodb_config["mid_term_ttl"] = mid_term_config.get("ttl", 86400)  # 1 day

        if long_term_config:
            mongodb_config["long_term_collection"] = long_term_config.get("collection_name", "cherry_ai_long_term")
            mongodb_config["long_term_ttl"] = long_term_config.get("ttl", 2592000)  # 30 days

        if mongodb_config:
            config["mongodb"] = mongodb_config

        # Add Vertex AI configuration
        if semantic_config:
            config["vertex"] = semantic_config
        elif project_id:
            config["vertex"] = {
                "project_id": project_id,
                "location": "us-west4",
                "index_name": "cherry_ai-memory-index",
                "embedding_model": "textembedding-gecko@003",
                "collection_name": "vertex_memory",
            }

        return LayeredMemoryManager.from_config(config)
