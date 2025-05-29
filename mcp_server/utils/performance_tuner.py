#!/usr/bin/env python3
"""
performance_tuner.py - Performance optimization utilities for MCP Server

This module provides utilities for optimizing the performance of the MCP server,
including memory management, caching strategies, and resource utilization.
"""

import asyncio
import gc
import logging
import os
import threading
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional

import psutil

logger = logging.getLogger(__name__)


class PerformanceTuner:
    """Performance optimization manager for MCP Server."""

    def __init__(
        self,
        enable_optimizations: bool = True,
        memory_limit_mb: int = 512,
        cpu_limit: int = 1,
        cache_ttl_seconds: int = 300,
        max_concurrent_requests: int = 10,
    ):
        """Initialize the performance tuner.

        Args:
            enable_optimizations: Whether to enable performance optimizations
            memory_limit_mb: Memory limit in MB
            cpu_limit: CPU limit (number of cores)
            cache_ttl_seconds: Time-to-live for cache entries in seconds
            max_concurrent_requests: Maximum number of concurrent requests
        """
        self.enable_optimizations = enable_optimizations
        self.memory_limit_mb = memory_limit_mb
        self.cpu_limit = cpu_limit
        self.cache_ttl_seconds = cache_ttl_seconds
        self.max_concurrent_requests = max_concurrent_requests
        self.request_semaphore = asyncio.Semaphore(max_concurrent_requests)
        self.metrics: Dict[str, Any] = {
            "memory_usage": 0,
            "cpu_usage": 0,
            "request_count": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_response_time": 0,
        }
        self._start_time = time.time()
        self._total_response_time = 0

        # Apply environment-based settings
        self._apply_environment_settings()

        # Start monitoring thread if optimizations are enabled
        if self.enable_optimizations:
            self._start_monitoring()

    def _apply_environment_settings(self) -> None:
        """Apply settings from environment variables."""
        if os.environ.get("OPTIMIZE_PERFORMANCE", "").lower() == "true":
            self.enable_optimizations = True

        if "MEMORY_LIMIT" in os.environ:
            try:
                # Parse memory limit (e.g., "512M" or "1G")
                memory_limit = os.environ["MEMORY_LIMIT"]
                if memory_limit.endswith("G"):
                    self.memory_limit_mb = int(float(memory_limit[:-1]) * 1024)
                elif memory_limit.endswith("M"):
                    self.memory_limit_mb = int(memory_limit[:-1])
                else:
                    self.memory_limit_mb = int(memory_limit)
            except (ValueError, TypeError):
                logger.warning(f"Invalid MEMORY_LIMIT: {os.environ['MEMORY_LIMIT']}")

        if "CPU_LIMIT" in os.environ:
            try:
                self.cpu_limit = int(os.environ["CPU_LIMIT"])
            except (ValueError, TypeError):
                logger.warning(f"Invalid CPU_LIMIT: {os.environ['CPU_LIMIT']}")

        if "CACHE_TTL" in os.environ:
            try:
                self.cache_ttl_seconds = int(os.environ["CACHE_TTL"])
            except (ValueError, TypeError):
                logger.warning(f"Invalid CACHE_TTL: {os.environ['CACHE_TTL']}")

        if "MAX_CONCURRENT_REQUESTS" in os.environ:
            try:
                self.max_concurrent_requests = int(os.environ["MAX_CONCURRENT_REQUESTS"])
                self.request_semaphore = asyncio.Semaphore(self.max_concurrent_requests)
            except (ValueError, TypeError):
                logger.warning(f"Invalid MAX_CONCURRENT_REQUESTS: {os.environ['MAX_CONCURRENT_REQUESTS']}")

    def _start_monitoring(self) -> None:
        """Start a background thread to monitor resource usage."""

        def monitor_resources():
            while True:
                try:
                    # Update metrics
                    process = psutil.Process(os.getpid())
                    self.metrics["memory_usage"] = process.memory_info().rss / (1024 * 1024)  # MB
                    self.metrics["cpu_usage"] = process.cpu_percent() / psutil.cpu_count()

                    # Check if memory usage exceeds limit
                    if self.metrics["memory_usage"] > self.memory_limit_mb * 0.9:
                        logger.warning(
                            f"Memory usage ({self.metrics['memory_usage']:.2f} MB) approaching limit ({self.memory_limit_mb} MB)"
                        )
                        self._reduce_memory_usage()

                    time.sleep(5)  # Check every 5 seconds
                except Exception as e:
                    logger.error(f"Error in resource monitoring: {e}")
                    time.sleep(10)  # Wait longer on error

        threading.Thread(target=monitor_resources, daemon=True).start()

    def _reduce_memory_usage(self) -> None:
        """Attempt to reduce memory usage."""
        # Force garbage collection
        gc.collect()

        # Clear caches
        if hasattr(self, "_cache"):
            self._cache.clear()

        # Log memory usage after reduction attempts
        process = psutil.Process(os.getpid())
        memory_usage = process.memory_info().rss / (1024 * 1024)  # MB
        logger.info(f"Memory usage after reduction: {memory_usage:.2f} MB")

    async def limit_concurrency(self, func: Callable) -> Callable:
        """Decorator to limit concurrency of async functions."""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with self.request_semaphore:
                return await func(*args, **kwargs)

        return wrapper

    def cache_result(self, ttl: Optional[int] = None) -> Callable:
        """Decorator to cache function results with TTL."""
        if ttl is None:
            ttl = self.cache_ttl_seconds

        def decorator(func: Callable) -> Callable:
            cache = {}

            @wraps(func)
            def wrapper(*args, **kwargs):
                # Create a cache key from the function name and arguments
                key = str(func.__name__) + str(args) + str(sorted(kwargs.items()))

                # Check if the result is in the cache and not expired
                if key in cache:
                    timestamp, result = cache[key]
                    if time.time() - timestamp < ttl:
                        self.metrics["cache_hits"] += 1
                        return result

                # Call the function and cache the result
                self.metrics["cache_misses"] += 1
                result = func(*args, **kwargs)
                cache[key] = (time.time(), result)

                # Clean up expired cache entries
                for k in list(cache.keys()):
                    if time.time() - cache[k][0] > ttl:
                        del cache[k]

                return result

            return wrapper

        return decorator

    async def async_cache_result(self, ttl: Optional[int] = None) -> Callable:
        """Decorator to cache async function results with TTL."""
        if ttl is None:
            ttl = self.cache_ttl_seconds

        def decorator(func: Callable) -> Callable:
            cache = {}

            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Create a cache key from the function name and arguments
                key = str(func.__name__) + str(args) + str(sorted(kwargs.items()))

                # Check if the result is in the cache and not expired
                if key in cache:
                    timestamp, result = cache[key]
                    if time.time() - timestamp < ttl:
                        self.metrics["cache_hits"] += 1
                        return result

                # Call the function and cache the result
                self.metrics["cache_misses"] += 1
                result = await func(*args, **kwargs)
                cache[key] = (time.time(), result)

                # Clean up expired cache entries
                for k in list(cache.keys()):
                    if time.time() - cache[k][0] > ttl:
                        del cache[k]

                return result

            return wrapper

        return decorator

    def track_performance(self, func: Callable) -> Callable:
        """Decorator to track function performance."""

        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed_time = time.time() - start_time

            # Update metrics
            self.metrics["request_count"] += 1
            self._total_response_time += elapsed_time
            self.metrics["average_response_time"] = self._total_response_time / self.metrics["request_count"]

            # Log slow operations
            if elapsed_time > 1.0:
                logger.warning(f"Slow operation: {func.__name__} took {elapsed_time:.2f} seconds")

            return result

        return wrapper

    async def async_track_performance(self, func: Callable) -> Callable:
        """Decorator to track async function performance."""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            elapsed_time = time.time() - start_time

            # Update metrics
            self.metrics["request_count"] += 1
            self._total_response_time += elapsed_time
            self.metrics["average_response_time"] = self._total_response_time / self.metrics["request_count"]

            # Log slow operations
            if elapsed_time > 1.0:
                logger.warning(f"Slow operation: {func.__name__} took {elapsed_time:.2f} seconds")

            return result

        return wrapper

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        # Update memory and CPU usage
        process = psutil.Process(os.getpid())
        self.metrics["memory_usage"] = process.memory_info().rss / (1024 * 1024)  # MB
        self.metrics["cpu_usage"] = process.cpu_percent() / psutil.cpu_count()

        # Add uptime
        self.metrics["uptime_seconds"] = time.time() - self._start_time

        return self.metrics

    def optimize_batch_size(self, data_size: int, max_batch_size: int = 100) -> int:
        """Calculate optimal batch size based on current resource usage.

        Args:
            data_size: Total size of data to process
            max_batch_size: Maximum allowed batch size

        Returns:
            Optimal batch size
        """
        # Start with max batch size
        batch_size = max_batch_size

        # Reduce batch size if memory usage is high
        memory_usage_percent = self.metrics["memory_usage"] / self.memory_limit_mb
        if memory_usage_percent > 0.8:
            # Reduce batch size proportionally to memory pressure
            reduction_factor = 1 - (memory_usage_percent - 0.8) * 5  # Scale from 1.0 to 0.0
            batch_size = max(1, int(batch_size * reduction_factor))

        # Reduce batch size if CPU usage is high
        if self.metrics["cpu_usage"] > 80:
            # Reduce batch size proportionally to CPU pressure
            reduction_factor = 1 - (self.metrics["cpu_usage"] - 80) / 20  # Scale from 1.0 to 0.0
            batch_size = max(1, int(batch_size * reduction_factor))

        # Ensure batch size is not larger than data size
        batch_size = min(batch_size, data_size)

        return batch_size


# Singleton instance for global use
_default_instance: Optional[PerformanceTuner] = None


def get_performance_tuner() -> PerformanceTuner:
    """Get the default PerformanceTuner instance."""
    global _default_instance
    if _default_instance is None:
        _default_instance = PerformanceTuner()
    return _default_instance


# Convenience decorators
def cache_result(ttl: Optional[int] = None) -> Callable:
    """Decorator to cache function results with TTL."""
    return get_performance_tuner().cache_result(ttl)


async def async_cache_result(ttl: Optional[int] = None) -> Callable:
    """Decorator to cache async function results with TTL."""
    return await get_performance_tuner().async_cache_result(ttl)


def track_performance(func: Callable) -> Callable:
    """Decorator to track function performance."""
    return get_performance_tuner().track_performance(func)


async def async_track_performance(func: Callable) -> Callable:
    """Decorator to track async function performance."""
    return await get_performance_tuner().async_track_performance(func)


def limit_concurrency(func: Callable) -> Callable:
    """Decorator to limit concurrency of async functions."""
    return get_performance_tuner().limit_concurrency(func)


def get_metrics() -> Dict[str, Any]:
    """Get current performance metrics."""
    return get_performance_tuner().get_metrics()
