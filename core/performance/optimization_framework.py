"""
Performance Optimization Framework
Event-driven coordination and resource management to replace sleep calls and improve performance
"""

import asyncio
import time
import psutil
import weakref
import gc
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# ========================================
# EVENT-DRIVEN COORDINATION SYSTEM
# ========================================

class EventType(Enum):
    """System event types for coordination"""
    SYSTEM_READY = "system_ready"
    DATABASE_CONNECTED = "database_connected"
    PERSONA_INITIALIZED = "persona_initialized"
    MEMORY_LOADED = "memory_loaded"
    VOICE_READY = "voice_ready"
    ADMIN_READY = "admin_ready"
    COORDINATION_ACTIVE = "coordination_active"
    RAG_INITIALIZED = "rag_initialized"
    AGENT_SWARM_READY = "agent_swarm_ready"
    USER_AUTHENTICATED = "user_authenticated"
    CONFIGURATION_UPDATED = "configuration_updated"

@dataclass
class Event:
    """Event data structure"""
    event_type: EventType
    data: Any = None
    timestamp: float = field(default_factory=time.time)
    source: str = "unknown"
    correlation_id: Optional[str] = None

class EventManager:
    """Event-driven coordination to replace sleep calls"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.events: Dict[EventType, asyncio.Event] = {}
        self.event_data: Dict[EventType, Event] = {}
        self.listeners: Dict[EventType, List[Callable]] = {}
        self.condition_waiters: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
    
    async def wait_for_event(self, 
                           event_type: EventType, 
                           timeout: float = 30.0,
                           correlation_id: str = None) -> Optional[Event]:
        """Wait for specific event instead of sleeping"""
        
        async with self._lock:
            if event_type not in self.events:
                self.events[event_type] = asyncio.Event()
        
        try:
            # Wait for event with timeout
            await asyncio.wait_for(self.events[event_type].wait(), timeout=timeout)
            
            # Return event data if available
            event_data = self.event_data.get(event_type)
            
            # Check correlation ID if specified
            if correlation_id and event_data and event_data.correlation_id != correlation_id:
                return None
            
            return event_data
            
        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout waiting for event {event_type.value} after {timeout}s")
            return None
    
    async def wait_for_condition(self, 
                               condition: Callable[[], bool], 
                               timeout: float = 30.0,
                               check_interval: float = 0.1,
                               description: str = "condition") -> bool:
        """Wait for condition to be true instead of fixed sleep"""
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                if condition():
                    self.logger.debug(f"Condition '{description}' met after {time.time() - start_time:.2f}s")
                    return True
            except Exception as e:
                self.logger.warning(f"Error checking condition '{description}': {e}")
            
            await asyncio.sleep(check_interval)
        
        self.logger.warning(f"Timeout waiting for condition '{description}' after {timeout}s")
        return False
    
    def trigger_event(self, 
                     event_type: EventType, 
                     data: Any = None,
                     source: str = "unknown",
                     correlation_id: str = None):
        """Trigger event to wake up waiting coroutines"""
        
        event = Event(
            event_type=event_type,
            data=data,
            source=source,
            correlation_id=correlation_id
        )
        
        # Store event data
        self.event_data[event_type] = event
        
        # Trigger event
        if event_type in self.events:
            self.events[event_type].set()
            self.logger.debug(f"Event {event_type.value} triggered by {source}")
        
        # Notify listeners
        if event_type in self.listeners:
            for listener in self.listeners[event_type]:
                try:
                    if asyncio.iscoroutinefunction(listener):
                        asyncio.create_task(listener(event))
                    else:
                        listener(event)
                except Exception as e:
                    self.logger.error(f"Error in event listener: {e}")
    
    async def wait_for_multiple_events(self, 
                                     event_types: List[EventType], 
                                     timeout: float = 30.0,
                                     wait_for_all: bool = True) -> Dict[EventType, Optional[Event]]:
        """Wait for multiple events"""
        
        tasks = []
        for event_type in event_types:
            task = asyncio.create_task(self.wait_for_event(event_type, timeout))
            tasks.append((event_type, task))
        
        results = {}
        
        if wait_for_all:
            # Wait for all events
            for event_type, task in tasks:
                results[event_type] = await task
        else:
            # Wait for any event
            done, pending = await asyncio.wait(
                [task for _, task in tasks], 
                return_when=asyncio.FIRST_COMPLETED,
                timeout=timeout
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
            
            # Get results from completed tasks
            for event_type, task in tasks:
                if task in done:
                    results[event_type] = await task
                else:
                    results[event_type] = None
        
        return results
    
    def add_event_listener(self, event_type: EventType, listener: Callable):
        """Add event listener"""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(listener)
    
    def remove_event_listener(self, event_type: EventType, listener: Callable):
        """Remove event listener"""
        if event_type in self.listeners:
            try:
                self.listeners[event_type].remove(listener)
            except ValueError:
                pass
    
    def reset_event(self, event_type: EventType):
        """Reset event to allow waiting again"""
        if event_type in self.events:
            self.events[event_type].clear()
        if event_type in self.event_data:
            del self.event_data[event_type]

# ========================================
# RESOURCE MANAGEMENT SYSTEM
# ========================================

@dataclass
class ResourceStats:
    """Resource usage statistics"""
    memory_usage_mb: float
    cpu_usage_percent: float
    open_connections: int
    active_tasks: int
    gc_collections: Dict[int, int]
    timestamp: datetime

class ResourceManager:
    """Advanced resource management and cleanup"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.resources: List[weakref.ref] = []
        self.cleanup_callbacks: List[Callable] = []
        self.memory_threshold_mb = 1000  # 1GB threshold
        self.cleanup_interval = 300  # 5 minutes
        self._cleanup_task: Optional[asyncio.Task] = None
        self._monitoring_active = False
    
    async def start_monitoring(self):
        """Start resource monitoring and cleanup"""
        if not self._monitoring_active:
            self._monitoring_active = True
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            self.logger.info("Resource monitoring started")
    
    async def stop_monitoring(self):
        """Stop resource monitoring"""
        self._monitoring_active = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Resource monitoring stopped")
    
    def get_resource_stats(self) -> ResourceStats:
        """Get current resource statistics"""
        
        # System memory info
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Count active asyncio tasks
        try:
            active_tasks = len([task for task in asyncio.all_tasks() if not task.done()])
        except RuntimeError:
            active_tasks = 0
        
        # Garbage collection stats
        gc_stats = {}
        for generation in range(3):
            gc_stats[generation] = gc.get_count()[generation]
        
        # Count open connections (simplified)
        open_connections = len([ref for ref in self.resources if ref() is not None])
        
        return ResourceStats(
            memory_usage_mb=memory.used / 1024 / 1024,
            cpu_usage_percent=cpu_percent,
            open_connections=open_connections,
            active_tasks=active_tasks,
            gc_collections=gc_stats,
            timestamp=datetime.now()
        )
    
    async def cleanup_resources(self, force: bool = False) -> Dict[str, Any]:
        """Perform resource cleanup"""
        
        stats_before = self.get_resource_stats()
        
        # Clean up dead weak references
        self.resources = [ref for ref in self.resources if ref() is not None]
        
        # Run cleanup callbacks
        cleanup_results = []
        for callback in self.cleanup_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    result = await callback()
                else:
                    result = callback()
                cleanup_results.append(result)
            except Exception as e:
                self.logger.error(f"Error in cleanup callback: {e}")
                cleanup_results.append({"error": str(e)})
        
        # Force garbage collection
        collected_objects = gc.collect()
        
        # Additional aggressive cleanup if needed
        if force or stats_before.memory_usage_mb > self.memory_threshold_mb:
            await self._aggressive_cleanup()
        
        stats_after = self.get_resource_stats()
        
        memory_freed = stats_before.memory_usage_mb - stats_after.memory_usage_mb
        
        cleanup_summary = {
            "memory_freed_mb": memory_freed,
            "objects_collected": collected_objects,
            "resources_cleaned": len(cleanup_results),
            "before_stats": stats_before.__dict__,
            "after_stats": stats_after.__dict__,
            "cleanup_results": cleanup_results
        }
        
        self.logger.info(
            f"Resource cleanup completed: "
            f"freed {memory_freed:.2f}MB, "
            f"collected {collected_objects} objects"
        )
        
        return cleanup_summary
    
    async def _periodic_cleanup(self):
        """Periodic resource cleanup task"""
        while self._monitoring_active:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                if not self._monitoring_active:
                    break
                
                stats = self.get_resource_stats()
                
                # Cleanup if memory usage is high
                if stats.memory_usage_mb > self.memory_threshold_mb * 0.7:
                    await self.cleanup_resources()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in periodic cleanup: {e}")
    
    async def _aggressive_cleanup(self):
        """Aggressive cleanup for high resource usage"""
        
        # Multiple garbage collection passes
        for _ in range(3):
            gc.collect()
            await asyncio.sleep(0.1)
        
        # Cancel completed tasks
        try:
            completed_tasks = [task for task in asyncio.all_tasks() if task.done()]
            for task in completed_tasks:
                if not task.cancelled():
                    task.cancel()
        except RuntimeError:
            pass
    
    def register_resource(self, resource: Any):
        """Register resource for monitoring"""
        self.resources.append(weakref.ref(resource))
    
    def add_cleanup_callback(self, callback: Callable):
        """Add cleanup callback"""
        self.cleanup_callbacks.append(callback)
    
    def remove_cleanup_callback(self, callback: Callable):
        """Remove cleanup callback"""
        try:
            self.cleanup_callbacks.remove(callback)
        except ValueError:
            pass

