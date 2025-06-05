#!/usr/bin/env python3
"""
Redis Health Monitoring and Metrics Collection
"""

import time
import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthMetric:
    """Individual health metric"""
    name: str
    value: Any
    status: HealthStatus
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None
    
    def is_healthy(self) -> bool:
        return self.status == HealthStatus.HEALTHY


@dataclass
class RedisMetrics:
    """Redis performance metrics"""
    # Connection metrics
    connections_active: int = 0
    connections_created: int = 0
    connections_failed: int = 0
    connection_pool_size: int = 0
    
    # Command metrics
    commands_executed: int = 0
    commands_failed: int = 0
    command_latency_ms: float = 0.0
    
    # Circuit breaker metrics
    circuit_breaker_state: str = "closed"
    circuit_breaker_trips: int = 0
    circuit_breaker_recoveries: int = 0
    
    # Cache metrics
    cache_hits: int = 0
    cache_misses: int = 0
    cache_hit_rate: float = 0.0
    
    # Memory metrics
    memory_used_bytes: int = 0
    memory_max_bytes: int = 0
    memory_usage_percent: float = 0.0
    
    # Fallback metrics
    fallback_invocations: int = 0
    fallback_success_rate: float = 0.0
    
    # Timestamp
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "connections": {
                "active": self.connections_active,
                "created": self.connections_created,
                "failed": self.connections_failed,
                "pool_size": self.connection_pool_size
            },
            "commands": {
                "executed": self.commands_executed,
                "failed": self.commands_failed,
                "latency_ms": self.command_latency_ms
            },
            "circuit_breaker": {
                "state": self.circuit_breaker_state,
                "trips": self.circuit_breaker_trips,
                "recoveries": self.circuit_breaker_recoveries
            },
            "cache": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_rate": self.cache_hit_rate
            },
            "memory": {
                "used_bytes": self.memory_used_bytes,
                "max_bytes": self.memory_max_bytes,
                "usage_percent": self.memory_usage_percent
            },
            "fallback": {
                "invocations": self.fallback_invocations,
                "success_rate": self.fallback_success_rate
            },
            "timestamp": self.timestamp.isoformat()
        }


