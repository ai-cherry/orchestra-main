"""
Resilience patterns for GCP service interactions.

This module provides circuit breakers, retries, and other resilience patterns
to make interactions with GCP services more robust in the face of transient failures.
"""

import asyncio
import functools
import logging
import random
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
    cast,
    Union,
)

from ..domain.exceptions_fixed import (
    APIError,
    BatchProcessingError,
    ConnectionError,
    ResourceExhaustedError,
    TimeoutError,
    MigrationError,
)

# Configure logging
logger = logging.getLogger(__name__)

# Type definitions
T = TypeVar("T")
R = TypeVar("R")
AsyncFunc = Callable[..., Awaitable[T]]
SyncFunc = Callable[..., T]
Func = Union[AsyncFunc[T], SyncFunc[T]]


class CircuitState(Enum):
    """States of a circuit breaker."""

    CLOSED = auto()  # Normal operation - requests are allowed
    OPEN = auto()  # Circuit is open - requests are rejected
    HALF_OPEN = auto()  # Testing if the service is healthy again


@dataclass
class CircuitBreakerConfig:
    """Configuration for a circuit breaker."""

    # Number of failures before opening the circuit
    failure_threshold: int = 5

    # Time in seconds to wait before transitioning from OPEN to HALF_OPEN
    reset_timeout: float = 30.0

    # Maximum number of requests allowed in HALF_OPEN state
    half_open_max_calls: int = 3

    # Number of successful requests in HALF_OPEN state to close the circuit
    success_threshold: int = 2

    # Exceptions that should be counted as failures
    failure_exceptions: List[type] = None

    # Window size for the rolling window of calls (in seconds)
    window_size: float = 60.0

    def __post_init__(self):
        """Initialize default values."""
        if self.failure_exceptions is None:
            self.failure_exceptions = [
                APIError,
                ConnectionError,
                TimeoutError,
                ResourceExhaustedError,
                BatchProcessingError,
            ]


