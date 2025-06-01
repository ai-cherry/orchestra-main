"""Base adapter for Factory AI Droid to MCP server communication.

This module provides the abstract base class for all droid-specific adapters,
implementing common functionality like circuit breaker pattern, metrics collection,
and fallback mechanisms.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, Optional, TypeVar

from prometheus_client import Counter, Histogram, Gauge

# Type variable for generic return types
T = TypeVar("T")

# Configure logging
logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""

    pass


class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance.

    Implements the circuit breaker pattern to prevent cascading failures
    when Factory AI services are unavailable.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type[Exception] = Exception,
    ) -> None:
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to catch
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED

    async def call(
        self, func: Callable[..., T], *args: Any, **kwargs: Any
    ) -> T:
        """Execute function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from func

        Raises:
            CircuitBreakerError: If circuit is open
            Exception: If func raises an exception
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerError("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        return (
            self.last_failure_time is not None
            and datetime.now() - self.last_failure_time
            > timedelta(seconds=self.recovery_timeout)
        )

    def _on_success(self) -> None:
        """Handle successful call."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN


class FactoryMCPAdapter(ABC):
    """Base adapter for Factory AI Droid to MCP server communication.

    This abstract base class provides common functionality for all droid-specific
    adapters including request/response translation, circuit breaker pattern,
    performance monitoring, and fallback mechanisms.
    """

    # Prometheus metrics
    request_counter = Counter(
        "factory_mcp_requests_total",
        "Total number of requests",
        ["adapter", "status"],
    )
    request_duration = Histogram(
        "factory_mcp_request_duration_seconds",
        "Request duration in seconds",
        ["adapter"],
    )
    circuit_breaker_state = Gauge(
        "factory_mcp_circuit_breaker_state",
        "Circuit breaker state (0=closed, 1=open, 2=half_open)",
        ["adapter"],
    )

    def __init__(
        self,
        mcp_server: Any,
        droid_config: Dict[str, Any],
        adapter_name: str,
    ) -> None:
        """Initialize the adapter.

        Args:
            mcp_server: MCP server instance
            droid_config: Configuration for the Factory AI droid
            adapter_name: Name of this adapter for metrics
        """
        self.mcp_server = mcp_server
        self.droid_config = droid_config
        self.adapter_name = adapter_name
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=droid_config.get("failure_threshold", 5),
            recovery_timeout=droid_config.get("recovery_timeout", 60),
            expected_exception=Exception,
        )
        self.metrics = {
            "requests": 0,
            "successes": 0,
            "failures": 0,
            "total_latency": 0.0,
            "fallback_count": 0,
        }
        self._factory_client: Optional[Any] = None

    @abstractmethod
    async def translate_to_factory(
        self, mcp_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Translate MCP request to Factory AI format.

        Args:
            mcp_request: Request in MCP format

        Returns:
            Request in Factory AI format
        """
        pass

    @abstractmethod
    async def translate_to_mcp(
        self, factory_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Translate Factory AI response to MCP format.

        Args:
            factory_response: Response from Factory AI

        Returns:
            Response in MCP format
        """
        pass

    @abstractmethod
    async def _call_factory_droid(
        self, factory_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call the Factory AI droid with the translated request.

        Args:
            factory_request: Request in Factory AI format

        Returns:
            Response from Factory AI droid
        """
        pass

    async def process_request(
        self, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process request with circuit breaker and metrics.

        This is the main entry point for processing requests. It handles:
        - Request translation
        - Circuit breaker protection
        - Performance metrics
        - Fallback to direct MCP on failure

        Args:
            request: Request in MCP format

        Returns:
            Response in MCP format
        """
        start_time = datetime.now()
        self.metrics["requests"] += 1

        try:
            # Update circuit breaker state metric
            self._update_circuit_state_metric()

            # Use circuit breaker for Factory AI calls
            factory_request = await self.translate_to_factory(request)
            factory_response = await self.circuit_breaker.call(
                self._call_factory_droid, factory_request
            )
            mcp_response = await self.translate_to_mcp(factory_response)

            self.metrics["successes"] += 1
            self.request_counter.labels(
                adapter=self.adapter_name, status="success"
            ).inc()
            logger.info(
                f"Successfully processed request via Factory AI: {request.get('method', 'unknown')}"
            )
            return mcp_response

        except CircuitBreakerError:
            logger.warning(
                "Circuit breaker is open, falling back to direct MCP"
            )
            self.metrics["failures"] += 1
            self.metrics["fallback_count"] += 1
            self.request_counter.labels(
                adapter=self.adapter_name, status="circuit_open"
            ).inc()
            return await self._fallback_to_mcp(request)

        except Exception as e:
            logger.error(f"Error processing request: {e}", exc_info=True)
            self.metrics["failures"] += 1
            self.request_counter.labels(
                adapter=self.adapter_name, status="failure"
            ).inc()
            # Fallback to direct MCP server
            return await self._fallback_to_mcp(request)

        finally:
            latency = (datetime.now() - start_time).total_seconds()
            self.metrics["total_latency"] += latency
            self.request_duration.labels(adapter=self.adapter_name).observe(
                latency
            )

    async def _fallback_to_mcp(
        self, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback to direct MCP server call.

        This method is called when Factory AI is unavailable or errors occur.

        Args:
            request: Original MCP request

        Returns:
            Response from direct MCP server call
        """
        try:
            logger.info("Executing fallback to direct MCP server")
            # Call MCP server directly
            if hasattr(self.mcp_server, "handle_request"):
                return await self.mcp_server.handle_request(request)
            else:
                # Fallback for different MCP server interfaces
                method = request.get("method", "")
                params = request.get("params", {})
                result = await getattr(self.mcp_server, method)(**params)
                return {"result": result}
        except Exception as e:
            logger.error(f"Fallback to MCP also failed: {e}", exc_info=True)
            return {
                "error": {
                    "code": -32603,
                    "message": "Internal error in both Factory AI and MCP",
                    "data": str(e),
                }
            }

    def _update_circuit_state_metric(self) -> None:
        """Update Prometheus metric for circuit breaker state."""
        state_value = {
            CircuitState.CLOSED: 0,
            CircuitState.OPEN: 1,
            CircuitState.HALF_OPEN: 2,
        }
        self.circuit_breaker_state.labels(adapter=self.adapter_name).set(
            state_value[self.circuit_breaker.state]
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics.

        Returns:
            Dictionary containing current metrics
        """
        avg_latency = (
            self.metrics["total_latency"] / self.metrics["requests"]
            if self.metrics["requests"] > 0
            else 0
        )
        success_rate = (
            self.metrics["successes"] / self.metrics["requests"]
            if self.metrics["requests"] > 0
            else 0
        )

        return {
            "adapter": self.adapter_name,
            "total_requests": self.metrics["requests"],
            "successful_requests": self.metrics["successes"],
            "failed_requests": self.metrics["failures"],
            "fallback_count": self.metrics["fallback_count"],
            "average_latency_seconds": avg_latency,
            "success_rate": success_rate,
            "circuit_breaker_state": self.circuit_breaker.state.value,
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the adapter.

        Returns:
            Health status including metrics and circuit breaker state
        """
        metrics = self.get_metrics()
        is_healthy = (
            self.circuit_breaker.state != CircuitState.OPEN
            and metrics["success_rate"] > 0.5
        )

        return {
            "healthy": is_healthy,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat(),
        }