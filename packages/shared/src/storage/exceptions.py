"""
Storage-related exceptions for the AI Orchestration System.

This module defines a structured exception hierarchy for all storage-related
errors, ensuring consistent error handling across different storage backends.
"""


class StorageError(Exception):
    """Base exception for all storage-related errors."""

    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(message)
        self.original_exception = original_exception


class ConnectionError(StorageError):
    """Exception raised when a connection to the storage backend fails."""

    pass


class ValidationError(StorageError):
    """Exception raised when data validation fails."""

    pass


class OperationError(StorageError):
    """Exception raised when a storage operation fails."""

    def __init__(
        self, operation: str, message: str, original_exception: Exception = None
    ):
        super().__init__(f"{operation} operation failed: {message}", original_exception)
        self.operation = operation
