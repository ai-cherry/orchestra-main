#!/usr/bin/env python3
"""
MCP Server for Google Secret Manager

This server enables Claude 4 to manage secrets in Google Secret Manager
through the Model Context Protocol (MCP).
"""

import os
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from google.cloud import secretmanager_v1
import google.auth

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app for MCP server
app = FastAPI(
    title="GCP Secret Manager MCP Server",
    description="MCP server for managing Google Secret Manager secrets",
    version="1.0.0"
)

# Get configuration from environment
PROJECT_ID = os.getenv("GCP_PROJECT_ID")

# Initialize Secret Manager client
try:
    credentials, project = google.auth.default()
    secret_client = secretmanager_v1.SecretManagerServiceClient()
except Exception as e:
    logger.error(f"Failed to initialize Secret Manager client: {e}")
    secret_client = None


class GetSecretRequest(BaseModel):
    """Request model for retrieving a secret"""
    secret_name: str = Field(..., description="Name of the secret")
    version: str = Field(default="latest", description="Version of the secret")


class CreateSecretRequest(BaseModel):
    """Request model for creating a secret"""
    secret_name: str = Field(..., description="Name of the secret")
    secret_value: str = Field(..., description="Value of the secret")
    labels: Optional[Dict[str, str]] = Field(default={}, description="Labels for the secret")


class UpdateSecretRequest(BaseModel):
    """Request model for updating a secret (adding new version)"""
    secret_name: str = Field(..., description="Name of the secret")
    secret_value: str = Field(..., description="New value of the secret")


class SecretInfo(BaseModel):
    """Response model for secret information"""
    name: str
    create_time: Optional[str]
    labels: Dict[str, str]
    latest_version: Optional[str]
    

class MCPToolDefinition(BaseModel):
    """MCP tool definition for Claude"""
    name: str
    description: str
    parameters: Dict[str, Any]


@app.get("/mcp/secrets/tools")
async def get_tools() -> List[MCPToolDefinition]:
    """Return available tools for Claude to use"""
    return [
        MCPToolDefinition(
            name="get_secret",
            description="Retrieve a secret value from Secret Manager",
            parameters={
                "type": "object",
                "properties": {
                    "secret_name": {"type": "string", "description": "Name of the secret"},
                    "version": {"type": "string", "description": "Version (default: latest)"}
                },
                "required": ["secret_name"]
            }
        ),
        MCPToolDefinition(
            name="create_secret",
            description="Create a new secret in Secret Manager",
            parameters={
                "type": "object",
                "properties": {
                    "secret_name": {"type": "string", "description": "Name of the secret"},
                    "secret_value": {"type": "string", "description": "Value of the secret"},
                    "labels": {"type": "object", "description": "Labels for the secret"}
                },
                "required": ["secret_name", "secret_value"]
            }
        ),
        MCPToolDefinition(
            name="update_secret",
            description="Add a new version to an existing secret",
            parameters={
                "type": "object",
                "properties": {
                    "secret_name": {"type": "string", "description": "Name of the secret"},
                    "secret_value": {"type": "string", "description": "New value"}
                },
                "required": ["secret_name", "secret_value"]
            }
        ),
        MCPToolDefinition(
            name="list_secrets",
            description="List all secrets in the project",
            parameters={
                "type": "object",
                "properties": {
                    "filter": {"type": "string", "description": "Optional filter"}
                }
            }
        )
    ]


@app.post("/mcp/secrets/get")
async def get_secret(request: GetSecretRequest) -> Dict[str, Any]:
    """Retrieve a secret value"""
    if not secret_client:
        raise HTTPException(status_code=500, detail="Secret Manager client not initialized")
    
    try:
        # Build the resource name
        if request.version == "latest":
            name = f"projects/{PROJECT_ID}/secrets/{request.secret_name}/versions/latest"
        else:
            name = f"projects/{PROJECT_ID}/secrets/{request.secret_name}/versions/{request.version}"
        
        # Access the secret version
        response = secret_client.access_secret_version(request={"name": name})
        
        # Decode the secret payload
        secret_value = response.payload.data.decode("UTF-8")
        
        logger.info(f"Successfully retrieved secret: {request.secret_name}")
        
        return {
            "status": "success",
            "secret_name": request.secret_name,
            "version": request.version,
            "value": secret_value,
            "message": f"Secret {request.secret_name} retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve secret: {e}")
        raise HTTPException(status_code=404, detail=f"Secret {request.secret_name} not found")


@app.post("/mcp/secrets/create")
async def create_secret(request: CreateSecretRequest) -> Dict[str, Any]:
    """Create a new secret"""
    if not secret_client:
        raise HTTPException(status_code=500, detail="Secret Manager client not initialized")
    
    try:
        # Build the parent name
        parent = f"projects/{PROJECT_ID}"
        
        # Create the secret
        secret = {
            "replication": {
                "automatic": {}
            },
            "labels": request.labels
        }
        
        response = secret_client.create_secret(
            request={
                "parent": parent,
                "secret_id": request.secret_name,
                "secret": secret
            }
        )
        
        # Add the initial version
        secret_name = response.name
        version_request = {
            "parent": secret_name,
            "payload": {"data": request.secret_value.encode("UTF-8")}
        }
        version_response = secret_client.add_secret_version(request=version_request)
        
        logger.info(f"Successfully created secret: {request.secret_name}")
        
        return {
            "status": "success",
            "secret_name": request.secret_name,
            "version": version_response.name.split('/')[-1],
            "message": f"Secret {request.secret_name} created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create secret: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/secrets/update")
async def update_secret(request: UpdateSecretRequest) -> Dict[str, Any]:
    """Add a new version to an existing secret"""
    if not secret_client:
        raise HTTPException(status_code=500, detail="Secret Manager client not initialized")
    
    try:
        # Build the secret name
        secret_name = f"projects/{PROJECT_ID}/secrets/{request.secret_name}"
        
        # Add the new version
        version_request = {
            "parent": secret_name,
            "payload": {"data": request.secret_value.encode("UTF-8")}
        }
        response = secret_client.add_secret_version(request=version_request)
        
        logger.info(f"Successfully updated secret: {request.secret_name}")
        
        return {
            "status": "success",
            "secret_name": request.secret_name,
            "version": response.name.split('/')[-1],
            "message": f"Secret {request.secret_name} updated with new version"
        }
        
    except Exception as e:
        logger.error(f"Failed to update secret: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/secrets/list")
async def list_secrets(filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all secrets"""
    if not secret_client:
        raise HTTPException(status_code=500, detail="Secret Manager client not initialized")
    
    try:
        parent = f"projects/{PROJECT_ID}"
        
        # List secrets with optional filter
        request = {"parent": parent}
        if filter:
            request["filter"] = filter
            
        secrets = secret_client.list_secrets(request=request)
        
        return [
            {
                "name": secret.name.split("/")[-1],
                "created": secret.create_time.isoformat() if secret.create_time else None,
                "labels": dict(secret.labels),
                "replication": secret.replication.WhichOneof("replication")
            }
            for secret in secrets
        ]
        
    except Exception as e:
        logger.error(f"Failed to list secrets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "gcp-secret-manager-mcp"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)