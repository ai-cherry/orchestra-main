#!/usr/bin/env python3
"""
"""
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("mcp-async-server")

# Pydantic models for API requests and responses
class StatusResponse(BaseModel):
    """Status response model."""
    """Memory request model."""
    scope: Optional[str] = "session"
    tool: Optional[str] = None
    ttl: Optional[int] = None

class MemoryResponse(BaseModel):
    """Memory response model."""
    """Memory sync request model."""
    scope: Optional[str] = "session"

class ExecuteRequest(BaseModel):
    """Execute request model."""
    """Execute response model."""
    """Workflow request model."""
    """Cross-tool workflow request model."""
    """Workflow response model."""
    """Success response model."""
    """Error response model."""
    """Asynchronous Model Context Protocol (MCP) Server."""
        """
        """
            logger.info("Configuration loaded successfully")
        except Exception:

            pass
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

        # Add except Exception:
     pass
        """Configure except Exception:
     pass
            return {
                "status": "running",
                "tools": self.tool_manager.get_enabled_tools(),
                "workflows": len(self.workflow_manager.get_available_workflows()),
            }

        # Memory endpoints
        @self.app.get("/api/memory", response_model=MemoryResponse)
        async def get_memory(key: str, scope: str = "session", tool: Optional[str] = None):
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
        async def delete_memory(key: str, scope: str = "session", tool: Optional[str] = None):
            success = await self.memory_store.delete(key, scope, tool)
            if not success:
                raise MemoryDeleteError(key, scope, tool)

            return {"success": True}

        @self.app.post("/api/memory/sync", response_model=SuccessResponse)
        async def sync_memory(request: MemorySyncRequest):
            success = await self.memory_store.sync(request.key, request.source_tool, request.target_tool, request.scope)
            if not success:
                raise MemorySyncError(request.key, request.source_tool, request.target_tool, request.scope)

            return {"success": True}

        # Tool execution endpoint
        @self.app.post("/api/execute", response_model=ExecuteResponse)
        async def execute(request: ExecuteRequest):
            # Check if the tool is enabled
            if request.tool not in self.tool_manager.get_enabled_tools():
                raise ToolNotEnabledError(request.tool)

            # Execute the tool
            result = self.tool_manager.execute(request.tool, request.mode, request.prompt, request.context)
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
            if request.workflow_id not in self.workflow_manager.get_available_workflows():
                raise WorkflowNotFoundError(request.workflow_id)

            # Execute the workflow
            result = self.workflow_manager.execute_workflow(request.workflow_id, request.parameters, request.tool)
            if result is None:
                raise WorkflowExecutionError(request.workflow_id)

            return {"result": result}

        @self.app.post("/api/workflows/cross-tool", response_model=WorkflowResponse)
        async def execute_cross_tool_workflow(request: CrossToolWorkflowRequest):
            # Check if the workflow exists
            if request.workflow_id not in self.workflow_manager.get_available_workflows():
                raise WorkflowNotFoundError(request.workflow_id)

            # Execute the workflow
            result = self.workflow_manager.execute_cross_tool_workflow(request.workflow_id, request.tools)
            if result is None:
                raise WorkflowExecutionError(request.workflow_id)

            return {"result": result}

    def run(self):
        """Run the async MCP server."""
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
