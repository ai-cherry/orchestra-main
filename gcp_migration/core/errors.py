"""
Core error handling system for the GCP Migration toolkit.

This module provides a refined exception hierarchy and robust error mapping capabilities
designed for performance and type safety. All exceptions maintain detailed context
while ensuring proper error propagation and recovery.
"""

from __future__ import annotations

import functools
import inspect
import logging
import traceback
from enum import Enum, auto
from typing import (
    Any, Callable, Dict, Generic, List, Literal, Optional, Type, TypeVar, Union,
    cast, overload
)

# Configure logging
logger = logging.getLogger(__name__)

# Generic type variables with proper constraints
T = TypeVar('T')
E = TypeVar('E', bound='MigrationError')  # Properly constrained to MigrationError
F = TypeVar('F', bound=Callable[..., Any])  # For decorators
R = TypeVar('R')  # Return type for functions


class ErrorSeverity(Enum):
    """Error severity levels for categorizing exceptions."""

    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


# Base exception hierarchy
class MigrationError(Exception):
    """
    Base exception class for all migration errors.

    This class provides a consistent interface for all migration errors with
    standardized metadata tracking and error chaining.
    """

    def __init__(
        self,
        message: str,
        cause: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR
    ) -> None:
        """
        Initialize a migration error.

        Args:
            message: Human-readable error message
            cause: Optional underlying exception that caused this error
            details: Optional structured details about the error
            severity: Error severity level for logging and handling
        """
        self.message = message
        self.cause = cause
        self.details = details or {}
        self.severity = severity

        # Construct message with cause if available
        if cause:
            full_message = f"{message} | Caused by: {type(cause).__name__}: {str(cause)}"
        else:
            full_message = message

        super().__init__(full_message)


# Infrastructure errors
class InfrastructureError(MigrationError):
    """Base class for infrastructure-related errors."""
    pass


class NetworkError(InfrastructureError):
    """Error related to network operations."""
    pass


class TimeoutError(NetworkError):
    """Error when an operation times out."""
    pass


class ConnectionError(NetworkError):
    """Error when a connection cannot be established."""
    pass


class ResourceExhaustedError(InfrastructureError):
    """Error when a resource limit is reached."""
    pass


# Authentication and authorization errors
class AuthenticationError(MigrationError):
    """Error related to authentication."""
    pass


class AuthorizationError(MigrationError):
    """Error related to authorization."""
    pass


class CredentialError(AuthenticationError):
    """Error related to credentials."""
    pass


# Resource errors
class ResourceError(MigrationError):
    """Base class for resource-related errors."""
    pass


class ResourceNotFoundError(ResourceError):
    """Error when a resource is not found."""
    pass


class ResourceAlreadyExistsError(ResourceError):
    """Error when creating a resource that already exists."""
    pass


class ResourceStateError(ResourceError):
    """Error when a resource is in an invalid state for an operation."""
    pass


# Data errors
class DataError(MigrationError):
    """Base class for data-related errors."""
    pass


class ValidationError(DataError):
    """Error when data validation fails."""
    pass


class SerializationError(DataError):
    """Error when data serialization or deserialization fails."""
    pass


class DataConsistencyError(DataError):
    """Error when data consistency checks fail."""
    pass


# GCP service errors
class GCPError(MigrationError):
    """Base class for GCP-related errors."""
    pass


class APIError(GCPError):
    """Error when a GCP API request fails."""
    pass


class QuotaError(GCPError):
    """Error when a GCP quota is exceeded."""
    pass


class ConfigurationError(GCPError):
    """Error in GCP configuration."""
    pass


# Specific GCP service errors
class SecretError(GCPError):
    """Error related to Secret Manager operations."""
    pass


class StorageError(GCPError):
    """Error related to Cloud Storage operations."""
    pass


class FirestoreError(GCPError):
    """Error related to Firestore operations."""
    pass


class VertexAIError(GCPError):
    """Error related to Vertex AI operations."""
    pass


# Migration process errors
class MigrationProcessError(MigrationError):
    """Base class for migration process errors."""
    pass


class PlanningError(MigrationProcessError):
    """Error during migration planning."""
    pass


class ExecutionError(MigrationProcessError):
    """Error during migration execution."""
    pass


class VerificationError(MigrationProcessError):
    """Error during migration verification."""
    pass


# Component errors
class ComponentError(MigrationError):
    """Base class for component-specific errors."""
    pass


class InitializationError(ComponentError):
    """Error during component initialization."""
    pass


class CircuitBreakerError(ComponentError):
    """Error related to circuit breaker operation."""
    pass


class CircuitOpenError(CircuitBreakerError):
    """Error when a circuit breaker is open."""
    pass


class BatchProcessingError(ComponentError):
    """Error during batch processing."""
    pass


class PoolExhaustedError(ComponentError):
    """Error when a resource pool is exhausted."""
    pass


class CacheError(ComponentError):
    """Error related to cache operations."""
    pass


