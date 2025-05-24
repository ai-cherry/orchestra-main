#!/usr/bin/env python3
"""
MCP Server for Google Cloud Run Management

This server enables Claude 4 to deploy and manage Cloud Run services
through the Model Context Protocol (MCP).
"""

import logging
import os
from typing import Any, Dict, List, Optional

import google.auth
from fastapi import FastAPI, HTTPException
from google.cloud import run_v2
from google.cloud.run_v2 import Container, Service
from pydantic import BaseModel, Field

# --- MCP CONFIG IMPORTS ---
from mcp_server.config.loader import load_config
from mcp_server.config.models import MCPConfig

gcp_config: MCPConfig = load_config()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app for MCP server
app = FastAPI(
    title="GCP Cloud Run MCP Server", description="MCP server for managing Google Cloud Run services", version="1.0.0"
)

# Get configuration from unified config (with env fallback)
PROJECT_ID = getattr(gcp_config, "gcp_project_id", None) or os.getenv("GCP_PROJECT_ID")
REGION = getattr(gcp_config, "gcp_region", None) or os.getenv("GCP_REGION", "us-central1")

# Initialize Cloud Run client
try:
    credentials, project = google.auth.default()
    run_client = run_v2.ServicesClient()
except Exception as e:
    logger.error(f"Failed to initialize Cloud Run client: {e}")
    run_client = None


class DeployRequest(BaseModel):
    """Request model for deploying a service"""

    service_name: str = Field(..., description="Name of the Cloud Run service")
    image: str = Field(..., description="Container image URL")
    env_vars: Optional[Dict[str, str]] = Field(default={}, description="Environment variables")
    memory: str = Field(default="512Mi", description="Memory allocation")
    cpu: str = Field(default="1", description="CPU allocation")
    min_instances: int = Field(default=0, description="Minimum number of instances")
    max_instances: int = Field(default=10, description="Maximum number of instances")


class ServiceStatus(BaseModel):
    """Response model for service status"""

    name: str
    url: Optional[str]
    ready: bool
    latest_revision: Optional[str]


class MCPToolDefinition(BaseModel):
    """MCP tool definition for Claude"""

    name: str
    description: str
    parameters: Dict[str, Any]


@app.get("/mcp/cloud-run/tools")
async def get_tools() -> List[MCPToolDefinition]:
    """Return available tools for Claude to use"""
    return [
        MCPToolDefinition(
            name="deploy_service",
            description="Deploy a new Cloud Run service or update existing one",
            parameters={
                "type": "object",
                "properties": {
                    "service_name": {"type": "string", "description": "Service name"},
                    "image": {"type": "string", "description": "Container image URL"},
                    "env_vars": {"type": "object", "description": "Environment variables"},
                    "memory": {"type": "string", "description": "Memory allocation (e.g., 512Mi)"},
                    "cpu": {"type": "string", "description": "CPU allocation (e.g., 1)"},
                },
                "required": ["service_name", "image"],
            },
        ),
        MCPToolDefinition(
            name="get_service_status",
            description="Get the status of a Cloud Run service",
            parameters={
                "type": "object",
                "properties": {"service_name": {"type": "string", "description": "Service name"}},
                "required": ["service_name"],
            },
        ),
        MCPToolDefinition(
            name="list_services",
            description="List all Cloud Run services in the project",
            parameters={"type": "object", "properties": {}},
        ),
    ]


@app.post("/mcp/cloud-run/deploy")
async def deploy_service(request: DeployRequest) -> Dict[str, Any]:
    """Deploy or update a Cloud Run service"""
    if not run_client:
        raise HTTPException(status_code=500, detail="Cloud Run client not initialized")

    try:
        # Build the service configuration
        service = Service()
        service.template.containers = [Container()]
        service.template.containers[0].image = request.image

        # Set environment variables
        if request.env_vars:
            service.template.containers[0].env = [{"name": k, "value": v} for k, v in request.env_vars.items()]

        # Set resource limits
        service.template.containers[0].resources.limits = {"memory": request.memory, "cpu": request.cpu}

        # Set scaling
        service.template.scaling.min_instance_count = request.min_instances
        service.template.scaling.max_instance_count = request.max_instances

        # Deploy the service
        parent = f"projects/{PROJECT_ID}/locations/{REGION}"

        operation = run_client.create_service(parent=parent, service=service, service_id=request.service_name)

        # Wait for operation to complete
        response = operation.result()

        logger.info(f"Successfully deployed service: {request.service_name}")

        return {
            "status": "success",
            "service_name": request.service_name,
            "url": response.uri,
            "message": f"Service {request.service_name} deployed successfully",
        }

    except Exception as e:
        logger.error(f"Failed to deploy service: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/cloud-run/status/{service_name}")
async def get_service_status(service_name: str) -> ServiceStatus:
    """Get the status of a Cloud Run service"""
    if not run_client:
        raise HTTPException(status_code=500, detail="Cloud Run client not initialized")

    try:
        name = f"projects/{PROJECT_ID}/locations/{REGION}/services/{service_name}"
        service = run_client.get_service(name=name)

        return ServiceStatus(
            name=service_name,
            url=service.uri,
            ready=service.terminal_condition.state == "CONDITION_SUCCEEDED",
            latest_revision=service.latest_created_revision_name,
        )

    except Exception as e:
        logger.error(f"Failed to get service status: {e}")
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")


@app.get("/mcp/cloud-run/list")
async def list_services() -> List[Dict[str, Any]]:
    """List all Cloud Run services"""
    if not run_client:
        raise HTTPException(status_code=500, detail="Cloud Run client not initialized")

    try:
        parent = f"projects/{PROJECT_ID}/locations/{REGION}"
        services = run_client.list_services(parent=parent)

        return [
            {
                "name": service.name.split("/")[-1],
                "url": service.uri,
                "created": service.create_time.isoformat() if service.create_time else None,
                "updated": service.update_time.isoformat() if service.update_time else None,
            }
            for service in services
        ]

    except Exception as e:
        logger.error(f"Failed to list services: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/gcp/pulumi/apply")
async def pulumi_apply(stack_name: str):
    """
    Trigger Pulumi stack apply for code-driven GCP infrastructure management.
    This endpoint should execute `pulumi up` (or equivalent Python automation) for the given stack.
    """
    import subprocess

    try:
        # Example: run Pulumi CLI (in practice, use subprocess with care and validate input)
        result = subprocess.run(
            ["pulumi", "up", "--stack", stack_name, "--yes", "--non-interactive"],
            capture_output=True,
            text=True,
            check=True,
        )
        return {"status": "success", "stack": stack_name, "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.CalledProcessError as e:
        logger.error(f"Pulumi apply failed: {e.stderr}")
        return {"status": "error", "stack": stack_name, "stdout": e.stdout, "stderr": e.stderr}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "gcp-cloud-run-mcp"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
