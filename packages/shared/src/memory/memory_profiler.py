"""
Memory Profiler for Memory Management System.

This module provides memory usage profiling and pressure monitoring
capabilities for the AI Orchestration System memory management components.
"""

import asyncio
import json
import logging
import time
import os
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

import google.cloud.profiler
from google.cloud import monitoring_v3
from google.cloud.monitoring_v3 import types
from google.protobuf import timestamp_pb2

from packages.shared.src.memory.tiered_storage import TieredStorageManager
from packages.shared.src.memory.redis_lru_cache import RedisLRUCache
from packages.shared.src.storage.exceptions import (
    StorageError,
    ConnectionError,
    OperationError,
)

# Set up logger
logger = logging.getLogger(__name__)


class MemoryProfiler:
    """
    Memory profiler for the memory management system.

    This class provides memory usage profiling, pressure monitoring,
    and alert capabilities for the AI Orchestration System's
    memory management components. It integrates with Google Cloud
    Profiler and Monitoring for visualization and alerting.
    """

    def __init__(
        self,
        project_id: str,
        service_name: str = "memory-service",
        profiling_interval: int = 60,  # Profiling interval in seconds
        alert_thresholds: Optional[Dict[str, float]] = None,
        enable_cloud_profiler: bool = True,
        enable_cloud_monitoring: bool = True,
        credentials_path: Optional[str] = None,
    ):
        """
        Initialize the memory profiler.

        Args:
            project_id: Google Cloud project ID
            service_name: Service name for Cloud Profiler
            profiling_interval: Interval in seconds between profiling runs
            alert_thresholds: Optional dict of metric names to threshold values
            enable_cloud_profiler: Whether to enable Google Cloud Profiler
            enable_cloud_monitoring: Whether to enable Google Cloud Monitoring
            credentials_path: Optional path to service account credentials
        """
        self._project_id = project_id
        self._service_name = service_name
        self._profiling_interval = profiling_interval
        self._enable_cloud_profiler = enable_cloud_profiler
        self._enable_cloud_monitoring = enable_cloud_monitoring
        self._credentials_path = credentials_path

        # Default alert thresholds
        self._alert_thresholds = alert_thresholds or {
            "memory_usage_pct": 85.0,  # Alert at 85% memory usage
            "cache_hit_rate": 40.0,  # Alert below 40% hit rate
            "cache_eviction_rate": 10.0,  # Alert above 10 evictions/s
            "tier_migration_rate": 20.0,  # Alert above 20 migrations/s
            "firestore_read_exceeded": 1.0,  # Alert if rate limit exceeded
            "firestore_write_exceeded": 1.0,  # Alert if rate limit exceeded
        }

        # Components to monitor
        self._tiered_storage: Optional[TieredStorageManager] = None
        self._redis_cache: Optional[RedisLRUCache] = None

        # Monitoring metrics
        self._metric_client = None
        self._custom_metrics = {}

        # Profiling state
        self._profiling_thread = None
        self._stop_profiling = threading.Event()
        self._last_metrics = {}

        # Initialize profiling
        if self._enable_cloud_profiler:
            self._init_cloud_profiler()

        if self._enable_cloud_monitoring:
            self._init_cloud_monitoring()

    def _init_cloud_profiler(self) -> None:
        """Initialize Google Cloud Profiler."""
        try:
            # Configure profiler
            profiler_config = {
                "service": self._service_name,
                "project_id": self._project_id,
            }

            # Add credentials if provided
            if self._credentials_path:
                profiler_config["service_account_json_file"] = self._credentials_path

            # Start the profiler
            google.cloud.profiler.start(**profiler_config)
            logger.info(f"Cloud Profiler started for service {self._service_name}")

        except Exception as e:
            logger.error(f"Failed to initialize Cloud Profiler: {e}")

    def _init_cloud_monitoring(self) -> None:
        """Initialize Google Cloud Monitoring."""
        try:
            from google.cloud import monitoring_v3

            # Create monitoring client
            self._metric_client = monitoring_v3.MetricServiceClient()

            # Create custom metric descriptors
            self._create_metric_descriptor(
                "memory_usage_pct", "Memory usage percentage", "GAUGE", "DOUBLE", "%"
            )

            self._create_metric_descriptor(
                "cache_hit_rate", "Cache hit rate", "GAUGE", "DOUBLE", "%"
            )

            self._create_metric_descriptor(
                "cache_miss_rate", "Cache miss rate", "GAUGE", "DOUBLE", "%"
            )

            self._create_metric_descriptor(
                "cache_eviction_rate",
                "Cache eviction rate",
                "GAUGE",
                "DOUBLE",
                "evictions/s",
            )

            self._create_metric_descriptor(
                "tier_migration_rate",
                "Tier migration rate",
                "GAUGE",
                "DOUBLE",
                "migrations/s",
            )

            self._create_metric_descriptor(
                "hot_tier_items_count",
                "Hot tier items count",
                "GAUGE",
                "INT64",
                "items",
            )

            self._create_metric_descriptor(
                "warm_tier_items_count",
                "Warm tier items count",
                "GAUGE",
                "INT64",
                "items",
            )

            self._create_metric_descriptor(
                "cold_tier_items_count",
                "Cold tier items count",
                "GAUGE",
                "INT64",
                "items",
            )

            logger.info(f"Cloud Monitoring initialized for project {self._project_id}")

        except Exception as e:
            logger.error(f"Failed to initialize Cloud Monitoring: {e}")
            self._metric_client = None

    def _create_metric_descriptor(
        self,
        metric_id: str,
        display_name: str,
        metric_kind: str,
        value_type: str,
        unit: str,
    ) -> None:
        """
        Create a custom metric descriptor in Cloud Monitoring.

        Args:
            metric_id: Metric identifier
            display_name: Human-readable name
            metric_kind: GAUGE, DELTA, or CUMULATIVE
            value_type: BOOL, INT64, DOUBLE, STRING, DISTRIBUTION
            unit: Unit of measure
        """
        if not self._metric_client:
            return

        # Construct the metric type
        type_str = f"custom.googleapis.com/memory/{metric_id}"

        # Check if descriptor already exists
        project_name = f"projects/{self._project_id}"
        existing = self._metric_client.list_metric_descriptors(
            name=project_name, filter=f'metric.type="{type_str}"'
        )

        if list(existing):
            # Descriptor already exists
            logger.debug(f"Metric descriptor {type_str} already exists")
            return

        # Create descriptor
        descriptor = monitoring_v3.types.MetricDescriptor()
        descriptor.type = type_str
        descriptor.display_name = display_name
        descriptor.description = f"Memory profiler metric: {display_name}"
        descriptor.metric_kind = getattr(
            monitoring_v3.types.MetricDescriptor.MetricKind, metric_kind
        )
        descriptor.value_type = getattr(
            monitoring_v3.types.MetricDescriptor.ValueType, value_type
        )
        descriptor.unit = unit

        # Add to monitoring
        self._metric_client.create_metric_descriptor(
            name=project_name, metric_descriptor=descriptor
        )

        # Store for later use
        self._custom_metrics[metric_id] = type_str
        logger.info(f"Created metric descriptor: {type_str}")

    def set_tiered_storage(self, tiered_storage: TieredStorageManager) -> None:
        """
        Set the tiered storage manager to monitor.

        Args:
            tiered_storage: The tiered storage manager instance
        """
        self._tiered_storage = tiered_storage

    def set_redis_cache(self, redis_cache: RedisLRUCache) -> None:
        """
        Set the Redis LRU cache to monitor.

        Args:
            redis_cache: The Redis LRU cache instance
        """
        self._redis_cache = redis_cache

    def start_profiling(self) -> bool:
        """
        Start the memory profiling thread.

        Returns:
            True if profiling started successfully, False otherwise
        """
        if self._profiling_thread and self._profiling_thread.is_alive():
            logger.warn("Profiling already running")
            return False

        # Reset stop event
        self._stop_profiling.clear()

        # Start profiling thread
        self._profiling_thread = threading.Thread(
            target=self._profiling_loop, daemon=True
        )
        self._profiling_thread.start()

        logger.info("Memory profiling started")
        return True

    def stop_profiling(self) -> None:
        """Stop the memory profiling thread."""
        if self._profiling_thread and self._profiling_thread.is_alive():
            self._stop_profiling.set()
            self._profiling_thread.join(timeout=5.0)
            logger.info("Memory profiling stopped")

    def _profiling_loop(self) -> None:
        """Main profiling loop that runs in a background thread."""
        while not self._stop_profiling.is_set():
            try:
                # Collect and report metrics
                self._collect_and_report_metrics()

                # Check for memory pressure
                self._check_memory_pressure()

                # Sleep for the profiling interval
                self._stop_profiling.wait(self._profiling_interval)

            except Exception as e:
                logger.error(f"Error in profiling loop: {e}")
                # Sleep briefly before retrying
                time.sleep(5)

    async def collect_metrics(self) -> Dict[str, Any]:
        """
        Collect memory metrics from all monitored components.

        Returns:
            Dictionary of collected metrics
        """
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "memory_pressure_detected": False,
            "alerts": [],
        }

        # Collect Redis cache metrics
        if self._redis_cache:
            try:
                cache_metrics = await self._redis_cache.get_memory_usage()
                metrics.update(
                    {
                        "redis_memory_usage_mb": cache_metrics.get("used_memory_mb", 0),
                        "redis_memory_usage_pct": cache_metrics.get(
                            "memory_usage_pct", 0
                        )
                        * 100,
                        "redis_hit_count": cache_metrics.get("hit_count", 0),
                        "redis_miss_count": cache_metrics.get("miss_count", 0),
                        "redis_hit_rate": cache_metrics.get("hit_rate", 0) * 100,
                        "redis_eviction_rate": cache_metrics.get("eviction_rate", 0),
                        "redis_keys_count": cache_metrics.get("keys_count", 0),
                    }
                )
            except Exception as e:
                logger.error(f"Error collecting Redis metrics: {e}")

        # Collect tiered storage metrics
        if self._tiered_storage:
            try:
                storage_health = await self._tiered_storage.health_check()

                # Extract tiered storage metrics
                tier_health = storage_health.get("tiered_storage", {})
                tier_details = tier_health.get("details", {})

                metrics.update(
                    {
                        "tiered_storage_status": tier_health.get("status", "unknown"),
                        "hot_tier_items": tier_details.get("hot_tier_items", 0),
                        "tracked_items": tier_details.get("tracked_items", 0),
                        "last_migration": tier_details.get("last_migration", ""),
                        "has_redis": tier_details.get("redis_connected", False),
                    }
                )

                # Extract base storage metrics
                base_health = storage_health.get("base_storage", {})
                metrics.update(
                    {
                        "base_storage_status": base_health.get("status", "unknown"),
                        "base_storage_items": base_health.get("item_count", 0),
                    }
                )

            except Exception as e:
                logger.error(f"Error collecting tiered storage metrics: {e}")

        # Get system memory info if on Linux
        try:
            if os.path.exists("/proc/meminfo"):
                with open("/proc/meminfo", "r") as f:
                    meminfo = f.read()

                # Parse key memory stats
                mem_total = 0
                mem_free = 0
                mem_available = 0

                for line in meminfo.splitlines():
                    if line.startswith("MemTotal:"):
                        mem_total = int(line.split()[1])
                    elif line.startswith("MemFree:"):
                        mem_free = int(line.split()[1])
                    elif line.startswith("MemAvailable:"):
                        mem_available = int(line.split()[1])

                # Convert to MB and calculate usage
                mem_total_mb = mem_total / 1024
                mem_free_mb = mem_free / 1024
                mem_available_mb = mem_available / 1024
                mem_used_mb = mem_total_mb - mem_available_mb
                mem_usage_pct = (
                    (mem_used_mb / mem_total_mb) * 100 if mem_total_mb > 0 else 0
                )

                metrics.update(
                    {
                        "system_mem_total_mb": mem_total_mb,
                        "system_mem_free_mb": mem_free_mb,
                        "system_mem_available_mb": mem_available_mb,
                        "system_mem_used_mb": mem_used_mb,
                        "system_mem_usage_pct": mem_usage_pct,
                    }
                )
        except Exception as e:
            logger.error(f"Error collecting system memory metrics: {e}")

        # Store the metrics
        self._last_metrics = metrics

        return metrics

    def _check_memory_pressure(self) -> bool:
        """
        Check for memory pressure conditions based on collected metrics.

        Returns:
            True if memory pressure detected, False otherwise
        """
        if not self._last_metrics:
            return False

        pressure_detected = False
        alerts = []

        # Check Redis memory usage
        if "redis_memory_usage_pct" in self._last_metrics:
            usage_pct = self._last_metrics["redis_memory_usage_pct"]
            threshold = self._alert_thresholds.get("memory_usage_pct", 85.0)

            if usage_pct > threshold:
                pressure_detected = True
                alert = (
                    f"Redis memory usage at {usage_pct:.1f}% (threshold: {threshold}%)"
                )
                alerts.append(alert)
                logger.warning(alert)

        # Check cache hit rate
        if "redis_hit_rate" in self._last_metrics:
            hit_rate = self._last_metrics["redis_hit_rate"]
            threshold = self._alert_thresholds.get("cache_hit_rate", 40.0)

            if hit_rate < threshold:
                pressure_detected = True
                alert = f"Cache hit rate at {hit_rate:.1f}% (threshold: {threshold}%)"
                alerts.append(alert)
                logger.warning(alert)

        # Check eviction rate
        if "redis_eviction_rate" in self._last_metrics:
            eviction_rate = self._last_metrics["redis_eviction_rate"]
            threshold = self._alert_thresholds.get("cache_eviction_rate", 10.0)

            if eviction_rate > threshold:
                pressure_detected = True
                alert = f"Cache eviction rate at {eviction_rate:.1f}/s (threshold: {threshold}/s)"
                alerts.append(alert)
                logger.warning(alert)

        # Check system memory usage
        if "system_mem_usage_pct" in self._last_metrics:
            usage_pct = self._last_metrics["system_mem_usage_pct"]
            threshold = self._alert_thresholds.get("system_memory_usage_pct", 90.0)

            if usage_pct > threshold:
                pressure_detected = True
                alert = (
                    f"System memory usage at {usage_pct:.1f}% (threshold: {threshold}%)"
                )
                alerts.append(alert)
                logger.warning(alert)

        # Update metrics with pressure status and alerts
        self._last_metrics["memory_pressure_detected"] = pressure_detected
        self._last_metrics["alerts"] = alerts

        # If pressure detected, log it
        if pressure_detected:
            logger.warning(f"Memory pressure detected: {alerts}")

        return pressure_detected

    def _collect_and_report_metrics(self) -> None:
        """Collect metrics and report them to monitoring services."""
        # Create an event loop for async calls
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Collect metrics
            metrics = loop.run_until_complete(self.collect_metrics())

            # Report to Cloud Monitoring
            if self._enable_cloud_monitoring and self._metric_client:
                self._report_to_cloud_monitoring(metrics)

        finally:
            loop.close()

    def _report_to_cloud_monitoring(self, metrics: Dict[str, Any]) -> None:
        """
        Report metrics to Google Cloud Monitoring.

        Args:
            metrics: Dictionary of collected metrics
        """
        if not self._metric_client:
            return

        # Create time series data
        series = []

        # Current time
        now = time.time()
        seconds = int(now)
        nanos = int((now - seconds) * 10**9)

        timestamp = timestamp_pb2.Timestamp(seconds=seconds, nanos=nanos)

        # Map metrics to custom metrics
        metric_mappings = {
            "redis_memory_usage_pct": "memory_usage_pct",
            "redis_hit_rate": "cache_hit_rate",
            "redis_eviction_rate": "cache_eviction_rate",
            "hot_tier_items": "hot_tier_items_count",
        }

        # Create time series for each metric
        for metric_name, value in metrics.items():
            # Skip non-numeric values
            if not isinstance(value, (int, float)):
                continue

            # Map to custom metric if available
            custom_metric = metric_mappings.get(metric_name)
            if not custom_metric or custom_metric not in self._custom_metrics:
                continue

            # Create time series
            series.append(
                self._create_time_series(
                    metric_type=self._custom_metrics[custom_metric],
                    value=value,
                    timestamp=timestamp,
                )
            )

        # Write time series data in batches
        if series:
            try:
                project_name = f"projects/{self._project_id}"
                self._metric_client.create_time_series(
                    name=project_name, time_series=series
                )
                logger.debug(f"Reported {len(series)} metrics to Cloud Monitoring")
            except Exception as e:
                logger.error(f"Error reporting to Cloud Monitoring: {e}")

    def _create_time_series(
        self,
        metric_type: str,
        value: Union[int, float],
        timestamp: timestamp_pb2.Timestamp,
    ) -> types.TimeSeries:
        """
        Create a time series for Cloud Monitoring.

        Args:
            metric_type: The metric type string
            value: The metric value
            timestamp: The timestamp

        Returns:
            TimeSeries object
        """
        series = types.TimeSeries()
        series.metric.type = metric_type

        # Add labels
        series.metric.labels["service"] = self._service_name

        # Set resource
        series.resource.type = "global"

        # Create point
        point = types.Point()
        point.interval.end_time.seconds = timestamp.seconds
        point.interval.end_time.nanos = timestamp.nanos

        # Set value based on type
        if isinstance(value, int):
            point.value.int64_value = value
        else:
            point.value.double_value = value

        series.points.append(point)

        return series

    def get_latest_metrics(self) -> Dict[str, Any]:
        """
        Get the latest collected metrics.

        Returns:
            Dictionary of latest metrics
        """
        return self._last_metrics

    def is_memory_pressure_detected(self) -> bool:
        """
        Check if memory pressure is currently detected.

        Returns:
            True if memory pressure is detected, False otherwise
        """
        return self._last_metrics.get("memory_pressure_detected", False)

    def get_alerts(self) -> List[str]:
        """
        Get the current memory alerts.

        Returns:
            List of alert messages
        """
        return self._last_metrics.get("alerts", [])
