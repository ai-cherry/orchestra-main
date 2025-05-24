#!/usr/bin/env python3
"""
workflow_manager.py - Cross-Tool Workflow Manager

This module provides a manager for executing workflows across different AI tools,
handling workflow loading, parameter substitution, and result aggregation.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logger = logging.getLogger("mcp-workflow-manager")


class WorkflowManager:
    """Manager for cross-tool workflows."""

    def __init__(self, tool_manager, memory_store):
        """Initialize the workflow manager.

        Args:
            tool_manager: ToolManager instance for executing tool operations
            memory_store: MemoryStore instance for storing workflow results
        """
        self.tool_manager = tool_manager
        self.memory_store = memory_store
        self.workflows = {}

        # Load workflows from directories
        self._load_workflows()

    def _load_workflows(self):
        """Load workflows from directories."""
        # Directories to search for workflows
        workflow_dirs = [
            Path("/workspaces/orchestra-main/mcp_workflows"),
            Path("/workspaces/orchestra-main/user_workflows"),
        ]

        for workflow_dir in workflow_dirs:
            if workflow_dir.exists():
                for workflow_file in workflow_dir.glob("*.json"):
                    try:
                        with open(workflow_file, "r") as f:
                            workflow_def = json.load(f)
                            workflow_id = workflow_def.get("workflow_id")
                            if workflow_id:
                                self.workflows[workflow_id] = workflow_def
                                logger.info(f"Loaded workflow: {workflow_id}")
                    except Exception as e:
                        logger.error(f"Error loading workflow {workflow_file}: {e}")

    def get_available_workflows(self) -> Dict[str, Any]:
        """Get all available workflows.

        Returns:
            Dictionary of workflow IDs to workflow metadata
        """
        return {
            workflow_id: {
                "description": workflow_def.get("description", ""),
                "target_tools": workflow_def.get("target_tools", []),
                "steps": len(workflow_def.get("steps", [])),
            }
            for workflow_id, workflow_def in self.workflows.items()
        }

    def execute_workflow(
        self,
        workflow_id: str,
        parameters: Dict[str, Any] = None,
        tool: Optional[str] = None,
    ) -> Optional[str]:
        """Execute a workflow.

        Args:
            workflow_id: The ID of the workflow to execute
            parameters: Optional parameters to substitute in the workflow
            tool: Optional tool to use for execution

        Returns:
            The workflow result if successful, None otherwise
        """
        if workflow_id not in self.workflows:
            logger.error(f"Workflow not found: {workflow_id}")
            return None

        workflow_def = self.workflows[workflow_id]
        target_tools = workflow_def.get("target_tools", [])

        # Determine the tool to use
        if not tool:
            if target_tools:
                # Use the first target tool that is enabled
                for target_tool in target_tools:
                    if target_tool in self.tool_manager.get_enabled_tools():
                        tool = target_tool
                        break

            if not tool:
                # Use the first enabled tool
                enabled_tools = self.tool_manager.get_enabled_tools()
                if enabled_tools:
                    tool = enabled_tools[0]
                else:
                    logger.error("No enabled tools available")
                    return None

        # Execute the workflow
        logger.info(f"Executing workflow {workflow_id} with tool {tool}")

        # Extract steps
        steps = workflow_def.get("steps", [])
        if not steps:
            logger.error(f"Workflow {workflow_id} has no steps")
            return None

        # Execute steps
        results = []
        for i, step in enumerate(steps):
            step_type = step.get("type")

            if step_type == "mode":
                mode = step.get("mode")
                task = step.get("task")

                # Replace parameters in the task
                if parameters:
                    for param_key, param_value in parameters.items():
                        task = task.replace(f"{{{param_key}}}", str(param_value))

                # Get context from previous steps if needed
                context = None
                if i > 0:
                    context = "\n\n".join(results)

                # Execute the step
                result = self.tool_manager.execute(tool, mode, task, context)
                if result:
                    results.append(result)
                else:
                    logger.error(f"Failed to execute step {i+1} of workflow {workflow_id}")
            else:
                logger.error(f"Unsupported step type: {step_type}")

        # Combine results
        final_result = "\n\n".join(results)

        # Store workflow result in memory
        self.memory_store.set(f"workflow_{workflow_id}_result", final_result, scope="session", tool=tool)

        return final_result

    def execute_cross_tool_workflow(self, workflow_id: str, tools: List[str] = None) -> Optional[str]:
        """Execute a workflow across multiple tools.

        Args:
            workflow_id: The ID of the workflow to execute
            tools: Optional list of tools to use for execution

        Returns:
            The workflow result if successful, None otherwise
        """
        if workflow_id not in self.workflows:
            logger.error(f"Workflow not found: {workflow_id}")
            return None

        self.workflows[workflow_id]

        # Use specified tools or all enabled tools
        if not tools:
            tools = self.tool_manager.get_enabled_tools()

        if not tools:
            logger.error("No tools available for cross-tool workflow")
            return None

        # Execute the workflow with each tool
        results = []
        for tool in tools:
            result = self.execute_workflow(workflow_id, None, tool)
            if result:
                results.append(f"[{tool}] {result}")

        # Combine results
        final_result = "\n\n".join(results)

        # Store workflow result in memory
        self.memory_store.set(f"cross_tool_workflow_{workflow_id}_result", final_result, scope="global")

        return final_result
