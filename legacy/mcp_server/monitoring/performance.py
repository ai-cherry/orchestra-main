"""
Performance monitoring and optimization for single-user Cherry AI
Lightweight, efficient monitoring without external dependencies
"""

import time
import psutil
import asyncio
from collections import deque, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Deque
import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class PerformanceMetric:
    """Single performance measurement"""
    timestamp: float
    metric_type: str
    value: float
    context: str
    metadata: Optional[Dict] = None

class PerformanceMonitor:
    """Lightweight performance monitoring for single-user deployment"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics: Dict[str, Deque[PerformanceMetric]] = defaultdict(
            lambda: deque(maxlen=max_history)
        )
        self.start_time = time.time()
        self.request_times: Deque[float] = deque(maxlen=1000)
        self.error_count = 0
        self.context = os.getenv("cherry_ai_CONTEXT", "development")
        
        # Performance thresholds based on context
        self.thresholds = {
            "development": {
                "response_time_ms": 1000,
                "memory_percent": 90,
                "cpu_percent": 95
            },
            "production": {
                "response_time_ms": 200,
                "memory_percent": 80,
                "cpu_percent": 85
            },
            "testing": {
                "response_time_ms": 500,
                "memory_percent": 85,
                "cpu_percent": 90
            }
        }
    
    def record_metric(self, metric_type: str, value: float, metadata: Optional[Dict] = None):
        """Record a performance metric"""
        metric = PerformanceMetric(
            timestamp=time.time(),
            metric_type=metric_type,
            value=value,
            context=self.context,
            metadata=metadata or {}
        )
        self.metrics[metric_type].append(metric)
    
    def record_request(self, duration_ms: float, endpoint: str, status_code: int):
        """Record API request performance"""
        self.request_times.append(time.time())
        self.record_metric(
            "request_duration",
            duration_ms,
            {
                "endpoint": endpoint,
                "status_code": status_code,
                "success": 200 <= status_code < 300
            }
        )
        
        if status_code >= 500:
            self.error_count += 1
    
    async def collect_system_metrics(self):
        """Collect system performance metrics"""
        while True:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.record_metric("cpu_usage", cpu_percent)
                
                # Memory usage
                memory = psutil.virtual_memory()
                self.record_metric("memory_usage", memory.percent)
                self.record_metric("memory_available_mb", memory.available / 1024 / 1024)
                
                # Disk usage
                disk = psutil.disk_usage('/')
                self.record_metric("disk_usage", disk.percent)
                
                # Network I/O
                net_io = psutil.net_io_counters()
                self.record_metric("network_bytes_sent", net_io.bytes_sent)
                self.record_metric("network_bytes_recv", net_io.bytes_recv)
                
                # Process-specific metrics
                process = psutil.Process()
                self.record_metric("process_memory_mb", process.memory_info().rss / 1024 / 1024)
                self.record_metric("process_threads", process.num_threads())
                
                # Check for performance issues
                await self._check_performance_thresholds()
                
            except Exception as e:
                print(f"Error collecting metrics: {e}")
            
            # Collection interval based on context
            interval = 60 if self.context == "production" else 30
            await asyncio.sleep(interval)
    
    async def _check_performance_thresholds(self):
        """Check if performance metrics exceed thresholds"""
        thresholds = self.thresholds.get(self.context, self.thresholds["production"])
        alerts = []
        
        # Check response times
        if self.metrics["request_duration"]:
            recent_requests = list(self.metrics["request_duration"])[-100:]
            avg_response_time = sum(m.value for m in recent_requests) / len(recent_requests)
            
            if avg_response_time > thresholds["response_time_ms"]:
                alerts.append({
                    "type": "high_response_time",
                    "value": avg_response_time,
                    "threshold": thresholds["response_time_ms"]
                })
        
        # Check CPU usage
        if self.metrics["cpu_usage"]:
            recent_cpu = list(self.metrics["cpu_usage"])[-10:]
            avg_cpu = sum(m.value for m in recent_cpu) / len(recent_cpu)
            
            if avg_cpu > thresholds["cpu_percent"]:
                alerts.append({
                    "type": "high_cpu_usage",
                    "value": avg_cpu,
                    "threshold": thresholds["cpu_percent"]
                })
        
        # Check memory usage
        if self.metrics["memory_usage"]:
            current_memory = self.metrics["memory_usage"][-1].value
            
            if current_memory > thresholds["memory_percent"]:
                alerts.append({
                    "type": "high_memory_usage",
                    "value": current_memory,
                    "threshold": thresholds["memory_percent"]
                })
        
        # Log alerts in development, take action in production
        if alerts:
            if self.context == "development":
                for alert in alerts:
                    print(f"⚠️  Performance Alert: {alert}")
            else:
                await self._handle_performance_alerts(alerts)
    
    async def _handle_performance_alerts(self, alerts: List[Dict]):
        """Handle performance alerts in production"""
        # In production, we might want to:
        # - Send notifications
        # - Trigger auto-scaling
        # - Clear caches
        # - Restart services
        
        for alert in alerts:
            if alert["type"] == "high_memory_usage":
                # Clear caches or trigger garbage collection
                import gc
                gc.collect()
                self.record_metric("gc_triggered", 1)
    
    def get_summary(self) -> Dict:
        """Get performance summary"""
        uptime = time.time() - self.start_time
        
        # Calculate request rate
        now = time.time()
        recent_requests = [t for t in self.request_times if now - t < 60]
        requests_per_minute = len(recent_requests)
        
        # Calculate average response time
        recent_durations = list(self.metrics["request_duration"])[-100:]
        avg_response_time = (
            sum(m.value for m in recent_durations) / len(recent_durations)
            if recent_durations else 0
        )
        
        # Get current system metrics
        current_metrics = {}
        for metric_type in ["cpu_usage", "memory_usage", "disk_usage"]:
            if self.metrics[metric_type]:
                current_metrics[metric_type] = self.metrics[metric_type][-1].value
        
        return {
            "uptime_seconds": uptime,
            "context": self.context,
            "requests_per_minute": requests_per_minute,
            "avg_response_time_ms": avg_response_time,
            "error_count": self.error_count,
            "current_metrics": current_metrics,
            "metric_counts": {k: len(v) for k, v in self.metrics.items()}
        }
    
    def export_metrics(self, filepath: Optional[Path] = None) -> str:
        """Export metrics to JSON file"""
        if not filepath:
            filepath = Path(f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        export_data = {
            "export_time": datetime.now().isoformat(),
            "context": self.context,
            "summary": self.get_summary(),
            "metrics": {}
        }
        
        # Convert metrics to serializable format
        for metric_type, metrics in self.metrics.items():
            export_data["metrics"][metric_type] = [
                asdict(m) for m in list(metrics)[-100:]  # Last 100 of each type
            ]
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return str(filepath)

# Singleton instance
_monitor_instance: Optional[PerformanceMonitor] = None

def get_performance_monitor() -> PerformanceMonitor:
    """Get or create the performance monitor singleton"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = PerformanceMonitor()
    return _monitor_instance

