"""
Error handling utilities for Orchestra.

This module provides standardized error handling components to ensure consistent
error management across all Orchestra services, including:

1. GCP client error handling decorators
2. Resource management context managers
3. Standardized error logging
4. Circuit breaker pattern implementation
5. Custom exception hierarchy
"""

import asyncio
import functools
import logging
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, cast

# Type variables
T = TypeVar('T')
AsyncFunc = TypeVar('AsyncFunc', bound=Callable[..., Any])

# Setup module logger
logger = logging.getLogger(__name__)


#########################################
# Custom Exception Hierarchy
#########################################

class OrchestraError(Exception):
    """Base exception for all Orchestra errors."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error
        self.error_id = str(uuid.uuid4())[:8]  # Short UUID for tracking


class ConfigurationError(OrchestraError):
    """Error in system configuration."""
    pass


class ConnectionError(OrchestraError):
    """Error establishing connection to a service."""
    pass


class ServiceError(OrchestraError):
    """Error from an external service."""
    pass


class StorageError(OrchestraError):
    """Error accessing or manipulating stored data."""
    pass


class ValidationError(OrchestraError):
    """Error validating data."""
    pass


class ResourceError(OrchestraError):
    """Error managing a resource."""
    pass


class TimeoutError(OrchestraError):
    """Operation timed out."""
    pass


class RateLimitError(OrchestraError):
    """Rate limit exceeded."""
    pass


class AuthenticationError(OrchestraError):
    """Authentication failed."""
    pass


class AuthorizationError(OrchestraError):
    """Authorization failed (not permitted)."""
    pass


class NotFoundError(OrchestraError):
    """Resource not found."""
    pass


class PreconditionError(OrchestraError):
    """Precondition for operation not met."""
    pass


class TemporaryError(OrchestraError):
    """Temporary error, operation may succeed if retried."""
    pass


class UnexpectedError(OrchestraError):
    """Unexpected error not covered by other categories."""
    pass


#########################################
# Standardized Error Logging
#########################################

class ErrorLogger:
    """Standardized error logging with consistent formatting."""
    
    def __init__(self, logger_name: str):
        """
        Initialize the error logger.
        
        Args:
            logger_name: Name for the logger, typically __name__
        """
        self.logger = logging.getLogger(logger_name)
        
    def log_error(
        self, 
        operation: str, 
        error: Exception, 
        level: str = "error", 
        include_traceback: bool = False,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log an error with standardized formatting.
        
        Args:
            operation: The operation that failed
            error: The exception that occurred
            level: Logging level (debug, info, warning, error, critical)
            include_traceback: Whether to include a stack trace
            context: Additional contextual information to include in the log
            
        Returns:
            Error ID for correlation in responses
        """
        error_id = str(uuid.uuid4())[:8]  # Generate short error ID for correlation
        
        # Build structured log data
        log_data = {
            "error_id": error_id,
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error)
        }
        
        # Add any additional context
        if context:
            log_data["context"] = context
            
        # Standard error message format
        message = f"[{error_id}] Error in {operation}: {error}"
        
        # Get the logging method based on level
        log_method = getattr(self.logger, level.lower(), self.logger.error)
        
        # Log with or without traceback
        if include_traceback:
            log_method(message, exc_info=True, extra={"structured": log_data})
        else:
            log_method(message, extra={"structured": log_data})
            
        return error_id


#########################################
# GCP Error Handler
#########################################

