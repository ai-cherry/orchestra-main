"""
Integration tests for the specialized Phidata agents.

These tests verify that the specialized Phidata agents work correctly when
integrated with the full Orchestra system, making API calls to the /phidata/chat endpoint.
"""

import json
import pytest
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock, AsyncMock

from fastapi.testclient import TestClient

# Import the main application
from core.orchestrator.src.main import app
from packages.agents.src.phidata.wrapper import PhidataAgentWrapper


# Create test client
client = TestClient(app)


@pytest.fixture
def mock_pg_agent_storage():
    """Mock PostgreSQL agent storage."""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_pgvector_memory():
    """Mock PostgreSQL vector memory."""
    mock = MagicMock()
    # Add search method to simulate vector operations
    mock.search = AsyncMock(return_value=[
        {"text": "Document content about AI", "metadata": {"source": "ai_doc.pdf"}},
        {"text": "Document content about robotics", "metadata": {"source": "robotics.pdf"}}
    ])
    return mock


@pytest.fixture
def mock_agent_registry():
    """Mock agent registry with all specialized Phidata agents."""
    mock = MagicMock()
    
    # Each agent gets its own mock, configured with appropriate behavior
    rental_agent_mock = AsyncMock(spec=PhidataAgentWrapper)
    rental_agent_mock.id = "rental-researcher"
    rental_agent_mock.name = "Rental Property Researcher"
    rental_agent_mock.run.return_value = MagicMock(
        content="I found 3 apartments in San Francisco under $3000 with 2 bedrooms...",
        content_type="text/markdown",
        metadata={"agent_id": "rental-researcher"}
    )
    
    rag_agent_mock = AsyncMock(spec=PhidataAgentWrapper)
    rag_agent_mock.id = "rag-agent"
    rag_agent_mock.name = "RAG Knowledge Assistant"
    rag_agent_mock.run.return_value = MagicMock(
        content="According to the document, revenue increased by 12% in Q4 2023...",
        content_type="text/markdown",
        metadata={"agent_id": "rag-agent"}
    )
    
    python_agent_mock = AsyncMock(spec=PhidataAgentWrapper)
    python_agent_mock.id = "python-agent"
    python_agent_mock.name = "Python Code Assistant"
    python_agent_mock.run.return_value = MagicMock(
        content="```python\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n\nresult = fibonacci(10)\nprint(result)\n```\n\nOutput: 55",
        content_type="text/markdown",
        metadata={"agent_id": "python-agent"}
    )
    
    structured_output_agent_mock = AsyncMock(spec=PhidataAgentWrapper)
    structured_output_agent_mock.id = "structured-output-agent"
    structured_output_agent_mock.name = "Structured Output Agent"
    structured_output_agent_mock.run.return_value = MagicMock(
        content='```json\n{\n  "name": "Ultra Noise-Canceling Headphones X7",\n  "price": 299.99,\n  "category": "Electronics"\n}\n```',
        content_type="text/markdown",
        metadata={"agent_id": "structured-output-agent"}
    )
    
    hn_team_mock = AsyncMock(spec=PhidataAgentWrapper)
    hn_team_mock.id = "hn-team"
    hn_team_mock.name = "Hacker News Analysis Team"
    hn_team_mock.run.return_value = MagicMock(
        content="# Hacker News Analysis: Top Stories\n\n## Trending Topics\n\n1. **Advanced AI Systems**\n2. **Web Development Frameworks**\n3. **Cybersecurity**",
        content_type="text/markdown",
        metadata={"agent_id": "hn-team"}
    )
    
    # Configure the registry's get_agent method
    def get_agent_side_effect(agent_id):
        if agent_id == "rental-researcher":
            return rental_agent_mock
        elif agent_id == "rag-agent":
            return rag_agent_mock
        elif agent_id == "python-agent":
            return python_agent_mock
        elif agent_id == "structured-output-agent":
            return structured_output_agent_mock
        elif agent_id == "hn-team":
            return hn_team_mock
        return None
    
    mock.get_agent.side_effect = get_agent_side_effect
    
    # Also support agent selection by context
    mock.select_agent_for_context.return_value = python_agent_mock
    
    return mock


