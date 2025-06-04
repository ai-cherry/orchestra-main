"""
Resource optimization utilities for AI Cherry
Focused on efficient resource usage and code optimization
"""

import asyncio
import psutil
import gc
import sys
import time
import weakref
import functools
from typing import Any, Dict, List, Optional, Callable, AsyncGenerator, Generator
from datetime import datetime, timedelta
from dataclasses import dataclass
from contextlib import asynccontextmanager, contextmanager
import logging

logger = logging.getLogger(__name__)


@dataclass
class ResourceMetrics:
    """Resource usage metrics"""
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    disk_usage_mb: float
    open_files: int
    timestamp: datetime


class ResourceMonitor:
    """Monitor system resource usage"""
    
    def __init__(self, collection_interval: float = 60.0):
        self.collection_interval = collection_interval
        self.metrics_history: List[ResourceMetrics] = []
        self.max_history = 1440  # 24 hours at 1-minute intervals
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
    
    def get_current_metrics(self) -> ResourceMetrics:
        """Get current resource usage metrics"""
        process = psutil.Process()
        
        try:
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            memory_percent = process.memory_percent()
            
            # Get open file count safely
            try:
                open_files = len(process.open_files())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                open_files = 0
            
            # Get disk usage for current working directory
            try:
                disk_usage = psutil.disk_usage('.')
                disk_usage_mb = disk_usage.used / (1024 * 1024)
            except (OSError, psutil.Error):
                disk_usage_mb = 0
            
            return ResourceMetrics(
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                memory_percent=memory_percent,
                disk_usage_mb=disk_usage_mb,
                open_files=open_files,
                timestamp=datetime.utcnow()
            )
        
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.warning(f"Could not get resource metrics: {e}")
            return ResourceMetrics(
                cpu_percent=0.0,
                memory_mb=0.0,
                memory_percent=0.0,
                disk_usage_mb=0.0,
                open_files=0,
                timestamp=datetime.utcnow()
            )
    
    async def start_monitoring(self):
        """Start continuous resource monitoring"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Resource monitoring started")
    
    async def stop_monitoring(self):
        """Stop resource monitoring"""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Resource monitoring stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self._monitoring:
            try:
                metrics = self.get_current_metrics()
                self.metrics_history.append(metrics)
                
                # Keep only recent history
                if len(self.metrics_history) > self.max_history:
                    self.metrics_history = self.metrics_history[-self.max_history:]
                
                # Log warnings for high resource usage
                if metrics.memory_percent > 80:
                    logger.warning(f"High memory usage: {metrics.memory_percent:.1f}%")
                
                if metrics.cpu_percent > 90:
                    logger.warning(f"High CPU usage: {metrics.cpu_percent:.1f}%")
                
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                await asyncio.sleep(self.collection_interval)
    
    def get_metrics_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get resource usage summary for specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp > cutoff_time
        ]
        
        if not recent_metrics:
            return {"error": "No metrics available for the specified time period"}
        
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_mb for m in recent_metrics]
        memory_percent_values = [m.memory_percent for m in recent_metrics]
        
        return {
            "time_period_hours": hours,
            "sample_count": len(recent_metrics),
            "cpu": {
                "avg": sum(cpu_values) / len(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values)
            },
            "memory_mb": {
                "avg": sum(memory_values) / len(memory_values),
                "max": max(memory_values),
                "min": min(memory_values)
            },
            "memory_percent": {
                "avg": sum(memory_percent_values) / len(memory_percent_values),
                "max": max(memory_percent_values),
                "min": min(memory_percent_values)
            },
            "latest": recent_metrics[-1].__dict__ if recent_metrics else None
        }


class MemoryOptimizer:
    """Memory optimization utilities"""
    
    @staticmethod
    def force_garbage_collection() -> Dict[str, int]:
        """Force garbage collection and return statistics"""
        before_objects = len(gc.get_objects())
        
        # Force collection of all generations
        collected = [gc.collect(i) for i in range(3)]
        
        after_objects = len(gc.get_objects())
        
        return {
            "objects_before": before_objects,
            "objects_after": after_objects,
            "objects_freed": before_objects - after_objects,
            "collected_gen0": collected[0],
            "collected_gen1": collected[1],
            "collected_gen2": collected[2]
        }
    
    @staticmethod
    def get_memory_usage() -> Dict[str, Any]:
        """Get detailed memory usage information"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "rss_mb": memory_info.rss / (1024 * 1024),
            "vms_mb": memory_info.vms / (1024 * 1024),
            "percent": process.memory_percent(),
            "available_mb": psutil.virtual_memory().available / (1024 * 1024),
            "gc_stats": {
                "counts": gc.get_count(),
                "thresholds": gc.get_threshold(),
                "objects": len(gc.get_objects())
            }
        }
    
    @staticmethod
    def optimize_memory():
        """Perform memory optimization"""
        # Force garbage collection
        gc_stats = MemoryOptimizer.force_garbage_collection()
        
        # Clear internal caches if available
        if hasattr(sys, '_clear_type_cache'):
            sys._clear_type_cache()
        
        logger.info(f"Memory optimization completed: {gc_stats}")
        return gc_stats


