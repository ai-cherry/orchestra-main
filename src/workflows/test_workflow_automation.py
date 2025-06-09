"""
Test module for the Workflow Automation Integration.

This module contains tests to validate the workflow automation system and its integration
with other Orchestra AI components.
"""

import unittest
import os
import json
import shutil
from datetime import datetime, timedelta

from .workflow_automation import (
    WorkflowEngine,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowStep,
    WorkflowStatus,
    StepStatus,
    StepType,
    ConnectorType,
    WorkflowAction
)

class TestWorkflowAction(WorkflowAction):
    """Test action for workflow testing."""
    
    def execute(self, parameters, context):
        """Execute the test action."""
        action_type = parameters.get("action_type", "succeed")
        
        if action_type == "succeed":
            return {"status": "success", "message": "Test action succeeded"}
        elif action_type == "fail":
            return {"error": "Test action failed"}
        elif action_type == "set_context":
            key = parameters.get("key")
            value = parameters.get("value")
            if key:
                context[key] = value
            return {"set_context": True, "key": key, "value": value}
        else:
            return {"status": "unknown", "action_type": action_type}

class WorkflowAutomationTests(unittest.TestCase):
    """Test cases for the Workflow Automation Integration."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a test directory for workflow storage
        self.test_dir = os.path.join(os.path.dirname(__file__), "test_workflows")
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Initialize workflow engine
        self.engine = WorkflowEngine(storage_dir=self.test_dir)
        
        # Register test action
        self.engine.register_action("test", TestWorkflowAction())
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove test directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_workflow_creation(self):
        """Test creating a workflow definition."""
        # Create a simple workflow
        workflow_id = self.engine.create_workflow(
            name="Test Workflow",
            description="A test workflow",
            steps=[
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "First step",
                    "step_type": StepType.ACTION,
                    "action": "test",
                    "parameters": {"action_type": "succeed"},
                    "next_steps": ["step2"]
                },
                {
                    "id": "step2",
                    "name": "Step 2",
                    "description": "Second step",
                    "step_type": StepType.ACTION,
                    "action": "test",
                    "parameters": {"action_type": "set_context", "key": "test_key", "value": "test_value"},
                    "next_steps": []
                }
            ],
            start_step_id="step1",
            tags=["test"]
        )
        
        # Verify workflow was created
        self.assertIsNotNone(workflow_id)
        
        # Get workflow
        workflow = self.engine.get_workflow(workflow_id)
        
        # Verify workflow properties
        self.assertEqual(workflow.name, "Test Workflow")
        self.assertEqual(workflow.description, "A test workflow")
        self.assertEqual(workflow.start_step_id, "step1")
        self.assertEqual(len(workflow.steps), 2)
        self.assertIn("step1", workflow.steps)
        self.assertIn("step2", workflow.steps)
        self.assertEqual(workflow.steps["step1"].next_steps, ["step2"])
        self.assertEqual(workflow.steps["step2"].next_steps, [])
    
    def test_workflow_execution(self):
        """Test executing a workflow."""
        # Create a simple workflow
        workflow_id = self.engine.create_workflow(
            name="Test Execution",
            description="A test execution workflow",
            steps=[
                {
                    "id": "step1",
                    "name": "Step 1",
                    "description": "First step",
                    "step_type": StepType.ACTION,
                    "action": "test",
                    "parameters": {"action_type": "succeed"},
                    "next_steps": ["step2"]
                },
                {
                    "id": "step2",
                    "name": "Step 2",
                    "description": "Second step",
                    "step_type": StepType.ACTION,
                    "action": "test",
                    "parameters": {"action_type": "set_context", "key": "test_key", "value": "test_value"},
                    "next_steps": []
                }
            ],
            start_step_id="step1"
        )
        
        # Execute workflow
        execution_id = self.engine.execute_workflow(workflow_id)
        
        # Wait for execution to complete (in a real test, you'd use proper async waiting)
        import time
        max_wait = 5  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            execution = self.engine.get_execution(execution_id)
            if execution.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
                break
            time.sleep(0.1)
        
        # Get execution
        execution = self.engine.get_execution(execution_id)
        
        # Verify execution completed successfully
        self.assertEqual(execution.status, WorkflowStatus.COMPLETED)
        self.assertIsNotNone(execution.started_at)
        self.assertIsNotNone(execution.completed_at)
        self.assertIsNone(execution.error)
        
        # Verify context was updated
        self.assertIn("test_key", execution.context)
        self.assertEqual(execution.context["test_key"], "test_value")
        
        # Verify steps were executed
        self.assertEqual(execution.steps["step1"].status, StepStatus.COMPLETED)
        self.assertEqual(execution.steps["step2"].status, StepStatus.COMPLETED)
    
    def test_condition_step(self):
        """Test conditional workflow execution."""
        # Create a workflow with a condition
        workflow_id = self.engine.create_workflow(
            name="Conditional Workflow",
            description="A workflow with conditions",
            steps=[
                {
                    "id": "step1",
                    "name": "Set Context",
                    "step_type": StepType.ACTION,
                    "action": "test",
                    "parameters": {"action_type": "set_context", "key": "value", "value": 10},
                    "next_steps": ["condition"]
                },
                {
                    "id": "condition",
                    "name": "Check Value",
                    "step_type": StepType.CONDITION,
                    "condition": "value > 5",
                    "next_steps": ["true_branch", "false_branch"]
                },
                {
                    "id": "true_branch",
                    "name": "True Branch",
                    "step_type": StepType.ACTION,
                    "action": "test",
                    "parameters": {"action_type": "set_context", "key": "result", "value": "value_is_greater"},
                    "next_steps": ["end"]
                },
                {
                    "id": "false_branch",
                    "name": "False Branch",
                    "step_type": StepType.ACTION,
                    "action": "test",
                    "parameters": {"action_type": "set_context", "key": "result", "value": "value_is_less"},
                    "next_steps": ["end"]
                },
                {
                    "id": "end",
                    "name": "End",
                    "step_type": StepType.ACTION,
                    "action": "test",
                    "parameters": {"action_type": "succeed"},
                    "next_steps": []
                }
            ],
            start_step_id="step1"
        )
        
        # Execute workflow
        execution_id = self.engine.execute_workflow(workflow_id)
        
        # Wait for execution to complete
        import time
        max_wait = 5  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            execution = self.engine.get_execution(execution_id)
            if execution.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
                break
            time.sleep(0.1)
        
        # Get execution
        execution = self.engine.get_execution(execution_id)
        
        # Verify execution completed successfully
        self.assertEqual(execution.status, WorkflowStatus.COMPLETED)
        
        # Verify the true branch was taken
        self.assertEqual(execution.context["result"], "value_is_greater")
        self.assertEqual(execution.steps["true_branch"].status, StepStatus.COMPLETED)
        self.assertEqual(execution.steps["false_branch"].status, StepStatus.PENDING)
    
    def test_error_handling(self):
        """Test workflow error handling."""
        # Create a workflow with an error
        workflow_id = self.engine.create_workflow(
            name="Error Workflow",
            description="A workflow with an error",
            steps=[
                {
                    "id": "step1",
                    "name": "Succeed Step",
                    "step_type": StepType.ACTION,
                    "action": "test",
                    "parameters": {"action_type": "succeed"},
                    "next_steps": ["error_step"]
                },
                {
                    "id": "error_step",
                    "name": "Error Step",
                    "step_type": StepType.ACTION,
                    "action": "test",
                    "parameters": {"action_type": "fail"},
                    "max_retries": 0,  # No retries to ensure immediate failure
                    "next_steps": ["final_step"]
                },
                {
                    "id": "final_step",
                    "name": "Final Step",
                    "step_type": StepType.ACTION,
                    "action": "test",
                    "parameters": {"action_type": "succeed"},
                    "next_steps": []
                }
            ],
            start_step_id="step1"
        )
        
        # Execute workflow
        execution_id = self.engine.execute_workflow(workflow_id)
        
        # Wait for execution to complete
        import time
        max_wait = 5  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            execution = self.engine.get_execution(execution_id)
            if execution.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
                break
            time.sleep(0.1)
        
        # Get execution
        execution = self.engine.get_execution(execution_id)
        
        # Print debug information
        print(f"Workflow status: {execution.status}")
        print(f"Workflow error: {execution.error}")
        print(f"Step statuses: {[(step_id, step.status) for step_id, step in execution.steps.items()]}")
        
        # Verify execution failed
        self.assertEqual(execution.status, WorkflowStatus.FAILED)
        self.assertIsNotNone(execution.error)
        
        # Verify steps status
        self.assertEqual(execution.steps["step1"].status, StepStatus.COMPLETED)
        self.assertEqual(execution.steps["error_step"].status, StepStatus.FAILED)
        self.assertEqual(execution.steps["final_step"].status, StepStatus.SKIPPED)
    
    def test_integration_with_collaboration_framework(self):
        """Test integration with the AI Persona Collaboration Framework."""
        # This is a mock test since we can't actually import the collaboration framework in the test environment
        # In a real test, you would use actual imports and test with real components
        
        # Create a workflow that uses the collaboration action
        workflow_id = self.engine.create_workflow(
            name="Collaboration Integration",
            description="Tests integration with collaboration framework",
            steps=[
                {
                    "id": "step1",
                    "name": "Collaboration Step",
                    "step_type": StepType.ACTION,
                    "action": "collaboration",
                    "parameters": {
                        "action_type": "create_session",
                        "task_description": "Test collaboration task",
                        "primary_persona": "CHERRY"
                    },
                    "next_steps": []
                }
            ],
            start_step_id="step1"
        )
        
        # We don't actually execute this workflow since it would require the real collaboration framework
        # Instead, we just verify the workflow was created correctly
        workflow = self.engine.get_workflow(workflow_id)
        self.assertEqual(workflow.steps["step1"].action, "collaboration")
        self.assertEqual(workflow.steps["step1"].parameters["action_type"], "create_session")
    
    def test_integration_with_context_management(self):
        """Test integration with the Adaptive Context Management system."""
        # This is a mock test since we can't actually import the context management in the test environment
        
        # Create a workflow that uses the context action
        workflow_id = self.engine.create_workflow(
            name="Context Integration",
            description="Tests integration with context management",
            steps=[
                {
                    "id": "step1",
                    "name": "Context Step",
                    "step_type": StepType.ACTION,
                    "action": "context",
                    "parameters": {
                        "action_type": "add_item",
                        "content": "Test context item",
                        "item_type": "FACT",
                        "source": "test"
                    },
                    "next_steps": []
                }
            ],
            start_step_id="step1"
        )
        
        # We don't actually execute this workflow since it would require the real context management
        # Instead, we just verify the workflow was created correctly
        workflow = self.engine.get_workflow(workflow_id)
        self.assertEqual(workflow.steps["step1"].action, "context")
        self.assertEqual(workflow.steps["step1"].parameters["action_type"], "add_item")
    
    def test_integration_with_knowledge_graph(self):
        """Test integration with the Unified Knowledge Graph."""
        # This is a mock test since we can't actually import the knowledge graph in the test environment
        
        # Create a workflow that uses the knowledge graph action
        workflow_id = self.engine.create_workflow(
            name="Knowledge Graph Integration",
            description="Tests integration with knowledge graph",
            steps=[
                {
                    "id": "step1",
                    "name": "Knowledge Graph Step",
                    "step_type": StepType.ACTION,
                    "action": "knowledge_graph",
                    "parameters": {
                        "action_type": "add_node",
                        "name": "Test Entity",
                        "node_type": "ENTITY",
                        "properties": {"test": "value"}
                    },
                    "next_steps": []
                }
            ],
            start_step_id="step1"
        )
        
        # We don't actually execute this workflow since it would require the real knowledge graph
        # Instead, we just verify the workflow was created correctly
        workflow = self.engine.get_workflow(workflow_id)
        self.assertEqual(workflow.steps["step1"].action, "knowledge_graph")
        self.assertEqual(workflow.steps["step1"].parameters["action_type"], "add_node")

if __name__ == "__main__":
    unittest.main()
