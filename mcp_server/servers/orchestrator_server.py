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

# Import existing functions from agent_control
from agent.app.services.agent_control import (
    get_agent_logs,
    restart_agent,
    get_agent_config,
    update_agent_config,
    get_agent_metrics
)
from agent.app.services.workflow_runner import run_workflow as run_workflow_sync


# Create the missing functions as stubs
async def get_all_agents() -> List[Dict[str, Any]]:
    """Get all available agents."""
    # Stub implementation - in production, this would query the database
    return [
        {"id": "data-processor", "name": "Data Processing Agent", "status": "active"},
        {"id": "nlp-analyzer", "name": "NLP Analysis Agent", "status": "active"},
        {"id": "task-scheduler", "name": "Task Scheduler Agent", "status": "active"},
        {"id": "monitoring", "name": "System Monitor Agent", "status": "active"},
    ]


async def run_agent_task(agent_id: str, task: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
    """Run a task on a specific agent."""
    # Stub implementation - in production, this would dispatch to the actual agent
    if parameters is None:
        parameters = {}
    
    # Simulate agent execution
    result = {
        "agent_id": agent_id,
        "task": task,
        "status": "completed",
        "output": f"Executed task '{task}' on agent '{agent_id}' with parameters: {parameters}",
        "metrics": get_agent_metrics(agent_id)
    }
    return result


async def run_workflow(workflow_name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Async wrapper for workflow runner."""
    if params is None:
        params = {}
    
    # Call the sync function - in production, this would be properly async
    result = run_workflow_sync(workflow_name)
    result["params"] = params
    return result


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
                Tool(
                    name="list_agents",
                    description="List all available agents",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="run_agent",
                    description="Run a specific agent with a task",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent_id": {"type": "string", "description": "Agent ID to run"},
                            "task": {"type": "string", "description": "Task description"},
                            "parameters": {"type": "object", "description": "Optional parameters"},
                        },
                        "required": ["agent_id", "task"],
                    },
                ),
                Tool(
                    name="switch_mode",
                    description="Switch orchestrator mode",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "mode": {"type": "string", "enum": ["autonomous", "guided", "assistant"]},
                            "context": {"type": "object"},
                        },
                        "required": ["mode"],
                    },
                ),
                Tool(
                    name="run_workflow",
                    description="Run an orchestration workflow",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow": {"type": "string", "description": "Workflow name"},
                            "params": {"type": "object", "description": "Workflow parameters"},
                        },
                        "required": ["workflow"],
                    },
                ),
                Tool(
                    name="get_agent_status",
                    description="Get status and metrics for a specific agent",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent_id": {"type": "string", "description": "Agent ID to check"},
                        },
                        "required": ["agent_id"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""

            if name == "list_agents":
                agents = await get_all_agents()
                agent_list = "\n".join([f"- {agent['id']}: {agent['name']} ({agent['status']})" for agent in agents])
                return [TextContent(type="text", text=f"Available agents:\n{agent_list}")]

            if name == "run_agent":
                agent_id = arguments.get("agent_id")
                task = arguments.get("task")
                params = arguments.get("parameters", {})
                
                result = await run_agent_task(agent_id, task, params)
                return [TextContent(type="text", text=f"Agent {agent_id} result:\nStatus: {result['status']}\nOutput: {result['output']}")]

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

            if name == "get_agent_status":
                agent_id = arguments.get("agent_id")
                
                # Get various agent information
                config = get_agent_config(agent_id)
                metrics = get_agent_metrics(agent_id)
                logs = get_agent_logs(agent_id)
                
                status_text = f"""Agent Status for {agent_id}:
Configuration: {config}
Metrics: CPU: {metrics['cpu']}%, Memory: {metrics['mem']}MB
Recent Logs: {', '.join(logs['logs'][:2])}"""
                
                return [TextContent(type="text", text=status_text)]

            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, 
                write_stream,
                initialization_options={}  # Add empty initialization options
            )


if __name__ == "__main__":
    server = OrchestratorServer()
    asyncio.run(server.run())
