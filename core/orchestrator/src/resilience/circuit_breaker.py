"""
Circuit Breaker Pattern Implementation for Agent Orchestrator.

This module provides a circuit breaker pattern implementation that tracks agent failures,
trips circuits when thresholds are exceeded, and implements retry with exponential backoff.
"""

import logging
import random
import threading
from datetime import datetime, timedelta
from enum import Enum
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    Optional,
    TypeVar,
)

from core.orchestrator.src.exceptions import (
    AgentExecutionError,
    CircuitBreakerOpenError,
)
from core.orchestrator.src.resilience.tasks import get_task_queue_manager
from core.orchestrator.src.utils.error_handling import log_error

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for generic return type
T = TypeVar("T")


class CircuitState(Enum):
    """Circuit states for the circuit breaker."""

    CLOSED = "CLOSED"  # Normal operation - requests flow through
    OPEN = "OPEN"  # Circuit tripped - requests go to fallback
    HALF_OPEN = "HALF_OPEN"  # Testing if service is recovered


class CircuitBreaker(Generic[T]):
    """
    Circuit Breaker implementation for agent resilience.

    Tracks consecutive failures, trips circuits based on thresholds,
    and implements exponential backoff for retries.
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: int = 60,
        max_retry_timeout: int = 3600,
        name: str = "default",
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of consecutive failures before tripping circuit
            recovery_timeout: Initial timeout in seconds before attempting recovery
            max_retry_timeout: Maximum timeout in seconds for retries
            name: Name identifier for this circuit breaker
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.max_retry_timeout = max_retry_timeout

        # State tracking
        self._failure_counts: Dict[str, int] = {}
        self._circuit_state: Dict[str, CircuitState] = {}
        self._last_failure_time: Dict[str, datetime] = {}
        self._retry_timeout: Dict[str, int] = {}
        self._next_attempt_time: Dict[str, datetime] = {}

        # Use separate locks for different agents to reduce contention
        self._agent_locks: Dict[str, threading.RLock] = {}
        self._global_lock = threading.RLock()  # Only used for global operations

        # Cloud monitoring metrics client
        self._metrics_client = None

        # Task queue manager for retries
        self._task_queue_manager = get_task_queue_manager()

        logger.info(f"Circuit breaker '{name}' initialized with failure threshold: {failure_threshold}")

    def set_metrics_client(self, metrics_client: Any) -> None:
        """
        Set the metrics client for Cloud Monitoring.

        Args:
            metrics_client: Cloud Monitoring metrics client
        """
        self._metrics_client = metrics_client

    def _get_agent_lock(self, agent_id: str) -> threading.RLock:
        """
        Get the lock for a specific agent, creating it if it doesn't exist.

        Args:
            agent_id: Identifier for the agent

        Returns:
            The lock for this agent
        """
        with self._global_lock:
            if agent_id not in self._agent_locks:
                self._agent_locks[agent_id] = threading.RLock()
            return self._agent_locks[agent_id]

    def _initialize_agent_state(self, agent_id: str) -> None:
        """
        Initialize the state for a new agent.

        Args:
            agent_id: Identifier for the agent
        """
        with self._get_agent_lock(agent_id):
            if agent_id not in self._circuit_state:
                self._circuit_state[agent_id] = CircuitState.CLOSED
                self._failure_counts[agent_id] = 0
                self._retry_timeout[agent_id] = self.recovery_timeout
                logger.debug(f"Initialized circuit state for agent '{agent_id}'")

    def execute(
        self,
        agent_id: str,
        operation: Callable[[], T],
        fallback_operation: Callable[[], T],
        operation_data: Optional[Dict[str, Any]] = None,
    ) -> T:
        """
        Execute operation with circuit breaker protection.

        Args:
            agent_id: Identifier for the agent being protected
            operation: Primary operation to execute
            fallback_operation: Fallback operation if circuit is open or primary fails
            operation_data: Data for the operation to retry if it fails

        Returns:
            Result from either primary or fallback operation

        Raises:
            CircuitBreakerOpenError: If circuit is open and fallback fails
            AgentExecutionError: If both the primary and fallback operations fail
        """
        # Initialize agent state if needed
        self._initialize_agent_state(agent_id)

        # Check if circuit is open
        should_use_fallback = False
        next_retry_time = None

        with self._get_agent_lock(agent_id):
            state = self._circuit_state[agent_id]

            # If circuit is open, check if we should try recovery
            if state == CircuitState.OPEN:
                current_time = datetime.now()
                if agent_id in self._next_attempt_time and current_time >= self._next_attempt_time[agent_id]:
                    # Transition to half-open state for a recovery attempt
                    self._circuit_state[agent_id] = CircuitState.HALF_OPEN
                    logger.info(f"Circuit for agent '{agent_id}' transitioning to HALF_OPEN for recovery attempt")
                    self._report_metric(f"{agent_id}.circuit_state_change", 1, {"state": "HALF_OPEN"})
                else:
                    # Circuit is open and not ready for retry - use fallback
                    should_use_fallback = True
                    if agent_id in self._next_attempt_time:
                        next_retry_time = self._next_attempt_time[agent_id].isoformat()

        # If circuit is open, use fallback
        if should_use_fallback:
            logger.info(f"Circuit for agent '{agent_id}' is OPEN - using fallback (next retry: {next_retry_time})")
            self._report_metric(f"{agent_id}.fallback_execution", 1)

            try:
                return fallback_operation()
            except Exception as fallback_error:
                # If fallback also fails, raise a more specific error
                context = {
                    "agent_id": agent_id,
                    "circuit_state": "OPEN",
                    "next_retry_time": next_retry_time,
                }

                log_error(fallback_error, context, log_to_monitoring=True)

                raise CircuitBreakerOpenError(
                    message=f"Fallback operation failed while circuit is open for agent '{agent_id}'",
                    agent_id=agent_id,
                    next_retry_time=next_retry_time,
                    original_error=fallback_error,
                )

        # Circuit is CLOSED or HALF_OPEN - try the primary operation
        try:
            result = operation()

            # Success - update state based on current state
            with self._get_agent_lock(agent_id):
                if self._circuit_state[agent_id] == CircuitState.HALF_OPEN:
                    # Recovery successful - reset circuit
                    self._circuit_state[agent_id] = CircuitState.CLOSED
                    self._failure_counts[agent_id] = 0
                    self._retry_timeout[agent_id] = self.recovery_timeout
                    logger.info(f"Circuit for agent '{agent_id}' recovered and CLOSED")
                    self._report_metric(f"{agent_id}.circuit_state_change", 1, {"state": "CLOSED"})
                    self._report_metric(f"{agent_id}.recovery_success", 1)
                elif self._failure_counts.get(agent_id, 0) > 0:
                    # Reset any tracked failures during normal operation
                    self._failure_counts[agent_id] = 0
                    self._report_metric(f"{agent_id}.failure_count_reset", 1)

            return result

        except Exception as e:
            # Handle primary operation failure
            with self._get_agent_lock(agent_id):
                # Record the failure
                self._record_failure(agent_id, e)

                # If circuit was HALF_OPEN, this confirms service is still failing
                if self._circuit_state[agent_id] == CircuitState.HALF_OPEN:
                    self._increase_retry_timeout(agent_id)

                # Check if we need to trip the circuit
                if (
                    self._circuit_state[agent_id] == CircuitState.CLOSED
                    and self._failure_counts[agent_id] >= self.failure_threshold
                ):
                    self._trip_circuit(agent_id)

                # Schedule retry using Cloud Tasks if operation data is provided
                if operation_data:
                    retry_attempt = self._failure_counts[agent_id]
                    delay_seconds = self._retry_timeout.get(agent_id, self.recovery_timeout)

                    try:
                        task_name = self._task_queue_manager.schedule_retry(
                            agent_id=agent_id,
                            operation_data=operation_data,
                            retry_attempt=retry_attempt,
                            delay_seconds=delay_seconds,
                        )
                        if task_name:
                            logger.info(f"Scheduled retry for agent '{agent_id}' with task {task_name}")
                        else:
                            logger.warning(f"Failed to schedule retry for agent '{agent_id}'")
                    except Exception as task_error:
                        logger.error(f"Error scheduling retry for agent '{agent_id}': {task_error}")

            # Log primary operation failure
            logger.warning(
                f"Primary operation for agent '{agent_id}' failed, using fallback. "
                f"Error: {type(e).__name__}: {str(e)}"
            )
            self._report_metric(f"{agent_id}.fallback_execution", 1, {"reason": "primary_failure"})

            # Execute fallback with error handling
            try:
                return fallback_operation()
            except Exception as fallback_error:
                # Both primary and fallback failed - raise a comprehensive error
                context = {
                    "agent_id": agent_id,
                    "primary_error_type": type(e).__name__,
                    "fallback_error_type": type(fallback_error).__name__,
                }

                log_error(fallback_error, context, log_to_monitoring=True)

                # Wrap both errors in a detailed AgentExecutionError
                raise AgentExecutionError(
                    message=(
                        f"Both primary and fallback operations failed for agent '{agent_id}'. "
                        f"Primary: {type(e).__name__}: {str(e)}. "
                        f"Fallback: {type(fallback_error).__name__}: {str(fallback_error)}"
                    ),
                    agent_id=agent_id,
                    original_error=e,
                    details={"fallback_error": str(fallback_error)},
                )

    async def execute_async(
        self,
        agent_id: str,
        operation: Callable[[], Awaitable[T]],
        fallback_operation: Callable[[], Awaitable[T]],
        operation_data: Optional[Dict[str, Any]] = None,
    ) -> T:
        """
        Execute async operation with circuit breaker protection.

        Args:
            agent_id: Identifier for the agent being protected
            operation: Primary async operation to execute
            fallback_operation: Fallback async operation if circuit is open or primary fails
            operation_data: Data for the operation to retry if it fails

        Returns:
            Result from either primary or fallback operation

        Raises:
            CircuitBreakerOpenError: If circuit is open and fallback fails
            AgentExecutionError: If both the primary and fallback operations fail
        """
        # Initialize agent state if needed
        self._initialize_agent_state(agent_id)

        # Check if circuit is open
        should_use_fallback = False
        next_retry_time = None

        with self._get_agent_lock(agent_id):
            state = self._circuit_state[agent_id]

            # If circuit is open, check if we should try recovery
            if state == CircuitState.OPEN:
                current_time = datetime.now()
                if agent_id in self._next_attempt_time and current_time >= self._next_attempt_time[agent_id]:
                    # Transition to half-open state for a recovery attempt
                    self._circuit_state[agent_id] = CircuitState.HALF_OPEN
                    logger.info(f"Circuit for agent '{agent_id}' transitioning to HALF_OPEN for recovery attempt")
                    self._report_metric(f"{agent_id}.circuit_state_change", 1, {"state": "HALF_OPEN"})
                else:
                    # Circuit is open and not ready for retry - use fallback
                    should_use_fallback = True
                    if agent_id in self._next_attempt_time:
                        next_retry_time = self._next_attempt_time[agent_id].isoformat()

        # If circuit is open, use fallback
        if should_use_fallback:
            logger.info(f"Circuit for agent '{agent_id}' is OPEN - using fallback (next retry: {next_retry_time})")
            self._report_metric(f"{agent_id}.fallback_execution", 1)

            try:
                return await fallback_operation()
            except Exception as fallback_error:
                # If fallback also fails, raise a more specific error
                context = {
                    "agent_id": agent_id,
                    "circuit_state": "OPEN",
                    "next_retry_time": next_retry_time,
                }

                log_error(fallback_error, context, log_to_monitoring=True)

                raise CircuitBreakerOpenError(
                    message=f"Fallback operation failed while circuit is open for agent '{agent_id}'",
                    agent_id=agent_id,
                    next_retry_time=next_retry_time,
                    original_error=fallback_error,
                )

        # Circuit is CLOSED or HALF_OPEN - try the primary operation
        try:
            result = await operation()

            # Success - update state based on current state
            with self._get_agent_lock(agent_id):
                if self._circuit_state[agent_id] == CircuitState.HALF_OPEN:
                    # Recovery successful - reset circuit
                    self._circuit_state[agent_id] = CircuitState.CLOSED
                    self._failure_counts[agent_id] = 0
                    self._retry_timeout[agent_id] = self.recovery_timeout
                    logger.info(f"Circuit for agent '{agent_id}' recovered and CLOSED")
                    self._report_metric(f"{agent_id}.circuit_state_change", 1, {"state": "CLOSED"})
                    self._report_metric(f"{agent_id}.recovery_success", 1)
                elif self._failure_counts.get(agent_id, 0) > 0:
                    # Reset any tracked failures during normal operation
                    self._failure_counts[agent_id] = 0
                    self._report_metric(f"{agent_id}.failure_count_reset", 1)

            return result

        except Exception as e:
            # Handle primary operation failure
            with self._get_agent_lock(agent_id):
                # Record the failure
                self._record_failure(agent_id, e)

                # If circuit was HALF_OPEN, this confirms service is still failing
                if self._circuit_state[agent_id] == CircuitState.HALF_OPEN:
                    self._increase_retry_timeout(agent_id)

                # Check if we need to trip the circuit
                if (
                    self._circuit_state[agent_id] == CircuitState.CLOSED
                    and self._failure_counts[agent_id] >= self.failure_threshold
                ):
                    self._trip_circuit(agent_id)

                # Schedule retry using Cloud Tasks if operation data is provided
                if operation_data:
                    retry_attempt = self._failure_counts[agent_id]
                    delay_seconds = self._retry_timeout.get(agent_id, self.recovery_timeout)

                    try:
                        task_name = self._task_queue_manager.schedule_retry(
                            agent_id=agent_id,
                            operation_data=operation_data,
                            retry_attempt=retry_attempt,
                            delay_seconds=delay_seconds,
                        )
                        if task_name:
                            logger.info(f"Scheduled retry for agent '{agent_id}' with task {task_name}")
                        else:
                            logger.warning(f"Failed to schedule retry for agent '{agent_id}'")
                    except Exception as task_error:
                        logger.error(f"Error scheduling retry for agent '{agent_id}': {task_error}")

            # Log primary operation failure
            logger.warning(
                f"Primary operation for agent '{agent_id}' failed, using fallback. "
                f"Error: {type(e).__name__}: {str(e)}"
            )
            self._report_metric(f"{agent_id}.fallback_execution", 1, {"reason": "primary_failure"})

            # Execute fallback with error handling
            try:
                return await fallback_operation()
            except Exception as fallback_error:
                # Both primary and fallback failed - raise a comprehensive error
                context = {
                    "agent_id": agent_id,
                    "primary_error_type": type(e).__name__,
                    "fallback_error_type": type(fallback_error).__name__,
                }

                log_error(fallback_error, context, log_to_monitoring=True)

                # Wrap both errors in a detailed AgentExecutionError
                raise AgentExecutionError(
                    message=(
                        f"Both primary and fallback operations failed for agent '{agent_id}'. "
                        f"Primary: {type(e).__name__}: {str(e)}. "
                        f"Fallback: {type(fallback_error).__name__}: {str(fallback_error)}"
                    ),
                    agent_id=agent_id,
                    original_error=e,
                    details={"fallback_error": str(fallback_error)},
                )

    def _record_failure(self, agent_id: str, exception: Exception) -> None:
        """
        Record a failure for the specified agent.

        Args:
            agent_id: Identifier for the agent
            exception: The exception that occurred
        """
        self._failure_counts[agent_id] = self._failure_counts.get(agent_id, 0) + 1
        self._last_failure_time[agent_id] = datetime.now()

        # Report failure to metrics
        self._report_metric(f"{agent_id}.failure_count", self._failure_counts[agent_id])
        self._report_metric(
            f"{agent_id}.failure_occurrence",
            1,
            {"error_type": type(exception).__name__},
        )

        logger.warning(
            f"Failure #{self._failure_counts[agent_id]} recorded for agent '{agent_id}': "
            f"{type(exception).__name__}: {str(exception)}"
        )

    def _trip_circuit(self, agent_id: str) -> None:
        """
        Trip the circuit for an agent, transitioning to OPEN state.

        Args:
            agent_id: Identifier for the agent
        """
        self._circuit_state[agent_id] = CircuitState.OPEN
        next_attempt = datetime.now() + timedelta(seconds=self._retry_timeout[agent_id])
        self._next_attempt_time[agent_id] = next_attempt

        # Report to metrics
        self._report_metric(f"{agent_id}.circuit_state_change", 1, {"state": "OPEN"})
        self._report_metric(
            f"{agent_id}.circuit_trip",
            1,
            {"failure_count": self._failure_counts[agent_id]},
        )

        logger.warning(
            f"Circuit TRIPPED for agent '{agent_id}' after {self._failure_counts[agent_id]} failures. "
            f"Next retry attempt at {next_attempt.isoformat()}"
        )

    def _increase_retry_timeout(self, agent_id: str) -> None:
        """
        Increase retry timeout with exponential backoff.

        Args:
            agent_id: Identifier for the agent
        """
        # Exponential backoff with jitter
        current_timeout = self._retry_timeout[agent_id]
        new_timeout = min(current_timeout * 2, self.max_retry_timeout)

        # Add jitter (±10%)
        jitter = random.uniform(0.9, 1.1)
        new_timeout = int(new_timeout * jitter)

        self._retry_timeout[agent_id] = new_timeout
        next_attempt = datetime.now() + timedelta(seconds=new_timeout)
        self._next_attempt_time[agent_id] = next_attempt

        # Report to metrics
        self._report_metric(f"{agent_id}.retry_timeout", new_timeout)

        logger.info(
            f"Increased retry timeout for agent '{agent_id}' to {new_timeout}s. "
            f"Next attempt at {next_attempt.isoformat()}"
        )

    def _report_metric(self, metric_name: str, value: Any, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Report metric to Cloud Monitoring if metrics client is configured.

        Args:
            metric_name: Name of the metric
            value: Value to report
            labels: Optional labels/dimensions for the metric
        """
        if self._metrics_client:
            try:
                self._metrics_client.report_metric(f"agent_circuit_breaker.{metric_name}", value, labels=labels)
            except Exception as e:
                logger.error(f"Failed to report metric {metric_name}: {str(e)}")

    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """
        Get the current status of an agent's circuit.

        Args:
            agent_id: Identifier for the agent

        Returns:
            Dict containing circuit state information
        """
        with self._get_agent_lock(agent_id):
            if agent_id not in self._circuit_state:
                return {
                    "agent_id": agent_id,
                    "circuit_state": CircuitState.CLOSED.value,
                    "failure_count": 0,
                    "in_operation": False,
                }

            next_attempt = self._next_attempt_time.get(agent_id, None)

            return {
                "agent_id": agent_id,
                "circuit_state": self._circuit_state[agent_id].value,
                "failure_count": self._failure_counts.get(agent_id, 0),
                "last_failure_time": self._last_failure_time.get(agent_id, None),
                "retry_timeout": self._retry_timeout.get(agent_id, self.recovery_timeout),
                "next_attempt_time": next_attempt.isoformat() if next_attempt else None,
                "in_operation": True,
            }

    def force_reset(self, agent_id: str) -> None:
        """
        Force reset the circuit for an agent.

        Args:
            agent_id: Identifier for the agent
        """
        with self._get_agent_lock(agent_id):
            if agent_id in self._circuit_state:
                self._circuit_state[agent_id] = CircuitState.CLOSED
                self._failure_counts[agent_id] = 0
                self._retry_timeout[agent_id] = self.recovery_timeout
                if agent_id in self._next_attempt_time:
                    del self._next_attempt_time[agent_id]

                logger.info(f"Circuit for agent '{agent_id}' was force reset to CLOSED state")
                self._report_metric(f"{agent_id}.circuit_force_reset", 1)


# Global instance for singleton access
_circuit_breaker = None
_circuit_breaker_lock = threading.RLock()


def get_circuit_breaker() -> CircuitBreaker:
    """
    Get the global circuit breaker instance.

    Returns:
        The global CircuitBreaker instance
    """
    global _circuit_breaker

    with _circuit_breaker_lock:
        if _circuit_breaker is None:
            # Get settings to determine failure threshold, etc.
            # Default values can be overridden by environment variables
            import os

            failure_threshold = int(os.environ.get("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "3"))
            recovery_timeout = int(os.environ.get("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "60"))
            max_retry_timeout = int(os.environ.get("CIRCUIT_BREAKER_MAX_RETRY_TIMEOUT", "3600"))

            _circuit_breaker = CircuitBreaker(
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                max_retry_timeout=max_retry_timeout,
                name="agent_orchestrator",
            )

            logger.info(
                f"Created global circuit breaker with failure_threshold={failure_threshold}, "
                f"recovery_timeout={recovery_timeout}s, max_retry_timeout={max_retry_timeout}s"
            )

        return _circuit_breaker
