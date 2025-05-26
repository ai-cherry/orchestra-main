"""
Memory factory for AI Orchestra.

This module provides factory functions for creating memory instances.
"""

import logging
from typing import Any, Dict, Optional

from core.orchestrator.src.config.models import MemoryConfig
from core.orchestrator.src.memory.backends.firestore_memory import FirestoreMemory
from core.orchestrator.src.memory.backends.redis_memory import RedisMemory
from core.orchestrator.src.memory.backends.vertex_memory import VertexMemory
from core.orchestrator.src.memory.layered_memory_manager import LayeredMemoryManager

logger = logging.getLogger(__name__)


class MemoryFactory:
    """Factory for creating memory instances."""

    @staticmethod
    def create_memory_from_config(
        config: Dict[str, Any],
    ) -> Optional[LayeredMemoryManager]:
        """
        Create a memory manager from configuration.

        Args:
            config: Configuration dictionary

        Returns:
            Initialized LayeredMemoryManager
        """
        try:
            return LayeredMemoryManager.from_config(config)
        except Exception as e:
            logger.error(f"Error creating memory manager: {e}")
            return None

    @staticmethod
    def create_memory_from_memory_config(
        memory_config: MemoryConfig,
    ) -> Optional[LayeredMemoryManager]:
        """
        Create a memory manager from a MemoryConfig.

        Args:
            memory_config: MemoryConfig instance

        Returns:
            Initialized LayeredMemoryManager
        """
        try:
            return LayeredMemoryManager.from_memory_config(memory_config)
        except Exception as e:
            logger.error(f"Error creating memory manager: {e}")
            return None

    @staticmethod
    def create_redis_memory(
        host: str = "localhost",
        port: int = 6379,
        password: Optional[str] = None,
        db: int = 0,
        ttl: int = 3600,
        prefix: str = "orchestra:",
    ) -> RedisMemory:
        """
        Create a Redis memory backend.

        Args:
            host: Redis host
            port: Redis port
            password: Redis password
            db: Redis database
            ttl: Time-to-live in seconds
            prefix: Key prefix

        Returns:
            Initialized RedisMemory
        """
        return RedisMemory(
            host=host, port=port, password=password, db=db, ttl=ttl, prefix=prefix
        )

    @staticmethod
    def create_firestore_memory(
        collection_name: str = "orchestra_memory",
        ttl: Optional[int] = None,
        client=None,
    ) -> FirestoreMemory:
        """
        Create a Firestore memory backend.

        Args:
            collection_name: Firestore collection name
            ttl: Time-to-live in seconds
            client: Firestore client

        Returns:
            Initialized FirestoreMemory
        """
        return FirestoreMemory(collection_name=collection_name, ttl=ttl, client=client)

    @staticmethod
    def create_vertex_memory(
        project_id: str,
        location: str = "us-west4",
        index_name: str = "orchestra-memory-index",
        embedding_model: str = "textembedding-gecko@003",
        collection_name: str = "vertex_memory",
        client=None,
        firestore_client=None,
    ) -> VertexMemory:
        """
        Create a Vertex AI memory backend.

        Args:
            project_id: GCP project ID
            location: GCP region
            index_name: Vector index name
            embedding_model: Embedding model name
            collection_name: Firestore collection name
            client: Vertex AI client
            firestore_client: Firestore client

        Returns:
            Initialized VertexMemory
        """
        return VertexMemory(
            project_id=project_id,
            location=location,
            index_name=index_name,
            embedding_model=embedding_model,
            collection_name=collection_name,
            client=client,
            firestore_client=firestore_client,
        )

    @staticmethod
    def create_layered_memory(
        short_term_config: Optional[Dict[str, Any]] = None,
        mid_term_config: Optional[Dict[str, Any]] = None,
        long_term_config: Optional[Dict[str, Any]] = None,
        semantic_config: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None,
    ) -> LayeredMemoryManager:
        """
        Create a layered memory manager with all memory layers.

        Args:
            short_term_config: Configuration for short-term memory
            mid_term_config: Configuration for mid-term memory
            long_term_config: Configuration for long-term memory
            semantic_config: Configuration for semantic memory
            project_id: GCP project ID

        Returns:
            Initialized LayeredMemoryManager
        """
        config = {}

        # Add Redis configuration
        if short_term_config:
            config["redis"] = short_term_config

        # Add Firestore configuration
        firestore_config = {}
        if mid_term_config:
            firestore_config["mid_term_collection"] = mid_term_config.get(
                "collection_name", "orchestra_mid_term"
            )
            firestore_config["mid_term_ttl"] = mid_term_config.get(
                "ttl", 86400
            )  # 1 day

        if long_term_config:
            firestore_config["long_term_collection"] = long_term_config.get(
                "collection_name", "orchestra_long_term"
            )
            firestore_config["long_term_ttl"] = long_term_config.get(
                "ttl", 2592000
            )  # 30 days

        if firestore_config:
            config["firestore"] = firestore_config

        # Add Vertex AI configuration
        if semantic_config:
            config["vertex"] = semantic_config
        elif project_id:
            config["vertex"] = {
                "project_id": project_id,
                "location": "us-west4",
                "index_name": "orchestra-memory-index",
                "embedding_model": "textembedding-gecko@003",
                "collection_name": "vertex_memory",
            }

        return LayeredMemoryManager.from_config(config)
