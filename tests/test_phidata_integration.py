"""
Integration tests for the Phidata agent integration with the Orchestra system.

These tests verify that the PhidataAgentWrapper correctly integrates with
the Orchestra API and that requests to the /phidata/chat endpoint correctly
utilize the PhidataAgentWrapper.
"""

import pytest
import json
from typing import Dict, Any
from unittest.mock import patch, MagicMock, AsyncMock

from fastapi.testclient import TestClient

# Import the main application
from core.orchestrator.src.main import app
from core.orchestrator.src.api.endpoints.phidata_chat import router as phidata_router
from core.orchestrator.src.agents.agent_registry import AgentRegistry, get_agent_registry
from packages.agents.src._base import OrchestraAgentBase
from packages.agents.src.phidata.wrapper import PhidataAgentWrapper
from packages.agents.src.registry import AgentRegistry as PackagesAgentRegistry
from packages.shared.src.models.domain_models import UserRequest as AgentInput
from packages.shared.src.models.domain_models import AgentResponse as AgentOutput


# Create test client
client = TestClient(app)


@pytest.fixture
def mock_agent_wrapper():
    """Create a mock PhidataAgentWrapper."""
    mock = AsyncMock(spec=PhidataAgentWrapper)
    mock.agent_type = "phidata"
    mock.name = "TestPhidataAgent"
    mock.id = "test_phidata_agent"
    
    # Mock the run method to return a response
    mock.run.return_value = AgentOutput(
        request_id="test-request-id",
        agent_type="phidata",
        content="This is a test response from the mock Phidata agent.",
        content_type="text/markdown",
        metadata={"agent_name": "TestPhidataAgent", "agent_id": "test_phidata_agent"}
    )
    
    return mock


@pytest.fixture
def mock_agent_registry(mock_agent_wrapper):
    """Create a mock agent registry with a registered PhidataAgentWrapper."""
    mock = MagicMock(spec=AgentRegistry)
    
    # Return the mock wrapper for either get_agent or select_agent_for_context
    mock.get_agent.return_value = mock_agent_wrapper
    mock.select_agent_for_context.return_value = mock_agent_wrapper
    
    return mock