# Error mapping registry
ERROR_MAPPING: Dict[str, Type[MigrationError]] = {
    # Network errors
    "RequestException": NetworkError,
    "ConnectionError": ConnectionError,
    "Timeout": TimeoutError,

    # Authentication errors
    "DefaultCredentialsError": CredentialError,
    "UnauthenticatedError": AuthenticationError,
    "PermissionDenied": AuthorizationError,

    # GCP-specific errors
    "NotFound": ResourceNotFoundError,
    "AlreadyExists": ResourceAlreadyExistsError,
    "InvalidArgument": ValidationError,
    "FailedPrecondition": ResourceStateError,
    "OutOfRange": ValidationError,
    "Unauthenticated": AuthenticationError,
    "PermissionDenied": AuthorizationError,
    "ResourceExhausted": ResourceExhaustedError,
    "Aborted": DataConsistencyError,
    "DeadlineExceeded": TimeoutError,
    "Unavailable": NetworkError,

    # General errors
    "ValueError": ValidationError,
    "TypeError": ValidationError,
    "KeyError": ResourceNotFoundError,
    "IndexError": ResourceNotFoundError,
    "OSError": InfrastructureError,
    "IOError": InfrastructureError,
}


@overload
def map_exception(
    exception: Exception, target_type: Type[E], message: Optional[str] = None
) -> E:
    """Map an exception to a specific MigrationError type."""
    ...


@overload
def map_exception(
    exception: Exception, message: Optional[str] = None
) -> MigrationError:
    """Map an exception to a MigrationError type based on its class name."""
    ...


def map_exception(
    exception: Exception,
    target_type_or_message: Optional[Union[Type[E], str]] = None,
    message: Optional[str] = None
) -> Union[E, MigrationError]:
    """
    Map an exception to a MigrationError type with proper context.

    This function provides flexible mapping capabilities with two main forms:
    1. Explicit target type: map_exception(e, SpecificError, "Message")
    2. Automatic mapping: map_exception(e, "Message")

    Args:
        exception: The exception to map
        target_type_or_message: Either a target error type or a message
        message: The error message (when first arg is a type)

    Returns:
        A MigrationError instance with proper context

    Examples:
        ```python
        # Explicit mapping
        try:
            # Some operation
        except ValueError as e:
            raise map_exception(e, ValidationError, "Invalid configuration")

        # Automatic mapping based on exception type
        try:
            # Some operation
        except Exception as e:
            raise map_exception(e, "Operation failed")
        ```
    """
    # Determine if first argument is a type or message
    if isinstance(target_type_or_message, type) and issubclass(target_type_or_message, MigrationError):
        # Form 1: Explicit target type
        target_type = target_type_or_message
        error_message = message
    else:
        # Form 2: Automatic mapping
        target_type = _get_error_type_for_exception(exception)
        error_message = target_type_or_message

    # Use exception message if no message provided
    if error_message is None:
        error_message = str(exception)

    # Create the error instance
    return target_type(message=error_message, cause=exception)


def _get_error_type_for_exception(exception: Exception) -> Type[MigrationError]:
    """
    Get the appropriate MigrationError type for an exception.

    Args:
        exception: The exception to map

    Returns:
        A MigrationError subclass
    """
    exception_class = exception.__class__.__name__

    # Check exact match first
    if exception_class in ERROR_MAPPING:
        return ERROR_MAPPING[exception_class]

    # Check parent classes
    for parent in exception.__class__.__mro__[1:]:  # Skip the class itself
        if parent.__name__ in ERROR_MAPPING:
            return ERROR_MAPPING[parent.__name__]

    # Default to base MigrationError
    return MigrationError


def handle_exception(
    logger: Optional[logging.Logger] = None,
    default_error_type: Type[MigrationError] = MigrationError,
    error_message: Optional[str] = None,
    re_raise: bool = True,
    log_traceback: bool = True,
    severity: ErrorSeverity = ErrorSeverity.ERROR
) -> Callable[[F], F]:
    """
    Decorator for handling exceptions in functions.
    
    This decorator provides comprehensive exception handling with logging,
    mapping to domain-specific errors, and optional re-raising.
    
    Args:
        logger: Logger to use (defaults to module logger)
        default_error_type: Default error type for mapping
        error_message: Optional error message template
        re_raise: Whether to re-raise exceptions
        log_traceback: Whether to log the full traceback
        severity: Error severity level for logging
        
    Returns:
        Decorated function
        
    Example:
        ```python
        @handle_exception(
            logger=custom_logger,
            default_error_type=ConfigurationError,
            error_message="Failed to configure GCP service",
            re_raise=True,
            log_traceback=True,
            severity=ErrorSeverity.ERROR
        )
        def configure_gcp_service(project_id: str) -> bool:
            # Configuration implementation
            if not project_id:
                raise ValueError("Project ID cannot be empty")
            # More implementation...
            return True
            
        # With default parameters:
        @handle_exception
        def simple_function():
            # Function implementation
            pass
        ```
