#!/usr/bin/env python3
"""
MCP Server for Google Secret Manager
Enables secure secret management through MCP
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import google.auth
from fastapi import FastAPI, HTTPException
from google.cloud import secretmanager
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="GCP Secrets MCP Server",
    description="MCP server for managing Google Secret Manager",
    version="1.0.0",
)

# Get configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID")

# Initialize Secret Manager client
try:
    credentials, project = google.auth.default()
    client = secretmanager.SecretManagerServiceClient()
    if not PROJECT_ID:
        PROJECT_ID = project
except Exception as e:
    logger.error(f"Failed to initialize Secret Manager client: {e}")
    client = None


class SecretRequest(BaseModel):
    """Request model for secret operations"""

    secret_id: str = Field(..., description="Secret identifier")
    value: Optional[str] = Field(None, description="Secret value (for create/update)")
    labels: Optional[Dict[str, str]] = Field(default={}, description="Secret labels")


class SecretVersion(BaseModel):
    """Model for secret version"""

    version: int
    state: str
    created_time: str
    destroyed_time: Optional[str] = None


class MCPToolDefinition(BaseModel):
    """MCP tool definition"""

    name: str
    description: str
    parameters: Dict[str, Any]


@app.get("/mcp/tools")
async def get_tools() -> List[MCPToolDefinition]:
    """Return available tools"""
    return [
        MCPToolDefinition(
            name="get_secret",
            description="Retrieve a secret value",
            parameters={
                "type": "object",
                "properties": {
                    "secret_id": {"type": "string", "description": "Secret ID"},
                    "version": {
                        "type": "string",
                        "description": "Version (default: latest)",
                    },
                },
                "required": ["secret_id"],
            },
        ),
        MCPToolDefinition(
            name="create_secret",
            description="Create a new secret",
            parameters={
                "type": "object",
                "properties": {
                    "secret_id": {"type": "string", "description": "Secret ID"},
                    "value": {"type": "string", "description": "Secret value"},
                    "labels": {"type": "object", "description": "Labels"},
                },
                "required": ["secret_id", "value"],
            },
        ),
        MCPToolDefinition(
            name="update_secret",
            description="Add a new version to existing secret",
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
            parameters={
                "type": "object",
                "properties": {
                    "filter": {"type": "string", "description": "Optional filter"}
                },
            },
        ),
        MCPToolDefinition(
            name="delete_secret",
            description="Delete a secret",
            parameters={
                "type": "object",
                "properties": {
                    "secret_id": {"type": "string", "description": "Secret ID"}
                },
                "required": ["secret_id"],
            },
        ),
    ]


@app.post("/mcp/get_secret")
async def get_secret(secret_id: str, version: str = "latest") -> Dict[str, Any]:
    """Get a secret value"""
    if not client:
        raise HTTPException(
            status_code=500, detail="Secret Manager client not initialized"
        )

    try:
        name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/{version}"
        response = client.access_secret_version(request={"name": name})

        # Decode the secret
        secret_value = response.payload.data.decode("UTF-8")

        # Try to parse as JSON
        try:
            secret_data = json.loads(secret_value)
        except json.JSONDecodeError:
            secret_data = secret_value

        return {
            "secret_id": secret_id,
            "version": version,
            "value": secret_data,
            "created_time": (
                response.create_time.isoformat() if response.create_time else None
            ),
        }

    except Exception as e:
        logger.error(f"Failed to get secret: {e}")
        raise HTTPException(status_code=404, detail=f"Secret {secret_id} not found")


@app.post("/mcp/create_secret")
async def create_secret(request: SecretRequest) -> Dict[str, Any]:
    """Create a new secret"""
    if not client:
        raise HTTPException(
            status_code=500, detail="Secret Manager client not initialized"
        )

    try:
        parent = f"projects/{PROJECT_ID}"

        # Create the secret
        secret = client.create_secret(
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
        version = client.add_secret_version(
            request={
                "parent": secret.name,
                "payload": {"data": request.value.encode("UTF-8")},
            }
        )

        logger.info(f"Created secret: {request.secret_id}")

        return {
            "status": "success",
            "secret_id": request.secret_id,
            "version": version.name.split("/")[-1],
            "message": f"Secret {request.secret_id} created successfully",
        }

    except Exception as e:
        logger.error(f"Failed to create secret: {e}")
        if "already exists" in str(e):
            raise HTTPException(
                status_code=409, detail=f"Secret {request.secret_id} already exists"
            )
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/update_secret")
async def update_secret(secret_id: str, value: str) -> Dict[str, Any]:
    """Add a new version to existing secret"""
    if not client:
        raise HTTPException(
            status_code=500, detail="Secret Manager client not initialized"
        )

    try:
        parent = f"projects/{PROJECT_ID}/secrets/{secret_id}"

        # Add new version
        version = client.add_secret_version(
            request={"parent": parent, "payload": {"data": value.encode("UTF-8")}}
        )

        logger.info(f"Updated secret: {secret_id}")

        return {
            "status": "success",
            "secret_id": secret_id,
            "version": version.name.split("/")[-1],
            "message": f"Secret {secret_id} updated with new version",
        }

    except Exception as e:
        logger.error(f"Failed to update secret: {e}")
        raise HTTPException(status_code=404, detail=f"Secret {secret_id} not found")


@app.post("/mcp/list_secrets")
async def list_secrets(filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all secrets"""
    if not client:
        raise HTTPException(
            status_code=500, detail="Secret Manager client not initialized"
        )

    try:
        parent = f"projects/{PROJECT_ID}"

        # List secrets
        secrets = client.list_secrets(request={"parent": parent, "filter": filter})

        result = []
        for secret in secrets:
            result.append(
                {
                    "name": secret.name.split("/")[-1],
                    "created_time": (
                        secret.create_time.isoformat() if secret.create_time else None
                    ),
                    "labels": dict(secret.labels),
                    "replication": (
                        "automatic" if secret.replication.automatic else "user_managed"
                    ),
                }
            )

        return result

    except Exception as e:
        logger.error(f"Failed to list secrets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/list_versions")
