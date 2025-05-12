"""
Exception hierarchy for GCP migration toolkit.

This module defines a comprehensive exception hierarchy for the GCP migration 
toolkit, providing structured error handling with consistent interfaces and 
error mapping from external libraries.
"""

from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, cast, Union
import json
import traceback


T = TypeVar('T', bound='MigrationError')


class MigrationError(Exception):
    """
    Base exception class for all migration-related errors.
    
    This is the root of the exception hierarchy for the migration toolkit.
    All other exceptions inherit from this class.
    """
    
    def __init__(
        self, 
        message: str, 
        cause: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a migration error.
        
        Args:
            message: The error message
            cause: The underlying exception that caused this error
            details: Additional error details
        """
        self.message = message
        self.cause = cause
        self.details = details or {}
        
        # Build the full message including cause information
        full_message = message
        if cause:
            cause_str = str(cause)
            # Avoid duplicate information
            if cause_str and cause_str not in message:
                full_message = f"{message}: {cause_str}"
        
        super().__init__(full_message)
    
    @property
    def display_message(self) -> str:
        """Get a user-friendly error message for display purposes."""
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the error to a dictionary representation.
        
        Returns:
            Dictionary containing error information
        """
        result = {
            "error_type": self.__class__.__name__,
            "message": self.message,
        }
        
        if self.details:
            result["details"] = self.details
            
        if self.cause:
            result["cause"] = {
                "type": self.cause.__class__.__name__,
                "message": str(self.cause),
            }
            
        return result
    
    def to_json(self) -> str:
        """
        Convert the error to a JSON string.
        
        Returns:
            JSON string representation of the error
        """
        return json.dumps(self.to_dict(), default=str)


# Auth-related exceptions

class AuthenticationError(MigrationError):
    """Error occurred during authentication process."""
    pass


class AuthorizationError(MigrationError):
    """Error due to insufficient permissions or authority."""
    pass


class CredentialError(AuthenticationError):
    """Error related to credential management or retrieval."""
    pass


class TokenError(AuthenticationError):
    """Error with authentication tokens."""
    pass


# Configuration and setup exceptions

class ConfigurationError(MigrationError):
    """Error in configuration settings or environment setup."""
    pass


class ValidationError(MigrationError):
    """Error validating input data or parameters."""
    pass


class DependencyError(MigrationError):
    """Error related to missing or incompatible dependencies."""
    pass


# Resource-specific exceptions

class ResourceError(MigrationError):
    """Base class for resource-related errors."""
    
    def __init__(
        self,
        message: str,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        cause: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a resource error.
        
        Args:
            message: The error message
            resource_id: ID of the resource (if available)
            resource_type: Type of the resource (if available)
            cause: The underlying exception that caused this error
            details: Additional error details
        """
        details = details or {}
        if resource_id:
            details["resource_id"] = resource_id
        if resource_type:
            details["resource_type"] = resource_type
            
        super().__init__(message, cause, details)


class ResourceNotFoundError(ResourceError):
    """The requested resource was not found."""
    pass


class ResourceAlreadyExistsError(ResourceError):
    """The resource already exists when trying to create it."""
    pass


class ResourceExhaustedError(ResourceError):
    """Resource limits have been reached (quotas, etc.)."""
    pass


# API and communication exceptions

class APIError(MigrationError):
    """Base class for API-related errors."""
    
    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        operation: Optional[str] = None,
        status_code: Optional[Union[int, str]] = None,
        cause: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize an API error.
        
        Args:
            message: The error message
            service_name: Name of the service causing the error
            operation: Name of the operation that failed
            status_code: HTTP status code or error code
            cause: The underlying exception that caused this error
            details: Additional error details
        """
        details = details or {}
        if service_name:
            details["service_name"] = service_name
        if operation:
            details["operation"] = operation
        if status_code:
            details["status_code"] = status_code
            
        super().__init__(message, cause, details)


class TimeoutError(APIError):
    """The operation exceeded the time limit."""
    pass


class ConnectionError(APIError):
    """Error establishing a connection to a service."""
    pass


class BatchProcessingError(APIError):
    """Error processing a batch of operations."""
    
    def __init__(
        self,
        message: str,
        failed_items: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        """
        Initialize a batch processing error.
        
        Args:
            message: The error message
            failed_items: List of items that failed processing
            **kwargs: Additional arguments for APIError
        """
        details = kwargs.pop("details", {}) or {}
        if failed_items:
            details["failed_items"] = failed_items
        
        super().__init__(message, details=details, **kwargs)


# Service-specific exceptions

class GCPError(APIError):
    """Base class for all Google Cloud Platform errors."""
    pass


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


# Migration-specific exceptions

class MigrationExecutionError(MigrationError):
    """Error occurred during migration execution."""
    pass


class MigrationValidationError(ValidationError):
    """Error validating a migration plan or context."""
    pass


class MigrationRollbackError(MigrationError):
    """Error during migration rollback process."""
    pass


# Error mapping utility functions

def map_to_migration_error(
    exception: Exception,
    target_type: Type[T],
    message: Optional[str] = None,
    **kwargs
) -> T:
    """
    Map an external exception to a migration error type.
    
    Args:
        exception: The external exception to map
        target_type: The target migration error type
        message: Optional message override
        **kwargs: Additional arguments for the target error
        
    Returns:
        A new instance of the target error type
    """
    # Use the exception's message if none provided
    if not message:
        message = str(exception)
    
    # Create a new instance of the target type
    return target_type(message=message, cause=exception, **kwargs)


def map_gcp_error(
    exception: Exception,
    service_name: Optional[str] = None,
    operation: Optional[str] = None
) -> GCPError:
    """
    Map a Google Cloud exception to the appropriate GCP error type.
    
    Args:
        exception: Google Cloud exception to map
        service_name: Name of the service causing the error
        operation: Name of the operation that failed
        
    Returns:
        A mapped GCP error
    """
    error_message = str(exception)
    error_type = exception.__class__.__name__
    status_code = getattr(exception, "code", None)
    
    # Try to extract more info if available
    details = {}
    for attr in ["errors", "response", "details", "message"]:
        if hasattr(exception, attr):
            value = getattr(exception, attr)
            if value is not None:
                details[attr] = value
    
    # Map to specific error types based on the error info
    if "not found" in error_message.lower() or error_type.endswith("NotFoundError"):
        return ResourceNotFoundError(
            message=error_message,
            resource_type=service_name,
            cause=exception,
            details=details
        )
    elif "already exists" in error_message.lower() or error_type.endswith("AlreadyExistsError"):
        return ResourceAlreadyExistsError(
            message=error_message,
            resource_type=service_name,
            cause=exception,
            details=details
        )
    elif "quota" in error_message.lower() or "resource exhausted" in error_message.lower():
        return ResourceExhaustedError(
            message=error_message,
            resource_type=service_name,
            cause=exception,
            details=details
        )
    elif "permission" in error_message.lower() or "forbidden" in error_message.lower():
        return AuthorizationError(
            message=f"Access denied: {error_message}",
            cause=exception,
            details=details
        )
    elif "timeout" in error_message.lower():
        return TimeoutError(
            message=f"Operation timed out: {error_message}",
            service_name=service_name,
            operation=operation,
            cause=exception,
            details=details
        )
    elif "unauthenticated" in error_message.lower() or "unauthorized" in error_message.lower():
        return AuthenticationError(
            message=f"Authentication failed: {error_message}",
            cause=exception,
            details=details
        )
    elif "invalid argument" in error_message.lower() or "validation" in error_message.lower():
        return ValidationError(
            message=f"Validation error: {error_message}",
            cause=exception,
            details=details
        )
    
    # Service-specific error mapping
    if service_name:
        if service_name.lower() == "secretmanager" or "secret" in service_name.lower():
            return SecretError(
                message=error_message,
                service_name=service_name,
                operation=operation,
                status_code=status_code,
                cause=exception,
                details=details
            )
        elif service_name.lower() == "storage" or "gcs" in service_name.lower():
            return StorageError(
                message=error_message,
                service_name=service_name,
                operation=operation,
                status_code=status_code,
                cause=exception,
                details=details
            )
        elif service_name.lower() == "firestore":
            return FirestoreError(
                message=error_message,
                service_name=service_name,
                operation=operation,
                status_code=status_code,
                cause=exception,
                details=details
            )
        elif "vertex" in service_name.lower() or "ai" in service_name.lower():
            return VertexAIError(
                message=error_message,
                service_name=service_name,
                operation=operation,
                status_code=status_code,
                cause=exception,
                details=details
            )
    
    # Default to generic GCP error
    return GCPError(
        message=error_message,
        service_name=service_name,
        operation=operation,
        status_code=status_code,
        cause=exception,
        details=details
    )


def format_exception(exc: Exception) -> str:
    """
    Format an exception with its traceback for logging.
    
    Args:
        exc: Exception to format
        
    Returns:
        Formatted exception string with traceback
    """
    tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
    return ''.join(tb_lines)


class ErrorContext:
    """
    Context manager for standardized error handling.
    
    This context manager catches exceptions, maps them to migration errors,
    and optionally logs them or reraises them.
    """
    
    def __init__(
        self,
        operation_name: str,
        target_type: Type[MigrationError] = MigrationError,
        service_name: Optional[str] = None,
        logger: Optional[Any] = None,
        reraise: bool = True,
        message: Optional[str] = None
    ):
        """
        Initialize the error context.
        
        Args:
            operation_name: Name of the operation being performed
            target_type: Target migration error type for mapping
            service_name: Name of the service (for GCP errors)
            logger: Optional logger to log errors
            reraise: Whether to reraise caught exceptions
            message: Optional message override
        """
        self.operation_name = operation_name
        self.target_type = target_type
        self.service_name = service_name
        self.logger = logger
        self.reraise = reraise
        self.message = message
    
    def __enter__(self):
        """Enter the context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the context manager.
        
        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
            
        Returns:
            True to suppress the exception, False to propagate it
        """
        if exc_val is None:
            return False
        
        # Map the exception to a migration error
        if isinstance(exc_val, MigrationError):
            mapped_error = exc_val
        elif self.target_type == GCPError or issubclass(self.target_type, GCPError):
            mapped_error = map_gcp_error(
                exc_val,
                service_name=self.service_name,
                operation=self.operation_name
            )
        else:
            mapped_error = map_to_migration_error(
                exc_val,
                self.target_type,
                message=self.message or f"Error in {self.operation_name}",
                operation=self.operation_name
            )
        
        # Log the error if a logger is provided
        if self.logger:
            self.logger.error(
                f"Error in {self.operation_name}: {mapped_error}",
                exc_info=True
            )
        
        # Reraise the mapped error if requested
        if self.reraise:
            raise mapped_error
        
        # Suppress the original exception
        return True