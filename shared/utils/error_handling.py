"""Error handling utilities for the orchestrator."""

import functools
import logging
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


def handle_errors(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to handle errors in async functions."""
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            raise
    return wrapper


class OrchestrationError(Exception):
    """Base exception for orchestration errors."""
    pass


class APIError(OrchestrationError):
    """API-related errors."""
    pass


class ConfigurationError(OrchestrationError):
    """Configuration-related errors."""
    pass


class TransitionError(OrchestrationError):
    """Mode transition errors."""
    pass