#!/usr/bin/env python3
"""
optimized_memory_sync.py - Performance-Optimized Memory Synchronization Demo

A streamlined version of the memory synchronization demo that prioritizes
performance over security for single-developer, single-user projects.
"""

import json
import logging
import os
import sys
from typing import Any, Dict, Optional

# Import from simple_mcp instead of the complex memory_sync_engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from simple_mcp import SimpleMemoryStore

# Configure minimal logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("optimized-memory-sync")

class FastToolAdapter:
    """Lightweight adapter for simulating AI tool integration."""

    def __init__(self, name: str, context_window: int):
        """Initialize the tool adapter with minimal overhead."""
        self.name = name
        self.context_window = context_window
        self.memory = {}
        logger.info(f"Initialized {name} with context window: {context_window}")

    def store(self, key: str, content: Any) -> bool:
        """Store content directly without metadata overhead."""
        self.memory[key] = content
        return True

    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve content directly."""
        return self.memory.get(key)

    def delete(self, key: str) -> bool:
        """Delete content directly."""
        if key in self.memory:
            del self.memory[key]
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get simple memory statistics."""
        total_size = sum(len(json.dumps(v)) for v in self.memory.values())
        return {
            "entry_count": len(self.memory),
            "total_size_bytes": total_size,
            "estimated_tokens": total_size // 4,
        }

class OptimizedMemoryManager:
    """Optimized memory manager for single-developer projects."""

    def __init__(self, storage_path: str = "./.mcp_memory"):
        """Initialize with a simple memory store."""
        self.memory_store = SimpleMemoryStore(storage_path)
        self.tools = {}

    def register_tool(self, name: str, context_window: int) -> FastToolAdapter:
        """Register a tool with the memory manager."""
        adapter = FastToolAdapter(name, context_window)
        self.tools[name] = adapter
        return adapter

    def share_memory(self, key: str, content: Any, source_tool: str) -> None:
        """Share memory between tools without complex synchronization."""
        # Store in central memory store
        self.memory_store.set(f"{source_tool}:{key}", content)

        # Share with other tools directly
        for tool_name, adapter in self.tools.items():
            if tool_name != source_tool:
                # Simple content truncation for tools with smaller context windows
                if isinstance(content, str) and len(content) > adapter.context_window // 4:
                    truncated = content[: adapter.context_window // 8] + "... [truncated]"
                    adapter.store(key, truncated)
                else:
                    adapter.store(key, content)

        logger.info(f"Shared memory '{key}' from {source_tool} with {len(self.tools)-1} other tools")

    def get_memory_status(self) -> Dict[str, Any]:
        """Get memory status across all tools."""
        status = {"total_entries": 0, "tools": {}}

        for tool_name, adapter in self.tools.items():
            stats = adapter.get_stats()
            status["tools"][tool_name] = stats
            status["total_entries"] += stats["entry_count"]

        return status

def run_demo():
    """Run the optimized memory synchronization demo."""
    print("=== Optimized Memory Synchronization Demo ===\n")

    # Create memory manager
    manager = OptimizedMemoryManager()

    # Register tools with different context windows
    manager.register_tool("roo", 16000)
    manager.register_tool("cline", 8000)
    manager.register_tool("gemini", 200000)
    manager.register_tool("copilot", 5000)

    print("1. Creating and sharing small memory item...")
    manager.share_memory(
        "project_info",
        "AI Orchestra - A framework for orchestrating multiple AI tools",
        "roo",
    )

    print("\n2. Creating and sharing medium memory item...")
    medium_content = {
        "project": "AI Orchestra",
        "components": ["Memory Sync", "Task Router", "Mode Manager"],
        "status": "In Development",
    }
    manager.share_memory("project_details", medium_content, "cline")

    print("\n3. Creating and sharing large memory item...")
    large_content = "# Strategic Analysis\n\n" + ("Lorem ipsum " * 1000)
    manager.share_memory("strategic_analysis", large_content, "gemini")

    # Display memory status
    status = manager.get_memory_status()
    print("\n=== Memory Status ===")
    print(f"Total Entries: {status['total_entries']}")

    for tool_name, stats in status["tools"].items():
        print(f"\n{tool_name.upper()}:")
        print(f"  Entries: {stats['entry_count']}")
        print(f"  Estimated Tokens: {stats['estimated_tokens']}")

    print("\n=== Demo Complete ===")

if __name__ == "__main__":
    run_demo()
