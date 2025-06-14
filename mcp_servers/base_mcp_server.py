"""
Base MCP Server Template for Orchestra AI
Following patterns from .cursor/iac-agent.md
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from abc import ABC, abstractmethod

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import structlog
import aiohttp
import redis.asyncio as redis
from prometheus_client import Counter, Histogram, generate_latest

# Structured logging setup
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


# Metrics
request_count = Counter('mcp_requests_total', 'Total MCP requests', ['server', 'method'])
request_duration = Histogram('mcp_request_duration_seconds', 'MCP request duration', ['server', 'method'])
health_check_count = Counter('mcp_health_checks_total', 'Total health checks', ['server'])


class HealthStatus(BaseModel):
    status: str
    service: str
    port: int
    environment: str
    timestamp: str
    version: str = "1.0.0"
    connections: Dict[str, bool]
    uptime_seconds: float
    metrics: Optional[Dict[str, Any]] = None


class ServiceInfo(BaseModel):
    name: str
    endpoint: str
    capabilities: List[str]
    status: str
    last_check: str


class BaseMCPServer(ABC):
    """
    Standard MCP Server Implementation
    Following patterns from .cursor/iac-agent.md
    """
    
    def __init__(self, 
                 port: int, 
                 name: str, 
                 capabilities: List[str],
                 environment: str = "development"):
        self.port = port
        self.name = name
        self.capabilities = capabilities
        self.environment = environment
        self.health_endpoint = f"http://localhost:{port}/health"
        self.start_time = datetime.now()
        
        # FastAPI app
        self.app = FastAPI(title=f"MCP {name} Server", version="1.0.0")
        
        # Connections
        self.redis_client: Optional[redis.Redis] = None
        self.registry_client: Optional[aiohttp.ClientSession] = None
        
        # Setup routes
        self._setup_routes()
        
        logger.info(f"Initializing {name} MCP Server",
                   port=port,
                   capabilities=capabilities,
                   environment=environment)
    
    def _setup_routes(self):
        """Setup standard MCP routes"""
        
        @self.app.on_event("startup")
        async def startup():
            await self.start_server()
        
        @self.app.on_event("shutdown")
        async def shutdown():
            await self.stop_server()
        
        @self.app.get("/health", response_model=HealthStatus)
        async def health_check():
            """Comprehensive health check implementation"""
            health_check_count.labels(server=self.name).inc()
            return await self.health_check()
        
        @self.app.get("/ready")
        async def readiness_check():
            """Readiness probe for Kubernetes"""
            connections = await self._check_connections()
            if all(connections.values()):
                return {"ready": True}
            raise HTTPException(status_code=503, detail="Not ready")
        
        @self.app.get("/metrics")
        async def metrics():
            """Prometheus metrics endpoint"""
            return generate_latest()
        
        # Add custom routes
        self._setup_custom_routes()
    
    @abstractmethod
    def _setup_custom_routes(self):
        """Setup server-specific routes"""
        pass
    
    async def start_server(self) -> None:
        """Start the MCP server with proper error handling"""
        try:
            logger.info(f"Starting {self.name} server", port=self.port)
            
            # Initialize connections
            await self._initialize_connections()
            
            # Register with service registry
            await self.register_with_registry()
            
            # Custom startup logic
            await self._custom_startup()
            
            logger.info(f"{self.name} server started successfully",
                       port=self.port,
                       health_endpoint=self.health_endpoint)
            
        except Exception as e:
            logger.error(f"Failed to start {self.name} server",
                        error=str(e),
                        exc_info=True)
            raise
    
    async def stop_server(self) -> None:
        """Graceful shutdown"""
        try:
            logger.info(f"Stopping {self.name} server")
            
            # Deregister from service registry
            await self.deregister_from_registry()
            
            # Close connections
            await self._close_connections()
            
            # Custom shutdown logic
            await self._custom_shutdown()
            
            logger.info(f"{self.name} server stopped")
            
        except Exception as e:
            logger.error(f"Error during {self.name} server shutdown",
                        error=str(e),
                        exc_info=True)
    
    async def health_check(self) -> HealthStatus:
        """Comprehensive health check implementation"""
        try:
            connections = await self._check_connections()
            uptime = (datetime.now() - self.start_time).total_seconds()
            
            # Get custom metrics
            metrics = await self._get_health_metrics()
            
            return HealthStatus(
                status="healthy",
                service=self.name,
                port=self.port,
                environment=self.environment,
                timestamp=datetime.now().isoformat(),
                connections=connections,
                uptime_seconds=uptime,
                metrics=metrics
            )
            
        except Exception as e:
            logger.error(f"Health check failed for {self.name}",
                        error=str(e),
                        exc_info=True)
            return HealthStatus(
                status="unhealthy",
                service=self.name,
                port=self.port,
                environment=self.environment,
                timestamp=datetime.now().isoformat(),
                connections={},
                uptime_seconds=0,
                metrics={"error": str(e)}
            )
    
    async def register_with_registry(self) -> None:
        """Register server with MCP registry"""
        if self.environment == "development":
            logger.info("Skipping registry registration in development")
            return
            
        try:
            registry_url = "http://localhost:8006/register"
            service_info = {
                "name": self.name,
                "endpoint": f"http://localhost:{self.port}",
                "capabilities": self.capabilities,
                "health_endpoint": self.health_endpoint
            }
            
            if not self.registry_client:
                self.registry_client = aiohttp.ClientSession()
            
            async with self.registry_client.post(registry_url, json=service_info) as resp:
                if resp.status == 200:
                    logger.info(f"Registered {self.name} with service registry")
                else:
                    logger.warning(f"Failed to register with service registry",
                                 status=resp.status)
                    
        except Exception as e:
            logger.warning(f"Could not register with service registry",
                         error=str(e))
    
    async def deregister_from_registry(self) -> None:
        """Deregister server from MCP registry"""
        if self.environment == "development":
            return
            
        try:
            registry_url = f"http://localhost:8006/deregister/{self.name}"
            
            if self.registry_client:
                async with self.registry_client.delete(registry_url) as resp:
                    if resp.status == 200:
                        logger.info(f"Deregistered {self.name} from service registry")
                        
        except Exception as e:
            logger.warning(f"Could not deregister from service registry",
                         error=str(e))
    
    async def _initialize_connections(self) -> None:
        """Initialize standard connections"""
        # Redis connection
        try:
            self.redis_client = redis.Redis(
                host="localhost",
                port=6379,
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self.redis_client = None
    
    async def _close_connections(self) -> None:
        """Close all connections"""
        if self.redis_client:
            await self.redis_client.close()
            
        if self.registry_client:
            await self.registry_client.close()
    
    async def _check_connections(self) -> Dict[str, bool]:
        """Check status of all connections"""
        connections = {}
        
        # Check Redis
        if self.redis_client:
            try:
                await self.redis_client.ping()
                connections["redis"] = True
            except:
                connections["redis"] = False
        else:
            connections["redis"] = False
        
        # Let subclasses add their checks
        custom_connections = await self._check_custom_connections()
        connections.update(custom_connections)
        
        return connections
    
    # Abstract methods for subclasses
    @abstractmethod
    async def _custom_startup(self) -> None:
        """Custom startup logic for specific server"""
        pass
    
    @abstractmethod
    async def _custom_shutdown(self) -> None:
        """Custom shutdown logic for specific server"""
        pass
    
    @abstractmethod
    async def _check_custom_connections(self) -> Dict[str, bool]:
        """Check custom connections specific to server"""
        pass
    
    @abstractmethod
    async def _get_health_metrics(self) -> Dict[str, Any]:
        """Get custom health metrics for server"""
        pass


class MCPServiceRegistry:
    """
    Service Discovery Pattern
    Central registry for all MCP services
    """
    
    def __init__(self):
        self.services: Dict[str, ServiceInfo] = {}
        self.app = FastAPI(title="MCP Service Registry", version="1.0.0")
        self._setup_routes()
        
        logger.info("Initializing MCP Service Registry")
    
    def _setup_routes(self):
        @self.app.post("/register")
        async def register_service(service_info: dict) -> dict:
            """Register MCP service for discovery"""
            try:
                service = ServiceInfo(
                    name=service_info["name"],
                    endpoint=service_info["endpoint"],
                    capabilities=service_info["capabilities"],
                    status="active",
                    last_check=datetime.now().isoformat()
                )
                self.services[service.name] = service
                logger.info(f"Registered service: {service.name}")
                return {"status": "registered", "service": service.name}
            except Exception as e:
                logger.error(f"Failed to register service", error=str(e))
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.delete("/deregister/{service_name}")
        async def deregister_service(service_name: str) -> dict:
            """Deregister MCP service"""
            if service_name in self.services:
                del self.services[service_name]
                logger.info(f"Deregistered service: {service_name}")
                return {"status": "deregistered", "service": service_name}
            raise HTTPException(status_code=404, detail="Service not found")
        
        @self.app.get("/services")
        async def list_services() -> List[ServiceInfo]:
            """List all registered services"""
            return list(self.services.values())
        
        @self.app.get("/discover/{capability}")
        async def discover_by_capability(capability: str) -> List[ServiceInfo]:
            """Discover services by capability"""
            return [
                service for service in self.services.values()
                if capability in service.capabilities
            ]
        
        @self.app.get("/health/{service_name}")
        async def check_service_health(service_name: str) -> dict:
            """Check health of specific service"""
            if service_name not in self.services:
                raise HTTPException(status_code=404, detail="Service not found")
            
            service = self.services[service_name]
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{service.endpoint}/health", timeout=5) as resp:
                        if resp.status == 200:
                            service.status = "healthy"
                        else:
                            service.status = "unhealthy"
            except:
                service.status = "unreachable"
            
            service.last_check = datetime.now().isoformat()
            return {"service": service_name, "status": service.status}


# Port Allocation Strategy (from .cursor/iac-agent.md)
MCP_PORT_ALLOCATION = {
    "memory": 8003,
    "tools-registry": 8006,
    "code-intelligence": 8007,
    "git-intelligence": 8008,
    "infrastructure": 8009,
    # 8010-8019: Reserved for future MCP servers
    # 8020-8029: Development/Testing MCP servers
}


def get_next_available_port(start=8010, end=8020) -> int:
    """Get next available port in range"""
    import socket
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return port
            except:
                continue
    raise Exception(f"No available ports in range {start}-{end}") 