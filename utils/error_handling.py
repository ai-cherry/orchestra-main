"""
Standardized error handling utilities for the entire codebase.

This module provides consistent error handling mechanisms including decorators,
context managers, and utility functions to standardize error handling practices
across all modules in the codebase.
"""

import enum
import functools
import inspect
import logging
import traceback
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast, overload

# Type variables for function signatures
T = TypeVar('T')
R = TypeVar('R')
E = TypeVar('E', bound=Exception)
F = TypeVar('F', bound=Callable[..., Any])
AsyncF = TypeVar('AsyncF', bound=Callable[..., Any])

# Configure logging
logger = logging.getLogger(__name__)


class ErrorSeverity(enum.Enum):
    """Error severity levels for standardized error handling."""
    
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class BaseError(Exception):
    """Base class for all custom exceptions in the codebase."""
    
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
    
    def __str__(self) -> str:
        """
        Get string representation of the error.
        
        Returns:
            String representation
        """
        if self.cause:
            return f"{self.message} (caused by: {type(self.cause).__name__}: {str(self.cause)})"
        return self.message


def handle_exception(
    target_error: Optional[Type[BaseError]] = None,
    logger: Optional[logging.Logger] = None,
    default_message: Optional[str] = None,
) -> Callable[[F], F]:
    """
    Decorator for consistent exception handling.
    
    Args:
        target_error: The custom error type to wrap exceptions in. If None, exceptions will be re-raised.
        logger: The logger to use. If None, a logger will be created based on the function's module.
        default_message: Default error message to use if no specific message is available.
    
    Returns:
        A decorator function
    """
    def decorator(func: F) -> F:
        # Get the logger if not provided
        nonlocal logger
        if logger is None:
            logger = logging.getLogger(func.__module__)
        
        # Get the default message if not provided
        nonlocal default_message
        if default_message is None:
            default_message = f"Error in {func.__name__}"
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except BaseError as e:
                # Log the error with appropriate severity
                log_level = {
                    ErrorSeverity.DEBUG: logger.debug,
                    ErrorSeverity.INFO: logger.info,
                    ErrorSeverity.WARNING: logger.warning,
                    ErrorSeverity.ERROR: logger.error,
                    ErrorSeverity.CRITICAL: logger.critical,
                }[e.severity]
                
                log_level(f"{type(e).__name__}: {e.message}")
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
                
                # Wrap the error in a BaseError if target_error is provided
                if target_error:
                    error_message = default_message
                    raise target_error(
                        message=error_message,
                        severity=ErrorSeverity.ERROR,
                        details={"original_error": str(e)},
                        cause=e,
                    ) from e
                else:
                    # Re-raise the original error if no target_error is specified
                    raise
        
        return cast(F, wrapper)
    
    return decorator


async def handle_async_exception(
    target_error: Optional[Type[BaseError]] = None,
    logger: Optional[logging.Logger] = None,
    default_message: Optional[str] = None,
) -> Callable[[AsyncF], AsyncF]:
    """
    Decorator for consistent async exception handling.
    
    Args:
        target_error: The custom error type to wrap exceptions in. If None, exceptions will be re-raised.
        logger: The logger to use. If None, a logger will be created based on the function's module.
        default_message: Default error message to use if no specific message is available.
    
    Returns:
        An async decorator function
    """
    def decorator(func: AsyncF) -> AsyncF:
        # Get the logger if not provided
        nonlocal logger
        if logger is None:
            logger = logging.getLogger(func.__module__)
        
        # Get the default message if not provided
        nonlocal default_message
        if default_message is None:
            default_message = f"Error in {func.__name__}"
        
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except BaseError as e:
                # Log the error with appropriate severity
                log_level = {
                    ErrorSeverity.DEBUG: logger.debug,
                    ErrorSeverity.INFO: logger.info,
                    ErrorSeverity.WARNING: logger.warning,
                    ErrorSeverity.ERROR: logger.error,
                    ErrorSeverity.CRITICAL: logger.critical,
                }[e.severity]
                
                log_level(f"{type(e).__name__}: {e.message}")
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
                
                # Wrap the error in a BaseError if target_error is provided
                if target_error:
                    error_message = default_message
                    raise target_error(
                        message=error_message,
                        severity=ErrorSeverity.ERROR,
                        details={"original_error": str(e)},
                        cause=e,
                    ) from e
                else:
                    # Re-raise the original error if no target_error is specified
                    raise
        
        return cast(AsyncF, wrapper)
    
    return decorator


@contextmanager
def error_context(
    target_error: Type[BaseError],
    message: str,
    logger: Optional[logging.Logger] = None,
    details: Optional[Dict[str, Any]] = None,
):
    """
    Context manager for error handling.
    
    Args:
        target_error: The custom error type to wrap exceptions in
        message: The error message
        logger: The logger to use. If None, a logger will be created based on the caller's module.
        details: Additional error details
    
    Yields:
        None
    
    Raises:
        target_error: If an exception occurs within the context
    """
    # Get the logger if not provided
    if logger is None:
        frame = inspect.currentframe()
        if frame and frame.f_back:
            module_name = frame.f_back.f_globals.get('__name__', '')
            logger = logging.getLogger(module_name)
        else:
            logger = logging.getLogger(__name__)
    
    try:
        yield
    except BaseError as e:
        # Log the error with appropriate severity
        log_level = {
            ErrorSeverity.DEBUG: logger.debug,
            ErrorSeverity.INFO: logger.info,
            ErrorSeverity.WARNING: logger.warning,
            ErrorSeverity.ERROR: logger.error,
            ErrorSeverity.CRITICAL: logger.critical,
        }[e.severity]
        
        log_level(f"{type(e).__name__}: {e.message}")
        if e.details:
            logger.debug(f"Details: {e.details}")
        if e.cause:
            logger.debug(f"Cause: {str(e.cause)}")
        
        # Re-raise the error
        raise
    except Exception as e:
        # Log the unexpected error
        logger.error(f"Error in context '{message}': {str(e)}")
        logger.debug(traceback.format_exc())
        
        # Wrap the error in the target_error
        raise target_error(
            message=message,
            severity=ErrorSeverity.ERROR,
            details=details or {"original_error": str(e)},
            cause=e,
        ) from e


def safe_execute(
    func: Callable[..., T],
    *args: Any,
    default: T = None,
    log_errors: bool = True,
    logger: Optional[logging.Logger] = None,
    **kwargs: Any,
) -> T:
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


async def safe_execute_async(
    func: Callable[..., Any],
    *args: Any,
    default: Any = None,
    log_errors: bool = True,
    logger: Optional[logging.Logger] = None,
    **kwargs: Any,
) -> Any:
    """
    Safely execute an async function and return a default value if it fails.
    
    Args:
        func: The async function to execute
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
        return await func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logger.error(f"Error executing {func.__name__}: {str(e)}")
            logger.debug(traceback.format_exc())
        return default
