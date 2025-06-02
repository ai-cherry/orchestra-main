"""
Storage interface for data ingestion system.

This module defines the base interface for storage adapters including
PostgreSQL, Weaviate, and S3/MinIO implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum

class StorageType(Enum):
    """Types of storage backends supported."""
    POSTGRES = "postgres"
    WEAVIATE = "weaviate"
    REDIS = "redis"

@dataclass
class StorageResult:
    """
    Result of a storage operation.
    
    Attributes:
        success: Whether the operation was successful
        key: The key/ID of the stored item
        error: Error message if operation failed
        metadata: Additional metadata about the operation
    """
    success: bool
    key: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}

class StorageInterface(ABC):
    """
    Abstract base class for all storage adapters.
    
    This interface provides a consistent API for different storage backends
    while allowing for backend-specific optimizations.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the storage adapter with configuration.
        
        Args:
            config: Configuration dictionary with connection details
        """
        self.config = config
        self.storage_type: StorageType = None
        self._connected = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the storage backend.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Close connection to the storage backend.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def store(
        self, 
        data: Any, 
        key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StorageResult:
        """
        Store data in the backend.
        
        Args:
            data: The data to store
            key: Optional key/ID for the data
            metadata: Optional metadata to store with the data
            
        Returns:
            StorageResult indicating success/failure and the key
        """
        pass
    
    @abstractmethod
    async def retrieve(
        self, 
        key: str,
        include_metadata: bool = False
    ) -> Optional[Any]:
        """
        Retrieve data from the backend.
        
        Args:
            key: The key/ID of the data to retrieve
            include_metadata: Whether to include metadata in response
            
        Returns:
            The retrieved data or None if not found
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> StorageResult:
        """
        Delete data from the backend.
        
        Args:
            key: The key/ID of the data to delete
            
        Returns:
            StorageResult indicating success/failure
        """
        pass
    
    @abstractmethod
    async def list(
        self, 
        prefix: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[str]:
        """
        List keys in the storage backend.
        
        Args:
            prefix: Optional prefix to filter keys
            limit: Maximum number of keys to return
            offset: Number of keys to skip
            
        Returns:
            List of keys matching the criteria
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the storage backend.
        
        Args:
            key: The key to check
            
        Returns:
            True if the key exists, False otherwise
        """
        pass
    
    async def batch_store(
        self, 
        items: List[Dict[str, Any]]
    ) -> List[StorageResult]:
        """
        Store multiple items in a batch operation.
        
        Default implementation calls store() for each item.
        Override for backend-specific batch optimizations.
        
        Args:
            items: List of items to store, each with 'data' and optional 'key'
            
        Returns:
            List of StorageResult objects for each item
        """
        results = []
        for item in items:
            result = await self.store(
                data=item.get('data'),
                key=item.get('key'),
                metadata=item.get('metadata')
            )
            results.append(result)
        return results
    
    async def batch_retrieve(
        self, 
        keys: List[str]
    ) -> Dict[str, Any]:
        """
        Retrieve multiple items in a batch operation.
        
        Default implementation calls retrieve() for each key.
        Override for backend-specific batch optimizations.
        
        Args:
            keys: List of keys to retrieve
            
        Returns:
            Dictionary mapping keys to their data
        """
        results = {}
        for key in keys:
            data = await self.retrieve(key)
            if data is not None:
                results[key] = data
        return results
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the storage backend.
        
        Returns:
            Dictionary with health status information
        """
        try:
            # Try a simple operation to verify connectivity
            test_key = f"_health_check_{datetime.utcnow().timestamp()}"
            result = await self.store("test", key=test_key)
            
            if result.success:
                await self.delete(test_key)
                return {
                    "healthy": True,
                    "storage_type": self.storage_type.value if self.storage_type else "unknown",
                    "connected": self._connected,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "healthy": False,
                    "error": result.error,
                    "storage_type": self.storage_type.value if self.storage_type else "unknown",
                    "connected": self._connected,
                    "timestamp": datetime.utcnow().isoformat()
                }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "storage_type": self.storage_type.value if self.storage_type else "unknown",
                "connected": self._connected,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def is_connected(self) -> bool:
        """Check if the storage backend is connected."""
        return self._connected