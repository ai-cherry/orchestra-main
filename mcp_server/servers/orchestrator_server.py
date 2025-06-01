"""
Orchestrator MCP Server - Manages agent coordination
"""

import asyncio
import os
import sys
from typing import Any, Dict, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from agent.app.services.agent_control import run_agent_task, get_all_agents
from agent.app.services.workflow_runner import run_workflow


class OrchestratorServer:
    """MCP server for orchestrator."""

    def __init__(self):
        self.server = Server("orchestrator")
        self.setup_handlers()

    def setup_handlers(self):
        """Setup MCP handlers."""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools."""
            return [
                {
                    "name": "list_agents",
                    "description": "List all available agents",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                    },
                },
                {
                    "name": "run_agent",
                    "description": "Run a specific agent with a task",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "agent_id": {"type": "string", "description": "Agent ID to run"},
                            "task": {"type": "string", "description": "Task description"},
                            "parameters": {"type": "object", "description": "Optional parameters"},
                        },
                        "required": ["agent_id", "task"],
                    },
                },
                {
                    "name": "switch_mode",
                    "description": "Switch orchestrator mode",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "mode": {"type": "string", "enum": ["autonomous", "guided", "assistant"]},
                            "context": {"type": "object"},
                        },
                        "required": ["mode"],
                    },
                },
                {
                    "name": "run_workflow",
                    "description": "Run an orchestration workflow",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "workflow": {"type": "string", "description": "Workflow name"},
                            "params": {"type": "object", "description": "Workflow parameters"},
                        },
                        "required": ["workflow"],
                    },
                },
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""

            if name == "list_agents":
                agents = await get_all_agents()
                agent_list = "\n".join([f"- {agent['id']}: {agent['name']}" for agent in agents])
                return [TextContent(type="text", text=f"Available agents:\n{agent_list}")]

            if name == "run_agent":
                agent_id = arguments.get("agent_id")
                task = arguments.get("task")
                params = arguments.get("parameters", {})
                
                result = await run_agent_task(agent_id, task, params)
                return [TextContent(type="text", text=f"Agent {agent_id} result: {result}")]

            if name == "switch_mode":
                mode = arguments.get("mode")
                context = arguments.get("context", {})
                # Store mode in context for future use
                result = f"Switched to {mode} mode with context: {context}"
                return [TextContent(type="text", text=result)]

            if name == "run_workflow":
                workflow_name = arguments.get("workflow")
                params = arguments.get("params", {})
                
                result = await run_workflow(workflow_name, params)
                return [TextContent(type="text", text=f"Workflow '{workflow_name}' result: {result}")]

            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream)


if __name__ == "__main__":
    server = OrchestratorServer()
    asyncio.run(server.run())
