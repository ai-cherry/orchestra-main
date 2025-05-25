"""
Error handling utilities for AI Orchestra.

This module provides utilities for consistent error handling across the application.
It extends the basic error handling in errors.py with more advanced features like
context managers, support for both sync and async functions, and better logging.
"""

import asyncio
import functools
import logging
import time
import traceback
from typing import (
    Any,
    Callable,
    Optional,
    ParamSpec,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

from .errors import AIServiceError

# Type variables for function signatures
T = TypeVar("T")
P = ParamSpec("P")
F = TypeVar("F", bound=Callable[..., Any])


def _handle_error(func_name: str, e: Exception, logger: logging.Logger) -> None:
    """
    Common error handling logic for both sync and async functions.

    Args:
        func_name: The name of the function where the error occurred
        e: The exception that was raised
        logger: The logger to use for logging the error

    Raises:
        AIServiceError: Always raised, either the original one or a wrapped one
    """
    if isinstance(e, AIServiceError):
        # Log the error
        logger.error(f"AIServiceError in {func_name}: {e.code}:{e.message}")
        if e.details:
            logger.debug(f"Error details: {e.details}")
        if e.cause:
            logger.debug(f"Error cause: {str(e.cause)}")

        # Re-raise the error
        raise
    else:
        # Log the unexpected error
        logger.error(f"Unexpected error in {func_name}: {str(e)}")
        logger.debug(traceback.format_exc())

        # Wrap the error in an AIServiceError
        raise AIServiceError(
            code="UNEXPECTED_ERROR",
            message=f"An unexpected error occurred in {func_name}",
            details={"original_error": str(e), "traceback": traceback.format_exc()},
            cause=e,
        )


@overload
def handle_exception(func: F) -> F: ...


@overload
def handle_exception(
    *, logger: Optional[logging.Logger] = None
) -> Callable[[F], F]: ...


def handle_exception(
    func: Optional[F] = None, *, logger: Optional[logging.Logger] = None
) -> Union[F, Callable[[F], F]]:
    """
    Decorator for consistent exception handling.

    This decorator wraps a function to provide consistent exception handling.
    It logs exceptions and wraps them in AIServiceError if they are not already.
    It works with both synchronous and asynchronous functions.

    Args:
        func: The function to decorate
        logger: The logger to use for logging exceptions.
              If None, a logger will be created based on the function's module.

    Returns:
        The decorated function or a decorator function

    Example:
        ```python
        # Simple usage
        @handle_exception
        async def my_function():
            # Function implementation

        # With custom logger
        @handle_exception(logger=custom_logger)
        async def my_function():
            # Function implementation
        ```
    """

    def decorator(func: F) -> F:
        # Get the logger if not provided
        nonlocal logger
        if logger is None:
            logger = logging.getLogger(func.__module__)

        func_name = func.__qualname__

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                _handle_error(func_name, e, logger)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                _handle_error(func_name, e, logger)

        # Return the appropriate wrapper based on whether the function is async
        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)

    # Handle both @handle_exception and @handle_exception(logger=...)
    if func is None:
        return decorator
    else:
        return decorator(func)