def handle_gcp_error(func: AsyncFunc) -> AsyncFunc:
    """
    Decorator for handling GCP client errors with appropriate responses.
    
    This decorator catches Google Cloud API exceptions and maps them to
    Orchestra's exception hierarchy. It also logs errors with consistent
    formatting.
    
    Example:
        @handle_gcp_error
        async def get_firestore_document(doc_id):
            # GCP calls here
    """
    error_logger = ErrorLogger(__name__)
    
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            # Try importing Google API exceptions
            # If imports fail, we'll use generic exception handling
            try:
                from google.api_core.exceptions import (
                    NotFound, 
                    FailedPrecondition,
                    ResourceExhausted,
                    Unavailable,
                    DeadlineExceeded,
                    GoogleAPIError,
                    Unauthenticated,
                    PermissionDenied
                )
                gcp_exceptions_available = True
            except ImportError:
                gcp_exceptions_available = False
                
            # Execute the function
            return await func(*args, **kwargs)
            
        except Exception as e:
            # Use the GCP exception types if available, otherwise rely on string matching
            if gcp_exceptions_available:
                # Handle each specific GCP exception type
                
                # These imports are inside the except block because they were previously imported
                # in the try block and will be available here if the import succeeded
                from google.api_core.exceptions import (
                    NotFound, 
                    FailedPrecondition,
                    ResourceExhausted,
                    Unavailable,
                    DeadlineExceeded,
                    GoogleAPIError,
                    Unauthenticated,
                    PermissionDenied
                )
                
                if isinstance(e, NotFound):
                    # Handle resource not found (404)
                    error_id = error_logger.log_error(
                        func.__name__, e, level="warning",
                        context={"status_code": 404}
                    )
                    raise NotFoundError(f"GCP resource not found: {e}", e) from e
                    
                elif isinstance(e, FailedPrecondition):
                    # Handle precondition failures (400 with specific reason)
                    error_id = error_logger.log_error(
                        func.__name__, e, level="error",
                        context={"status_code": 400}
                    )
                    raise PreconditionError(f"Operation precondition failed: {e}", e) from e
                    
                elif isinstance(e, ResourceExhausted):
                    # Handle rate limits (429)
                    error_id = error_logger.log_error(
                        func.__name__, e, level="warning",
                        context={"status_code": 429}
                    )
                    raise RateLimitError(f"Rate limit exceeded: {e}", e) from e
                    
                elif isinstance(e, Unavailable):
                    # Handle service unavailable (503)
                    error_id = error_logger.log_error(
                        func.__name__, e, level="warning",
                        context={"status_code": 503}
                    )
                    raise TemporaryError(f"Service temporarily unavailable: {e}", e) from e
                    
                elif isinstance(e, DeadlineExceeded):
                    # Handle timeout (504)
                    error_id = error_logger.log_error(
                        func.__name__, e, level="warning",
                        context={"status_code": 504}
                    )
                    raise TimeoutError(f"Operation timed out: {e}", e) from e
                    
                elif isinstance(e, Unauthenticated):
                    # Handle authentication failures (401)
                    error_id = error_logger.log_error(
                        func.__name__, e, level="error",
                        context={"status_code": 401}
                    )
                    raise AuthenticationError(f"Authentication failed: {e}", e) from e
                    
                elif isinstance(e, PermissionDenied):
                    # Handle permission issues (403)
                    error_id = error_logger.log_error(
                        func.__name__, e, level="error",
                        context={"status_code": 403}
                    )
                    raise AuthorizationError(f"Authorization failed: {e}", e) from e
                    
                elif isinstance(e, GoogleAPIError):
                    # Handle other API errors
                    error_id = error_logger.log_error(
                        func.__name__, e, level="error",
                        include_traceback=True,
                        context={"google_api_error": True}
                    )
                    raise ServiceError(f"GCP service error: {e}", e) from e
                    
                else:
                    # Handle unexpected errors
                    error_id = error_logger.log_error(
                        func.__name__, e, level="error",
                        include_traceback=True
                    )
                    raise UnexpectedError(f"Unexpected error: {e}", e) from e
            else:
                # Fallback to string matching for environments without GCP libraries
                error_str = str(e).lower()
                
                if "not found" in error_str or "404" in error_str:
                    error_id = error_logger.log_error(func.__name__, e, level="warning")
                    raise NotFoundError(f"Resource not found: {e}", e) from e
                    
                elif "permission denied" in error_str or "forbidden" in error_str or "403" in error_str:
                    error_id = error_logger.log_error(func.__name__, e, level="error")
                    raise AuthorizationError(f"Authorization failed: {e}", e) from e
                    
                elif "unauthenticated" in error_str or "401" in error_str:
                    error_id = error_logger.log_error(func.__name__, e, level="error")
                    raise AuthenticationError(f"Authentication failed: {e}", e) from e
                    
                elif "quota" in error_str or "rate limit" in error_str or "429" in error_str:
                    error_id = error_logger.log_error(func.__name__, e, level="warning")
                    raise RateLimitError(f"Rate limit exceeded: {e}", e) from e
                    
                elif "deadline exceeded" in error_str or "timeout" in error_str or "504" in error_str:
                    error_id = error_logger.log_error(func.__name__, e, level="warning")
                    raise TimeoutError(f"Operation timed out: {e}", e) from e
                    
                elif "unavailable" in error_str or "503" in error_str:
                    error_id = error_logger.log_error(func.__name__, e, level="warning")
                    raise TemporaryError(f"Service temporarily unavailable: {e}", e) from e
                    
                elif "precondition" in error_str or "400" in error_str:
                    error_id = error_logger.log_error(func.__name__, e, level="error")
                    raise PreconditionError(f"Operation precondition failed: {e}", e) from e
                    
                else:
                    # Default case - unexpected error
                    error_id = error_logger.log_error(
                        func.__name__, e, level="error", include_traceback=True
                    )
                    raise UnexpectedError(f"Unexpected error: {e}", e) from e
            
    return cast(AsyncFunc, wrapper)


