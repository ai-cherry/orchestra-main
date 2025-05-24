#!/usr/bin/env python3
"""
Base MCP Server with GCP Integration

Provides a standard base class for all MCP servers with:
- Automatic Service Directory registration
- Pub/Sub event publishing
- Health check endpoints
- Dynamic configuration
- Self-healing capabilities
"""

import asyncio
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

from google.cloud import pubsub_v1
from google.cloud import servicedirectory_v1
from google.api_core import exceptions as gcp_exceptions
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class MCPServerConfig(BaseModel):
    """Configuration for MCP servers."""
    name: str
    version: str = "1.0.0"
    service_type: str
    required_secrets: List[str]
    optional_secrets: List[str] = []
    health_endpoint: str = "/health"
    namespace: str = "orchestra-ai"
    project_id: str
    region: str = "us-central1"
    pubsub_topic: Optional[str] = "mcp-events"
    enable_service_directory: bool = True
    enable_pubsub: bool = True
    health_check_interval: int = 30  # seconds
    retry_config: Dict[str, int] = {
        "max_retries": 3,
        "initial_delay": 1,
        "max_delay": 60,
        "exponential_base": 2
    }


class HealthStatus(BaseModel):
    """Health status model."""
    status: str  # healthy, degraded, unhealthy
    timestamp: datetime
    details: Dict[str, Any]
    uptime_seconds: float
    last_error: Optional[str] = None


