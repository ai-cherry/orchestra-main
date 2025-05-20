"""
Domain exceptions for the Memory System.

This module defines domain-specific exceptions for the memory system,
following the hexagonal architecture pattern to isolate domain logic
from infrastructure-specific error details.
"""


class MemoryException(Exception):
    """Base exception for all memory-related errors."""

    pass


class MemoryStorageException(MemoryException):
    """Base exception for storage-related errors."""

    pass


class MemoryItemNotFound(MemoryException):
    """Exception raised when a memory item is not found."""

    pass


class MemoryConnectionError(MemoryStorageException):
    """Exception raised when a connection to the storage system fails."""

    pass


class MemoryQueryError(MemoryStorageException):
    """Exception raised when a query operation fails."""

    pass


class MemoryWriteError(MemoryStorageException):
    """Exception raised when a write operation fails."""

    pass


class MemoryValidationError(MemoryException):
    """Exception raised when validation of memory data fails."""

    pass
