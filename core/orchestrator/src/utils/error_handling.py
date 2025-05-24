"""
Error handling utilities for AI Orchestration System.

This module provides standardized error handling patterns and utilities
for logging, error propagation, and graceful degradation.
"""

import asyncio
import functools
import logging
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union, cast

from core.orchestrator.src.exceptions import (
    LLMProviderError,
    MemoryConnectionError,
    OrchestratorError,
)

# Type variables for generic function signatures
T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])

# Configure logging
logger = logging.getLogger(__name__)


def log_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    level: int = logging.ERROR,
    include_traceback: bool = True,
    log_to_monitoring: bool = False,
) -> None:
    """
    Log an error with consistent formatting and context.

    Args:
        error: The exception to log
        context: Additional context information
        level: Logging level
        include_traceback: Whether to include the traceback
        log_to_monitoring: Whether to also log to monitoring system
    """
    # Format error message
    error_type = type(error).__name__
    error_message = str(error)

    # Add original error information for OrchestratorError
    if isinstance(error, OrchestratorError) and error.original_error:
        error_message += f" (Original error: {type(error.original_error).__name__}: {str(error.original_error)})"

    # Build log message
    message = f"{error_type}: {error_message}"

    # Add context if provided
    context_str = ""
    if context:
        context_str = " | Context: " + ", ".join(f"{k}={v}" for k, v in context.items())
        message += context_str

    # Log the error
    if include_traceback:
        logger.log(level, message, exc_info=True)
    else:
        logger.log(level, message)

    # Log to monitoring system if enabled
    if log_to_monitoring:
        try:
            from core.orchestrator.src.resilience.monitoring import (
                get_monitoring_client,
            )

            monitoring_client = get_monitoring_client()

            monitoring_data = {
                "error_type": error_type,
                "error_message": error_message,
                "timestamp": datetime.now().isoformat(),
            }

            if context:
                monitoring_data.update(context)

            monitoring_client.report_error(monitoring_data)
        except Exception as monitoring_error:
            logger.warning(f"Failed to log error to monitoring: {monitoring_error}")


def handle_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    fallback_value: Optional[Any] = None,
    propagate_types: Optional[list] = None,
    always_log: bool = True,
    log_level: int = logging.ERROR,
    include_traceback: bool = True,
    log_to_monitoring: bool = False,
) -> Union[Any, Exception]:
    """
    Handle an error according to standardized patterns.

    Args:
        error: The exception to handle
        context: Additional context information
        fallback_value: Value to return if error is not propagated
        propagate_types: List of exception types that should be propagated
        always_log: Whether to always log the error
        log_level: Logging level to use
        include_traceback: Whether to include the traceback in logs
        log_to_monitoring: Whether to log to monitoring system

    Returns:
        Either the fallback value or raises the error

    Raises:
        Exception: If the error type is in propagate_types
    """
    # Default propagation types if not specified
    if propagate_types is None:
        # By default, propagate OrchestratorError and its subclasses
        propagate_types = [OrchestratorError]

    # Determine if we should propagate this error
    should_propagate = any(isinstance(error, error_type) for error_type in propagate_types)

    # Always log if requested or if we're going to propagate
    if always_log or should_propagate:
        log_error(
            error=error,
            context=context,
            level=log_level,
            include_traceback=include_traceback,
            log_to_monitoring=log_to_monitoring,
        )

    # Propagate the error if it's one of the specified types
    if should_propagate:
        raise error

    # Otherwise return the fallback value
    return fallback_value


