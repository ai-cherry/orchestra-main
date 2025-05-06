"""
Tests for the Runtime Agents API endpoints.

This module contains tests for the Runtime Agents API endpoints,
ensuring they correctly handle requests and agent execution.
"""

import unittest
import uuid
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from core.orchestrator.src.main import app
from core.orchestrator.src.services.agent_service import get_agent_instance
from packages.agents.base import BaseAgent


class TestAgentsEndpoint(unittest.TestCase):
    """Test cases for the Agents API endpoints."""

    def setUp(self):
        """Set up the test client and mocks."""
        self.client = TestClient(app)
        
        # Patch the background task execution to avoid actually running tasks
        self.task_patch = patch('fastapi.BackgroundTasks.add_task')
        self.mock_add_task = self.task_patch.start()

    def tearDown(self):
        """Clean up resources after each test."""
        self.task_patch.stop()

    @patch('core.orchestrator.src.services.agent_service.get_agent_instance')
    def test_run_agent_success(self, mock_get_agent):
        """Test successful agent run request."""
        # Mock the agent instance
        mock_agent = MagicMock(spec=BaseAgent)
        mock_agent.name = "mock_agent"
        mock_get_agent.return_value = mock_agent
        
        # Test request
        test_context = {"url": "https://example.com"}
        test_config = {"test_config_key": "test_config_value"}
        
        # Make the request
        response = self.client.post(
            "/api/agents/run/web_scraper",
            json={
                "context": test_context,
                "config": test_config
            }
        )
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data["status"], "Task started")
        self.assertEqual(response_data["agent_name"], "web_scraper")
        self.assertTrue("task_id" in response_data)
        
        # Verify the agent was instantiated correctly
        mock_get_agent.assert_called_once()
        args, kwargs = mock_get_agent.call_args
        self.assertEqual(args[0], "web_scraper")
        self.assertEqual(kwargs["config"], test_config)
        
        # Verify the background task was started
        self.mock_add_task.assert_called_once()
        args, kwargs = self.mock_add_task.call_args
        self.assertEqual(args[0].__name__, '_execute_agent_task')  # Check function name
        self.assertEqual(args[1], mock_agent)  # Check agent instance
        self.assertEqual(args[2], test_context)  # Check context
        
    @patch('core.orchestrator.src.services.agent_service.get_agent_instance')
    def test_run_agent_not_found(self, mock_get_agent):
        """Test handling of unknown agent types."""
        # Mock agent not found
        mock_get_agent.side_effect = ValueError("Unknown agent type: nonexistent_agent")
        
        # Make the request
        response = self.client.post(
            "/api/agents/run/nonexistent_agent",
            json={
                "context": {"test": "data"}
            }
        )
        
        # Verify the response
        self.assertEqual(response.status_code, 404)
        response_data = response.json()
        self.assertIn("detail", response_data)
        self.assertIn("Agent not found", response_data["detail"])
        self.assertIn("nonexistent_agent", response_data["detail"])
        
    def test_run_agent_invalid_request(self):
        """Test handling of invalid request data."""
        # Missing required context field
        response = self.client.post(
            "/api/agents/run/web_scraper",
            json={
                "config": {"some": "config"}
                # Missing "context" field
            }
        )
        
        # Verify the response
        self.assertEqual(response.status_code, 422)  # Unprocessable Entity


if __name__ == "__main__":
    unittest.main()