class ObjectPool:
    """Generic object pool for reusing expensive objects"""
    
    def __init__(self, factory: Callable, max_size: int = 10, cleanup_func: Optional[Callable] = None):
        self.factory = factory
        self.max_size = max_size
        self.cleanup_func = cleanup_func
        self._pool: List[Any] = []
        self._in_use: weakref.WeakSet = weakref.WeakSet()
    
    def acquire(self) -> Any:
        """Acquire an object from the pool"""
        if self._pool:
            obj = self._pool.pop()
        else:
            obj = self.factory()
        
        self._in_use.add(obj)
        return obj
    
    def release(self, obj: Any):
        """Release an object back to the pool"""
        if obj in self._in_use:
            self._in_use.discard(obj)
            
            if len(self._pool) < self.max_size:
                # Clean up the object if cleanup function provided
                if self.cleanup_func:
                    try:
                        self.cleanup_func(obj)
                    except Exception as e:
                        logger.warning(f"Error cleaning up pooled object: {e}")
                        return
                
                self._pool.append(obj)
    
    def clear(self):
        """Clear the pool"""
        self._pool.clear()
    
    def stats(self) -> Dict[str, int]:
        """Get pool statistics"""
        return {
            "available": len(self._pool),
            "in_use": len(self._in_use),
            "max_size": self.max_size
        }


@asynccontextmanager
async def resource_limit(max_memory_mb: Optional[float] = None, max_cpu_percent: Optional[float] = None):
    """Context manager to monitor and limit resource usage"""
    monitor = ResourceMonitor(collection_interval=1.0)
    await monitor.start_monitoring()
    
    try:
        yield monitor
        
        # Check final resource usage
        final_metrics = monitor.get_current_metrics()
        
        if max_memory_mb and final_metrics.memory_mb > max_memory_mb:
            logger.warning(f"Memory usage exceeded limit: {final_metrics.memory_mb:.1f}MB > {max_memory_mb}MB")
        
        if max_cpu_percent and final_metrics.cpu_percent > max_cpu_percent:
            logger.warning(f"CPU usage exceeded limit: {final_metrics.cpu_percent:.1f}% > {max_cpu_percent}%")
    
    finally:
        await monitor.stop_monitoring()


class AsyncBatchOptimizer:
    """Optimize async operations through intelligent batching"""
    
    def __init__(self, batch_size: int = 10, max_wait_time: float = 1.0):
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self._pending_operations: List[Dict[str, Any]] = []
        self._processing = False
        self._results: Dict[str, Any] = {}
    
    async def add_operation(self, operation_id: str, coro) -> Any:
        """Add an async operation to be batched"""
        future = asyncio.Future()
        
        self._pending_operations.append({
            "id": operation_id,
            "coro": coro,
            "future": future
        })
        
        # Trigger batch processing if needed
        if len(self._pending_operations) >= self.batch_size:
            asyncio.create_task(self._process_batch())
        elif not self._processing:
            asyncio.create_task(self._delayed_process())
        
        return await future
    
    async def _delayed_process(self):
        """Process batch after delay"""
        await asyncio.sleep(self.max_wait_time)
        if self._pending_operations and not self._processing:
            await self._process_batch()
    
    async def _process_batch(self):
        """Process current batch of operations"""
        if self._processing or not self._pending_operations:
            return
        
        self._processing = True
        
        try:
            # Take current batch
            batch = self._pending_operations[:self.batch_size]
            self._pending_operations = self._pending_operations[self.batch_size:]
            
            # Execute all operations concurrently
            coroutines = [op["coro"] for op in batch]
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Set results for futures
            for op, result in zip(batch, results):
                if isinstance(result, Exception):
                    op["future"].set_exception(result)
                else:
                    op["future"].set_result(result)
        
        finally:
            self._processing = False