def error_boundary(
    fallback_value: Optional[Any] = None,
    propagate_types: Optional[list] = None,
    context_provider: Optional[Callable[..., Dict[str, Any]]] = None,
    always_log: bool = True,
    log_level: int = logging.ERROR,
    include_traceback: bool = True,
    log_to_monitoring: bool = False,
) -> Callable[[F], F]:
    """
    Decorator that creates an error boundary around a function.

    This decorator wraps a function with standardized error handling,
    providing graceful degradation and consistent error handling.

    Args:
        fallback_value: Value to return if an error occurs
        propagate_types: List of exception types that should be propagated
        context_provider: Function that provides context information from the args/kwargs
        always_log: Whether to always log errors
        log_level: Logging level to use
        include_traceback: Whether to include the traceback in logs
        log_to_monitoring: Whether to log to monitoring system

    Returns:
        Decorated function with error handling
    """

    def decorator(func: F) -> F:
        # Determine if the function is async
        is_async = asyncio.iscoroutinefunction(func)

        if is_async:

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    # Get context if a provider is specified
                    context = None
                    if context_provider:
                        try:
                            context = context_provider(*args, **kwargs)
                        except Exception as context_error:
                            logger.warning(f"Error in context provider: {context_error}")

                    # Add function name to context
                    if context is None:
                        context = {}
                    context["function"] = func.__name__

                    # Handle the error
                    return handle_error(
                        error=e,
                        context=context,
                        fallback_value=fallback_value,
                        propagate_types=propagate_types,
                        always_log=always_log,
                        log_level=log_level,
                        include_traceback=include_traceback,
                        log_to_monitoring=log_to_monitoring,
                    )

            return cast(F, async_wrapper)
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Get context if a provider is specified
                    context = None
                    if context_provider:
                        try:
                            context = context_provider(*args, **kwargs)
                        except Exception as context_error:
                            logger.warning(f"Error in context provider: {context_error}")

                    # Add function name to context
                    if context is None:
                        context = {}
                    context["function"] = func.__name__

                    # Handle the error
                    return handle_error(
                        error=e,
                        context=context,
                        fallback_value=fallback_value,
                        propagate_types=propagate_types,
                        always_log=always_log,
                        log_level=log_level,
                        include_traceback=include_traceback,
                        log_to_monitoring=log_to_monitoring,
                    )

            return cast(F, sync_wrapper)

    return decorator


def retry(
    max_attempts: int = 3,
    delay_seconds: float = 1.0,
    backoff_factor: float = 2.0,
    retry_exceptions: Optional[list] = None,
    context_provider: Optional[Callable[..., Dict[str, Any]]] = None,
) -> Callable[[F], F]:
    """
    Decorator that implements retry logic with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts
        delay_seconds: Initial delay between retries in seconds
        backoff_factor: Factor to increase delay with each retry
        retry_exceptions: List of exception types to retry on
        context_provider: Function that provides context information from the args/kwargs

    Returns:
        Decorated function with retry logic
    """
    # Default retry exceptions if not specified
    if retry_exceptions is None:
        # By default, retry on connection and temporary errors
        retry_exceptions = [
            MemoryConnectionError,
            LLMProviderError,
            ConnectionError,
            TimeoutError,
        ]

    def decorator(func: F) -> F:
        # Determine if the function is async
        is_async = asyncio.iscoroutinefunction(func)

        if is_async:

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                last_exception = None
                current_delay = delay_seconds

                # Get context if a provider is specified
                context = None
                if context_provider:
                    try:
                        context = context_provider(*args, **kwargs)
                    except Exception as context_error:
                        logger.warning(f"Error in context provider: {context_error}")

                # Add function name to context
                if context is None:
                    context = {}
                context["function"] = func.__name__

                for attempt in range(1, max_attempts + 1):
                    context["attempt"] = attempt

                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e

                        # Check if this exception should be retried
                        should_retry = any(isinstance(e, exc_type) for exc_type in retry_exceptions)

                        if not should_retry or attempt >= max_attempts:
                            # Don't retry - either wrong exception type or too many attempts
                            break

                        # Log the retry
                        logger.info(
                            f"Retrying {func.__name__} after error {type(e).__name__}: {str(e)}, "
                            f"attempt {attempt}/{max_attempts}, delay {current_delay}s"
                        )

                        # Wait before retrying
                        await asyncio.sleep(current_delay)

                        # Increase delay for next attempt
                        current_delay *= backoff_factor

                # If we get here, all retries failed
                if last_exception:
                    context["max_attempts"] = max_attempts
                    log_error(last_exception, context)
                    raise last_exception

                # This should never happen, but just in case
                raise RuntimeError("Retry logic failed, but no exception was raised")

            return cast(F, async_wrapper)
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                last_exception = None
                current_delay = delay_seconds

                # Get context if a provider is specified
                context = None
                if context_provider:
                    try:
                        context = context_provider(*args, **kwargs)
                    except Exception as context_error:
                        logger.warning(f"Error in context provider: {context_error}")

                # Add function name to context
                if context is None:
                    context = {}
                context["function"] = func.__name__

                for attempt in range(1, max_attempts + 1):
                    context["attempt"] = attempt

                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e

                        # Check if this exception should be retried
                        should_retry = any(isinstance(e, exc_type) for exc_type in retry_exceptions)

                        if not should_retry or attempt >= max_attempts:
                            # Don't retry - either wrong exception type or too many attempts
                            break

                        # Log the retry
                        logger.info(
                            f"Retrying {func.__name__} after error {type(e).__name__}: {str(e)}, "
                            f"attempt {attempt}/{max_attempts}, delay {current_delay}s"
                        )

                        # Wait before retrying
                        import time

                        time.sleep(current_delay)

                        # Increase delay for next attempt
                        current_delay *= backoff_factor

                # If we get here, all retries failed
                if last_exception:
                    context["max_attempts"] = max_attempts
                    log_error(last_exception, context)
                    raise last_exception

                # This should never happen, but just in case
                raise RuntimeError("Retry logic failed, but no exception was raised")

            return cast(F, sync_wrapper)

    return decorator


