#!/usr/bin/env python3
"""
structured_logging.py - Structured Logging with Correlation IDs

This module provides a structured logging system with correlation ID tracking
across asynchronous contexts. It outputs JSON-formatted logs with consistent
fields and supports context propagation through asyncio tasks.
"""

import asyncio
import functools
import inspect
import json
import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Callable, Dict, Optional, TypeVar, cast

# Context variable to store correlation ID
correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
session_id: ContextVar[Optional[str]] = ContextVar("session_id", default=None)
user_id: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
extra_context: ContextVar[Dict[str, Any]] = ContextVar("extra_context", default={})

# Type variables for function decorators
F = TypeVar("F", bound=Callable[..., Any])
AsyncF = TypeVar("AsyncF", bound=Callable[..., Any])


class StructuredLogFormatter(logging.Formatter):
    """Formatter that outputs JSON formatted logs with correlation IDs."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON with correlation ID and other context.

        Args:
            record: The log record to format

        Returns:
            JSON formatted log string
        """
        # Create the base log record
        timestamp = datetime.fromtimestamp(record.created).isoformat()
        log_record = {
            "timestamp": timestamp,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id.get() or "unknown",
            "request_id": request_id.get(),
            "session_id": session_id.get(),
            "user_id": user_id.get(),
            "location": f"{record.pathname}:{record.lineno}",
            "function": record.funcName,
        }

        # Add exception info if available
        if record.exc_info:
            exception_type, exception_value, _ = record.exc_info
            log_record["exception"] = {
                "type": exception_type.__name__ if exception_type else None,
                "message": str(exception_value) if exception_value else None,
                "traceback": self.formatException(record.exc_info),
            }

        # Add extra fields from record
        if hasattr(record, "extra"):
            for key, value in record.extra.items():
                if key not in log_record:
                    log_record[key] = value

        # Add any extra context
        context = extra_context.get()
        if context:
            for key, value in context.items():
                if key not in log_record:
                    log_record[key] = value

        # Remove None values for cleaner output
        log_record = {k: v for k, v in log_record.items() if v is not None}

        return json.dumps(log_record)


class StructuredLogger(logging.Logger):
    """Logger subclass that adds structured logging capabilities."""

    def _log_with_extra(
        self,
        level: int,
        msg: str,
        args: tuple,
        exc_info: Any = None,
        extra: Optional[Dict[str, Any]] = None,
        stack_info: bool = False,
        stacklevel: int = 1,
    ) -> None:
        """Log with extra context information.

        Args:
            level: The logging level
            msg: The log message
            args: Arguments for message formatting
            exc_info: Exception information
            extra: Extra fields to include in the log record
            stack_info: Whether to include stack information
            stacklevel: How many levels up the stack to identify the caller
        """
        # Merge extra with context
        merged_extra = {}
        context = extra_context.get()
        if context:
            merged_extra.update(context)
        if extra:
            merged_extra.update(extra)

        # Add extra as a special attribute that our formatter will look for
        if merged_extra:
            extra_obj = {"extra": merged_extra}
        else:
            extra_obj = None

        # Call the parent _log method
        super()._log(level, msg, args, exc_info, extra_obj, stack_info, stacklevel + 1)

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message with extra context."""
        self._log_with_extra(logging.DEBUG, msg, args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message with extra context."""
        self._log_with_extra(logging.INFO, msg, args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message with extra context."""
        self._log_with_extra(logging.WARNING, msg, args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message with extra context."""
        self._log_with_extra(logging.ERROR, msg, args, **kwargs)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message with extra context."""
        self._log_with_extra(logging.CRITICAL, msg, args, **kwargs)

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log an exception message with extra context."""
        kwargs["exc_info"] = kwargs.get("exc_info", True)
        self._log_with_extra(logging.ERROR, msg, args, **kwargs)


def configure_logging(
    level: int = logging.INFO, json_output: bool = True, log_file: Optional[str] = None
) -> None:
    """Configure structured logging.

    Args:
        level: The logging level
        json_output: Whether to output logs as JSON
        log_file: Optional file path to write logs to
    """
    # Register our custom logger class
    logging.setLoggerClass(StructuredLogger)

    # Create handlers
    handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    if json_output:
        console_handler.setFormatter(StructuredLogFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] [%(correlation_id)s] %(name)s: %(message)s"
            )
        )
    handlers.append(console_handler)

    # File handler if specified
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(StructuredLogFormatter())
            handlers.append(file_handler)
        except Exception as e:
            print(f"Error setting up log file: {e}")

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for h in root_logger.handlers:
        root_logger.removeHandler(h)

    # Add our handlers
    for handler in handlers:
        root_logger.addHandler(handler)

    # Log that logging is configured
    logger = cast(StructuredLogger, logging.getLogger(__name__))
    logger.info(
        "Structured logging configured",
        extra={
            "log_level": logging.getLevelName(level),
            "json_output": json_output,
            "log_file": log_file,
        },
    )


