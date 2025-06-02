"""
Tool Executor - Execute tools with error handling
"""

import asyncio
import time
import traceback
from typing import Any, Dict, List

from .registry import ToolRegistry

class ToolExecutor:
    """Execute tools with proper error handling."""

    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.execution_history: List[Dict[str, Any]] = []
        self._tool_implementations: Dict[str, Any] = {}

    def register_implementation(self, tool_name: str, implementation):
        """Register a tool implementation."""
        self._tool_implementations[tool_name] = implementation

    async def execute(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return results."""
        start_time = time.time()

        # Validate tool exists
        tool_def = self.registry.get_tool(tool_name)
        if not tool_def:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
                "tool_name": tool_name,
            }

        # Get implementation
        implementation = self._tool_implementations.get(tool_name)
        if not implementation:
            return {
                "success": False,
                "error": f"No implementation for tool '{tool_name}'",
                "tool_name": tool_name,
            }

        try:
            # Execute tool
            if asyncio.iscoroutinefunction(implementation):
                result = await implementation(**parameters)
            else:
                result = await asyncio.get_event_loop().run_in_executor(None, lambda: implementation(**parameters))

            execution_time = time.time() - start_time

            # Record execution
            self.execution_history.append(
                {
                    "tool_name": tool_name,
                    "parameters": parameters,
                    "success": True,
                    "execution_time": execution_time,
                    "timestamp": time.time(),
                }
            )

            return {
                "success": True,
                "result": result,
                "tool_name": tool_name,
                "execution_time": execution_time,
            }

        except Exception as e:
            execution_time = time.time() - start_time

            self.execution_history.append(
                {
                    "tool_name": tool_name,
                    "parameters": parameters,
                    "success": False,
                    "execution_time": execution_time,
                    "timestamp": time.time(),
                    "error": str(e),
                }
            )

            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "tool_name": tool_name,
                "execution_time": execution_time,
            }

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        if not self.execution_history:
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "average_execution_time": 0.0,
            }

        total = len(self.execution_history)
        successful = sum(1 for e in self.execution_history if e["success"])
        total_time = sum(e["execution_time"] for e in self.execution_history)

        return {
            "total_executions": total,
            "success_rate": successful / total if total > 0 else 0.0,
            "average_execution_time": total_time / total if total > 0 else 0.0,
        }
