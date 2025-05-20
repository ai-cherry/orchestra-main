#!/usr/bin/env python3
"""
Pytest configuration for MCP server tests.

This module provides fixtures for testing the MCP server components.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from mcp_server.storage.memory_store import MemoryStore
from mcp_server.tools.tool_manager import ToolManager
from mcp_server.workflows.workflow_manager import WorkflowManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def memory_config(temp_dir):
    """Create a memory store configuration for testing."""
    return {
        "storage_path": str(temp_dir),
        "ttl_seconds": 3600,
        "max_items_per_key": 100,
        "enable_compression": True,
    }


@pytest.fixture
def memory_store(memory_config):
    """Create a memory store instance for testing."""
    return MemoryStore(memory_config)


@pytest.fixture
def tool_config():
    """Create a tool manager configuration for testing."""
    return {
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
    return MagicMock()


@pytest.fixture
def tool_manager(tool_config, mock_memory_store):
    """Create a tool manager instance for testing."""
    return ToolManager(tool_config, mock_memory_store)


@pytest.fixture
def mock_tool_manager():
    """Create a mock tool manager for testing."""
    mock = MagicMock()
    mock.get_enabled_tools.return_value = ["roo", "gemini"]
    return mock


@pytest.fixture
def workflow_manager(mock_tool_manager, mock_memory_store):
    """Create a workflow manager instance for testing."""
    # We need to patch the Path class to use a temporary directory for workflows
    # This is done in the individual test files
    return WorkflowManager(mock_tool_manager, mock_memory_store)


@pytest.fixture
def test_workflow():
    """Create a test workflow for testing."""
    return {
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
    return {
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
