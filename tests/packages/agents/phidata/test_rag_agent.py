"""
Unit tests for the RAG (Retrieval-Augmented Generation) Phidata agent wrapper.

This tests the configuration, initialization, and behavior of the RAG agent
which uses PGVector for document retrieval and LLM for response generation.
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
    setattr(mock, "claude_3_opus", mock_model)
    
    return mock


@pytest.fixture
def mock_tool_registry():
    """Create a mock tool registry for testing."""
    mock = MagicMock()
    
    # Add a mock pdf_loader tool
    pdf_loader_tool = MagicMock()
    pdf_loader_tool.name = "pdf_loader"
    pdf_loader_tool.to_phidata_tool = MagicMock(return_value=MagicMock())
    mock.get_tool.return_value = pdf_loader_tool
    
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
    # Add search method to mock vector operations
    mock.search = AsyncMock(return_value=[
        {"text": "Document content 1", "metadata": {"source": "doc1.pdf"}},
        {"text": "Document content 2", "metadata": {"source": "doc2.pdf"}}
    ])
    return mock


@pytest.fixture
def rag_agent_config():
    """Create a test config for the RAG agent."""
    return {
        "id": "rag-agent",
        "name": "RAG Knowledge Assistant",
        "description": "Document-based retrieval augmented generation agent",
        "phidata_agent_class": "agno.agent.Agent",
        "llm_ref": "claude_3_opus",
        "markdown": True,
        "show_tool_calls": True,
        "streaming": False,
        
        # Storage configuration
        "storage": {
            "table_name": "rag_agent_storage",
            "schema_name": "llm"
        },
        
        # Memory configuration with PGVector
        "memory": {
            "table_name": "rag_agent_memory",
            "schema_name": "llm",
            "vector_dimension": 768
        },
        
        # Tools configuration
        "tools": [
            {
                "type": "registry:pdf_loader",
                "params": {
                    "chunk_size": 1000,
                    "chunk_overlap": 200
                }
            },
            {
                "type": "phi.tools.filesystem.ReadFile",
                "params": {}
            }
        ],
        
        # Agent instructions
        "instructions": [
            "You are a document-based RAG assistant that helps users find information in their documents.",
            "You have access to a vector database that contains document chunks.",
            "When answering questions, first retrieve relevant documents using vector search.",
            "Then use the retrieved information to generate accurate and informative responses.",
            "Always cite sources when providing information from documents.",
            "If the information cannot be found in the documents, clearly state that."
        ]
    }


@pytest.mark.asyncio
class TestRAGAgent:
    """Test suite for the RAG Phidata agent wrapper."""
    
    @patch("packages.phidata.src.cloudsql_pgvector.get_pg_agent_storage")
    @patch("packages.phidata.src.cloudsql_pgvector.get_pgvector_memory")
    @patch("importlib.import_module")
    async def test_rag_agent_initialization(
        self, 
        mock_import_module, 
        mock_get_pgvector_memory, 
        mock_get_pg_agent_storage,
        rag_agent_config, 
        mock_memory_manager,
        mock_llm_client, 
        mock_tool_registry,
        mock_pg_agent_storage,
        mock_pgvector_memory
    ):
        """Test initialization of the RAG agent."""
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
            agent_config=rag_agent_config,
            memory_manager=mock_memory_manager,
            llm_client=mock_llm_client,
            tool_registry=mock_tool_registry
        )
        
        # Verify the agent was initialized with correct parameters
        assert agent_wrapper.name == "RAG Knowledge Assistant"
        assert agent_wrapper.id == "rag-agent"
        assert agent_wrapper.agent_type == "phidata"
        
        # Verify PostgreSQL storage was initialized correctly
        mock_get_pg_agent_storage.assert_called_once_with(
            agent_id="rag-agent",
            config={},  # Default empty dict if not specified
            table_name="rag_agent_storage"
        )
        
        # Verify PGVector memory was initialized correctly
        mock_get_pgvector_memory.assert_called_once()
        
        # Verify Phidata Agent was initialized with correct parameters
        mock_agent_class.assert_called_once()
        call_kwargs = mock_agent_class.call_args[1]
        assert "instructions" in call_kwargs
        assert call_kwargs["storage"] == mock_pg_agent_storage
        assert call_kwargs["memory"] == mock_pgvector_memory
    
    @patch("packages.phidata.src.cloudsql_pgvector.get_pg_agent_storage")
    @patch("packages.phidata.src.cloudsql_pgvector.get_pgvector_memory")
    @patch("importlib.import_module")
    async def test_rag_agent_run_with_document_retrieval(
        self, 
        mock_import_module, 
        mock_get_pgvector_memory, 
        mock_get_pg_agent_storage,
        rag_agent_config, 
        mock_memory_manager,
        mock_llm_client, 
        mock_tool_registry,
        mock_pgvector_memory
    ):
        """Test the run method of the RAG agent with document retrieval."""
        # Setup agent module mock
        mock_agent_module = MagicMock()
        mock_agent_class = MagicMock()
        mock_agent_instance = MagicMock()
        mock_agent_module.Agent = mock_agent_class
        mock_agent_class.return_value = mock_agent_instance
        
        # Setup mock for vector database result
        mock_get_pgvector_memory.return_value = mock_pgvector_memory
        
        # Setup response mock that includes retrieved document information
        mock_response = MagicMock()
        mock_response.content = """
        Based on the documents I found:
        
        The quarterly report shows a 12% increase in revenue compared to last year.
        The growth was primarily driven by the new product line launched in Q2.
        
        Source: doc1.pdf
        """
        mock_agent_instance.run = AsyncMock(return_value=mock_response)
        
        def mock_import_side_effect(name):
            if name == "agno.agent":
                return mock_agent_module
            return MagicMock()
            
        mock_import_module.side_effect = mock_import_side_effect
        
        # Initialize the agent wrapper
        agent_wrapper = PhidataAgentWrapper(
            agent_config=rag_agent_config,
            memory_manager=mock_memory_manager,
            llm_client=mock_llm_client,
            tool_registry=mock_tool_registry
        )
        
        # Create test input
        test_input = AgentInput(
            request_id="test-request",
            prompt="What were the key findings in the quarterly report?",
            user_id="test-user",
            session_id="test-session",
            metadata={"document_id": "quarterly_report_2023Q4"}
        )
        
        # Run the agent
        output = await agent_wrapper.run(test_input)
        
        # Verify agent was called with correct parameters
        mock_agent_instance.run.assert_called_once()
        call_kwargs = mock_agent_instance.run.call_args[1]
        assert call_kwargs["message"] == "What were the key findings in the quarterly report?"
        assert call_kwargs["user_id"] == "test-user"
        assert call_kwargs["session_id"] == "test-session"
        assert "document_id" in call_kwargs
        
        # Verify output contains retrieved information
        assert isinstance(output, AgentOutput)
        assert "12% increase in revenue" in output.content
        assert "Source: doc1.pdf" in output.content
    
    @patch("packages.phidata.src.cloudsql_pgvector.get_pg_agent_storage")
    @patch("packages.phidata.src.cloudsql_pgvector.get_pgvector_memory")
    @patch("importlib.import_module")
    async def test_rag_agent_vector_search_integration(
        self, 
        mock_import_module, 
        mock_get_pgvector_memory, 
        mock_get_pg_agent_storage,
        rag_agent_config, 
        mock_memory_manager,
        mock_llm_client, 
        mock_tool_registry,
        mock_pgvector_memory
    ):
        """Test the integration with vector search for the RAG agent."""
        # Setup agent module mock
        mock_agent_module = MagicMock()
        mock_phi_tools_module = MagicMock()
        
        # Create a mock PGVector class that simulates vector operations
        class MockPgVector:
            def __init__(self, *args, **kwargs):
                pass
                
            async def search(self, query, limit=5):
                return [
                    {"text": "Revenue increased by 12% in Q4 2023", "metadata": {"source": "financial_report.pdf", "page": 5}},
                    {"text": "New product line contributed to 8% of total revenue", "metadata": {"source": "financial_report.pdf", "page": 7}}
                ]
                
            async def add_texts(self, texts, metadatas=None):
                return ["id1", "id2"]
                
        # Add the mock to the module
        mock_phi_tools_module.PgVector = MockPgVector
        
        mock_agent_instance = MagicMock()
        mock_agent_instance.memory = mock_pgvector_memory
        mock_agent_class = MagicMock(return_value=mock_agent_instance)
        mock_agent_module.Agent = mock_agent_class
        
        def mock_import_side_effect(name):
            if name == "agno.agent":
                return mock_agent_module
            if name == "phi.tools.vector":
                return mock_phi_tools_module
            return MagicMock()
            
        mock_import_module.side_effect = mock_import_side_effect
        
        # Setup response that includes document information
        mock_response = MagicMock()
        mock_response.content = "Based on the financial report, revenue increased by 12% in Q4 2023."
        mock_agent_instance.run = AsyncMock(return_value=mock_response)
        
        # Initialize the agent wrapper
        agent_wrapper = PhidataAgentWrapper(
            agent_config=rag_agent_config,
            memory_manager=mock_memory_manager,
            llm_client=mock_llm_client,
            tool_registry=mock_tool_registry
        )
        agent_wrapper.agent_memory = mock_pgvector_memory
        
        # Create test input
        test_input = AgentInput(
            request_id="test-request",
            prompt="What was the revenue growth in Q4 2023?",
            user_id="test-user",
            session_id="test-session"
        )
        
        # Run the agent
        output = await agent_wrapper.run(test_input)
        
        # Verify output includes information from the vector search
        assert isinstance(output, AgentOutput)
        assert "revenue increased by 12% in q4 2023" in output.content.lower()
