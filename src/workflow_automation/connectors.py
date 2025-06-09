"""
Connector system for integrating with external services.

This module implements the connector registry and base connector classes
for integrating workflows with external systems and services.
"""

from typing import Dict, List, Optional, Any, Union, Type
import abc
import logging
from .models import WorkflowStep, WorkflowInstance

logger = logging.getLogger(__name__)


class BaseConnector(abc.ABC):
    """Base class for all system connectors."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the connector with configuration."""
        self.config = config or {}
    
    @abc.abstractmethod
    async def execute_operation(
        self,
        operation: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an operation with the connector."""
        pass
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test the connection to the external system."""
        return {"status": "not_implemented"}
    
    async def get_operations(self) -> List[Dict[str, Any]]:
        """Get a list of supported operations."""
        return []


class ConnectorRegistry:
    """Registry of available system connectors."""
    
    def __init__(self):
        """Initialize the connector registry."""
        self.connectors: Dict[str, Type[BaseConnector]] = {}
        self.connector_instances: Dict[str, BaseConnector] = {}
    
    def register(self, connector_type: str, connector_class: Type[BaseConnector]) -> None:
        """Register a connector class for a specific type."""
        self.connectors[connector_type] = connector_class
    
    def get_connector_class(self, connector_type: str) -> Optional[Type[BaseConnector]]:
        """Get a connector class by type."""
        return self.connectors.get(connector_type)
    
    def get_connector(self, connector_type: str, config: Dict[str, Any] = None) -> Optional[BaseConnector]:
        """Get or create a connector instance by type."""
        # Check if we already have an instance with this config
        instance_key = f"{connector_type}:{hash(str(config))}"
        if instance_key in self.connector_instances:
            return self.connector_instances[instance_key]
        
        # Create a new instance
        connector_class = self.get_connector_class(connector_type)
        if not connector_class:
            return None
        
        connector = connector_class(config)
        self.connector_instances[instance_key] = connector
        return connector
    
    def list_connector_types(self) -> List[str]:
        """List all registered connector types."""
        return list(self.connectors.keys())


class ConnectorStepExecutor:
    """Step executor that uses connectors to execute operations."""
    
    def __init__(self, connector_registry: ConnectorRegistry):
        """Initialize the connector step executor."""
        self.connector_registry = connector_registry
    
    async def execute(
        self,
        step: WorkflowStep,
        input_data: Dict[str, Any],
        workflow_instance: WorkflowInstance
    ) -> Dict[str, Any]:
        """Execute a workflow step using a connector."""
        # Get connector type from step parameters
        connector_type = step.parameters.get("connector_type")
        if not connector_type:
            raise ValueError(f"No connector_type specified for step: {step.id}")
        
        # Get operation from step parameters
        operation = step.parameters.get("operation")
        if not operation:
            raise ValueError(f"No operation specified for step: {step.id}")
        
        # Get connector configuration
        config = step.parameters.get("connector_config", {})
        
        # Get connector instance
        connector = self.connector_registry.get_connector(connector_type, config)
        if not connector:
            raise ValueError(f"Connector not found for type: {connector_type}")
        
        # Prepare operation parameters
        parameters = step.parameters.get("parameters", {})
        
        # Replace parameter templates with actual values
        parameters = self._resolve_parameter_templates(parameters, input_data)
        
        # Execute the operation
        result = await connector.execute_operation(operation, parameters, input_data)
        return result
    
    def _resolve_parameter_templates(
        self,
        parameters: Dict[str, Any],
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve parameter templates with actual values from input data."""
        resolved = {}
        
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # This is a template, resolve it
                path = value[2:-1].split(".")
                resolved_value = input_data
                try:
                    for part in path:
                        resolved_value = resolved_value[part]
                    resolved[key] = resolved_value
                except (KeyError, TypeError):
                    # If the path doesn't exist, use the original value
                    resolved[key] = value
            elif isinstance(value, dict):
                # Recursively resolve nested dictionaries
                resolved[key] = self._resolve_parameter_templates(value, input_data)
            elif isinstance(value, list):
                # Recursively resolve lists
                resolved[key] = [
                    self._resolve_parameter_templates(item, input_data) 
                    if isinstance(item, dict) else item 
                    for item in value
                ]
            else:
                # Use the original value
                resolved[key] = value
        
        return resolved


# Example connector implementations

class EmailConnector(BaseConnector):
    """Connector for sending emails."""
    
    async def execute_operation(
        self,
        operation: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an email operation."""
        if operation == "send_email":
            return await self._send_email(parameters)
        elif operation == "get_emails":
            return await self._get_emails(parameters)
        else:
            raise ValueError(f"Unsupported operation: {operation}")
    
    async def _send_email(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Send an email."""
        # In a real implementation, this would use an email library
        # For now, we'll just log the email details
        
        recipient = parameters.get("recipient")
        subject = parameters.get("subject")
        body = parameters.get("body")
        
        logger.info(f"Sending email to {recipient} with subject: {subject}")
        
        # Simulate sending email
        return {
            "status": "sent",
            "recipient": recipient,
            "subject": subject,
            "timestamp": "2025-06-09T04:42:00Z"
        }
    
    async def _get_emails(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get emails from a mailbox."""
        # In a real implementation, this would use an email library
        # For now, we'll just return a mock response
        
        folder = parameters.get("folder", "inbox")
        limit = parameters.get("limit", 10)
        
        logger.info(f"Getting {limit} emails from folder: {folder}")
        
        # Simulate getting emails
        return {
            "status": "success",
            "folder": folder,
            "count": 0,
            "emails": []
        }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test the email connection."""
        # In a real implementation, this would test the SMTP/IMAP connection
        return {"status": "connected"}
    
    async def get_operations(self) -> List[Dict[str, Any]]:
        """Get a list of supported operations."""
        return [
            {
                "name": "send_email",
                "description": "Send an email",
                "parameters": ["recipient", "subject", "body"]
            },
            {
                "name": "get_emails",
                "description": "Get emails from a mailbox",
                "parameters": ["folder", "limit"]
            }
        ]


class RestApiConnector(BaseConnector):
    """Connector for interacting with REST APIs."""
    
    async def execute_operation(
        self,
        operation: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a REST API operation."""
        if operation == "get":
            return await self._make_request("GET", parameters)
        elif operation == "post":
            return await self._make_request("POST", parameters)
        elif operation == "put":
            return await self._make_request("PUT", parameters)
        elif operation == "delete":
            return await self._make_request("DELETE", parameters)
        else:
            raise ValueError(f"Unsupported operation: {operation}")
    
    async def _make_request(self, method: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Make an HTTP request."""
        # In a real implementation, this would use aiohttp or httpx
        # For now, we'll just log the request details
        
        url = parameters.get("url")
        headers = parameters.get("headers", {})
        data = parameters.get("data")
        
        logger.info(f"Making {method} request to {url}")
        
        # Simulate making a request
        return {
            "status": "success",
            "status_code": 200,
            "headers": {},
            "body": {"message": "This is a simulated response"}
        }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test the API connection."""
        # In a real implementation, this would make a test request
        return {"status": "connected"}
    
    async def get_operations(self) -> List[Dict[str, Any]]:
        """Get a list of supported operations."""
        return [
            {
                "name": "get",
                "description": "Make a GET request",
                "parameters": ["url", "headers"]
            },
            {
                "name": "post",
                "description": "Make a POST request",
                "parameters": ["url", "headers", "data"]
            },
            {
                "name": "put",
                "description": "Make a PUT request",
                "parameters": ["url", "headers", "data"]
            },
            {
                "name": "delete",
                "description": "Make a DELETE request",
                "parameters": ["url", "headers"]
            }
        ]
