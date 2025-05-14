#!/usr/bin/env python3
"""
Unified Circuit Breaker Pattern for AI Orchestra

This module provides a thread-safe, robust circuit breaker pattern implementation 
for protecting services during failure conditions. It supports both synchronous 
and asynchronous code, preserves exception context, and offers detailed telemetry.

Key improvements over previous implementations:
- Thread-safety with proper locking to prevent race conditions
- Preservation of original exception context
- Configurable fallback functions with typed returns
- Built-in metrics and telemetry
- Support for both sync and async operations with the same API
- Clear state transition logging

Usage:
    # Synchronous usage with decorator
    from gcp_migration.circuit_breaker_unified import circuit_break
    
    @circuit_break(name="my_service")
    def my_function(arg1, arg2):
        # Function that might fail
        return result
    
    # Asynchronous usage with decorator
    @circuit_break(name="my_async_service")
    async def my_async_function(arg1, arg2):
        # Async function that might fail
        return result
    
    # Direct usage
    from gcp_migration.circuit_breaker_unified import CircuitBreaker
    
    breaker = CircuitBreaker(name="custom_breaker", failure_threshold=3)
    result = breaker.execute(my_function, arg1, arg2)
    
    # With fallback
    def fallback_function(arg1, arg2, exception):
        # Alternative implementation when circuit is open
        return fallback_result
    
    breaker = CircuitBreaker(
        name="with_fallback", 
        fallback_function=fallback_function
    )
    result = breaker.execute(my_function, arg1, arg2)
"""

import asyncio
import functools
import logging
import threading
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, Type, TypeVar, Union, cast

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("circuit-breaker")

# Type variables for generic typing
T = TypeVar("T")  # Return type of the protected function
F = TypeVar("F", bound=Callable[..., Any])  # Function type for decorators


class CircuitState(Enum):
    """Circuit breaker state."""
    CLOSED = "CLOSED"      # Normal operation - requests are allowed
    OPEN = "OPEN"          # Circuit is broken - requests fail fast
    HALF_OPEN = "HALF_OPEN"  # Testing if service is back - limited requests


class CircuitBreakerError(Exception):
    """Base exception for circuit breaker errors."""
    pass


class CircuitOpenError(CircuitBreakerError):
    """Error raised when circuit is open."""
    
    def __init__(self, breaker_name: str, until: datetime, original_exceptions: List[Exception]):
        """Initialize open circuit error.
        
        Args:
            breaker_name: Name of the circuit breaker
            until: Time until circuit might close
            original_exceptions: List of exceptions that caused the circuit to open
        """
        self.breaker_name = breaker_name
        self.until = until
        self.original_exceptions = original_exceptions
        
        if original_exceptions:
            recent_errors = "; ".join(str(e) for e in original_exceptions[-3:])
            message = (
                f"Circuit '{breaker_name}' is OPEN until {until.isoformat()}. "
                f"Recent errors: {recent_errors}"
            )
        else:
            message = f"Circuit '{breaker_name}' is OPEN until {until.isoformat()}"
            
        super().__init__(message)


