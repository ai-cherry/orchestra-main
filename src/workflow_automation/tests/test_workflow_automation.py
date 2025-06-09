"""
Unit tests for the workflow automation system.

This module contains tests for the core components of the workflow automation system,
including models, engine, connectors, and integration points.
"""

import unittest
import asyncio
from unittest.mock import MagicMock, patch
import json
import os
import sys
from datetime import datetime

# Add parent directory to path to import workflow_automation
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflow_automation.models import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowInstance,
    WorkflowStatus,
    StepStatus,
    ErrorHandler,
    ErrorAction,
    WorkflowTrigger
)
from workflow_automation.engine import (
    WorkflowEngine,
    WorkflowStorageManager,
    EventBus,
    StepExecutor
)
from workflow_automation.connectors import (
    BaseConnector,
    ConnectorRegistry,
    ConnectorStepExecutor,
    EmailConnector,
    RestApiConnector
)


class TestWorkflowModels(unittest.TestCase):
    """Test cases for workflow data models."""
    
    def test_workflow_definition(self):
        """Test creating a workflow definition."""
        definition = WorkflowDefinition(
            id="test-workflow",
            name="Test Workflow",
            description="A test workflow"
        )
        
        self.assertEqual(definition.id, "test-workflow")
        self.assertEqual(definition.name, "Test Workflow")
        self.assertEqual(definition.description, "A test workflow")
        self.assertEqual(definition.version, "1.0.0")
        self.assertEqual(len(definition.steps), 0)
        self.assertEqual(len(definition.triggers), 0)
        self.assertEqual(len(definition.variables), 0)
        self.assertEqual(len(definition.error_handlers), 0)
    
    def test_workflow_step(self):
        """Test creating a workflow step."""
        step = WorkflowStep(
            id="test-step",
            type="test-type",
            parameters={"param1": "value1"},
            depends_on=["step1", "step2"]
        )
        
        self.assertEqual(step.id, "test-step")
        self.assertEqual(step.type, "test-type")
        self.assertEqual(step.parameters, {"param1": "value1"})
        self.assertEqual(step.depends_on, ["step1", "step2"])
    
    def test_workflow_instance(self):
        """Test creating a workflow instance."""
        instance = WorkflowInstance(
            workflow_id="test-workflow",
            input_data={"input1": "value1"},
            variables={"var1": "value1"}
        )
        
        self.assertEqual(instance.workflow_id, "test-workflow")
        self.assertEqual(instance.status, WorkflowStatus.PENDING)
        self.assertEqual(instance.input_data, {"input1": "value1"})
        self.assertEqual(instance.variables, {"var1": "value1"})
        self.assertIsNone(instance.start_time)
        self.assertIsNone(instance.end_time)
        self.assertIsNone(instance.current_step_id)
        self.assertEqual(len(instance.step_executions), 0)
    
    def test_workflow_instance_to_dict(self):
        """Test converting a workflow instance to a dictionary."""
        instance = WorkflowInstance(
            id="test-instance",
            workflow_id="test-workflow",
            status=WorkflowStatus.RUNNING,
            start_time="2025-06-09T04:00:00Z",
            input_data={"input1": "value1"},
            variables={"var1": "value1"}
        )
        
        instance_dict = instance.to_dict()
        
        self.assertEqual(instance_dict["id"], "test-instance")
        self.assertEqual(instance_dict["workflow_id"], "test-workflow")
        self.assertEqual(instance_dict["status"], WorkflowStatus.RUNNING)
        self.assertEqual(instance_dict["start_time"], "2025-06-09T04:00:00Z")
        self.assertEqual(instance_dict["input_data"], {"input1": "value1"})
        self.assertEqual(instance_dict["variables"], {"var1": "value1"})
    
    def test_workflow_instance_from_dict(self):
        """Test creating a workflow instance from a dictionary."""
        instance_dict = {
            "id": "test-instance",
            "workflow_id": "test-workflow",
            "status": WorkflowStatus.RUNNING,
            "start_time": "2025-06-09T04:00:00Z",
            "input_data": {"input1": "value1"},
            "variables": {"var1": "value1"}
        }
        
        instance = WorkflowInstance.from_dict(instance_dict)
        
        self.assertEqual(instance.id, "test-instance")
        self.assertEqual(instance.workflow_id, "test-workflow")
        self.assertEqual(instance.status, WorkflowStatus.RUNNING)
        self.assertEqual(instance.start_time, "2025-06-09T04:00:00Z")
        self.assertEqual(instance.input_data, {"input1": "value1"})
        self.assertEqual(instance.variables, {"var1": "value1"})