class CircuitBreaker:
    """
    Circuit breaker implementation to prevent cascading failures.

    This class implements the circuit breaker pattern, which helps to prevent
    a failure in one service from cascading to other services by temporarily
    disabling operations after a number of failures.
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """
        Initialize the circuit breaker.

        Args:
            name: Name of the circuit breaker
            config: Circuit breaker configuration
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()

        # State
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        self._last_failure_time = 0.0
        self._last_state_change_time = time.time()

        # Rolling window of calls
        self._call_history: List[Tuple[float, bool]] = []  # [(timestamp, success)]

        # Lock for thread safety
        self._lock = asyncio.Lock()

    async def execute(self, func: AsyncFunc[T], *args, **kwargs) -> T:
        """
        Execute a function with circuit breaking.

        Args:
            func: Async function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function

        Raises:
            CircuitOpenError: If the circuit is open
            OriginalError: If the function raises an error
        """
        # Check if the circuit is open
        await self._check_state()

        try:
            # Execute the function
            result = await func(*args, **kwargs)

            # Record success
            await self._record_success()

            return result

        except Exception as e:
            # Check if this is a failure exception
            is_failure = any(
                isinstance(e, exc) for exc in self.config.failure_exceptions
            )

            if is_failure:
                # Record the failure
                await self._record_failure()

            # Re-raise the exception
            raise

    async def execute_sync(self, func: SyncFunc[T], *args, **kwargs) -> T:
        """
        Execute a synchronous function with circuit breaking.

        Args:
            func: Synchronous function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function

        Raises:
            CircuitOpenError: If the circuit is open
            OriginalError: If the function raises an error
        """
        # Check if the circuit is open
        await self._check_state()

        try:
            # Execute the function
            result = func(*args, **kwargs)

            # Record success
            await self._record_success()

            return result

        except Exception as e:
            # Check if this is a failure exception
            is_failure = any(
                isinstance(e, exc) for exc in self.config.failure_exceptions
            )

            if is_failure:
                # Record the failure
                await self._record_failure()

            # Re-raise the exception
            raise

    async def _check_state(self) -> None:
        """
        Check the current state of the circuit and react accordingly.

        Raises:
            CircuitOpenError: If the circuit is open
        """
        async with self._lock:
            current_time = time.time()

            # Clean up old calls from history
            self._clean_call_history(current_time)

            # Check state transition
            if self._state == CircuitState.OPEN:
                # Check if the reset timeout has elapsed
                if (
                    current_time - self._last_failure_time
                ) >= self.config.reset_timeout:
                    # Transition to HALF_OPEN
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    self._success_count = 0
                    self._last_state_change_time = current_time
                    logger.info(
                        f"Circuit '{self.name}' transitioned from OPEN to HALF_OPEN"
                    )
                else:
                    # Circuit is still open
                    raise CircuitOpenError(
                        f"Circuit '{self.name}' is OPEN",
                        state=self._state,
                        will_reset_at=self._last_failure_time
                        + self.config.reset_timeout,
                    )

            elif self._state == CircuitState.HALF_OPEN:
                # Check if we've exceeded the maximum allowed calls
                if self._half_open_calls >= self.config.half_open_max_calls:
                    # Too many calls in HALF_OPEN state
                    raise CircuitOpenError(
                        f"Circuit '{self.name}' is HALF_OPEN and at max calls",
                        state=self._state,
                        will_reset_at=self._last_failure_time
                        + self.config.reset_timeout,
                    )

                # Increment the half-open calls counter
                self._half_open_calls += 1

    async def _record_success(self) -> None:
        """Record a successful call."""
        async with self._lock:
            current_time = time.time()

            # Add to call history
            self._call_history.append((current_time, True))

            # Update success count for HALF_OPEN state
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1

                # Check if we have reached the success threshold
                if self._success_count >= self.config.success_threshold:
                    # Transition to CLOSED
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._last_state_change_time = current_time
                    logger.info(
                        f"Circuit '{self.name}' transitioned from HALF_OPEN to CLOSED"
                    )

    async def _record_failure(self) -> None:
        """Record a failed call."""
        async with self._lock:
            current_time = time.time()

            # Add to call history
            self._call_history.append((current_time, False))

            # Update state based on the failure
            if self._state == CircuitState.CLOSED:
                # Count failures in the window
                self._failure_count = sum(
                    1 for ts, success in self._call_history if not success
                )

                # Check if we have reached the failure threshold
                if self._failure_count >= self.config.failure_threshold:
                    # Transition to OPEN
                    self._state = CircuitState.OPEN
                    self._last_failure_time = current_time
                    self._last_state_change_time = current_time
                    logger.warning(
                        f"Circuit '{self.name}' transitioned from CLOSED to OPEN "
                        f"after {self._failure_count} failures"
                    )

            elif self._state == CircuitState.HALF_OPEN:
                # Any failure in HALF_OPEN returns the circuit to OPEN
                self._state = CircuitState.OPEN
                self._last_failure_time = current_time
                self._last_state_change_time = current_time
                logger.warning(
                    f"Circuit '{self.name}' transitioned from HALF_OPEN to OPEN after a failure"
                )

    def _clean_call_history(self, current_time: float) -> None:
        """
        Clean up old calls from the history.

        Args:
            current_time: Current time in seconds
        """
        # Keep only calls within the window
        window_start = current_time - self.config.window_size
        self._call_history = [
            (ts, success) for ts, success in self._call_history if ts >= window_start
        ]

    @property
    def state(self) -> CircuitState:
        """Get the current state of the circuit."""
        return self._state

    @property
    def failure_count(self) -> int:
        """Get the current failure count."""
        return self._failure_count

    @property
    def failure_rate(self) -> float:
        """Get the failure rate over the window."""
        if not self._call_history:
            return 0.0

        failures = sum(1 for _, success in self._call_history if not success)
        return failures / len(self._call_history)

    def reset(self) -> None:
        """Reset the circuit breaker to CLOSED state."""
        with asyncio.locks.Lock():
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._half_open_calls = 0
            self._call_history.clear()
            self._last_state_change_time = time.time()
            logger.info(f"Circuit '{self.name}' was manually reset to CLOSED")


