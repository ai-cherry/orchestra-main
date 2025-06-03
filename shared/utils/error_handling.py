"""Error handling utilities for the orchestrator."""
    """Decorator to handle errors in async functions."""
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            raise
    return wrapper


class OrchestrationError(Exception):
    """Base exception for orchestration errors."""
    """API-related errors."""
    """Configuration-related errors."""
    """Mode transition errors."""