"""
Exception hierarchy for the GCP Migration toolkit.

This module defines a comprehensive exception hierarchy for error handling
with clear categorization and structured metadata. These exceptions provide
rich context for debugging while maintaining high performance.
"""

from typing import Any, Dict, Optional, Type, TypeVar


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
    ) -> None:
        """
        Initialize a migration error.

        Args:
            message: Human-readable error message
            cause: Optional underlying exception that caused this error
            details: Optional structured details about the error
        """
        self.message = message
        self.cause = cause
        self.details = details or {}

        # Construct message with cause if available
        if cause:
            full_message = (
                f"{message} | Caused by: {type(cause).__name__}: {str(cause)}"
            )
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


# Type variable for generic error mapping
T = TypeVar("T", bound=Exception)


def map_to_migration_error(
    exception: Exception, target_type: Type[T], message: Optional[str] = None
) -> T:
    """
    Map an exception to a specific MigrationError subtype.

    This utility function helps convert external exceptions to domain-specific
    exceptions with proper type safety.

    Args:
        exception: The original exception to map
        target_type: The target MigrationError subclass
        message: Optional custom message (defaults to exception message)

    Returns:
        A new instance of the target exception type

    Example:
        ```python
        try:
            # Some operation that might fail
            result = api_client.get_resource()
        except RequestException as e:
            # Map to domain-specific error
            raise map_to_migration_error(e, NetworkError, "API request failed")
        ```
    """
    # Ensure target type is a MigrationError
    if not issubclass(target_type, MigrationError):
        raise TypeError(f"Target type must be a MigrationError, got {target_type}")

    # Use provided message or extract from exception
    error_message = message or str(exception)

    # Create and return the mapped exception
    return target_type(message=error_message, cause=exception)


# Error mapping dictionary for common external exceptions
ERROR_MAPPING = {
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


def map_exception_by_name(
    exception: Exception,
    default_type: Type[MigrationError] = MigrationError,
    message: Optional[str] = None,
) -> MigrationError:
    """
    Map an exception to a MigrationError based on its class name.

    This function uses the ERROR_MAPPING dictionary to determine the appropriate
    MigrationError subclass based on the exception's class name.

    Args:
        exception: The exception to map
        default_type: Default MigrationError type if no mapping is found
        message: Optional custom message

    Returns:
        A new MigrationError instance
    """
    # Get exception class name
    exception_class = exception.__class__.__name__

    # Find mapping or use default
    target_type = ERROR_MAPPING.get(exception_class, default_type)

    # Map the exception
    return map_to_migration_error(exception, target_type, message)


def safe_operation(
    operation: callable,
    error_mapper: Optional[callable] = None,
    default_error_type: Type[MigrationError] = MigrationError,
    error_message: Optional[str] = None,
):
    """
    Decorator for safely executing operations with error mapping.

    This decorator wraps operations to catch exceptions and map them to
    domain-specific errors.

    Args:
        operation: The function to decorate
        error_mapper: Optional custom error mapping function
        default_error_type: Default error type if no mapping is found
        error_message: Optional error message template

    Returns:
        Decorated function

    Example:
        ```python
        @safe_operation(default_error_type=StorageError)
        def read_file(path):
            with open(path, 'r') as f:
                return f.read()
        ```
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get custom message if provided
                message = error_message
                if message is None:
                    message = f"Error in {func.__name__}: {str(e)}"

                # Use custom mapper if provided
                if error_mapper is not None:
                    mapped_error = error_mapper(e, message)
                else:
                    mapped_error = map_exception_by_name(e, default_error_type, message)

                raise mapped_error from e

        return wrapper

    # Allow usage as @safe_operation or @safe_operation()
    if callable(operation) and not isinstance(operation, type):
        func = operation
        operation = None
        return decorator(func)

    return decorator


def safe_async_operation(
    operation: callable,
    error_mapper: Optional[callable] = None,
    default_error_type: Type[MigrationError] = MigrationError,
    error_message: Optional[str] = None,
):
    """
    Decorator for safely executing async operations with error mapping.

    This decorator wraps async operations to catch exceptions and map them to
    domain-specific errors.

    Args:
        operation: The async function to decorate
        error_mapper: Optional custom error mapping function
        default_error_type: Default error type if no mapping is found
        error_message: Optional error message template

    Returns:
        Decorated async function

    Example:
        ```python
        @safe_async_operation(default_error_type=NetworkError)
        async def fetch_data(url):
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.json()
        ```
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Get custom message if provided
                message = error_message
                if message is None:
                    message = f"Error in {func.__name__}: {str(e)}"

                # Use custom mapper if provided
                if error_mapper is not None:
                    mapped_error = error_mapper(e, message)
                else:
                    mapped_error = map_exception_by_name(e, default_error_type, message)

                raise mapped_error from e

        return wrapper

    # Allow usage as @safe_async_operation or @safe_async_operation()
    if callable(operation) and not isinstance(operation, type):
        func = operation
        operation = None
        return decorator(func)

    return decorator
