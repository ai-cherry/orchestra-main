"""
Telemetry integration for memory components.

This module provides telemetry integration for memory components, including
distributed tracing, metrics, and structured logging.
"""

import functools
import inspect
import logging
import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional, TypeVar, cast

from packages.shared.src.memory.config import TelemetryConfig

# Try to import OpenTelemetry
try:
    from opentelemetry import trace
    from opentelemetry.trace import Span, SpanKind, StatusCode
    from opentelemetry.metrics import get_meter

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False

    # Create dummy classes for type hints
    class Span:
        pass

    class SpanKind:
        INTERNAL = "internal"
        CLIENT = "client"
        SERVER = "server"

    class StatusCode:
        OK = "ok"
        ERROR = "error"


# Configure logging
logger = logging.getLogger(__name__)

# Type variables for function decorators
F = TypeVar("F", bound=Callable[..., Any])
T = TypeVar("T")


class MemoryTelemetry:
    """
    Telemetry integration for memory components.

    This class provides methods for distributed tracing, metrics, and structured
    logging for memory components.
    """

    def __init__(self, config: Optional[TelemetryConfig] = None):
        """
        Initialize the telemetry integration.

        Args:
            config: Telemetry configuration
        """
        self.config = config or TelemetryConfig()
        self.enabled = self.config.enabled

        # Set up logging
        log_level = getattr(logging, self.config.log_level, logging.INFO)
        self.logger = logging.getLogger("memory.telemetry")
        self.logger.setLevel(log_level)

        # Set up metrics if OpenTelemetry is available
        if OPENTELEMETRY_AVAILABLE and self.enabled:
            self.meter = get_meter("memory")

            # Create counters
            self.operation_counter = self.meter.create_counter(
                name="memory_operations",
                description="Number of memory operations",
                unit="1",
            )

            self.error_counter = self.meter.create_counter(
                name="memory_errors", description="Number of memory errors", unit="1"
            )

            # Create histograms
            self.operation_duration = self.meter.create_histogram(
                name="memory_operation_duration",
                description="Duration of memory operations",
                unit="ms",
            )

            self.logger.info("Memory telemetry initialized with OpenTelemetry")
        else:
            self.logger.info("Memory telemetry initialized without OpenTelemetry")

    def trace_operation(
        self,
        name: str,
        kind: str = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, str]] = None,
    ) -> Callable[[F], F]:
        """
        Decorator for tracing memory operations.

        Args:
            name: Name of the operation
            kind: Kind of span (internal, client, server)
            attributes: Additional attributes for the span

        Returns:
            Decorated function
        """

        def decorator(func: F) -> F:
            # Check if the function is async
            is_async = inspect.iscoroutinefunction(func)

            if is_async:

                @functools.wraps(func)
                async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                    if not self.enabled:
                        return await func(*args, **kwargs)

                    start_time = time.time()
                    span = self._start_span(name, kind, attributes)

                    try:
                        result = await func(*args, **kwargs)
                        self._record_metrics(name, time.time() - start_time, False)
                        self._end_span(span, StatusCode.OK)
                        return result
                    except Exception as e:
                        self._record_metrics(name, time.time() - start_time, True)
                        self._end_span(span, StatusCode.ERROR, str(e))
                        raise

                return cast(F, async_wrapper)
            else:

                @functools.wraps(func)
                def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                    if not self.enabled:
                        return func(*args, **kwargs)

                    start_time = time.time()
                    span = self._start_span(name, kind, attributes)

                    try:
                        result = func(*args, **kwargs)
                        self._record_metrics(name, time.time() - start_time, False)
                        self._end_span(span, StatusCode.OK)
                        return result
                    except Exception as e:
                        self._record_metrics(name, time.time() - start_time, True)
                        self._end_span(span, StatusCode.ERROR, str(e))
                        raise

                return cast(F, sync_wrapper)

        return decorator

    @contextmanager
    def trace_context(
        self,
        name: str,
        kind: str = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, str]] = None,
    ):
        """
        Context manager for tracing memory operations.

        Args:
            name: Name of the operation
            kind: Kind of span (internal, client, server)
            attributes: Additional attributes for the span

        Yields:
            Span object
        """
        if not self.enabled:
            yield None
            return

        start_time = time.time()
        span = self._start_span(name, kind, attributes)

        try:
            yield span
            self._record_metrics(name, time.time() - start_time, False)
            self._end_span(span, StatusCode.OK)
        except Exception as e:
            self._record_metrics(name, time.time() - start_time, True)
            self._end_span(span, StatusCode.ERROR, str(e))
            raise

    def _start_span(
        self, name: str, kind: str, attributes: Optional[Dict[str, str]] = None
    ) -> Optional[Span]:
        """
        Start a new span.

        Args:
            name: Name of the span
            kind: Kind of span (internal, client, server)
            attributes: Additional attributes for the span

        Returns:
            Span object or None if tracing is not available
        """
        if not OPENTELEMETRY_AVAILABLE or not self.enabled:
            return None

        tracer = trace.get_tracer("memory")
        span = tracer.start_span(name, kind=kind)

        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)

        return span

    def _end_span(
        self, span: Optional[Span], status: str, description: Optional[str] = None
    ) -> None:
        """
        End a span.

        Args:
            span: Span object
            status: Status code (ok, error)
            description: Optional description for the status
        """
        if not span:
            return

        if status == StatusCode.ERROR and description:
            span.record_exception(Exception(description))
            span.set_status(StatusCode.ERROR, description)
        else:
            span.set_status(StatusCode.OK)

        span.end()

    def _record_metrics(self, name: str, duration: float, is_error: bool) -> None:
        """
        Record metrics for an operation.

        Args:
            name: Name of the operation
            duration: Duration of the operation in seconds
            is_error: Whether the operation resulted in an error
        """
        if not OPENTELEMETRY_AVAILABLE or not self.enabled:
            return

        # Record operation count
        self.operation_counter.add(1, {"operation": name})

        # Record duration in milliseconds
        self.operation_duration.record(duration * 1000, {"operation": name})

        # Record error if applicable
        if is_error:
            self.error_counter.add(1, {"operation": name})

    def log_operation(
        self, level: int, message: str, operation: str, **kwargs: Any
    ) -> None:
        """
        Log a memory operation with structured data.

        Args:
            level: Log level
            message: Log message
            operation: Operation name
            **kwargs: Additional log data
        """
        if not self.enabled:
            return

        # Add operation to log data
        log_data = {"operation": operation, **kwargs}

        # Log with structured data
        self.logger.log(level, message, extra={"data": log_data})


