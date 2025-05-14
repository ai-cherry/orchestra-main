#!/usr/bin/env python3
"""
Enhanced Circuit Breaker Pattern for AI Orchestra

This module provides an improved implementation of the circuit breaker pattern
with metrics collection, optional persistence, and more robust error handling.
"""

import functools
import json
import logging
import os
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, TypeVar, Union, cast

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("circuit-breaker")

# Type variables
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


class CircuitState(Enum):
    """Circuit breaker state."""
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Circuit is broken, calls fail fast
    HALF_OPEN = "HALF_OPEN"  # Testing if service is back


class CircuitBreakerError(Exception):
    """Base exception for circuit breaker errors."""
    pass


class OpenCircuitError(CircuitBreakerError):
    """Error raised when circuit is open."""
    
    def __init__(self, service_name: str, until: datetime):
        """Initialize open circuit error.
        
        Args:
            service_name: Service name
            until: Time until circuit might close
        """
        self.service_name = service_name
        self.until = until
        super().__init__(f"Circuit for {service_name} is open until {until}")


class MetricsCollector:
    """Collects metrics for circuit breaker."""
    
    def __init__(self, name: str):
        """Initialize metrics collector.
        
        Args:
            name: Circuit name
        """
        self.name = name
        self.reset()
    
    def reset(self) -> None:
        """Reset metrics."""
        self.success_count = 0
        self.failure_count = 0
        self.timeout_count = 0
        self.rejection_count = 0
        self.response_times: List[float] = []
        self.last_success_time: Optional[datetime] = None
        self.last_failure_time: Optional[datetime] = None
        self.last_rejection_time: Optional[datetime] = None
    
    def record_success(self, response_time: Optional[float] = None) -> None:
        """Record successful call.
        
        Args:
            response_time: Response time in seconds
        """
        self.success_count += 1
        self.last_success_time = datetime.now()
        
        if response_time is not None:
            self.response_times.append(response_time)
            
            # Keep only the last 100 response times
            if len(self.response_times) > 100:
                self.response_times = self.response_times[-100:]
    
    def record_failure(self, is_timeout: bool = False) -> None:
        """Record failed call.
        
        Args:
            is_timeout: Whether the failure was due to timeout
        """
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if is_timeout:
            self.timeout_count += 1
    
    def record_rejection(self) -> None:
        """Record rejected call."""
        self.rejection_count += 1
        self.last_rejection_time = datetime.now()
    
    def success_rate(self) -> float:
        """Calculate success rate.
        
        Returns:
            Success rate (0.0 to 1.0)
        """
        total = self.success_count + self.failure_count
        if total == 0:
            return 1.0
        
        return self.success_count / total
    
    def avg_response_time(self) -> Optional[float]:
        """Calculate average response time.
        
        Returns:
            Average response time in seconds or None if no data
        """
        if not self.response_times:
            return None
        
        return sum(self.response_times) / len(self.response_times)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics.
        
        Returns:
            Dictionary of metrics
        """
        return {
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "timeout_count": self.timeout_count,
            "rejection_count": self.rejection_count,
            "success_rate": self.success_rate(),
            "avg_response_time": self.avg_response_time(),
            "last_success": self.last_success_time.isoformat() if self.last_success_time else None,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_rejection": self.last_rejection_time.isoformat() if self.last_rejection_time else None,
        }


class CircuitBreakerStorage:
    """Storage for circuit breaker state."""
    
    @staticmethod
    def save_state(name: str, state: Dict[str, Any], storage_dir: Optional[Path] = None) -> bool:
        """Save circuit breaker state.
        
        Args:
            name: Circuit name
            state: State to save
            storage_dir: Storage directory
            
        Returns:
            True if successful
        """
        if storage_dir is None:
            storage_dir = Path("logs/circuit_breaker")
        
        try:
            # Create directory if it doesn't exist
            storage_dir.mkdir(parents=True, exist_ok=True)
            
            # Convert datetime objects to ISO format strings
            serializable_state = {}
            for key, value in state.items():
                if isinstance(value, datetime):
                    serializable_state[key] = value.isoformat()
                else:
                    serializable_state[key] = value
            
            # Save state to file
            state_file = storage_dir / f"{name}.json"
            with open(state_file, "w") as f:
                json.dump(serializable_state, f, indent=2)
            
            return True
        except Exception as e:
            logger.warning(f"Failed to save circuit breaker state: {e}")
            return False
    
    @staticmethod
    def load_state(name: str, storage_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
        """Load circuit breaker state.
        
        Args:
            name: Circuit name
            storage_dir: Storage directory
            
        Returns:
            Loaded state or None if not found
        """
        if storage_dir is None:
            storage_dir = Path("logs/circuit_breaker")
        
        try:
            state_file = storage_dir / f"{name}.json"
            if not state_file.exists():
                return None
            
            with open(state_file, "r") as f:
                state = json.load(f)
            
            # Convert ISO format strings to datetime objects
            for key in ["last_failure_time", "last_success_time"]:
                if key in state and state[key]:
                    state[key] = datetime.fromisoformat(state[key])
            
            return state
        except Exception as e:
            logger.warning(f"Failed to load circuit breaker state: {e}")
            return None


class CircuitBreaker:
    """Enhanced circuit breaker for service calls."""
    
    # Class-level registry of circuit breakers
    _breakers: Dict[str, "CircuitBreaker"] = {}
    
    @classmethod
    def get_breaker(cls, name: str) -> "CircuitBreaker":
        """Get a circuit breaker by name.
        
        Args:
            name: Circuit breaker name
            
        Returns:
            Circuit breaker
        """
        if name not in cls._breakers:
            cls._breakers[name] = CircuitBreaker(name)
        return cls._breakers[name]
    
    @classmethod
    def reset_all(cls) -> None:
        """Reset all circuit breakers."""
        for breaker in cls._breakers.values():
            breaker.reset()
    
    @classmethod
    def get_all_metrics(cls) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all circuit breakers.
        
        Returns:
            Dictionary of circuit breaker name to metrics
        """
        return {name: breaker.get_metrics() for name, breaker in cls._breakers.items()}
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 1,
        enable_persistence: bool = False,
        storage_dir: Optional[Path] = None,
    ):
        """Initialize circuit breaker.
        
        Args:
            name: Circuit name
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before trying again
            half_open_max_calls: Max calls in half-open state
            enable_persistence: Whether to persist state to disk
            storage_dir: Directory for state persistence
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.enable_persistence = enable_persistence
        self.storage_dir = storage_dir
        
        # Initialize state
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0
        
        # Initialize metrics
        self.metrics = MetricsCollector(name)
        
        # Load state from disk if enabled
        if enable_persistence:
            self._load_state()
        
        logger.info(f"Circuit breaker '{name}' initialized")
    
    def _save_state(self) -> None:
        """Save circuit breaker state to disk."""
        if not self.enable_persistence:
            return
        
        state = {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "half_open_calls": self.half_open_calls,
        }
        
        CircuitBreakerStorage.save_state(self.name, state, self.storage_dir)
    
    def _load_state(self) -> None:
        """Load circuit breaker state from disk."""
        if not self.enable_persistence:
            return
        
        state = CircuitBreakerStorage.load_state(self.name, self.storage_dir)
        if state:
            try:
                self.state = CircuitState(state["state"])
                self.failure_count = state["failure_count"]
                self.last_failure_time = state.get("last_failure_time")
                self.half_open_calls = state.get("half_open_calls", 0)
                
                logger.info(f"Loaded circuit breaker state for '{self.name}': {self.state.value}")
            except (KeyError, ValueError) as e:
                logger.warning(f"Invalid circuit breaker state: {e}")
    
    def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
        
        # Reset metrics
        self.metrics.reset()
        
        # Save state if persistence is enabled
        if self.enable_persistence:
            self._save_state()
        
        logger.info(f"Circuit breaker '{self.name}' reset")
    
    def success(self, response_time: Optional[float] = None) -> None:
        """Record successful call.
        
        Args:
            response_time: Response time in seconds
        """
        # Record metrics
        self.metrics.record_success(response_time)
        
        # Update state
        if self.state == CircuitState.HALF_OPEN:
            logger.info(f"Circuit '{self.name}' closing after successful test")
            self.reset()
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
        
        # Save state if persistence is enabled
        if self.enable_persistence:
            self._save_state()
    
    def failure(self, is_timeout: bool = False) -> None:
        """Record failed call.
        
        Args:
            is_timeout: Whether the failure was due to timeout
        """
        # Record metrics
        self.metrics.record_failure(is_timeout)
        
        # Update state
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            logger.warning(f"Circuit '{self.name}' reopened after failed test")
            self.state = CircuitState.OPEN
        elif self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                logger.warning(
                    f"Circuit '{self.name}' opened after {self.failure_count} failures"
                )
                self.state = CircuitState.OPEN
        
        # Save state if persistence is enabled
        if self.enable_persistence:
            self._save_state()
    
    def allow_request(self) -> bool:
        """Check if request is allowed.
        
        Returns:
            True if request is allowed
        """
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            if self.last_failure_time is None:
                # No failure time recorded, allow the request
                return True
            
            recovery_time = self.last_failure_time + timedelta(seconds=self.recovery_timeout)
            if datetime.now() >= recovery_time:
                logger.info(f"Circuit '{self.name}' entering half-open state")
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                
                # Save state if persistence is enabled
                if self.enable_persistence:
                    self._save_state()
            else:
                # Request rejected
                self.metrics.record_rejection()
                return False
        
        # Half-open state
        if self.half_open_calls < self.half_open_max_calls:
            self.half_open_calls += 1
            
            # Save state if persistence is enabled
            if self.enable_persistence:
                self._save_state()
            
            return True
        
        # Too many half-open calls
        self.metrics.record_rejection()
        return False
    
    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state.
        
        Returns:
            Circuit breaker state
        """
        recovery_time = None
        if self.last_failure_time and self.state == CircuitState.OPEN:
            recovery_time = (self.last_failure_time + timedelta(seconds=self.recovery_timeout)).isoformat()
        
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "half_open_calls": self.half_open_calls,
            "half_open_max_calls": self.half_open_max_calls,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "recovery_time": recovery_time,
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics.
        
        Returns:
            Circuit breaker metrics
        """
        metrics = self.metrics.get_metrics()
        metrics.update(self.get_state())
        return metrics


class CircuitContext:
    """Context manager for circuit breaker."""
    
    def __init__(self, breaker: CircuitBreaker, details: Optional[str] = None):
        """Initialize circuit context.
        
        Args:
            breaker: Circuit breaker
            details: Optional details for logging
        """
        self.breaker = breaker
        self.details = details
        self.start_time: Optional[float] = None
    
    def __enter__(self) -> "CircuitContext":
        """Enter context manager.
        
        Returns:
            Circuit context
            
        Raises:
            OpenCircuitError: If circuit is open
        """
        if not self.breaker.allow_request():
            until = (
                self.breaker.last_failure_time + timedelta(seconds=self.breaker.recovery_timeout)
                if self.breaker.last_failure_time
                else datetime.now() + timedelta(seconds=self.breaker.recovery_timeout)
            )
            raise OpenCircuitError(self.breaker.name, until)
        
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Exit context manager.
        
        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
            
        Returns:
            True to suppress exception, False to propagate
        """
        # Calculate response time
        response_time = None
        if self.start_time is not None:
            response_time = time.time() - self.start_time
        
        if exc_type is None:
            # No exception, success
            self.breaker.success(response_time)
        else:
            # Exception, failure
            is_timeout = isinstance(exc_val, TimeoutError)
            self.breaker.failure(is_timeout)
        
        # Don't suppress the exception
        return False


