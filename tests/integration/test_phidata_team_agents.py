"""
Integration tests for Phidata Business Intelligence Agents and Team

This test verifies the proper functioning of Phidata agent wrappers with
team capabilities, focusing on agent references for team member instantiation.
"""

import pytest
import os
import asyncio
from unittest.mock import MagicMock, patch

from packages.agents.src.registry import get_registry
from packages.shared.src.models.domain_models import UserRequest as AgentInput


@pytest.fixture
def mock_portkey_client():
    """Mock Portkey client for testing."""
    mock_client = MagicMock()
    
    # Mock LLM models by reference
    mock_client.llm_gpt4_turbo_via_portkey = MagicMock()
    
    return mock_client


@pytest.fixture
def mock_memory_manager():
    """Mock memory manager for testing."""
    mock_memory = MagicMock()
    mock_memory.get_conversation_history = MagicMock(return_value=[])
    mock_memory.store_interaction = MagicMock()
    
    return mock_memory


@pytest.fixture
def mock_tool_registry():
    """Mock tool registry for testing."""
    mock_tools = MagicMock()
    mock_tools.get_tool = MagicMock(return_value=None)
    mock_tools.get_all_tools = MagicMock(return_value=[])
    
    return mock_tools


@pytest.fixture
def gong_agent_config():
    """Test configuration for Gong agent."""
    return {
        "wrapper_type": "phidata",
        "phidata_agent_class": "agno.agent.Agent",
        "agent_name": "Gong Analyst",
        "description": "Analyzes Gong call recordings and transcripts",
        "llm_ref": "llm_gpt4_turbo_via_portkey",
        "tools": [
            {
                "name": "GongTool",
                "type": "packages.tools.src.gong.GongTool"
            }
        ],
        "role": "Analyze Gong call recordings and provide insights",
        "instructions": [
            "Extract key discussion topics from call transcripts",
            "Identify competitor mentions"
        ],
        "memory": {
            "memory_type": "pgvector",
            "table_name": "test_gong_memory"
        }
    }


@pytest.fixture
def hubspot_agent_config():
    """Test configuration for HubSpot agent."""
    return {
        "wrapper_type": "phidata",
        "phidata_agent_class": "agno.agent.Agent",
        "agent_name": "HubSpot Manager",
        "description": "Manages HubSpot CRM operations",
        "llm_ref": "llm_gpt4_turbo_via_portkey",
        "tools": [
            {
                "name": "HubSpotTool",
                "type": "packages.tools.src.hubspot.HubSpotTool"
            }
        ],
        "role": "Manage HubSpot CRM operations",
        "instructions": ["Update deal stages", "Enrich contacts"],
        "memory": {
            "memory_type": "pgvector",
            "table_name": "test_hubspot_memory"
        }
    }


@pytest.fixture
def team_agent_config():
    """Test configuration for Team agent."""
    return {
        "wrapper_type": "phidata",
        "phidata_agent_class": "agno.team.Team",
        "agent_name": "Business Insight Engine",
        "description": "Team of agents for business intelligence",
        "team_mode": "coordinate",
        "members": [
            "test_gong_agent",  # Reference to the Gong agent definition
            "test_hubspot_agent"  # Reference to the HubSpot agent definition
        ],
        "controller": {
            "name": "Insight Controller",
            "llm_ref": "llm_gpt4_turbo_via_portkey",
            "role": "Coordinate team members to gather insights",
            "instructions": [
                "Cross-reference data from multiple systems",
                "Generate comprehensive reports"
            ]
        },
        "memory": {
            "memory_type": "pgvector",
            "table_name": "test_team_memory"
        }
    }


