"""
Standardized error handling utilities for GCP migrations.

This module provides decorators and utilities for consistent error handling,
retry logic, and error reporting across the GCP migration toolkit.
"""

import asyncio
import functools
import logging
import time
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union, cast

from gcp_migration.domain.exceptions import (
    AuthenticationError,
    ConfigurationError,
    FirestoreError,
    GCPError,
    MigrationError,
    ResourceNotFoundError,
    SecretError,
    StorageError,
    ValidationError,
    VertexAIError,
)

# Configure logging
logger = logging.getLogger(__name__)

# Type variables for function signatures
T = TypeVar("T")
E = TypeVar("E", bound=Exception)
F = TypeVar("F", bound=Callable[..., Any])
AsyncF = TypeVar("AsyncF", bound=Callable[..., Any])


def with_error_mapping(
    target_error: Type[MigrationError],
    source_errors: Union[Type[Exception], tuple[Type[Exception], ...]],
    error_message: Optional[str] = None,
) -> Callable[[F], F]:
    """
    Decorator that maps external exceptions to domain-specific exceptions.
    
    This decorator helps standardize error handling by converting external
    library exceptions into our domain-specific exception hierarchy.
    
    Args:
        target_error: The domain-specific exception to raise
        source_errors: The external exception(s) to catch
        error_message: Optional message to include in the raised exception
        
    Returns:
        A decorator function
        
    Example:
        @with_error_mapping(StorageError, (IOError, ValueError), "Failed to read file")
        def read_file(path: str) -> str:
            with open(path, "r") as f:
                return f.read()
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except source_errors as e:
                msg = error_message or f"Error in {func.__name__}: {str(e)}"
                logger.error(msg, exc_info=True)
                raise target_error(message=msg, cause=e)
            
        return cast(F, wrapper)
    return decorator


def with_async_error_mapping(
    target_error: Type[MigrationError],
    source_errors: Union[Type[Exception], tuple[Type[Exception], ...]],
    error_message: Optional[str] = None,
) -> Callable[[AsyncF], AsyncF]:
    """
    Async version of the error mapping decorator.
    
    Args:
        target_error: The domain-specific exception to raise
        source_errors: The external exception(s) to catch
        error_message: Optional message to include in the raised exception
        
    Returns:
        An async decorator function
        
    Example:
        @with_async_error_mapping(StorageError, (IOError, ValueError), "Failed to read file")
        async def read_file_async(path: str) -> str:
            async with aiofiles.open(path, "r") as f:
                return await f.read()
    """
    def decorator(func: AsyncF) -> AsyncF:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except source_errors as e:
                msg = error_message or f"Error in {func.__name__}: {str(e)}"
                logger.error(msg, exc_info=True)
                raise target_error(message=msg, cause=e)
            
        return cast(AsyncF, wrapper)
    return decorator


def with_retry(
    max_attempts: int = 3,
    initial_backoff: float = 1.0,
    max_backoff: float = 30.0,
    backoff_multiplier: float = 2.0,
    jitter: float = 0.1,
    retryable_errors: tuple[Type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """
    Decorator that adds retry logic with exponential backoff and jitter.
    
    This decorator automatically retries functions that fail with specified
    exceptions, using exponential backoff with jitter for better resilience.
    
    Args:
        max_attempts: Maximum number of retry attempts
        initial_backoff: Initial backoff time in seconds
        max_backoff: Maximum backoff time in seconds
        backoff_multiplier: Multiplier for exponential backoff
        jitter: Random jitter factor to add to backoff
        retryable_errors: Tuple of exception types that should trigger retry
        
    Returns:
        A decorator function
        
    Example:
        @with_retry(max_attempts=5, retryable_errors=(ConnectionError, TimeoutError))
        def fetch_data(url: str) -> dict:
            return requests.get(url).json()
    """
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
                            exc_info=True
                        )
                        raise
                    
                    # Calculate backoff with jitter
                    backoff = min(
                        initial_backoff * (backoff_multiplier ** (attempt - 1)),
                        max_backoff
                    )
                    # Add jitter
                    import random
                    actual_backoff = backoff * (1 + random.uniform(-jitter, jitter))
                    
                    logger.warning(
                        f"Attempt {attempt} failed for {func.__name__}, "
                        f"retrying in {actual_backoff:.2f}s: {str(e)}"
                    )
                    
                    # Wait before retrying
                    time.sleep(actual_backoff)
            
            # This should never be reached, but for type safety
            if last_exception:
                raise last_exception
            return None
            
        return cast(F, wrapper)
    return decorator


def with_async_retry(
    max_attempts: int = 3,
    initial_backoff: float = 1.0,
    max_backoff: float = 30.0,
    backoff_multiplier: float = 2.0,
    jitter: float = 0.1,
    retryable_errors: tuple[Type[Exception], ...] = (Exception,),
) -> Callable[[AsyncF], AsyncF]:
    """
    Async version of the retry decorator.
    
    Args:
        max_attempts: Maximum number of retry attempts
        initial_backoff: Initial backoff time in seconds
        max_backoff: Maximum backoff time in seconds
        backoff_multiplier: Multiplier for exponential backoff
        jitter: Random jitter factor to add to backoff
        retryable_errors: Tuple of exception types that should trigger retry
        
    Returns:
        An async decorator function
        
    Example:
        @with_async_retry(max_attempts=5, retryable_errors=(aiohttp.ClientError,))
        async def fetch_data_async(url: str) -> dict:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.json()
    """
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
                            exc_info=True
                        )
                        raise
                    
                    # Calculate backoff with jitter
                    backoff = min(
                        initial_backoff * (backoff_multiplier ** (attempt - 1)),
                        max_backoff
                    )
                    # Add jitter
                    import random
                    actual_backoff = backoff * (1 + random.uniform(-jitter, jitter))
                    
                    logger.warning(
                        f"Attempt {attempt} failed for {func.__name__}, "
                        f"retrying in {actual_backoff:.2f}s: {str(e)}"
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
    target_error: Type[MigrationError],
    message: Optional[str] = None,
) -> MigrationError:
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


# Common error mapping functions
def map_google_api_error(exception: Exception, message: Optional[str] = None) -> GCPError:
    """Map a Google API exception to a GCPError."""
    return map_exception(exception, GCPError, message)


def map_secret_error(exception: Exception, message: Optional[str] = None) -> SecretError:
    """Map an exception to a SecretError."""
    return map_exception(exception, SecretError, message)


def map_storage_error(exception: Exception, message: Optional[str] = None) -> StorageError:
    """Map an exception to a StorageError."""
    return map_exception(exception, StorageError, message)


def map_firestore_error(exception: Exception, message: Optional[str] = None) -> FirestoreError:
    """Map an exception to a FirestoreError."""
    return map_exception(exception, FirestoreError, message)


def map_authentication_error(exception: Exception, message: Optional[str] = None) -> AuthenticationError:
    """Map an exception to an AuthenticationError."""
    return map_exception(exception, AuthenticationError, message)