#!/usr/bin/env python3
"""
main.py - MCP Server Main Application

This module provides a simple application that demonstrates the MCP memory system with
Copilot and Gemini integration, showing how memory can be shared and synchronized
between different AI tools.
"""

import os
import sys
import json
import logging
import asyncio
import argparse
from typing import Dict, Any, Optional, List

from mcp_server.config import load_config, MCPConfig
from mcp_server.models.memory import (
    MemoryEntry,
    MemoryType,
    MemoryScope,
    CompressionLevel,
    StorageTier,
    MemoryMetadata,
)
from mcp_server.storage.in_memory_storage import InMemoryStorage
from mcp_server.managers.standard_memory_manager import StandardMemoryManager
from mcp_server.adapters.copilot_adapter import CopilotAdapter
from mcp_server.adapters.gemini_adapter import GeminiAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("mcp-main")


class MCPApplication:
    """Main MCP application class."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the MCP application."""
        self.config = config or {}
        self.storage = None
        self.memory_manager = None
        self.tools = {}
        self.initialized = False

    async def initialize(self) -> bool:
        """Initialize the MCP application."""
        logger.info("Initializing MCP application")

        # Initialize storage
        storage_config = self.config.get("storage", {})
        self.storage = InMemoryStorage(storage_config)

        # Initialize memory manager
        self.memory_manager = StandardMemoryManager(self.storage)

        # Initialize and register tools
        copilot_config = self.config.get("copilot", {})
        gemini_config = self.config.get("gemini", {})

        # Initialize Copilot adapter
        copilot_adapter = CopilotAdapter(copilot_config)
        self.memory_manager.register_tool(copilot_adapter)
        self.tools["copilot"] = copilot_adapter

        # Initialize Gemini adapter
        gemini_adapter = GeminiAdapter(gemini_config)
        self.memory_manager.register_tool(gemini_adapter)
        self.tools["gemini"] = gemini_adapter

        # Initialize memory manager
        init_success = await self.memory_manager.initialize()

        if init_success:
            logger.info("MCP application initialized successfully")
            self.initialized = True
            return True
        else:
            logger.error("Failed to initialize MCP application")
            return False

    async def create_memory(
        self,
        key: str,
        content: Any,
        source_tool: str,
        memory_type: str = "shared",
        scope: str = "session",
        priority: int = 5,
        ttl_seconds: int = 3600,
    ) -> bool:
        """Create a new memory entry."""
        if not self.initialized:
            logger.error("MCP application not initialized")
            return False

        # Create memory entry
        entry = MemoryEntry(
            memory_type=MemoryType(memory_type),
            scope=MemoryScope(scope),
            priority=priority,
            compression_level=CompressionLevel.NONE,
            ttl_seconds=ttl_seconds,
            content=content,
            metadata=MemoryMetadata(
                source_tool=source_tool,
                last_modified=0.0,  # Will be set by manager
                context_relevance=0.8,  # Default high relevance
            ),
        )

        # Create memory
        return await self.memory_manager.create_memory(key, entry, source_tool)

    async def get_memory(self, key: str, tool: str) -> Optional[MemoryEntry]:
        """Get a memory entry for a specific tool."""
        if not self.initialized:
            logger.error("MCP application not initialized")
            return None

        return await self.memory_manager.get_memory(key, tool)

    async def execute_prompt(
        self, prompt: str, mode: str = "chat", tool: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a prompt with a specific tool or all tools."""
        if not self.initialized:
            logger.error("MCP application not initialized")
            return {"error": "MCP application not initialized"}

        results = {}

        if tool:
            # Execute with a specific tool
            if tool in self.tools:
                adapter = self.tools[tool]
                try:
                    response = await adapter.execute(mode, prompt)
                    results[tool] = response
                except Exception as e:
                    logger.error(f"Error executing prompt with {tool}: {e}")
                    results[tool] = f"Error: {str(e)}"
            else:
                results["error"] = f"Tool not found: {tool}"
        else:
            # Execute with all tools
            for tool_name, adapter in self.tools.items():
                try:
                    response = await adapter.execute(mode, prompt)
                    results[tool_name] = response
                except Exception as e:
                    logger.error(f"Error executing prompt with {tool_name}: {e}")
                    results[tool_name] = f"Error: {str(e)}"

        return results

    async def get_status(self) -> Dict[str, Any]:
        """Get the status of the MCP application."""
        if not self.initialized:
            return {"status": "not_initialized"}

        # Get memory status
        memory_status = await self.memory_manager.get_memory_status()

        # Get tool statuses
        tool_statuses = {}
        for tool_name, adapter in self.tools.items():
            try:
                tool_status = await adapter.get_status()
                tool_statuses[tool_name] = tool_status
            except Exception as e:
                logger.error(f"Error getting status for {tool_name}: {e}")
                tool_statuses[tool_name] = {"status": "error", "error": str(e)}

        return {
            "status": "initialized",
            "memory": memory_status,
            "tools": tool_statuses,
        }

    async def demo(self):
        """Run a simple demonstration of the MCP system."""
        if not self.initialized:
            logger.error("MCP application not initialized")
            print("Error: MCP application not initialized")
            return

        print("\n===== MCP MEMORY SYSTEM DEMONSTRATION =====\n")

        # Step 1: Get status
        print("Getting initial status...")
        status = await self.get_status()
        print(f"Status: {json.dumps(status, indent=2)}")

        # Step 2: Create some memory entries
        print("\nCreating memory entries...")

        # Create a shared memory entry from Copilot
        await self.create_memory(
            key="project_overview",
            content="This project implements a memory synchronization system for AI tools.",
            source_tool="copilot",
            memory_type="shared",
            scope="global",
            priority=10,
        )
        print("Created 'project_overview' memory from Copilot")

        # Create tool-specific memory from Gemini
        await self.create_memory(
            key="architecture_analysis",
            content={
                "components": ["memory_manager", "storage", "adapters"],
                "patterns": ["factory", "adapter", "repository"],
                "complexity": "medium",
            },
            source_tool="gemini",
            memory_type="knowledge",
            scope="project",
            priority=8,
        )
        print("Created 'architecture_analysis' memory from Gemini")

        # Step 3: Retrieve memory from different tools
        print("\nRetrieving memory entries from different tools...")

        # Get project overview from Gemini
        project_overview_gemini = await self.get_memory("project_overview", "gemini")
        print(f"'project_overview' from Gemini: {project_overview_gemini.content}")

        # Get architecture analysis from Copilot
        architecture_copilot = await self.get_memory("architecture_analysis", "copilot")
        print(
            f"'architecture_analysis' from Copilot: {json.dumps(architecture_copilot.content, indent=2)}"
        )

        # Step 4: Execute prompts with different tools
        print("\nExecuting prompts with different tools...")

        # Execute a prompt with Copilot
        copilot_result = await self.execute_prompt(
            prompt="Generate a function to calculate fibonacci numbers",
            mode="code",
            tool="copilot",
        )
        print(f"Copilot result: {copilot_result['copilot']}")

        # Execute a prompt with Gemini
        gemini_result = await self.execute_prompt(
            prompt="Explain the advantages of memory synchronization between AI tools",
            mode="chat",
            tool="gemini",
        )
        print(f"Gemini result: {gemini_result['gemini']}")

        # Step 5: Get final status
        print("\nGetting final status...")
        final_status = await self.get_status()
        print(f"Final memory entry count: {final_status['memory']['entry_count']}")
        print(f"Tools: {', '.join(final_status['tools'].keys())}")

        print("\n===== DEMONSTRATION COMPLETE =====\n")


async def main_async(config_path: Optional[str] = None):
    """Async main function."""
    # Load configuration using the config loader
    try:
        config = load_config(config_path)
        logger.info(f"Using configuration with log level: {config.log_level}")

        # Set the log level from config
        logging.getLogger().setLevel(config.log_level)

        # Check for API keys
        has_copilot_key = (
            bool(config.copilot.api_key) if config.copilot.enabled else False
        )
        has_gemini_key = bool(config.gemini.api_key) if config.gemini.enabled else False

        if config.debug:
            logger.info(f"Copilot API key available: {has_copilot_key}")
            logger.info(f"Gemini API key available: {has_gemini_key}")

    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        logger.warning("Using default configuration")
        config = MCPConfig()

    # Create and initialize application
    app = MCPApplication(config.dict())
    init_success = await app.initialize()

    if not init_success:
        logger.error("Failed to initialize MCP application")
        return 1

    # Run the demo
    await app.demo()

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="MCP Memory System")
    parser.add_argument("--config", help="Path to configuration file")
    args = parser.parse_args()

    exit_code = asyncio.run(main_async(args.config))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