class CircuitOpenError(MigrationError):
    """
    Error raised when a circuit is open.

    This error indicates that the circuit breaker is preventing
    further calls due to previous failures.
    """

    def __init__(
        self,
        message: str,
        state: CircuitState = CircuitState.OPEN,
        will_reset_at: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a circuit open error.

        Args:
            message: The error message
            state: Current circuit breaker state
            will_reset_at: Time when the circuit will attempt to reset
            details: Additional error details
        """
        details = details or {}
        details["circuit_state"] = state.name
        if will_reset_at:
            details["will_reset_at"] = will_reset_at
            details["seconds_remaining"] = max(0, will_reset_at - time.time())

        super().__init__(message, details=details)


class CircuitBreakerRegistry:
    """
    Registry of circuit breakers.

    This class provides a central registry for circuit breakers,
    allowing them to be looked up by name.
    """

    _registry: Dict[str, CircuitBreaker] = {}
    _lock = asyncio.Lock()

    @classmethod
    async def register(
        cls, name: str, config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """
        Register a circuit breaker.

        Args:
            name: Name of the circuit breaker
            config: Circuit breaker configuration

        Returns:
            The registered circuit breaker
        """
        async with cls._lock:
            if name in cls._registry:
                return cls._registry[name]

            circuit = CircuitBreaker(name, config)
            cls._registry[name] = circuit
            return circuit

    @classmethod
    def get(cls, name: str) -> Optional[CircuitBreaker]:
        """
        Get a circuit breaker by name.

        Args:
            name: Name of the circuit breaker

        Returns:
            The circuit breaker or None if not found
        """
        return cls._registry.get(name)

    @classmethod
    async def reset_all(cls) -> None:
        """Reset all registered circuit breakers."""
        async with cls._lock:
            for circuit in cls._registry.values():
                circuit.reset()

    @classmethod
    async def reset(cls, name: str) -> None:
        """
        Reset a specific circuit breaker.

        Args:
            name: Name of the circuit breaker
        """
        async with cls._lock:
            if name in cls._registry:
                cls._registry[name].reset()


def with_circuit_breaker(
    circuit_name: str, config: Optional[CircuitBreakerConfig] = None
):
    """
    Decorator that applies circuit breaking to a function.

    This decorator wraps a function with circuit breaker logic.
    If the circuit is open, the function will not be called.

    Args:
        circuit_name: Name of the circuit breaker
        config: Circuit breaker configuration

    Returns:
        Decorated function
    """

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get or create the circuit breaker
            circuit = await CircuitBreakerRegistry.register(circuit_name, config)

            # Execute with the circuit breaker
            return await circuit.execute(func, *args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For synchronous functions, we need to use the event loop
            loop = asyncio.get_event_loop()

            # Get or create the circuit breaker
            circuit_future = loop.create_task(
                CircuitBreakerRegistry.register(circuit_name, config)
            )
            circuit = loop.run_until_complete(circuit_future)

            # Execute with the circuit breaker
            return loop.run_until_complete(circuit.execute_sync(func, *args, **kwargs))

        # Return the appropriate wrapper based on the function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class RetryConfig:
    """
    Configuration for retry logic.

    This class defines the configuration for retry behavior,
    including backoff strategy and limits.
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Optional[List[type]] = None,
    ):
        """
        Initialize retry configuration.

        Args:
            max_retries: Maximum number of retries
            base_delay: Base delay in seconds for exponential backoff
            max_delay: Maximum delay in seconds
            backoff_factor: Factor for exponential backoff
            jitter: Whether to add jitter to the delay
            retryable_exceptions: List of exceptions that are retryable
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter

        if retryable_exceptions is None:
            # Default retryable exceptions are transient errors
            self.retryable_exceptions = [
                ConnectionError,
                TimeoutError,
                ResourceExhaustedError,
            ]
        else:
            self.retryable_exceptions = retryable_exceptions

    def calculate_delay(self, retry_count: int) -> float:
        """
        Calculate the delay for a retry.

        Args:
            retry_count: Current retry count (0-based)

        Returns:
            Delay in seconds
        """
        # Exponential backoff
        delay = self.base_delay * (self.backoff_factor**retry_count)

        # Limit to max delay
        delay = min(delay, self.max_delay)

        # Add jitter if configured
        if self.jitter:
            jitter_amount = random.uniform(0, 0.25 * delay)
            delay = delay + jitter_amount

        return delay

    def should_retry(self, exception: Exception) -> bool:
        """
        Check if an exception is retryable.

        Args:
            exception: The exception to check

        Returns:
            True if the exception is retryable, False otherwise
        """
        return any(isinstance(exception, exc) for exc in self.retryable_exceptions)


def with_retry(config: Optional[RetryConfig] = None):
    """
    Decorator that applies retry logic to a function.

    This decorator wraps a function with retry logic. If the function
    raises a retryable exception, it will be retried with backoff.

    Args:
        config: Retry configuration

    Returns:
        Decorated function
    """
    config = config or RetryConfig()

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None

            for retry in range(config.max_retries + 1):
                try:
                    if retry > 0:
                        # Calculate backoff delay
                        delay = config.calculate_delay(retry - 1)

                        # Log retry attempt
                        logger.info(
                            f"Retrying {func.__name__} (attempt {retry}/{config.max_retries}) "
                            f"after {delay:.2f}s delay"
                        )

                        # Wait for the backoff delay
                        await asyncio.sleep(delay)

                    # Call the function
                    return await func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    # Check if we should retry
                    if not config.should_retry(e) or retry >= config.max_retries:
                        # Don't retry, just re-raise
                        raise

                    # Log the exception (will retry)
                    logger.warning(
                        f"Exception in {func.__name__} (will retry): {e}", exc_info=True
                    )

            # This should not happen if the code is correct
            assert last_exception is not None
            raise last_exception

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None

            for retry in range(config.max_retries + 1):
                try:
                    if retry > 0:
                        # Calculate backoff delay
                        delay = config.calculate_delay(retry - 1)

                        # Log retry attempt
                        logger.info(
                            f"Retrying {func.__name__} (attempt {retry}/{config.max_retries}) "
                            f"after {delay:.2f}s delay"
                        )

                        # Wait for the backoff delay
                        time.sleep(delay)

                    # Call the function
                    return func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    # Check if we should retry
                    if not config.should_retry(e) or retry >= config.max_retries:
                        # Don't retry, just re-raise
                        raise

                    # Log the exception (will retry)
                    logger.warning(
                        f"Exception in {func.__name__} (will retry): {e}", exc_info=True
                    )

            # This should not happen if the code is correct
            assert last_exception is not None
            raise last_exception

        # Return the appropriate wrapper based on the function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def with_timeout(timeout: float):
    """
    Decorator that applies a timeout to a function.

    This decorator wraps a function with timeout logic. If the function
    takes longer than the specified timeout, it will be cancelled.

    Args:
        timeout: Timeout in seconds

    Returns:
        Decorated function
    """

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                # Execute the function with a timeout
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            except asyncio.TimeoutError:
                # Convert to our TimeoutError
                raise TimeoutError(
                    f"Function {func.__name__} timed out after {timeout} seconds",
                    operation=func.__name__,
                    details={"timeout": timeout},
                )

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For synchronous functions, we can't use asyncio.wait_for
            # We'll have to rely on the function implementing its own timeout
            # In a real implementation, we might use threading to implement timeouts
            logger.warning(
                f"Timeout decorator not supported for sync function {func.__name__}"
            )
            return func

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
