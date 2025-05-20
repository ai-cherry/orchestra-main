"""
Error handling for AI Orchestra.

This module provides a consistent error handling framework.
"""

from typing import Dict, Optional, Any
import logging
import json
import traceback


class AIServiceError(Exception):
    """Base class for AI service errors."""

    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize the error.

        Args:
            code: Error code
            message: Error message
            details: Additional error details
            cause: The underlying exception that caused this error
        """
        self.code = code
        self.message = message
        self.details = details or {}
        self.cause = cause
        super().__init__(f"{code}: {message}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the error to a dictionary.

        Returns:
            Dictionary representation of the error
        """
        result = {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }

        if self.cause:
            result["cause"] = str(self.cause)

        return result

    def to_json(self) -> str:
        """
        Convert the error to JSON.

        Returns:
            JSON representation of the error
        """
        return json.dumps(self.to_dict())


class ModelNotFoundError(AIServiceError):
    """Raised when a requested AI model is not found."""

    def __init__(
        self,
        model_id: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize the error.

        Args:
            model_id: The ID of the model that was not found
            details: Additional error details
            cause: The underlying exception that caused this error
        """
        super().__init__(
            code="MODEL_NOT_FOUND",
            message=f"Model '{model_id}' not found",
            details=details,
            cause=cause,
        )
        self.model_id = model_id


class ModelUnavailableError(AIServiceError):
    """Raised when an AI model is temporarily unavailable."""

    def __init__(
        self,
        model_id: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize the error.

        Args:
            model_id: The ID of the model that is unavailable
            details: Additional error details
            cause: The underlying exception that caused this error
        """
        super().__init__(
            code="MODEL_UNAVAILABLE",
            message=f"Model '{model_id}' is temporarily unavailable",
            details=details,
            cause=cause,
        )
        self.model_id = model_id


class InvalidInputError(AIServiceError):
    """Raised when input to an AI model is invalid."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            details: Additional error details
            cause: The underlying exception that caused this error
        """
        super().__init__(
            code="INVALID_INPUT",
            message=message,
            details=details,
            cause=cause,
        )


class AuthenticationError(AIServiceError):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            details: Additional error details
            cause: The underlying exception that caused this error
        """
        super().__init__(
            code="AUTHENTICATION_ERROR",
            message=message,
            details=details,
            cause=cause,
        )


class MemoryError(AIServiceError):
    """Raised when there is an error with memory operations."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize the error.

        Args:
            message: Error message
            details: Additional error details
            cause: The underlying exception that caused this error
        """
        super().__init__(
            code="MEMORY_ERROR",
            message=message,
            details=details,
            cause=cause,
        )


def handle_exception(func):
    """
    Decorator to handle exceptions in a consistent way.

    Args:
        func: The function to decorate

    Returns:
        The decorated function
    """

    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except AIServiceError as e:
            # Log the error
            logging.error(f"AIServiceError: {e.code}:{e.message}")
            if e.details:
                logging.error(f"Details: {json.dumps(e.details)}")
            if e.cause:
                logging.error(f"Cause: {str(e.cause)}")

            # Re-raise the error
            raise
        except Exception as e:
            # Log the unexpected error
            logging.error(f"Unexpected error: {str(e)}")
            logging.error(traceback.format_exc())

            # Wrap the error in an AIServiceError
            raise AIServiceError(
                code="UNEXPECTED_ERROR",
                message="An unexpected error occurred",
                details={"original_error": str(e)},
                cause=e,
            )

    return wrapper
