#!/usr/bin/env python3
"""
MCP Server for Google Secret Manager Management

This server enables API-driven management of GCP Secret Manager resources
through the Model Context Protocol (MCP).
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from google.api_core.exceptions import NotFound
from google.cloud import secretmanager
from pydantic import BaseModel, Field

# --- MCP CONFIG IMPORTS ---
from mcp_server.config.loader import load_config
from mcp_server.config.models import MCPConfig

# --- Shared GCP Client Utility ---
from mcp_server.utils.gcp_client import init_gcp_client

gcp_config: MCPConfig = load_config()
PROJECT_ID = getattr(gcp_config, "gcp_project_id", None) or "your-gcp-project"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app for MCP server
app = FastAPI(
    title="GCP Secret Manager MCP Server",
    description="MCP server for managing Google Secret Manager resources",
    version="1.0.0",
)

# Initialize Secret Manager client using shared utility
secret_client = init_gcp_client(secretmanager.SecretManagerServiceClient, PROJECT_ID)


class CreateSecretRequest(BaseModel):
    secret_id: str = Field(..., description="Secret ID")
    value: str = Field(..., description="Secret value")
    labels: Optional[Dict[str, str]] = Field(
        default=None, description="Labels for the secret"
    )


class UpdateSecretRequest(BaseModel):
    secret_id: str = Field(..., description="Secret ID")
    value: str = Field(..., description="New secret value")


class MCPToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]


@app.get("/mcp/secret-manager/tools")
async def get_tools() -> List[MCPToolDefinition]:
    """Return available Secret Manager tools for MCP."""
    return [
        MCPToolDefinition(
            name="create_secret",
            description="Create a new secret",
            parameters={
                "type": "object",
                "properties": {
                    "secret_id": {"type": "string", "description": "Secret ID"},
                    "value": {"type": "string", "description": "Secret value"},
                    "labels": {
                        "type": "object",
                        "description": "Labels for the secret",
                    },
                },
                "required": ["secret_id", "value"],
            },
        ),
        MCPToolDefinition(
            name="get_secret",
            description="Retrieve the latest value of a secret",
            parameters={
                "type": "object",
                "properties": {
                    "secret_id": {"type": "string", "description": "Secret ID"}
                },
                "required": ["secret_id"],
            },
        ),
        MCPToolDefinition(
            name="update_secret",
            description="Update an existing secret with a new value",
            parameters={
                "type": "object",
                "properties": {
                    "secret_id": {"type": "string", "description": "Secret ID"},
                    "value": {"type": "string", "description": "New secret value"},
                },
                "required": ["secret_id", "value"],
            },
        ),
        MCPToolDefinition(
            name="list_secrets",
            description="List all secrets in the project",
            parameters={"type": "object", "properties": {}},
        ),
    ]


@app.post("/mcp/secret-manager/create")
async def create_secret(request: CreateSecretRequest):
    """Create a new secret and add an initial version."""
    if not secret_client:
        raise HTTPException(
            status_code=500, detail="Secret Manager client not initialized"
        )
    parent = f"projects/{PROJECT_ID}"
    try:
        # Create the secret
        secret = secret_client.create_secret(
            request={
                "parent": parent,
                "secret_id": request.secret_id,
                "secret": {
                    "replication": {"automatic": {}},
                    "labels": request.labels or {},
                },
            }
        )
        # Add the initial version
        secret_client.add_secret_version(
            request={
                "parent": secret.name,
                "payload": {"data": request.value.encode("UTF-8")},
            }
        )
        return {"status": "success", "secret_id": request.secret_id}
    except Exception as e:
        from mcp_server.utils.gcp_client import handle_gcp_error

        raise HTTPException(
            status_code=500, detail=handle_gcp_error(e, "Failed to create secret")
        )


@app.get("/mcp/secret-manager/get/{secret_id}")
async def get_secret(secret_id: str):
    """Retrieve the latest value of a secret."""
    if not secret_client:
        raise HTTPException(
            status_code=500, detail="Secret Manager client not initialized"
        )
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    try:
        response = secret_client.access_secret_version(request={"name": name})
        value = response.payload.data.decode("UTF-8")
        return {"secret_id": secret_id, "value": value}
    except NotFound:
        raise HTTPException(status_code=404, detail=f"Secret {secret_id} not found")
    except Exception as e:
        from mcp_server.utils.gcp_client import handle_gcp_error

        raise HTTPException(
            status_code=500, detail=handle_gcp_error(e, "Failed to get secret")
        )


@app.post("/mcp/secret-manager/update")
async def update_secret(request: UpdateSecretRequest):
    """Update an existing secret by adding a new version."""
    if not secret_client:
        raise HTTPException(
            status_code=500, detail="Secret Manager client not initialized"
        )
    name = f"projects/{PROJECT_ID}/secrets/{request.secret_id}"
    try:
        # Add a new version
        secret_client.add_secret_version(
            request={"parent": name, "payload": {"data": request.value.encode("UTF-8")}}
        )
        return {"status": "success", "secret_id": request.secret_id}
    except NotFound:
        raise HTTPException(
            status_code=404, detail=f"Secret {request.secret_id} not found"
        )
    except Exception as e:
        from mcp_server.utils.gcp_client import handle_gcp_error

        raise HTTPException(
            status_code=500, detail=handle_gcp_error(e, "Failed to update secret")
        )


@app.get("/mcp/secret-manager/list")
async def list_secrets():
    """List all secrets in the project."""
    if not secret_client:
        raise HTTPException(
            status_code=500, detail="Secret Manager client not initialized"
        )
    parent = f"projects/{PROJECT_ID}"
    try:
        secrets = secret_client.list_secrets(request={"parent": parent})
        return {
            "secrets": [
                {"name": secret.name, "labels": dict(secret.labels)}
                for secret in secrets
            ]
        }
    except Exception as e:
        from mcp_server.utils.gcp_client import handle_gcp_error

        raise HTTPException(
            status_code=500, detail=handle_gcp_error(e, "Failed to list secrets")
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "gcp-secret-manager-mcp"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
