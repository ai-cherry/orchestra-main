#!/usr/bin/env python3
"""
AI Orchestra GCP Migration Error Handling Framework

This module provides standardized error handling for the GCP migration process,
including error classification, structured logging, and retry mechanisms.

Author: Roo
"""

import functools
import json
import logging
import sys
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Type, TypeVar, Union, cast

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("gcp-migration")

# Type variable for function decorators
F = TypeVar("F", bound=Callable[..., Any])


class ErrorSeverity(Enum):
    """Error severity levels for migration errors."""

    INFO = "info"  # Informational, non-critical
    WARNING = "warning"  # Warning, operation continued but with issues
    ERROR = "error"  # Error, operation failed but non-fatal for migration
    CRITICAL = "critical"  # Critical, migration phase should be aborted
    FATAL = "fatal"  # Fatal, entire migration should be aborted


class ErrorCategory(Enum):
    """Categories of migration errors for better classification."""

    AUTHENTICATION = "authentication"  # Authentication/authorization issues
    CONFIGURATION = "configuration"  # Configuration errors (missing values, validation)
    NETWORK = "network"  # Network connectivity issues
    RESOURCE = "resource"  # GCP resource errors (not found, quota, etc)
    API = "api"  # GCP API errors
    DATA = "data"  # Data-related errors (format, validation)
    DEPENDENCY = "dependency"  # Missing dependencies
    INTERNAL = "internal"  # Internal errors in the migration code
    UNKNOWN = "unknown"  # Unclassified errors


@dataclass
class MigrationError(Exception):
    """Base class for all migration errors.

    This class provides structured error information including severity,
    category, error code, and context for better error tracking and reporting.
    """

    message: str
    severity: ErrorSeverity = ErrorSeverity.ERROR
    category: ErrorCategory = ErrorCategory.UNKNOWN
    error_code: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    is_transient: bool = False
    timestamp: float = field(default_factory=time.time)
    traceback_info: Optional[str] = None

    def __post_init__(self):
        """Initialize the parent Exception class."""
        super().__init__(self.message)
        if not self.traceback_info:
            self.traceback_info = traceback.format_exc()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary for serialization.

        Returns:
            Dict representation of the error
        """
        return {
            "message": self.message,
            "severity": self.severity.value,
            "category": self.category.value,
            "error_code": self.error_code,
            "context": self.context,
            "is_transient": self.is_transient,
            "timestamp": self.timestamp,
            "traceback": self.traceback_info
            if self.traceback_info != "None\n"
            else None,
        }

    def to_json(self) -> str:
        """Convert the error to a JSON string.

        Returns:
            JSON representation of the error
        """
        return json.dumps(self.to_dict())

    def log(self):
        """Log the error with the appropriate severity level."""
        error_dict = self.to_dict()

        # Add more context to the log message
        context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
        log_msg = f"{self.message}"
        if context_str:
            log_msg += f" [{context_str}]"

        if self.error_code:
            log_msg = f"[{self.error_code}] {log_msg}"

        # Log with appropriate severity
        if self.severity == ErrorSeverity.INFO:
            logger.info(log_msg)
        elif self.severity == ErrorSeverity.WARNING:
            logger.warning(log_msg)
        elif self.severity == ErrorSeverity.ERROR:
            logger.error(log_msg)
        elif self.severity in (ErrorSeverity.CRITICAL, ErrorSeverity.FATAL):
            logger.critical(log_msg)

            # For fatal errors, print traceback for immediate visibility
            if self.severity == ErrorSeverity.FATAL and self.traceback_info:
                logger.critical(f"Traceback:\n{self.traceback_info}")


# Specific error types


class AuthenticationError(MigrationError):
    """Error related to GCP authentication."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.AUTHENTICATION,
            error_code=error_code or "AUTH_ERROR",
            context=context or {},
            **kwargs,
        )


class ConfigurationError(MigrationError):
    """Error related to migration configuration."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.CONFIGURATION,
            error_code=error_code or "CONFIG_ERROR",
            context=context or {},
            **kwargs,
        )


class NetworkError(MigrationError):
    """Error related to network connectivity."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.NETWORK,
            error_code=error_code or "NETWORK_ERROR",
            context=context or {},
            is_transient=True,  # Network errors are often transient
            **kwargs,
        )