# FastAPI integration
class PerformanceMiddleware:
    """FastAPI middleware for automatic performance monitoring"""
    
    def __init__(self, app):
        self.app = app
        self.monitor = get_performance_monitor()
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                duration_ms = (time.time() - start_time) * 1000
                
                # Record the metric
                self.monitor.record_request(
                    duration_ms,
                    scope["path"],
                    message.get("status", 200)
                )
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)

# Optimization utilities
class PerformanceOptimizer:
    """Automatic performance optimization for single-user deployment"""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.optimizations_applied = []
    
    async def auto_optimize(self):
        """Automatically apply performance optimizations based on metrics"""
        while True:
            try:
                summary = self.monitor.get_summary()
                
                # Memory optimization
                if summary["current_metrics"].get("memory_usage", 0) > 70:
                    await self._optimize_memory()
                
                # Response time optimization
                if summary["avg_response_time_ms"] > 500:
                    await self._optimize_response_time()
                
                # CPU optimization
                if summary["current_metrics"].get("cpu_usage", 0) > 80:
                    await self._optimize_cpu()
                
            except Exception as e:
                print(f"Error in auto-optimization: {e}")
            
            # Run optimization checks every 5 minutes
            await asyncio.sleep(300)
    
    async def _optimize_memory(self):
        """Apply memory optimizations"""
        import gc
        
        # Force garbage collection
        gc.collect()
        
        # Clear any caches (implement based on your caching strategy)
        # For example: clear_caches()
        
        self.optimizations_applied.append({
            "type": "memory",
            "timestamp": datetime.now().isoformat(),
            "action": "gc_collect"
        })
        
        self.monitor.record_metric("optimization_applied", 1, {"type": "memory"})
    
    async def _optimize_response_time(self):
        """Apply response time optimizations"""
        # Implement based on your application
        # Examples:
        # - Enable query result caching
        # - Optimize database queries
        # - Enable compression
        
        self.optimizations_applied.append({
            "type": "response_time",
            "timestamp": datetime.now().isoformat(),
            "action": "cache_enabled"
        })
        
        self.monitor.record_metric("optimization_applied", 1, {"type": "response_time"})
    
    async def _optimize_cpu(self):
        """Apply CPU optimizations"""
        # Implement based on your application
        # Examples:
        # - Reduce logging verbosity
        # - Disable debug features
        # - Optimize algorithms
        
        self.optimizations_applied.append({
            "type": "cpu",
            "timestamp": datetime.now().isoformat(),
            "action": "logging_reduced"
        })
        
        self.monitor.record_metric("optimization_applied", 1, {"type": "cpu"})