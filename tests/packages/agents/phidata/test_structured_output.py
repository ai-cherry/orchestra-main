"""
Unit tests for the Structured Output specialized Phidata agent wrapper.

This tests the configuration, initialization, and behavior of the Structured Output agent
which is implemented to output data in specific structured formats using Pydantic models.
"""

import pytest
import asyncio
from typing import List, Dict, Optional
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
    setattr(mock, "claude_3_sonnet", mock_model)
    
    return mock


@pytest.fixture
def mock_tool_registry():
    """Create a mock tool registry for testing."""
    mock = MagicMock()
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
def structured_output_config():
    """Create a test config for the Structured Output agent."""
    return {
        "id": "structured-output-agent",
        "name": "Structured Output Agent",
        "description": "Agent that generates responses in structured formats using Pydantic models",
        "phidata_agent_class": "agno.agent.Agent",
        "llm_ref": "claude_3_sonnet",
        "markdown": True,
        "show_tool_calls": True,
        
        # Storage configuration
        "storage": {
            "table_name": "structured_output_storage",
            "schema_name": "llm"
        },
        
        # Memory configuration
        "memory": {
            "table_name": "structured_output_memory",
            "schema_name": "llm",
            "vector_dimension": 768
        },
        
        # Model schemas for structured output
        "output_schemas": {
            "product": """
            from pydantic import BaseModel, Field
            from typing import List, Optional
            
            class ProductReview(BaseModel):
                review_id: str = Field(..., description="Unique identifier for the review")
                rating: float = Field(..., description="Rating from 1-5 stars")
                review_text: str = Field(..., description="Text content of the review")
                pros: List[str] = Field(default_factory=list, description="List of positive points")
                cons: List[str] = Field(default_factory=list, description="List of negative points")
            
            class ProductInfo(BaseModel):
                name: str = Field(..., description="Product name")
                description: str = Field(..., description="Product description")
                price: float = Field(..., description="Product price")
                category: str = Field(..., description="Product category")
                features: List[str] = Field(default_factory=list, description="List of product features")
                reviews: List[ProductReview] = Field(default_factory=list, description="List of product reviews")
                average_rating: Optional[float] = Field(None, description="Average of all review ratings")
            """,
            
            "article": """
            from pydantic import BaseModel, Field
            from typing import List, Optional, Dict
            from datetime import datetime
            
            class Author(BaseModel):
                name: str = Field(..., description="Author's name")
                bio: Optional[str] = Field(None, description="Author's biography")
                
            class Article(BaseModel):
                title: str = Field(..., description="Article title")
                author: Author = Field(..., description="Article author")
                content: str = Field(..., description="Main article content")
                summary: str = Field(..., description="Brief summary of the article")
                keywords: List[str] = Field(default_factory=list, description="Keywords related to the article")
                published_date: str = Field(..., description="Date published in ISO format")
                categories: List[str] = Field(default_factory=list, description="Article categories")
            """
        },
        
        # Instructions for the agent
        "instructions": [
            "You are a specialized agent that converts unstructured text into structured data.",
            "When given information, extract relevant details and organize them according to the specified schema.",
            "If asked about a product, use the ProductInfo schema to structure your response.",
            "If asked about an article, use the Article schema to structure your response.",
            "Always validate that your output conforms to the specified schema.",
            "If information is missing for required fields, make a reasonable inference or state that it's unknown.",
            "Always respond with a combination of structured output and a brief summary of what you extracted.",
            "Format structured data using proper JSON format within markdown code blocks."
        ]
    }


