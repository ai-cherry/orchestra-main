"""
Enhanced base class for all MCP servers with improved error handling,
connection pooling, and monitoring capabilities.
"""

import asyncio
import time
import psutil
import logging
from typing import Any, Dict, List, Optional, Callable, TypeVar
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import backoff
import asyncpg
from prometheus_client import Counter, Histogram, Gauge
from mcp.server import Server
from mcp.server.stdio import stdio_server

T = TypeVar('T')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CircuitState:
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker for preventing cascading failures"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        return (
            self.last_failure_time and
            datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
        )
    
    def _on_success(self):
        """Reset circuit breaker on successful call"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failure and potentially open circuit"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN


class ConnectionPoolManager:
    """Manages database connection pools for optimal performance"""
    
    def __init__(self, dsn: str, min_size: int = 10, max_size: int = 20):
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self._pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self):
        """Initialize connection pool"""
        self._pool = await asyncpg.create_pool(
            self.dsn,
            min_size=self.min_size,
            max_size=self.max_size,
            command_timeout=60,
            max_queries=50000,
            max_inactive_connection_lifetime=300
        )
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire connection from pool"""
        if not self._pool:
            await self.initialize()
        async with self._pool.acquire() as connection:
            yield connection
    
    async def close(self):
        """Close all connections in pool"""
        if self._pool:
            await self._pool.close()


class MCPMetrics:
    """Prometheus metrics for MCP servers"""
    
    def __init__(self, server_name: str):
        self.server_name = server_name
        
        # Define metrics
        self.request_count = Counter(
            f'mcp_{server_name}_requests_total',
            'Total number of requests',
            ['method', 'endpoint', 'status']
        )
        
        self.request_duration = Histogram(
            f'mcp_{server_name}_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint']
        )
        
        self.active_connections = Gauge(
            f'mcp_{server_name}_active_connections',
            'Number of active connections'
        )
        
        self.error_rate = Gauge(
            f'mcp_{server_name}_error_rate',
            'Current error rate'
        )
        
        self.memory_usage = Gauge(
            f'mcp_{server_name}_memory_usage_mb',
            'Memory usage in MB'
        )
    
    def track_request(self, method: str, endpoint: str):
        """Decorator to track request metrics"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                status = 'success'
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    status = 'error'
                    raise
                finally:
                    duration = time.time() - start_time
                    self.request_count.labels(method, endpoint, status).inc()
                    self.request_duration.labels(method, endpoint).observe(duration)
            
            return wrapper
        return decorator


class EnhancedMCPServerBase:
    """Enhanced base class for all MCP servers"""
    
    def __init__(self, server_name: str, version: str = "1.0.0"):
        self.server_name = server_name
        self.version = version
        self.server = Server(server_name)
        
        # Initialize components
        self.metrics = MCPMetrics(server_name)
        self.circuit_breaker = CircuitBreaker()
        self.connection_pool: Optional[ConnectionPoolManager] = None
        
        # Request tracking
        self.request_count = 0
        self.error_count = 0
        self.start_time = time.time()
        
        # Setup base handlers
        self._setup_base_handlers()
    
    def _setup_base_handlers(self):
        """Setup base handlers including health check"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Dict[str, Any]]:
            """List available tools including health check"""
            base_tools = [
                {
                    "name": "health_check",
                    "description": "Get detailed health status of the server",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                    },
                }
            ]
            
            # Add server-specific tools
            custom_tools = await self.get_custom_tools()
            return base_tools + custom_tools
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[Any]:
            """Handle tool calls with metrics and error handling"""
            
            if name == "health_check":
                health_status = await self.get_health_status()
                return [{"type": "text", "text": str(health_status)}]
            
            # Delegate to custom tool handler
            return await self.handle_custom_tool(name, arguments)
    
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        max_time=30
    )
    async def execute_with_retry(
        self, 
        func: Callable[..., T], 
        *args, 
        **kwargs
    ) -> T:
        """Execute function with exponential backoff retry"""
        return await self.circuit_breaker.call(func, *args, **kwargs)
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def _get_connection_count(self) -> int:
        """Get active connection count"""
        if self.connection_pool and self.connection_pool._pool:
            return self.connection_pool._pool.get_size()
        return 0
    
    def _calculate_error_rate(self) -> float:
        """Calculate current error rate"""
        if self.request_count == 0:
            return 0.0
        return self.error_count / self.request_count
    
    def _get_avg_response_time(self) -> float:
        """Get average response time in milliseconds"""
        # This would be calculated from actual metrics
        # For now, return a placeholder
        return 50.0
    
    async def _check_dependencies(self) -> Dict[str, Any]:
        """Check health of dependencies"""
        dependencies = {}
        
        # Check database connection
        if self.connection_pool:
            try:
                async with self.connection_pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                dependencies["database"] = {"status": "healthy"}
            except Exception as e:
                dependencies["database"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return dependencies
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get detailed health status"""
        uptime = time.time() - self.start_time
        
        health_status = {
            "status": "healthy",
            "server_name": self.server_name,
            "version": self.version,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": uptime,
            "metrics": {
                "memory_usage_mb": self._get_memory_usage(),
                "active_connections": self._get_connection_count(),
                "request_count": self.request_count,
                "error_count": self.error_count,
                "error_rate": self._calculate_error_rate(),
                "average_response_time_ms": self._get_avg_response_time(),
                "circuit_breaker_state": self.circuit_breaker.state
            },
            "dependencies": await self._check_dependencies()
        }
        
        # Update Prometheus metrics
        self.metrics.memory_usage.set(health_status["metrics"]["memory_usage_mb"])
        self.metrics.active_connections.set(health_status["metrics"]["active_connections"])
        self.metrics.error_rate.set(health_status["metrics"]["error_rate"])
        
        # Determine overall health
        if health_status["metrics"]["error_rate"] > 0.1:  # 10% error rate
            health_status["status"] = "degraded"
        
        for dep_name, dep_status in health_status["dependencies"].items():
            if dep_status.get("status") != "healthy":
                health_status["status"] = "unhealthy"
                break
        
        return health_status
    
    async def initialize_connection_pool(self, dsn: str):
        """Initialize database connection pool"""
        self.connection_pool = ConnectionPoolManager(dsn)
        await self.connection_pool.initialize()
    
    async def cleanup(self):
        """Cleanup resources on shutdown"""
        if self.connection_pool:
            await self.connection_pool.close()
    
    async def run(self):
        """Run the MCP server with enhanced error handling"""
        try:
            # Perform any initialization
            await self.initialize()
            
            # Run the server
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(read_stream, write_stream)
        except Exception as e:
            logger.error(f"Server {self.server_name} crashed: {e}", exc_info=True)
            raise
        finally:
            await self.cleanup()
    
    # Methods to be implemented by subclasses
    async def initialize(self):
        """Initialize server-specific resources"""
        pass
    
    async def get_custom_tools(self) -> List[Dict[str, Any]]:
        """Get server-specific tools"""
        return []
    
    async def handle_custom_tool(self, name: str, arguments: Dict[str, Any]) -> List[Any]:
        """Handle server-specific tool calls"""
        return [{"type": "text", "text": f"Unknown tool: {name}"}]