def circuit_break(
    name: Optional[str] = None,
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    half_open_max_calls: int = 1,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    enable_persistence: bool = False,
    storage_dir: Optional[Path] = None,
) -> Callable[[F], F]:
    """Circuit breaker decorator.
    
    Args:
        name: Circuit breaker name
        failure_threshold: Failures before opening circuit
        recovery_timeout: Seconds before trying again
        half_open_max_calls: Max calls in half-open state
        exceptions: Exception types to catch
        enable_persistence: Whether to persist state to disk
        storage_dir: Directory for state persistence
    
    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        breaker_name = name or func.__qualname__
        circuit = CircuitBreaker.get_breaker(breaker_name)
        circuit.failure_threshold = failure_threshold
        circuit.recovery_timeout = recovery_timeout
        circuit.half_open_max_calls = half_open_max_calls
        circuit.enable_persistence = enable_persistence
        circuit.storage_dir = storage_dir
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            context = CircuitContext(circuit, details=f"Function: {func.__name__}")
            try:
                with context:
                    return func(*args, **kwargs)
            except exceptions as e:
                # Let the circuit context handle failure recording
                raise
            
        return cast(F, wrapper)
    
    return decorator


def async_circuit_break(
    name: Optional[str] = None,
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    half_open_max_calls: int = 1,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    enable_persistence: bool = False,
    storage_dir: Optional[Path] = None,
) -> Callable[[F], F]:
    """Async circuit breaker decorator.
    
    Args:
        name: Circuit breaker name
        failure_threshold: Failures before opening circuit
        recovery_timeout: Seconds before trying again
        half_open_max_calls: Max calls in half-open state
        exceptions: Exception types to catch
        enable_persistence: Whether to persist state to disk
        storage_dir: Directory for state persistence
    
    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        breaker_name = name or func.__qualname__
        circuit = CircuitBreaker.get_breaker(breaker_name)
        circuit.failure_threshold = failure_threshold
        circuit.recovery_timeout = recovery_timeout
        circuit.half_open_max_calls = half_open_max_calls
        circuit.enable_persistence = enable_persistence
        circuit.storage_dir = storage_dir
        
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            context = CircuitContext(circuit, details=f"Async function: {func.__name__}")
            try:
                with context:
                    return await func(*args, **kwargs)
            except exceptions as e:
                # Let the circuit context handle failure recording
                raise
            
        return cast(F, wrapper)
    
    return decorator