async def list_versions(secret_id: str) -> List[SecretVersion]:
    """List all versions of a secret"""
    if not client:
        raise HTTPException(
            status_code=500, detail="Secret Manager client not initialized"
        )

    try:
        parent = f"projects/{PROJECT_ID}/secrets/{secret_id}"

        # List versions
        versions = client.list_secret_versions(request={"parent": parent})

        result = []
        for version in versions:
            result.append(
                SecretVersion(
                    version=int(version.name.split("/")[-1]),
                    state=version.state.name,
                    created_time=(
                        version.create_time.isoformat() if version.create_time else ""
                    ),
                    destroyed_time=(
                        version.destroy_time.isoformat()
                        if version.destroy_time
                        else None
                    ),
                )
            )

        return sorted(result, key=lambda x: x.version, reverse=True)

    except Exception as e:
        logger.error(f"Failed to list versions: {e}")
        raise HTTPException(status_code=404, detail=f"Secret {secret_id} not found")


@app.post("/mcp/delete_secret")
async def delete_secret(secret_id: str) -> Dict[str, Any]:
    """Delete a secret"""
    if not client:
        raise HTTPException(
            status_code=500, detail="Secret Manager client not initialized"
        )

    try:
        name = f"projects/{PROJECT_ID}/secrets/{secret_id}"

        # Delete the secret
        client.delete_secret(request={"name": name})

        logger.info(f"Deleted secret: {secret_id}")

        return {
            "status": "success",
            "secret_id": secret_id,
            "message": f"Secret {secret_id} deleted successfully",
        }

    except Exception as e:
        logger.error(f"Failed to delete secret: {e}")
        raise HTTPException(status_code=404, detail=f"Secret {secret_id} not found")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    is_healthy = client is not None

    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "service": "gcp-secrets-mcp",
        "project_id": PROJECT_ID,
        "client_initialized": is_healthy,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
