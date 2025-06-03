"""Performance monitoring utilities for the orchestrator."""

import asyncio
import functools
import logging
import time
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


def benchmark(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to benchmark async function execution time."""
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        start_time = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            elapsed = time.perf_counter() - start_time
            logger.info(f"{func.__name__} completed in {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"{func.__name__} failed after {elapsed:.3f}s: {str(e)}")
            raise
    return wrapper


class PerformanceMonitor:
    """Monitor performance metrics for operations."""
    
    def __init__(self):
        self.metrics = {}
        
    def record_metric(self, name: str, value: float) -> None:
        """Record a performance metric."""
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(value)
        
    def get_average(self, name: str) -> float:
        """Get average value for a metric."""
        if name not in self.metrics or not self.metrics[name]:
            return 0.0
        return sum(self.metrics[name]) / len(self.metrics[name])
        
    def clear_metrics(self) -> None:
        """Clear all metrics."""
        self.metrics.clear()