#!/usr/bin/env python3
"""
Tests for the WorkflowManager class.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp_server.workflows.workflow_manager import WorkflowManager

class TestWorkflowManager(unittest.TestCase):
    """Test cases for the WorkflowManager class."""
    
    def setUp(self):
        """Set up test environment."""
        self.tool_manager = MagicMock()
        self.memory_store = MagicMock()
        
        # Mock tool_manager.get_enabled_tools to return a list of tools
        self.tool_manager.get_enabled_tools.return_value = ["roo", "gemini"]
        
        # Create a temporary directory for test workflows
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workflow_dir = Path(self.temp_dir.name)
        
        # Create test workflows
        self.create_test_workflows()
        
        # Patch the workflow directories
        self.patcher = patch("mcp_server.workflows.workflow_manager.Path")
        self.mock_path = self.patcher.start()
        
        # Mock the workflow directories to include our temporary directory
        def mock_path_side_effect(p):
            if p.endswith("mcp_workflows"):
                return self.workflow_dir
            elif p.endswith("user_workflows"):
                return Path("/nonexistent/path")  # This path doesn't exist
            return Path(p)
        
        self.mock_path.side_effect = mock_path_side_effect
        
        # Initialize the workflow manager
        self.workflow_manager = WorkflowManager(self.tool_manager, self.memory_store)
    
    def tearDown(self):
        """Clean up test environment."""
        self.patcher.stop()
        self.temp_dir.cleanup()
    
    def create_test_workflows(self):
        """Create test workflow files."""
        # Create a simple workflow
        simple_workflow = {
            "workflow_id": "simple_workflow",
            "description": "A simple workflow",
            "target_tools": ["roo"],
            "steps": [
                {
                    "type": "mode",
                    "mode": "code",
                    "task": "Write a function to add two numbers"
                }
            ]
        }
        
        # Create a workflow with parameters
        param_workflow = {
            "workflow_id": "param_workflow",
            "description": "A workflow with parameters",
            "target_tools": ["roo", "gemini"],
            "steps": [
                {
                    "type": "mode",
                    "mode": "code",
                    "task": "Write a function to {action} {count} {items}"
                },
                {
                    "type": "mode",
                    "mode": "ask",
                    "task": "Explain the function"
                }
            ]
        }
        
        # Create a workflow with an invalid step type
        invalid_workflow = {
            "workflow_id": "invalid_workflow",
            "description": "A workflow with an invalid step",
            "target_tools": ["roo"],
            "steps": [
                {
                    "type": "invalid",
                    "mode": "code",
                    "task": "This step has an invalid type"
                }
            ]
        }
        
        # Write workflows to files
        with open(self.workflow_dir / "simple_workflow.json", "w") as f:
            json.dump(simple_workflow, f)
        
        with open(self.workflow_dir / "param_workflow.json", "w") as f:
            json.dump(param_workflow, f)
        
        with open(self.workflow_dir / "invalid_workflow.json", "w") as f:
            json.dump(invalid_workflow, f)
        
        # Create a file with invalid JSON
        with open(self.workflow_dir / "invalid_json.json", "w") as f:
            f.write("This is not valid JSON")
    
    def test_load_workflows(self):
        """Test loading workflows from directories."""
        # Check that the workflows were loaded
        self.assertEqual(len(self.workflow_manager.workflows), 3)
        self.assertIn("simple_workflow", self.workflow_manager.workflows)
        self.assertIn("param_workflow", self.workflow_manager.workflows)
        self.assertIn("invalid_workflow", self.workflow_manager.workflows)
    
    def test_get_available_workflows(self):
        """Test getting available workflows."""
        workflows = self.workflow_manager.get_available_workflows()
        
        # Check that all workflows are included
        self.assertEqual(len(workflows), 3)
        
        # Check simple workflow metadata
        self.assertEqual(workflows["simple_workflow"]["description"], "A simple workflow")
        self.assertEqual(workflows["simple_workflow"]["target_tools"], ["roo"])
        self.assertEqual(workflows["simple_workflow"]["steps"], 1)
        
        # Check param workflow metadata
        self.assertEqual(workflows["param_workflow"]["description"], "A workflow with parameters")
        self.assertEqual(workflows["param_workflow"]["target_tools"], ["roo", "gemini"])
        self.assertEqual(workflows["param_workflow"]["steps"], 2)
    
    def test_execute_workflow(self):
        """Test executing a workflow."""
        # Mock tool_manager.execute to return successful results
        self.tool_manager.execute.side_effect = [
            "Function implementation"
        ]
        
        # Execute the workflow
        result = self.workflow_manager.execute_workflow("simple_workflow", tool="roo")
        
        # Check that tool_manager.execute was called with the correct arguments
        self.tool_manager.execute.assert_called_once_with(
            "roo", "code", "Write a function to add two numbers", None
        )
        
        # Check the result
        self.assertEqual(result, "Function implementation")
        
        # Check that the result was stored in memory
        self.memory_store.set.assert_called_once_with(
            "workflow_simple_workflow_result",
            "Function implementation",
            scope="session",
            tool="roo"
        )
    
    def test_execute_workflow_with_parameters(self):
        """Test executing a workflow with parameters."""
        # Mock tool_manager.execute to return successful results
        self.tool_manager.execute.side_effect = [
            "Function implementation",
            "Function explanation"
        ]
        
        # Execute the workflow with parameters
        parameters = {
            "action": "sort",
            "count": 10,
            "items": "numbers"
        }
        result = self.workflow_manager.execute_workflow("param_workflow", parameters, "roo")
        
        # Check that tool_manager.execute was called with the correct arguments
        self.assertEqual(self.tool_manager.execute.call_count, 2)
        
        # First call: code mode with parameter substitution
        args1, kwargs1 = self.tool_manager.execute.call_args_list[0]
        self.assertEqual(args1[0], "roo")
        self.assertEqual(args1[1], "code")
        self.assertEqual(args1[2], "Write a function to sort 10 numbers")
        self.assertIsNone(args1[3])  # No context for first step
        
        # Second call: ask mode with context from first step
        args2, kwargs2 = self.tool_manager.execute.call_args_list[1]
        self.assertEqual(args2[0], "roo")
        self.assertEqual(args2[1], "ask")
        self.assertEqual(args2[2], "Explain the function")
        self.assertEqual(args2[3], "Function implementation")  # Context from first step
        
        # Check the result (combined results from both steps)
        self.assertEqual(result, "Function implementation\n\nFunction explanation")
        
        # Check that the result was stored in memory
        self.memory_store.set.assert_called_once_with(
            "workflow_param_workflow_result",
            "Function implementation\n\nFunction explanation",
            scope="session",
            tool="roo"
        )
    
    def test_execute_workflow_with_invalid_step(self):
        """Test executing a workflow with an invalid step."""
        # Execute the workflow
        result = self.workflow_manager.execute_workflow("invalid_workflow", tool="roo")
        
        # Check that tool_manager.execute was not called
        self.tool_manager.execute.assert_not_called()
        
        # Check that the result is an empty string (no steps were executed)
        self.assertEqual(result, "")
        
        # Check that the result was stored in memory
        self.memory_store.set.assert_called_once_with(
            "workflow_invalid_workflow_result",
            "",
            scope="session",
            tool="roo"
        )
    
    def test_execute_workflow_not_found(self):
        """Test executing a workflow that doesn't exist."""
        result = self.workflow_manager.execute_workflow("nonexistent_workflow")
        self.assertIsNone(result)
        self.tool_manager.execute.assert_not_called()
        self.memory_store.set.assert_not_called()
    
    def test_execute_workflow_no_steps(self):
        """Test executing a workflow with no steps."""
        # Create a workflow with no steps
        no_steps_workflow = {
            "workflow_id": "no_steps_workflow",
            "description": "A workflow with no steps",
            "target_tools": ["roo"],
            "steps": []
        }
        
        # Add the workflow to the manager
        self.workflow_manager.workflows["no_steps_workflow"] = no_steps_workflow
        
        # Execute the workflow
        result = self.workflow_manager.execute_workflow("no_steps_workflow")
        
        # Check that the result is None
        self.assertIsNone(result)
        
        # Check that tool_manager.execute was not called
        self.tool_manager.execute.assert_not_called()
    
    def test_execute_workflow_tool_selection(self):
        """Test tool selection when executing a workflow."""
        # Mock tool_manager.execute to return a successful result
        self.tool_manager.execute.return_value = "Function implementation"
        
        # Execute the workflow without specifying a tool
        result = self.workflow_manager.execute_workflow("simple_workflow")
        
        # Check that tool_manager.execute was called with the first target tool
        self.tool_manager.execute.assert_called_once_with(
            "roo", "code", "Write a function to add two numbers", None
        )
        
        # Reset the mock
        self.tool_manager.execute.reset_mock()
        
        # Change the enabled tools to not include the target tool
        self.tool_manager.get_enabled_tools.return_value = ["gemini"]
        
        # Execute the workflow without specifying a tool
        result = self.workflow_manager.execute_workflow("simple_workflow")
        
        # Check that tool_manager.execute was called with the first enabled tool
        self.tool_manager.execute.assert_called_once_with(
            "gemini", "code", "Write a function to add two numbers", None
        )
    
    def test_execute_cross_tool_workflow(self):
        """Test executing a workflow across multiple tools."""
        # Mock tool_manager.execute to return different results for different tools
        def mock_execute(tool, mode, prompt, context):
            return f"{tool} implementation"
        
        self.tool_manager.execute.side_effect = mock_execute
        
        # Execute the workflow across tools
        result = self.workflow_manager.execute_cross_tool_workflow("simple_workflow")
        
        # Check that tool_manager.execute was called for each enabled tool
        self.assertEqual(self.tool_manager.execute.call_count, 2)
        
        # Check the calls
        args1, kwargs1 = self.tool_manager.execute.call_args_list[0]
        self.assertEqual(args1[0], "roo")
        self.assertEqual(args1[1], "code")
        self.assertEqual(args1[2], "Write a function to add two numbers")
        
        args2, kwargs2 = self.tool_manager.execute.call_args_list[1]
        self.assertEqual(args2[0], "gemini")
        self.assertEqual(args2[1], "code")
        self.assertEqual(args2[2], "Write a function to add two numbers")
        
        # Check the result
        self.assertEqual(result, "[roo] roo implementation\n\n[gemini] gemini implementation")
        
        # Check that the result was stored in memory
        self.memory_store.set.assert_called_once_with(
            "cross_tool_workflow_simple_workflow_result",
            "[roo] roo implementation\n\n[gemini] gemini implementation",
            scope="global"
        )
    
    def test_execute_cross_tool_workflow_with_specified_tools(self):
        """Test executing a workflow across specified tools."""
        # Mock tool_manager.execute to return different results for different tools
        def mock_execute(tool, mode, prompt, context):
            return f"{tool} implementation"
        
        self.tool_manager.execute.side_effect = mock_execute
        
        # Execute the workflow across specified tools
        result = self.workflow_manager.execute_cross_tool_workflow(
            "simple_workflow", tools=["roo"]
        )
        
        # Check that tool_manager.execute was called only for the specified tool
        self.tool_manager.execute.assert_called_once_with(
            "roo", "code", "Write a function to add two numbers", None
        )
        
        # Check the result
        self.assertEqual(result, "[roo] roo implementation")
        
        # Check that the result was stored in memory
        self.memory_store.set.assert_called_once_with(
            "cross_tool_workflow_simple_workflow_result",
            "[roo] roo implementation",
            scope="global"
        )
    
    def test_execute_cross_tool_workflow_no_tools(self):
        """Test executing a cross-tool workflow with no tools available."""
        # Mock tool_manager.get_enabled_tools to return an empty list
        self.tool_manager.get_enabled_tools.return_value = []
        
        # Execute the workflow
        result = self.workflow_manager.execute_cross_tool_workflow("simple_workflow")
        
        # Check that the result is None
        self.assertIsNone(result)
        
        # Check that tool_manager.execute was not called
        self.tool_manager.execute.assert_not_called()
        
        # Check that memory_store.set was not called
        self.memory_store.set.assert_not_called()

if __name__ == "__main__":
    unittest.main()