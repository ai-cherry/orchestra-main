"""
Circuit Breaker Implementation for LLM Providers
------------------------------------------------

This module implements the circuit breaker pattern to prevent cascading failures
when using multiple LLM providers. It tracks failures per provider and temporarily
disables providers that exceed a certain failure threshold, allowing the system
to gracefully degrade and recover.

Key features:
- Per-provider failure tracking
- Automatic circuit opening after threshold of failures
- Self-healing with automatic reset after cooldown period
- Prometheus metrics integration
- Support for retry policies with exponential backoff

Usage:
    from core.orchestrator.src.services.llm.circuit_breaker import CircuitBreaker, ProviderCircuitOpenError

    # Create a circuit breaker
    breaker = CircuitBreaker(max_failures=3, reset_timeout=60)

    # Use with a provider
    try:
        result = await breaker.call_provider("openai", some_async_function, arg1, arg2)
    except ProviderCircuitOpenError:
        # Handle provider being unavailable
        result = await fallback_provider()
"""

import asyncio
import logging
import threading
import time
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar, Union

# Import tenacity for retry logic
try:
    from tenacity import (
        RetryError,
        retry,
        retry_if_exception_type,
        stop_after_attempt,
        wait_exponential,
    )

    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False

# Import prometheus for metrics
try:
    import prometheus_client as prom

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Type for function that can be called
T = TypeVar("T")
SyncOrAsyncCallable = Callable[..., Union[T, Awaitable[T]]]
SyncOrAsyncResult = Union[T, Awaitable[T]]


class CircuitState(Enum):
    """Possible states for a circuit breaker."""

    CLOSED = "closed"  # Normal operation, requests go through
    OPEN = "open"  # Circuit is open, requests are blocked
    HALF_OPEN = "half_open"  # Testing if service is healthy again


class ProviderCircuitOpenError(Exception):
    """Exception raised when a provider circuit is open."""

    def __init__(self, provider: str):
        self.provider = provider
        message = f"Circuit for provider '{provider}' is open due to too many failures"
        super().__init__(message)