def handle_llm_error(func: AsyncFunc) -> AsyncFunc:
    """
    Decorator for handling LLM provider errors with appropriate responses.
    
    This decorator catches errors from external LLM providers (OpenAI, Anthropic, etc.)
    and maps them to Orchestra's exception hierarchy. It also logs errors with
    consistent formatting.
    
    Example:
        @handle_llm_error
        async def generate_text(prompt):
            # LLM API calls here
    """
    error_logger = ErrorLogger(__name__)
    
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            # Try importing exception types from various LLM providers
            # If imports fail, we'll use generic exception handling
            openai_exceptions_available = False
            anthropic_exceptions_available = False
            portkey_exceptions_available = False
            
            try:
                from openai import (
                    APITimeoutError,
                    APIConnectionError,
                    RateLimitError,
                    APIStatusError,
                    BadRequestError,
                    AuthenticationError as OpenAIAuthError,
                    PermissionDeniedError
                )
                openai_exceptions_available = True
            except ImportError:
                pass
                
            try:
                from anthropic.errors import (
                    APITimeoutError as AnthropicTimeoutError,
                    APIConnectionError as AnthropicConnectionError,
                    RateLimitError as AnthropicRateLimitError,
                    BadRequestError as AnthropicBadRequestError
                )
                anthropic_exceptions_available = True
            except ImportError:
                pass
                
            try:
                from portkey_ai.api_resources.exceptions import APIError as PortkeyAPIError
                portkey_exceptions_available = True
            except ImportError:
                pass
                
            # Execute the function
            return await func(*args, **kwargs)
            
        except Exception as e:
            # Use specific exception types if available
            # OpenAI Exceptions
            if openai_exceptions_available:
                from openai import (
                    APITimeoutError,
                    APIConnectionError,
                    RateLimitError,
                    APIStatusError,
                    BadRequestError,
                    AuthenticationError as OpenAIAuthError,
                    PermissionDeniedError
                )
                
                if isinstance(e, APITimeoutError):
                    error_id = error_logger.log_error(
                        func.__name__, e, level="warning",
                        context={"provider": "openai", "error_type": "timeout"}
                    )
                    raise TimeoutError(f"OpenAI request timed out: {e}", e) from e
                    
                elif isinstance(e, APIConnectionError):
                    error_id = error_logger.log_error(
                        func.__name__, e, level="warning",
                        context={"provider": "openai", "error_type": "connection"}
                    )
                    raise ConnectionError(f"OpenAI connection error: {e}", e) from e
                    
                elif isinstance(e, RateLimitError):
                    error_id = error_logger.log_error(
                        func.__name__, e, level="warning",
                        context={"provider": "openai", "error_type": "rate_limit"}
                    )
                    raise RateLimitError(f"OpenAI rate limit exceeded: {e}", e) from e
                    
                elif isinstance(e, BadRequestError):
                    error_id = error_logger.log_error(
                        func.__name__, e, level="error",
                        context={"provider": "openai", "error_type": "bad_request"}
                    )
                    raise ValidationError(f"Invalid request to OpenAI: {e}", e) from e
                    
                elif isinstance(e, OpenAIAuthError):
                    error_id = error_logger.log_error(
                        func.__name__, e, level="error",
                        context={"provider": "openai", "error_type": "auth"}
                    )
                    raise AuthenticationError(f"OpenAI authentication failed: {e}", e) from e
                    
                elif isinstance(e, PermissionDeniedError):
                    error_id = error_logger.log_error(
                        func.__name__, e, level="error",
                        context={"provider": "openai", "error_type": "permission"}
                    )
                    raise AuthorizationError(f"OpenAI permission denied: {e}", e) from e
                    
                elif isinstance(e, APIStatusError):
                    status = getattr(e, "status_code", None)
                    error_id = error_logger.log_error(
                        func.__name__, e, level="error",
                        context={"provider": "openai", "status_code": status}
                    )
                    if status == 404:
                        raise NotFoundError(f"OpenAI resource not found: {e}", e) from e
                    else:
                        raise ServiceError(f"OpenAI API error: {e}", e) from e
                        
            # Anthropic Exceptions
            if anthropic_exceptions_available:
                from anthropic.errors import (
                    APITimeoutError as AnthropicTimeoutError,
                    APIConnectionError as AnthropicConnectionError,
                    RateLimitError as AnthropicRateLimitError,
                    BadRequestError as AnthropicBadRequestError
                )
                
                if isinstance(e, AnthropicTimeoutError):
                    error_id = error_logger.log_error(
                        func.__name__, e, level="warning",
                        context={"provider": "anthropic", "error_type": "timeout"}
                    )
                    raise TimeoutError(f"Anthropic request timed out: {e}", e) from e
                    
                elif isinstance(e, AnthropicConnectionError):
                    error_id = error_logger.log_error(
                        func.__name__, e, level="warning",
                        context={"provider": "anthropic", "error_type": "connection"}
                    )
                    raise ConnectionError(f"Anthropic connection error: {e}", e) from e
                    
                elif isinstance(e, AnthropicRateLimitError):
                    error_id = error_logger.log_error(
                        func.__name__, e, level="warning",
                        context={"provider": "anthropic", "error_type": "rate_limit"}
                    )
                    raise RateLimitError(f"Anthropic rate limit exceeded: {e}", e) from e
                    
                elif isinstance(e, AnthropicBadRequestError):
                    error_id = error_logger.log_error(
                        func.__name__, e, level="error",
                        context={"provider": "anthropic", "error_type": "bad_request"}
                    )
                    raise ValidationError(f"Invalid request to Anthropic: {e}", e) from e
                        
            # Portkey Exceptions
            if portkey_exceptions_available:
                from portkey_ai.api_resources.exceptions import APIError as PortkeyAPIError
                
                if isinstance(e, PortkeyAPIError):
                    error_id = error_logger.log_error(
                        func.__name__, e, level="error",
                        context={"provider": "portkey"}
                    )
                    raise ServiceError(f"Portkey API error: {e}", e) from e
            
            # Fallback to string matching if specific exceptions are not available
            error_str = str(e).lower()
            
            if any(term in error_str for term in ["timeout", "timed out", "deadline"]):
                error_id = error_logger.log_error(func.__name__, e, level="warning")
                raise TimeoutError(f"LLM request timed out: {e}", e) from e
                
            elif any(term in error_str for term in ["rate limit", "ratelimit", "too many requests", "429"]):
                error_id = error_logger.log_error(func.__name__, e, level="warning")
                raise RateLimitError(f"LLM rate limit exceeded: {e}", e) from e
                
            elif any(term in error_str for term in ["connect", "network", "unreachable"]):
                error_id = error_logger.log_error(func.__name__, e, level="warning")
                raise ConnectionError(f"LLM connection error: {e}", e) from e
                
            elif any(term in error_str for term in ["auth", "key", "permission", "access", "forbidden", "unauthorized"]):
                error_id = error_logger.log_error(func.__name__, e, level="error")
                raise AuthenticationError(f"LLM authentication error: {e}", e) from e
                
            elif any(term in error_str for term in ["invalid", "bad request", "validation"]):
                error_id = error_logger.log_error(func.__name__, e, level="error")
                raise ValidationError(f"Invalid LLM request: {e}", e) from e
                
            else:
                # Default case - unexpected error
                error_id = error_logger.log_error(
                    func.__name__, e, level="error", include_traceback=True,
                    context={"provider": "llm"}
                )
                raise ServiceError(f"LLM service error: {e}", e) from e
    
    return cast(AsyncFunc, wrapper)