class BaseMCPServer(ABC):
    """Base class for all MCP servers with GCP integration."""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.start_time = time.time()
        self.publisher = None
        self.service_client = None
        self.health_status = HealthStatus(
            status="initializing",
            timestamp=datetime.utcnow(),
            details={},
            uptime_seconds=0
        )
        self._health_check_task = None
        self._shutdown = False
        
        # Validate required secrets
        self._validate_secrets()
        
        # Initialize GCP clients
        self._init_gcp_clients()
    
    def _validate_secrets(self):
        """Validate that all required secrets are present."""
        missing = []
        for secret in self.config.required_secrets:
            if not os.getenv(secret):
                missing.append(secret)
        
        if missing:
            raise ValueError(f"Missing required secrets: {', '.join(missing)}")
        
        logger.info(f"All required secrets validated for {self.config.name}")
    
    def _init_gcp_clients(self):
        """Initialize GCP clients."""
        if self.config.enable_pubsub:
            try:
                self.publisher = pubsub_v1.PublisherClient()
                self.topic_path = self.publisher.topic_path(
                    self.config.project_id,
                    self.config.pubsub_topic
                )
                logger.info(f"Initialized Pub/Sub publisher for topic: {self.topic_path}")
            except Exception as e:
                logger.error(f"Failed to initialize Pub/Sub: {e}")
                self.config.enable_pubsub = False
        
        if self.config.enable_service_directory:
            try:
                self.service_client = servicedirectory_v1.RegistrationServiceClient()
                logger.info("Initialized Service Directory client")
            except Exception as e:
                logger.error(f"Failed to initialize Service Directory: {e}")
                self.config.enable_service_directory = False
    
    async def start(self):
        """Start the MCP server."""
        logger.info(f"Starting {self.config.name} MCP server...")
        
        # Register with Service Directory
        await self._register_service()
        
        # Start health check loop
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        # Publish startup event
        await self.publish_event("server_started", {
            "name": self.config.name,
            "version": self.config.version,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Start server-specific logic
        await self.on_start()
        
        self.health_status.status = "healthy"
        logger.info(f"{self.config.name} MCP server started successfully")
    
    async def stop(self):
        """Stop the MCP server."""
        logger.info(f"Stopping {self.config.name} MCP server...")
        self._shutdown = True
        
        # Stop health check
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Deregister from Service Directory
        await self._deregister_service()
        
        # Publish shutdown event
        await self.publish_event("server_stopped", {
            "name": self.config.name,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Stop server-specific logic
        await self.on_stop()
        
        logger.info(f"{self.config.name} MCP server stopped")
    
    async def _register_service(self):
        """Register with GCP Service Directory."""
        if not self.config.enable_service_directory or not self.service_client:
            return
        
        try:
            # Create namespace if it doesn't exist
            namespace_path = f"projects/{self.config.project_id}/locations/{self.config.region}/namespaces/{self.config.namespace}"
            
            try:
                self.service_client.get_namespace(name=namespace_path)
            except gcp_exceptions.NotFound:
                logger.info(f"Creating namespace: {self.config.namespace}")
                self.service_client.create_namespace(
                    parent=f"projects/{self.config.project_id}/locations/{self.config.region}",
                    namespace_id=self.config.namespace,
                    namespace={}
                )
            
            # Register service
            service_id = f"{self.config.name}-{self.config.service_type}"
            service_path = f"{namespace_path}/services/{service_id}"
            
            service = {
                "metadata": {
                    "version": self.config.version,
                    "type": self.config.service_type,
                    "health_endpoint": self.config.health_endpoint,
                    "started_at": datetime.utcnow().isoformat()
                }
            }
            
            try:
                self.service_client.create_service(
                    parent=namespace_path,
                    service_id=service_id,
                    service=service
                )
                logger.info(f"Registered service: {service_id}")
            except gcp_exceptions.AlreadyExists:
                # Update existing service
                self.service_client.update_service(
                    service={
                        "name": service_path,
                        "metadata": service["metadata"]
                    }
                )
                logger.info(f"Updated existing service: {service_id}")
            
            # Register endpoint (if applicable)
            if hasattr(self, 'endpoint_url'):
                endpoint_id = f"{service_id}-endpoint"
                endpoint = {
                    "address": self.endpoint_url,
                    "port": getattr(self, 'port', 8080),
                    "metadata": {
                        "protocol": "https"
                    }
                }
                
                try:
                    self.service_client.create_endpoint(
                        parent=service_path,
                        endpoint_id=endpoint_id,
                        endpoint=endpoint
                    )
                    logger.info(f"Registered endpoint: {endpoint_id}")
                except gcp_exceptions.AlreadyExists:
                    pass
                    
        except Exception as e:
            logger.error(f"Failed to register with Service Directory: {e}")
    
    async def _deregister_service(self):
        """Deregister from GCP Service Directory."""
        if not self.config.enable_service_directory or not self.service_client:
            return
        
        try:
            service_id = f"{self.config.name}-{self.config.service_type}"
            service_path = f"projects/{self.config.project_id}/locations/{self.config.region}/namespaces/{self.config.namespace}/services/{service_id}"
            
            self.service_client.delete_service(name=service_path)
            logger.info(f"Deregistered service: {service_id}")
        except Exception as e:
            logger.error(f"Failed to deregister from Service Directory: {e}")
    
    async def publish_event(self, event_type: str, data: Dict[str, Any]):
        """Publish event to Pub/Sub."""
        if not self.config.enable_pubsub or not self.publisher:
            return
        
        try:
            event = {
                "event_type": event_type,
                "source": self.config.name,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
            
            message = json.dumps(event).encode('utf-8')
            future = self.publisher.publish(self.topic_path, message)
            
            # Wait for publish to complete (with timeout)
            await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, future.result),
                timeout=5.0
            )
            
            logger.debug(f"Published event: {event_type}")
        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")
    
    async def _health_check_loop(self):
        """Periodic health check loop."""
        while not self._shutdown:
            try:
                # Update uptime
                self.health_status.uptime_seconds = time.time() - self.start_time
                self.health_status.timestamp = datetime.utcnow()
                
                # Run custom health check
                health_details = await self.check_health()
                self.health_status.details = health_details
                
                # Determine overall status
                if all(v.get("healthy", False) for v in health_details.values() if isinstance(v, dict)):
                    self.health_status.status = "healthy"
                elif any(v.get("healthy", False) for v in health_details.values() if isinstance(v, dict)):
                    self.health_status.status = "degraded"
                else:
                    self.health_status.status = "unhealthy"
                
                # Publish health status
                await self.publish_event("health_check", {
                    "status": self.health_status.status,
                    "details": health_details,
                    "uptime_seconds": self.health_status.uptime_seconds
                })
                
                # Self-healing
                if self.health_status.status == "unhealthy":
                    await self.attempt_self_heal()
                
            except Exception as e:
                logger.error(f"Health check error: {e}")
                self.health_status.last_error = str(e)
                self.health_status.status = "unhealthy"
            
            await asyncio.sleep(self.config.health_check_interval)
    
    async def attempt_self_heal(self):
        """Attempt to self-heal when unhealthy."""
        logger.warning(f"{self.config.name} attempting self-heal...")
        
        try:
            # Re-validate secrets
            self._validate_secrets()
            
            # Re-initialize GCP clients
            self._init_gcp_clients()
            
            # Call custom self-heal logic
            await self.self_heal()
            
            logger.info(f"{self.config.name} self-heal completed")
        except Exception as e:
            logger.error(f"Self-heal failed: {e}")
    
    def get_health_status(self) -> HealthStatus:
        """Get current health status."""
        return self.health_status
    
    # Abstract methods to be implemented by subclasses
    
    @abstractmethod
    async def on_start(self):
        """Called when server starts. Implement server-specific logic."""
    
    @abstractmethod
    async def on_stop(self):
        """Called when server stops. Implement cleanup logic."""
    
    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """Check server health. Return dict with health details."""
    
    @abstractmethod
    async def self_heal(self):
        """Attempt to self-heal. Implement recovery logic."""
    
    @abstractmethod
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools."""
    
    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool with arguments."""


class RetryHelper:
    """Helper class for retry logic."""
    
    @staticmethod
    async def retry_with_backoff(
        func: Callable,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0
    ):
        """Retry a function with exponential backoff."""
        last_exception = None
        delay = initial_delay
        
        for attempt in range(max_retries + 1):
            try:
                return await func()
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    delay = min(delay * exponential_base, max_delay)
                else:
                    logger.error(f"All {max_retries + 1} attempts failed")
        
        raise last_exception


# Example usage
if __name__ == "__main__":
    # This is just an example implementation
    class ExampleMCPServer(BaseMCPServer):
        async def on_start(self):
            logger.info("Example server starting...")
        
        async def on_stop(self):
            logger.info("Example server stopping...")
        
        async def check_health(self) -> Dict[str, Any]:
            return {
                "example_check": {"healthy": True, "message": "All good"}
            }
        
        async def self_heal(self):
            logger.info("Example self-heal logic")
        
        async def list_tools(self) -> List[Dict[str, Any]]:
            return [{"name": "example_tool", "description": "An example tool"}]
        
        async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
            return f"Called {tool_name} with {arguments}"
    
    # Run example
    config = MCPServerConfig(
        name="example",
        service_type="example",
        required_secrets=[],
        project_id=os.getenv("GOOGLE_CLOUD_PROJECT", "cherry-ai-project")
    )
    
    server = ExampleMCPServer(config)
    asyncio.run(server.start()) 