def convert_exceptions(
    mapping: Dict[Type[Exception], Type[Exception]],
    context_provider: Optional[Callable[..., Dict[str, Any]]] = None,
) -> Callable[[F], F]:
    """
    Decorator that converts exceptions from one type to another.

    This is useful for wrapping lower-level exceptions with domain-specific ones.

    Args:
        mapping: Dictionary mapping from source exception types to target exception types
        context_provider: Function that provides context information from the args/kwargs

    Returns:
        Decorated function that converts exceptions
    """

    def decorator(func: F) -> F:
        # Determine if the function is async
        is_async = asyncio.iscoroutinefunction(func)

        if is_async:

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    # Check if this exception should be converted
                    for source_type, target_type in mapping.items():
                        if isinstance(e, source_type):
                            # Get context if a provider is specified
                            context = None
                            if context_provider:
                                try:
                                    context = context_provider(*args, **kwargs)
                                except Exception as context_error:
                                    logger.warning(f"Error in context provider: {context_error}")

                            # Add function name to context
                            if context is None:
                                context = {}
                            context["function"] = func.__name__

                            # Create a new message incorporating the original exception
                            message = f"{str(e)} (in {func.__name__})"

                            # Create and raise the new exception
                            if issubclass(target_type, OrchestratorError):
                                new_exception = target_type(message, original_error=e)
                            else:
                                new_exception = target_type(message)

                            # Add the original traceback
                            new_exception.__traceback__ = e.__traceback__

                            raise new_exception

                    # If no conversion matches, re-raise the original exception
                    raise

            return cast(F, async_wrapper)
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Check if this exception should be converted
                    for source_type, target_type in mapping.items():
                        if isinstance(e, source_type):
                            # Get context if a provider is specified
                            context = None
                            if context_provider:
                                try:
                                    context = context_provider(*args, **kwargs)
                                except Exception as context_error:
                                    logger.warning(f"Error in context provider: {context_error}")

                            # Add function name to context
                            if context is None:
                                context = {}
                            context["function"] = func.__name__

                            # Create a new message incorporating the original exception
                            message = f"{str(e)} (in {func.__name__})"

                            # Create and raise the new exception
                            if issubclass(target_type, OrchestratorError):
                                new_exception = target_type(message, original_error=e)
                            else:
                                new_exception = target_type(message)

                            # Add the original traceback
                            new_exception.__traceback__ = e.__traceback__

                            raise new_exception

                    # If no conversion matches, re-raise the original exception
                    raise

            return cast(F, sync_wrapper)

    return decorator
