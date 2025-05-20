"""
Error handling utilities for the GCP Migration toolkit.

This module provides consistent error handling behavior throughout
the application, including:
- Error wrapping
- Contextual error information
- Decorators for common error handling patterns
"""

import functools
import inspect
import sys
import traceback
from contextlib import contextmanager
from typing import Any, Callable, Dict, Generator, Optional, Type, TypeVar, Union, cast

from gcp_migration.domain.exceptions import MigrationError
from gcp_migration.utils.logging import get_logger


logger = get_logger(__name__)

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


def wrap_exceptions(
    target_exception: Type[MigrationError],
    source_exceptions: Union[Type[Exception], tuple[Type[Exception], ...]],
    message: str = "An error occurred",
) -> Callable[[F], F]:
    """
    Decorator to wrap source exceptions into a target exception type.

    Args:
        target_exception: The exception type to wrap to (must be a MigrationError subclass)
        source_exceptions: The exception type(s) to catch
        message: The error message to use

    Returns:
        Decorator function

    Example:
        @wrap_exceptions(StorageError, (IOError, OSError), "Failed to access storage")
        def read_file(path: str) -> str:
            with open(path, "r") as f:
                return f.read()
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except source_exceptions as e:
                context = {
                    "function": func.__name__,
                    "args": str(args) if args else None,
                    "kwargs": str(kwargs) if kwargs else None,
                    "exception_type": e.__class__.__name__,
                }

                logger.error(f"{message}: {str(e)}", extra={"context": context})
                # Use the proper constructor for MigrationError
                raise target_exception(message=message, cause=e, details=context) from e

        return cast(F, wrapper)

    return decorator


def async_wrap_exceptions(
    target_exception: Type[MigrationError],
    source_exceptions: Union[Type[Exception], tuple[Type[Exception], ...]],
    message: str = "An error occurred",
) -> Callable[[F], F]:
    """
    Decorator to wrap source exceptions into a target exception type for async functions.

    Args:
        target_exception: The exception type to wrap to (must be a MigrationError subclass)
        source_exceptions: The exception type(s) to catch
        message: The error message to use

    Returns:
        Decorator function

    Example:
        @async_wrap_exceptions(DBError, (asyncpg.PostgresError,), "Database operation failed")
        async def fetch_user(user_id: int) -> dict:
            return await db.fetch_one("SELECT * FROM users WHERE id = $1", user_id)
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except source_exceptions as e:
                context = {
                    "function": func.__name__,
                    "args": str(args) if args else None,
                    "kwargs": str(kwargs) if kwargs else None,
                    "exception_type": e.__class__.__name__,
                }

                logger.error(f"{message}: {str(e)}", extra={"context": context})
                # Use the proper constructor for MigrationError
                raise target_exception(message=message, cause=e, details=context) from e

        return cast(F, wrapper)

    return decorator


@contextmanager
def error_context(
    error_class: Type[MigrationError],
    message: str,
    reraise: bool = True,
    log_level: str = "error",
) -> Generator[None, None, None]:
    """
    Context manager for handling exceptions within a block.

    Args:
        error_class: The exception class to raise if an error occurs (must be a MigrationError subclass)
        message: The error message
        reraise: Whether to reraise the exception
        log_level: The log level to use (debug, info, warning, error, critical)

    Yields:
        None

    Example:
        with error_context(FileError, "Failed to read config file"):
            config = read_config_file("config.yaml")
    """
    try:
        yield
    except Exception as e:
        # Get caller information
        frame = inspect.currentframe()
        if frame is not None:
            frame = frame.f_back
        if frame is not None:
            caller = f"{frame.f_code.co_filename}:{frame.f_lineno}"
        else:
            caller = "unknown"

        # Create context with call stack
        context = {
            "caller": caller,
            "exception_type": e.__class__.__name__,
            "traceback": traceback.format_exc(),
        }

        # Log the error
        log_func = getattr(logger, log_level)
        log_func(f"{message}: {str(e)}", extra={"context": context})

        # Raise the wrapped exception
        if reraise:
            if isinstance(e, error_class):
                raise
            else:
                # Use the proper constructor for MigrationError
                raise error_class(message=message, cause=e, details=context) from e