class CircuitBreaker:
    """
    Implements the circuit breaker pattern for LLM service providers.

    Tracks failures per provider and temporarily disables providers
    that exceed a threshold of failures.
    """

    def __init__(
        self,
        max_failures: int = 5,
        reset_timeout: int = 60,
        half_open_max_calls: int = 1,
    ):
        """
        Initialize the CircuitBreaker.

        Args:
            max_failures: Number of failures before opening the circuit
            reset_timeout: Seconds to wait before trying the provider again
            half_open_max_calls: Number of test calls allowed in half-open state
        """
        self.max_failures = max_failures
        self.reset_timeout = reset_timeout
        self.half_open_max_calls = half_open_max_calls

        # State tracking
        self.failures: Dict[str, int] = {}
        self.circuit_state: Dict[str, CircuitState] = {}
        self.last_failure_time: Dict[str, float] = {}
        self.half_open_calls: Dict[str, int] = {}

        # Thread safety
        self._lock = threading.RLock()

        # Initialize metrics if prometheus is available
        if PROMETHEUS_AVAILABLE:
            self.failure_counter = prom.Counter(
                "llm_provider_failures_total",
                "Number of failures per provider",
                ["provider"],
            )
            self.circuit_state_gauge = prom.Gauge(
                "llm_provider_circuit_state",
                "Circuit state per provider (0=closed, 1=half-open, 2=open)",
                ["provider"],
            )
            self.request_latency = prom.Histogram(
                "llm_provider_request_seconds",
                "Request latency in seconds per provider",
                ["provider"],
            )
        else:
            logger.warning("Prometheus client not available - metrics disabled")
            logger.warning("Install with: pip install prometheus-client")

    def _get_circuit_state(self, provider: str) -> CircuitState:
        """Get the current circuit state for a provider."""
        with self._lock:
            if provider not in self.circuit_state:
                self.circuit_state[provider] = CircuitState.CLOSED

            # Check if we should transition from OPEN to HALF_OPEN
            if (
                self.circuit_state[provider] == CircuitState.OPEN
                and provider in self.last_failure_time
                and time.time() - self.last_failure_time[provider] > self.reset_timeout
            ):
                logger.info(
                    f"Circuit for {provider} transitioning from OPEN to HALF_OPEN"
                )
                self.circuit_state[provider] = CircuitState.HALF_OPEN
                self.half_open_calls[provider] = 0

                # Update prometheus metric if available
                if PROMETHEUS_AVAILABLE:
                    self.circuit_state_gauge.labels(provider=provider).set(
                        1
                    )  # 1 = half-open

            return self.circuit_state[provider]

    def record_success(self, provider: str) -> None:
        """Record a successful call to a provider."""
        with self._lock:
            # Reset failure count
            if provider in self.failures:
                del self.failures[provider]

            # If we're in HALF_OPEN and succeeded, close the circuit
            if self._get_circuit_state(provider) == CircuitState.HALF_OPEN:
                logger.info(
                    f"Circuit for {provider} transitioning from HALF_OPEN to CLOSED after success"
                )
                self.circuit_state[provider] = CircuitState.CLOSED

                # Update prometheus metric if available
                if PROMETHEUS_AVAILABLE:
                    self.circuit_state_gauge.labels(provider=provider).set(
                        0
                    )  # 0 = closed

    def record_failure(self, provider: str) -> None:
        """Record a failed call to a provider."""
        with self._lock:
            # Update prometheus metric if available
            if PROMETHEUS_AVAILABLE:
                self.failure_counter.labels(provider=provider).inc()

            # Update failure count
            self.failures[provider] = self.failures.get(provider, 0) + 1
            self.last_failure_time[provider] = time.time()

            logger.warning(
                f"Recorded failure for {provider} (count: {self.failures[provider]})"
            )

            # Check if we need to open the circuit
            if self.failures[provider] >= self.max_failures:
                current_state = self._get_circuit_state(provider)

                if current_state == CircuitState.CLOSED:
                    logger.warning(
                        f"Circuit for {provider} transitioning from CLOSED to OPEN"
                    )
                    self.circuit_state[provider] = CircuitState.OPEN

                    # Update prometheus metric if available
                    if PROMETHEUS_AVAILABLE:
                        self.circuit_state_gauge.labels(provider=provider).set(
                            2
                        )  # 2 = open

                elif current_state == CircuitState.HALF_OPEN:
                    logger.warning(
                        f"Circuit for {provider} transitioning from HALF_OPEN back to OPEN after failure"
                    )
                    self.circuit_state[provider] = CircuitState.OPEN

                    # Update prometheus metric if available
                    if PROMETHEUS_AVAILABLE:
                        self.circuit_state_gauge.labels(provider=provider).set(
                            2
                        )  # 2 = open

    def _can_make_request(self, provider: str) -> bool:
        """Check if a request can be made to the provider."""
        circuit_state = self._get_circuit_state(provider)

        if circuit_state == CircuitState.CLOSED:
            return True

        elif circuit_state == CircuitState.HALF_OPEN:
            with self._lock:
                # Only allow a limited number of test calls in half-open state
                if self.half_open_calls.get(provider, 0) < self.half_open_max_calls:
                    self.half_open_calls[provider] = (
                        self.half_open_calls.get(provider, 0) + 1
                    )
                    return True
            return False

        # Circuit is OPEN
        return False

    async def call_provider_async(
        self,
        provider: str,
        func: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """
        Call an async provider function with circuit breaker protection.

        Args:
            provider: Name of the provider (e.g., "openai", "anthropic")
            func: Async function to call
            *args, **kwargs: Arguments to pass to the function

        Returns:
            The result of the function call

        Raises:
            ProviderCircuitOpenError: If the circuit is open for this provider
            Exception: Any exception raised by the function
        """
        if not self._can_make_request(provider):
            raise ProviderCircuitOpenError(provider)

        # Use tenacity for retries if available
        if TENACITY_AVAILABLE:

            @retry(
                stop=stop_after_attempt(2),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                retry=retry_if_exception_type(Exception),
                reraise=True,
            )
            async def _wrapped_call():
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    elapsed = time.time() - start_time

                    # Record metrics
                    if PROMETHEUS_AVAILABLE:
                        self.request_latency.labels(provider=provider).observe(elapsed)

                    # Record success
                    self.record_success(provider)
                    return result
                except Exception as e:
                    elapsed = time.time() - start_time
                    logger.warning(f"Provider {provider} call failed: {str(e)}")

                    # Record metrics
                    if PROMETHEUS_AVAILABLE:
                        self.request_latency.labels(provider=provider).observe(elapsed)

                    # Record failure
                    self.record_failure(provider)
                    raise

            try:
                return await _wrapped_call()
            except RetryError:
                # All retries failed
                self.record_failure(provider)
                raise
        else:
            # Without tenacity, just make a single call
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                elapsed = time.time() - start_time

                # Record metrics
                if PROMETHEUS_AVAILABLE:
                    self.request_latency.labels(provider=provider).observe(elapsed)

                # Record success
                self.record_success(provider)
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.warning(f"Provider {provider} call failed: {str(e)}")

                # Record metrics
                if PROMETHEUS_AVAILABLE:
                    self.request_latency.labels(provider=provider).observe(elapsed)

                # Record failure
                self.record_failure(provider)
                raise

    def call_provider_sync(
        self, provider: str, func: Callable[..., T], *args: Any, **kwargs: Any
    ) -> T:
        """
        Call a synchronous provider function with circuit breaker protection.

        Args:
            provider: Name of the provider
            func: Synchronous function to call
            *args, **kwargs: Arguments to pass to the function

        Returns:
            The result of the function call

        Raises:
            ProviderCircuitOpenError: If the circuit is open for this provider
            Exception: Any exception raised by the function
        """
        if not self._can_make_request(provider):
            raise ProviderCircuitOpenError(provider)

        # Use tenacity for retries if available
        if TENACITY_AVAILABLE:

            @retry(
                stop=stop_after_attempt(2),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                retry=retry_if_exception_type(Exception),
                reraise=True,
            )
            def _wrapped_call():
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    elapsed = time.time() - start_time

                    # Record metrics
                    if PROMETHEUS_AVAILABLE:
                        self.request_latency.labels(provider=provider).observe(elapsed)

                    # Record success
                    self.record_success(provider)
                    return result
                except Exception as e:
                    elapsed = time.time() - start_time
                    logger.warning(f"Provider {provider} call failed: {str(e)}")

                    # Record metrics
                    if PROMETHEUS_AVAILABLE:
                        self.request_latency.labels(provider=provider).observe(elapsed)

                    # Record failure
                    self.record_failure(provider)
                    raise

            try:
                return _wrapped_call()
            except RetryError:
                # All retries failed
                self.record_failure(provider)
                raise
        else:
            # Without tenacity, just make a single call
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time

                # Record metrics
                if PROMETHEUS_AVAILABLE:
                    self.request_latency.labels(provider=provider).observe(elapsed)

                # Record success
                self.record_success(provider)
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.warning(f"Provider {provider} call failed: {str(e)}")

                # Record metrics
                if PROMETHEUS_AVAILABLE:
                    self.request_latency.labels(provider=provider).observe(elapsed)

                # Record failure
                self.record_failure(provider)
                raise

    async def call_provider(
        self, provider: str, func: SyncOrAsyncCallable[T], *args: Any, **kwargs: Any
    ) -> T:
        """
        Call a provider function (sync or async) with circuit breaker protection.

        Args:
            provider: Name of the provider
            func: Function to call (can be sync or async)
            *args, **kwargs: Arguments to pass to the function

        Returns:
            The result of the function call

        Raises:
            ProviderCircuitOpenError: If the circuit is open for this provider
            Exception: Any exception raised by the function
        """
        # Determine if the function is async or sync
        is_async = asyncio.iscoroutinefunction(func)

        if is_async:
            # For async functions
            result = await self.call_provider_async(provider, func, *args, **kwargs)  # type: ignore
            return result
        else:
            # For sync functions
            result = self.call_provider_sync(provider, func, *args, **kwargs)  # type: ignore
            return result

    def reset(self, provider: Optional[str] = None) -> None:
        """
        Reset circuit breaker state.

        Args:
            provider: Specific provider to reset, or None to reset all
        """
        with self._lock:
            if provider:
                # Reset a specific provider
                if provider in self.failures:
                    del self.failures[provider]
                if provider in self.circuit_state:
                    self.circuit_state[provider] = CircuitState.CLOSED
                    # Update prometheus metric if available
                    if PROMETHEUS_AVAILABLE:
                        self.circuit_state_gauge.labels(provider=provider).set(
                            0
                        )  # 0 = closed
                if provider in self.last_failure_time:
                    del self.last_failure_time[provider]
                if provider in self.half_open_calls:
                    del self.half_open_calls[provider]
            else:
                # Reset all providers
                self.failures = {}
                for provider in list(self.circuit_state.keys()):
                    self.circuit_state[provider] = CircuitState.CLOSED
                    # Update prometheus metric if available
                    if PROMETHEUS_AVAILABLE:
                        self.circuit_state_gauge.labels(provider=provider).set(
                            0
                        )  # 0 = closed
                self.last_failure_time = {}
                self.half_open_calls = {}


# Singleton instance for convenience
_default_circuit_breaker = None


def get_circuit_breaker(
    max_failures: int = 5, reset_timeout: int = 60
) -> CircuitBreaker:
    """
    Get or create the default CircuitBreaker instance.

    Args:
        max_failures: Number of failures before opening the circuit
        reset_timeout: Seconds to wait before trying the provider again

    Returns:
        A CircuitBreaker instance
    """
    global _default_circuit_breaker
    if _default_circuit_breaker is None:
        _default_circuit_breaker = CircuitBreaker(
            max_failures=max_failures, reset_timeout=reset_timeout
        )
    return _default_circuit_breaker
