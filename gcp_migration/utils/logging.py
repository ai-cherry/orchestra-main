"""
Configurable logging setup for the GCP Migration toolkit.

This module provides a centralized logging configuration that can be used
throughout the application for consistent log formatting, level control,
and output destinations.
"""

import logging
import sys
from functools import lru_cache
from pathlib import Path
from typing import Optional

from gcp_migration.config.settings import LogLevel, settings


@lru_cache(maxsize=1)
def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance for the specified name.
    
    Args:
        name: The name for the logger, typically __name__ of the calling module
        
    Returns:
        A configured Logger instance
    """
    # Configure logging if not already done
    setup_logging()
    
    # Get the logger for the specified name
    return logging.getLogger(name)


@lru_cache(maxsize=1)
def setup_logging() -> logging.Logger:
    """
    Configure the logging system based on application settings.
    
    Returns:
        The configured root logger
        
    This function sets up:
    - Log formatting based on settings
    - Console output
    - File output (if configured)
    - Log level based on settings
    """
    # Configure root logger
    root_logger = logging.getLogger()
    
    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set log level
    level = _get_log_level(settings.log_level)
    root_logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(settings.log_format)
    
    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(formatter)
    root_logger.addHandler(console)
    
    # File handler (if configured)
    if settings.log_file:
        _ensure_log_directory(settings.log_file)
        file_handler = logging.FileHandler(settings.log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Return the logger
    return root_logger


def _get_log_level(level: LogLevel) -> int:
    """
    Convert LogLevel enum to logging module level.
    
    Args:
        level: The LogLevel enum value
        
    Returns:
        The corresponding logging module level constant
    """
    level_map = {
        LogLevel.DEBUG: logging.DEBUG,
        LogLevel.INFO: logging.INFO,
        LogLevel.WARNING: logging.WARNING,
        LogLevel.ERROR: logging.ERROR,
        LogLevel.CRITICAL: logging.CRITICAL,
    }
    return level_map.get(level, logging.INFO)


def _ensure_log_directory(log_file: Path) -> None:
    """
    Ensure the directory for the log file exists.
    
    Args:
        log_file: Path to the log file
    """
    log_dir = log_file.parent
    log_dir.mkdir(parents=True, exist_ok=True)


# Create a module-level logger
logger = get_logger(__name__)


class SensitiveFilter(logging.Filter):
    """Filter to redact sensitive information from logs."""
    
    def __init__(self, sensitive_keys: Optional[list[str]] = None):
        """
        Initialize the filter.
        
        Args:
            sensitive_keys: List of keys to consider sensitive and redact in logs
        """
        super().__init__()
        self.sensitive_keys = sensitive_keys or settings.sensitive_env_vars
        
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log records by redacting sensitive information.
        
        Args:
            record: The log record to filter
            
        Returns:
            Always True (to include the record), but the record is modified
        """
        if isinstance(record.msg, str):
            record.msg = self._redact_sensitive_info(record.msg)
            
        # Also check args if they're a dict or a string
        if hasattr(record, 'args'):
            if isinstance(record.args, dict):
                for key, value in record.args.items():
                    if isinstance(value, str):
                        record.args[key] = self._redact_sensitive_info(value)
            elif isinstance(record.args, tuple):
                new_args = list(record.args)
                for i, arg in enumerate(new_args):
                    if isinstance(arg, str):
                        new_args[i] = self._redact_sensitive_info(arg)
                record.args = tuple(new_args)
                
        return True
    
    def _redact_sensitive_info(self, text: str) -> str:
        """
        Redact sensitive information from a string.
        
        Args:
            text: The text to redact
            
        Returns:
            The redacted text
        """
        if not isinstance(text, str):
            return text
            
        # For each sensitive key, look for "key=value" or "key: value" patterns
        for key in self.sensitive_keys:
            # Look for various formats: key=value, key: value, "key": "value"
            for pattern in (
                f"{key}=", 
                f"{key}:", 
                f'"{key}":', 
                f"'{key}':"
            ):
                start_idx = text.find(pattern)
                if start_idx != -1:
                    # Find the end of the value (space, comma, newline, etc.)
                    start_idx += len(pattern)
                    
                    # Handle quoted strings
                    if start_idx < len(text) and text[start_idx] in ('"', "'"):
                        quote_char = text[start_idx]
                        start_idx += 1
                        end_idx = text.find(quote_char, start_idx)
                        if end_idx == -1:  # If no closing quote, go to end of string
                            end_idx = len(text)
                    else:
                        # Otherwise, find the end of the value
                        end_idx = start_idx
                        while end_idx < len(text) and text[end_idx] not in (' ', ',', '\n', '}'):
                            end_idx += 1
                    
                    # Redact the value
                    value_length = end_idx - start_idx
                    redacted = "*" * min(8, value_length)  # Show at most 8 asterisks
                    
                    text = text[:start_idx] + redacted + text[end_idx:]
        
        return text


# Add the sensitive filter to the root logger
root_logger = logging.getLogger()
sensitive_filter = SensitiveFilter()
for handler in root_logger.handlers:
    handler.addFilter(sensitive_filter)