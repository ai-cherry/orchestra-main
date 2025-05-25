#!/usr/bin/env python3
"""
GCP Resources MCP Server

This MCP server provides tools and resources for accessing Google Cloud resources
and making them available to all AI assistants (Gemini, Roo, Claude, GitHub Copilot, etc.)
through the Model Context Protocol.

It exposes:
1. Tools for capturing GCP resource snapshots
2. Resources for accessing previously captured snapshots
3. Utilities for comparing GCP resources with code
"""

import argparse
import datetime
import glob
import json
import logging
import os
import subprocess
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("gcp-resources-mcp")

# MCP Server Configuration
app = FastAPI(
    title="GCP Resources MCP Server",
    description="MCP server for GCP resource snapshots and tools",
    version="1.0.0",
)

# Default settings
DEFAULT_SNAPSHOT_DIR = os.path.join(os.getcwd(), ".gcp-snapshots")
DEFAULT_SNAPSHOT_SCRIPT = os.path.join(os.getcwd(), "snapshot_gcp_resources.sh")

# Ensure our directories exist
os.makedirs(DEFAULT_SNAPSHOT_DIR, exist_ok=True)

# Server configuration (set via environment variables or startup args)
config = {
    "snapshot_dir": os.environ.get("GCP_SNAPSHOT_DIR", DEFAULT_SNAPSHOT_DIR),
    "snapshot_script": os.environ.get("GCP_SNAPSHOT_SCRIPT", DEFAULT_SNAPSHOT_SCRIPT),
    "default_project_id": os.environ.get("GCP_PROJECT_ID", ""),
}


# MCP models
class GcpSnapshotRequest(BaseModel):
    """Request to create a new GCP snapshot."""

    project_id: str = Field(..., description="The GCP project ID to snapshot")
    comprehensive: bool = Field(
        False, description="Whether to capture comprehensive details"
    )
    compare_with_code: bool = Field(
        False, description="Whether to compare with codebase"
    )
    code_dir: str = Field(".", description="Directory to compare with (if comparing)")
    output_subdir: Optional[str] = Field(
        None, description="Optional subdirectory for output"
    )


class GcpResourceListRequest(BaseModel):
    """Request to list GCP resources of a specific type."""

    snapshot_id: str = Field(..., description="Snapshot ID (directory name)")
    resource_type: str = Field(
        ..., description="Resource type (compute, storage, etc.)"
    )


class GcpResourceCompareRequest(BaseModel):
    """Request to compare GCP resources with code."""

    snapshot_id: str = Field(..., description="Snapshot ID (directory name)")
    resource_types: List[str] = Field(
        default=["compute", "storage", "databases", "ai"],
        description="Resource types to compare",
    )
    code_dir: str = Field(".", description="Directory to compare with")


class GcpSnapshotInfoResponse(BaseModel):
    """Response with information about a GCP snapshot."""

    snapshot_id: str
    project_id: str
    created_at: str
    snapshot_type: str
    summary_file: str
    resources: Dict[str, int]


# Utility functions
def get_available_snapshots() -> List[str]:
    """Get list of available snapshot directories."""
    snapshot_pattern = os.path.join(config["snapshot_dir"], "*")
    return [
        os.path.basename(d) for d in glob.glob(snapshot_pattern) if os.path.isdir(d)
    ]


def get_snapshot_info(snapshot_id: str) -> Optional[GcpSnapshotInfoResponse]:
    """Get information about a specific snapshot."""
    snapshot_dir = os.path.join(config["snapshot_dir"], snapshot_id)

    if not os.path.isdir(snapshot_dir):
        return None

    # Try to load metadata
    metadata_file = os.path.join(snapshot_dir, "metadata.json")
    if not os.path.exists(metadata_file):
        return None

    with open(metadata_file, "r") as f:
        metadata = json.load(f)

    # Count resources by type
    resources = {}
    for resource_type in ["compute", "storage", "databases", "networking", "ai", "iam"]:
        resource_dir = os.path.join(snapshot_dir, resource_type)
        if os.path.isdir(resource_dir):
            json_files = glob.glob(os.path.join(resource_dir, "*.json"))
            resources[resource_type] = len(json_files)

    return GcpSnapshotInfoResponse(
        snapshot_id=snapshot_id,
        project_id=metadata.get("project_id", "unknown"),
        created_at=metadata.get("snapshot_date", "unknown"),
        snapshot_type=metadata.get("snapshot_type", "unknown"),
        summary_file=os.path.join(snapshot_dir, "resource_summary.md"),
        resources=resources,
    )