# ========================================
# DATABASE CONNECTION POOL OPTIMIZATION
# ========================================

class OptimizedConnectionPool:
    """Optimized database connection pool"""
    
    def __init__(self, 
                 database_url: str,
                 min_connections: int = 5,
                 max_connections: int = 20,
                 connection_timeout: int = 30):
        
        self.database_url = database_url
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.pool = None
        self.logger = logging.getLogger(__name__)
        self._initialized = False
    
    async def initialize(self):
        """Initialize connection pool"""
        if not self._initialized:
            try:
                import asyncpg
                
                self.pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=self.min_connections,
                    max_size=self.max_connections,
                    command_timeout=self.connection_timeout,
                    server_settings={
                        'jit': 'off',  # Disable JIT for faster simple queries
                        'application_name': 'ai_assistant_ecosystem'
                    }
                )
                
                self._initialized = True
                self.logger.info(f"Database pool initialized: {self.min_connections}-{self.max_connections} connections")
                
            except ImportError:
                self.logger.warning("asyncpg not available, using mock pool")
                self.pool = MockConnectionPool()
                self._initialized = True
            except Exception as e:
                self.logger.error(f"Failed to initialize database pool: {e}")
                raise
    
    async def get_connection(self):
        """Get connection from pool"""
        if not self._initialized:
            await self.initialize()
        
        if hasattr(self.pool, 'acquire'):
            return self.pool.acquire()
        else:
            return MockConnection()
    
    async def execute_query(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute query with connection pooling"""
        async with await self.get_connection() as conn:
            if hasattr(conn, 'fetch'):
                result = await conn.fetch(query, *args)
                return [dict(row) for row in result]
            else:
                # Mock implementation
                return []
    
    async def execute_batch(self, query: str, args_list: List[tuple]) -> int:
        """Execute batch query"""
        async with await self.get_connection() as conn:
            if hasattr(conn, 'executemany'):
                return await conn.executemany(query, args_list)
            else:
                # Mock implementation
                return len(args_list)
    
    async def close(self):
        """Close connection pool"""
        if self.pool and hasattr(self.pool, 'close'):
            await self.pool.close()
        self._initialized = False

class MockConnectionPool:
    """Mock connection pool for testing"""
    
    def acquire(self):
        return MockConnection()

class MockConnection:
    """Mock database connection"""
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def fetch(self, query: str, *args):
        return []
    
    async def executemany(self, query: str, args_list: List[tuple]):
        return len(args_list)

# ========================================
# PERFORMANCE MONITORING
# ========================================

@dataclass
class PerformanceMetrics:
    """Performance metrics data"""
    operation_name: str
    duration_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None

class PerformanceMonitor:
    """Performance monitoring and optimization"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics: List[PerformanceMetrics] = []
        self.max_metrics = 10000
        self.slow_operation_threshold_ms = 1000
    
    async def monitor_operation(self, operation_name: str, operation: Callable, *args, **kwargs):
        """Monitor operation performance"""
        
        start_time = time.time()
        start_memory = psutil.virtual_memory().used / 1024 / 1024
        start_cpu = psutil.cpu_percent()
        
        success = True
        error_message = None
        result = None
        
        try:
            if asyncio.iscoroutinefunction(operation):
                result = await operation(*args, **kwargs)
            else:
                result = operation(*args, **kwargs)
        except Exception as e:
            success = False
            error_message = str(e)
            raise
        finally:
            # Calculate metrics
            duration_ms = (time.time() - start_time) * 1000
            end_memory = psutil.virtual_memory().used / 1024 / 1024
            end_cpu = psutil.cpu_percent()
            
            metrics = PerformanceMetrics(
                operation_name=operation_name,
                duration_ms=duration_ms,
                memory_usage_mb=end_memory - start_memory,
                cpu_usage_percent=(start_cpu + end_cpu) / 2,
                timestamp=datetime.now(),
                success=success,
                error_message=error_message
            )
            
            self.metrics.append(metrics)
            
            # Maintain metrics limit
            if len(self.metrics) > self.max_metrics:
                self.metrics = self.metrics[-self.max_metrics:]
            
            # Log slow operations
            if duration_ms > self.slow_operation_threshold_ms:
                self.logger.warning(
                    f"Slow operation detected: {operation_name} took {duration_ms:.2f}ms"
                )
        
        return result
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        
        if not self.metrics:
            return {"message": "No performance data available"}
        
        # Calculate averages
        total_operations = len(self.metrics)
        successful_operations = len([m for m in self.metrics if m.success])
        
        avg_duration = sum(m.duration_ms for m in self.metrics) / total_operations
        avg_memory = sum(m.memory_usage_mb for m in self.metrics) / total_operations
        avg_cpu = sum(m.cpu_usage_percent for m in self.metrics) / total_operations
        
        # Find slowest operations
        slowest_operations = sorted(
            self.metrics, 
            key=lambda x: x.duration_ms, 
            reverse=True
        )[:10]
        
        # Operation frequency
        operation_counts = {}
        for metric in self.metrics:
            operation_counts[metric.operation_name] = operation_counts.get(metric.operation_name, 0) + 1
        
        return {
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "success_rate": (successful_operations / total_operations) * 100,
            "average_duration_ms": avg_duration,
            "average_memory_usage_mb": avg_memory,
            "average_cpu_usage_percent": avg_cpu,
            "slowest_operations": [
                {
                    "operation": op.operation_name,
                    "duration_ms": op.duration_ms,
                    "timestamp": op.timestamp.isoformat()
                }
                for op in slowest_operations
            ],
            "operation_frequency": operation_counts
        }

# ========================================
# GLOBAL INSTANCES
# ========================================

# Global performance optimization instances
event_manager = EventManager()
resource_manager = ResourceManager()
performance_monitor = PerformanceMonitor()

# Helper functions for migration from sleep patterns
async def wait_for_system_ready(timeout: float = 30.0) -> bool:
    """Wait for system to be ready instead of sleeping"""
    event = await event_manager.wait_for_event(EventType.SYSTEM_READY, timeout)
    return event is not None

async def wait_for_database_ready(timeout: float = 30.0) -> bool:
    """Wait for database to be ready instead of sleeping"""
    event = await event_manager.wait_for_event(EventType.DATABASE_CONNECTED, timeout)
    return event is not None

async def wait_for_persona_ready(timeout: float = 30.0) -> bool:
    """Wait for personas to be ready instead of sleeping"""
    event = await event_manager.wait_for_event(EventType.PERSONA_INITIALIZED, timeout)
    return event is not None

def signal_system_ready(source: str = "system"):
    """Signal that system is ready"""
    event_manager.trigger_event(EventType.SYSTEM_READY, source=source)

def signal_database_ready(source: str = "database"):
    """Signal that database is ready"""
    event_manager.trigger_event(EventType.DATABASE_CONNECTED, source=source)

def signal_persona_ready(source: str = "persona"):
    """Signal that personas are ready"""
    event_manager.trigger_event(EventType.PERSONA_INITIALIZED, source=source)

# Export all performance optimization components
__all__ = [
    "EventType",
    "Event", 
    "EventManager",
    "ResourceStats",
    "ResourceManager",
    "OptimizedConnectionPool",
    "PerformanceMetrics",
    "PerformanceMonitor",
    "event_manager",
    "resource_manager", 
    "performance_monitor",
    "wait_for_system_ready",
    "wait_for_database_ready",
    "wait_for_persona_ready",
    "signal_system_ready",
    "signal_database_ready",
    "signal_persona_ready"
]