def generate_report(output_file: Optional[str] = None) -> str:
    """Generate circuit breaker report.
    
    Args:
        output_file: Output file path
        
    Returns:
        Report content
    """
    metrics = CircuitBreaker.get_all_metrics()
    
    # Build report
    report_lines = []
    report_lines.append("# Circuit Breaker Report")
    report_lines.append("")
    report_lines.append(f"Generated: {datetime.now().isoformat()}")
    report_lines.append("")
    
    if not metrics:
        report_lines.append("No circuit breakers available.")
    else:
        # Overview table
        report_lines.append("## Overview")
        report_lines.append("")
        report_lines.append("| Circuit | State | Success Rate | Failures | Avg Response Time |")
        report_lines.append("|---------|-------|--------------|----------|-------------------|")
        
        for name, metric in metrics.items():
            state = metric["state"]
            state_emoji = "🟢" if state == "CLOSED" else "🔴" if state == "OPEN" else "🟡"
            success_rate = metric.get("success_rate", 0) * 100
            failures = metric.get("failure_count", 0)
            avg_time = metric.get("avg_response_time")
            avg_time_str = f"{avg_time*1000:.1f}ms" if avg_time is not None else "N/A"
            
            report_lines.append(f"| {name} | {state_emoji} {state} | {success_rate:.1f}% | {failures} | {avg_time_str} |")
        
        report_lines.append("")
        
        # Detailed sections
        report_lines.append("## Details")
        report_lines.append("")
        
        for name, metric in metrics.items():
            report_lines.append(f"### {name}")
            report_lines.append("")
            
            report_lines.append(f"**State:** {metric['state']}")
            report_lines.append(f"**Failure Count:** {metric['failure_count']}/{metric['failure_threshold']}")
            report_lines.append(f"**Success Rate:** {metric['success_rate']*100:.1f}%")
            report_lines.append(f"**Rejection Count:** {metric['rejection_count']}")
            
            if metric.get('last_failure'):
                report_lines.append(f"**Last Failure:** {metric['last_failure']}")
            
            if metric.get('recovery_time'):
                report_lines.append(f"**Recovery Time:** {metric['recovery_time']}")
            
            avg_time = metric.get("avg_response_time")
            if avg_time is not None:
                report_lines.append(f"**Average Response Time:** {avg_time*1000:.1f}ms")
            
            report_lines.append("")
    
    # Write to file if requested
    report_content = "\n".join(report_lines)
    
    if output_file:
        try:
            with open(output_file, "w") as f:
                f.write(report_content)
            logger.info(f"Circuit breaker report saved to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save circuit breaker report: {e}")
    
    return report_content


