#!/usr/bin/env python3
"""
Circuit Breaker Pattern Implementation for AI Orchestra

This module implements the circuit breaker pattern for resilient service calls.
It's particularly useful for vector search operations and other resource-intensive
calls that might fail or time out under heavy load.
"""

import functools
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union, cast

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("circuit-breaker")

# Type variables
T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


class CircuitState(Enum):
    """Circuit breaker state."""
    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"      # Circuit is broken, calls fail fast
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


class CircuitBreaker:
    """Circuit breaker for service calls."""
    
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
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 1,
    ):
        """Initialize circuit breaker.
        
        Args:
            name: Circuit name
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before trying again
            half_open_max_calls: Max calls in half-open state
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0
        
        logger.info(f"Circuit breaker '{name}' initialized")
    
    def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
        logger.info(f"Circuit breaker '{self.name}' reset")
    
    def success(self) -> None:
        """Record successful call."""
        if self.state == CircuitState.HALF_OPEN:
            logger.info(f"Circuit '{self.name}' closing after successful test")
            self.reset()
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    def failure(self) -> None:
        """Record failed call."""
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
    
    def allow_request(self) -> bool:
        """Check if request is allowed.
        
        Returns:
            True if request is allowed
        """
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            recovery_time = self.last_failure_time + timedelta(seconds=self.recovery_timeout)
            if datetime.now() >= recovery_time:
                logger.info(f"Circuit '{self.name}' entering half-open state")
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
            else:
                return False
        
        # Half-open state
        if self.half_open_calls < self.half_open_max_calls:
            self.half_open_calls += 1
            return True
        
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
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "recovery_time": recovery_time,
        }


def circuit_break(
    name: Optional[str] = None,
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    exceptions: Tuple[type, ...] = (Exception,),
) -> Callable[[F], F]:
    """Circuit breaker decorator.
    
    Args:
        name: Circuit breaker name
        failure_threshold: Failures before opening circuit
        recovery_timeout: Seconds before trying again
        exceptions: Exception types to catch
    
    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        breaker_name = name or func.__qualname__
        circuit = CircuitBreaker.get_breaker(breaker_name)
        circuit.failure_threshold = failure_threshold
        circuit.recovery_timeout = recovery_timeout
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not circuit.allow_request():
                recovery_time = "unknown"
                if circuit.last_failure_time:
                    recovery_time = (circuit.last_failure_time + 
                                    timedelta(seconds=recovery_timeout)).isoformat()
                
                raise OpenCircuitError(breaker_name, 
                                      cast(datetime, circuit.last_failure_time) + 
                                      timedelta(seconds=recovery_timeout))
            
            try:
                result = func(*args, **kwargs)
                circuit.success()
                return result
            except exceptions as e:
                circuit.failure()
                raise
            
        return cast(F, wrapper)
    
    return decorator


def async_circuit_break(
    name: Optional[str] = None,
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    exceptions: Tuple[type, ...] = (Exception,),
) -> Callable[[F], F]:
    """Async circuit breaker decorator.
    
    Args:
        name: Circuit breaker name
        failure_threshold: Failures before opening circuit
        recovery_timeout: Seconds before trying again
        exceptions: Exception types to catch
    
    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        breaker_name = name or func.__qualname__
        circuit = CircuitBreaker.get_breaker(breaker_name)
        circuit.failure_threshold = failure_threshold
        circuit.recovery_timeout = recovery_timeout
        
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not circuit.allow_request():
                recovery_time = "unknown"
                if circuit.last_failure_time:
                    recovery_time = (circuit.last_failure_time + 
                                    timedelta(seconds=recovery_timeout)).isoformat()
                
                raise OpenCircuitError(breaker_name, 
                                      cast(datetime, circuit.last_failure_time) + 
                                      timedelta(seconds=recovery_timeout))
            
            try:
                result = await func(*args, **kwargs)
                circuit.success()
                return result
            except exceptions as e:
                circuit.failure()
                raise
            
        return cast(F, wrapper)
    
    return decorator


# Example usage 
if __name__ == "__main__":
    import random
    import sys
    
    # Set up test function
    @circuit_break(failure_threshold=3, recovery_timeout=5.0)
    def unreliable_service() -> str:
        """Test function that sometimes fails."""
        if random.random() < 0.7:  # 70% chance of failure
            raise ValueError("Service failed")
        return "Service succeeded"
    
    # Test loop
    print("Testing circuit breaker")
    print("----------------------")
    
    for i in range(10):
        try:
            result = unreliable_service()
            print(f"Call {i+1}: Success - {result}")
        except OpenCircuitError as e:
            print(f"Call {i+1}: Circuit open until {e.until}")
        except ValueError:
            print(f"Call {i+1}: Service failed")
        
        # Wait a bit
        time.sleep(1)
    
    print("\nWaiting for circuit to reset...")
    time.sleep(5)
    
    for i in range(10, 15):
        try:
            result = unreliable_service()
            print(f"Call {i+1}: Success - {result}")
        except OpenCircuitError as e:
            print(f"Call {i+1}: Circuit open until {e.until}")
        except ValueError:
            print(f"Call {i+1}: Service failed")
        
        # Wait a bit
        time.sleep(1)