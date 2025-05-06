"""
Unit tests for the Python specialized Phidata agent wrapper.

This tests the configuration, initialization, and behavior of the Python agent
which is implemented to execute and explain Python code.
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
    setattr(mock, "gpt_4_turbo", mock_model)
    
    return mock


@pytest.fixture
def mock_tool_registry():
    """Create a mock tool registry for testing."""
    mock = MagicMock()
    
    # Add a mock code execution tool
    code_execution_tool = MagicMock()
    code_execution_tool.name = "python_executor"
    code_execution_tool.to_phidata_tool = MagicMock(return_value=MagicMock())
    mock.get_tool.return_value = code_execution_tool
    
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
def python_agent_config():
    """Create a test config for the Python agent."""
    return {
        "id": "python-agent",
        "name": "Python Code Assistant",
        "description": "Specialized agent for executing and analyzing Python code",
        "phidata_agent_class": "agno.agent.Agent",
        "llm_ref": "gpt_4_turbo",
        "markdown": True,
        "show_tool_calls": True,
        "streaming": False,
        
        # Storage configuration
        "storage": {
            "table_name": "python_agent_storage",
            "schema_name": "llm"
        },
        
        # Memory configuration
        "memory": {
            "table_name": "python_agent_memory",
            "schema_name": "llm",
            "vector_dimension": 768
        },
        
        # Tools configuration
        "tools": [
            {
                "type": "registry:python_executor",
                "params": {
                    "timeout": 10,  # Maximum execution time in seconds
                    "max_code_length": 5000  # Maximum code length to execute
                }
            },
            {
                "type": "phi.tools.filesystem.ReadFile",
                "params": {}
            },
            {
                "type": "phi.tools.filesystem.WriteFile",
                "params": {}
            }
        ],
        
        # Agent instructions
        "instructions": [
            "You are a specialized Python code assistant.",
            "You can help users with writing, debugging, and executing Python code.",
            "Always use the python_executor tool to run code when testing solutions.",
            "Provide detailed explanations of your code and its logic.",
            "When debugging, first identify the issue and then suggest fixes.",
            "When a user asks you to optimize code, analyze time and space complexity.",
            "You can also read and write files to assist in code development.",
            "Always format code blocks with proper syntax highlighting using markdown."
        ]
    }


@pytest.mark.asyncio
class TestPythonAgent:
    """Test suite for the Python Phidata agent wrapper."""
    
    @patch("packages.phidata.src.cloudsql_pgvector.get_pg_agent_storage")
    @patch("packages.phidata.src.cloudsql_pgvector.get_pgvector_memory")
    @patch("importlib.import_module")
    async def test_python_agent_initialization(
        self, 
        mock_import_module, 
        mock_get_pgvector_memory, 
        mock_get_pg_agent_storage,
        python_agent_config, 
        mock_memory_manager,
        mock_llm_client, 
        mock_tool_registry,
        mock_pg_agent_storage,
        mock_pgvector_memory
    ):
        """Test initialization of the Python agent."""
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
            agent_config=python_agent_config,
            memory_manager=mock_memory_manager,
            llm_client=mock_llm_client,
            tool_registry=mock_tool_registry
        )
        
        # Verify the agent was initialized with correct parameters
        assert agent_wrapper.name == "Python Code Assistant"
        assert agent_wrapper.id == "python-agent"
        assert agent_wrapper.agent_type == "phidata"
        assert agent_wrapper._is_team is False
        
        # Verify PostgreSQL storage was initialized correctly
        mock_get_pg_agent_storage.assert_called_once_with(
            agent_id="python-agent",
            config={},  # Default empty dict if not specified
            table_name="python_agent_storage"
        )
        
        # Verify PGVector memory was initialized correctly
        mock_get_pgvector_memory.assert_called_once()
        
        # Verify Phidata Agent was initialized with correct parameters
        mock_agent_class.assert_called_once()
        call_kwargs = mock_agent_class.call_args[1]
        assert call_kwargs["name"] == "Python Code Assistant"
        assert call_kwargs["markdown"] is True
        assert call_kwargs["show_tool_calls"] is True
        assert call_kwargs["storage"] == mock_pg_agent_storage
        assert call_kwargs["memory"] == mock_pgvector_memory
        assert len(call_kwargs["instructions"]) > 0
        
        # Verify tools were initialized
        assert call_kwargs["tools"] is not None
        
        # Verify LLM was fetched correctly
        assert agent_wrapper._get_llm_from_ref("gpt_4_turbo") == mock_llm_client.gpt_4_turbo
    
    @patch("packages.phidata.src.cloudsql_pgvector.get_pg_agent_storage")
    @patch("packages.phidata.src.cloudsql_pgvector.get_pgvector_memory")
    @patch("importlib.import_module")
    async def test_python_agent_code_execution(
        self, 
        mock_import_module, 
        mock_get_pgvector_memory, 
        mock_get_pg_agent_storage,
        python_agent_config, 
        mock_memory_manager,
        mock_llm_client, 
        mock_tool_registry
    ):
        """Test the Python agent executing code."""
        # Setup agent module mock
        mock_agent_module = MagicMock()
        mock_agent_class = MagicMock()
        mock_agent_instance = MagicMock()
        mock_agent_module.Agent = mock_agent_class
        mock_agent_class.return_value = mock_agent_instance
        
        # Setup tool call mock that simulates code execution
        mock_tool_call = {
            "name": "python_executor",
            "input": {
                "code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n\nresult = fibonacci(10)\nprint(result)"
            },
            "output": {
                "result": "55",
                "stdout": "55\n",
                "stderr": "",
                "success": True
            }
        }
        
        # Setup response mock with tool calls
        mock_response = MagicMock()
        mock_response.content = """
        I've calculated the 10th Fibonacci number for you:
        
        ```python
        def fibonacci(n):
            if n <= 1:
                return n
            return fibonacci(n-1) + fibonacci(n-2)
        
        result = fibonacci(10)
        print(result)
        ```
        
        This recursive implementation gives us 55 as the 10th Fibonacci number.
        
        Note that this solution has exponential time complexity O(2^n). For larger values of n, 
        I would recommend using dynamic programming or memoization to optimize it.
        """
        mock_response.tool_calls = [mock_tool_call]
        mock_agent_instance.run = AsyncMock(return_value=mock_response)
        
        def mock_import_side_effect(name):
            if name == "agno.agent":
                return mock_agent_module
            return MagicMock()
            
        mock_import_module.side_effect = mock_import_side_effect
        
        # Initialize the agent wrapper
        agent_wrapper = PhidataAgentWrapper(
            agent_config=python_agent_config,
            memory_manager=mock_memory_manager,
            llm_client=mock_llm_client,
            tool_registry=mock_tool_registry
        )
        
        # Create test input
        test_input = AgentInput(
            request_id="test-request",
            prompt="Write a recursive function to calculate the 10th Fibonacci number",
            user_id="test-user",
            session_id="test-session"
        )
        
        # Run the agent
        output = await agent_wrapper.run(test_input)
        
        # Verify agent was called with correct parameters
        mock_agent_instance.run.assert_called_once()
        
        # Verify output
        assert isinstance(output, AgentOutput)
        assert "fibonacci" in output.content
        assert "55" in output.content
        assert "exponential time complexity" in output.content
        assert "tool_calls" in output.metadata
    
    @patch("packages.phidata.src.cloudsql_pgvector.get_pg_agent_storage")
    @patch("packages.phidata.src.cloudsql_pgvector.get_pgvector_memory")
    @patch("importlib.import_module")
    async def test_python_agent_code_debugging(
        self, 
        mock_import_module, 
        mock_get_pgvector_memory, 
        mock_get_pg_agent_storage,
        python_agent_config, 
        mock_memory_manager,
        mock_llm_client, 
        mock_tool_registry
    ):
        """Test the Python agent debugging erroneous code."""
        # Setup agent module mock
        mock_agent_module = MagicMock()
        mock_agent_class = MagicMock()
        mock_agent_instance = MagicMock()
        mock_agent_module.Agent = mock_agent_class
        mock_agent_class.return_value = mock_agent_instance
        
        # Setup tool call mocks that simulate debugging process
        # First execution with error
        error_tool_call = {
            "name": "python_executor",
            "input": {
                "code": "def calculate_average(numbers):\n    total = 0\n    for num in numbers:\n        total += num\n    return total / len(numbers)\n\ndata = [10, 20, 30, 40, None]\nresult = calculate_average(data)\nprint(result)"
            },
            "output": {
                "result": None,
                "stdout": "",
                "stderr": "TypeError: unsupported operand type(s) for +=: 'int' and 'NoneType'",
                "success": False
            }
        }
        
        # Fixed code execution
        fixed_tool_call = {
            "name": "python_executor",
            "input": {
                "code": "def calculate_average(numbers):\n    total = 0\n    count = 0\n    for num in numbers:\n        if num is not None:\n            total += num\n            count += 1\n    return total / count if count > 0 else 0\n\ndata = [10, 20, 30, 40, None]\nresult = calculate_average(data)\nprint(result)"
            },
            "output": {
                "result": "25.0",
                "stdout": "25.0\n",
                "stderr": "",
                "success": True
            }
        }
        
        # Setup response mock with both tool calls
        mock_response = MagicMock()
        mock_response.content = """
        I found and fixed the bug in your code. The issue was that your `data` list contains a `None` value, which can't be added to an integer.

        Here's the fixed code:

        ```python
        def calculate_average(numbers):
            total = 0
            count = 0
            for num in numbers:
                if num is not None:
                    total += num
                    count += 1
            return total / count if count > 0 else 0

        data = [10, 20, 30, 40, None]
        result = calculate_average(data)
        print(result)
        ```

        Changes made:
        1. Added a counter variable to track valid numbers
        2. Added a check to skip None values
        3. Used the count instead of len(numbers) for the average calculation
        4. Added error handling to avoid division by zero

        The result is 25.0, which is the average of [10, 20, 30, 40] (ignoring the None value).
        """
        mock_response.tool_calls = [error_tool_call, fixed_tool_call]
        mock_agent_instance.run = AsyncMock(return_value=mock_response)
        
        def mock_import_side_effect(name):
            if name == "agno.agent":
                return mock_agent_module
            return MagicMock()
            
        mock_import_module.side_effect = mock_import_side_effect
        
        # Initialize the agent wrapper
        agent_wrapper = PhidataAgentWrapper(
            agent_config=python_agent_config,
            memory_manager=mock_memory_manager,
            llm_client=mock_llm_client,
            tool_registry=mock_tool_registry
        )
        
        # Create test input
        test_input = AgentInput(
            request_id="test-request",
            prompt="Debug this code: def calculate_average(numbers):\n    total = 0\n    for num in numbers:\n        total += num\n    return total / len(numbers)\n\ndata = [10, 20, 30, 40, None]\nresult = calculate_average(data)\nprint(result)",
            user_id="test-user",
            session_id="test-session"
        )
        
        # Run the agent
        output = await agent_wrapper.run(test_input)
        
        # Verify output contains debugging information
        assert isinstance(output, AgentOutput)
        assert "None value" in output.content
        assert "fixed the bug" in output.content
        assert "25.0" in output.content
        assert "tool_calls" in output.metadata
        assert len(output.metadata["tool_calls"]) == 2  # Verify both tool calls are included