if __name__ == "__main__":
    """CLI interface for circuit breaker."""
    import argparse
    import sys
    import random
    
    parser = argparse.ArgumentParser(description="Circuit Breaker")
    parser.add_argument("--test", action="store_true", help="Run test simulation")
    parser.add_argument("--name", default="test_circuit", help="Circuit name for test")
    parser.add_argument("--failure-rate", type=float, default=0.7, help="Failure rate for test")
    parser.add_argument("--iterations", type=int, default=20, help="Iterations for test")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between iterations")
    parser.add_argument("--threshold", type=int, default=3, help="Failure threshold")
    parser.add_argument("--timeout", type=float, default=5.0, help="Recovery timeout")
    parser.add_argument("--persistence", action="store_true", help="Enable persistence")
    parser.add_argument("--report", action="store_true", help="Generate report after test")
    parser.add_argument("--report-file", help="Report output file")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Set verbose logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run test simulation
    if args.test:
        @circuit_break(
            name=args.name,
            failure_threshold=args.threshold,
            recovery_timeout=args.timeout,
            enable_persistence=args.persistence,
        )
        def test_service() -> str:
            """Test service that randomly fails."""
            # Simulate random latency
            latency = random.uniform(0.1, 0.5)
            time.sleep(latency)
            
            # Simulate random failure
            if random.random() < args.failure_rate:
                raise ValueError("Service failed")
            
            return "Service succeeded"
        
        print(f"Running circuit breaker test with {args.iterations} iterations")
        print(f"Circuit: {args.name}")
        print(f"Failure rate: {args.failure_rate}")
        print(f"Failure threshold: {args.threshold}")
        print(f"Recovery timeout: {args.timeout}s")
        print(f"Persistence: {'enabled' if args.persistence else 'disabled'}")
        print("-" * 40)
        
        for i in range(args.iterations):
            try:
                result = test_service()
                print(f"Iteration {i+1}: Success - {result}")
            except OpenCircuitError as e:
                print(f"Iteration {i+1}: Circuit open until {e.until}")
            except ValueError:
                print(f"Iteration {i+1}: Service failed")
            
            # Wait before next iteration
            if i < args.iterations - 1:
                time.sleep(args.delay)
        
        # Get metrics
        circuit = CircuitBreaker.get_breaker(args.name)
        metrics = circuit.get_metrics()
        
        print("\nMetrics:")
        for key, value in metrics.items():
            print(f"  {key}: {value}")
    
    # Generate report
    if args.report or args.report_file:
        report = generate_report(args.report_file)
        
        if not args.report_file:
            print("\nCircuit Breaker Report:")
            print("-" * 40)
            print(report)