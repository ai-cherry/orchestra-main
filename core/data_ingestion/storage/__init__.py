"""
Storage adapter implementations for data ingestion system.

This module provides concrete implementations of the StorageInterface
for different storage backends including PostgreSQL, Weaviate, and S3.
"""

from typing import Dict, Type
from ..interfaces.storage import StorageInterface, StorageType

# Import concrete adapters
from .postgres_adapter import PostgresAdapter
from .weaviate_adapter import WeaviateAdapter

# Storage adapter registry
STORAGE_REGISTRY: Dict[StorageType, Type[StorageInterface]] = {
    StorageType.POSTGRES: PostgresAdapter,
    StorageType.WEAVIATE: WeaviateAdapter,
}

def get_storage_adapter(storage_type: StorageType) -> Type[StorageInterface]:
    """
    Get the storage adapter class for a given storage type.
    
    Args:
        storage_type: The type of storage backend
        
    Returns:
        The storage adapter class
        
    Raises:
        ValueError: If storage type is not supported
    """
    adapter_class = STORAGE_REGISTRY.get(storage_type)
    if not adapter_class:
        raise ValueError(f"Unsupported storage type: {storage_type}")
    return adapter_class

__all__ = [
    "PostgresAdapter",
    "WeaviateAdapter",
    "get_storage_adapter",
    "STORAGE_REGISTRY",
]