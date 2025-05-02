"""
Memory System for AI Orchestration System.

This package implements the memory system for the AI Orchestration System,
following the hexagonal architecture pattern to separate domain logic from
infrastructure concerns.
"""

# Domain exceptions
from packages.shared.src.memory.exceptions import (
    MemoryException,
    MemoryStorageException,
    MemoryItemNotFound,
    MemoryConnectionError,
    MemoryQueryError,
    MemoryWriteError,
    MemoryValidationError,
)

# Ports (interfaces)
from packages.shared.src.memory.ports import MemoryStoragePort

# Services (domain logic)
from packages.shared.src.memory.services import MemoryService, MemoryServiceFactory

# Adapters (infrastructure)
from packages.shared.src.memory.adapters import FirestoreStorageAdapter, PostgresStorageAdapter

# Legacy backward-compatible imports
from packages.shared.src.memory.memory_types import MemoryHealth
from packages.shared.src.memory.memory_interface import MemoryInterface
from packages.shared.src.memory.memory_manager import MemoryManager

__all__ = [
    # Domain exceptions
    "MemoryException",
    "MemoryStorageException",
    "MemoryItemNotFound",
    "MemoryConnectionError",
    "MemoryQueryError",
    "MemoryWriteError",
    "MemoryValidationError",

    # Ports
    "MemoryStoragePort",

    # Services
    "MemoryService",
    "MemoryServiceFactory",

    # Adapters
    "FirestoreStorageAdapter",
    "PostgresStorageAdapter",

    # Legacy
    "MemoryHealth",
    "MemoryInterface",
    "MemoryManager",
]