#########################################
# Resource Cleanup Context Manager
#########################################

class ResourceManager:
    """Context manager for managing resources with proper cleanup."""
    
    def __init__(self, resource: Any, resource_name: str):
        """
        Initialize the resource manager.
        
        Args:
            resource: The resource to manage
            resource_name: A descriptive name for the resource
        """
        self.resource = resource
        self.resource_name = resource_name
        self.logger = logging.getLogger(__name__)
        
    def __enter__(self) -> Any:
        """Initialize the resource and return it."""
        self.logger.debug(f"Initializing resource: {self.resource_name}")
        return self.resource
        
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """Clean up the resource when exiting the context."""
        try:
            # Check if resource has close, shutdown or cleanup method
            if hasattr(self.resource, 'close') and callable(getattr(self.resource, 'close')):
                self.resource.close()
            elif hasattr(self.resource, 'shutdown') and callable(getattr(self.resource, 'shutdown')):
                self.resource.shutdown()
            elif hasattr(self.resource, 'cleanup') and callable(getattr(self.resource, 'cleanup')):
                self.resource.cleanup()
                
            self.logger.debug(f"Successfully cleaned up resource: {self.resource_name}")
        except Exception as e:
            self.logger.warning(f"Error cleaning up resource {self.resource_name}: {e}")
            # Don't suppress the original exception
            return False
        
        # Don't suppress any exceptions
        return False
        
    async def __aenter__(self) -> Any:
        """Initialize the resource and return it (async version)."""
        self.logger.debug(f"Initializing async resource: {self.resource_name}")
        return self.resource
        
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """Clean up the resource when exiting the context (async version)."""
        try:
            # Check for async close methods first
            if hasattr(self.resource, 'aclose') and callable(getattr(self.resource, 'aclose')):
                await self.resource.aclose()
            elif hasattr(self.resource, 'async_close') and callable(getattr(self.resource, 'async_close')):
                await self.resource.async_close()
            # Then check for methods that might be coroutines or regular methods
            elif hasattr(self.resource, 'close'):
                close_method = getattr(self.resource, 'close')
                if asyncio.iscoroutinefunction(close_method):
                    await close_method()
                else:
                    close_method()
            elif hasattr(self.resource, 'shutdown'):
                shutdown_method = getattr(self.resource, 'shutdown')
                if asyncio.iscoroutinefunction(shutdown_method):
                    await shutdown_method()
                else:
                    shutdown_method()
            elif hasattr(self.resource, 'cleanup'):
                cleanup_method = getattr(self.resource, 'cleanup')
                if asyncio.iscoroutinefunction(cleanup_method):
                    await cleanup_method()
                else:
                    cleanup_method()
                
            self.logger.debug(f"Successfully cleaned up async resource: {self.resource_name}")
        except Exception as e:
            self.logger.warning(f"Error cleaning up async resource {self.resource_name}: {e}")
            # Don't suppress the original exception
            return False
        
        # Don't suppress any exceptions
        return False


