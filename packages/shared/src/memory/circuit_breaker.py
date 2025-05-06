"""
Circuit Breaker pattern implementation for AI Orchestra memory system.

This module provides a circuit breaker implementation to improve resilience
when interacting with external services like Firestore.
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, TypeVar, Generic, cast, Awaitable

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for generic functions
T = TypeVar('T')

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation, requests pass through
    OPEN = "open"      # Failing, requests are blocked
    HALF_OPEN = "half_open"  # Testing if service is back online


class CircuitBreakerError(Exception):
    """Exception raised when the circuit breaker is open."""
    
    def __init__(self, message: str, last_error: Optional[Exception] = None):
        self.message = message
        self.last_error = last_error
        super().__init__(message)


class CircuitBreaker:
    """
    Circuit breaker implementation for external service calls.
    
    This class implements the circuit breaker pattern to prevent
    cascading failures when an external service is experiencing issues.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 1,
        reset_timeout: float = 60.0,
        excluded_exceptions: Optional[List[type]] = None,
    ):
        """
        Initialize the circuit breaker.
        
        Args:
            name: Name of the circuit breaker
            failure_threshold: Number of failures before opening the circuit
            recovery_timeout: Time in seconds to wait before trying recovery
            half_open_max_calls: Maximum number of calls in half-open state
            reset_timeout: Time in seconds to reset failure count if no failures
            excluded_exceptions: Exceptions that don't count as failures
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.reset_timeout = reset_timeout
        self.excluded_exceptions = excluded_exceptions or []
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._last_success_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()
        self._last_error: Optional[Exception] = None
        
    async def _check_state_transition(self) -> None:
        """Check if the circuit breaker should transition to a different state."""
        now = time.time()
        
        if self._state == CircuitState.OPEN:
            # Check if recovery timeout has elapsed
            if (self._last_failure_time is not None and 
                now - self._last_failure_time >= self.recovery_timeout):
                logger.info(f"Circuit {self.name} transitioning from OPEN to HALF_OPEN")
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
                
        elif self._state == CircuitState.CLOSED:
            # Check if failure threshold has been reached
            if self._failure_count >= self.failure_threshold:
                logger.warning(
                    f"Circuit {self.name} transitioning from CLOSED to OPEN "
                    f"after {self._failure_count} failures"
                )
                self._state = CircuitState.OPEN
                
            # Check if we should reset the failure count
            elif (self._last_success_time is not None and 
                  self._last_failure_time is not None and
                  self._last_success_time > self._last_failure_time and
                  now - self._last_success_time >= self.reset_timeout):
                logger.info(f"Resetting failure count for circuit {self.name}")
                self._failure_count = 0
                
    async def _record_success(self) -> None:
        """Record a successful call."""
        async with self._lock:
            self._last_success_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_calls += 1
                
                # If we've had enough successful calls in half-open state,
                # transition back to closed
                if self._half_open_calls >= self.half_open_max_calls:
                    logger.info(f"Circuit {self.name} transitioning from HALF_OPEN to CLOSED")
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    
    async def _record_failure(self, error: Exception) -> None:
        """Record a failed call."""
        async with self._lock:
            # Check if this exception type should be excluded
            if any(isinstance(error, exc_type) for exc_type in self.excluded_exceptions):
                logger.debug(f"Excluded exception {type(error).__name__} for circuit {self.name}")
                return
                
            self._failure_count += 1
            self._last_failure_time = time.time()
            self._last_error = error
            
            if self._state == CircuitState.HALF_OPEN:
                logger.warning(f"Circuit {self.name} transitioning from HALF_OPEN to OPEN")
                self._state = CircuitState.OPEN
                
            await self._check_state_transition()
            
    async def execute(self, func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T:
        """
        Execute a function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function
            
        Raises:
            CircuitBreakerError: If the circuit is open
            Exception: Any exception raised by the function
        """
        async with self._lock:
            await self._check_state_transition()
            
            if self._state == CircuitState.OPEN:
                error_msg = f"Circuit {self.name} is OPEN, rejecting request"
                logger.warning(error_msg)
                raise CircuitBreakerError(error_msg, self._last_error)
                
        try:
            result = await func(*args, **kwargs)
            await self._record_success()
            return result
        except Exception as e:
            await self._record_failure(e)
            raise
            
    def __call__(self, func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        """
        Decorator for async functions to apply circuit breaker protection.
        
        Args:
            func: Async function to protect
            
        Returns:
            Protected async function
        """
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await self.execute(func, *args, **kwargs)
            
        return wrapper