class CircuitBreaker(Generic[T]):
    """Thread-safe circuit breaker implementation."""
    
    # Class-level registry of circuit breakers
    _registry: Dict[str, "CircuitBreaker"] = {}
    _registry_lock = threading.RLock()
    
    @classmethod
    def get_breaker(cls, name: str) -> "CircuitBreaker":
        """Get a circuit breaker by name, creating if it doesn't exist.
        
        Args:
            name: Name of the circuit breaker
            
        Returns:
            Circuit breaker instance
        """
        with cls._registry_lock:
            if name not in cls._registry:
                cls._registry[name] = CircuitBreaker(name=name)
            return cls._registry[name]
    
    @classmethod
    def reset_all(cls) -> None:
        """Reset all circuit breakers."""
        with cls._registry_lock:
            for breaker in cls._registry.values():
                breaker.reset()
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 1,
        excluded_exceptions: Optional[List[Type[Exception]]] = None,
        fallback_function: Optional[Callable[..., T]] = None,
    ):
        """Initialize circuit breaker.
        
        Args:
            name: Circuit name
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before trying again
            half_open_max_calls: Max calls in half-open state
            excluded_exceptions: Exceptions that don't count as failures
            fallback_function: Function to call when circuit is open
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.excluded_exceptions = excluded_exceptions or []
        self.fallback_function = fallback_function
        
        # State variables - protected by lock
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._half_open_calls = 0
        self._recent_exceptions: List[Exception] = []
        
        # Telemetry counters
        self._success_count = 0
        self._failure_count_total = 0
        self._rejection_count = 0
        self._state_transition_count = 0
        
        # Thread safety
        self._lock = threading.RLock()
        
        logger.info(f"Circuit breaker '{name}' initialized")
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            self._check_state_transition()
            return self._state
    
    @property
    def metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics."""
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "failure_count_total": self._failure_count_total,
                "rejection_count": self._rejection_count,
                "state_transition_count": self._state_transition_count,
                "last_failure_time": self._last_failure_time.isoformat() if self._last_failure_time else None,
                "recovery_time": (
                    (self._last_failure_time + timedelta(seconds=self.recovery_timeout)).isoformat()
                    if self._last_failure_time and self._state == CircuitState.OPEN
                    else None
                ),
                "half_open_calls": self._half_open_calls,
            }
    
    def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        with self._lock:
            old_state = self._state
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None
            self._half_open_calls = 0
            self._recent_exceptions = []
            
            if old_state != CircuitState.CLOSED:
                self._state_transition_count += 1
                logger.info(f"Circuit breaker '{self.name}' reset from {old_state.value} to CLOSED")
    
    def _check_state_transition(self) -> None:
        """Check and possibly transition circuit state based on timeouts.
        
        This method is called whenever the state is accessed and handles
        automatic transition from OPEN to HALF-OPEN after recovery_timeout.
        It is thread-safe as it's always called within a lock context.
        """
        # Already protected by lock from caller
        if (
            self._state == CircuitState.OPEN
            and self._last_failure_time is not None
            and datetime.now() >= self._last_failure_time + timedelta(seconds=self.recovery_timeout)
        ):
            self._state = CircuitState.HALF_OPEN
            self._half_open_calls = 0
            self._state_transition_count += 1
            logger.info(
                f"Circuit '{self.name}' auto-transitioned from OPEN to HALF-OPEN after "
                f"{self.recovery_timeout}s"
            )
    
    def _record_success(self) -> None:
        """Record a successful call."""
        with self._lock:
            self._success_count += 1
            
            if self._state == CircuitState.HALF_OPEN:
                logger.info(f"Circuit '{self.name}' closing after successful test")
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._last_failure_time = None
                self._half_open_calls = 0
                self._recent_exceptions = []
                self._state_transition_count += 1
            elif self._state == CircuitState.CLOSED:
                # In closed state, successful calls reset the failure count
                self._failure_count = 0
    
    def _record_failure(self, exception: Exception) -> None:
        """Record a failed call.
        
        Args:
            exception: Exception that caused the failure
        """
        with self._lock:
            self._failure_count_total += 1
            self._last_failure_time = datetime.now()
            
            # Keep the most recent exceptions
            self._recent_exceptions.append(exception)
            if len(self._recent_exceptions) > 10:
                self._recent_exceptions = self._recent_exceptions[-10:]
            
            if self._state == CircuitState.HALF_OPEN:
                logger.warning(
                    f"Circuit '{self.name}' reopening after failed test: {str(exception)}"
                )
                self._state = CircuitState.OPEN
                self._state_transition_count += 1
            elif self._state == CircuitState.CLOSED:
                self._failure_count += 1
                if self._failure_count >= self.failure_threshold:
                    logger.warning(
                        f"Circuit '{self.name}' tripped OPEN after {self._failure_count} failures. "
                        f"Last error: {str(exception)}"
                    )
                    self._state = CircuitState.OPEN
                    self._state_transition_count += 1
    
    def _allow_request(self) -> bool:
        """Check if a request should be allowed through.
        
        Returns:
            True if the request is allowed, False otherwise
        """
        with self._lock:
            self._check_state_transition()
            
            if self._state == CircuitState.CLOSED:
                return True
            
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls < self.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False
            
            # Circuit is OPEN
            self._rejection_count += 1
            return False
    
    def _get_recovery_time(self) -> Optional[datetime]:
        """Get the time when the circuit might transition to HALF-OPEN.
        
        Returns:
            Datetime when recovery might occur or None if not applicable
        """
        with self._lock:
            if self._state == CircuitState.OPEN and self._last_failure_time is not None:
                return self._last_failure_time + timedelta(seconds=self.recovery_timeout)
            return None
    
    def execute(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Positional arguments to pass to function
            **kwargs: Keyword arguments to pass to function
            
        Returns:
            Function result
            
        Raises:
            CircuitOpenError: If circuit is open
            Exception: Original exception if call fails and no fallback
        """
        if not self._allow_request():
            recovery_time = self._get_recovery_time()
            if recovery_time is None:
                recovery_time = datetime.now() + timedelta(seconds=self.recovery_timeout)
                
            # Get a copy of recent exceptions to preserve context
            with self._lock:
                recent_exceptions = self._recent_exceptions.copy()
                
            if self.fallback_function:
                try:
                    return self.fallback_function(*args, **kwargs, exception=CircuitOpenError(
                        self.name, recovery_time, recent_exceptions
                    ))
                except Exception as fallback_error:
                    logger.error(f"Fallback function for circuit '{self.name}' failed: {fallback_error}")
                    raise CircuitOpenError(self.name, recovery_time, recent_exceptions) from fallback_error
            else:
                raise CircuitOpenError(self.name, recovery_time, recent_exceptions)
        
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            # Check if this exception should be counted as a failure
            if not any(isinstance(e, exc_type) for exc_type in self.excluded_exceptions):
                self._record_failure(e)
            # Re-raise the original exception to preserve context
            raise
    
    async def execute_async(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute async function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args: Positional arguments to pass to function
            **kwargs: Keyword arguments to pass to function
            
        Returns:
            Function result
            
        Raises:
            CircuitOpenError: If circuit is open
            Exception: Original exception if call fails and no fallback
        """
        if not self._allow_request():
            recovery_time = self._get_recovery_time()
            if recovery_time is None:
                recovery_time = datetime.now() + timedelta(seconds=self.recovery_timeout)
                
            # Get a copy of recent exceptions to preserve context
            with self._lock:
                recent_exceptions = self._recent_exceptions.copy()
                
            if self.fallback_function:
                try:
                    if asyncio.iscoroutinefunction(self.fallback_function):
                        return await self.fallback_function(*args, **kwargs, exception=CircuitOpenError(
                            self.name, recovery_time, recent_exceptions
                        ))
                    else:
                        return self.fallback_function(*args, **kwargs, exception=CircuitOpenError(
                            self.name, recovery_time, recent_exceptions
                        ))
                except Exception as fallback_error:
                    logger.error(f"Fallback function for circuit '{self.name}' failed: {fallback_error}")
                    raise CircuitOpenError(self.name, recovery_time, recent_exceptions) from fallback_error
            else:
                raise CircuitOpenError(self.name, recovery_time, recent_exceptions)
        
        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            # Check if this exception should be counted as a failure
            if not any(isinstance(e, exc_type) for exc_type in self.excluded_exceptions):
                self._record_failure(e)
            # Re-raise the original exception to preserve context
            raise


def circuit_break(
    func: Optional[F] = None,
    *,
    name: Optional[str] = None,
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    half_open_max_calls: int = 1,
    excluded_exceptions: Optional[List[Type[Exception]]] = None,
    fallback_function: Optional[Callable[..., Any]] = None,
) -> Any:
    """Circuit breaker decorator.
    
    This decorator can be used with or without arguments.
    
    Args:
        func: Function to decorate (when used without arguments)
        name: Circuit breaker name
        failure_threshold: Failures before opening circuit
        recovery_timeout: Seconds before trying again
        half_open_max_calls: Max calls in half-open state
        excluded_exceptions: Exceptions that don't count as failures
        fallback_function: Function to call when circuit is open
        
    Returns:
        Decorated function
    """
    def decorator(f: F) -> F:
        # Use function name as circuit name if not provided
        breaker_name = name or f.__qualname__
        
        # Get or create circuit breaker
        breaker = CircuitBreaker.get_breaker(breaker_name)
        
        # Update circuit breaker parameters
        breaker.failure_threshold = failure_threshold
        breaker.recovery_timeout = recovery_timeout
        breaker.half_open_max_calls = half_open_max_calls
        if excluded_exceptions is not None:
            breaker.excluded_exceptions = excluded_exceptions
        if fallback_function is not None:
            breaker.fallback_function = fallback_function
        
        @functools.wraps(f)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            return breaker.execute(f, *args, **kwargs)
        
        @functools.wraps(f)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            return await breaker.execute_async(f, *args, **kwargs)
        
        if asyncio.iscoroutinefunction(f):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)
    
    # Handle both @circuit_break and @circuit_break()
    if func is not None:
        return decorator(func)
    return decorator


