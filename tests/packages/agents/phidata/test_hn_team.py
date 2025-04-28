"""
Unit tests for the HN Team Phidata agent wrapper.

This tests the configuration, initialization, and behavior of the Hacker News Team agent
which is implemented as a specialized PhidataAgentWrapper using Phidata's Team functionality.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from packages.agents.src.phidata.wrapper import PhidataAgentWrapper
from packages.shared.src.models.domain_models import UserRequest as AgentInput
from packages.shared.src.models.domain_models import AgentResponse as AgentOutput


@pytest.fixture
def mock_memory_manager():
    """Create a mock memory manager for testing."""
    mock = AsyncMock()
    return mock


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client for testing."""
    mock = MagicMock()
    
    # Add a mock LLM model as an attribute
    mock_model = MagicMock()
    mock_model.generate = AsyncMock(return_value="Mock LLM response")
    setattr(mock, "gpt_4o", mock_model)
    
    return mock


@pytest.fixture
def mock_tool_registry():
    """Create a mock tool registry for testing."""
    mock = MagicMock()
    
    # Add a mock web search tool
    web_search_tool = MagicMock()
    web_search_tool.name = "web_search"
    web_search_tool.to_phidata_tool = MagicMock(return_value=MagicMock())
    
    # Add a mock HN API tool
    hn_api_tool = MagicMock()
    hn_api_tool.name = "hn_api"
    hn_api_tool.to_phidata_tool = MagicMock(return_value=MagicMock())
    
    def get_tool_side_effect(tool_name):
        if tool_name == "web_search":
            return web_search_tool
        elif tool_name == "hn_api":
            return hn_api_tool
        return None
    
    mock.get_tool.side_effect = get_tool_side_effect
    
    return mock


@pytest.fixture
def mock_pg_agent_storage():
    """Mock the PostgreSQL agent storage."""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_pgvector_memory():
    """Mock the PostgreSQL vector memory."""
    mock = MagicMock()
    return mock


@pytest.fixture
def hn_team_config():
    """Create a test config for the HN Team agent."""
    return {
        "id": "hn-team",
        "name": "Hacker News Analysis Team",
        "description": "Team of specialized agents that analyze Hacker News content",
        "phidata_agent_class": "agno.team.Team",
        "llm_ref": "gpt_4o",
        "team_model_ref": "gpt_4o",
        "markdown": True,
        "show_tool_calls": True,
        
        # Storage configuration
        "storage": {
            "table_name": "hn_team_storage",
            "schema_name": "llm"
        },
        
        # Memory configuration
        "memory": {
            "table_name": "hn_team_memory",
            "schema_name": "llm",
            "vector_dimension": 768
        },
        
        # Team settings
        "team_mode": "coordinate",
        "team_success_criteria": "The task is considered complete when all team members have provided their specialized analysis and the coordinator has synthesized the results into a comprehensive report.",
        "team_instructions": [
            "You are a team of specialized agents who analyze content from Hacker News.",
            "Collaborate to provide comprehensive insights about trending topics, specific posts, or user activities.",
            "The team coordinator should synthesize inputs from all team members into a clear, cohesive response."
        ],
        
        # Team members
        "members": [
            {
                "name": "HN_Fetcher",
                "role": "Retrieves and summarizes Hacker News posts and comments",
                "model_ref": "gpt_4o",
                "instructions": [
                    "You specialize in retrieving data from Hacker News using the HN API.",
                    "Fetch top stories, specific posts, or user activity as requested.",
                    "Summarize post content, comments, and metadata in a clear, concise format."
                ],
                "tools": [
                    {
                        "type": "registry:hn_api",
                        "params": {}
                    }
                ],
                "storage": {
                    "table_name": "hn_fetcher_storage"
                }
            },
            {
                "name": "Topic_Analyzer",
                "role": "Analyzes topics and trends among Hacker News posts",
                "model_ref": "gpt_4o",
                "instructions": [
                    "You specialize in analyzing patterns and trends in Hacker News content.",
                    "Identify recurring themes, emerging technologies, and community sentiment.",
                    "Provide insights on which topics are gaining or losing traction over time."
                ],
                "tools": [],
                "storage": {
                    "table_name": "topic_analyzer_storage"
                }
            },
            {
                "name": "Context_Researcher",
                "role": "Provides broader context for Hacker News discussions",
                "model_ref": "gpt_4o",
                "instructions": [
                    "You specialize in researching additional context for Hacker News posts.",
                    "Find relevant background information, company histories, or technical details.",
                    "Use web search to supplement information from Hacker News itself."
                ],
                "tools": [
                    {
                        "type": "registry:web_search",
                        "params": {
                            "search_engine": "google"
                        }
                    }
                ],
                "storage": {
                    "table_name": "context_researcher_storage"
                }
            }
        ]
    }