#########################################
# Circuit Breaker Pattern
#########################################

class CircuitBreaker:
    """
    Circuit breaker pattern implementation to prevent cascading failures.
    
    The circuit breaker prevents repeated calls to a failing service by
    "opening" after a threshold of failures and only allowing limited
    "test" calls after a recovery timeout.
    """
    
    # Circuit states
    CLOSED = "closed"  # Normal operation, requests go through
    OPEN = "open"      # Failed state, requests are blocked
    HALF_OPEN = "half_open"  # Testing state, limited requests allowed
    
    def __init__(
        self, 
        name: str,
        failure_threshold: int = 5, 
        recovery_timeout: int = 30, 
        half_open_max: int = 2
    ):
        """
        Initialize the circuit breaker.
        
        Args:
            name: Name of the circuit for logging
            failure_threshold: Number of failures before opening the circuit
            recovery_timeout: Seconds before allowing test requests
            half_open_max: Maximum number of requests in half-open state
        """
        self.name = name
        self.state = self.CLOSED
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max = half_open_max
        self.half_open_count = 0
        self.last_failure_time = None
        self.logger = logging.getLogger(__name__)
        
    def allow_request(self) -> bool:
        """
        Determine if a request should be allowed based on circuit state.
        
        Returns:
            True if the request should be allowed, False otherwise
        """
        now = time.time()
        
        if self.state == self.OPEN:
            # Check if recovery timeout has elapsed
            if self.last_failure_time and now - self.last_failure_time > self.recovery_timeout:
                self.logger.info(f"Circuit '{self.name}' transitioning from OPEN to HALF_OPEN")
                self.state = self.HALF_OPEN
                self.half_open_count = 0
                return True
            return False
            
        if self.state == self.HALF_OPEN:
            # Only allow limited requests in half-open state
            if self.half_open_count < self.half_open_max:
                self.half_open_count += 1
                return True
            return False
            
        # Circuit is CLOSED, always allow
        return True
        
    def record_success(self) -> None:
        """Record successful request, potentially closing circuit."""
        if self.state == self.HALF_OPEN:
            self.logger.info(f"Circuit '{self.name}': Successful request in HALF_OPEN state, closing circuit")
            self.state = self.CLOSED
            self.failure_count = 0
            
    def record_failure(self) -> None:
        """Record failed request, potentially opening circuit."""
        self.last_failure_time = time.time()
        
        if self.state == self.HALF_OPEN:
            self.logger.warning(f"Circuit '{self.name}': Request failed in HALF_OPEN state, reopening circuit")
            self.state = self.OPEN
            return
            
        # Increment failure count
        self.failure_count += 1
        
        # Check if threshold exceeded
        if self.state == self.CLOSED and self.failure_count >= self.failure_threshold:
            self.logger.warning(
                f"Circuit '{self.name}': Failure threshold reached ({self.failure_count}), opening circuit"
            )
            self.state = self.OPEN