def log_exceptions(
    log_level: str = "error",
    reraise: bool = True,
) -> Callable[[F], F]:
    """
    Decorator to log exceptions without changing their type.

    Args:
        log_level: The log level to use (debug, info, warning, error, critical)
        reraise: Whether to reraise the exception

    Returns:
        Decorator function

    Example:
        @log_exceptions()
        def process_file(path: str) -> dict:
            with open(path, "r") as f:
                return json.load(f)
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Capture context details
                context = {
                    "function": func.__name__,
                    "args": str(args) if args else None,
                    "kwargs": str(kwargs) if kwargs else None,
                    "exception_type": e.__class__.__name__,
                    "traceback": traceback.format_exc(),
                }

                # Log the exception
                log_func = getattr(logger, log_level)
                log_func(
                    f"Exception in {func.__name__}: {str(e)}",
                    extra={"context": context},
                )

                # Reraise if requested
                if reraise:
                    raise

                # Return None if not reraising
                return None

        return cast(F, wrapper)

    return decorator


def async_log_exceptions(
    log_level: str = "error",
    reraise: bool = True,
) -> Callable[[F], F]:
    """
    Decorator to log exceptions without changing their type for async functions.

    Args:
        log_level: The log level to use (debug, info, warning, error, critical)
        reraise: Whether to reraise the exception

    Returns:
        Decorator function

    Example:
        @async_log_exceptions()
        async def process_file(path: str) -> dict:
            async with aiofiles.open(path, "r") as f:
                content = await f.read()
                return json.loads(content)
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Capture context details
                context = {
                    "function": func.__name__,
                    "args": str(args) if args else None,
                    "kwargs": str(kwargs) if kwargs else None,
                    "exception_type": e.__class__.__name__,
                    "traceback": traceback.format_exc(),
                }

                # Log the exception
                log_func = getattr(logger, log_level)
                log_func(
                    f"Exception in {func.__name__}: {str(e)}",
                    extra={"context": context},
                )

                # Reraise if requested
                if reraise:
                    raise

                # Return None if not reraising
                return None

        return cast(F, wrapper)

    return decorator


def extract_error_details(exception: Exception) -> Dict[str, Any]:
    """
    Extract detailed information from an exception.

    Args:
        exception: The exception to extract details from

    Returns:
        Dictionary with error details
    """
    # Base details
    details = {
        "error_type": exception.__class__.__name__,
        "error_message": str(exception),
        "traceback": traceback.format_exception_only(type(exception), exception),
    }

    # Full traceback
    tb = (
        traceback.format_tb(exception.__traceback__)
        if exception.__traceback__
        else None
    )
    if tb:
        details["full_traceback"] = tb

    # Original cause
    if isinstance(exception, MigrationError) and exception.cause:
        details["cause"] = {
            "error_type": exception.cause.__class__.__name__,
            "error_message": str(exception.cause),
        }

    # Additional context
    if isinstance(exception, MigrationError) and exception.details:
        details["context"] = exception.details

    return details


def format_error_for_user(exception: Exception) -> str:
    """
    Format an exception into a user-friendly error message.

    Args:
        exception: The exception to format

    Returns:
        Formatted error message suitable for display to users
    """
    if isinstance(exception, MigrationError):
        # Format domain exceptions nicely
        message = f"Error: {exception.message}"

        # Add cause if available
        if exception.cause:
            message += (
                f"\nCause: {exception.cause.__class__.__name__}: {str(exception.cause)}"
            )

        return message
    else:
        # Generic message for unexpected exceptions
        return f"An unexpected error occurred: {exception.__class__.__name__}: {str(exception)}"


def get_traceback_string() -> str:
    """
    Get the current exception traceback as a string.

    Returns:
        Formatted traceback string
    """
    exc_type, exc_value, exc_traceback = sys.exc_info()
    if exc_type is None or exc_value is None or exc_traceback is None:
        return "No exception in context"

    return "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
