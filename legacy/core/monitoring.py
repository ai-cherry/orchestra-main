"""
Application Monitoring
Provides comprehensive monitoring and metrics collection
"""

import time
import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class Metric:
    """Represents a single metric"""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = field(default_factory=dict)

class MetricsCollector:
    """Collects and manages application metrics"""
    
    def __init__(self):
        self.metrics: Dict[str, list] = defaultdict(list)
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.timers: Dict[str, list] = defaultdict(list)
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        self.counters[name] += value
        self.metrics[name].append(Metric(name, self.counters[name], tags=tags or {}))
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric"""
        self.gauges[name] = value
        self.metrics[name].append(Metric(name, value, tags=tags or {}))
    
    def record_timer(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None):
        """Record a timer metric"""
        self.timers[name].append(duration)
        self.metrics[name].append(Metric(name, duration, tags=tags or {}))
    
    @asynccontextmanager
    async def timer(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Context manager for timing operations"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_timer(name, duration, tags)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        summary = {
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'timers': {}
        }
        
        # Calculate timer statistics
        for name, durations in self.timers.items():
            if durations:
                summary['timers'][name] = {
                    'count': len(durations),
                    'mean': sum(durations) / len(durations),
                    'min': min(durations),
                    'max': max(durations),
                    'total': sum(durations)
                }
        
        return summary

class HealthChecker:
    """Manages health checks for the application"""
    
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.check_results: Dict[str, Dict[str, Any]] = {}
    
    def register_check(self, name: str, check_func: Callable):
        """Register a health check"""
        self.checks[name] = check_func
    
    async def run_checks(self) -> Dict[str, Any]:
        """Run all registered health checks"""
        results = {}
        overall_healthy = True
        
        for name, check_func in self.checks.items():
            try:
                start_time = time.time()
                
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                
                duration = time.time() - start_time
                
                results[name] = {
                    'healthy': result.get('healthy', True),
                    'message': result.get('message', 'OK'),
                    'duration_ms': duration * 1000,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                if not results[name]['healthy']:
                    overall_healthy = False
                    
            except Exception as e:
                results[name] = {
                    'healthy': False,
                    'message': str(e),
                    'duration_ms': 0,
                    'timestamp': datetime.utcnow().isoformat()
                }
                overall_healthy = False
        
        self.check_results = results
        
        return {
            'healthy': overall_healthy,
            'checks': results,
            'timestamp': datetime.utcnow().isoformat()
        }

# Global instances
metrics = MetricsCollector()
health = HealthChecker()

def monitor_performance(name: str):
    """Decorator to monitor function performance"""
    def decorator(func: Callable):
        async def async_wrapper(*args, **kwargs):
            async with metrics.timer(f"{name}.duration"):
                try:
                    result = await func(*args, **kwargs)
                    metrics.increment_counter(f"{name}.success")
                    return result
                except Exception as e:
                    metrics.increment_counter(f"{name}.error")
                    raise
        
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                metrics.record_timer(f"{name}.duration", duration)
                metrics.increment_counter(f"{name}.success")
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics.record_timer(f"{name}.duration", duration)
                metrics.increment_counter(f"{name}.error")
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