def run_snapshot_script(params: GcpSnapshotRequest) -> str:
    """Run the GCP snapshot script with the given parameters."""
    # Build command
    cmd = [
        config["snapshot_script"],
        "-p",
        params.project_id,
    ]

    # Add optional flags
    if params.comprehensive:
        cmd.append("-a")

    if params.compare_with_code:
        cmd.append("-c")
        cmd.extend(["-d", params.code_dir])

    # Set output directory
    if params.output_subdir:
        output_dir = os.path.join(config["snapshot_dir"], params.output_subdir)
    else:
        output_dir = config["snapshot_dir"]

    cmd.extend(["-o", output_dir])

    # Run command
    logger.info(f"Running snapshot command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("Snapshot completed successfully")

        # Parse the output to find the snapshot directory
        for line in result.stdout.splitlines():
            if "Snapshot directory:" in line:
                snapshot_dir = line.split("Snapshot directory:")[1].strip()
                return os.path.basename(snapshot_dir)

        # Fallback to looking for the newest directory
        snapshots = sorted(
            glob.glob(os.path.join(output_dir, f"{params.project_id}_*")),
            key=os.path.getctime,
            reverse=True,
        )
        if snapshots:
            return os.path.basename(snapshots[0])

        raise ValueError("Could not determine snapshot directory")

    except subprocess.CalledProcessError as e:
        logger.error(f"Snapshot failed: {e}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        raise ValueError(f"Snapshot script failed: {e}")


# MCP Endpoints - Tools
@app.post("/mcp/tools/create_gcp_snapshot")
async def create_gcp_snapshot(request: GcpSnapshotRequest) -> Dict[str, Any]:
    """
    Create a new GCP resource snapshot.

    This tool captures a point-in-time inventory of GCP resources in the specified project.
    """
    try:
        snapshot_id = run_snapshot_script(request)
        snapshot_info = get_snapshot_info(snapshot_id)

        return {
            "snapshot_id": snapshot_id,
            "project_id": request.project_id,
            "location": f"{config['snapshot_dir']}/{snapshot_id}",
            "info": snapshot_info.dict() if snapshot_info else None,
        }
    except Exception as e:
        logger.exception("Error creating GCP snapshot")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/tools/compare_gcp_with_code")
async def compare_gcp_with_code(request: GcpResourceCompareRequest) -> Dict[str, Any]:
    """
    Compare GCP resources with code to identify gaps or inconsistencies.

    This tool analyzes the snapshots and code to find resources that may not be
    properly tracked in infrastructure-as-code.
    """
    snapshot_dir = os.path.join(config["snapshot_dir"], request.snapshot_id)
    if not os.path.isdir(snapshot_dir):
        raise HTTPException(
            status_code=404, detail=f"Snapshot {request.snapshot_id} not found"
        )

    # Get metadata
    metadata_file = os.path.join(snapshot_dir, "metadata.json")
    if not os.path.exists(metadata_file):
        raise HTTPException(
            status_code=404,
            detail=f"Metadata for snapshot {request.snapshot_id} not found",
        )

    with open(metadata_file, "r") as f:
        metadata = json.load(f)

    # Check if comparison already exists
    comparison_file = os.path.join(snapshot_dir, "code_comparison.md")
    if os.path.exists(comparison_file):
        with open(comparison_file, "r") as f:
            comparison_content = f.read()

        return {
            "snapshot_id": request.snapshot_id,
            "project_id": metadata.get("project_id", "unknown"),
            "comparison_file": comparison_file,
            "comparison_content": comparison_content,
            "already_existed": True,
        }

    # Otherwise, we need to run the comparison
    # Build a comparison file using grep and other tools
    # results = {"untracked_resources": [], "matched_resources": []}  # Removed unused assignment

    # TODO: Implement comparison logic without running the full script again
    # For now, return an error suggesting to use the snapshot script directly with -c flag

    raise HTTPException(
        status_code=400,
        detail="Direct comparison not yet implemented. Please run the snapshot script with -c flag for comparison.",
    )


@app.post("/mcp/tools/list_gcp_resources")
async def list_gcp_resources(request: GcpResourceListRequest) -> Dict[str, Any]:
    """
    List resources of a specific type from a GCP snapshot.

    This retrieves structured information about resources such as compute instances,
    Cloud Run services, storage buckets, etc.
    """
    snapshot_dir = os.path.join(config["snapshot_dir"], request.snapshot_id)
    if not os.path.isdir(snapshot_dir):
        raise HTTPException(
            status_code=404, detail=f"Snapshot {request.snapshot_id} not found"
        )

    resource_dir = os.path.join(snapshot_dir, request.resource_type)
    if not os.path.isdir(resource_dir):
        raise HTTPException(
            status_code=404,
            detail=f"Resource type {request.resource_type} not found in snapshot",
        )

    # Load all JSON files in the resource directory
    resources = {}
    for json_file in glob.glob(os.path.join(resource_dir, "*.json")):
        file_name = os.path.basename(json_file)
        try:
            with open(json_file, "r") as f:
                resources[file_name] = json.load(f)
        except Exception as e:
            resources[file_name] = {"error": str(e)}

    return {
        "snapshot_id": request.snapshot_id,
        "resource_type": request.resource_type,
        "resources": resources,
    }


# MCP Endpoints - Resources
@app.get("/mcp/resources/available_snapshots")
async def available_snapshots() -> Dict[str, Any]:
    """List all available GCP resource snapshots."""
    snapshots = []
    for snapshot_id in get_available_snapshots():
        info = get_snapshot_info(snapshot_id)
        if info:
            snapshots.append(info.dict())

    return {
        "snapshots": snapshots,
        "snapshot_count": len(snapshots),
        "snapshot_dir": config["snapshot_dir"],
    }


@app.get("/mcp/resources/snapshot/{snapshot_id}")
async def get_snapshot(snapshot_id: str) -> Dict[str, Any]:
    """Get information about a specific GCP snapshot."""
    info = get_snapshot_info(snapshot_id)
    if not info:
        raise HTTPException(status_code=404, detail=f"Snapshot {snapshot_id} not found")

    return info.dict()


@app.get("/mcp/resources/snapshot/{snapshot_id}/summary")
async def get_snapshot_summary(snapshot_id: str) -> Dict[str, Any]:
    """Get the summary of a GCP snapshot."""
    snapshot_dir = os.path.join(config["snapshot_dir"], snapshot_id)
    if not os.path.isdir(snapshot_dir):
        raise HTTPException(status_code=404, detail=f"Snapshot {snapshot_id} not found")

    summary_file = os.path.join(snapshot_dir, "resource_summary.md")
    if not os.path.exists(summary_file):
        raise HTTPException(
            status_code=404, detail=f"Summary for snapshot {snapshot_id} not found"
        )

    with open(summary_file, "r") as f:
        summary_content = f.read()

    return {
        "snapshot_id": snapshot_id,
        "summary_file": summary_file,
        "summary_content": summary_content,
    }


@app.get(
    "/mcp/resources/snapshot/{snapshot_id}/resources/{resource_type}/{resource_file}"
)
async def get_resource_file(
    snapshot_id: str, resource_type: str, resource_file: str
) -> Dict[str, Any]:
    """Get a specific resource file from a GCP snapshot."""
    snapshot_dir = os.path.join(config["snapshot_dir"], snapshot_id)
    if not os.path.isdir(snapshot_dir):
        raise HTTPException(status_code=404, detail=f"Snapshot {snapshot_id} not found")

    resource_path = os.path.join(snapshot_dir, resource_type, resource_file)
    if not os.path.exists(resource_path):
        raise HTTPException(
            status_code=404, detail=f"Resource file {resource_file} not found"
        )

    with open(resource_path, "r") as f:
        content = f.read()

        # Try to parse as JSON if it has a .json extension
        if resource_file.endswith(".json"):
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                pass

    return {
        "snapshot_id": snapshot_id,
        "resource_type": resource_type,
        "resource_file": resource_file,
        "content": content,
    }


# Healthcheck endpoint
@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "timestamp": datetime.datetime.now().isoformat(),
        "config": {
            "snapshot_dir": config["snapshot_dir"],
            "snapshot_script": config["snapshot_script"],
        },
    }


# Main entry point
if __name__ == "__main__":
    import uvicorn

    parser = argparse.ArgumentParser(description="GCP Resources MCP Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8085, help="Port to bind to")
    parser.add_argument(
        "--snapshot-dir",
        default=DEFAULT_SNAPSHOT_DIR,
        help="Directory to store snapshots",
    )
    parser.add_argument(
        "--snapshot-script",
        default=DEFAULT_SNAPSHOT_SCRIPT,
        help="Path to snapshot script",
    )
    parser.add_argument("--project-id", default="", help="Default GCP project ID")

    args = parser.parse_args()

    # Update config from args
    config["snapshot_dir"] = args.snapshot_dir
    config["snapshot_script"] = args.snapshot_script
    config["default_project_id"] = args.project_id

    # Ensure snapshot directory exists
    os.makedirs(config["snapshot_dir"], exist_ok=True)

    # Start server
    logger.info(f"Starting GCP Resources MCP Server on {args.host}:{args.port}")
    logger.info(f"Snapshot directory: {config['snapshot_dir']}")
    logger.info(f"Snapshot script: {config['snapshot_script']}")

    uvicorn.run(app, host=args.host, port=args.port)
