#!/usr/bin/env python3
"""
"""
    """Create a temporary directory for testing."""
    """Create a memory store configuration for testing."""
        "storage_path": str(temp_dir),
        "ttl_seconds": 3600,
        "max_items_per_key": 100,
        "enable_compression": True,
    }

@pytest.fixture
def memory_store(memory_config):
    """Create a memory store instance for testing."""
    """Create a tool manager configuration for testing."""
        "roo": {
            "enabled": True,
            "api_endpoint": "http://localhost:8081",
        },
        "cline": {
            "enabled": False,
            "api_endpoint": "http://localhost:8082",
        },
        "gemini": {
            "enabled": True,
            "api_key_env": "GEMINI_API_KEY",
        },
        "copilot": {
            "enabled": False,
        },
    }

@pytest.fixture
def mock_memory_store():
    """Create a mock memory store for testing."""
    """Create a tool manager instance for testing."""
    """Create a mock tool manager for testing."""
    mock.get_enabled_tools.return_value = ["roo", "gemini"]
    return mock

@pytest.fixture
def workflow_manager(mock_tool_manager, mock_memory_store):
    """Create a workflow manager instance for testing."""
    """Create a test workflow for testing."""
        "workflow_id": "test_workflow",
        "description": "A test workflow",
        "target_tools": ["roo"],
        "steps": [
            {
                "type": "mode",
                "mode": "code",
                "task": "Write a function to add two numbers",
            }
        ],
    }

@pytest.fixture
def test_workflow_with_params():
    """Create a test workflow with parameters for testing."""
        "workflow_id": "param_workflow",
        "description": "A workflow with parameters",
        "target_tools": ["roo", "gemini"],
        "steps": [
            {
                "type": "mode",
                "mode": "code",
                "task": "Write a function to {action} {count} {items}",
            },
            {"type": "mode", "mode": "ask", "task": "Explain the function"},
        ],
    }