class TestWorkflowStorageManager(unittest.TestCase):
    """Test cases for workflow storage manager."""
    
    def setUp(self):
        """Set up test environment."""
        self.storage_manager = WorkflowStorageManager()
    
    def test_save_and_get_definition(self):
        """Test saving and retrieving a workflow definition."""
        definition = WorkflowDefinition(
            id="test-workflow",
            name="Test Workflow",
            description="A test workflow"
        )
        
        # Save the definition
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.storage_manager.save_definition(definition))
        
        # Get the definition
        retrieved_definition = loop.run_until_complete(
            self.storage_manager.get_definition("test-workflow")
        )
        
        self.assertEqual(retrieved_definition.id, "test-workflow")
        self.assertEqual(retrieved_definition.name, "Test Workflow")
        self.assertEqual(retrieved_definition.description, "A test workflow")
        
        loop.close()
    
    def test_save_and_get_instance(self):
        """Test saving and retrieving a workflow instance."""
        instance = WorkflowInstance(
            id="test-instance",
            workflow_id="test-workflow",
            input_data={"input1": "value1"}
        )
        
        # Save the instance
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.storage_manager.save_instance(instance))
        
        # Get the instance
        retrieved_instance = loop.run_until_complete(
            self.storage_manager.get_instance("test-instance")
        )
        
        self.assertEqual(retrieved_instance.id, "test-instance")
        self.assertEqual(retrieved_instance.workflow_id, "test-workflow")
        self.assertEqual(retrieved_instance.input_data, {"input1": "value1"})
        
        loop.close()
    
    def test_list_definitions(self):
        """Test listing workflow definitions."""
        definition1 = WorkflowDefinition(
            id="test-workflow-1",
            name="Test Workflow 1",
            description="A test workflow 1"
        )
        
        definition2 = WorkflowDefinition(
            id="test-workflow-2",
            name="Test Workflow 2",
            description="A test workflow 2"
        )
        
        # Save the definitions
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.storage_manager.save_definition(definition1))
        loop.run_until_complete(self.storage_manager.save_definition(definition2))
        
        # List the definitions
        definitions = loop.run_until_complete(self.storage_manager.list_definitions())
        
        self.assertEqual(len(definitions), 2)
        self.assertTrue(any(d.id == "test-workflow-1" for d in definitions))
        self.assertTrue(any(d.id == "test-workflow-2" for d in definitions))
        
        loop.close()
    
    def test_list_instances(self):
        """Test listing workflow instances."""
        instance1 = WorkflowInstance(
            id="test-instance-1",
            workflow_id="test-workflow-1",
            status=WorkflowStatus.RUNNING
        )
        
        instance2 = WorkflowInstance(
            id="test-instance-2",
            workflow_id="test-workflow-2",
            status=WorkflowStatus.COMPLETED
        )
        
        # Save the instances
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.storage_manager.save_instance(instance1))
        loop.run_until_complete(self.storage_manager.save_instance(instance2))
        
        # List all instances
        instances = loop.run_until_complete(self.storage_manager.list_instances())
        self.assertEqual(len(instances), 2)
        
        # List instances by workflow ID
        instances = loop.run_until_complete(
            self.storage_manager.list_instances(workflow_id="test-workflow-1")
        )
        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0].id, "test-instance-1")
        
        # List instances by status
        instances = loop.run_until_complete(
            self.storage_manager.list_instances(status=WorkflowStatus.RUNNING)
        )
        self.assertEqual(len(instances), 1)
        self.assertEqual(instances[0].id, "test-instance-1")
        
        loop.close()
    
    def test_update_instance_status(self):
        """Test updating a workflow instance status."""
        instance = WorkflowInstance(
            id="test-instance",
            workflow_id="test-workflow",
            status=WorkflowStatus.RUNNING
        )
        
        # Save the instance
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.storage_manager.save_instance(instance))
        
        # Update the status
        loop.run_until_complete(
            self.storage_manager.update_instance_status(
                "test-instance",
                WorkflowStatus.COMPLETED
            )
        )
        
        # Get the updated instance
        updated_instance = loop.run_until_complete(
            self.storage_manager.get_instance("test-instance")
        )
        
        self.assertEqual(updated_instance.status, WorkflowStatus.COMPLETED)
        self.assertIsNotNone(updated_instance.end_time)
        
        loop.close()


class TestConnectorRegistry(unittest.TestCase):
    """Test cases for connector registry."""
    
    def setUp(self):
        """Set up test environment."""
        self.registry = ConnectorRegistry()
    
    def test_register_and_get_connector_class(self):
        """Test registering and retrieving a connector class."""
        # Register a connector class
        self.registry.register("test-connector", BaseConnector)
        
        # Get the connector class
        connector_class = self.registry.get_connector_class("test-connector")
        
        self.assertEqual(connector_class, BaseConnector)
    
    def test_get_nonexistent_connector_class(self):
        """Test retrieving a nonexistent connector class."""
        connector_class = self.registry.get_connector_class("nonexistent")
        
        self.assertIsNone(connector_class)
    
    def test_list_connector_types(self):
        """Test listing connector types."""
        # Register connector classes
        self.registry.register("test-connector-1", BaseConnector)
        self.registry.register("test-connector-2", BaseConnector)
        
        # List connector types
        connector_types = self.registry.list_connector_types()
        
        self.assertEqual(len(connector_types), 2)
        self.assertIn("test-connector-1", connector_types)
        self.assertIn("test-connector-2", connector_types)


