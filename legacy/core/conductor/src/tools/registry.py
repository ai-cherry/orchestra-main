# TODO: Consider adding connection pooling configuration
"""
Tool registry for Cherry AI - defines available tools for agents.
Supports PostgreSQL, Redis, and Weaviate only.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class ToolParameter:
    """Definition of a tool parameter."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[str] = None


@dataclass
class ToolDefinition:
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
        
        # PostgreSQL Database Tools
        self.register_tool(
            ToolDefinition(
                name="postgres_query",
                description="Execute PostgreSQL query for agent memories and persistent data",
                category="database",
                parameters=[
                    ToolParameter(
                        name="query",
                        type="string",
                        description="PostgreSQL query (SELECT, INSERT, UPDATE, DELETE)",
                    ),
                    ToolParameter(
                        name="params",
                        type="list",
                        description="Query parameters for safe execution",
                        required=False,
                        default=[],
                    ),
                    ToolParameter(
                        name="fetch_mode",
                        type="string",
                        description="Result fetch mode: 'all', 'one', 'none'",
                        required=False,
                        default="all",
                    ),
                ],
                output_type="list[dict] | dict | None",
                when_to_use="When you need to store or retrieve structured data, agent memories, or perform complex queries",
                constraints="Always use parameterized queries; respect ACID properties",
                examples=[
                    'postgres_query("SELECT * FROM memories WHERE agent_id = $1", ["coder"])',
                    'postgres_query("INSERT INTO logs (message) VALUES ($1)", ["Started task"])',
                ],
                cost_indicator="low",
                related_tools=["cache_get", "vector_search"],
            )
        )

        self.register_tool(
            ToolDefinition(
                name="postgres_explain",
                description="Get PostgreSQL query execution plan for optimization",
                category="database",
                parameters=[
                    ToolParameter(
                        name="query",
                        type="string",
                        description="PostgreSQL query to analyze",
                    ),
                    ToolParameter(
                        name="analyze",
                        type="boolean",
                        description="Run EXPLAIN ANALYZE for actual execution stats",
                        required=False,
                        default=False,
                    ),
                ],
                output_type="list[dict]",
                when_to_use="For optimizing slow queries or understanding query performance",
                constraints="ANALYZE mode actually executes the query; be careful with DML statements",
                examples=[
                    'postgres_explain("SELECT * FROM large_table WHERE indexed_col = $1")',
                    'postgres_explain("SELECT * FROM memories ORDER BY created_at", analyze=True)',
                ],
                cost_indicator="low",
                related_tools=["postgres_query"],
            )
        )

        # Redis Cache Tools
        self.register_tool(
            ToolDefinition(
                name="cache_get",
                description="Get value from Redis cache",
                category="cache",
                parameters=[ToolParameter(name="key", type="string", description="Cache key to retrieve")],
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
                description="Set value in Redis cache",
                category="cache",
                parameters=[
                    ToolParameter(name="key", type="string", description="Cache key"),
                    ToolParameter(name="value", type="string", description="Value to cache"),
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

        self.register_tool(
            ToolDefinition(
                name="cache_delete",
                description="Delete key from Redis cache",
                category="cache",
                parameters=[ToolParameter(name="key", type="string", description="Cache key to delete")],
                output_type="bool",
                when_to_use="To invalidate cached data or clean up expired entries",
                constraints="Returns False if key doesn't exist",
                cost_indicator="low",
                related_tools=["cache_get", "cache_set"],
            )
        )

        self.register_tool(
            ToolDefinition(
                name="semantic_cache_get",
                description="Get value from Redis semantic cache using vector similarity",
                category="cache",
                parameters=[
                    ToolParameter(name="query", type="string", description="Semantic query to search for"),
                    ToolParameter(
                        name="similarity_threshold",
                        type="float",
                        description="Minimum similarity score (0.0-1.0)",
                        required=False,
                        default=0.8,
                    ),
                ],
                output_type="dict | None",
                when_to_use="For finding semantically similar cached results, avoiding redundant LLM calls",
                constraints="Requires vector embeddings; may have false positives",
                examples=[
                    'semantic_cache_get("How to deploy to cloud?")',
                    'semantic_cache_get("Python error handling", similarity_threshold=0.9)',
                ],
                cost_indicator="medium",
                related_tools=["semantic_cache_set", "vector_search"],
            )
        )

        # Weaviate Vector Search Tools
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
                    ToolParameter(
                        name="where_filter",
                        type="dict",
                        description="Additional filters to apply",
                        required=False,
                        default={},
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
                related_tools=["postgres_query", "text_embedding"],
            )
        )

        self.register_tool(
            ToolDefinition(
                name="vector_store",
                description="Store document in Weaviate with vector embeddings",
                category="search",
                parameters=[
                    ToolParameter(
                        name="content",
                        type="string",
                        description="Text content to store and index",
                    ),
                    ToolParameter(
                        name="collection",
                        type="string",
                        description="Weaviate collection name",
                    ),
                    ToolParameter(
                        name="metadata",
                        type="dict",
                        description="Additional metadata to store",
                        required=False,
                        default={},
                    ),
                ],
                output_type="dict",
                when_to_use="To add new documents for semantic search, building knowledge base",
                constraints="Content should be meaningful chunks; avoid very short text",
                cost_indicator="medium",
                related_tools=["vector_search"],
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
                    'run_script("cherry_ai_status.py")',
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
            return [tool for tool in self.tools.values() if tool.category == category]
        return list(self.tools.values())

    def search_tools(self, query: str, category: Optional[str] = None) -> List[ToolDefinition]:
        """Search tools by query and optional category."""
        query_lower = query.lower()
        results = []

        for tool in self.tools.values():
            if category and tool.category != category:
                continue

            searchable_text = (
                f"{tool.name} {tool.description} {tool.when_to_use} " f"{' '.join(tool.examples or [])} {tool.category}"
            ).lower()

            if query_lower in searchable_text:
                results.append(tool)

        return results

    def get_tools_by_cost(self, max_cost: str = "high") -> List[ToolDefinition]:
        """Get tools filtered by cost indicator."""
        cost_levels = {"low": 1, "medium": 2, "high": 3}
        max_level = cost_levels.get(max_cost, 3)

        return [tool for tool in self.tools.values() if cost_levels.get(tool.cost_indicator, 3) <= max_level]

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
        md += "**Architecture**: PostgreSQL + Redis + Weaviate only\n\n"

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
