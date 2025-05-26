"""
Tool Registry - Central registry for all available tools with rich metadata
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class ToolParameter(BaseModel):
    """Definition of a tool parameter."""

    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None


class ToolDefinition(BaseModel):
    """Rich definition of a tool with metadata."""

    name: str
    description: str
    category: str  # "database", "cache", "deployment", "analysis", etc.
    parameters: List[ToolParameter]
    output_type: str
    when_to_use: str
    constraints: Optional[str] = None
    examples: Optional[List[str]] = None
    cost_indicator: Optional[str] = None  # "low", "medium", "high"
    related_tools: Optional[List[str]] = None


class ToolRegistry:
    """Central registry for all available tools."""

    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self._load_builtin_tools()

    def _load_builtin_tools(self):
        """Load built-in tool definitions."""

        # MongoDB Tools
        self.register_tool(
            ToolDefinition(
                name="mongodb_query",
                description="Query MongoDB for agent memories and persistent data",
                category="database",
                parameters=[
                    ToolParameter(
                        name="collection",
                        type="string",
                        description="MongoDB collection name",
                    ),
                    ToolParameter(
                        name="query", type="object", description="MongoDB query object"
                    ),
                    ToolParameter(
                        name="projection",
                        type="object",
                        description="Fields to include/exclude",
                        required=False,
                        default={},
                    ),
                    ToolParameter(
                        name="limit",
                        type="integer",
                        description="Maximum number of results",
                        required=False,
                        default=10,
                    ),
                    ToolParameter(
                        name="sort",
                        type="object",
                        description="Sort criteria",
                        required=False,
                        default={},
                    ),
                ],
                output_type="list[dict]",
                when_to_use="When you need to retrieve stored agent memories, user data, or perform complex queries",
                constraints="Queries should use indexes when possible; avoid full collection scans",
                examples=[
                    'mongodb_query("memories", {"agent_id": "coder"}, limit=5)',
                    'mongodb_query("users", {"active": true}, projection={"name": 1})',
                ],
                cost_indicator="medium",
                related_tools=["cache_get", "mongodb_aggregate"],
            )
        )

        # Cache Tools
        self.register_tool(
            ToolDefinition(
                name="cache_get",
                description="Get value from Redis/DragonflyDB cache",
                category="cache",
                parameters=[
                    ToolParameter(
                        name="key", type="string", description="Cache key to retrieve"
                    )
                ],
                output_type="string | None",
                when_to_use="For fast retrieval of frequently accessed data, session data, or temporary values",
                constraints="Data may expire; always handle None returns",
                examples=[
                    'cache_get("user:123:preferences")',
                    'cache_get("api:rate_limit:client_xyz")',
                ],
                cost_indicator="low",
                related_tools=["cache_set", "cache_delete"],
            )
        )

        self.register_tool(
            ToolDefinition(
                name="cache_set",
                description="Set value in Redis/DragonflyDB cache",
                category="cache",
                parameters=[
                    ToolParameter(name="key", type="string", description="Cache key"),
                    ToolParameter(
                        name="value", type="string", description="Value to cache"
                    ),
                    ToolParameter(
                        name="ttl",
                        type="integer",
                        description="Time to live in seconds",
                        required=False,
                        default=3600,
                    ),
                ],
                output_type="bool",
                when_to_use="To cache frequently accessed data, API responses, or computation results",
                constraints="Keep TTL appropriate to data freshness needs",
                cost_indicator="low",
                related_tools=["cache_get", "cache_delete"],
            )
        )

        # Vector Search Tools
        self.register_tool(
            ToolDefinition(
                name="vector_search",
                description="Semantic search using Weaviate vector database",
                category="search",
                parameters=[
                    ToolParameter(
                        name="query",
                        type="string",
                        description="Natural language search query",
                    ),
                    ToolParameter(
                        name="collection",
                        type="string",
                        description="Weaviate collection to search",
                    ),
                    ToolParameter(
                        name="limit",
                        type="integer",
                        description="Maximum results",
                        required=False,
                        default=5,
                    ),
                ],
                output_type="list[dict]",
                when_to_use="For semantic/similarity search, finding related content, or AI-powered search",
                constraints="Requires text to be pre-indexed with embeddings",
                examples=[
                    'vector_search("how to deploy to cloud", "documentation", limit=3)',
                    'vector_search("error handling patterns", "code_examples")',
                ],
                cost_indicator="medium",
                related_tools=["mongodb_query", "text_embedding"],
            )
        )

        # System Tools
        self.register_tool(
            ToolDefinition(
                name="run_script",
                description="Execute a Python script from the scripts/ directory",
                category="system",
                parameters=[
                    ToolParameter(
                        name="script_name",
                        type="string",
                        description="Script filename (without path)",
                    ),
                    ToolParameter(
                        name="args",
                        type="list",
                        description="Command line arguments",
                        required=False,
                        default=[],
                    ),
                ],
                output_type="dict",
                when_to_use="To run automation scripts, validators, or system checks",
                constraints="Only scripts in scripts/ directory; runs with current environment",
                examples=[
                    'run_script("orchestra_status.py")',
                    'run_script("ai_code_reviewer.py", ["--check-file", "main.py"])',
                ],
                cost_indicator="low",
                related_tools=["shell_command", "python_eval"],
            )
        )

        # LLM Tools
        self.register_tool(
            ToolDefinition(
                name="llm_query",
                description="Query an LLM for analysis, generation, or decision-making",
                category="ai",
                parameters=[
                    ToolParameter(
                        name="prompt",
                        type="string",
                        description="The prompt/question for the LLM",
                    ),
                    ToolParameter(
                        name="model",
                        type="string",
                        description="Model to use",
                        required=False,
                        default="gpt-4",
                    ),
                    ToolParameter(
                        name="temperature",
                        type="float",
                        description="Temperature for randomness",
                        required=False,
                        default=0.7,
                    ),
                ],
                output_type="string",
                when_to_use="For complex analysis, content generation, or decision-making requiring AI",
                constraints="Costs vary by model; be mindful of token usage",
                examples=[
                    'llm_query("Analyze this error and suggest fixes: {error}")',
                    'llm_query("Generate unit tests for this function", model="gpt-4", temperature=0.2)',
                ],
                cost_indicator="high",
                related_tools=["llm_stream", "llm_embed"],
            )
        )

    def register_tool(self, tool: ToolDefinition):
        """Register a new tool."""
        self.tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get tool definition by name."""
        return self.tools.get(name)

    def list_tools(self, category: Optional[str] = None) -> List[ToolDefinition]:
        """List all tools, optionally filtered by category."""
        if category:
            return [t for t in self.tools.values() if t.category == category]
        return list(self.tools.values())

    def search_tools(
        self, query: str, category: Optional[str] = None
    ) -> List[ToolDefinition]:
        """Search tools by query and optional category."""
        results = []
        query_lower = query.lower()

        for tool in self.tools.values():
            if category and tool.category != category:
                continue

            # Search in multiple fields
            searchable_text = (
                f"{tool.name} {tool.description} {tool.when_to_use} "
                f"{' '.join(tool.examples or [])} {tool.category}"
            ).lower()

            if query_lower in searchable_text:
                results.append(tool)

        return results

    def get_tools_by_cost(self, max_cost: str = "high") -> List[ToolDefinition]:
        """Get tools filtered by cost indicator."""
        cost_levels = {"low": 1, "medium": 2, "high": 3}
        max_level = cost_levels.get(max_cost, 3)

        return [
            tool
            for tool in self.tools.values()
            if cost_levels.get(tool.cost_indicator, 3) <= max_level
        ]

    def to_function_calling_schema(self) -> List[Dict]:
        """Convert to OpenAI function calling format."""
        functions = []
        for tool in self.tools.values():
            properties = {}
            required = []

            for param in tool.parameters:
                properties[param.name] = {
                    "type": param.type,
                    "description": param.description,
                }
                if param.default is not None:
                    properties[param.name]["default"] = param.default
                if param.required:
                    required.append(param.name)

            functions.append(
                {
                    "name": tool.name,
                    "description": f"{tool.description} ({tool.when_to_use})",
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                    },
                }
            )

        return functions

    def export_to_markdown(self) -> str:
        """Export all tools as markdown documentation."""
        md = "# Available Tools\n\n"

        # Group by category
        categories = {}
        for tool in self.tools.values():
            if tool.category not in categories:
                categories[tool.category] = []
            categories[tool.category].append(tool)

        for category, tools in sorted(categories.items()):
            md += f"## {category.title()} Tools\n\n"

            for tool in sorted(tools, key=lambda t: t.name):
                md += f"### {tool.name}\n\n"
                md += f"**Description**: {tool.description}\n\n"
                md += f"**When to use**: {tool.when_to_use}\n\n"

                if tool.parameters:
                    md += "**Parameters**:\n"
                    for param in tool.parameters:
                        req = "required" if param.required else "optional"
                        md += f"- `{param.name}` ({param.type}, {req}): {param.description}"
                        if param.default is not None:
                            md += f" (default: {param.default})"
                        md += "\n"
                    md += "\n"

                if tool.examples:
                    md += "**Examples**:\n```python\n"
                    md += "\n".join(tool.examples)
                    md += "\n```\n\n"

                if tool.constraints:
                    md += f"**Constraints**: {tool.constraints}\n\n"

                if tool.cost_indicator:
                    md += f"**Cost**: {tool.cost_indicator}\n\n"

                if tool.related_tools:
                    md += f"**Related tools**: {', '.join(tool.related_tools)}\n\n"

                md += "---\n\n"

        return md