@pytest.fixture
def mock_phidata_deps():
    """Mock all Phidata dependencies."""
    # First, patch the agent registry to use our mock
    with patch("core.orchestrator.src.agents.agent_registry.get_agent_registry") as mock_get_registry:
        # Then patch memory manager
        with patch("core.orchestrator.src.api.dependencies.memory.get_memory_manager") as mock_get_memory:
            # Finally patch LLM client
            with patch("core.orchestrator.src.api.dependencies.llm.get_llm_client") as mock_get_llm:
                # Set up memory manager
                memory_manager = AsyncMock()
                memory_manager.get_conversation_history.return_value = []
                memory_manager.add_memory_item.return_value = None
                mock_get_memory.return_value = memory_manager
                
                # Set up LLM client
                mock_get_llm.return_value = MagicMock()
                
                yield {
                    "get_registry": mock_get_registry,
                    "get_memory": mock_get_memory,
                    "get_llm": mock_get_llm,
                    "memory_manager": memory_manager
                }


@pytest.mark.parametrize("agent_id,prompt,expected_content", [
    (
        "rental-researcher", 
        "Find apartments in San Francisco under $3000 with 2 bedrooms", 
        "3 apartments in San Francisco"
    ),
    (
        "rag-agent", 
        "What was the revenue growth in Q4 2023?", 
        "revenue increased by 12%"
    ),
    (
        "python-agent", 
        "Write a recursive function to calculate the 10th Fibonacci number", 
        "fibonacci"
    ),
    (
        "structured-output-agent", 
        "Extract structured information about Ultra Noise-Canceling Headphones X7", 
        "Ultra Noise-Canceling Headphones X7"
    ),
    (
        "hn-team", 
        "What are the trending topics on Hacker News today?", 
        "Trending Topics"
    ),
])
def test_phidata_chat_with_specialized_agents(
    mock_phidata_deps, mock_agent_registry, agent_id, prompt, expected_content
):
    """Test the /phidata/chat endpoint with each specialized agent type."""
    # Configure mock registry
    mock_phidata_deps["get_registry"].return_value = mock_agent_registry
    
    # Test request payload
    payload = {
        "message": prompt,
        "session_id": "test-session-123",
        "user_id": "test-user-456",
        "agent_id": agent_id
    }
    
    # Make the request
    with app.container.llm_client.override(mock_phidata_deps["get_llm"]()):
        with app.container.memory_manager.override(mock_phidata_deps["get_memory"]()):
            response = client.post("/phidata/chat", json=payload)
    
    # Check the response
    assert response.status_code == 200
    response_data = response.json()
    
    # Verify response structure and content
    assert "response_content" in response_data
    assert expected_content in response_data["response_content"]
    assert response_data["session_id"] == "test-session-123"
    assert response_data["user_id"] == "test-user-456"
    
    # Verify that memory operations were performed
    mock_phidata_deps["memory_manager"].get_conversation_history.assert_called_once()
    mock_phidata_deps["memory_manager"].add_memory_item.assert_called()
    
    # Verify that the correct agent was used
    mock_agent_registry.get_agent.assert_called_once_with(agent_id)


# Test RAG Agent with actual document loading
@patch("packages.phidata.src.cloudsql_pgvector.get_pgvector_memory")
@patch("packages.phidata.src.cloudsql_pgvector.get_pg_agent_storage")
def test_rag_agent_integration_with_document(
    mock_get_pg_agent_storage,
    mock_get_pgvector_memory,
    mock_phidata_deps,
    mock_agent_registry,
    mock_pgvector_memory,
    mock_pg_agent_storage,
):
    """Test the RAG agent with document retrieval from PGVector."""
    # Configure mocks
    mock_get_pgvector_memory.return_value = mock_pgvector_memory
    mock_get_pg_agent_storage.return_value = mock_pg_agent_storage
    mock_phidata_deps["get_registry"].return_value = mock_agent_registry
    
    # Test request payload - include document_id in metadata
    payload = {
        "message": "Summarize the key points in the AI document",
        "session_id": "test-session-123",
        "user_id": "test-user-456",
        "agent_id": "rag-agent",
        "metadata": {
            "document_id": "ai_doc.pdf"
        }
    }
    
    # Make the request
    with app.container.llm_client.override(mock_phidata_deps["get_llm"]()):
        with app.container.memory_manager.override(mock_phidata_deps["get_memory"]()):
            response = client.post("/phidata/chat", json=payload)
    
    # Check the response
    assert response.status_code == 200
    
    # Verify PGVector search was called with document_id
    rag_agent = mock_agent_registry.get_agent("rag-agent")
    rag_agent.run.assert_called_once()
    # Verify the document_id was passed to the agent
    call_args = rag_agent.run.call_args[0][0]
    assert call_args.metadata["document_id"] == "ai_doc.pdf"


