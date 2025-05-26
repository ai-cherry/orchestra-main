#!/usr/bin/env python
"""
SuperAGI Integration for Orchestra AI
=====================================
This script integrates SuperAGI with the existing Orchestra system,
providing autonomous agent capabilities with memory management.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Optional, Any

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import redis.asyncio as redis
from google.cloud import firestore, pubsub_v1

# Add Orchestra modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from orchestra.memory.memory_manager import MemoryManager
from orchestra.personas.persona_manager import PersonaManager
from orchestra_adapter import OrchestraAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SuperAGI Orchestra Integration",
    description="Autonomous AI agents with Orchestra integration",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
redis_client: Optional[redis.Redis] = None
firestore_client: Optional[firestore.Client] = None
pubsub_publisher: Optional[pubsub_v1.PublisherClient] = None
orchestra_adapter: Optional[OrchestraAdapter] = None


# Request/Response models
class AgentRequest(BaseModel):
    """Request model for agent execution"""

    agent_id: str = Field(..., description="ID of the agent to execute")
    task: str = Field(..., description="Task for the agent to perform")
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Additional context"
    )
    persona_id: Optional[str] = Field(None, description="Persona to use for the agent")
    memory_context: bool = Field(True, description="Whether to include memory context")


class AgentResponse(BaseModel):
    """Response model for agent execution"""

    agent_id: str
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    version: str
    services: Dict[str, str]


# Dependency injection
async def get_redis() -> redis.Redis:
    """Get Redis client"""
    return redis_client


async def get_firestore() -> firestore.Client:
    """Get Firestore client"""
    return firestore_client


async def get_orchestra() -> OrchestraAdapter:
    """Get Orchestra adapter"""
    return orchestra_adapter


# API endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    services = {}

    # Check Redis
    try:
        await redis_client.ping()
        services["redis"] = "healthy"
    except Exception as e:
        services["redis"] = f"unhealthy: {str(e)}"

    # Check Firestore
    try:
        # Simple read to verify connection
        firestore_client.collection("_health").document("check").get()
        services["firestore"] = "healthy"
    except Exception as e:
        services["firestore"] = f"unhealthy: {str(e)}"

    # Check Orchestra
    services["orchestra"] = "healthy" if orchestra_adapter else "not initialized"

    overall_status = (
        "healthy" if all(v == "healthy" for v in services.values()) else "degraded"
    )

    return HealthResponse(status=overall_status, version="1.0.0", services=services)


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    if not all([redis_client, firestore_client, orchestra_adapter]):
        raise HTTPException(status_code=503, detail="Service not ready")
    return {"status": "ready"}


@app.post("/agents/execute", response_model=AgentResponse)
async def execute_agent(
    request: AgentRequest,
    redis_conn: redis.Redis = Depends(get_redis),
    orchestra: OrchestraAdapter = Depends(get_orchestra),
):
    """Execute an agent with the given task"""
    try:
        # Create task ID
        task_id = f"{request.agent_id}_{asyncio.get_event_loop().time()}"

        # Get memory context if requested
        memory_context = {}
        if request.memory_context:
            memory_key = f"agent:{request.agent_id}:memory"
            memory_data = await redis_conn.get(memory_key)
            if memory_data:
                import json

                memory_context = json.loads(memory_data)

        # Prepare agent context
        agent_context = {
            "task": request.task,
            "memory": memory_context,
            "persona_id": request.persona_id,
            **request.context,
        }

        # Execute through Orchestra adapter
        result = await orchestra.execute_agent(
            agent_id=request.agent_id, context=agent_context
        )

        # Store result in memory
        if result.get("store_memory", True):
            memory_key = f"agent:{request.agent_id}:memory"
            memory_data = {
                "last_task": request.task,
                "last_result": result.get("output"),
                "timestamp": asyncio.get_event_loop().time(),
            }
            await redis_conn.setex(
                memory_key, 3600, json.dumps(memory_data)  # 1 hour TTL
            )

        # Publish event
        if pubsub_publisher:
            topic_path = pubsub_publisher.topic_path(
                os.environ.get("GCP_PROJECT_ID"), "orchestra-events"
            )
            event_data = {
                "event_type": "agent_execution",
                "agent_id": request.agent_id,
                "task_id": task_id,
                "status": "completed",
            }
            pubsub_publisher.publish(topic_path, json.dumps(event_data).encode("utf-8"))

        return AgentResponse(
            agent_id=request.agent_id,
            task_id=task_id,
            status="completed",
            result=result,
            metadata={
                "execution_time": result.get("execution_time", 0),
                "tokens_used": result.get("tokens_used", 0),
            },
        )

    except Exception as e:
        logger.error(f"Agent execution failed: {str(e)}")
        return AgentResponse(
            agent_id=request.agent_id, task_id=task_id, status="failed", error=str(e)
        )


@app.get("/agents")
async def list_agents(orchestra: OrchestraAdapter = Depends(get_orchestra)):
    """List available agents"""
    agents = await orchestra.list_agents()
    return {"agents": agents}


@app.get("/agents/{agent_id}")
async def get_agent(
    agent_id: str, orchestra: OrchestraAdapter = Depends(get_orchestra)
):
    """Get agent details"""
    agent = await orchestra.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@app.post("/agents/{agent_id}/tools")
async def add_agent_tool(
    agent_id: str,
    tool_config: Dict[str, Any],
    orchestra: OrchestraAdapter = Depends(get_orchestra),
):
    """Add a tool to an agent"""
    result = await orchestra.add_agent_tool(agent_id, tool_config)
    return {"status": "success", "result": result}


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global redis_client, firestore_client, pubsub_publisher, orchestra_adapter

    logger.info("Starting SuperAGI Orchestra Integration...")

    # Initialize Redis
    redis_host = os.environ.get("REDIS_HOST", "localhost")
    redis_port = int(os.environ.get("REDIS_PORT", 6379))
    redis_client = await redis.from_url(f"redis://{redis_host}:{redis_port}")
    logger.info(f"Connected to Redis at {redis_host}:{redis_port}")

    # Initialize Firestore
    project_id = os.environ.get("GCP_PROJECT_ID")
    if project_id:
        firestore_client = firestore.Client(project=project_id)
        logger.info(f"Connected to Firestore in project {project_id}")
    else:
        logger.warning("GCP_PROJECT_ID not set, Firestore disabled")

    # Initialize Pub/Sub
    if project_id:
        pubsub_publisher = pubsub_v1.PublisherClient()
        logger.info("Initialized Pub/Sub publisher")

    # Initialize Orchestra adapter
    orchestra_adapter = OrchestraAdapter(
        redis_client=redis_client,
        firestore_client=firestore_client,
        config={
            "memory_manager": MemoryManager(),
            "persona_manager": PersonaManager("config/personas.yaml"),
            "max_concurrent_agents": 10,
        },
    )
    await orchestra_adapter.initialize()
    logger.info("Orchestra adapter initialized")

    logger.info("SuperAGI Orchestra Integration started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down SuperAGI Orchestra Integration...")

    if redis_client:
        await redis_client.close()

    if orchestra_adapter:
        await orchestra_adapter.shutdown()

    logger.info("Shutdown complete")


def main():
    """Main entry point"""
    # Get configuration from environment
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8080))
    workers = int(os.environ.get("WORKERS", 4))

    # Run the application
    uvicorn.run(
        "superagi_integration:app",
        host=host,
        port=port,
        workers=workers,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    main()
