"""
Memory Metrics Collector Implementation

Comprehensive metrics collection and monitoring for the memory system,
with support for Prometheus export and real-time analytics.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
import json

try:
    from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("prometheus_client not available, metrics export will be limited")

from ..interfaces import (
    IMemoryMetrics,
    MemoryTier,
    MetricsConfig
)
from ..exceptions import MemoryMetricsError

logger = logging.getLogger(__name__)

@dataclass
class AccessMetric:
    """Represents a single access metric event."""
    timestamp: datetime
    key: str
    tier: Optional[MemoryTier]
    hit: bool
    latency_ms: float
    size_bytes: Optional[int] = None

@dataclass
class OperationMetric:
    """Represents a single operation metric event."""
    timestamp: datetime
    operation: str
    success: bool
    latency_ms: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TierMigrationMetric:
    """Represents a tier migration event."""
    timestamp: datetime
    key: str
    from_tier: MemoryTier
    to_tier: MemoryTier
    reason: str
    size_bytes: Optional[int] = None

class MetricsAggregator:
    """Aggregates metrics over time windows."""
    
    def __init__(self, window_size_seconds: int = 60):
        self.window_size = window_size_seconds
        self.access_metrics: deque = deque()
        self.operation_metrics: deque = deque()
        self.migration_metrics: deque = deque()
        
        # Aggregated stats
        self.hit_rates: Dict[str, float] = {}
        self.latency_percentiles: Dict[str, Dict[int, float]] = {}
        self.operation_counts: Dict[str, int] = defaultdict(int)
        self.error_counts: Dict[str, int] = defaultdict(int)
    
    def add_access(self, metric: AccessMetric) -> None:
        """Add an access metric."""
        self.access_metrics.append(metric)
        self._cleanup_old_metrics()
    
    def add_operation(self, metric: OperationMetric) -> None:
        """Add an operation metric."""
        self.operation_metrics.append(metric)
        self._cleanup_old_metrics()
    
    def add_migration(self, metric: TierMigrationMetric) -> None:
        """Add a migration metric."""
        self.migration_metrics.append(metric)
        self._cleanup_old_metrics()
    
    def calculate_aggregates(self) -> Dict[str, Any]:
        """Calculate aggregated statistics."""
        now = datetime.utcnow()
        
        # Hit rates by tier
        tier_hits = defaultdict(int)
        tier_total = defaultdict(int)
        
        for metric in self.access_metrics:
            if metric.tier:
                tier_total[metric.tier.value] += 1
                if metric.hit:
                    tier_hits[metric.tier.value] += 1
        
        hit_rates = {}
        for tier, total in tier_total.items():
            hit_rates[tier] = tier_hits[tier] / total if total > 0 else 0.0
        
        # Latency percentiles
        operation_latencies = defaultdict(list)
        for metric in self.operation_metrics:
            operation_latencies[metric.operation].append(metric.latency_ms)
        
        latency_percentiles = {}
        for op, latencies in operation_latencies.items():
            if latencies:
                latencies_sorted = sorted(latencies)
                latency_percentiles[op] = {
                    50: self._percentile(latencies_sorted, 50),
                    90: self._percentile(latencies_sorted, 90),
                    95: self._percentile(latencies_sorted, 95),
                    99: self._percentile(latencies_sorted, 99),
                }
        
        # Operation success rates
        operation_success = defaultdict(int)
        operation_total = defaultdict(int)
        
        for metric in self.operation_metrics:
            operation_total[metric.operation] += 1
            if metric.success:
                operation_success[metric.operation] += 1
        
        success_rates = {}
        for op, total in operation_total.items():
            success_rates[op] = operation_success[op] / total if total > 0 else 0.0
        
        # Migration patterns
        migration_patterns = defaultdict(int)
        for metric in self.migration_metrics:
            pattern = f"{metric.from_tier.value}->{metric.to_tier.value}"
            migration_patterns[pattern] += 1
        
        return {
            "window_size_seconds": self.window_size,
            "hit_rates": dict(hit_rates),
            "latency_percentiles": latency_percentiles,
            "success_rates": dict(success_rates),
            "migration_patterns": dict(migration_patterns),
            "total_accesses": len(self.access_metrics),
            "total_operations": len(self.operation_metrics),
            "total_migrations": len(self.migration_metrics),
        }
    
    def _cleanup_old_metrics(self) -> None:
        """Remove metrics older than the window size."""
        cutoff_time = datetime.utcnow() - timedelta(seconds=self.window_size)
        
        # Clean access metrics
        while self.access_metrics and self.access_metrics[0].timestamp < cutoff_time:
            self.access_metrics.popleft()
        
        # Clean operation metrics
        while self.operation_metrics and self.operation_metrics[0].timestamp < cutoff_time:
            self.operation_metrics.popleft()
        
        # Clean migration metrics
        while self.migration_metrics and self.migration_metrics[0].timestamp < cutoff_time:
            self.migration_metrics.popleft()
    
    def _percentile(self, sorted_list: List[float], percentile: int) -> float:
        """Calculate percentile from sorted list."""
        if not sorted_list:
            return 0.0
        
        index = int(len(sorted_list) * percentile / 100)
        if index >= len(sorted_list):
            index = len(sorted_list) - 1
        
        return sorted_list[index]

class MemoryMetricsCollector(IMemoryMetrics):
    """
    Production-ready metrics collection system for memory management.
    
    Features:
    - Real-time metrics collection
    - Time-window aggregation
    - Prometheus export support
    - Custom metric tracking
    - Performance monitoring
    - Alerting thresholds
    """
    
    def __init__(self, config: MetricsConfig):
        """Initialize the metrics collector."""
        self.config = config
        self.enabled = config.enabled
        
        # Aggregators for different time windows
        self.aggregators = {
            "1m": MetricsAggregator(60),
            "5m": MetricsAggregator(300),
            "15m": MetricsAggregator(900),
            "1h": MetricsAggregator(3600),
        }
        
        # Raw metrics storage (limited)
        self.recent_accesses: deque = deque(maxlen=10000)
        self.recent_operations: deque = deque(maxlen=10000)
        self.recent_migrations: deque = deque(maxlen=1000)
        
        # Counters
        self.total_accesses = 0
        self.total_hits = 0
        self.total_operations = 0
        self.total_errors = 0
        self.total_migrations = 0
        
        # Prometheus metrics (if available)
        if PROMETHEUS_AVAILABLE and config.prometheus_enabled:
            self._init_prometheus_metrics()
        else:
            self.prometheus_registry = None
        
        # Alert thresholds
        self.alert_thresholds = {
            "error_rate": 0.05,  # 5% error rate
            "latency_p99": 1000,  # 1 second
            "hit_rate": 0.8,      # 80% hit rate
        }
        
        # Active alerts
        self.active_alerts: Dict[str, datetime] = {}
        
        logger.info(f"Initialized MemoryMetricsCollector with config: {config}")
    
    def _init_prometheus_metrics(self) -> None:
        """Initialize Prometheus metrics."""
        self.prometheus_registry = CollectorRegistry()
        
        # Counters
        self.prom_access_total = Counter(
            'memory_access_total',
            'Total number of memory accesses',
            ['tier', 'hit'],
            registry=self.prometheus_registry
        )
        
        self.prom_operation_total = Counter(
            'memory_operation_total',
            'Total number of memory operations',
            ['operation', 'success'],
            registry=self.prometheus_registry
        )
        
        self.prom_migration_total = Counter(
            'memory_migration_total',
            'Total number of tier migrations',
            ['from_tier', 'to_tier', 'reason'],
            registry=self.prometheus_registry
        )
        
        # Histograms
        self.prom_latency_histogram = Histogram(
            'memory_operation_latency_ms',
            'Operation latency in milliseconds',
            ['operation'],
            buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000],
            registry=self.prometheus_registry
        )
        
        # Gauges
        self.prom_hit_rate = Gauge(
            'memory_hit_rate',
            'Current hit rate by tier',
            ['tier'],
            registry=self.prometheus_registry
        )
        
        self.prom_items_count = Gauge(
            'memory_items_count',
            'Number of items in each tier',
            ['tier'],
            registry=self.prometheus_registry
        )
    
    async def initialize(self) -> None:
        """Initialize the metrics collector."""
        logger.info("Metrics collector initialized")
    
    async def record_access(
        self,
        key: str,
        tier: Optional[MemoryTier],
        hit: bool,
        latency_ms: float,
        size_bytes: Optional[int] = None
    ) -> None:
        """Record a memory access event."""
        if not self.enabled:
            return
        
        metric = AccessMetric(
            timestamp=datetime.utcnow(),
            key=key,
            tier=tier,
            hit=hit,
            latency_ms=latency_ms,
            size_bytes=size_bytes
        )
        
        # Add to aggregators
        for aggregator in self.aggregators.values():
            aggregator.add_access(metric)
        
        # Store recent access
        self.recent_accesses.append(metric)
        
        # Update counters
        self.total_accesses += 1
        if hit:
            self.total_hits += 1
        
        # Update Prometheus metrics
        if self.prometheus_registry and tier:
            self.prom_access_total.labels(
                tier=tier.value,
                hit=str(hit)
            ).inc()
    
    async def record_operation(
        self,
        operation: str,
        success: bool,
        latency_ms: float,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record an operation event."""
        if not self.enabled:
            return
        
        metric = OperationMetric(
            timestamp=datetime.utcnow(),
            operation=operation,
            success=success,
            latency_ms=latency_ms,
            error=error,
            metadata=metadata or {}
        )
        
        # Add to aggregators
        for aggregator in self.aggregators.values():
            aggregator.add_operation(metric)
        
        # Store recent operation
        self.recent_operations.append(metric)
        
        # Update counters
        self.total_operations += 1
        if not success:
            self.total_errors += 1
        
        # Update Prometheus metrics
        if self.prometheus_registry:
            self.prom_operation_total.labels(
                operation=operation,
                success=str(success)
            ).inc()
            
            self.prom_latency_histogram.labels(
                operation=operation
            ).observe(latency_ms)
        
        # Check alerts
        await self._check_alerts(operation, success, latency_ms)
    
    async def record_tier_migration(
        self,
        key: str,
        from_tier: MemoryTier,
        to_tier: MemoryTier,
        reason: str,
        size_bytes: Optional[int] = None
    ) -> None:
        """Record a tier migration event."""
        if not self.enabled:
            return
        
        metric = TierMigrationMetric(
            timestamp=datetime.utcnow(),
            key=key,
            from_tier=from_tier,
            to_tier=to_tier,
            reason=reason,
            size_bytes=size_bytes
        )
        
        # Add to aggregators
        for aggregator in self.aggregators.values():
            aggregator.add_migration(metric)
        
        # Store recent migration
        self.recent_migrations.append(metric)
        
        # Update counter
        self.total_migrations += 1
        
        # Update Prometheus metrics
        if self.prometheus_registry:
            self.prom_migration_total.labels(
                from_tier=from_tier.value,
                to_tier=to_tier.value,
                reason=reason
            ).inc()
    
    async def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        # Calculate current rates
        hit_rate = self.total_hits / self.total_accesses if self.total_accesses > 0 else 0.0
        error_rate = self.total_errors / self.total_operations if self.total_operations > 0 else 0.0
        
        # Get aggregated metrics
        aggregated = {}
        for window, aggregator in self.aggregators.items():
            aggregated[window] = aggregator.calculate_aggregates()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "enabled": self.enabled,
            "totals": {
                "accesses": self.total_accesses,
                "hits": self.total_hits,
                "operations": self.total_operations,
                "errors": self.total_errors,
                "migrations": self.total_migrations,
            },
            "rates": {
                "hit_rate": hit_rate,
                "error_rate": error_rate,
            },
            "aggregated": aggregated,
            "active_alerts": list(self.active_alerts.keys()),
        }
    
    async def export_metrics(self) -> Dict[str, Any]:
        """Export metrics in a structured format."""
        current = await self.get_current_metrics()
        
        # Add tier-specific metrics
        tier_metrics = {}
        for window_metrics in current["aggregated"].values():
            for tier, hit_rate in window_metrics.get("hit_rates", {}).items():
                if tier not in tier_metrics:
                    tier_metrics[tier] = {
                        "hit_rate": hit_rate,
                        "access_count": 0,
                    }
        
        # Count accesses by tier
        for metric in self.recent_accesses:
            if metric.tier:
                tier_name = metric.tier.value
                if tier_name in tier_metrics:
                    tier_metrics[tier_name]["access_count"] += 1
        
        current["tier_metrics"] = tier_metrics
        
        # Add operation-specific metrics
        operation_metrics = defaultdict(lambda: {
            "count": 0,
            "success_count": 0,
            "error_count": 0,
            "latencies": [],
        })
        
        for metric in self.recent_operations:
            op_data = operation_metrics[metric.operation]
            op_data["count"] += 1
            if metric.success:
                op_data["success_count"] += 1
            else:
                op_data["error_count"] += 1
            op_data["latencies"].append(metric.latency_ms)
        
        # Calculate operation stats
        for op, data in operation_metrics.items():
            if data["latencies"]:
                latencies = sorted(data["latencies"])
                data["latency_p50"] = self._percentile(latencies, 50)
                data["latency_p95"] = self._percentile(latencies, 95)
                data["latency_p99"] = self._percentile(latencies, 99)
                del data["latencies"]  # Remove raw data
        
        current["operation_metrics"] = dict(operation_metrics)
        
        return current
    
    async def get_prometheus_metrics(self) -> Optional[bytes]:
        """Get metrics in Prometheus format."""
        if not self.prometheus_registry:
            return None
        
        try:
            # Update gauge values
            aggregates = self.aggregators["1m"].calculate_aggregates()
            
            for tier, hit_rate in aggregates.get("hit_rates", {}).items():
                self.prom_hit_rate.labels(tier=tier).set(hit_rate)
            
            # Generate Prometheus format
            return generate_latest(self.prometheus_registry)
            
        except Exception as e:
            logger.error(f"Failed to generate Prometheus metrics: {str(e)}")
            return None
    
    async def reset_metrics(self) -> None:
        """Reset all metrics."""
        # Clear aggregators
        for aggregator in self.aggregators.values():
            aggregator.access_metrics.clear()
            aggregator.operation_metrics.clear()
            aggregator.migration_metrics.clear()
        
        # Clear recent data
        self.recent_accesses.clear()
        self.recent_operations.clear()
        self.recent_migrations.clear()
        
        # Reset counters
        self.total_accesses = 0
        self.total_hits = 0
        self.total_operations = 0
        self.total_errors = 0
        self.total_migrations = 0
        
        # Clear alerts
        self.active_alerts.clear()
        
        logger.info("Metrics reset completed")
    
    async def set_alert_threshold(
        self,
        metric_name: str,
        threshold: float
    ) -> None:
        """Set an alert threshold for a metric."""
        self.alert_thresholds[metric_name] = threshold
        logger.info(f"Set alert threshold for {metric_name}: {threshold}")
    
    async def get_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts."""
        alerts = []
        
        for alert_name, alert_time in self.active_alerts.items():
            alerts.append({
                "name": alert_name,
                "triggered_at": alert_time.isoformat(),
                "duration_seconds": (datetime.utcnow() - alert_time).total_seconds(),
            })
        
        return alerts
    
    def _percentile(self, sorted_list: List[float], percentile: int) -> float:
        """Calculate percentile from sorted list."""
        if not sorted_list:
            return 0.0
        
        index = int(len(sorted_list) * percentile / 100)
        if index >= len(sorted_list):
            index = len(sorted_list) - 1
        
        return sorted_list[index]
    
    async def _check_alerts(
        self,
        operation: str,
        success: bool,
        latency_ms: float
    ) -> None:
        """Check if any alert thresholds are exceeded."""
        # Check error rate
        if self.total_operations > 100:  # Need minimum operations
            error_rate = self.total_errors / self.total_operations
            if error_rate > self.alert_thresholds.get("error_rate", 0.05):
                alert_name = f"high_error_rate_{error_rate:.2%}"
                if alert_name not in self.active_alerts:
                    self.active_alerts[alert_name] = datetime.utcnow()
                    logger.warning(f"Alert triggered: {alert_name}")
        
        # Check latency
        if latency_ms > self.alert_thresholds.get("latency_p99", 1000):
            alert_name = f"high_latency_{operation}_{latency_ms:.0f}ms"
            if alert_name not in self.active_alerts:
                self.active_alerts[alert_name] = datetime.utcnow()
                logger.warning(f"Alert triggered: {alert_name}")
        
        # Clean old alerts (auto-resolve after 5 minutes)
        cutoff_time = datetime.utcnow() - timedelta(minutes=5)
        resolved_alerts = [
            name for name, time in self.active_alerts.items()
            if time < cutoff_time
        ]
        
        for alert_name in resolved_alerts:
            del self.active_alerts[alert_name]
            logger.info(f"Alert resolved: {alert_name}")