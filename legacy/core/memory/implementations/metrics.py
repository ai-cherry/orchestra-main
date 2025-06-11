"""
"""
    logger.warning("prometheus_client not available, metrics export will be limited")

from core.interfaces import (
    IMemoryMetrics,
    MemoryTier,
    MetricsConfig
)
from core.exceptions import MemoryMetricsError

logger = logging.getLogger(__name__)

@dataclass
class AccessMetric:
    """Represents a single access metric event."""
    """Represents a single operation metric event."""
    """Represents a tier migration event."""
    """Aggregates metrics over time windows."""
        """Add an access metric."""
        """Add an operation metric."""
        """Add a migration metric."""
        """Calculate aggregated statistics."""
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
        """Calculate percentile from sorted list."""
    """
    """
        """Initialize the metrics collector."""
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
        """Record an operation event."""
        """Record a tier migration event."""
        """Get current metrics snapshot."""
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
            aggregates = self.aggregators["1m"].calculate_aggregates()
            
            for tier, hit_rate in aggregates.get("hit_rates", {}).items():
                self.prom_hit_rate.labels(tier=tier).set(hit_rate)
            
            # Generate Prometheus format
            return generate_latest(self.prometheus_registry)
            
        except Exception:

            
            pass
            logger.error(f"Failed to generate Prometheus metrics: {str(e)}")
            return None
    
    async def reset_metrics(self) -> None:
        """Reset all metrics."""
        logger.info("Metrics reset completed")
    
    async def set_alert_threshold(
        self,
        metric_name: str,
        threshold: float
    ) -> None:
        """Set an alert threshold for a metric."""
        logger.info(f"Set alert threshold for {metric_name}: {threshold}")
    
    async def get_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts."""
                "name": alert_name,
                "triggered_at": alert_time.isoformat(),
                "duration_seconds": (datetime.utcnow() - alert_time).total_seconds(),
            })
        
        return alerts
    
    def _percentile(self, sorted_list: List[float], percentile: int) -> float:
        """Calculate percentile from sorted list."""
        """Check if any alert thresholds are exceeded."""
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