@pytest.mark.asyncio
class TestHnTeamAgent:
    """Test suite for the HN Team Phidata agent wrapper."""
    
    @patch("packages.phidata.src.cloudsql_pgvector.get_pg_agent_storage")
    @patch("packages.phidata.src.cloudsql_pgvector.get_pgvector_memory")
    @patch("importlib.import_module")
    async def test_hn_team_initialization(
        self, 
        mock_import_module, 
        mock_get_pgvector_memory, 
        mock_get_pg_agent_storage,
        hn_team_config, 
        mock_memory_manager,
        mock_llm_client, 
        mock_tool_registry,
        mock_pg_agent_storage,
        mock_pgvector_memory
    ):
        """Test initialization of the HN Team agent."""
        # Setup mocks
        mock_get_pg_agent_storage.return_value = mock_pg_agent_storage
        mock_get_pgvector_memory.return_value = mock_pgvector_memory
        
        # Mock agent and team module import
        mock_agent_module = MagicMock()
        mock_team_module = MagicMock()
        mock_agent_class = MagicMock()
        mock_team_class = MagicMock()
        mock_team_instance = MagicMock()
        
        mock_agent_module.Agent = mock_agent_class
        mock_team_module.Team = mock_team_class
        mock_team_class.return_value = mock_team_instance
        
        def mock_import_side_effect(name):
            if name == "agno.agent":
                return mock_agent_module
            elif name == "agno.team":
                return mock_team_module
            return MagicMock()
            
        mock_import_module.side_effect = mock_import_side_effect
        
        # Initialize the agent wrapper
        agent_wrapper = PhidataAgentWrapper(
            agent_config=hn_team_config,
            memory_manager=mock_memory_manager,
            llm_client=mock_llm_client,
            tool_registry=mock_tool_registry
        )
        
        # Verify the team was initialized with correct parameters
        assert agent_wrapper.name == "Hacker News Analysis Team"
        assert agent_wrapper.id == "hn-team"
        assert agent_wrapper.agent_type == "phidata"
        assert agent_wrapper._is_team is True
        
        # Verify PostgreSQL storage was initialized correctly
        mock_get_pg_agent_storage.assert_called_with(
            agent_id="hn-team",
            config={},  # Default empty dict if not specified
            table_name="hn_team_storage"
        )
        
        # Verify PGVector memory was initialized correctly
        mock_get_pgvector_memory.assert_called()
        
        # Verify Team was initialized with correct parameters
        mock_team_class.assert_called_once()
        call_kwargs = mock_team_class.call_args[1]
        assert call_kwargs["name"] == "Hacker News Analysis Team"
        assert call_kwargs["mode"] == "coordinate"
        assert call_kwargs["storage"] == mock_pg_agent_storage
        assert call_kwargs["memory"] == mock_pgvector_memory
        assert len(call_kwargs["members"]) == 3  # Should have 3 team members
        
        # Verify LLM was fetched correctly
        assert agent_wrapper._get_llm_from_ref("gpt_4o") == mock_llm_client.gpt_4o
    
    @patch("packages.phidata.src.cloudsql_pgvector.get_pg_agent_storage")
    @patch("packages.phidata.src.cloudsql_pgvector.get_pgvector_memory")
    @patch("importlib.import_module")
    async def test_hn_team_member_initialization(
        self, 
        mock_import_module, 
        mock_get_pgvector_memory, 
        mock_get_pg_agent_storage, 
        hn_team_config,
        mock_memory_manager, 
        mock_llm_client,
        mock_tool_registry,
        mock_pg_agent_storage,
        mock_pgvector_memory
    ):
        """Test that team members are correctly initialized."""
        # Setup mocks for storages
        mock_get_pg_agent_storage.side_effect = [
            mock_pg_agent_storage,  # Main team storage
            MagicMock(),  # HN_Fetcher storage
            MagicMock(),  # Topic_Analyzer storage
            MagicMock(),  # Context_Researcher storage
        ]
        mock_get_pgvector_memory.return_value = mock_pgvector_memory
        
        # Mock agent and team module import
        mock_agent_module = MagicMock()
        mock_team_module = MagicMock()
        mock_agent_class = MagicMock()
        mock_team_class = MagicMock()
        
        # Create mock agent instances for members
        mock_member1 = MagicMock(name="HN_Fetcher")
        mock_member2 = MagicMock(name="Topic_Analyzer")
        mock_member3 = MagicMock(name="Context_Researcher")
        
        # Setup agent class to return different instances for different calls
        mock_agent_instances = [mock_member1, mock_member2, mock_member3]
        mock_agent_class.side_effect = mock_agent_instances
        
        mock_agent_module.Agent = mock_agent_class
        mock_team_module.Team = mock_team_class
        
        def mock_import_side_effect(name):
            if name == "agno.agent":
                return mock_agent_module
            elif name == "agno.team":
                return mock_team_module
            return MagicMock()
            
        mock_import_module.side_effect = mock_import_side_effect
        
        # Initialize the agent wrapper
        agent_wrapper = PhidataAgentWrapper(
            agent_config=hn_team_config,
            memory_manager=mock_memory_manager,
            llm_client=mock_llm_client,
            tool_registry=mock_tool_registry
        )
        
        # Verify each team member was initialized with correct parameters
        assert mock_agent_class.call_count == 3  # Should create 3 team members
        
        # Check the first member (HN_Fetcher) initialization
        first_member_call = mock_agent_class.call_args_list[0]
        assert first_member_call[1]["name"] == "HN_Fetcher"
        assert first_member_call[1]["role"] == "Retrieves and summarizes Hacker News posts and comments"
        assert len(first_member_call[1]["tools"]) > 0  # Should have the HN API tool
        
        # Check the second member (Topic_Analyzer) initialization
        second_member_call = mock_agent_class.call_args_list[1]
        assert second_member_call[1]["name"] == "Topic_Analyzer"
        assert second_member_call[1]["role"] == "Analyzes topics and trends among Hacker News posts"
        
        # Check the third member (Context_Researcher) initialization
        third_member_call = mock_agent_class.call_args_list[2]
        assert third_member_call[1]["name"] == "Context_Researcher"
        assert third_member_call[1]["role"] == "Provides broader context for Hacker News discussions"
        assert len(third_member_call[1]["tools"]) > 0  # Should have the web search tool
        
        # Verify each member has its own storage
        assert mock_get_pg_agent_storage.call_count == 1 + len(hn_team_config["members"])
    
    @patch("packages.phidata.src.cloudsql_pgvector.get_pg_agent_storage")
    @patch("packages.phidata.src.cloudsql_pgvector.get_pgvector_memory")
    @patch("importlib.import_module")
    async def test_hn_team_run_method(
        self, 
        mock_import_module, 
        mock_get_pgvector_memory, 
        mock_get_pg_agent_storage,
        hn_team_config, 
        mock_memory_manager,
        mock_llm_client, 
        mock_tool_registry
    ):
        """Test the run method of the HN Team agent."""
        # Setup agent and team module mock
        mock_agent_module = MagicMock()
        mock_team_module = MagicMock()
        mock_agent_class = MagicMock()
        mock_team_class = MagicMock()
        mock_team_instance = MagicMock()
        
        # Setup response mock with team collaboration
        mock_response = MagicMock()
        mock_response.content = """
        # Hacker News Analysis: Top Stories (April 25, 2025)
        
        ## Top Stories Report
        
        Based on our analysis of today's Hacker News activity, here are the key insights:
        
        ### Trending Topics
        
        1. **Advanced AI Systems** - 5 of the top 10 stories relate to new machine learning models and their implications
        2. **Web Development Frameworks** - Significant discussion around new frontend frameworks
        3. **Cybersecurity** - Multiple stories about recent data breaches and security vulnerabilities
        
        ### Most Discussed Story
        
        The most discussed story today is "New Research Shows 50% Efficiency Improvement in Quantum Computing Error Correction" with 142 comments. Key points from the discussion:
        
        - Many users are excited about the practical implications for quantum computing
        - There's healthy skepticism about the reproducibility of the results
        - Several experts in the field have weighed in with technical clarifications
        
        ### Community Sentiment
        
        Overall sentiment is positive (67%) with particular enthusiasm around open source AI models and quantum computing advancements.
        
        *This analysis was compiled by the Hacker News Analysis Team using data from April 25, 2025.*
        """
        
        mock_team_instance.run = AsyncMock(return_value=mock_response)
        mock_team_class.return_value = mock_team_instance
        
        mock_agent_module.Agent = mock_agent_class
        mock_team_module.Team = mock_team_class
        
        def mock_import_side_effect(name):
            if name == "agno.agent":
                return mock_agent_module
            elif name == "agno.team":
                return mock_team_module
            return MagicMock()
            
        mock_import_module.side_effect = mock_import_side_effect
        
        # Initialize the agent wrapper
        agent_wrapper = PhidataAgentWrapper(
            agent_config=hn_team_config,
            memory_manager=mock_memory_manager,
            llm_client=mock_llm_client,
            tool_registry=mock_tool_registry
        )
        
        # Create test input
        test_input = AgentInput(
            request_id="test-request",
            prompt="What are the trending topics on Hacker News today? Please provide a comprehensive analysis.",
            user_id="test-user",
            session_id="test-session"
        )
        
        # Run the agent
        output = await agent_wrapper.run(test_input)
        
        # Verify agent was called with correct parameters
        mock_team_instance.run.assert_called_once()
        call_kwargs = mock_team_instance.run.call_args[1]
        assert call_kwargs["message"] == "What are the trending topics on Hacker News today? Please provide a comprehensive analysis."
        assert call_kwargs["user_id"] == "test-user"
        assert call_kwargs["session_id"] == "test-session"
        
        # Verify output
        assert isinstance(output, AgentOutput)
        assert "Hacker News Analysis" in output.content
        assert "Trending Topics" in output.content
        assert "Advanced AI Systems" in output.content
        assert "Web Development Frameworks" in output.content
        assert "Community Sentiment" in output.content