class ResourceError(MigrationError):
    """Error related to GCP resource operations."""

    def __init__(
        self,
        message: str,
        resource_type: str,
        resource_name: str,
        operation: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        context = context or {}
        context.update(
            {
                "resource_type": resource_type,
                "resource_name": resource_name,
                "operation": operation,
            }
        )
        super().__init__(
            message=message,
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.RESOURCE,
            error_code=error_code or "RESOURCE_ERROR",
            context=context,
            **kwargs,
        )


class ApiError(MigrationError):
    """Error related to GCP API calls."""

    def __init__(
        self,
        message: str,
        api_name: str,
        method: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        context = context or {}
        context.update(
            {
                "api_name": api_name,
                "method": method,
            }
        )
        if status_code is not None:
            context["status_code"] = status_code

        # Determine if the error is likely transient based on status code
        is_transient = False
        if status_code:
            # 408 (Timeout), 429 (Too Many Requests), 5xx (Server errors)
            is_transient = status_code in (408, 429) or (
                status_code >= 500 and status_code < 600
            )

        super().__init__(
            message=message,
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.API,
            error_code=error_code or "API_ERROR",
            context=context,
            is_transient=is_transient,
            **kwargs,
        )


class DataError(MigrationError):
    """Error related to data format or validation."""

    def __init__(
        self,
        message: str,
        data_type: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        context = context or {}
        context["data_type"] = data_type
        super().__init__(
            message=message,
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.DATA,
            error_code=error_code or "DATA_ERROR",
            context=context,
            **kwargs,
        )


class DependencyError(MigrationError):
    """Error related to missing or incompatible dependencies."""

    def __init__(
        self,
        message: str,
        dependency: str,
        required_version: Optional[str] = None,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        context = context or {}
        context["dependency"] = dependency
        if required_version:
            context["required_version"] = required_version
        super().__init__(
            message=message,
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.DEPENDENCY,
            error_code=error_code or "DEPENDENCY_ERROR",
            context=context,
            **kwargs,
        )


# Retry functionality


def retry_on_exception(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: Optional[Set[Type[Exception]]] = None,
    retryable_return_values: Optional[Set[Any]] = None,
    logger_instance: Optional[logging.Logger] = None,
) -> Callable[[F], F]:
    """Retry decorator for functions that may raise exceptions.

    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries in seconds
        backoff_factor: Exponential backoff factor for retry delay
        retryable_exceptions: Set of exception types to retry on, if not provided,
            retries on MigrationError if is_transient is True
        retryable_return_values: Set of return values to retry on
        logger_instance: Logger to use for retry messages

    Returns:
        Decorator function
    """
    retryable_exceptions = retryable_exceptions or set()
    retryable_return_values = retryable_return_values or set()
    logger_instance = logger_instance or logger

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 0
            current_delay = retry_delay

            while True:
                attempt += 1
                try:
                    result = func(*args, **kwargs)

                    # Check if we should retry based on return value
                    if retryable_return_values and result in retryable_return_values:
                        if attempt <= max_retries:
                            logger_instance.info(
                                f"Retrying {func.__name__} due to return value: {result} "
                                f"(attempt {attempt}/{max_retries})"
                            )
                            time.sleep(current_delay)
                            current_delay *= backoff_factor
                            continue

                    # Success
                    return result

                except Exception as e:
                    # Check if we should retry based on exception type
                    should_retry = False

                    # Check if it's a retryable exception type
                    if any(
                        isinstance(e, exc_type) for exc_type in retryable_exceptions
                    ):
                        should_retry = True

                    # Check if it's a MigrationError and is_transient
                    elif isinstance(e, MigrationError) and e.is_transient:
                        should_retry = True

                    # Retry if conditions met and attempts remaining
                    if should_retry and attempt <= max_retries:
                        logger_instance.warning(
                            f"Retrying {func.__name__} due to exception: {str(e)} "
                            f"(attempt {attempt}/{max_retries})"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                        continue

                    # Max retries reached or not retryable
                    raise

        return cast(F, wrapper)

    return decorator


# Error classification helper


def classify_exception(exception: Exception) -> MigrationError:
    """Convert any exception to a MigrationError with proper classification.

    Args:
        exception: The exception to classify

    Returns:
        A MigrationError instance
    """
    # If it's already a MigrationError, just return it
    if isinstance(exception, MigrationError):
        return exception

    # Google Auth errors
    if "google.auth" in str(type(exception)):
        return AuthenticationError(
            message=str(exception),
            error_code="GOOGLE_AUTH_ERROR",
            context={"original_exception": str(type(exception).__name__)},
        )

    # Google API errors
    elif "google.api_core" in str(type(exception)):
        return ApiError(
            message=str(exception),
            api_name="Google Cloud API",
            method="unknown",
            error_code="GOOGLE_API_ERROR",
            context={"original_exception": str(type(exception).__name__)},
        )

    # Connection/network errors
    elif any(
        net_err in str(type(exception).__name__.lower())
        for net_err in ["connection", "timeout", "network"]
    ):
        return NetworkError(
            message=str(exception),
            error_code="NETWORK_CONNECTIVITY_ERROR",
            context={"original_exception": str(type(exception).__name__)},
        )

    # Default to unknown error
    else:
        return MigrationError(
            message=str(exception),
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.UNKNOWN,
            error_code="UNKNOWN_ERROR",
            context={"original_exception": str(type(exception).__name__)},
        )


# Context manager for error handling


class ErrorHandler:
    """Context manager for standardized error handling.

    Usage:
        with ErrorHandler("Operation description", context={"key": "value"}) as handler:
            # Code that might raise exceptions
            result = risky_operation()

            # Can add contexts during execution
            handler.add_context("result_id", result.id)
    """

    def __init__(
        self,
        operation: str,
        context: Optional[Dict[str, Any]] = None,
        fatal_on_error: bool = False,
        logger_instance: Optional[logging.Logger] = None,
    ):
        """Initialize the error handler.

        Args:
            operation: Description of the operation being performed
            context: Initial context for error reporting
            fatal_on_error: If True, will exit the process on error
            logger_instance: Logger to use (defaults to module logger)
        """
        self.operation = operation
        self.context = context or {}
        self.context["operation"] = operation
        self.fatal_on_error = fatal_on_error
        self.logger = logger_instance or logger
        self.error = None

    def __enter__(self):
        """Enter the context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Handle exceptions raised in the context.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback

        Returns:
            True if exception was handled, False otherwise
        """
        if exc_val is not None:
            # Convert to MigrationError if it's not already
            if not isinstance(exc_val, MigrationError):
                self.error = classify_exception(exc_val)
                self.error.context.update(self.context)
            else:
                self.error = exc_val
                self.error.context.update(self.context)

            # Log the error
            self.error.log()

            # Exit if fatal
            if self.fatal_on_error:
                self.logger.critical(f"Fatal error during {self.operation}. Exiting.")
                sys.exit(1)

            # Indicate that we've handled the exception
            return True

        return False

    def add_context(self, key: str, value: Any):
        """Add context information during execution.

        Args:
            key: Context key
            value: Context value
        """
        self.context[key] = value


# Test the error handling framework if run directly
if __name__ == "__main__":
    # Configure more detailed logging for the test
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Test basic error creation and logging
    print("Testing basic error creation and logging...")
    error = MigrationError(
        message="Test migration error",
        severity=ErrorSeverity.WARNING,
        context={"test_key": "test_value"},
    )
    error.log()
    print(f"Error as JSON: {error.to_json()}")

    # Test retry decorator
    print("\nTesting retry decorator...")

    @retry_on_exception(max_retries=3, retry_delay=0.1)
    def flaky_function(succeed_on_attempt: int, current_attempts: list):
        """A function that succeeds only after a certain number of attempts."""
        current_attempts[0] += 1
        print(f"Attempt {current_attempts[0]}")
        if current_attempts[0] < succeed_on_attempt:
            raise NetworkError(
                "Temporary network issue", error_code="TEST_NETWORK_ERROR"
            )
        return "Success!"

    try:
        attempts = [0]
        result = flaky_function(3, attempts)
        print(f"Function succeeded after {attempts[0]} attempts with result: {result}")
    except Exception as e:
        print(f"Function failed with exception: {e}")

    # Test error handler context manager
    print("\nTesting error handler context manager...")

    try:
        with ErrorHandler("test operation", context={"test": True}) as handler:
            handler.add_context("added_during", "execution")
            # This will raise an error
            raise ValueError("Test value error")
    except Exception as e:
        print(f"Caught exception: {e}")

    print("Error handling tests complete")
