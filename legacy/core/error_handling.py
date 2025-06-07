"""
Centralized Error Handling
Provides consistent error handling across the application
"""

import logging
from typing import Any, Dict, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import traceback

logger = logging.getLogger(__name__)

class ApplicationError(Exception):
    """Base application error"""
    def __init__(self, message: str, code: str, status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)

class ValidationError(ApplicationError):
    """Validation error"""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, "VALIDATION_ERROR", 400)
        self.field = field

class AuthenticationError(ApplicationError):
    """Authentication error"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR", 401)

class AuthorizationError(ApplicationError):
    """Authorization error"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, "AUTHORIZATION_ERROR", 403)

class NotFoundError(ApplicationError):
    """Resource not found error"""
    def __init__(self, resource: str, id: Any):
        super().__init__(f"{resource} with id {id} not found", "NOT_FOUND", 404)

class ConflictError(ApplicationError):
    """Resource conflict error"""
    def __init__(self, message: str):
        super().__init__(message, "CONFLICT", 409)

class ExternalServiceError(ApplicationError):
    """External service error"""
    def __init__(self, service: str, message: str):
        super().__init__(f"{service} error: {message}", "EXTERNAL_SERVICE_ERROR", 503)

async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
    """Handle application errors"""
    error_response = {
        "error": {
            "code": exc.code,
            "message": exc.message,
            "status_code": exc.status_code
        }
    }
    
    if hasattr(exc, 'field') and exc.field:
        error_response["error"]["field"] = exc.field
    
    logger.warning(f"Application error: {exc.code} - {exc.message}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )

async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors"""
    error_id = hash(str(exc) + str(request.url))
    
    logger.error(f"Unexpected error {error_id}: {str(exc)}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "error_id": str(error_id)
            }
        }
    )

def setup_error_handlers(app):
    """Setup error handlers for FastAPI app"""
    app.add_exception_handler(ApplicationError, application_error_handler)
    app.add_exception_handler(HTTPException, application_error_handler)
    app.add_exception_handler(Exception, generic_error_handler)