# Global telemetry instance
telemetry = MemoryTelemetry()


def configure_telemetry(config: TelemetryConfig) -> None:
    """
    Configure the global telemetry instance.

    Args:
        config: Telemetry configuration
    """
    global telemetry
    telemetry = MemoryTelemetry(config)


def trace_operation(
    name: str,
    kind: str = SpanKind.INTERNAL,
    attributes: Optional[Dict[str, str]] = None,
) -> Callable[[F], F]:
    """
    Decorator for tracing memory operations.

    Args:
        name: Name of the operation
        kind: Kind of span (internal, client, server)
        attributes: Additional attributes for the span

    Returns:
        Decorated function
    """
    return telemetry.trace_operation(name, kind, attributes)


@contextmanager
def trace_context(
    name: str,
    kind: str = SpanKind.INTERNAL,
    attributes: Optional[Dict[str, str]] = None,
):
    """
    Context manager for tracing memory operations.

    Args:
        name: Name of the operation
        kind: Kind of span (internal, client, server)
        attributes: Additional attributes for the span

    Yields:
        Span object
    """
    with telemetry.trace_context(name, kind, attributes) as span:
        yield span


def log_operation(level: int, message: str, operation: str, **kwargs: Any) -> None:
    """
    Log a memory operation with structured data.

    Args:
        level: Log level
        message: Log message
        operation: Operation name
        **kwargs: Additional log data
    """
    telemetry.log_operation(level, message, operation, **kwargs)
