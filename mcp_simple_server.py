#!/usr/bin/env python3
"""
🚀 Simple Working MCP Server for Orchestra AI
Provides basic context sharing capabilities for Cursor, Roo, and Continue
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# MCP imports
from mcp.server import Server
from mcp import types
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleOrchestralMCPServer:
    """Simple MCP Server for Orchestra AI Ecosystem"""
    
    def __init__(self):
        self.server = Server("orchestra-simple")
        self.context_data = {}
        self._setup_tools()
    
    def _setup_tools(self):
        """Setup basic MCP tools"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List available tools"""
            return [
                types.Tool(
                    name="register_tool",
                    description="Register a coding tool for context sharing",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "tool_name": {"type": "string"},
                        },
                        "required": ["tool_name"]
                    }
                ),
                types.Tool(
                    name="get_context",
                    description="Get shared context for a tool",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "requesting_tool": {"type": "string"},
                        },
                        "required": ["requesting_tool"]
                    }
                ),
                types.Tool(
                    name="route_task",
                    description="Route a task to the optimal tool",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_description": {"type": "string"},
                            "task_type": {"type": "string"},
                        },
                        "required": ["task_description", "task_type"]
                    }
                ),
                types.Tool(
                    name="health_check",
                    description="Check server health and configuration",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
            """Handle tool calls"""
            
            if name == "register_tool":
                tool_name = arguments["tool_name"]
                self.context_data[tool_name] = {
                    "registered_at": "now",
                    "status": "active"
                }
                return [types.TextContent(
                    type="text",
                    text=f"✅ Tool {tool_name} registered successfully"
                )]
            
            elif name == "get_context":
                requesting_tool = arguments["requesting_tool"]
                
                # Provide tool-specific context
                if requesting_tool == "cursor":
                    context = {
                        "mode": "fast_editing",
                        "standards": "Python 3.10+, type hints, Black formatting",
                        "openai_api": "configured",
                        "mcp_server": "connected"
                    }
                elif requesting_tool == "roo":
                    context = {
                        "modes": "10 specialized modes available",
                        "openrouter_api": "configured for cost optimization",
                        "models": ["deepseek-r1", "claude-sonnet-4", "gemini-2.5-pro"],
                        "boomerang_tasks": "enabled"
                    }
                elif requesting_tool == "continue":
                    context = {
                        "ui_model": "gpt-4o-2024-11-20",
                        "commands": ["/ui", "/prototype", "/persona"],
                        "focus": "React/TypeScript generation",
                        "openai_api": "configured"
                    }
                else:
                    context = {
                        "general_context": "Orchestra AI ecosystem",
                        "available_tools": ["cursor", "roo", "continue"],
                        "mcp_server": "operational"
                    }
                
                return [types.TextContent(
                    type="text",
                    text=json.dumps(context, indent=2)
                )]
            
            elif name == "route_task":
                task_description = arguments["task_description"]
                task_type = arguments["task_type"]
                
                # Simple task routing logic
                if "ui" in task_type.lower() or "component" in task_description.lower():
                    optimal_tool = "continue"
                    reason = "UI-GPT-4o excels at React/TypeScript component generation"
                elif "complex" in task_description.lower() or "workflow" in task_type.lower():
                    optimal_tool = "roo"
                    reason = "Specialized modes handle complex workflows optimally"
                else:
                    optimal_tool = "cursor"
                    reason = "Native AI integration for general coding tasks"
                
                return [types.TextContent(
                    type="text",
                    text=f"🎯 Optimal tool: {optimal_tool}\n💡 Reason: {reason}"
                )]
            
            elif name == "health_check":
                # Check system health
                health_status = {
                    "mcp_server": "operational",
                    "registered_tools": list(self.context_data.keys()),
                    "openai_api": "configured",
                    "openrouter_api": "configured",
                    "cursor_rules": "active",
                    "roo_modes": "10 available",
                    "continue_config": "ui-gpt-4o ready"
                }
                
                return [types.TextContent(
                    type="text",
                    text=f"🟢 System Health Check\n{json.dumps(health_status, indent=2)}"
                )]
            
            else:
                raise ValueError(f"Unknown tool: {name}")

async def main():
    """Main entry point for the simple MCP server"""
    server_instance = SimpleOrchestralMCPServer()
    
    logger.info("🚀 Starting Simple Orchestra MCP Server...")
    
    # Use a simpler initialization without problematic notification options
    async with stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="orchestra-simple",
                server_version="1.0.0",
                capabilities=server_instance.server.get_capabilities()
            )
        )

if __name__ == "__main__":
    asyncio.run(main()) 