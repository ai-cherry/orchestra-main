"""Error handling utilities for the conductor."""
    """Decorator to handle errors in async functions."""
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            raise
    return wrapper


class coordinationError(Exception):
    """Base exception for coordination errors."""
    """API-related errors."""
    """Configuration-related errors."""
    """Mode transition errors."""