@pytest.mark.asyncio
class TestStructuredOutputAgent:
    """Test suite for the Structured Output Phidata agent wrapper."""
    
    @patch("packages.phidata.src.cloudsql_pgvector.get_pg_agent_storage")
    @patch("packages.phidata.src.cloudsql_pgvector.get_pgvector_memory")
    @patch("importlib.import_module")
    async def test_structured_output_agent_initialization(
        self, 
        mock_import_module, 
        mock_get_pgvector_memory, 
        mock_get_pg_agent_storage,
        structured_output_config, 
        mock_memory_manager,
        mock_llm_client, 
        mock_tool_registry,
        mock_pg_agent_storage,
        mock_pgvector_memory
    ):
        """Test initialization of the Structured Output agent."""
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
            agent_config=structured_output_config,
            memory_manager=mock_memory_manager,
            llm_client=mock_llm_client,
            tool_registry=mock_tool_registry
        )
        
        # Verify the agent was initialized with correct parameters
        assert agent_wrapper.name == "Structured Output Agent"
        assert agent_wrapper.id == "structured-output-agent"
        assert agent_wrapper.agent_type == "phidata"
        
        # Verify PostgreSQL storage was initialized correctly
        mock_get_pg_agent_storage.assert_called_once_with(
            agent_id="structured-output-agent",
            config={},  # Default empty dict if not specified
            table_name="structured_output_storage"
        )
        
        # Verify PGVector memory was initialized correctly
        mock_get_pgvector_memory.assert_called_once()
        
        # Verify Phidata Agent was initialized with correct parameters
        mock_agent_class.assert_called_once()
        call_kwargs = mock_agent_class.call_args[1]
        assert call_kwargs["name"] == "Structured Output Agent"
        assert call_kwargs["storage"] == mock_pg_agent_storage
        assert call_kwargs["memory"] == mock_pgvector_memory
        
        # Verify LLM was fetched correctly
        assert agent_wrapper._get_llm_from_ref("claude_3_sonnet") == mock_llm_client.claude_3_sonnet
    
    @patch("packages.phidata.src.cloudsql_pgvector.get_pg_agent_storage")
    @patch("packages.phidata.src.cloudsql_pgvector.get_pgvector_memory")
    @patch("importlib.import_module")
    async def test_structured_output_product_schema(
        self, 
        mock_import_module, 
        mock_get_pgvector_memory, 
        mock_get_pg_agent_storage,
        structured_output_config, 
        mock_memory_manager,
        mock_llm_client, 
        mock_tool_registry
    ):
        """Test the structured output agent with product schema."""
        # Setup agent module mock
        mock_agent_module = MagicMock()
        mock_agent_class = MagicMock()
        mock_agent_instance = MagicMock()
        mock_agent_module.Agent = mock_agent_class
        mock_agent_class.return_value = mock_agent_instance
        
        # Setup response mock with structured product data
        mock_response = MagicMock()
        mock_response.content = """
        I've structured the product information according to the ProductInfo schema:

        ```json
        {
          "name": "Ultra Noise-Canceling Headphones X7",
          "description": "Premium wireless headphones with advanced active noise cancellation and high-fidelity sound",
          "price": 299.99,
          "category": "Electronics",
          "features": [
            "50-hour battery life", 
            "Active noise cancellation", 
            "Bluetooth 5.2", 
            "Comfortable memory foam ear cups",
            "Voice assistant integration"
          ],
          "reviews": [
            {
              "review_id": "R123456",
              "rating": 4.5,
              "review_text": "These headphones have amazing sound quality and the noise cancellation is top-notch.",
              "pros": ["Great sound", "Effective noise cancellation", "Long battery life"],
              "cons": ["Slightly heavy", "Expensive"]
            },
            {
              "review_id": "R789012",
              "rating": 5.0,
              "review_text": "Absolutely worth every penny. Best headphones I've ever owned.",
              "pros": ["Comfortable fit", "Premium build quality", "Perfect sound balance"],
              "cons": []
            }
          ],
          "average_rating": 4.75
        }
        ```

        This structured data captures all the key information about the Ultra Noise-Canceling Headphones X7, including its features, price, category, and customer reviews. The average rating of 4.75 out of 5 stars indicates high customer satisfaction.
        """
        mock_agent_instance.run = AsyncMock(return_value=mock_response)
        
        def mock_import_side_effect(name):
            if name == "agno.agent":
                return mock_agent_module
            return MagicMock()
            
        mock_import_module.side_effect = mock_import_side_effect
        
        # Initialize the agent wrapper
        agent_wrapper = PhidataAgentWrapper(
            agent_config=structured_output_config,
            memory_manager=mock_memory_manager,
            llm_client=mock_llm_client,
            tool_registry=mock_tool_registry
        )
        
        # Create test input
        test_input = AgentInput(
            request_id="test-request",
            prompt="Extract structured information about this product: Ultra Noise-Canceling Headphones X7 is a premium wireless headphone priced at $299.99. It features 50-hour battery life, active noise cancellation, Bluetooth 5.2, and memory foam ear cups. One customer said 'These headphones have amazing sound quality and the noise cancellation is top-notch' and gave it 4.5/5 stars. Another review gave it a perfect 5/5 stars saying 'Absolutely worth every penny. Best headphones I've ever owned.'",
            user_id="test-user",
            session_id="test-session",
            metadata={"schema": "product"}
        )
        
        # Run the agent
        output = await agent_wrapper.run(test_input)
        
        # Verify output contains structured data
        assert isinstance(output, AgentOutput)
        assert "Ultra Noise-Canceling Headphones X7" in output.content
        assert "299.99" in output.content
        assert "json" in output.content.lower()
        assert "average_rating" in output.content
        assert "4.75" in output.content
    
    @patch("packages.phidata.src.cloudsql_pgvector.get_pg_agent_storage")
    @patch("packages.phidata.src.cloudsql_pgvector.get_pgvector_memory")
    @patch("importlib.import_module")
    async def test_structured_output_article_schema(
        self, 
        mock_import_module, 
        mock_get_pgvector_memory, 
        mock_get_pg_agent_storage,
        structured_output_config, 
        mock_memory_manager,
        mock_llm_client, 
        mock_tool_registry
    ):
        """Test the structured output agent with article schema."""
        # Setup agent module mock
        mock_agent_module = MagicMock()
        mock_agent_class = MagicMock()
        mock_agent_instance = MagicMock()
        mock_agent_module.Agent = mock_agent_class
        mock_agent_class.return_value = mock_agent_instance
        
        # Setup response mock with structured article data
        mock_response = MagicMock()
        mock_response.content = """
        I've extracted and structured the article information according to the Article schema:

        ```json
        {
          "title": "Advances in Quantum Computing: Breaking New Ground",
          "author": {
            "name": "Dr. Emily Chen",
            "bio": "Quantum physicist and research lead at Quantum Innovations Lab"
          },
          "content": "Recent breakthroughs in quantum computing have shown promising results in solving complex problems that were previously intractable with classical computers. Researchers at MIT have developed a new approach to qubit stability that could lead to significant advances in error correction, one of the biggest challenges in quantum computing today. The new technique, which involves a novel method of shielding qubits from environmental noise, has shown an impressive 50% reduction in decoherence...",
          "summary": "New research demonstrates significant advances in quantum computing stability, potentially bringing practical quantum computers closer to reality.",
          "keywords": ["quantum computing", "qubits", "decoherence", "error correction", "quantum physics"],
          "published_date": "2023-11-15",
          "categories": ["Technology", "Science", "Physics", "Computing"]
        }
        ```

        This structured data captures the key elements of the article about quantum computing advances. The article discusses new techniques for improving qubit stability and error correction, written by Dr. Emily Chen, a quantum physicist. It was published on November 15, 2023, and categorized under Technology, Science, Physics, and Computing.
        """
        mock_agent_instance.run = AsyncMock(return_value=mock_response)
        
        def mock_import_side_effect(name):
            if name == "agno.agent":
                return mock_agent_module
            return MagicMock()
            
        mock_import_module.side_effect = mock_import_side_effect
        
        # Initialize the agent wrapper
        agent_wrapper = PhidataAgentWrapper(
            agent_config=structured_output_config,
            memory_manager=mock_memory_manager,
            llm_client=mock_llm_client,
            tool_registry=mock_tool_registry
        )
        
        # Create test input
        test_input = AgentInput(
            request_id="test-request",
            prompt="Extract structured information from this article text: 'Advances in Quantum Computing: Breaking New Ground' by Dr. Emily Chen, a quantum physicist at Quantum Innovations Lab. Published on November 15, 2023. The article discusses recent breakthroughs in quantum computing, particularly advances in qubit stability and error correction developed by MIT researchers, which showed a 50% reduction in decoherence.",
            user_id="test-user",
            session_id="test-session",
            metadata={"schema": "article"}
        )
        
        # Run the agent
        output = await agent_wrapper.run(test_input)
        
        # Verify output contains structured data
        assert isinstance(output, AgentOutput)
        assert "Advances in Quantum Computing" in output.content
        assert "Dr. Emily Chen" in output.content
        assert "json" in output.content.lower()
        assert "published_date" in output.content
        assert "2023-11-15" in output.content
