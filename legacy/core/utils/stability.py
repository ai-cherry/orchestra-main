"""
Stability and reliability utilities for AI Cherry
Focused on robust error handling and graceful degradation
"""

import asyncio
import logging
import functools
import time
from typing import Any, Callable, Optional, Type, Union, Dict, List
from datetime import datetime, timedelta
import traceback
from enum import Enum

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Retry strategy options"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIXED_DELAY = "fixed_delay"
    LINEAR_BACKOFF = "linear_backoff"


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class StabilityError(Exception):
    """Base exception for stability-related errors"""
    def __init__(self, message: str, error_type: str = "general", original_error: Optional[Exception] = None):
        super().__init__(message)
        self.error_type = error_type
        self.original_error = original_error
        self.timestamp = datetime.utcnow()


class RetryableError(StabilityError):
    """Exception that indicates operation should be retried"""
    pass


class NonRetryableError(StabilityError):
    """Exception that indicates operation should not be retried"""
    pass


def retry_with_backoff(
    max_attempts: int = 3,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,),
    non_retryable_exceptions: tuple = (NonRetryableError,)
):
    """
    Decorator for retrying operations with configurable backoff strategies
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    result = await func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(f"Operation {func.__name__} succeeded on attempt {attempt + 1}")
                    return result
                    
                except non_retryable_exceptions as e:
                    logger.error(f"Non-retryable error in {func.__name__}: {e}")
                    raise
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error(f"Operation {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise RetryableError(
                            f"Operation failed after {max_attempts} attempts",
                            error_type="max_retries_exceeded",
                            original_error=e
                        )
                    
                    # Calculate delay based on strategy
                    if strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                    elif strategy == RetryStrategy.LINEAR_BACKOFF:
                        delay = min(base_delay * (attempt + 1), max_delay)
                    else:  # FIXED_DELAY
                        delay = base_delay
                    
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay:.2f}s")
                    await asyncio.sleep(delay)
            
            # This should never be reached, but just in case
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(f"Operation {func.__name__} succeeded on attempt {attempt + 1}")
                    return result
                    
                except non_retryable_exceptions as e:
                    logger.error(f"Non-retryable error in {func.__name__}: {e}")
                    raise
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error(f"Operation {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise RetryableError(
                            f"Operation failed after {max_attempts} attempts",
                            error_type="max_retries_exceeded",
                            original_error=e
                        )
                    
                    # Calculate delay
                    if strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                    elif strategy == RetryStrategy.LINEAR_BACKOFF:
                        delay = min(base_delay * (attempt + 1), max_delay)
                    else:
                        delay = base_delay
                    
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay:.2f}s")
                    # TODO: Replace with asyncio.sleep() for async code
                    time.sleep(delay)
            
            raise last_exception
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for stability
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
    
    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    logger.info(f"Circuit breaker for {func.__name__} entering HALF_OPEN state")
                else:
                    raise StabilityError(
                        f"Circuit breaker is OPEN for {func.__name__}",
                        error_type="circuit_breaker_open"
                    )
            
            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
                
            except self.expected_exception as e:
                self._on_failure()
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    logger.info(f"Circuit breaker for {func.__name__} entering HALF_OPEN state")
                else:
                    raise StabilityError(
                        f"Circuit breaker is OPEN for {func.__name__}",
                        error_type="circuit_breaker_open"
                    )
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
                
            except self.expected_exception as e:
                self._on_failure()
                raise
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful operation"""
        self.failure_count = 0
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
            logger.info("Circuit breaker reset to CLOSED state")
    
    def _on_failure(self):
        """Handle failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


class GracefulDegradation:
    """
    Graceful degradation handler for non-critical operations
    """
    
    def __init__(self, fallback_value: Any = None, log_errors: bool = True):
        self.fallback_value = fallback_value
        self.log_errors = log_errors
    
    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if self.log_errors:
                    logger.warning(f"Graceful degradation in {func.__name__}: {e}")
                return self.fallback_value
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if self.log_errors:
                    logger.warning(f"Graceful degradation in {func.__name__}: {e}")
                return self.fallback_value
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper


class HealthChecker:
    """
    Health checking utility for system components
    """
    
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.last_results: Dict[str, Dict[str, Any]] = {}
    
    def register_check(self, name: str, check_func: Callable):
        """Register a health check function"""
        self.checks[name] = check_func
    
    async def run_check(self, name: str) -> Dict[str, Any]:
        """Run a specific health check"""
        if name not in self.checks:
            return {
                "status": "error",
                "message": f"Health check '{name}' not found",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        try:
            check_func = self.checks[name]
            start_time = time.time()
            
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()
            
            duration = time.time() - start_time
            
            check_result = {
                "status": "healthy",
                "result": result,
                "duration_ms": round(duration * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.last_results[name] = check_result
            return check_result
            
        except Exception as e:
            error_result = {
                "status": "unhealthy",
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.last_results[name] = error_result
            logger.error(f"Health check '{name}' failed: {e}")
            return error_result
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all registered health checks"""
        results = {}
        overall_healthy = True
        
        for name in self.checks:
            result = await self.run_check(name)
            results[name] = result
            if result["status"] != "healthy":
                overall_healthy = False
        
        return {
            "overall_status": "healthy" if overall_healthy else "unhealthy",
            "checks": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_last_results(self) -> Dict[str, Any]:
        """Get the last health check results"""
        return self.last_results.copy()


class ErrorCollector:
    """
    Collect and analyze errors for stability insights
    """
    
    def __init__(self, max_errors: int = 1000):
        self.max_errors = max_errors
        self.errors: List[Dict[str, Any]] = []
    
    def record_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        operation: Optional[str] = None
    ):
        """Record an error with context"""
        error_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "operation": operation,
            "context": context or {},
            "traceback": traceback.format_exc()
        }
        
        self.errors.append(error_record)
        
        # Keep only the most recent errors
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors:]
        
        logger.error(f"Error recorded: {error_record}")
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_errors = [
            e for e in self.errors
            if datetime.fromisoformat(e["timestamp"]) > cutoff_time
        ]
        
        # Count by error type
        error_counts = {}
        operation_counts = {}
        
        for error in recent_errors:
            error_type = error["error_type"]
            operation = error.get("operation", "unknown")
            
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
            operation_counts[operation] = operation_counts.get(operation, 0) + 1
        
        return {
            "total_errors": len(recent_errors),
            "error_types": error_counts,
            "operations": operation_counts,
            "time_period_hours": hours,
            "most_common_error": max(error_counts.items(), key=lambda x: x[1])[0] if error_counts else None,
            "most_problematic_operation": max(operation_counts.items(), key=lambda x: x[1])[0] if operation_counts else None
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent errors"""
        return self.errors[-limit:] if self.errors else []


# Global instances
health_checker = HealthChecker()
error_collector = ErrorCollector()


def safe_operation(
    fallback_value: Any = None,
    log_errors: bool = True,
    collect_errors: bool = True,
    operation_name: Optional[str] = None
):
    """
    Decorator that combines graceful degradation with error collection
    """
    def decorator(func: Callable) -> Callable:
        op_name = operation_name or func.__name__
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if collect_errors:
                    error_collector.record_error(
                        e,
                        context={"args": str(args), "kwargs": str(kwargs)},
                        operation=op_name
                    )
                
                if log_errors:
                    logger.warning(f"Safe operation {op_name} failed gracefully: {e}")
                
                return fallback_value
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if collect_errors:
                    error_collector.record_error(
                        e,
                        context={"args": str(args), "kwargs": str(kwargs)},
                        operation=op_name
                    )
                
                if log_errors:
                    logger.warning(f"Safe operation {op_name} failed gracefully: {e}")
                
                return fallback_value
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

