"""
Unit tests for the Rental Researcher specialized Phidata agent wrapper.

This tests the configuration, initialization, and behavior of the Rental Researcher
agent which is implemented as a specialized PhidataAgentWrapper.
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
    
    # Add a mock property search tool
    property_search_tool = MagicMock()
    property_search_tool.name = "property_search"
    property_search_tool.to_phidata_tool = MagicMock(return_value=MagicMock())
    mock.get_tool.return_value = property_search_tool
    
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
def rental_researcher_config():
    """Create a test config for the Rental Researcher agent."""
    return {
        "id": "rental-researcher",
        "name": "Rental Property Researcher",
        "description": "Specialized agent for researching rental properties",
        "phidata_agent_class": "agno.agent.Agent",
        "llm_ref": "gpt_4o",
        "markdown": True,
        "show_tool_calls": True,
        "streaming": True,
        
        # Storage configuration
        "storage": {
            "table_name": "rental_researcher_storage",
            "schema_name": "llm"
        },
        
        # Memory configuration
        "memory": {
            "table_name": "rental_researcher_memory",
            "schema_name": "llm",
            "vector_dimension": 768
        },
        
        # Tools configuration
        "tools": [
            {
                "type": "registry:property_search",
                "params": {
                    "api_key": "MOCK_API_KEY"
                }
            },
            {
                "type": "phi.tools.web.WebSearch",
                "params": {
                    "api_key": "MOCK_API_KEY",
                    "search_engine_id": "MOCK_ENGINE_ID"
                }
            }
        ],
        
        # Agent instructions
        "instructions": [
            "You are a specialized rental property research assistant.",
            "Your goal is to help users find rental properties that match their criteria.",
            "Use the property_search tool to find listings that meet user requirements.",
            "Use the web search tool to find additional information about neighborhoods.",
            "Always provide detailed information about rental properties including:",
            "- Price and fees",
            "- Square footage and number of rooms",
            "- Amenities and features",
            "- Location and nearby points of interest",
            "- Transportation options"
        ]
    }


@pytest.mark.asyncio
class TestRentalResearcherAgent:
    """Test suite for the Rental Researcher Phidata agent wrapper."""
    
    @patch("packages.phidata.src.cloudsql_pgvector.get_pg_agent_storage")
    @patch("packages.phidata.src.cloudsql_pgvector.get_pgvector_memory")
    @patch("importlib.import_module")
    async def test_rental_researcher_initialization(
        self, 
        mock_import_module, 
        mock_get_pgvector_memory, 
        mock_get_pg_agent_storage,
        rental_researcher_config, 
        mock_memory_manager,
        mock_llm_client, 
        mock_tool_registry,
        mock_pg_agent_storage,
        mock_pgvector_memory
    ):
        """Test initialization of the Rental Researcher agent."""
        # Setup mocks
        mock_get_pg_agent_storage.return_value = mock_pg_agent_storage
        mock_get_pgvector_memory.return_value = mock_pgvector_memory
        
        # Mock agent module import
        mock_agent_module = MagicMock()
        mock_agent_class = MagicMock()
        mock_agent_instance = MagicMock()
        mock_agent_module.Agent = mock_agent_class
        mock_agent_class.return_value = mock_agent_instance
        
        def mock_import_side_effect(name):
            if name == "agno.agent":
                return mock_agent_module
            return MagicMock()
            
        mock_import_module.side_effect = mock_import_side_effect
        
        # Initialize the agent wrapper
        agent_wrapper = PhidataAgentWrapper(
            agent_config=rental_researcher_config,
            memory_manager=mock_memory_manager,
            llm_client=mock_llm_client,
            tool_registry=mock_tool_registry
        )
        
        # Verify the agent was initialized with correct parameters
        assert agent_wrapper.name == "Rental Property Researcher"
        assert agent_wrapper.id == "rental-researcher"
        assert agent_wrapper.agent_type == "phidata"
        assert agent_wrapper._is_team is False
        
        # Verify PostgreSQL storage was initialized correctly
        mock_get_pg_agent_storage.assert_called_once_with(
            agent_id="rental-researcher",
            config={},  # Default empty dict if not specified
            table_name="rental_researcher_storage"
        )
        
        # Verify PGVector memory was initialized correctly
        mock_get_pgvector_memory.assert_called_once()
        
        # Verify Phidata Agent was initialized with correct parameters
        mock_agent_class.assert_called_once()
        call_kwargs = mock_agent_class.call_args[1]
        assert call_kwargs["name"] == "Rental Property Researcher"
        assert call_kwargs["markdown"] is True
        assert call_kwargs["show_tool_calls"] is True
        assert call_kwargs["storage"] == mock_pg_agent_storage
        assert call_kwargs["memory"] == mock_pgvector_memory
        assert len(call_kwargs["instructions"]) > 0
        
        # Verify tools were initialized
        assert call_kwargs["tools"] is not None
        
        # Verify LLM was fetched correctly
        assert agent_wrapper._get_llm_from_ref("gpt_4o") == mock_llm_client.gpt_4o
    
    @patch("packages.phidata.src.cloudsql_pgvector.get_pg_agent_storage")
    @patch("packages.phidata.src.cloudsql_pgvector.get_pgvector_memory")
    @patch("importlib.import_module")
    async def test_rental_researcher_run(
        self, 
        mock_import_module, 
        mock_get_pgvector_memory, 
        mock_get_pg_agent_storage,
        rental_researcher_config, 
        mock_memory_manager,
        mock_llm_client, 
        mock_tool_registry
    ):
        """Test the run method of the Rental Researcher agent."""
        # Setup agent module mock
        mock_agent_module = MagicMock()
        mock_agent_class = MagicMock()
        mock_agent_instance = MagicMock()
        mock_agent_module.Agent = mock_agent_class
        mock_agent_class.return_value = mock_agent_instance
        
        # Setup response mock
        mock_response = MagicMock()
        mock_response.content = "I found 3 rental properties matching your criteria in San Francisco."
        mock_agent_instance.run = AsyncMock(return_value=mock_response)
        
        def mock_import_side_effect(name):
            if name == "agno.agent":
                return mock_agent_module
            return MagicMock()
            
        mock_import_module.side_effect = mock_import_side_effect
        
        # Initialize the agent wrapper
        agent_wrapper = PhidataAgentWrapper(
            agent_config=rental_researcher_config,
            memory_manager=mock_memory_manager,
            llm_client=mock_llm_client,
            tool_registry=mock_tool_registry
        )
        
        # Create test input
        test_input = AgentInput(
            request_id="test-request",
            prompt="Find apartments in San Francisco under $3000 with 2 bedrooms",
            user_id="test-user",
            session_id="test-session"
        )
        
        # Run the agent
        output = await agent_wrapper.run(test_input)
        
        # Verify agent was called with correct parameters
        mock_agent_instance.run.assert_called_once()
        call_kwargs = mock_agent_instance.run.call_args[1]
        assert call_kwargs["message"] == "Find apartments in San Francisco under $3000 with 2 bedrooms"
        assert call_kwargs["user_id"] == "test-user"
        assert call_kwargs["session_id"] == "test-session"
        
        # Verify output
        assert isinstance(output, AgentOutput)
        assert output.content == "I found 3 rental properties matching your criteria in San Francisco."
        assert output.content_type == "text/markdown"
        assert output.agent_type == "phidata"
    
    @patch("packages.phidata.src.cloudsql_pgvector.get_pg_agent_storage")
    @patch("packages.phidata.src.cloudsql_pgvector.get_pgvector_memory")
    @patch("importlib.import_module")
    async def test_rental_researcher_streaming(
        self, 
        mock_import_module, 
        mock_get_pgvector_memory, 
        mock_get_pg_agent_storage,
        rental_researcher_config, 
        mock_memory_manager,
        mock_llm_client, 
        mock_tool_registry
    ):
        """Test the streaming response handling of the Rental Researcher agent."""
        # Setup agent module mock
        mock_agent_module = MagicMock()
        mock_agent_class = MagicMock()
        mock_agent_instance = MagicMock()
        mock_agent_module.Agent = mock_agent_class
        mock_agent_class.return_value = mock_agent_instance
        
        # Setup streaming response mock (generator)
        async def mock_streaming_generator():
            chunks = [
                MagicMock(content="I found "),
                MagicMock(content="3 rental "),
                MagicMock(content="properties matching "),
                MagicMock(content="your criteria in "),
                MagicMock(content="San Francisco.")
            ]
            for chunk in chunks:
                yield chunk
        
        mock_agent_instance.run = AsyncMock(return_value=mock_streaming_generator())
        
        def mock_import_side_effect(name):
            if name == "agno.agent":
                return mock_agent_module
            return MagicMock()
            
        mock_import_module.side_effect = mock_import_side_effect
        
        # Initialize the agent wrapper
        agent_wrapper = PhidataAgentWrapper(
            agent_config=rental_researcher_config,
            memory_manager=mock_memory_manager,
            llm_client=mock_llm_client,
            tool_registry=mock_tool_registry
        )
        
        # Create test input
        test_input = AgentInput(
            request_id="test-request",
            prompt="Find apartments in San Francisco under $3000 with 2 bedrooms",
            user_id="test-user",
            session_id="test-session"
        )
        
        # Run the agent
        output = await agent_wrapper.run(test_input)
        
        # Verify output contains the combined streaming content
        assert isinstance(output, AgentOutput)
        assert output.content == "I found 3 rental properties matching your criteria in San Francisco."
        assert output.content_type == "text/markdown"
