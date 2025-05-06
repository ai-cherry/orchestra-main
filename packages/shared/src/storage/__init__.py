"""
Storage modules for AI Orchestration System.

This package provides storage abstractions and implementations for
various data storage needs in the AI Orchestration System, including
memory management, agent data, and other persistent storage requirements.
"""

from packages.shared.src.storage.config import StorageConfig
from packages.shared.src.storage.exceptions import (
    StorageError, 
    ConnectionError, 
    ValidationError, 
    OperationError
)

# Import Firestore components if available
try:
    from packages.shared.src.storage.firestore import (
        V2_AVAILABLE,
        MEMORY_ITEMS_COLLECTION,
        AGENT_DATA_COLLECTION
    )
    
    if V2_AVAILABLE:
        from packages.shared.src.storage.firestore import (
            FirestoreMemoryManagerV2,
            FirestoreStorageManager,
            AsyncFirestoreStorageManager
        )
        
    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False
    V2_AVAILABLE = False

# Constants
__version__ = "1.0.0"

__all__ = [
    "StorageConfig",
    "StorageError",
    "ConnectionError",
    "ValidationError",
    "OperationError",
    "FIRESTORE_AVAILABLE",
    "V2_AVAILABLE"
]

# Add Firestore components to __all__ if available
if FIRESTORE_AVAILABLE:
    __all__.extend([
        "MEMORY_ITEMS_COLLECTION",
        "AGENT_DATA_COLLECTION"
    ])
    
    if V2_AVAILABLE:
        __all__.extend([
            "FirestoreMemoryManagerV2",
            "FirestoreStorageManager",
            "AsyncFirestoreStorageManager"
        ])
