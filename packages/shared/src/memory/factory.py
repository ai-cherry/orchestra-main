"""
Memory manager factory for AI Orchestra.

This module provides a factory for creating memory manager instances based on
configuration. It supports different types of memory managers and implements
capability discovery to detect available services.
"""

import importlib
import logging
import sys
from typing import Any, Dict, List, Optional, Type, Union, cast

from packages.shared.src.memory.config import (
    MemoryBackendType,
    MemoryConfig,
    VectorSearchType,
)
from packages.shared.src.memory.memory_manager import MemoryManager
from packages.shared.src.storage.vector.factory import VectorSearchFactory


logger = logging.getLogger(__name__)


class MemoryManagerFactory:
    """
    Factory for creating memory manager instances.

    This class provides methods for creating different types of memory managers
    based on configuration. It supports capability discovery to detect available
    services and provides a unified interface for creating memory managers.
    """

    @staticmethod
    async def create_memory_manager(
        config: Optional[MemoryConfig] = None, log_level: int = logging.INFO
    ) -> MemoryManager:
        """
        Create a memory manager instance based on configuration.

        Args:
            config: Memory configuration
            log_level: Logging level for the memory manager

        Returns:
            A memory manager instance

        Raises:
            ValueError: If the backend type is not supported
            ImportError: If the required dependencies are not available
        """
        # Use default config if not provided
        if config is None:
            config = MemoryConfig.from_env()

        # Create memory manager based on backend type
        if config.backend == MemoryBackendType.FIRESTORE:
            return await MemoryManagerFactory._create_firestore_memory_manager(
                config, log_level
            )
        elif config.backend == MemoryBackendType.REDIS:
            return await MemoryManagerFactory._create_redis_memory_manager(
                config, log_level
            )
        elif config.backend == MemoryBackendType.IN_MEMORY:
            return await MemoryManagerFactory._create_in_memory_manager(
                config, log_level
            )
        else:
            raise ValueError(f"Unsupported backend type: {config.backend}")

    @staticmethod
    async def _create_firestore_memory_manager(
        config: MemoryConfig, log_level: int
    ) -> MemoryManager:
        """
        Create a Firestore memory manager.

        Args:
            config: Memory configuration
            log_level: Logging level for the memory manager

        Returns:
            A Firestore memory manager instance

        Raises:
            ImportError: If the required dependencies are not available
        """
        # Check if Firestore is available
        try:
            from packages.shared.src.storage.firestore.v2 import (
                FirestoreMemoryManagerV2,
            )
        except ImportError:
            logger.error("Firestore dependencies not available")
            raise ImportError(
                "Firestore dependencies not available. "
                "Install with: pip install google-cloud-firestore"
            )

        # Get Firestore config
        firestore_config = config.firestore
        if not firestore_config:
            raise ValueError("Firestore configuration is required")

        # Get vector search config
        vector_search_config = config.vector_search
        vector_search_provider = "in_memory"
        vector_search_params = {}

        if vector_search_config:
            vector_search_provider = vector_search_config.provider.value

            if vector_search_provider == VectorSearchType.VERTEX.value:
                if not vector_search_config.vertex:
                    raise ValueError(
                        "Vertex AI Vector Search configuration is required"
                    )

                vertex_config = vector_search_config.vertex
                vector_search_params = {
                    "project_id": vertex_config.project_id,
                    "location": vertex_config.location,
                    "index_endpoint_id": vertex_config.index_endpoint_id,
                    "index_id": vertex_config.index_id,
                }
            elif vector_search_provider == VectorSearchType.IN_MEMORY.value:
                if vector_search_config.in_memory:
                    vector_search_params = {
                        "dimensions": vector_search_config.in_memory.dimensions
                    }

        # Create and initialize the memory manager
        memory_manager = FirestoreMemoryManagerV2(
            project_id=firestore_config.project_id,
            credentials_json=firestore_config.credentials_json,
            credentials_path=firestore_config.credentials_path,
            namespace=firestore_config.namespace,
            log_level=log_level,
            connection_pool_size=firestore_config.connection_pool_size,
            batch_size=firestore_config.batch_size,
            max_errors_before_unhealthy=firestore_config.max_errors_before_unhealthy,
            vector_search_provider=vector_search_provider,
            vector_search_config=vector_search_params,
        )

        await memory_manager.initialize()
        return memory_manager

    @staticmethod
    async def _create_redis_memory_manager(
        config: MemoryConfig, log_level: int
    ) -> MemoryManager:
        """
        Create a Redis memory manager.

        Args:
            config: Memory configuration
            log_level: Logging level for the memory manager

        Returns:
            A Redis memory manager instance

        Raises:
            ImportError: If the required dependencies are not available
        """
        # Check if Redis is available
        try:
            from packages.shared.src.memory.concrete_memory_manager import (
                ConcreteMemoryManager,
            )
            from packages.shared.src.storage.redis.redis_client import AsyncRedisClient
        except ImportError:
            logger.error("Redis dependencies not available")
            raise ImportError(
                "Redis dependencies not available. " "Install with: pip install redis"
            )

        # Get Redis config
        redis_config = config.redis
        if not redis_config:
            raise ValueError("Redis configuration is required")

        # Create Redis client
        redis_client = AsyncRedisClient(
            host=redis_config.host,
            port=redis_config.port,
            db=redis_config.db,
            password=redis_config.password,
            ssl=redis_config.ssl,
            namespace=redis_config.namespace,
            connection_pool_size=redis_config.connection_pool_size,
            log_level=log_level,
        )

        # Create and initialize the memory manager
        memory_manager = ConcreteMemoryManager(
            redis_client=redis_client,
            namespace=redis_config.namespace,
            ttl=redis_config.ttl,
        )

        await memory_manager.initialize()
        return memory_manager

    @staticmethod
    async def _create_in_memory_manager(
        config: MemoryConfig, log_level: int
    ) -> MemoryManager:
        """
        Create an in-memory manager.

        Args:
            config: Memory configuration
            log_level: Logging level for the memory manager

        Returns:
            An in-memory manager instance
        """
        # Check if in-memory manager is available
        try:
            from packages.shared.src.memory.concrete_memory_manager import (
                ConcreteMemoryManager,
            )
        except ImportError:
            logger.error("Memory manager dependencies not available")
            raise ImportError("Memory manager dependencies not available.")

        # Get in-memory config
        in_memory_config = config.in_memory
        if not in_memory_config:
            raise ValueError("In-memory configuration is required")

        # Create and initialize the memory manager
        memory_manager = ConcreteMemoryManager(
            namespace=in_memory_config.namespace,
            ttl=in_memory_config.ttl,
            max_items=in_memory_config.max_items,
        )

        await memory_manager.initialize()
        return memory_manager

    @staticmethod
    def detect_capabilities() -> Dict[str, bool]:
        """
        Detect available memory capabilities.

        Returns:
            Dictionary of capability names and their availability
        """
        capabilities = {
            "firestore": False,
            "redis": False,
            "vector_search": {"in_memory": True, "vertex": False},  # Always available
        }

        # Check Firestore availability
        try:
            import google.cloud.firestore

            capabilities["firestore"] = True
        except ImportError:
            pass

        # Check Redis availability
        try:
            import redis

            capabilities["redis"] = True
        except ImportError:
            pass

        # Check Vertex AI Vector Search availability
        try:
            import google.cloud.aiplatform

            capabilities["vector_search"]["vertex"] = True
        except ImportError:
            pass

        return capabilities

    @staticmethod
    def get_available_backends() -> List[MemoryBackendType]:
        """
        Get a list of available memory backends.

        Returns:
            List of available memory backend types
        """
        capabilities = MemoryManagerFactory.detect_capabilities()
        available_backends = [MemoryBackendType.IN_MEMORY]  # Always available

        if capabilities["firestore"]:
            available_backends.append(MemoryBackendType.FIRESTORE)

        if capabilities["redis"]:
            available_backends.append(MemoryBackendType.REDIS)

        return available_backends

    @staticmethod
    def get_available_vector_search_providers() -> List[VectorSearchType]:
        """
        Get a list of available vector search providers.

        Returns:
            List of available vector search provider types
        """
        capabilities = MemoryManagerFactory.detect_capabilities()
        available_providers = [
            VectorSearchType.IN_MEMORY,
            VectorSearchType.NONE,
        ]  # Always available

        if capabilities["vector_search"]["vertex"]:
            available_providers.append(VectorSearchType.VERTEX)

        return available_providers
