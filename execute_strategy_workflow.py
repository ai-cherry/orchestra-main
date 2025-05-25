#!/usr/bin/env python3
"""
execute_strategy_workflow.py - Run the strategic analysis workflow through Roo

This script executes the AI tool integration strategy workflow using Roo's existing
workflow management capabilities, bypassing the need for the new MCP CLI until
we have all dependencies installed.
"""

import json
import logging
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("strategy-workflow-executor")


def load_workflow(workflow_path):
    """Load a workflow definition from a JSON file."""
    try:
        with open(workflow_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading workflow: {e}")
        return None


def execute_roo_workflow(workflow_def):
    """Execute a workflow using Roo's workflow manager."""
    try:
        # Import Roo's workflow manager
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from roo_workflow_manager import SubtaskManager

        # Create subtask manager instance
        manager = SubtaskManager()

        # Extract workflow details
        main_task = workflow_def.get(
            "description", "Execute strategic analysis workflow"
        )
        subtasks = workflow_def.get("steps", [])

        # Execute the workflow
        logger.info(f"Executing workflow: {workflow_def.get('workflow_id')}")
        result = manager.orchestrate_workflow(main_task, subtasks)

        # Save the result to a file
        output_dir = Path("mcp_workflows/results")
        output_dir.mkdir(exist_ok=True, parents=True)

        output_file = output_dir / f"{workflow_def.get('workflow_id')}_result.md"
        with open(output_file, "w") as f:
            f.write(result)

        logger.info(f"Workflow results saved to: {output_file}")
        return result

    except ImportError:
        logger.error(
            "Could not import Roo's workflow manager. Make sure roo_workflow_manager.py is available."
        )
        return None
    except Exception as e:
        logger.error(f"Error executing workflow: {e}")
        return None


def main():
    """Main function to execute the strategic analysis workflow."""
    # Path to the workflow definition
    workflow_path = Path("mcp_workflows/ai_tool_integration_strategy.json")

    # Load the workflow
    workflow_def = load_workflow(workflow_path)
    if not workflow_def:
        logger.error(f"Failed to load workflow from {workflow_path}")
        sys.exit(1)

    # Execute the workflow
    result = execute_roo_workflow(workflow_def)
    if result:
        print("\n" + "=" * 80)
        print("STRATEGIC ANALYSIS RESULTS")
        print("=" * 80)
        print(result)
        print("=" * 80)
    else:
        logger.error("Failed to execute workflow")
        sys.exit(1)


if __name__ == "__main__":
    main()
