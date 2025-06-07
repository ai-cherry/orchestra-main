"""
Performance monitoring for the system
"""

import time
import asyncio
from typing import Dict, Any, Callable
from functools import wraps

class PerformanceMonitor:
    """Monitors performance metrics"""
    
    def __init__(self):
        self.timings = {}
        
    def measure_time(self, name: str):
        """Decorator to measure function execution time"""
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start
                    self.record_timing(name, duration)
                    return result
                except Exception as e:
                    duration = time.time() - start
                    self.record_timing(name, duration, error=True)
                    raise
                    
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start
                    self.record_timing(name, duration)
                    return result
                except Exception as e:
                    duration = time.time() - start
                    self.record_timing(name, duration, error=True)
                    raise
                    
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
        
    def record_timing(self, name: str, duration: float, error: bool = False):
        """Record a timing measurement"""
        if name not in self.timings:
            self.timings[name] = []
            
        self.timings[name].append({
            "duration": duration,
            "timestamp": time.time(),
            "error": error
        })
        
    def get_stats(self, name: str = None) -> Dict[str, Any]:
        """Get performance statistics"""
        if name:
            timings = self.timings.get(name, [])
        else:
            timings = []
            for timing_list in self.timings.values():
                timings.extend(timing_list)
                
        if not timings:
            return {}
            
        durations = [t["duration"] for t in timings if not t["error"]]
        if not durations:
            return {"error_rate": 1.0}
            
        durations.sort()
        
        return {
            "count": len(timings),
            "error_count": sum(1 for t in timings if t["error"]),
            "error_rate": sum(1 for t in timings if t["error"]) / len(timings),
            "min": min(durations),
            "max": max(durations),
            "avg": sum(durations) / len(durations),
            "p50": durations[len(durations) // 2],
            "p95": durations[int(len(durations) * 0.95)] if len(durations) > 20 else durations[-1],
            "p99": durations[int(len(durations) * 0.99)] if len(durations) > 100 else durations[-1]
        }
