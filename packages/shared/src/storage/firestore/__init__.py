"""
Firestore storage modules for AI Orchestration System.

This package contains the Firestore-based storage implementations for
the AI Orchestration System, providing persistent storage for memory
items, agent data, and other system information.
"""

# Import constants
from packages.shared.src.storage.firestore.constants import (
    MEMORY_ITEMS_COLLECTION,
    AGENT_DATA_COLLECTION,
    USER_SESSIONS_COLLECTION,
    VECTOR_EMBEDDINGS_COLLECTION,
    MAX_BATCH_SIZE,
)

# Import the v2 implementation
try:
    from packages.shared.src.storage.firestore.v2 import (
        FirestoreMemoryManagerV2,
        FirestoreStorageManager,
        AsyncFirestoreStorageManager,
    )

    V2_AVAILABLE = True
except ImportError:
    V2_AVAILABLE = False

# Constants
__version__ = "2.0.0"

__all__ = [
    "MEMORY_ITEMS_COLLECTION",
    "AGENT_DATA_COLLECTION",
    "USER_SESSIONS_COLLECTION",
    "VECTOR_EMBEDDINGS_COLLECTION",
    "MAX_BATCH_SIZE",
]

# Add v2 components to __all__ if available
if V2_AVAILABLE:
    __all__.extend(
        [
            "FirestoreMemoryManagerV2",
            "FirestoreStorageManager",
            "AsyncFirestoreStorageManager",
            "V2_AVAILABLE",
        ]
    )
else:
    __all__.append("V2_AVAILABLE")
