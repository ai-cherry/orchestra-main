"""
Unit tests for the PhidataAgentWrapper class.

Tests the functionality of the PhidataAgentWrapper that adapts Phidata agents
for use within the Orchestra orchestration system.
"""

import asyncio
import pytest
import importlib
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from packages.agents.src.phidata.wrapper import PhidataAgentWrapper
from packages.shared.src.models.domain_models import UserRequest as AgentInput
from packages.shared.src.models.domain_models import AgentResponse as AgentOutput
from packages.memory.src.base import MemoryManager
from packages.llm.src.portkey_client import PortkeyClient
from packages.tools.src.base import ToolRegistry

# Mock fixtures
@pytest.fixture
def mock_memory_manager():
    """Create a mock memory manager for testing."""
    mock = AsyncMock(spec=MemoryManager)
    mock.get_memory.return_value = []
    mock.add_memory.return_value = None
    return mock

@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client for testing."""
    mock = MagicMock(spec=PortkeyClient)
    
    # Add a mock LLM model as an attribute that can be referenced
    mock_model = MagicMock()
    mock_model.generate.return_value = "Mock LLM response"
    # Make model accessible as an attribute
    setattr(mock, "llm_openai_gpt4o_via_portkey", mock_model)
    
    return mock

@pytest.fixture
def mock_tool_registry():
    """Create a mock tool registry for testing."""
    mock = MagicMock(spec=ToolRegistry)
    return mock

@pytest.fixture
def mock_phidata_agent():
    """Create a mock Phidata agent for testing."""
    mock = MagicMock()
    mock.run = AsyncMock(return_value=MagicMock(content="Mock agent response"))
    return mock

@pytest.fixture
def agent_config():
    """Create a test agent configuration."""
    return {
        "name": "TestPhidataAgent",
        "id": "test_phidata_agent",
        "phidata_agent_class": "agno.agent.Agent",
        "llm_ref": "llm_openai_gpt4o_via_portkey",
        "instructions": ["You are a helpful test assistant."],
        "markdown": True,
        "show_tool_calls": True,
        "tools": []
    }

@pytest.fixture
def team_config():
    """Create a test team configuration."""
    return {
        "name": "TestPhidataTeam",
        "id": "test_phidata_team",
        "phidata_agent_class": "agno.team.Team",
        "llm_ref": "llm_openai_gpt4o_via_portkey",
        "team_model_ref": "llm_openai_gpt4o_via_portkey",
        "team_mode": "coordinate",
        "team_success_criteria": "Test success criteria",
        "team_instructions": ["You are a helpful test team."],
        "team_markdown": True,
        "members": [
            {
                "name": "TestMember1",
                "role": "Test role 1",
                "model_ref": "llm_openai_gpt4o_via_portkey",
                "instructions": ["You are test member 1."]
            },
            {
                "name": "TestMember2",
                "role": "Test role 2",
                "model_ref": "llm_openai_gpt4o_via_portkey",
                "instructions": ["You are test member 2."]
            }
        ]
    }

@pytest.mark.asyncio
class TestPhidataAgentWrapper:
    """Test suite for PhidataAgentWrapper."""
    
    @patch("importlib.import_module")
    def test_init_single_agent(self, mock_import_module, agent_config, mock_memory_manager, 
                              mock_llm_client, mock_tool_registry, mock_phidata_agent):
        """Test initialization of a single Phidata agent wrapper."""
        # Setup mock imports
        mock_module = MagicMock()
        mock_module.Agent = MagicMock(return_value=mock_phidata_agent)
        mock_import_module.return_value = mock_module
        
        # Initialize wrapper
        wrapper = PhidataAgentWrapper(
            agent_config=agent_config,
            memory_manager=mock_memory_manager,
            llm_client=mock_llm_client,
            tool_registry=mock_tool_registry
        )
        
        # Verify basic properties
        assert wrapper.name == "TestPhidataAgent"
        assert wrapper.id == "test_phidata_agent"
        assert wrapper.agent_type == "phidata"
        assert wrapper._is_team is False
        
        # Verify agent was initialized correctly
        mock_import_module.assert_called_with("agno.agent")
        assert wrapper.phidata_agent is not None
    
    @patch("importlib.import_module")
    def test_init_team(self, mock_import_module, team_config, mock_memory_manager, 
                      mock_llm_client, mock_tool_registry, mock_phidata_agent):
        """Test initialization of a Phidata team wrapper."""
        # Setup mock imports for team and agents
        mock_agent_module = MagicMock()
        mock_agent_module.Agent = MagicMock(return_value=mock_phidata_agent)
        
        mock_team_module = MagicMock()
        mock_team_module.Team = MagicMock(return_value=mock_phidata_agent)  # Reusing same mock
        
        # Setup module import to return different modules based on import path
        def side_effect(name):
            if name == "agno.agent":
                return mock_agent_module
            elif name == "agno.team":
                return mock_team_module
            return MagicMock()
            
        mock_import_module.side_effect = side_effect
        
        # Initialize wrapper
        wrapper = PhidataAgentWrapper(
            agent_config=team_config,
            memory_manager=mock_memory_manager,
            llm_client=mock_llm_client,
            tool_registry=mock_tool_registry
        )
        
        # Verify team properties
        assert wrapper.name == "TestPhidataTeam"
        assert wrapper.id == "test_phidata_team"
        assert wrapper._is_team is True
        
        # Verify team was initialized with members
        mock_team_module.Team.assert_called_once()
        call_kwargs = mock_team_module.Team.call_args[1]
        assert 'members' in call_kwargs
        assert call_kwargs['mode'] == 'coordinate'
    
    def test_init_missing_llm_ref(self, agent_config, mock_memory_manager, 
                                 mock_llm_client, mock_tool_registry):
        """Test initialization with missing LLM reference fails."""
        # Remove the LLM reference from config
        config = dict(agent_config)
        del config["llm_ref"]
        
        # Should raise ValueError
        with pytest.raises(ValueError, match="requires a 'llm_ref' in config"):
            PhidataAgentWrapper(
                agent_config=config,
                memory_manager=mock_memory_manager,
                llm_client=mock_llm_client,
                tool_registry=mock_tool_registry
            )
    
    @patch("importlib.import_module")
    def test_init_team_without_members(self, mock_import_module, team_config, mock_memory_manager, 
                                      mock_llm_client, mock_tool_registry):
        """Test initialization of a team without members fails."""
        # Setup mock imports
        mock_module = MagicMock()
        mock_module.Team = MagicMock()
        mock_import_module.return_value = mock_module
        
        # Remove members from config
        config = dict(team_config)
        config["members"] = []
        
        # Should raise ValueError
        with pytest.raises(ValueError, match="requires 'members' in config"):
            PhidataAgentWrapper(
                agent_config=config,
                memory_manager=mock_memory_manager,
                llm_client=mock_llm_client,
                tool_registry=mock_tool_registry
            )
    
    @patch("importlib.import_module")
    async def test_run_single_agent(self, mock_import_module, agent_config, mock_memory_manager, 
                                   mock_llm_client, mock_tool_registry, mock_phidata_agent):
        """Test the run method with a single agent."""
        # Setup mock imports
        mock_module = MagicMock()
        mock_module.Agent = MagicMock(return_value=mock_phidata_agent)
        mock_import_module.return_value = mock_module
        
        # Mock the run method to return a response with content
        mock_phidata_agent.run = AsyncMock(return_value=MagicMock(content="Test response"))
        
        # Initialize wrapper
        wrapper = PhidataAgentWrapper(
            agent_config=agent_config,
            memory_manager=mock_memory_manager,
            llm_client=mock_llm_client,
            tool_registry=mock_tool_registry
        )
        wrapper.phidata_agent = mock_phidata_agent
        
        # Create test input
        input_data = AgentInput(
            request_id="test-request-id",
            prompt="Test prompt",
            user_id="test-user",
            session_id="test-session"
        )
        
        # Run the agent
        output = await wrapper.run(input_data)
        
        # Verify the agent was called
        mock_phidata_agent.run.assert_called_once()
        
        # Verify output
        assert isinstance(output, AgentOutput)
        assert output.content == "Test response"
        assert output.request_id == "test-request-id"
        assert output.agent_type == "phidata"
        
        # Verify memory operations
        mock_memory_manager.get_memory.assert_called_once()
        assert mock_memory_manager.add_memory.call_count == 2  # Once for user, once for assistant
    
    @patch("importlib.import_module")
    async def test_run_with_history(self, mock_import_module, agent_config, mock_memory_manager, 
                                  mock_llm_client, mock_tool_registry, mock_phidata_agent):
        """Test run method with conversation history."""
        # Setup mock imports
        mock_module = MagicMock()
        mock_module.Agent = MagicMock(return_value=mock_phidata_agent)
        mock_import_module.return_value = mock_module
        
        # Mock memory to return history items
        mock_memory_item1 = MagicMock()
        mock_memory_item1.role = "user"
        mock_memory_item1.content = "Previous user message"
        
        mock_memory_item2 = MagicMock()
        mock_memory_item2.role = "assistant"
        mock_memory_item2.content = "Previous assistant response"
        
        mock_memory_manager.get_memory.return_value = [mock_memory_item1, mock_memory_item2]
        
        # Initialize wrapper
        wrapper = PhidataAgentWrapper(
            agent_config=agent_config,
            memory_manager=mock_memory_manager,
            llm_client=mock_llm_client,
            tool_registry=mock_tool_registry
        )
        wrapper.phidata_agent = mock_phidata_agent
        
        # Create test input
        input_data = AgentInput(
            request_id="test-request-id",
            prompt="Test prompt with history",
            user_id="test-user",
            session_id="test-session"
        )
        
        # Run the agent
        await wrapper.run(input_data)
        
        # Verify that history was requested from memory
        mock_memory_manager.get_memory.assert_called_once_with(
            user_id="test-user",
            session_id="test-session",
            limit=10
        )
        
        # Verify agent was called with history included
        run_args = mock_phidata_agent.run.call_args[1]
        assert "message" in run_args
        assert "Previous user message" in run_args["message"]
        assert "Previous assistant response" in run_args["message"]
        assert "Test prompt with history" in run_args["message"]
    
    @patch("importlib.import_module")
    async def test_run_error_handling(self, mock_import_module, agent_config, mock_memory_manager, 
                                    mock_llm_client, mock_tool_registry, mock_phidata_agent):
        """Test error handling in run method."""
        # Setup mock imports
        mock_module = MagicMock()
        mock_module.Agent = MagicMock(return_value=mock_phidata_agent)
        mock_import_module.return_value = mock_module
        
        # Make agent.run raise an exception
        mock_phidata_agent.run = AsyncMock(side_effect=RuntimeError("Test error"))
        
        # Initialize wrapper
        wrapper = PhidataAgentWrapper(
            agent_config=agent_config,
            memory_manager=mock_memory_manager,
            llm_client=mock_llm_client,
            tool_registry=mock_tool_registry
        )
        wrapper.phidata_agent = mock_phidata_agent
        
        # Create test input
        input_data = AgentInput(
            request_id="test-request-id",
            prompt="Test prompt that causes error",
            user_id="test-user",
            session_id="test-session"
        )
        
        # Run should handle the exception and return an error output
        output = await wrapper.run(input_data)
        
        # Verify output contains error information
        assert isinstance(output, AgentOutput)
        assert "Error executing Phidata agent" in output.content
        assert "Test error" in output.content
        assert "error" in output.metadata
    
    @patch("importlib.import_module")
    async def test_run_with_sync_agent(self, mock_import_module, agent_config, mock_memory_manager, 
                                     mock_llm_client, mock_tool_registry, mock_phidata_agent):
        """Test run method with a synchronous Phidata agent."""
        # Setup mock imports
        mock_module = MagicMock()
        mock_module.Agent = MagicMock(return_value=mock_phidata_agent)
        mock_import_module.return_value = mock_module
        
        # Mock a synchronous run method (not a coroutine)
        mock_phidata_agent.run = MagicMock(return_value=MagicMock(content="Sync test response"))
        
        # Initialize wrapper
        wrapper = PhidataAgentWrapper(
            agent_config=agent_config,
            memory_manager=mock_memory_manager,
            llm_client=mock_llm_client,
            tool_registry=mock_tool_registry
        )
        wrapper.phidata_agent = mock_phidata_agent
        
        # Create test input
        input_data = AgentInput(
            request_id="test-request-id",
            prompt="Test prompt for sync agent",
            user_id="test-user",
            session_id="test-session"
        )
        
        # Mock asyncio.to_thread to simulate running sync function in a thread pool
        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = MagicMock(content="Thread pool response")
            
            # Run the agent
            output = await wrapper.run(input_data)
            
            # Verify asyncio.to_thread was called for the sync function
            mock_to_thread.assert_called_once()
            assert mock_to_thread.call_args[0][0] == mock_phidata_agent.run
            
            # Check output
            assert output.content == "Thread pool response"
    
    @patch("importlib.import_module")
    async def test_health_check(self, mock_import_module, agent_config, mock_memory_manager, 
                              mock_llm_client, mock_tool_registry, mock_phidata_agent):
        """Test health_check method."""
        # Setup mock imports
        mock_module = MagicMock()
        mock_module.Agent = MagicMock(return_value=mock_phidata_agent)
        mock_import_module.return_value = mock_module
        
        # Initialize wrapper
        wrapper = PhidataAgentWrapper(
            agent_config=agent_config,
            memory_manager=mock_memory_manager,
            llm_client=mock_llm_client,
            tool_registry=mock_tool_registry
        )
        wrapper.phidata_agent = mock_phidata_agent
        
        # Check health
        health = await wrapper.health_check()
        assert health is True
        
        # Test negative case
        wrapper.phidata_agent = None
        health = await wrapper.health_check()
        assert health is False