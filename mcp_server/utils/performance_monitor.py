#!/usr/bin/env python3
"""
performance_monitor.py - Performance Monitoring Utilities for MCP Server

This module provides utilities for monitoring and optimizing performance of
the MCP server components. It tracks operation timings, memory usage, and
provides recommendations for optimization.
"""

import logging
import threading
import time
from collections import defaultdict
from functools import wraps
from typing import Any, Dict, List, Optional

# Configure logging
logger = logging.getLogger("mcp-performance")


class PerformanceMonitor:
    """Performance monitoring and optimization utilities."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the performance monitor.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.start_time = time.time()
        self.operations = defaultdict(list)
        self.slow_threshold = self.config.get("slow_threshold_ms", 100)  # ms
        self.max_history = self.config.get("max_history", 1000)
        self.lock = threading.Lock()
        self.enabled = self.config.get("enabled", True)

    def record_operation(self, name: str, duration: float) -> None:
        """Record an operation's duration.

        Args:
            name: Name of the operation
            duration: Duration in seconds
        """
        if not self.enabled:
            return

        with self.lock:
            # Convert to milliseconds for easier reading
            duration_ms = duration * 1000
            self.operations[name].append(duration_ms)

            # Trim history if needed
            if len(self.operations[name]) > self.max_history:
                self.operations[name] = self.operations[name][-self.max_history :]

            # Log slow operations
            if duration_ms > self.slow_threshold:
                logger.warning(f"Slow operation detected: {name} took {duration_ms:.2f}ms")

    def monitor(self, name: Optional[str] = None):
        """Decorator to monitor function execution time.

        Args:
            name: Optional custom name for the operation
        """

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)

                start_time = time.time()
                try:
                    return func(*args, **kwargs)
                finally:
                    op_name = name or f"{func.__module__}.{func.__name__}"
                    self.record_operation(op_name, time.time() - start_time)

            return wrapper

        return decorator

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics.

        Returns:
            Dictionary of performance metrics
        """
        metrics = {"uptime_seconds": time.time() - self.start_time, "operations": {}}

        with self.lock:
            for op_name, durations in self.operations.items():
                if not durations:
                    continue

                metrics["operations"][op_name] = {
                    "count": len(durations),
                    "avg_ms": sum(durations) / len(durations),
                    "min_ms": min(durations),
                    "max_ms": max(durations),
                    "latest_ms": durations[-1],
                }

        return metrics

    def get_slow_operations(self, threshold_ms: Optional[float] = None) -> Dict[str, Any]:
        """Get operations exceeding the slow threshold.

        Args:
            threshold_ms: Optional custom threshold in milliseconds

        Returns:
            Dictionary of slow operations with stats
        """
        threshold = threshold_ms or self.slow_threshold
        result = {}

        with self.lock:
            for op_name, durations in self.operations.items():
                if not durations:
                    continue

                # Calculate percentages above threshold
                slow_count = sum(1 for d in durations if d > threshold)
                if slow_count == 0:
                    continue

                slow_percentage = (slow_count / len(durations)) * 100

                result[op_name] = {
                    "total_count": len(durations),
                    "slow_count": slow_count,
                    "slow_percentage": slow_percentage,
                    "avg_ms": sum(durations) / len(durations),
                    "max_ms": max(durations),
                }

        # Sort by slow percentage (highest first)
        return {k: v for k, v in sorted(result.items(), key=lambda x: x[1]["slow_percentage"], reverse=True)}

    def reset(self) -> None:
        """Reset all performance metrics."""
        with self.lock:
            self.start_time = time.time()
            self.operations.clear()

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Get optimization recommendations based on performance data.

        Returns:
            List of recommendation dictionaries
        """
        recommendations = []

        # Get overall metrics
        self.get_metrics()
        slow_ops = self.get_slow_operations()

        # Check for slow operations
        if slow_ops:
            recommendations.append(
                {
                    "type": "performance",
                    "severity": ("high" if any(op["slow_percentage"] > 50 for op in slow_ops.values()) else "medium"),
                    "message": f"Found {len(slow_ops)} slow operations that exceed {self.slow_threshold}ms threshold",
                    "operations": list(slow_ops.keys()),
                }
            )

        # TODO: Add more recommendations based on patterns

        return recommendations


# Global performance monitor instance
_performance_monitor = None


def get_performance_monitor(
    config: Optional[Dict[str, Any]] = None,
) -> PerformanceMonitor:
    """Get or create the global performance monitor instance.

    Args:
        config: Optional configuration

    Returns:
        PerformanceMonitor instance
    """
    global _performance_monitor

    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor(config)

    return _performance_monitor
