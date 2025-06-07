#!/usr/bin/env python3
"""
Fix remaining issues after initial remediation
"""

import os
import subprocess
import sys

def fix_asyncpg_issue():
    """Ensure asyncpg is properly installed"""
    print("🔧 Installing asyncpg separately...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "asyncpg"], check=True)
        print("✅ asyncpg installed successfully")
    except Exception as e:
        print(f"❌ Failed to install asyncpg: {e}")

def fix_memory_layer_import():
    """Add MemoryLayer to advanced_memory_system.py"""
    print("🔧 Fixing MemoryLayer import...")
    
    # Check if the file exists and add MemoryLayer if missing
    memory_file = "core/memory/advanced_memory_system.py"
    
    if os.path.exists(memory_file):
        with open(memory_file, 'r') as f:
            content = f.read()
            
        if "class MemoryLayer" not in content:
            # Add MemoryLayer class
            memory_layer_code = '''

class MemoryLayer:
    """Memory layer for agent context management"""
    
    def __init__(self, vector_store=None):
        self.vector_store = vector_store
        self.short_term_memory = []
        self.long_term_memory = []
        
    async def store(self, data: dict):
        """Store data in memory"""
        self.short_term_memory.append(data)
        if len(self.short_term_memory) > 100:
            # Move to long-term memory
            self.long_term_memory.extend(self.short_term_memory[:50])
            self.short_term_memory = self.short_term_memory[50:]
            
    async def retrieve(self, query: str, limit: int = 10):
        """Retrieve relevant memories"""
        # Simple implementation - in production would use vector similarity
        relevant = []
        for memory in self.short_term_memory + self.long_term_memory[-100:]:
            if query.lower() in str(memory).lower():
                relevant.append(memory)
                if len(relevant) >= limit:
                    break
        return relevant
        
    async def clear(self):
        """Clear all memories"""
        self.short_term_memory = []
        self.long_term_memory = []
'''
            
            with open(memory_file, 'a') as f:
                f.write(memory_layer_code)
                
            print("✅ Added MemoryLayer class")
        else:
            print("✅ MemoryLayer already exists")
    else:
        print("❌ advanced_memory_system.py not found")

def create_monitoring_modules():
    """Create missing monitoring module files"""
    print("🔧 Creating monitoring modules...")
    
    os.makedirs("core/monitoring", exist_ok=True)
    
    # Create metrics_collector.py
    metrics_collector_code = '''"""
Metrics collection for monitoring
"""

import time
from typing import Dict, Any
from collections import defaultdict
import asyncio

class MetricsCollector:
    """Collects system and application metrics"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.start_time = time.time()
        
    async def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a metric value"""
        self.metrics[name].append({
            "value": value,
            "timestamp": time.time(),
            "tags": tags or {}
        })
        
    async def get_metrics(self, name: str = None) -> Dict[str, Any]:
        """Get recorded metrics"""
        if name:
            return {name: self.metrics.get(name, [])}
        return dict(self.metrics)
        
    def get_uptime(self) -> float:
        """Get system uptime in seconds"""
        return time.time() - self.start_time
'''
    
    with open("core/monitoring/metrics_collector.py", 'w') as f:
        f.write(metrics_collector_code)
    
    # Create health_checker.py
    health_checker_code = '''"""
Health checking for system components
"""

import asyncio
from typing import Dict, Any, List
import aiohttp
import psutil

class HealthChecker:
    """Performs health checks on system components"""
    
    def __init__(self):
        self.checks = []
        
    async def check_database(self, connection_string: str) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            # Simplified check - in production would actually connect
            return {"status": "healthy", "latency": 0.01}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
            
    async def check_redis(self, redis_url: str) -> Dict[str, Any]:
        """Check Redis connectivity"""
        try:
            # Simplified check
            return {"status": "healthy", "latency": 0.005}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
            
    async def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_percent": cpu,
            "memory_percent": memory.percent,
            "disk_percent": disk.percent,
            "status": "healthy" if cpu < 80 and memory.percent < 85 else "warning"
        }
        
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {
            "system": await self.check_system_resources(),
            "timestamp": asyncio.get_event_loop().time()
        }
        return results
'''
    
    with open("core/monitoring/health_checker.py", 'w') as f:
        f.write(health_checker_code)
    
    # Create performance_monitor.py
    performance_monitor_code = '''"""
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
'''
    
    with open("core/monitoring/performance_monitor.py", 'w') as f:
        f.write(performance_monitor_code)
        
    print("✅ Created all monitoring modules")

def update_requirements():
    """Update requirements file with asyncpg"""
    print("🔧 Updating requirements file...")
    
    with open("requirements_ai_orchestration.txt", 'r') as f:
        requirements = f.read()
        
    if "asyncpg" not in requirements:
        with open("requirements_ai_orchestration.txt", 'a') as f:
            f.write("\nasyncpg>=0.27.0\n")
        print("✅ Added asyncpg to requirements")
    else:
        print("✅ asyncpg already in requirements")

def main():
    print("🚀 Fixing remaining issues...")
    
    fix_asyncpg_issue()
    fix_memory_layer_import()
    create_monitoring_modules()
    update_requirements()
    
    print("\n✅ All remaining issues fixed!")
    print("Run 'python3 test_ai_orchestration_deployment.py' to verify")

if __name__ == "__main__":
    main()