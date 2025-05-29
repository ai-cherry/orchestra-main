"""
Tools MCP Server - Exposes available tools to AI assistants
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict, List

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from core.orchestrator.src.tools.executor import ToolExecutor

# Import our tool system
from core.orchestrator.src.tools.registry import ToolRegistry


class ToolsServer:
    """MCP server for tool discovery and execution."""

    def __init__(self):
        self.server = Server("tools")
        self.registry = ToolRegistry()
        self.executor = ToolExecutor(self.registry)
        self._register_tool_implementations()
        self.setup_handlers()

    def _register_tool_implementations(self):
        """Register tool implementations with executor."""
        # Import implementations
        from core.orchestrator.src.tools.implementations import cache_tools

        # Register cache tools
        self.executor.register_implementation("cache_get", cache_tools.cache_get)
        self.executor.register_implementation("cache_set", cache_tools.cache_set)
        self.executor.register_implementation("cache_delete", cache_tools.cache_delete)

        # More implementations would be registered here

    def setup_handlers(self):
        """Setup MCP handlers."""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List all available tools."""
            tools = []

            # Add execution tools
            for tool_name, tool_def in self.registry.tools.items():
                properties = {}
                required = []

                for param in tool_def.parameters:
                    properties[param.name] = {
                        "type": param.type,
                        "description": param.description,
                    }
                    if param.required:
                        required.append(param.name)

                tools.append(
                    Tool(
                        name=f"execute_{tool_name}",
                        description=f"{tool_def.description} | When to use: {tool_def.when_to_use}",
                        inputSchema={
                            "type": "object",
                            "properties": properties,
                            "required": required,
                        },
                    )
                )

            # Add meta tools
            tools.extend(
                [
                    Tool(
                        name="search_tools",
                        description="Search for tools by query and optional category",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query",
                                },
                                "category": {
                                    "type": "string",
                                    "description": "Optional category filter (database, cache, search, system, ai)",
                                },
                            },
                            "required": ["query"],
                        },
                    ),
                    Tool(
                        name="get_tool_details",
                        description="Get detailed information about a specific tool",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "tool_name": {
                                    "type": "string",
                                    "description": "Name of the tool",
                                }
                            },
                            "required": ["tool_name"],
                        },
                    ),
                    Tool(
                        name="list_tool_categories",
                        description="List all available tool categories",
                        inputSchema={"type": "object", "properties": {}},
                    ),
                ]
            )

            return tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""

            if name == "search_tools":
                results = self.registry.search_tools(arguments["query"], arguments.get("category"))

                # Format results
                output = f"Found {len(results)} tools:\n\n"
                for tool in results:
                    output += f"**{tool.name}** ({tool.category})\n"
                    output += f"  {tool.description}\n"
                    output += f"  When to use: {tool.when_to_use}\n"
                    if tool.cost_indicator:
                        output += f"  Cost: {tool.cost_indicator}\n"
                    output += "\n"

                return [TextContent(type="text", text=output)]

            elif name == "get_tool_details":
                tool = self.registry.get_tool(arguments["tool_name"])
                if tool:
                    output = f"# {tool.name}\n\n"
                    output += f"**Category**: {tool.category}\n"
                    output += f"**Description**: {tool.description}\n"
                    output += f"**When to use**: {tool.when_to_use}\n\n"

                    if tool.parameters:
                        output += "**Parameters**:\n"
                        for param in tool.parameters:
                            req = "required" if param.required else "optional"
                            output += f"- `{param.name}` ({param.type}, {req}): {param.description}"
                            if param.default is not None:
                                output += f" (default: {param.default})"
                            output += "\n"
                        output += "\n"

                    if tool.examples:
                        output += "**Examples**:\n```python\n"
                        output += "\n".join(tool.examples)
                        output += "\n```\n\n"

                    if tool.constraints:
                        output += f"**Constraints**: {tool.constraints}\n\n"

                    if tool.related_tools:
                        output += f"**Related tools**: {', '.join(tool.related_tools)}\n"

                    return [TextContent(type="text", text=output)]
                else:
                    return [
                        TextContent(
                            type="text",
                            text=f"Tool '{arguments['tool_name']}' not found",
                        )
                    ]

            elif name == "list_tool_categories":
                categories = set(tool.category for tool in self.registry.tools.values())
                output = "Available tool categories:\n\n"
                for category in sorted(categories):
                    tools_in_cat = [t for t in self.registry.tools.values() if t.category == category]
                    output += f"- **{category}** ({len(tools_in_cat)} tools)\n"

                return [TextContent(type="text", text=output)]

            elif name.startswith("execute_"):
                tool_name = name[8:]  # Remove "execute_" prefix
                result = await self.executor.execute(tool_name, arguments)

                if result["success"]:
                    output = "✅ Tool executed successfully\n\n"
                    output += f"**Result**: {json.dumps(result['result'], indent=2)}\n"
                    output += f"**Execution time**: {result['execution_time']:.3f}s"
                else:
                    output = "❌ Tool execution failed\n\n"
                    output += f"**Error**: {result['error']}\n"
                    if "traceback" in result:
                        output += f"\n**Traceback**:\n```\n{result['traceback']}\n```"

                return [TextContent(type="text", text=output)]

            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream)


if __name__ == "__main__":
    server = ToolsServer()
    asyncio.run(server.run())
