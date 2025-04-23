"""
Pytest configuration and fixtures for the AI Orchestration System.

This module provides reusable fixtures for testing the system.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
import asyncio
from typing import Dict, List, Any, AsyncGenerator

# For mocking LLM clients
@pytest.fixture
def mock_llm_client():
    """
    Create a mock LLM client for testing.
    
    Returns a mock that can be used to simulate LLM responses.
    """
    client = AsyncMock()
    
    # Setup generate_chat_completion method
    async def mock_generate_chat_completion(*args, **kwargs):
        return {
            "content": "Mocked response",
            "model": "test-model",
            "provider": "test-provider",
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            },
            "finish_reason": "stop",
            "response_time_ms": 100
        }
    
    client.generate_chat_completion = mock_generate_chat_completion
    client.generate_response = AsyncMock(return_value="Mocked response")
    
    return client


@pytest.fixture
def mock_memory_manager():
    """
    Create a mock memory manager for testing.
    
    Returns a mock that can be used to simulate memory operations.
    """
    manager = AsyncMock()
    
    # Setup get_conversation_history method
    async def mock_get_conversation_history(user_id=None, limit=10):
        return []
    
    # Setup add_memory_item method
    async def mock_add_memory_item(memory_item):
        return "mocked-memory-id"
    
    manager.get_conversation_history = mock_get_conversation_history
    manager.add_memory_item = mock_add_memory_item
    
    return manager


@pytest.fixture
def mock_persona_manager():
    """
    Create a mock persona manager for testing.
    
    Returns a mock that can be used to simulate persona operations.
    """
    manager = MagicMock()
    
    # Setup persona configurations
    personas = {
        "cherry": {
            "id": "cherry",
            "name": "Cherry",
            "description": "A cheerful assistant",
            "prompt_template": "Respond cheerfully: {input}"
        },
        "sophia": {
            "id": "sophia",
            "name": "Sophia",
            "description": "A wise assistant",
            "prompt_template": "Respond wisely: {input}"
        },
        "gordon_gekko": {
            "id": "gordon_gekko",
            "name": "Gordon Gekko",
            "description": "Ruthless Efficiency Expert",
            "prompt_template": "Respond bluntly: {input}"
        }
    }
    
    # Setup methods
    manager.get_persona_config.side_effect = lambda persona_id: personas.get(persona_id)
    manager.get_default_persona_id.return_value = "cherry"
    manager.list_personas.return_value = [
        {"id": k, "name": v["name"], "description": v["description"]}
        for k, v in personas.items()
    ]
    
    return manager
