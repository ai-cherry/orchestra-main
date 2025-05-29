"""
Error handling middleware for Orchestra AI API.

This module provides centralized error handling for all API endpoints.
"""

import logging
import traceback
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.api.models.responses import ErrorResponse

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling exceptions across all endpoints."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle any exceptions."""
        try:
            response = await call_next(request)
            return response

        except ValueError as e:
            # Handle validation errors
            logger.warning(f"Validation error: {str(e)}")
            error_response = ErrorResponse(
                error="ValidationError",
                message=str(e),
                details={"path": str(request.url.path)},
            )
            return JSONResponse(status_code=400, content=error_response.dict())

        except PermissionError as e:
            # Handle permission errors
            logger.warning(f"Permission error: {str(e)}")
            error_response = ErrorResponse(
                error="PermissionError",
                message="You don't have permission to perform this action",
                details={"path": str(request.url.path)},
            )
            return JSONResponse(status_code=403, content=error_response.dict())

        except FileNotFoundError as e:
            # Handle not found errors
            logger.warning(f"Not found error: {str(e)}")
            error_response = ErrorResponse(
                error="NotFoundError",
                message=str(e),
                details={"path": str(request.url.path)},
            )
            return JSONResponse(status_code=404, content=error_response.dict())

        except TimeoutError as e:
            # Handle timeout errors
            logger.error(f"Timeout error: {str(e)}")
            error_response = ErrorResponse(
                error="TimeoutError",
                message="Request timed out",
                details={"path": str(request.url.path)},
            )
            return JSONResponse(status_code=504, content=error_response.dict())

        except Exception as e:
            # Handle all other exceptions
            logger.error(f"Unhandled exception: {str(e)}", exc_info=True)

            # In production, don't expose internal errors
            error_response = ErrorResponse(
                error="InternalServerError",
                message="An internal error occurred",
                details={
                    "path": str(request.url.path),
                    "traceback": (traceback.format_exc() if logger.level <= logging.DEBUG else None),
                },
            )
            return JSONResponse(status_code=500, content=error_response.dict())


def handle_api_error(error: Exception, status_code: int = 500) -> JSONResponse:
    """
    Utility function to handle API errors consistently.

    Args:
        error: The exception that occurred
        status_code: HTTP status code to return

    Returns:
        JSONResponse with error details
    """
    error_type = type(error).__name__

    error_response = ErrorResponse(
        error=error_type,
        message=str(error),
        details={
            "type": error_type,
            "traceback": (traceback.format_exc() if logger.level <= logging.DEBUG else None),
        },
    )

    return JSONResponse(status_code=status_code, content=error_response.dict())
