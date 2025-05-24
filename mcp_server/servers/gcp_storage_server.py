#!/usr/bin/env python3
"""
MCP Server for Google Cloud Storage Management

This server enables API-driven management of GCP Cloud Storage resources
through the Model Context Protocol (MCP).
"""

import logging
from typing import Any, Dict, List

from fastapi import FastAPI, File, HTTPException, UploadFile
from google.api_core.exceptions import NotFound
from google.cloud import storage
from pydantic import BaseModel, Field

# --- MCP CONFIG IMPORTS ---
from mcp_server.config.loader import load_config
from mcp_server.config.models import MCPConfig

gcp_config: MCPConfig = load_config()
PROJECT_ID = getattr(gcp_config, "gcp_project_id", None) or "your-gcp-project"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app for MCP server
app = FastAPI(
    title="GCP Storage MCP Server",
    description="MCP server for managing Google Cloud Storage resources",
    version="1.0.0",
)

# Initialize Storage client
try:
    storage_client = storage.Client(project=PROJECT_ID)
except Exception as e:
    logger.error(f"Failed to initialize Storage client: {e}")
    storage_client = None


class CreateBucketRequest(BaseModel):
    bucket_name: str = Field(..., description="Bucket name")
    location: str = Field(default="US", description="Bucket location")
    storage_class: str = Field(default="STANDARD", description="Storage class")


class MCPToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]


@app.get("/mcp/storage/tools")
async def get_tools() -> List[MCPToolDefinition]:
    """Return available Storage tools for MCP."""
    return [
        MCPToolDefinition(
            name="create_bucket",
            description="Create a new Cloud Storage bucket",
            parameters={
                "type": "object",
                "properties": {
                    "bucket_name": {"type": "string", "description": "Bucket name"},
                    "location": {"type": "string", "description": "Bucket location"},
                    "storage_class": {"type": "string", "description": "Storage class"},
                },
                "required": ["bucket_name"],
            },
        ),
        MCPToolDefinition(
            name="list_buckets",
            description="List all Cloud Storage buckets",
            parameters={"type": "object", "properties": {}},
        ),
        MCPToolDefinition(
            name="upload_object",
            description="Upload an object to a bucket",
            parameters={
                "type": "object",
                "properties": {
                    "bucket_name": {"type": "string", "description": "Bucket name"},
                    "object_name": {"type": "string", "description": "Object name"},
                    "file": {"type": "string", "description": "File content (base64 or multipart)"},
                },
                "required": ["bucket_name", "object_name", "file"],
            },
        ),
        MCPToolDefinition(
            name="list_objects",
            description="List all objects in a bucket",
            parameters={
                "type": "object",
                "properties": {"bucket_name": {"type": "string", "description": "Bucket name"}},
                "required": ["bucket_name"],
            },
        ),
        MCPToolDefinition(
            name="delete_object",
            description="Delete an object from a bucket",
            parameters={
                "type": "object",
                "properties": {
                    "bucket_name": {"type": "string", "description": "Bucket name"},
                    "object_name": {"type": "string", "description": "Object name"},
                },
                "required": ["bucket_name", "object_name"],
            },
        ),
    ]


@app.post("/mcp/storage/create_bucket")
async def create_bucket(request: CreateBucketRequest):
    """Create a new Cloud Storage bucket."""
    if not storage_client:
        raise HTTPException(status_code=500, detail="Storage client not initialized")
    try:
        bucket = storage_client.bucket(request.bucket_name)
        bucket.storage_class = request.storage_class
        new_bucket = storage_client.create_bucket(bucket, location=request.location)
        return {"status": "success", "bucket_name": new_bucket.name}
    except Exception as e:
        logger.error(f"Failed to create bucket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/storage/list_buckets")
async def list_buckets():
    """List all Cloud Storage buckets."""
    if not storage_client:
        raise HTTPException(status_code=500, detail="Storage client not initialized")
    try:
        buckets = storage_client.list_buckets()
        return {"buckets": [bucket.name for bucket in buckets]}
    except Exception as e:
        logger.error(f"Failed to list buckets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/storage/upload_object")
async def upload_object(bucket_name: str, object_name: str, file: UploadFile = File(...)):
    """Upload an object to a bucket."""
    if not storage_client:
        raise HTTPException(status_code=500, detail="Storage client not initialized")
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        blob.upload_from_file(file.file)
        return {"status": "success", "bucket_name": bucket_name, "object_name": object_name}
    except Exception as e:
        logger.error(f"Failed to upload object: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/storage/list_objects")
async def list_objects(bucket_name: str):
    """List all objects in a bucket."""
    if not storage_client:
        raise HTTPException(status_code=500, detail="Storage client not initialized")
    try:
        bucket = storage_client.bucket(bucket_name)
        blobs = bucket.list_blobs()
        return {"objects": [blob.name for blob in blobs]}
    except Exception as e:
        logger.error(f"Failed to list objects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/mcp/storage/delete_object")
async def delete_object(bucket_name: str, object_name: str):
    """Delete an object from a bucket."""
    if not storage_client:
        raise HTTPException(status_code=500, detail="Storage client not initialized")
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        blob.delete()
        return {"status": "success", "bucket_name": bucket_name, "object_name": object_name}
    except NotFound:
        raise HTTPException(status_code=404, detail=f"Object {object_name} not found in bucket {bucket_name}")
    except Exception as e:
        logger.error(f"Failed to delete object: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "gcp-storage-mcp"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8005)