class RedisHealthMonitor:
    """Monitor Redis health and collect metrics"""
    
    def __init__(
        self,
        check_interval: int = 30,
        history_size: int = 100,
        alert_threshold: int = 3,
        alert_handlers: Optional[List[Callable]] = None
    ):
        self.check_interval = check_interval
        self.history_size = history_size
        self.alert_threshold = alert_threshold
        self.alert_handlers = alert_handlers or []
        
        # Health history
        self.health_history: deque = deque(maxlen=history_size)
        self.metrics_history: deque = deque(maxlen=history_size)
        
        # Current status
        self.current_status = HealthStatus.UNKNOWN
        self.consecutive_failures = 0
        self.last_check_time = None
        
        # Monitoring thread
        self._monitoring = False
        self._monitor_thread = None
        
    def add_alert_handler(self, handler: Callable[[HealthStatus, Dict], None]):
        """Add alert handler"""
        self.alert_handlers.append(handler)
        
    def start_monitoring(self, redis_client):
        """Start background monitoring"""
        if self._monitoring:
            return
            
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(redis_client,),
            daemon=True
        )
        self._monitor_thread.start()
        logger.info("Redis health monitoring started")
        
    def stop_monitoring(self):
        """Stop background monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Redis health monitoring stopped")
        
    def _monitor_loop(self, redis_client):
        """Background monitoring loop"""
        while self._monitoring:
            try:
                health = self.check_health(redis_client)
                self._process_health_check(health)
                # TODO: Replace with asyncio.sleep() for async code
                time.sleep(self.check_interval)
            except Exception as e:
                # TODO: Replace with asyncio.sleep() for async code
                logger.error(f"Health monitoring error: {e}")
                time.sleep(self.check_interval)
                
    def check_health(self, redis_client) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health = {
            "status": HealthStatus.UNKNOWN,
            "timestamp": datetime.utcnow(),
            "checks": {},
            "metrics": RedisMetrics()
        }
        
        try:
            # Basic connectivity
            start_time = time.time()
            ping_result = redis_client.ping()
            latency = (time.time() - start_time) * 1000
            
            health["checks"]["connectivity"] = HealthMetric(
                name="connectivity",
                value=ping_result,
                status=HealthStatus.HEALTHY if ping_result else HealthStatus.UNHEALTHY,
                timestamp=datetime.utcnow(),
                details={"latency_ms": latency}
            )
            
            # Memory check
            info = redis_client.execute_command("INFO", "memory")
            memory_info = self._parse_info(info)
            
            used_memory = int(memory_info.get("used_memory", 0))
            max_memory = int(memory_info.get("maxmemory", 0)) or (4 * 1024 * 1024 * 1024)  # 4GB default
            memory_percent = (used_memory / max_memory) * 100 if max_memory > 0 else 0
            
            memory_status = HealthStatus.HEALTHY
            if memory_percent > 90:
                memory_status = HealthStatus.UNHEALTHY
            elif memory_percent > 75:
                memory_status = HealthStatus.DEGRADED
                
            health["checks"]["memory"] = HealthMetric(
                name="memory",
                value=memory_percent,
                status=memory_status,
                timestamp=datetime.utcnow(),
                details={
                    "used_bytes": used_memory,
                    "max_bytes": max_memory,
                    "percent": memory_percent
                }
            )
            
            # Update metrics
            health["metrics"].memory_used_bytes = used_memory
            health["metrics"].memory_max_bytes = max_memory
            health["metrics"].memory_usage_percent = memory_percent
            
            # Connection pool check
            pool_info = redis_client.connection_pool.connection_kwargs
            health["metrics"].connection_pool_size = pool_info.get("max_connections", 0)
            
            # Performance check
            start_time = time.time()
            test_key = f"health_check:{int(time.time())}"
            redis_client.set(test_key, "test", ex=10)
            result = redis_client.get(test_key)
            redis_client.delete(test_key)
            operation_time = (time.time() - start_time) * 1000
            
            perf_status = HealthStatus.HEALTHY
            if operation_time > 100:  # 100ms threshold
                perf_status = HealthStatus.DEGRADED
            elif operation_time > 500:  # 500ms threshold
                perf_status = HealthStatus.UNHEALTHY
                
            health["checks"]["performance"] = HealthMetric(
                name="performance",
                value=operation_time,
                status=perf_status,
                timestamp=datetime.utcnow(),
                details={"operation_time_ms": operation_time}
            )
            
            health["metrics"].command_latency_ms = operation_time
            
            # Circuit breaker status
            if hasattr(redis_client, 'circuit_breaker'):
                cb_state = redis_client.circuit_breaker.state.value
                health["metrics"].circuit_breaker_state = cb_state
                
                cb_status = HealthStatus.HEALTHY
                if cb_state == "open":
                    cb_status = HealthStatus.UNHEALTHY
                elif cb_state == "half_open":
                    cb_status = HealthStatus.DEGRADED
                    
                health["checks"]["circuit_breaker"] = HealthMetric(
                    name="circuit_breaker",
                    value=cb_state,
                    status=cb_status,
                    timestamp=datetime.utcnow()
                )
            
            # Overall status
            all_checks = list(health["checks"].values())
            if all(check.status == HealthStatus.HEALTHY for check in all_checks):
                health["status"] = HealthStatus.HEALTHY
            elif any(check.status == HealthStatus.UNHEALTHY for check in all_checks):
                health["status"] = HealthStatus.UNHEALTHY
            else:
                health["status"] = HealthStatus.DEGRADED
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health["status"] = HealthStatus.UNHEALTHY
            health["error"] = str(e)
            
        return health
    
    def _parse_info(self, info_str: str) -> Dict[str, str]:
        """Parse Redis INFO output"""
        info_dict = {}
        for line in info_str.split('\n'):
            if ':' in line and not line.startswith('#'):
                key, value = line.split(':', 1)
                info_dict[key.strip()] = value.strip()
        return info_dict
    
    def _process_health_check(self, health: Dict[str, Any]):
        """Process health check results"""
        status = health["status"]
        
        # Update history
        self.health_history.append(health)
        if "metrics" in health:
            self.metrics_history.append(health["metrics"])
        
        # Track consecutive failures
        if status == HealthStatus.UNHEALTHY:
            self.consecutive_failures += 1
        else:
            self.consecutive_failures = 0
            
        # Status change detection
        if status != self.current_status:
            logger.info(f"Redis health status changed: {self.current_status} -> {status}")
            self.current_status = status
            
            # Trigger alerts
            if self.consecutive_failures >= self.alert_threshold:
                self._trigger_alerts(status, health)
                
        self.last_check_time = datetime.utcnow()
        
    def _trigger_alerts(self, status: HealthStatus, health: Dict[str, Any]):
        """Trigger alert handlers"""
        for handler in self.alert_handlers:
            try:
                handler(status, health)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")
                
    def get_current_health(self) -> Dict[str, Any]:
        """Get current health status"""
        if not self.health_history:
            return {
                "status": HealthStatus.UNKNOWN,
                "message": "No health checks performed yet"
            }
            
        latest = self.health_history[-1]
        return {
            "status": latest["status"],
            "timestamp": latest["timestamp"],
            "checks": {
                name: {
                    "status": check.status.value,
                    "value": check.value,
                    "details": check.details
                }
                for name, check in latest.get("checks", {}).items()
            },
            "consecutive_failures": self.consecutive_failures,
            "last_check_age_seconds": (
                datetime.utcnow() - self.last_check_time
            ).total_seconds() if self.last_check_time else None
        }
        
    def get_metrics_summary(self, window_minutes: int = 5) -> Dict[str, Any]:
        """Get metrics summary for time window"""
        if not self.metrics_history:
            return {}
            
        cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {}
            
        # Calculate averages
        summary = {
            "window_minutes": window_minutes,
            "sample_count": len(recent_metrics),
            "averages": {
                "command_latency_ms": sum(m.command_latency_ms for m in recent_metrics) / len(recent_metrics),
                "memory_usage_percent": sum(m.memory_usage_percent for m in recent_metrics) / len(recent_metrics),
                "cache_hit_rate": sum(m.cache_hit_rate for m in recent_metrics) / len(recent_metrics) if recent_metrics[0].cache_hits > 0 else 0
            },
            "totals": {
                "commands_executed": sum(m.commands_executed for m in recent_metrics),
                "commands_failed": sum(m.commands_failed for m in recent_metrics),
                "circuit_breaker_trips": sum(m.circuit_breaker_trips for m in recent_metrics),
                "fallback_invocations": sum(m.fallback_invocations for m in recent_metrics)
            }
        }
        
        return summary


# Alert handler examples
def log_alert_handler(status: HealthStatus, health: Dict[str, Any]):
    """Log health alerts"""
    logger.warning(f"Redis health alert: {status.value}")
    for check_name, check in health.get("checks", {}).items():
        if check.status != HealthStatus.HEALTHY:
            logger.warning(f"  {check_name}: {check.status.value} - {check.value}")


def webhook_alert_handler(webhook_url: str):
    """Create webhook alert handler"""
    def handler(status: HealthStatus, health: Dict[str, Any]):
        import requests
        try:
            payload = {
                "status": status.value,
                "timestamp": health["timestamp"].isoformat(),
                "checks": {
                    name: {
                        "status": check.status.value,
                        "value": check.value
                    }
                    for name, check in health.get("checks", {}).items()
                }
            }
            requests.post(webhook_url, json=payload, timeout=5)
        except Exception as e:
            logger.error(f"Webhook alert failed: {e}")
    return handler