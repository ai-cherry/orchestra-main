"""
Consolidated error handling framework for the entire codebase.

This implementation provides a unified approach to error handling across all modules,
combining the functionality from:
- utils/error_handling.py
- gcp_migration/utils/error_handling.py
- wif_implementation/error_handler.py

Usage:
    1. Import the base utilities from this module
    2. Import domain-specific errors from their respective modules
    3. Use the decorators and utilities as needed
"""

import asyncio
import enum
import functools
import inspect
import logging
import random
import time
import traceback
from contextlib import contextmanager
from typing import Any, Callable, Dict, Optional, Type, TypeVar, cast

# Type variables for function signatures
T = TypeVar("T")
R = TypeVar("R")
E = TypeVar("E", bound=Exception)
F = TypeVar("F", bound=Callable[..., Any])
AsyncF = TypeVar("AsyncF", bound=Callable[..., Any])

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

    Example:
        @handle_exception(target_error=ConfigError)
        def load_config(path: str) -> dict:
            with open(path) as f:
                return json.load(f)
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


def handle_async_exception(
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

    Example:
        @handle_async_exception(target_error=DatabaseError)
        async def fetch_records(query: str) -> List[Dict]:
            async with db.connection() as conn:
                return await conn.execute(query)
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

    Example:
        with error_context(DatabaseError, "Error updating user record", details={"user_id": 123}):
            db.update_user(user_id=123, data={"status": "active"})
    """
    # Get the logger if not provided
    if logger is None:
        frame = inspect.currentframe()
        if frame and frame.f_back:
            module_name = frame.f_back.f_globals.get("__name__", "")
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

    Example:
        result = safe_execute(parse_json, data, default={})
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

    Example:
        result = await safe_execute_async(fetch_data, url, default=[])
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


def with_retry(
    max_attempts: int = 3,
    initial_backoff: float = 1.0,
    max_backoff: float = 30.0,
    backoff_multiplier: float = 2.0,
    jitter: float = 0.1,
    retryable_errors: Optional[tuple[Type[Exception], ...]] = None,
) -> Callable[[F], F]:
    """
    Decorator that adds retry logic with exponential backoff and jitter.

    Args:
        max_attempts: Maximum number of retry attempts
        initial_backoff: Initial backoff time in seconds
        max_backoff: Maximum backoff time in seconds
        backoff_multiplier: Multiplier for exponential backoff
        jitter: Random jitter factor to add to backoff
        retryable_errors: Tuple of exception types that should trigger retry.
                         If None, retries on all exceptions.

    Returns:
        A decorator function

    Example:
        @with_retry(max_attempts=5, retryable_errors=(ConnectionError, TimeoutError))
        def fetch_data(url: str) -> dict:
            return requests.get(url).json()
    """
    if retryable_errors is None:
        retryable_errors = (Exception,)

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_errors as e:
                    last_exception = e

                    if attempt == max_attempts:
                        # Last attempt failed, re-raise the exception
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}",
                            exc_info=True,
                        )
                        raise

                    # Calculate backoff with jitter
                    backoff = min(
                        initial_backoff * (backoff_multiplier ** (attempt - 1)),
                        max_backoff,
                    )
                    # Add jitter
                    actual_backoff = backoff * (1 + random.uniform(-jitter, jitter))

                    logger.warning(
                        f"Attempt {attempt} failed for {func.__name__}, " f"retrying in {actual_backoff:.2f}s: {str(e)}"
                    )

                    # Wait before retrying
                    time.sleep(actual_backoff)

            # This should never be reached, but for type safety
            if last_exception:
                raise last_exception
            return None

        return cast(F, wrapper)

    return decorator


async def with_async_retry(
    max_attempts: int = 3,
    initial_backoff: float = 1.0,
    max_backoff: float = 30.0,
    backoff_multiplier: float = 2.0,
    jitter: float = 0.1,
    retryable_errors: Optional[tuple[Type[Exception], ...]] = None,
) -> Callable[[AsyncF], AsyncF]:
    """
    Async version of the retry decorator.

    Args:
        max_attempts: Maximum number of retry attempts
        initial_backoff: Initial backoff time in seconds
        max_backoff: Maximum backoff time in seconds
        backoff_multiplier: Multiplier for exponential backoff
        jitter: Random jitter factor to add to backoff
        retryable_errors: Tuple of exception types that should trigger retry.
                         If None, retries on all exceptions.

    Returns:
        An async decorator function

    Example:
        @with_async_retry(max_attempts=5, retryable_errors=(aiohttp.ClientError,))
        async def fetch_data_async(url: str) -> dict:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.json()
    """
    if retryable_errors is None:
        retryable_errors = (Exception,)

    def decorator(func: AsyncF) -> AsyncF:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_errors as e:
                    last_exception = e

                    if attempt == max_attempts:
                        # Last attempt failed, re-raise the exception
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}",
                            exc_info=True,
                        )
                        raise

                    # Calculate backoff with jitter
                    backoff = min(
                        initial_backoff * (backoff_multiplier ** (attempt - 1)),
                        max_backoff,
                    )
                    # Add jitter
                    actual_backoff = backoff * (1 + random.uniform(-jitter, jitter))

                    logger.warning(
                        f"Attempt {attempt} failed for {func.__name__}, " f"retrying in {actual_backoff:.2f}s: {str(e)}"
                    )

                    # Wait before retrying
                    await asyncio.sleep(actual_backoff)

            # This should never be reached, but for type safety
            if last_exception:
                raise last_exception
            return None

        return cast(AsyncF, wrapper)

    return decorator


def map_exception(
    exception: Exception,
    target_error: Type[BaseError],
    message: Optional[str] = None,
) -> BaseError:
    """
    Map an exception to a domain-specific exception.

    This utility function helps convert external exceptions to domain
    exceptions in places where decorators cannot be used.

    Args:
        exception: The original exception
        target_error: The domain-specific exception class to use
        message: Optional message for the new exception

    Returns:
        A new domain-specific exception

    Example:
        try:
            result = api_client.fetch_data()
        except ApiError as e:
            raise map_exception(e, ExternalServiceError, "Failed to fetch data")
    """
    error_message = message or str(exception)
    return target_error(message=error_message, cause=exception)


# Domain-specific error examples (to be moved to their own modules)


class ConfigError(BaseError):
    """Error related to configuration issues."""


class DataProcessingError(BaseError):
    """Error related to data processing."""


class NetworkError(BaseError):
    """Error related to network operations."""


class DatabaseError(BaseError):
    """Error related to database operations."""


class ValidationError(BaseError):
    """Error related to validation failures."""


class AuthenticationError(BaseError):
    """Error related to authentication failures."""


class AuthorizationError(BaseError):
    """Error related to authorization failures."""


class ResourceNotFoundError(BaseError):
    """Error raised when a resource cannot be found."""


# Usage examples


def example_with_decorator() -> None:
    """Example of using the error handling decorator."""

    @handle_exception(target_error=ConfigError)
    def load_config(path: str) -> Dict[str, Any]:
        # This would normally read from a file
        if not path.endswith(".json"):
            raise ValueError("Config file must be JSON")
        return {"key": "value"}

    try:
        load_config("config.yaml")  # This will raise ConfigError
    except ConfigError as e:
        print(f"Caught error: {e}")


def example_with_context_manager() -> None:
    """Example of using the error context manager."""

    def process_item(item: Dict[str, Any]) -> None:
        if "id" not in item:
            raise KeyError("Item must have an ID")

    try:
        with error_context(DataProcessingError, "Error processing item", details={"item_id": 123}):
            process_item({})  # This will raise DataProcessingError
    except DataProcessingError as e:
        print(f"Caught error: {e}")


def example_with_safe_execute() -> None:
    """Example of using safe execution."""

    def parse_json(text: str) -> Dict[str, Any]:
        import json

        return json.loads(text)

    # This will return the default value ({}) instead of raising an exception
    result = safe_execute(parse_json, "{invalid: json}", default={})
    print(f"Result: {result}")


async def example_with_retry() -> None:
    """Example of using retry logic."""

    attempt_count = 0

    @with_retry(max_attempts=3, retryable_errors=(ConnectionError,))
    def fetch_data(url: str) -> Dict[str, Any]:
        nonlocal attempt_count
        attempt_count += 1

        if attempt_count < 3:
            raise ConnectionError("Connection failed")

        return {"data": "success"}

    try:
        result = fetch_data("https://example.com/api")
        print(f"Result after {attempt_count} attempts: {result}")
    except Exception as e:
        print(f"Failed after {attempt_count} attempts: {e}")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run the examples
    example_with_decorator()
    example_with_context_manager()
    example_with_safe_execute()

    # Run the async example using asyncio
    # import asyncio  # Removed redundant unused import

    asyncio.run(example_with_retry())