@pytest.mark.asyncio
async def test_individual_agent_creation(mock_memory_manager, mock_portkey_client, mock_tool_registry, gong_agent_config):
    """Test creating an individual Phidata agent wrapper."""
    # Get agent registry
    registry = get_registry()
    
    # Mock the database calls
    with patch("packages.phidata.src.cloudsql_pgvector.get_pg_agent_storage", return_value=MagicMock()):
        with patch("packages.phidata.src.cloudsql_pgvector.get_pgvector_memory", return_value=MagicMock()):
            # Create the agent
            agent = registry.create_agent(
                agent_id="test_gong_agent",
                agent_config=gong_agent_config,
                memory_manager=mock_memory_manager,
                llm_client=mock_portkey_client,
                tool_registry=mock_tool_registry
            )
    
    # Verify agent was created
    assert agent is not None
    assert agent.agent_type == "phidata"
    assert agent.name == "Gong Analyst"
    
    # Verify basic health check (without actually connecting to DB)
    with patch.object(agent, "agent_storage", None):
        with patch.object(agent, "agent_memory", None):
            health_status = await agent.health_check()
            assert health_status is True


@pytest.mark.asyncio
async def test_team_with_member_references(
    mock_memory_manager, mock_portkey_client, mock_tool_registry,
    gong_agent_config, hubspot_agent_config, team_agent_config
):
    """Test creating a Phidata team with member references."""
    # Mock the agent registry and config access
    registry = get_registry()
    
    # Mock get_agent_config to return appropriate configs for member references
    with patch("core.orchestrator.src.core.config.get_agent_config", 
               side_effect=lambda agent_id: gong_agent_config if agent_id == "test_gong_agent" 
                                       else hubspot_agent_config if agent_id == "test_hubspot_agent" 
                                       else None):
        
        # Create member agents in the registry first
        with patch("packages.phidata.src.cloudsql_pgvector.get_pg_agent_storage", return_value=MagicMock()):
            with patch("packages.phidata.src.cloudsql_pgvector.get_pgvector_memory", return_value=MagicMock()):
                # Create Gong agent
                gong_agent = registry.create_agent(
                    agent_id="test_gong_agent",
                    agent_config=gong_agent_config,
                    memory_manager=mock_memory_manager,
                    llm_client=mock_portkey_client,
                    tool_registry=mock_tool_registry
                )
                
                # Create HubSpot agent
                hubspot_agent = registry.create_agent(
                    agent_id="test_hubspot_agent",
                    agent_config=hubspot_agent_config,
                    memory_manager=mock_memory_manager,
                    llm_client=mock_portkey_client,
                    tool_registry=mock_tool_registry
                )
                
                # Mock Team initialization
                with patch("agno.team.Team", MagicMock()):
                    # Create the team agent with references to member agents
                    team_agent = registry.create_agent(
                        agent_id="test_team_agent",
                        agent_config=team_agent_config,
                        memory_manager=mock_memory_manager,
                        llm_client=mock_portkey_client,
                        tool_registry=mock_tool_registry
                    )
    
    # Verify team agent was created
    assert team_agent is not None
    assert team_agent.name == "Business Insight Engine"
    assert team_agent._is_team is True


@pytest.mark.asyncio
async def test_team_agent_execution(mock_memory_manager, mock_portkey_client, mock_tool_registry, team_agent_config):
    """Test execution of a Phidata team agent."""
    # Mock the agent registry and config access
    registry = get_registry()
    
    # Mock successful responses from phidata agent
    mock_response = MagicMock()
    mock_response.content = "Combined insights from team members"
    
    # Mock the phidata agent's run method
    with patch("agno.team.Team.run", return_value=mock_response):
        with patch("core.orchestrator.src.core.config.get_agent_config", return_value={}):
            with patch("packages.phidata.src.cloudsql_pgvector.get_pg_agent_storage", return_value=MagicMock()):
                with patch("packages.phidata.src.cloudsql_pgvector.get_pgvector_memory", return_value=MagicMock()):
                    # Create the team agent
                    team_agent = registry.create_agent(
                        agent_id="test_team_agent",
                        agent_config=team_agent_config,
                        memory_manager=mock_memory_manager,
                        llm_client=mock_portkey_client,
                        tool_registry=mock_tool_registry
                    )
                    
                    # Test execution
                    input_data = AgentInput(
                        prompt="Analyze Q2 forecast for deal X",
                        user_id="test_user",
                        session_id="test_session"
                    )
                    
                    # Run the agent
                    result = await team_agent.run(input_data)
    
    # Verify result
    assert result is not None
    assert result.content == "Combined insights from team members"
    assert result.agent_type == "phidata"
