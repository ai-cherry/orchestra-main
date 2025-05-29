#!/usr/bin/env python3
"""
Base MCP Server

Provides a standard base class for all MCP servers with:
- Health check endpoints
- Dynamic configuration
- Self-healing capabilities
"""

import asyncio
import logging
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

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
        "exponential_base": 2,
    }


class HealthStatus(BaseModel):
    """Health status model."""

    status: str  # healthy, degraded, unhealthy
    timestamp: datetime
    details: Dict[str, Any]
    uptime_seconds: float
    last_error: Optional[str] = None


class BaseMCPServer(ABC):
    """Base class for all MCP servers (no GCP integration)."""

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.start_time = time.time()
        self.health_status = HealthStatus(
            status="initializing",
            timestamp=datetime.utcnow(),
            details={},
            uptime_seconds=0,
        )
        self._health_check_task = None
        self._shutdown = False

        # Validate required secrets
        self._validate_secrets()

    def _validate_secrets(self):
        """Validate that all required secrets are present."""
        missing = []
        for secret in self.config.required_secrets:
            if not os.getenv(secret):
                missing.append(secret)

        if missing:
            raise ValueError(f"Missing required secrets: {', '.join(missing)}")

        logger.info(f"All required secrets validated for {self.config.name}")

    # No-op: GCP client initialization removed.
    # All event publishing and service registration is stack-agnostic or handled by adapters.

    async def start(self):
        """Start the MCP server."""
        logger.info(f"Starting {self.config.name} MCP server...")

        # Start health check loop
        self._health_check_task = asyncio.create_task(self._health_check_loop())

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

        # Stop server-specific logic
        await self.on_stop()

        logger.info(f"{self.config.name} MCP server stopped")

    # GCP Service Directory registration/deregistration removed.

    # Pub/Sub event publishing removed. Use stack-native event hooks or logging.

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
                await self.publish_event(
                    "health_check",
                    {
                        "status": self.health_status.status,
                        "details": health_details,
                        "uptime_seconds": self.health_status.uptime_seconds,
                    },
                )

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

            # Re-initialize stack-native clients if needed (no GCP).

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
        exponential_base: float = 2.0,
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
            return {"example_check": {"healthy": True, "message": "All good"}}

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
        project_id=os.getenv("PROJECT_ID", "orchestra-local"),
    )

    server = ExampleMCPServer(config)
    asyncio.run(server.start())
