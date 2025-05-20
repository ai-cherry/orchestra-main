"""
Firestore memory management implementation version 2 for AI Orchestration System.

This package provides a new, improved implementation of Firestore-based
memory management for the AI Orchestration System, with cleaner separation
of concerns, better error handling, and more consistent interfaces.
"""

from packages.shared.src.storage.firestore.v2.adapter import FirestoreMemoryManagerV2
from packages.shared.src.storage.firestore.v2.core import FirestoreStorageManager
from packages.shared.src.storage.firestore.v2.async_core import (
    AsyncFirestoreStorageManager,
)
from packages.shared.src.storage.firestore.v2.models import (
    memory_item_to_document,
    document_to_memory_item,
    agent_data_to_document,
    document_to_agent_data,
    compute_content_hash,
    generate_id,
)

__all__ = [
    "FirestoreMemoryManagerV2",
    "FirestoreStorageManager",
    "AsyncFirestoreStorageManager",
    "memory_item_to_document",
    "document_to_memory_item",
    "agent_data_to_document",
    "document_to_agent_data",
    "compute_content_hash",
    "generate_id",
]