# Example usage and test code
if __name__ == "__main__":
    import random
    import sys
    
    # Set up test functions
    @circuit_break(failure_threshold=3, recovery_timeout=5.0)
    def unreliable_service() -> str:
        """Test function that sometimes fails."""
        if random.random() < 0.7:  # 70% chance of failure
            raise ValueError("Service failed")
        return "Service succeeded"
    
    @circuit_break(name="async_service", failure_threshold=3, recovery_timeout=5.0)
    async def unreliable_async_service() -> str:
        """Test async function that sometimes fails."""
        await asyncio.sleep(0.1)  # Simulate async work
        if random.random() < 0.7:  # 70% chance of failure
            raise ValueError("Async service failed")
        return "Async service succeeded"
    
    def fallback_service(*args, **kwargs) -> str:
        """Fallback function for circuit breaker."""
        exception = kwargs.get("exception")
        return f"Fallback service: {exception}"
    
    # Create a circuit breaker with fallback
    breaker_with_fallback = CircuitBreaker(
        name="with_fallback",
        failure_threshold=3,
        recovery_timeout=5.0,
        fallback_function=fallback_service
    )
    
    # Test synchronous circuit breaker
    def test_sync():
        print("\nTesting synchronous circuit breaker")
        print("-" * 40)
        
        for i in range(10):
            try:
                result = unreliable_service()
                print(f"Call {i+1}: Success - {result}")
            except CircuitOpenError as e:
                print(f"Call {i+1}: Circuit open until {e.until}")
            except ValueError:
                print(f"Call {i+1}: Service failed")
            
            # Wait a bit
            time.sleep(0.5)
        
        print("\nWaiting for circuit to reset...")
        time.sleep(5)
        
        for i in range(10, 15):
            try:
                result = unreliable_service()
                print(f"Call {i+1}: Success - {result}")
            except CircuitOpenError as e:
                print(f"Call {i+1}: Circuit open until {e.until}")
            except ValueError:
                print(f"Call {i+1}: Service failed")
            
            # Wait a bit
            time.sleep(0.5)
    
    # Test circuit breaker with fallback
    def test_fallback():
        print("\nTesting circuit breaker with fallback")
        print("-" * 40)
        
        def test_function():
            if random.random() < 0.7:  # 70% chance of failure
                raise ValueError("Test function failed")
            return "Test function succeeded"
        
        for i in range(10):
            try:
                result = breaker_with_fallback.execute(test_function)
                print(f"Call {i+1}: Success - {result}")
            except Exception as e:
                print(f"Call {i+1}: Error - {e}")
            
            # Wait a bit
            time.sleep(0.5)
    
    # Test asynchronous circuit breaker
    async def test_async():
        print("\nTesting asynchronous circuit breaker")
        print("-" * 40)
        
        for i in range(10):
            try:
                result = await unreliable_async_service()
                print(f"Call {i+1}: Success - {result}")
            except CircuitOpenError as e:
                print(f"Call {i+1}: Circuit open until {e.until}")
            except ValueError:
                print(f"Call {i+1}: Service failed")
            
            # Wait a bit
            await asyncio.sleep(0.5)
        
        print("\nWaiting for circuit to reset...")
        await asyncio.sleep(5)
        
        for i in range(10, 15):
            try:
                result = await unreliable_async_service()
                print(f"Call {i+1}: Success - {result}")
            except CircuitOpenError as e:
                print(f"Call {i+1}: Circuit open until {e.until}")
            except ValueError:
                print(f"Call {i+1}: Service failed")
            
            # Wait a bit
            await asyncio.sleep(0.5)
    
    # Run tests
    print("Circuit Breaker Test Suite")
    print("=" * 40)
    
    if len(sys.argv) > 1 and sys.argv[1] == "async":
        # Run async test
        asyncio.run(test_async())
    elif len(sys.argv) > 1 and sys.argv[1] == "fallback":
        # Run fallback test
        test_fallback()
    else:
        # Run sync test
        test_sync()
    
    # Show metrics
    print("\nCircuit Breaker Metrics:")
    print("-" * 40)
    metrics = CircuitBreaker.get_breaker("unreliable_service").metrics
    for key, value in metrics.items():
        print(f"{key}: {value}")