class MockConnector(BaseConnector):
    """Mock connector for testing."""
    
    async def execute_operation(
        self,
        operation: str,
        parameters: dict,
        context: dict
    ) -> dict:
        """Execute a mock operation."""
        if operation == "test-operation":
            return {"status": "success", "operation": operation, "parameters": parameters}
        else:
            raise ValueError(f"Unsupported operation: {operation}")


class TestConnectorStepExecutor(unittest.TestCase):
    """Test cases for connector step executor."""
    
    def setUp(self):
        """Set up test environment."""
        self.registry = ConnectorRegistry()
        self.registry.register("test-connector", MockConnector)
        self.executor = ConnectorStepExecutor(self.registry)
    
    def test_execute_step(self):
        """Test executing a step with a connector."""
        step = WorkflowStep(
            id="test-step",
            type="connector",
            parameters={
                "connector_type": "test-connector",
                "operation": "test-operation",
                "parameters": {"param1": "value1"}
            }
        )
        
        input_data = {"input1": "value1"}
        instance = WorkflowInstance(id="test-instance", workflow_id="test-workflow")
        
        # Execute the step
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(self.executor.execute(step, input_data, instance))
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["operation"], "test-operation")
        self.assertEqual(result["parameters"]["param1"], "value1")
        
        loop.close()
    
    def test_execute_step_with_template_parameters(self):
        """Test executing a step with template parameters."""
        step = WorkflowStep(
            id="test-step",
            type="connector",
            parameters={
                "connector_type": "test-connector",
                "operation": "test-operation",
                "parameters": {
                    "param1": "${input.value1}",
                    "param2": "${workflow.variables.var1}"
                }
            }
        )
        
        input_data = {
            "input": {"value1": "input-value1"},
            "workflow": {"variables": {"var1": "var-value1"}}
        }
        instance = WorkflowInstance(id="test-instance", workflow_id="test-workflow")
        
        # Execute the step
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(self.executor.execute(step, input_data, instance))
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["operation"], "test-operation")
        self.assertEqual(result["parameters"]["param1"], "input-value1")
        self.assertEqual(result["parameters"]["param2"], "var-value1")
        
        loop.close()


class TestEmailConnector(unittest.TestCase):
    """Test cases for email connector."""
    
    def setUp(self):
        """Set up test environment."""
        self.connector = EmailConnector()
    
    def test_send_email(self):
        """Test sending an email."""
        parameters = {
            "recipient": "test@example.com",
            "subject": "Test Subject",
            "body": "Test Body"
        }
        
        # Execute the operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            self.connector.execute_operation("send_email", parameters, {})
        )
        
        self.assertEqual(result["status"], "sent")
        self.assertEqual(result["recipient"], "test@example.com")
        self.assertEqual(result["subject"], "Test Subject")
        
        loop.close()
    
    def test_get_emails(self):
        """Test getting emails."""
        parameters = {
            "folder": "inbox",
            "limit": 10
        }
        
        # Execute the operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            self.connector.execute_operation("get_emails", parameters, {})
        )
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["folder"], "inbox")
        self.assertEqual(result["count"], 0)
        self.assertEqual(len(result["emails"]), 0)
        
        loop.close()
    
    def test_unsupported_operation(self):
        """Test executing an unsupported operation."""
        parameters = {}
        
        # Execute the operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        with self.assertRaises(ValueError):
            loop.run_until_complete(
                self.connector.execute_operation("unsupported", parameters, {})
            )
        
        loop.close()


class TestRestApiConnector(unittest.TestCase):
    """Test cases for REST API connector."""
    
    def setUp(self):
        """Set up test environment."""
        self.connector = RestApiConnector()
    
    def test_get_request(self):
        """Test making a GET request."""
        parameters = {
            "url": "https://api.example.com/resource",
            "headers": {"Accept": "application/json"}
        }
        
        # Execute the operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            self.connector.execute_operation("get", parameters, {})
        )
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["status_code"], 200)
        self.assertEqual(result["body"]["message"], "This is a simulated response")
        
        loop.close()
    
    def test_post_request(self):
        """Test making a POST request."""
        parameters = {
            "url": "https://api.example.com/resource",
            "headers": {"Content-Type": "application/json"},
            "data": {"key": "value"}
        }
        
        # Execute the operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            self.connector.execute_operation("post", parameters, {})
        )
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["status_code"], 200)
        self.assertEqual(result["body"]["message"], "This is a simulated response")
        
        loop.close()
    
    def test_unsupported_operation(self):
        """Test executing an unsupported operation."""
        parameters = {}
        
        # Execute the operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        with self.assertRaises(ValueError):
            loop.run_until_complete(
                self.connector.execute_operation("unsupported", parameters, {})
            )
        
        loop.close()


if __name__ == "__main__":
    unittest.main()