def get_correlation_id() -> str:
    """Get the current correlation ID or generate a new one.

    Returns:
        The current correlation ID
    """
    current_id = correlation_id.get()
    if current_id is None:
        current_id = str(uuid.uuid4())
        correlation_id.set(current_id)
    return current_id


def set_correlation_id(corr_id: str) -> None:
    """Set the correlation ID for the current context.

    Args:
        corr_id: The correlation ID to set
    """
    correlation_id.set(corr_id)


def with_correlation_id(func: F) -> F:
    """Decorator to ensure a correlation ID is set for the function call.

    This decorator works with both synchronous and asynchronous functions.

    Args:
        func: The function to decorate

    Returns:
        The decorated function
    """
    if asyncio.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get current context values
            current_corr_id = correlation_id.get()
            current_req_id = request_id.get()
            current_sess_id = session_id.get()
            current_usr_id = user_id.get()

            # Set new correlation ID if none exists
            if current_corr_id is None:
                current_corr_id = str(uuid.uuid4())
                correlation_id.set(current_corr_id)

            # Get logger for the calling module
            caller_module = inspect.getmodule(inspect.currentframe().f_back)
            logger = cast(
                StructuredLogger,
                logging.getLogger(
                    caller_module.__name__ if caller_module else __name__
                ),
            )

            try:
                logger.debug(
                    f"Starting async function {func.__name__}",
                    extra={"function": func.__name__},
                )
                return await func(*args, **kwargs)
            except Exception as e:
                logger.exception(
                    f"Exception in {func.__name__}: {str(e)}",
                    extra={"function": func.__name__, "error": str(e)},
                )
                raise
            finally:
                # Reset context if we set it
                if current_corr_id is None:
                    correlation_id.reset()
                if current_req_id is None:
                    request_id.reset()
                if current_sess_id is None:
                    session_id.reset()
                if current_usr_id is None:
                    user_id.reset()

        return cast(F, async_wrapper)
    else:

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get current context values
            current_corr_id = correlation_id.get()
            current_req_id = request_id.get()
            current_sess_id = session_id.get()
            current_usr_id = user_id.get()

            # Set new correlation ID if none exists
            if current_corr_id is None:
                current_corr_id = str(uuid.uuid4())
                correlation_id.set(current_corr_id)

            # Get logger for the calling module
            caller_module = inspect.getmodule(inspect.currentframe().f_back)
            logger = cast(
                StructuredLogger,
                logging.getLogger(
                    caller_module.__name__ if caller_module else __name__
                ),
            )

            try:
                logger.debug(
                    f"Starting function {func.__name__}",
                    extra={"function": func.__name__},
                )
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(
                    f"Exception in {func.__name__}: {str(e)}",
                    extra={"function": func.__name__, "error": str(e)},
                )
                raise
            finally:
                # Reset context if we set it
                if current_corr_id is None:
                    correlation_id.reset()
                if current_req_id is None:
                    request_id.reset()
                if current_sess_id is None:
                    session_id.reset()
                if current_usr_id is None:
                    user_id.reset()

        return cast(F, sync_wrapper)


def add_context(key: str, value: Any) -> None:
    """Add a key-value pair to the logging context.

    Args:
        key: The context key
        value: The context value
    """
    context = extra_context.get().copy()
    context[key] = value
    extra_context.set(context)


def remove_context(key: str) -> None:
    """Remove a key from the logging context.

    Args:
        key: The context key to remove
    """
    context = extra_context.get().copy()
    if key in context:
        del context[key]
        extra_context.set(context)


def clear_context() -> None:
    """Clear all keys from the logging context."""
    extra_context.set({})


class LogContext:
    """Context manager for temporarily adding context to logs."""

    def __init__(self, **kwargs: Any):
        """Initialize with context key-value pairs.

        Args:
            **kwargs: Key-value pairs to add to the context
        """
        self.kwargs = kwargs
        self.previous_context = {}

    def __enter__(self) -> "LogContext":
        """Add context when entering the context manager."""
        self.previous_context = extra_context.get().copy()
        new_context = self.previous_context.copy()
        new_context.update(self.kwargs)
        extra_context.set(new_context)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Restore previous context when exiting."""
        extra_context.set(self.previous_context)


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger with the given name.

    Args:
        name: The logger name

    Returns:
        A structured logger instance
    """
    return cast(StructuredLogger, logging.getLogger(name))
