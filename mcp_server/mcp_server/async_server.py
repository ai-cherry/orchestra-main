#!/usr/bin/env python3
"""
async_server.py - Asynchronous MCP Server

This module provides an asynchronous version of the MCP server,
using FastAPI for improved performance and scalability.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import components
from .storage.async_memory_store import AsyncMemoryStore
from .tools.tool_manager import ToolManager
from .workflows.workflow_manager import WorkflowManager
from .config import MCPConfig, load_config, get_config_path_from_env
from .exceptions import (
    MCPError,
    MemoryNotFoundError,
    MemoryWriteError,
    MemoryDeleteError,
    MemorySyncError,
    ToolNotEnabledError,
    ToolExecutionError,
    WorkflowNotFoundError,
    WorkflowExecutionError,
    ConfigFileError,
    ConfigValidationError,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("mcp-async-server")


# Pydantic models for API requests and responses
class StatusResponse(BaseModel):
    """Status response model."""

    status: str
    tools: List[str]
    workflows: int


class MemoryRequest(BaseModel):
    """Memory request model."""

    key: str
    content: Any
    scope: Optional[str] = "session"
    tool: Optional[str] = None
    ttl: Optional[int] = None


class MemoryResponse(BaseModel):
    """Memory response model."""

    key: str
    content: Any


class MemorySyncRequest(BaseModel):
    """Memory sync request model."""

    key: str
    source_tool: str
    target_tool: str
    scope: Optional[str] = "session"


class ExecuteRequest(BaseModel):
    """Execute request model."""

    tool: str
    mode: str
    prompt: str
    context: Optional[str] = None


class ExecuteResponse(BaseModel):
    """Execute response model."""

    result: str


class WorkflowRequest(BaseModel):
    """Workflow request model."""

    workflow_id: str
    parameters: Optional[Dict[str, Any]] = None
    tool: Optional[str] = None


class CrossToolWorkflowRequest(BaseModel):
    """Cross-tool workflow request model."""

    workflow_id: str
    tools: Optional[List[str]] = None


class WorkflowResponse(BaseModel):
    """Workflow response model."""

    result: str


class SuccessResponse(BaseModel):
    """Success response model."""

    success: bool


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    code: str
    details: Optional[Dict[str, Any]] = None


class AsyncMCPServer:
    """Asynchronous Model Context Protocol (MCP) Server."""

    def __init__(
        self,
        config_path: Optional[str] = None,
        memory_store=None,
        tool_manager=None,
        workflow_manager=None,
    ):
        """Initialize the async MCP server with optional dependency injection.

        Args:
            config_path: Path to configuration file
            memory_store: Optional AsyncMemoryStore instance (for dependency injection)
            tool_manager: Optional ToolManager instance (for dependency injection)
            workflow_manager: Optional WorkflowManager instance (for dependency injection)
        """
        # Load configuration
        try:
            self.config = load_config(config_path)
            logger.info("Configuration loaded successfully")
        except (ConfigFileError, ConfigValidationError) as e:
            logger.error(f"Error loading configuration: {e}")
            # Use default configuration
            self.config = MCPConfig()

        # Use injected dependencies or create new instances
        self.memory_store = memory_store or AsyncMemoryStore(self.config.memory.dict())
        self.tool_manager = tool_manager or ToolManager(
            {k: v.dict() for k, v in self.config.tools.items()},
            None,  # We'll handle memory store separately
        )
        self.workflow_manager = workflow_manager or WorkflowManager(
            self.tool_manager, None  # We'll handle memory store separately
        )

        # Initialize FastAPI application
        self.app = FastAPI(
            title="MCP Server",
            description="Model Context Protocol Server for AI tool integration",
            version="1.0.0",
        )

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.security.allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Add exception handlers
        self._configure_exception_handlers()

        # Configure routes
        self._configure_routes()

        logger.info("Async MCP server initialized")

    def _configure_exception_handlers(self):
        """Configure exception handlers for the FastAPI application."""

        @self.app.exception_handler(MCPError)
        async def mcp_error_handler(request, exc):
            """Handle MCP errors."""
            return JSONResponse(
                status_code=500,
                content=exc.to_dict(),
            )

        @self.app.exception_handler(MemoryNotFoundError)
        async def memory_not_found_handler(request, exc):
            """Handle memory not found errors."""
            return JSONResponse(
                status_code=404,
                content=exc.to_dict(),
            )

        @self.app.exception_handler(ToolNotEnabledError)
        async def tool_not_enabled_handler(request, exc):
            """Handle tool not enabled errors."""
            return JSONResponse(
                status_code=400,
                content=exc.to_dict(),
            )

        @self.app.exception_handler(WorkflowNotFoundError)
        async def workflow_not_found_handler(request, exc):
            """Handle workflow not found errors."""
            return JSONResponse(
                status_code=404,
                content=exc.to_dict(),
            )

    def _configure_routes(self):
        """Configure FastAPI routes."""

        # Status endpoint
        @self.app.get("/api/status", response_model=StatusResponse)
        async def status():
            return {
                "status": "running",
                "tools": self.tool_manager.get_enabled_tools(),
                "workflows": len(self.workflow_manager.get_available_workflows()),
            }

        # Memory endpoints
        @self.app.get("/api/memory", response_model=MemoryResponse)
        async def get_memory(
            key: str, scope: str = "session", tool: Optional[str] = None
        ):
            content = await self.memory_store.get(key, scope, tool)
            if content is None:
                raise MemoryNotFoundError(key, scope, tool)

            return {"key": key, "content": content}

        @self.app.post("/api/memory", response_model=SuccessResponse)
        async def set_memory(request: MemoryRequest):
            success = await self.memory_store.set(
                request.key, request.content, request.scope, request.tool, request.ttl
            )
            if not success:
                raise MemoryWriteError(request.key, request.scope, request.tool)

            return {"success": True}

        @self.app.delete("/api/memory", response_model=SuccessResponse)
        async def delete_memory(
            key: str, scope: str = "session", tool: Optional[str] = None
        ):
            success = await self.memory_store.delete(key, scope, tool)
            if not success:
                raise MemoryDeleteError(key, scope, tool)

            return {"success": True}

        @self.app.post("/api/memory/sync", response_model=SuccessResponse)
        async def sync_memory(request: MemorySyncRequest):
            success = await self.memory_store.sync(
                request.key, request.source_tool, request.target_tool, request.scope
            )
            if not success:
                raise MemorySyncError(
                    request.key, request.source_tool, request.target_tool, request.scope
                )

            return {"success": True}

        # Tool execution endpoint
        @self.app.post("/api/execute", response_model=ExecuteResponse)
        async def execute(request: ExecuteRequest):
            # Check if the tool is enabled
            if request.tool not in self.tool_manager.get_enabled_tools():
                raise ToolNotEnabledError(request.tool)

            # Execute the tool
            result = self.tool_manager.execute(
                request.tool, request.mode, request.prompt, request.context
            )
            if result is None:
                raise ToolExecutionError(request.tool, request.mode)

            return {"result": result}

        # Workflow endpoints
        @self.app.get("/api/workflows")
        async def get_workflows():
            return self.workflow_manager.get_available_workflows()

        @self.app.post("/api/workflows/execute", response_model=WorkflowResponse)
        async def execute_workflow(request: WorkflowRequest):
            # Check if the workflow exists
            if (
                request.workflow_id
                not in self.workflow_manager.get_available_workflows()
            ):
                raise WorkflowNotFoundError(request.workflow_id)

            # Execute the workflow
            result = self.workflow_manager.execute_workflow(
                request.workflow_id, request.parameters, request.tool
            )
            if result is None:
                raise WorkflowExecutionError(request.workflow_id)

            return {"result": result}

        @self.app.post("/api/workflows/cross-tool", response_model=WorkflowResponse)
        async def execute_cross_tool_workflow(request: CrossToolWorkflowRequest):
            # Check if the workflow exists
            if (
                request.workflow_id
                not in self.workflow_manager.get_available_workflows()
            ):
                raise WorkflowNotFoundError(request.workflow_id)

            # Execute the workflow
            result = self.workflow_manager.execute_cross_tool_workflow(
                request.workflow_id, request.tools
            )
            if result is None:
                raise WorkflowExecutionError(request.workflow_id)

            return {"result": result}

    def run(self):
        """Run the async MCP server."""
        host = self.config.server.host
        port = self.config.server.port
        debug = self.config.server.debug

        logger.info(f"Starting async MCP server on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port, debug=debug)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Async MCP Server")
    parser.add_argument("--config", help="Path to configuration file")
    args = parser.parse_args()

    # Get configuration path from command line or environment variable
    config_path = args.config or get_config_path_from_env()

    # Create and run the server
    server = AsyncMCPServer(config_path)
    server.run()


if __name__ == "__main__":
    main()