def safe_execute(
    func: Callable[P, T],
    *args: P.args,
    default: Optional[T] = None,
    log_errors: bool = True,
    **kwargs: P.kwargs,
) -> Optional[T]:
    """
    Safely execute a function and return a default value if it fails.

    Args:
        func: The function to execute
        *args: Positional arguments to pass to the function
        default: The default value to return if the function fails
        log_errors: Whether to log errors
        **kwargs: Keyword arguments to pass to the function

    Returns:
        The result of the function, or the default value if it fails
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logger = logging.getLogger(func.__module__)
            logger.error(f"Error executing {func.__name__}: {str(e)}")
            logger.debug(traceback.format_exc())
        return default


async def safe_execute_async(
    func: Callable[P, Any],
    *args: P.args,
    default: Any = None,
    log_errors: bool = True,
    **kwargs: P.kwargs,
) -> Any:
    """
    Safely execute an async function and return a default value if it fails.

    Args:
        func: The async function to execute
        *args: Positional arguments to pass to the function
        default: The default value to return if the function fails
        log_errors: Whether to log errors
        **kwargs: Keyword arguments to pass to the function

    Returns:
        The result of the function, or the default value if it fails
    """
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logger = logging.getLogger(func.__module__)
            logger.error(f"Error executing async {func.__name__}: {str(e)}")
            logger.debug(traceback.format_exc())
        return default


class ErrorContext:
    """
    Context manager for error handling.

    This context manager provides consistent error handling for a block of code.
    It logs exceptions and wraps them in AIServiceError if they are not already.

    Example:
        ```python
        with ErrorContext("operation_name", logger):
            # Code that might raise exceptions
        ```
    """

    def __init__(
        self,
        operation_name: str,
        logger: Optional[logging.Logger] = None,
        error_code: str = "OPERATION_ERROR",
    ):
        """
        Initialize the error context.

        Args:
            operation_name: The name of the operation being performed
            logger: The logger to use for logging exceptions
            error_code: The error code to use for wrapped exceptions
        """
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger(__name__)
        self.error_code = error_code

    def __enter__(self) -> "ErrorContext":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[traceback.TracebackType],
    ) -> bool:
        if exc_val is not None:
            if isinstance(exc_val, AIServiceError):
                # Log the error
                self.logger.error(
                    f"AIServiceError in {self.operation_name}: {exc_val.code}:{exc_val.message}"
                )
                if exc_val.details:
                    self.logger.debug(f"Error details: {exc_val.details}")
                if exc_val.cause:
                    self.logger.debug(f"Error cause: {str(exc_val.cause)}")

                # Don't suppress the exception
                return False
            else:
                # Log the unexpected error
                self.logger.error(
                    f"Unexpected error in {self.operation_name}: {str(exc_val)}"
                )
                self.logger.debug(traceback.format_exc())

                # Wrap the error in an AIServiceError
                raise AIServiceError(
                    code=self.error_code,
                    message=f"An error occurred during {self.operation_name}",
                    details={
                        "original_error": str(exc_val),
                        "traceback": traceback.format_exc(),
                    },
                    cause=exc_val,
                ) from exc_val

        return False


class AsyncErrorContext:
    """
    Async context manager for error handling.

    This async context manager provides consistent error handling for a block of async code.
    It logs exceptions and wraps them in AIServiceError if they are not already.

    Example:
        ```python
        async with AsyncErrorContext("operation_name", logger):
            # Async code that might raise exceptions
        ```
    """

    def __init__(
        self,
        operation_name: str,
        logger: Optional[logging.Logger] = None,
        error_code: str = "OPERATION_ERROR",
    ):
        """
        Initialize the async error context.

        Args:
            operation_name: The name of the operation being performed
            logger: The logger to use for logging exceptions
            error_code: The error code to use for wrapped exceptions
        """
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger(__name__)
        self.error_code = error_code

    async def __aenter__(self) -> "AsyncErrorContext":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[traceback.TracebackType],
    ) -> bool:
        if exc_val is not None:
            if isinstance(exc_val, AIServiceError):
                # Log the error
                self.logger.error(
                    f"AIServiceError in {self.operation_name}: {exc_val.code}:{exc_val.message}"
                )
                if exc_val.details:
                    self.logger.debug(f"Error details: {exc_val.details}")
                if exc_val.cause:
                    self.logger.debug(f"Error cause: {str(exc_val.cause)}")

                # Don't suppress the exception
                return False
            else:
                # Log the unexpected error
                self.logger.error(
                    f"Unexpected error in {self.operation_name}: {str(exc_val)}"
                )
                self.logger.debug(traceback.format_exc())

                # Wrap the error in an AIServiceError
                raise AIServiceError(
                    code=self.error_code,
                    message=f"An error occurred during {self.operation_name}",
                    details={
                        "original_error": str(exc_val),
                        "traceback": traceback.format_exc(),
                    },
                    cause=exc_val,
                ) from exc_val

        return False


def retry(
    max_attempts: int = 3,
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0,
    retry_exceptions: Optional[
        Union[Type[Exception], Tuple[Type[Exception], ...]]
    ] = None,
    logger: Optional[logging.Logger] = None,
) -> Callable[[F], F]:
    """
    Decorator for retrying a function on failure.

    Args:
        max_attempts: Maximum number of attempts
        retry_delay: Initial delay between retries in seconds
        backoff_factor: Factor to increase delay for each retry
        retry_exceptions: Exceptions to retry on, defaults to Exception
        logger: Logger to use for logging retries

    Returns:
        Decorated function

    Example:
        ```python
        @retry(max_attempts=3, retry_exceptions=(ConnectionError, TimeoutError))
        async def fetch_data():
            # Function implementation
        ```
    """
    if retry_exceptions is None:
        retry_exceptions = Exception

    def decorator(func: F) -> F:
        nonlocal logger
        if logger is None:
            logger = logging.getLogger(func.__module__)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            current_delay = retry_delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except retry_exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {current_delay:.2f}s..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {str(e)}"
                        )

            if last_exception:
                raise last_exception

            # This should never happen, but just in case
            raise RuntimeError(f"Unexpected error in retry logic for {func.__name__}")

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            current_delay = retry_delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retry_exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {current_delay:.2f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {str(e)}"
                        )

            if last_exception:
                raise last_exception

            # This should never happen, but just in case
            raise RuntimeError(f"Unexpected error in retry logic for {func.__name__}")

        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)

    return decorator
