"""
Memory System Monitoring for AI Orchestra.

This module provides monitoring capabilities for the memory system,
integrating with Google Cloud Monitoring for real-time metrics and alerts.
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, TypeVar, cast

try:
    from google.cloud import monitoring_v3
    from google.cloud.monitoring_v3 import MetricServiceClient
    from google.cloud.monitoring_v3.types import (
        TimeSeries, Point, TypedValue, TimeInterval, Metric, MonitoredResource
    )
    from google.protobuf.timestamp_pb2 import Timestamp
    CLOUD_MONITORING_AVAILABLE = True
except ImportError:
    CLOUD_MONITORING_AVAILABLE = False

from .memory_types import MemoryHealth

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for generic functions
T = TypeVar('T')

class MemoryMonitoring:
    """
    Monitoring for the memory system.
    
    This class provides monitoring capabilities for the memory system,
    including metrics collection, health checks, and integration with
    Google Cloud Monitoring.
    """
    
    def __init__(
        self,
        project_id: str,
        enabled: bool = True,
        metric_prefix: str = "custom.googleapis.com/ai_orchestra/memory",
        resource_type: str = "generic_task",
        resource_labels: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the memory monitoring system.
        
        Args:
            project_id: Google Cloud project ID
            enabled: Whether monitoring is enabled
            metric_prefix: Prefix for custom metrics
            resource_type: Monitored resource type
            resource_labels: Labels for the monitored resource
        """
        self.project_id = project_id
        self.enabled = enabled and CLOUD_MONITORING_AVAILABLE
        self.metric_prefix = metric_prefix
        self.resource_type = resource_type
        self.resource_labels = resource_labels or {
            "project_id": project_id,
            "location": "global",
            "namespace": "memory",
            "job": "memory_system",
        }
        
        self._client = None
        if self.enabled:
            try:
                self._client = MetricServiceClient()
                logger.info("Memory monitoring initialized with Cloud Monitoring integration")
            except Exception as e:
                logger.warning(f"Failed to initialize Cloud Monitoring client: {e}")
                self.enabled = False
        
        # Performance metrics
        self._operation_timings: Dict[str, List[float]] = {}
        self._error_counts: Dict[str, int] = {}
        self._last_metrics_flush = time.time()
        self._metrics_flush_interval = 60  # Flush metrics every 60 seconds
        
    def record_operation_time(self, operation: str, duration: float) -> None:
        """
        Record the duration of an operation.
        
        Args:
            operation: Name of the operation
            duration: Duration in seconds
        """
        if not self.enabled:
            return
            
        if operation not in self._operation_timings:
            self._operation_timings[operation] = []
            
        self._operation_timings[operation].append(duration)
        self._check_flush_metrics()
        
    def record_error(self, operation: str) -> None:
        """
        Record an error for an operation.
        
        Args:
            operation: Name of the operation
        """
        if not self.enabled:
            return
            
        if operation not in self._error_counts:
            self._error_counts[operation] = 0
            
        self._error_counts[operation] += 1
        self._check_flush_metrics()
        
    def _check_flush_metrics(self) -> None:
        """Check if metrics should be flushed to Cloud Monitoring."""
        current_time = time.time()
        if current_time - self._last_metrics_flush >= self._metrics_flush_interval:
            self.flush_metrics()
            
    def flush_metrics(self) -> None:
        """Flush collected metrics to Cloud Monitoring."""
        if not self.enabled or not self._client:
            return
            
        try:
            # Process operation timings
            for operation, timings in self._operation_timings.items():
                if not timings:
                    continue
                    
                # Calculate statistics
                avg_time = sum(timings) / len(timings)
                max_time = max(timings)
                min_time = min(timings)
                p95_time = sorted(timings)[int(len(timings) * 0.95)] if len(timings) >= 20 else max_time
                
                # Create time series for average time
                self._write_metric(
                    metric_type=f"{self.metric_prefix}/operation_time",
                    metric_labels={"operation": operation, "statistic": "avg"},
                    value=avg_time
                )
                
                # Create time series for max time
                self._write_metric(
                    metric_type=f"{self.metric_prefix}/operation_time",
                    metric_labels={"operation": operation, "statistic": "max"},
                    value=max_time
                )
                
                # Create time series for min time
                self._write_metric(
                    metric_type=f"{self.metric_prefix}/operation_time",
                    metric_labels={"operation": operation, "statistic": "min"},
                    value=min_time
                )
                
                # Create time series for p95 time
                self._write_metric(
                    metric_type=f"{self.metric_prefix}/operation_time",
                    metric_labels={"operation": operation, "statistic": "p95"},
                    value=p95_time
                )
                
            # Clear operation timings
            self._operation_timings.clear()
            
            # Process error counts
            for operation, count in self._error_counts.items():
                self._write_metric(
                    metric_type=f"{self.metric_prefix}/error_count",
                    metric_labels={"operation": operation},
                    value=count
                )
                
            # Clear error counts
            self._error_counts.clear()
            
            # Update last flush time
            self._last_metrics_flush = time.time()
            
        except Exception as e:
            logger.error(f"Failed to flush metrics to Cloud Monitoring: {e}")
            
    def _write_metric(
        self,
        metric_type: str,
        metric_labels: Dict[str, str],
        value: float,
        value_type: str = "double"
    ) -> None:
        """
        Write a metric to Cloud Monitoring.
        
        Args:
            metric_type: Type of the metric
            metric_labels: Labels for the metric
            value: Value of the metric
            value_type: Type of the value (double, int64, bool)
        """
        if not self.enabled or not self._client:
            return
            
        try:
            # Create the time series
            series = TimeSeries()
            
            # Set the metric
            series.metric.type = metric_type
            for key, value_str in metric_labels.items():
                series.metric.labels[key] = value_str
                
            # Set the resource
            series.resource.type = self.resource_type
            for key, value_str in self.resource_labels.items():
                series.resource.labels[key] = value_str
                
            # Create a data point
            point = Point()
            
            # Set the time interval
            now = time.time()
            seconds = int(now)
            nanos = int((now - seconds) * 10**9)
            
            interval = TimeInterval()
            interval.end_time.seconds = seconds
            interval.end_time.nanos = nanos
            point.interval = interval
            
            # Set the value
            if value_type == "double":
                point.value.double_value = value
            elif value_type == "int64":
                point.value.int64_value = int(value)
            elif value_type == "bool":
                point.value.bool_value = bool(value)
            else:
                raise ValueError(f"Unsupported value type: {value_type}")
                
            series.points.append(point)
            
            # Write the time series
            project_name = f"projects/{self.project_id}"
            self._client.create_time_series(name=project_name, time_series=[series])
            
        except Exception as e:
            logger.error(f"Failed to write metric to Cloud Monitoring: {e}")
            
    def report_health(self, health: MemoryHealth) -> None:
        """
        Report memory system health to Cloud Monitoring.
        
        Args:
            health: Memory health information
        """
        if not self.enabled:
            return
            
        try:
            # Report status
            self._write_metric(
                metric_type=f"{self.metric_prefix}/health/status",
                metric_labels={},
                value=1.0 if health.get("status") == "healthy" else 0.0,
                value_type="double"
            )
            
            # Report connection status
            self._write_metric(
                metric_type=f"{self.metric_prefix}/health/connection",
                metric_labels={},
                value=1.0 if health.get("connection_status") == "connected" else 0.0,
                value_type="double"
            )
            
            # Report error count
            self._write_metric(
                metric_type=f"{self.metric_prefix}/health/error_count",
                metric_labels={},
                value=float(health.get("error_count", 0)),
                value_type="double"
            )
            
            # Report latency
            if "latency_ms" in health:
                self._write_metric(
                    metric_type=f"{self.metric_prefix}/health/latency_ms",
                    metric_labels={},
                    value=float(health.get("latency_ms", 0)),
                    value_type="double"
                )
                
        except Exception as e:
            logger.error(f"Failed to report health to Cloud Monitoring: {e}")
            
    def instrument(self, operation_name: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """
        Decorator to instrument an operation with timing and error tracking.
        
        Args:
            operation_name: Name of the operation
            
        Returns:
            Decorated function
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            async def async_wrapper(*args: Any, **kwargs: Any) -> T:
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    self.record_operation_time(operation_name, time.time() - start_time)
                    return result
                except Exception as e:
                    self.record_error(operation_name)
                    raise
                    
            def sync_wrapper(*args: Any, **kwargs: Any) -> T:
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    self.record_operation_time(operation_name, time.time() - start_time)
                    return result
                except Exception as e:
                    self.record_error(operation_name)
                    raise
                    
            if asyncio.iscoroutinefunction(func):
                return cast(Callable[..., T], async_wrapper)
            else:
                return cast(Callable[..., T], sync_wrapper)
                
        return decorator