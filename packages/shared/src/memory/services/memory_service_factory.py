"""
Memory Service Factory for AI Orchestration System.

This module provides a factory for creating memory services with the appropriate
storage adapter, following the hexagonal architecture pattern.
"""

import logging
from typing import Dict, Optional, Any

from packages.shared.src.memory.ports import MemoryStoragePort
from packages.shared.src.memory.adapters.firestore_adapter import (
    FirestoreStorageAdapter,
)
from packages.shared.src.memory.adapters.postgres_adapter import PostgresStorageAdapter
from packages.shared.src.memory.services.memory_service import MemoryService
from packages.shared.src.storage.config import StorageConfig

# Configure logging
logger = logging.getLogger(__name__)


class MemoryServiceFactory:
    """
    Factory for creating memory services with appropriate storage adapters.

    This class handles the creation of memory services with the appropriate
    storage adapter based on configuration, hiding the complexity of adapter
    instantiation from clients.
    """

    @staticmethod
    async def create_memory_service(
        storage_type: str = "firestore",
        config: Optional[Dict[str, Any]] = None,
        storage_config: Optional[StorageConfig] = None,
    ) -> MemoryService:
        """
        Create a memory service with the appropriate storage adapter.

        Args:
            storage_type: Type of storage adapter to use ('firestore' or 'postgres')
            config: Configuration for the storage adapter
            storage_config: Storage configuration object

        Returns:
            Initialized memory service

        Raises:
            ValueError: If an unsupported storage type is specified
        """
        config = config or {}

        # Create the appropriate storage adapter
        storage_adapter = MemoryServiceFactory._create_storage_adapter(
            storage_type, config, storage_config
        )

        # Create and initialize the service
        service = MemoryService(storage_adapter)
        await service.initialize()

        logger.info(f"Created memory service with {storage_type} storage adapter")
        return service

    @staticmethod
    def _create_storage_adapter(
        storage_type: str,
        config: Dict[str, Any],
        storage_config: Optional[StorageConfig] = None,
    ) -> MemoryStoragePort:
        """
        Create a storage adapter of the specified type.

        Args:
            storage_type: Type of storage adapter to create
            config: Configuration for the storage adapter
            storage_config: Storage configuration object

        Returns:
            Storage adapter instance

        Raises:
            ValueError: If an unsupported storage type is specified
        """
        if storage_type == "firestore":
            return FirestoreStorageAdapter(
                project_id=config.get("project_id"),
                credentials_json=config.get("credentials_json"),
                credentials_path=config.get("credentials_path"),
                namespace=config.get("namespace", "default"),
                config=storage_config,
            )
        elif storage_type == "postgres":
            return PostgresStorageAdapter(
                host=config.get("host", "localhost"),
                port=config.get("port", 5432),
                database=config.get("database", "postgres"),
                user=config.get("user", "postgres"),
                password=config.get("password"),
                schema=config.get("schema", "public"),
                min_connections=config.get("min_connections", 5),
                max_connections=config.get("max_connections", 10),
                config=storage_config,
            )
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")