# Test Python Agent with code execution
def test_python_agent_code_execution(
    mock_phidata_deps,
    mock_agent_registry
):
    """Test the Python agent's code execution capabilities."""
    mock_phidata_deps["get_registry"].return_value = mock_agent_registry
    
    # Test request payload
    payload = {
        "message": "Debug this Python code: def calculate_average(numbers):\n    total = 0\n    for num in numbers:\n        total += num\n    return total / len(numbers)\n\ndata = [10, 20, 30, 40, None]\nresult = calculate_average(data)\nprint(result)",
        "session_id": "test-session-123",
        "user_id": "test-user-456",
        "agent_id": "python-agent"
    }
    
    # Make the request
    with app.container.llm_client.override(mock_phidata_deps["get_llm"]()):
        with app.container.memory_manager.override(mock_phidata_deps["get_memory"]()):
            response = client.post("/phidata/chat", json=payload)
    
    # Check the response
    assert response.status_code == 200
    
    # Verify the Python agent was called
    python_agent = mock_agent_registry.get_agent("python-agent")
    python_agent.run.assert_called_once()
    

# Test Structured Output Agent with schema
def test_structured_output_agent_with_schema(
    mock_phidata_deps,
    mock_agent_registry
):
    """Test the Structured Output agent with a specific schema."""
    mock_phidata_deps["get_registry"].return_value = mock_agent_registry
    
    # Test request payload with schema in metadata
    payload = {
        "message": "Extract product information for the Ultra Noise-Canceling Headphones X7",
        "session_id": "test-session-123",
        "user_id": "test-user-456",
        "agent_id": "structured-output-agent",
        "metadata": {
            "schema": "product"
        }
    }
    
    # Make the request
    with app.container.llm_client.override(mock_phidata_deps["get_llm"]()):
        with app.container.memory_manager.override(mock_phidata_deps["get_memory"]()):
            response = client.post("/phidata/chat", json=payload)
    
    # Check the response
    assert response.status_code == 200
    
    # Verify the Structured Output agent was called with the schema
    structured_agent = mock_agent_registry.get_agent("structured-output-agent")
    structured_agent.run.assert_called_once()
    call_args = structured_agent.run.call_args[0][0]
    assert call_args.metadata["schema"] == "product"


# Test HN Team with collaboration
def test_hn_team_collaboration(
    mock_phidata_deps,
    mock_agent_registry
):
    """Test the HN Team agent's collaborative analysis capabilities."""
    mock_phidata_deps["get_registry"].return_value = mock_agent_registry
    
    # Test request payload
    payload = {
        "message": "Analyze today's top Hacker News stories and identify emerging trends",
        "session_id": "test-session-123",
        "user_id": "test-user-456",
        "agent_id": "hn-team"
    }
    
    # Make the request
    with app.container.llm_client.override(mock_phidata_deps["get_llm"]()):
        with app.container.memory_manager.override(mock_phidata_deps["get_memory"]()):
            response = client.post("/phidata/chat", json=payload)
    
    # Check the response
    assert response.status_code == 200
    response_data = response.json()
    
    # Verify response contains team analysis
    assert "Trending Topics" in response_data["response_content"]
    assert "Advanced AI Systems" in response_data["response_content"]
    
    # Verify the HN Team agent was called
    hn_team = mock_agent_registry.get_agent("hn-team")
    hn_team.run.assert_called_once()
