"""
Logging utilities for AI Orchestra.

This module provides structured logging utilities.
"""

import logging
import json
import sys
import time
from typing import Any, Dict, Optional, Union
from datetime import datetime


def configure_logging(
    level: Union[int, str] = logging.INFO,
    log_format: Optional[str] = None,
    json_logs: bool = False,
) -> None:
    """
    Configure logging for the application.
    
    Args:
        level: Logging level
        log_format: Log format string
        json_logs: Whether to output logs in JSON format
    """
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    
    if not log_format:
        if json_logs:
            log_format = "%(message)s"
        else:
            log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    if json_logs:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(log_format))
    
    root_logger.addHandler(handler)


class JsonFormatter(logging.Formatter):
    """JSON log formatter."""
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as JSON.
        
        Args:
            record: The log record
            
        Returns:
            JSON formatted log
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        
        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        if hasattr(record, "props"):
            log_data.update(record.props)
        
        return json.dumps(log_data)


def log_event(
    logger: logging.Logger,
    event: str,
    status: str,
    details: Optional[Dict[str, Any]] = None,
    level: int = logging.INFO,
) -> None:
    """
    Log a structured event.
    
    Args:
        logger: The logger to use
        event: The event name
        status: The event status
        details: Optional event details
        level: Logging level
    """
    message = f"{event}:{status}"
    
    # Add details to the log record
    extra = {}
    if details:
        # For JSON formatter
        extra["props"] = details
        
        # For string formatter, append details to message
        details_str = json.dumps(details)
        message += f":{details_str}"
    
    logger.log(level, message, extra=extra)


def log_start(
    logger: logging.Logger,
    operation: str,
    details: Optional[Dict[str, Any]] = None,
) -> float:
    """
    Log the start of an operation and return the start time.
    
    Args:
        logger: The logger to use
        operation: The operation name
        details: Optional operation details
        
    Returns:
        Start time in seconds
    """
    start_time = time.time()
    log_event(logger, operation, "start", details)
    return start_time


def log_end(
    logger: logging.Logger,
    operation: str,
    start_time: float,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log the end of an operation with duration.
    
    Args:
        logger: The logger to use
        operation: The operation name
        start_time: Start time in seconds
        details: Optional operation details
    """
    duration = time.time() - start_time
    
    if details is None:
        details = {}
    
    details["duration_ms"] = int(duration * 1000)
    log_event(logger, operation, "complete", details)


def log_error(
    logger: logging.Logger,
    operation: str,
    error: Exception,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log an error.
    
    Args:
        logger: The logger to use
        operation: The operation name
        error: The error
        details: Optional error details
    """
    if details is None:
        details = {}
    
    details["error_type"] = type(error).__name__
    details["error_message"] = str(error)
    
    log_event(logger, operation, "error", details, level=logging.ERROR)
    logger.exception(f"{operation}:exception", exc_info=error)