class TestPhidataIntegration:
    """Integration tests for Phidata agent integration."""
    
    @patch("core.orchestrator.src.agents.agent_registry.get_agent_registry")
    @patch("core.orchestrator.src.api.dependencies.memory.get_memory_manager")
    @patch("core.orchestrator.src.api.dependencies.llm.get_llm_client")
    async def test_phidata_chat_endpoint(self, mock_get_llm, mock_get_memory, mock_get_registry, 
                                        mock_agent_registry, mock_agent_wrapper):
        """Test the /phidata/chat endpoint with a mock agent registry."""
        # Configure mocks
        mock_get_registry.return_value = mock_agent_registry
        
        # Mock memory manager
        memory_manager = AsyncMock()
        memory_manager.get_conversation_history.return_value = []
        memory_manager.add_memory_item.return_value = None
        mock_get_memory.return_value = memory_manager
        
        # Mock LLM client
        mock_get_llm.return_value = MagicMock()
        
        # Test request payload
        payload = {
            "message": "Test message",
            "session_id": "test-session-123",
            "user_id": "test-user-456",
            "agent_id": "test_phidata_agent",
            "metadata": {"test_key": "test_value"}
        }
        
        # Make the request
        with app.container.llm_client.override(mock_get_llm()):
            with app.container.memory_manager.override(mock_get_memory()):
                response = client.post("/phidata/chat", json=payload)
        
        # Check the response
        assert response.status_code == 200
        response_data = response.json()
        
        # Verify response structure
        assert "response_content" in response_data
        assert response_data["response_content"] == "This is a test response from the mock Phidata agent."
        assert response_data["response_type"] == "text"
        assert response_data["session_id"] == "test-session-123"
        assert response_data["user_id"] == "test-user-456"
        assert response_data["agent_id"] == "phidata"
        
        # Verify agent was called with correct parameters
        mock_agent_registry.get_agent.assert_called_with("test_phidata_agent")
        
        # Verify the agent's process method was called
        mock_agent_wrapper.process.assert_called_once()
        
        # Verify memory operations
        memory_manager.get_conversation_history.assert_called_once_with(
            user_id="test-user-456", 
            session_id="test-session-123",
            limit=10
        )
        memory_manager.add_memory_item.assert_called_once()
    
    @patch("packages.agents.src.registry.agent_registry")
    async def test_agent_registry_creation(self, mock_registry):
        """Test that the AgentRegistry correctly creates a PhidataAgentWrapper."""
        # Configure mock registry
        mock_registry.create_agent.return_value = AsyncMock(spec=PhidataAgentWrapper)
        
        # Test configuration
        agent_config = {
            "wrapper_type": "phidata",
            "name": "TestPhidataAgent",
            "phidata_agent_class": "agno.agent.Agent",
            "llm_ref": "llm_openai_gpt4o_via_portkey",
            "instructions": ["You are a helpful test assistant."],
            "markdown": True,
            "show_tool_calls": True
        }
        
        # Mock dependencies
        memory_manager = AsyncMock()
        llm_client = MagicMock()
        tool_registry = MagicMock()
        
        # Create agent through registry
        registry = PackagesAgentRegistry()
        agent = registry.create_agent(
            agent_id="test-phidata-agent",
            agent_config=agent_config,
            memory_manager=memory_manager,
            llm_client=llm_client,
            tool_registry=tool_registry
        )
        
        # Verify agent creation
        mock_registry.create_agent.assert_called_once()
        # Check that the correct ID and config were passed
        args = mock_registry.create_agent.call_args
        assert args[1]["agent_id"] == "test-phidata-agent"
        assert args[1]["agent_config"]["wrapper_type"] == "phidata"
    
    @patch("core.orchestrator.src.agents.agent_registry.get_agent_registry")
    @patch("core.orchestrator.src.api.dependencies.memory.get_memory_manager")
    @patch("core.orchestrator.src.api.dependencies.llm.get_llm_client")
    async def test_phidata_chat_with_context_selection(self, mock_get_llm, mock_get_memory, 
                                                     mock_get_registry, mock_agent_registry, 
                                                     mock_agent_wrapper):
        """Test the /phidata/chat endpoint when agent_id is not provided."""
        # Configure mocks
        mock_get_registry.return_value = mock_agent_registry
        
        # Mock memory manager
        memory_manager = AsyncMock()
        memory_manager.get_conversation_history.return_value = []
        memory_manager.add_memory_item.return_value = None
        mock_get_memory.return_value = memory_manager
        
        # Mock LLM client
        mock_get_llm.return_value = MagicMock()
        
        # Test request payload without agent_id
        payload = {
            "message": "Test message for context selection",
            "session_id": "test-session-123",
            "user_id": "test-user-456",
            "metadata": {"test_key": "test_value"}
        }
        
        # Make the request
        with app.container.llm_client.override(mock_get_llm()):
            with app.container.memory_manager.override(mock_get_memory()):
                response = client.post("/phidata/chat", json=payload)
        
        # Check the response
        assert response.status_code == 200
        
        # Verify agent was selected based on context
        mock_agent_registry.select_agent_for_context.assert_called_once()
        
        # Verify the agent's process method was called
        mock_agent_wrapper.process.assert_called_once()
    
    @patch("core.orchestrator.src.agents.agent_registry.get_agent_registry")
    @patch("core.orchestrator.src.api.dependencies.memory.get_memory_manager")
    @patch("core.orchestrator.src.api.dependencies.llm.get_llm_client")
    async def test_phidata_chat_error_handling(self, mock_get_llm, mock_get_memory, mock_get_registry, 
                                             mock_agent_registry):
        """Test error handling in the /phidata/chat endpoint."""
        # Configure mocks
        mock_get_registry.return_value = mock_agent_registry
        
        # Mock memory manager
        memory_manager = AsyncMock()
        memory_manager.get_conversation_history.return_value = []
        mock_get_memory.return_value = memory_manager
        
        # Mock LLM client
        mock_get_llm.return_value = MagicMock()
        
        # Make agent process raise an exception
        mock_agent = mock_agent_registry.get_agent.return_value
        mock_agent.process.side_effect = Exception("Test processing error")
        
        # Test request payload
        payload = {
            "message": "Test error message",
            "session_id": "test-session-123",
            "user_id": "test-user-456",
            "agent_id": "test_phidata_agent"
        }
        
        # Make the request
        with app.container.llm_client.override(mock_get_llm()):
            with app.container.memory_manager.override(mock_get_memory()):
                response = client.post("/phidata/chat", json=payload)
        
        # Check that the response indicates an error
        assert response.status_code == 500
        error_data = response.json()
        assert "detail" in error_data
        assert "Agent processing failed" in error_data["detail"]