class LazyLoader:
    """Lazy loading utility for expensive resources"""
    
    def __init__(self, loader_func: Callable, *args, **kwargs):
        self.loader_func = loader_func
        self.args = args
        self.kwargs = kwargs
        self._loaded = False
        self._value = None
        self._loading = False
        self._load_lock = asyncio.Lock()
    
    async def get(self):
        """Get the loaded value, loading if necessary"""
        if self._loaded:
            return self._value
        
        async with self._load_lock:
            if self._loaded:  # Double-check after acquiring lock
                return self._value
            
            if asyncio.iscoroutinefunction(self.loader_func):
                self._value = await self.loader_func(*self.args, **self.kwargs)
            else:
                self._value = self.loader_func(*self.args, **self.kwargs)
            
            self._loaded = True
            return self._value
    
    def is_loaded(self) -> bool:
        """Check if the value has been loaded"""
        return self._loaded
    
    def reset(self):
        """Reset the loader to unloaded state"""
        self._loaded = False
        self._value = None


class EfficiencyDecorator:
    """Decorator for optimizing function efficiency"""
    
    @staticmethod
    def memoize_with_ttl(ttl_seconds: int = 300):
        """Memoization with TTL for expensive computations"""
        def decorator(func):
            cache = {}
            
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                key = str(args) + str(sorted(kwargs.items()))
                now = time.time()
                
                if key in cache:
                    value, timestamp = cache[key]
                    if now - timestamp < ttl_seconds:
                        return value
                
                result = await func(*args, **kwargs)
                cache[key] = (result, now)
                
                # Clean expired entries periodically
                if len(cache) > 100:
                    expired_keys = [
                        k for k, (_, ts) in cache.items()
                        if now - ts >= ttl_seconds
                    ]
                    for k in expired_keys:
                        del cache[k]
                
                return result
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                key = str(args) + str(sorted(kwargs.items()))
                now = time.time()
                
                if key in cache:
                    value, timestamp = cache[key]
                    if now - timestamp < ttl_seconds:
                        return value
                
                result = func(*args, **kwargs)
                cache[key] = (result, now)
                
                # Clean expired entries
                if len(cache) > 100:
                    expired_keys = [
                        k for k, (_, ts) in cache.items()
                        if now - ts >= ttl_seconds
                    ]
                    for k in expired_keys:
                        del cache[k]
                
                return result
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    @staticmethod
    def rate_limit(calls_per_second: float = 10.0):
        """Rate limiting decorator"""
        def decorator(func):
            last_called = [0.0]
            min_interval = 1.0 / calls_per_second
            
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                now = time.time()
                time_since_last = now - last_called[0]
                
                if time_since_last < min_interval:
                    await asyncio.sleep(min_interval - time_since_last)
                
                last_called[0] = time.time()
                return await func(*args, **kwargs)
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                now = time.time()
                time_since_last = now - last_called[0]
                
                if time_since_last < min_interval:
                    time.sleep(min_interval - time_since_last)
                
                last_called[0] = time.time()
                return func(*args, **kwargs)
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator


# Global instances
resource_monitor = ResourceMonitor()
memory_optimizer = MemoryOptimizer()


async def optimize_system_resources():
    """Perform comprehensive system resource optimization"""
    logger.info("Starting system resource optimization")
    
    # Memory optimization
    gc_stats = memory_optimizer.optimize_memory()
    
    # Get current metrics
    current_metrics = resource_monitor.get_current_metrics()
    
    optimization_report = {
        "timestamp": datetime.utcnow().isoformat(),
        "memory_optimization": gc_stats,
        "current_metrics": current_metrics.__dict__,
        "recommendations": []
    }
    
    # Add recommendations based on current state
    if current_metrics.memory_percent > 70:
        optimization_report["recommendations"].append("Consider reducing memory usage or increasing available memory")
    
    if current_metrics.cpu_percent > 80:
        optimization_report["recommendations"].append("High CPU usage detected, consider optimizing CPU-intensive operations")
    
    if current_metrics.open_files > 100:
        optimization_report["recommendations"].append("High number of open files, ensure proper file handle cleanup")
    
    logger.info(f"System optimization completed: {optimization_report}")
    return optimization_report

