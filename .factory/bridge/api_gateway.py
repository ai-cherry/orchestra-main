"""
Factory AI Bridge API Gateway.

This module provides the main API gateway for Factory AI integration,
handling routing, authentication, and communication between Factory AI
Droids and the existing MCP infrastructure.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import aiohttp
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class DroidType(str, Enum):
    """Available Factory AI Droid types."""

    ARCHITECT = "architect"
    CODE = "code"
    DEBUG = "debug"
    RELIABILITY = "reliability"
    KNOWLEDGE = "knowledge"

class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class CircuitBreakerState:
    """Circuit breaker state for fault tolerance."""

    failures: int = 0
    last_failure_time: Optional[float] = None
    is_open: bool = False
    half_open_attempts: int = 0

class FactoryRequest(BaseModel):
    """Request model for Factory AI operations."""

    droid: DroidType
    task: str
    context: Dict[str, Any]
    options: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)
    timeout: Optional[int] = Field(default=30, ge=1, le=300)

class FactoryResponse(BaseModel):
    """Response model for Factory AI operations."""

    task_id: str
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    processing_time: Optional[float] = None

class FactoryBridgeGateway:
    """Main gateway for Factory AI Bridge operations."""

    def __init__(
        self,
        factory_api_key: str,
        factory_base_url: str = "https://api.factoryai.com/v1",
        mcp_servers: Optional[Dict[str, str]] = None,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: int = 60,
    ):
        """Initialize the Factory Bridge Gateway.

        Args:
            factory_api_key: API key for Factory AI
            factory_base_url: Base URL for Factory AI API
            mcp_servers: Mapping of droid types to MCP server endpoints
            circuit_breaker_threshold: Number of failures before opening circuit
            circuit_breaker_timeout: Seconds before attempting to close circuit
        """
        self.factory_api_key = factory_api_key
        self.factory_base_url = factory_base_url
        self.mcp_servers = mcp_servers or {}
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout

        # Circuit breakers per droid
        self.circuit_breakers: Dict[DroidType, CircuitBreakerState] = {
            droid: CircuitBreakerState() for droid in DroidType
        }

        # Request tracking
        self.active_requests: Dict[UUID, FactoryRequest] = {}
        self.request_history: List[Tuple[UUID, FactoryResponse]] = []

        # Performance metrics
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
        }

        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.factory_api_key}",
                "Content-Type": "application/json",
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    def _check_circuit_breaker(self, droid: DroidType) -> bool:
        """Check if circuit breaker allows request.

        Args:
            droid: Droid type to check

        Returns:
            True if request allowed, False if circuit is open
        """
        breaker = self.circuit_breakers[droid]

        if not breaker.is_open:
            return True

        # Check if timeout has passed
        if breaker.last_failure_time:
            elapsed = time.time() - breaker.last_failure_time
            if elapsed >= self.circuit_breaker_timeout:
                # Try half-open state
                breaker.is_open = False
                breaker.half_open_attempts = 0
                return True

        return False

    def _record_success(self, droid: DroidType):
        """Record successful request for circuit breaker."""
        breaker = self.circuit_breakers[droid]
        breaker.failures = 0
        breaker.half_open_attempts = 0

    def _record_failure(self, droid: DroidType):
        """Record failed request for circuit breaker."""
        breaker = self.circuit_breakers[droid]
        breaker.failures += 1
        breaker.last_failure_time = time.time()

        if breaker.failures >= self.circuit_breaker_threshold:
            breaker.is_open = True
            logger.warning(f"Circuit breaker opened for {droid}")

    async def process_request(self, request: FactoryRequest) -> FactoryResponse:
        """Process a Factory AI request.

        Args:
            request: Factory AI request

        Returns:
            Factory AI response

        Raises:
            HTTPException: If request processing fails
        """
        # Check circuit breaker
        if not self._check_circuit_breaker(request.droid):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Circuit breaker open for {request.droid}",
            )

        task_id = uuid4()
        self.active_requests[task_id] = request
        start_time = time.time()

        try:
            # Update metrics
            self.metrics["total_requests"] += 1

            # Prepare request payload
            payload = {
                "droid": request.droid.value,
                "task": request.task,
                "context": request.context,
                "options": request.options,
                "priority": request.priority,
            }

            # Make request to Factory AI
            async with self.session.post(
                f"{self.factory_base_url}/droids/{request.droid.value}/execute",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=request.timeout),
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    processing_time = time.time() - start_time

                    # Record success
                    self._record_success(request.droid)
                    self.metrics["successful_requests"] += 1
                    self._update_average_response_time(processing_time)

                    factory_response = FactoryResponse(
                        task_id=str(task_id),
                        status=TaskStatus.COMPLETED,
                        result=result,
                        processing_time=processing_time,
                        metadata={
                            "droid": request.droid.value,
                            "task": request.task,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                    )

                    # Store in history
                    self.request_history.append((task_id, factory_response))
                    if len(self.request_history) > 1000:
                        self.request_history.pop(0)

                    return factory_response

                else:
                    error_text = await response.text()
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Factory AI error: {error_text}",
                    )

        except asyncio.TimeoutError:
            self._record_failure(request.droid)
            self.metrics["failed_requests"] += 1
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Request timeout after {request.timeout} seconds",
            )

        except Exception as e:
            self._record_failure(request.droid)
            self.metrics["failed_requests"] += 1
            logger.error(f"Request processing error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )

        finally:
            # Clean up active request
            self.active_requests.pop(task_id, None)

    async def fallback_to_mcp(self, request: FactoryRequest) -> FactoryResponse:
        """Fallback to MCP server if Factory AI is unavailable.

        Args:
            request: Original Factory AI request

        Returns:
            Response from MCP server
        """
        mcp_endpoint = self.mcp_servers.get(request.droid)
        if not mcp_endpoint:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=f"No MCP fallback configured for {request.droid}",
            )

        # Transform request for MCP
        mcp_payload = self._transform_to_mcp_format(request)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    mcp_endpoint,
                    json=mcp_payload,
                    timeout=aiohttp.ClientTimeout(total=request.timeout),
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return FactoryResponse(
                            task_id=str(uuid4()),
                            status=TaskStatus.COMPLETED,
                            result=self._transform_from_mcp_format(result),
                            metadata={
                                "fallback": True,
                                "mcp_server": mcp_endpoint,
                            },
                        )
                    else:
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"MCP fallback error: {await response.text()}",
                        )

        except Exception as e:
            logger.error(f"MCP fallback error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"MCP fallback failed: {str(e)}",
            )

    def _transform_to_mcp_format(self, request: FactoryRequest) -> Dict[str, Any]:
        """Transform Factory AI request to MCP format."""
        # This would be customized based on actual MCP protocol
        return {
            "method": f"{request.droid.value}.{request.task}",
            "params": {
                "context": request.context,
                "options": request.options,
            },
            "id": str(uuid4()),
        }

    def _transform_from_mcp_format(self, mcp_response: Dict[str, Any]) -> Dict[str, Any]:
        """Transform MCP response to Factory AI format."""
        # This would be customized based on actual MCP protocol
        return mcp_response.get("result", {})

    def _update_average_response_time(self, new_time: float):
        """Update average response time metric."""
        total = self.metrics["successful_requests"]
        if total == 1:
            self.metrics["average_response_time"] = new_time
        else:
            current_avg = self.metrics["average_response_time"]
            self.metrics["average_response_time"] = (current_avg * (total - 1) + new_time) / total

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return {
            **self.metrics,
            "circuit_breakers": {
                droid.value: {
                    "is_open": breaker.is_open,
                    "failures": breaker.failures,
                }
                for droid, breaker in self.circuit_breakers.items()
            },
            "active_requests": len(self.active_requests),
        }

    def get_request_history(self, limit: int = 100) -> List[Tuple[str, FactoryResponse]]:
        """Get recent request history."""
        return [(str(task_id), response) for task_id, response in self.request_history[-limit:]]

# FastAPI app setup
app = FastAPI(
    title="Factory AI Bridge Gateway",
    version="1.0.0",
    description="Bridge between Factory AI Droids and MCP infrastructure",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global gateway instance (initialized on startup)
gateway: Optional[FactoryBridgeGateway] = None

@app.on_event("startup")
async def startup_event():
    """Initialize gateway on startup."""
    global gateway
    # This would load from environment/config
    gateway = FactoryBridgeGateway(
        factory_api_key="your-api-key",
        mcp_servers={
            DroidType.ARCHITECT: "http://localhost:8001/mcp/orchestrator",
            DroidType.CODE: "http://localhost:8002/mcp/tools",
            DroidType.DEBUG: "http://localhost:8002/mcp/tools",
            DroidType.RELIABILITY: "http://localhost:8003/mcp/deployment",
            DroidType.KNOWLEDGE: "http://localhost:8004/mcp/memory",
        },
    )

@app.post("/api/v1/execute", response_model=FactoryResponse)
async def execute_task(request: FactoryRequest) -> FactoryResponse:
    """Execute a Factory AI task."""
    if not gateway:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gateway not initialized",
        )

    try:
        async with gateway:
            return await gateway.process_request(request)
    except HTTPException:
        # Try fallback to MCP
        try:
            async with gateway:
                return await gateway.fallback_to_mcp(request)
        except Exception:
            raise

@app.get("/api/v1/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Get gateway performance metrics."""
    if not gateway:
        return {"error": "Gateway not initialized"}
    return gateway.get_metrics()

@app.get("/api/v1/history")
async def get_history(limit: int = 100) -> List[Dict[str, Any]]:
    """Get request history."""
    if not gateway:
        return []
    return [
        {"task_id": task_id, "response": response.dict()} for task_id, response in gateway.get_request_history(limit)
    ]

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}
