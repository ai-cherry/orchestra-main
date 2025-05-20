"""
Error handling for WIF implementation.

This module provides error handling utilities for the WIF implementation.
"""

import enum
import functools
import logging
import traceback
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union, cast

F = TypeVar("F", bound=Callable[..., Any])


class ErrorSeverity(enum.Enum):
    """Error severity levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class WIFError(Exception):
    """Base class for WIF implementation errors."""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            severity: Error severity
            details: Additional error details
            cause: The underlying exception that caused this error
        """
        self.message = message
        self.severity = severity
        self.details = details or {}
        self.cause = cause
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the error to a dictionary.

        Returns:
            Dictionary representation of the error
        """
        result = {
            "message": self.message,
            "severity": self.severity.value,
            "details": self.details,
        }

        if self.cause:
            result["cause"] = str(self.cause)

        return result


def handle_exception(logger: Optional[logging.Logger] = None) -> Callable[[F], F]:
    """
    Decorator for consistent exception handling.

    Args:
        logger: The logger to use for logging exceptions.
              If None, a logger will be created based on the function's module.

    Returns:
        A decorator function
    """

    def decorator(func: F) -> F:
        # Get the logger if not provided
        nonlocal logger
        if logger is None:
            logger = logging.getLogger(func.__module__)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except WIFError as e:
                # Log the error
                log_level = {
                    ErrorSeverity.DEBUG: logger.debug,
                    ErrorSeverity.INFO: logger.info,
                    ErrorSeverity.WARNING: logger.warning,
                    ErrorSeverity.ERROR: logger.error,
                    ErrorSeverity.CRITICAL: logger.critical,
                }[e.severity]

                log_level(f"WIFError: {e.message}")
                if e.details:
                    logger.debug(f"Details: {e.details}")
                if e.cause:
                    logger.debug(f"Cause: {str(e.cause)}")

                # Re-raise the error
                raise
            except Exception as e:
                # Log the unexpected error
                logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                logger.debug(traceback.format_exc())

                # Wrap the error in a WIFError
                raise WIFError(
                    message=f"An unexpected error occurred in {func.__name__}",
                    severity=ErrorSeverity.ERROR,
                    details={"original_error": str(e)},
                    cause=e,
                ) from e

        return cast(F, wrapper)

    return decorator


def safe_execute(
    func: Callable[..., Any],
    *args: Any,
    default: Any = None,
    log_errors: bool = True,
    logger: Optional[logging.Logger] = None,
    **kwargs: Any,
) -> Any:
    """
    Safely execute a function and return a default value if it fails.

    Args:
        func: The function to execute
        *args: Positional arguments to pass to the function
        default: The default value to return if the function fails
        log_errors: Whether to log errors
        logger: The logger to use for logging errors
        **kwargs: Keyword arguments to pass to the function

    Returns:
        The result of the function, or the default value if it fails
    """
    if logger is None:
        logger = logging.getLogger(func.__module__)

    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logger.error(f"Error executing {func.__name__}: {str(e)}")
            logger.debug(traceback.format_exc())
        return default