def with_circuit_breaker(circuit: CircuitBreaker) -> Callable[[AsyncFunc], AsyncFunc]:
    """
    Decorator for applying circuit breaker pattern to functions.
    
    Args:
        circuit: The CircuitBreaker instance to use
        
    Returns:
        Decorator function
    
    Example:
        # Create a circuit breaker
        firestore_circuit = CircuitBreaker("firestore", failure_threshold=3)
        
        # Apply to a function
        @with_circuit_breaker(firestore_circuit)
        async def get_document(doc_id):
            # Function implementation
    """
    def decorator(func: AsyncFunc) -> AsyncFunc:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Check if request is allowed
            if not circuit.allow_request():
                raise TemporaryError(
                    f"Circuit '{circuit.name}' is open, request rejected",
                    None
                )
                
            try:
                # Execute the function
                result = await func(*args, **kwargs)
                # Record success
                circuit.record_success()
                return result
            except Exception as e:
                # Record failure
                circuit.record_failure()
                # Re-raise the exception
                raise
                
        return cast(AsyncFunc, wrapper)
    return decorator


#########################################
# Retry Decorator
#########################################

def with_retry(
    max_retries: int = 3, 
    base_delay: float = 0.1, 
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: tuple = (ConnectionError, TimeoutError, TemporaryError)
) -> Callable[[AsyncFunc], AsyncFunc]:
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Multiplier for the delay after each attempt
        retryable_exceptions: Tuple of exceptions that should trigger a retry
        
    Returns:
        Decorator function
    
    Example:
        @with_retry(max_retries=5, retryable_exceptions=(ConnectionError, TimeoutError))
        async def make_api_call(endpoint):
            # Function implementation
    """
    def decorator(func: AsyncFunc) -> AsyncFunc:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            error_logger = ErrorLogger(__name__)
            
            # Track the last exception for re-raising
            last_exception = None
            
            for attempt in range(max_retries + 1):  # +1 because first attempt is not a retry
                try:
                    # Execute the function
                    return await func(*args, **kwargs)
                    
                except retryable_exceptions as e:
                    last_exception = e
                    
                    # If this was the last attempt, re-raise the exception
                    if attempt >= max_retries:
                        error_logger.log_error(
                            func.__name__, e, 
                            context={"retries_exhausted": True, "attempts": attempt + 1}
                        )
                        raise
                        
                    # Calculate delay with exponential backoff
                    delay = min(max_delay, base_delay * (backoff_factor ** attempt))
                    
                    # Log the retry
                    error_logger.log_error(
                        func.__name__, e, 
                        level="warning",
                        context={
                            "retry_attempt": attempt + 1, 
                            "max_retries": max_retries,
                            "delay": delay
                        }
                    )
                    
                    # Wait before retrying
                    await asyncio.sleep(delay)
                except Exception as e:
                    # Non-retryable exception, just re-raise
                    raise
                    
            # This should never be reached due to the re-raise in the loop,
            # but added for safety
            if last_exception:
                raise last_exception
                
            # Should never reach here
            raise RuntimeError("Unexpected error in retry logic")
            
        return cast(AsyncFunc, wrapper)
    return decorator


#########################################
# Usage Example / Demo
#########################################

async def example_usage():
    """Example usage of error handling utilities."""
    # Setup custom circuit breaker for Firestore
    firestore_circuit = CircuitBreaker(
        name="firestore", 
        failure_threshold=3,
        recovery_timeout=10
    )
    
    # Example: GCP error handling with retry and circuit breaker
    @with_retry(max_retries=3, retryable_exceptions=(TemporaryError, TimeoutError))
    @with_circuit_breaker(firestore_circuit)
    @handle_gcp_error
    async def get_firestore_document(doc_id: str) -> Dict[str, Any]:
        """Example of a function with comprehensive error handling."""
        # This would be an actual Firestore call
        # For demo purposes, we'll simulate different errors
        if "not_found" in doc_id:
            # Simulate 404 not found
            from google.api_core.exceptions import NotFound
            raise NotFound(f"Document {doc_id} not found")
        elif "timeout" in doc_id:
            # Simulate timeout
            from google.api_core.exceptions import DeadlineExceeded
            raise DeadlineExceeded(f"Timeout retrieving {doc_id}")
        elif "permission" in doc_id:
            # Simulate permission denied
            from google.api_core.exceptions import PermissionDenied
            raise PermissionDenied(f"Permission denied for {doc_id}")
        
        # Simulate successful response
        return {"id": doc_id, "data": {"sample": "data"}}
    
    # Example: LLM error handling
    @with_retry(max_retries=2)
    @handle_llm_error
    async def generate_text(prompt: str) -> str:
        """Example of handling LLM provider errors."""
        # This would be an actual LLM API call
        # For demo purposes, we'll simulate different errors
        if "timeout" in prompt:
            # Simulate timeout error
            raise TimeoutError("LLM request timed out")
        elif "rate_limit" in prompt:
            # Simulate rate limit error
            raise RateLimitError("Rate limit exceeded")
        
        # Simulate successful response
        return f"Generated text for: {prompt}"
    
    # Example: Resource management
    async def use_resource():
        """Example of resource management with context manager."""
        # Create a mock resource with cleanup method
        class MockResource:
            def __init__(self):
                self.logger = logging.getLogger(__name__)
                self.logger.info("Resource initialized")
                
            def close(self):
                self.logger.info("Resource closed")
        
        # Use the resource with context manager
        resource = MockResource()
        async with ResourceManager(resource, "mock_resource"):
            # Do something with the resource
            logger.info("Using resource within context")
            # If an exception occurs here, the resource will still be cleaned up
