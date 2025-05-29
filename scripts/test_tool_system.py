#!/usr/bin/env python3
"""
Test script for the AI Tool Awareness system
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.orchestrator.src.tools.executor import ToolExecutor
from core.orchestrator.src.tools.registry import ToolRegistry


async def test_tool_system():
    """Test the tool awareness system."""
    print("🔧 Testing AI Tool Awareness System")
    print("=" * 50)

    # Initialize registry
    registry = ToolRegistry()
    print(f"\n✅ Initialized tool registry with {len(registry.tools)} tools")

    # List categories
    categories = set(tool.category for tool in registry.tools.values())
    print(f"\n📁 Available categories: {', '.join(sorted(categories))}")

    # Search for cache tools
    print("\n🔍 Searching for cache tools...")
    cache_tools = registry.search_tools("cache")
    for tool in cache_tools:
        print(f"  - {tool.name}: {tool.description}")

    # Get detailed info about a tool
    print("\n📋 Getting details for 'cache_set'...")
    cache_set = registry.get_tool("cache_set")
    if cache_set:
        print(f"  Name: {cache_set.name}")
        print(f"  Category: {cache_set.category}")
        print(f"  When to use: {cache_set.when_to_use}")
        print("  Parameters:")
        for param in cache_set.parameters:
            print(f"    - {param.name} ({param.type}): {param.description}")

    # Test function calling schema
    print("\n🔌 Converting to function calling schema...")
    functions = registry.to_function_calling_schema()
    print(f"  Generated {len(functions)} function definitions")

    # Export documentation
    print("\n📚 Exporting tool documentation...")
    markdown = registry.export_to_markdown()
    doc_path = "docs/AVAILABLE_TOOLS.md"
    os.makedirs("docs", exist_ok=True)
    with open(doc_path, "w") as f:
        f.write(markdown)
    print(f"  Exported to {doc_path}")

    # Test executor (without actual implementations)
    print("\n🚀 Testing tool executor...")
    executor = ToolExecutor(registry)

    # Simulate tool registration
    async def mock_cache_get(key: str) -> str:
        return f"mock_value_for_{key}"

    executor.register_implementation("cache_get", mock_cache_get)

    # Execute a tool
    result = await executor.execute("cache_get", {"key": "test_key"})
    print(f"  Execution result: {result}")

    # Get execution stats
    stats = executor.get_execution_stats()
    print("\n📊 Execution statistics:")
    print(f"  Total executions: {stats['total_executions']}")
    print(f"  Success rate: {stats['success_rate']:.1%}")
    print(f"  Average time: {stats['average_execution_time']:.3f}s")

    print("\n✅ Tool system test complete!")


if __name__ == "__main__":
    asyncio.run(test_tool_system())
