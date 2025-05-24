#!/usr/bin/env python3
"""
tool_manager.py - AI Tool Integration Manager

This module provides a manager for integrating with various AI tools like
Roo, Cline, Gemini, and Copilot, handling execution and context sharing.
"""

import subprocess
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

# Configure logging
logger = logging.getLogger("mcp-tool-manager")


class ToolManager:
    """Manager for AI tool integrations."""

    def __init__(self, config: Dict[str, Any], memory_store):
        """Initialize the tool manager with configuration.

        Args:
            config: Dictionary containing tool configurations
            memory_store: MemoryStore instance for context sharing
        """
        self.config = config
        self.memory_store = memory_store
        self.tools = {}

        # Initialize tool integrations
        for tool_name, tool_config in config.items():
            if tool_config.get("enabled", False):
                self.tools[tool_name] = {
                    "config": tool_config,
                    "status": "initialized",
                }
                logger.info(f"Initialized tool integration: {tool_name}")

    def get_enabled_tools(self) -> List[str]:
        """Get the names of all enabled tools.

        Returns:
            List of enabled tool names
        """
        return list(self.tools.keys())

    def execute(self, tool: str, mode: str, prompt: str, context: Optional[str] = None) -> Optional[str]:
        """Execute a prompt with a specific tool and mode.

        Args:
            tool: The tool to use
            mode: The mode to execute in
            prompt: The prompt to execute
            context: Optional context information

        Returns:
            The execution result if successful, None otherwise
        """
        if tool not in self.tools:
            logger.error(f"Tool not enabled: {tool}")
            return None

        tool_config = self.tools[tool]["config"]

        # Execute based on the tool type
        if tool == "roo":
            return self._execute_roo(mode, prompt, context)
        elif tool == "cline":
            return self._execute_cline(mode, prompt, context)
        elif tool == "gemini":
            return self._execute_gemini(mode, prompt, context)
        elif tool == "copilot":
            return self._execute_copilot(mode, prompt, context)

        logger.error(f"Unsupported tool: {tool}")
        return None

    def _execute_roo(self, mode: str, prompt: str, context: Optional[str] = None) -> Optional[str]:
        """Execute a prompt with Roo.

        Args:
            mode: The mode to execute in
            prompt: The prompt to execute
            context: Optional context information

        Returns:
            The execution result if successful, None otherwise
        """
        try:
            import subprocess

            # Prepare command
            cmd = ["roo-cli", mode, prompt]
            if context:
                # Write context to a temporary file
                context_file = Path("/tmp/roo_context.txt")
                with open(context_file, "w") as f:
                    f.write(context)
                cmd.extend(["--context-file", str(context_file)])

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except ImportError:
            logger.error("roo-cli not found in PATH")
            return None
        except subprocess.CalledProcessError as e:
            logger.error(f"Error executing Roo: {e}")
            return None
        except Exception as e:
            logger.error(f"Error: {e}")
            return None

    def _execute_cline(self, mode: str, prompt: str, context: Optional[str] = None) -> Optional[str]:
        """Execute a prompt with Cline.bot.

        Args:
            mode: The mode to execute in
            prompt: The prompt to execute
            context: Optional context information

        Returns:
            The execution result if successful, None otherwise
        """
        try:
            from cline_integration import ClineModeManager

            # Create mode manager
            mode_manager = ClineModeManager()

            # Execute in the specified mode
            result = mode_manager.execute_in_mode(mode, prompt, context)
            return result
        except ImportError:
            logger.error("cline_integration module not found")
            return None
        except Exception as e:
            logger.error(f"Error executing Cline: {e}")
            return None

    def _execute_gemini(self, mode: str, prompt: str, context: Optional[str] = None) -> Optional[str]:
        """Execute a prompt with Gemini.

        Args:
            mode: The mode to execute in
            prompt: The prompt to execute
            context: Optional context information

        Returns:
            The execution result if successful, None otherwise
        """
        # Placeholder for Gemini integration
        logger.error("Gemini integration not yet implemented")
        return None

    def _execute_copilot(self, mode: str, prompt: str, context: Optional[str] = None) -> Optional[str]:
        """Execute a prompt with Co-pilot.

        Args:
            mode: The mode to execute in
            prompt: The prompt to execute
            context: Optional context information

        Returns:
            The execution result if successful, None otherwise
        """
        # Placeholder for Co-pilot integration
        logger.error("Co-pilot integration not yet implemented")
        return None
