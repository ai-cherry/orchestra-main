"""
Memory manager fixtures for testing.

This module provides pytest fixtures for mocking memory manager
functionality in tests.
"""

from unittest.mock import AsyncMock

import pytest

from packages.shared.src.memory.memory_manager import MemoryManager


@pytest.fixture
def mock_memory_manager():
    """
    Create a mock memory manager for testing.

    Returns:
        An AsyncMock instance that implements the MemoryManager interface
    """
    # Create AsyncMock for memory manager
    memory_manager = AsyncMock(spec=MemoryManager)

    # Mock get_conversation_history to return empty list
    memory_manager.get_conversation_history.return_value = []

    # Set up required abstract methods from MemoryManager
    memory_manager.initialize = AsyncMock(return_value=None)
    memory_manager.close = AsyncMock(return_value=None)
    memory_manager.add_memory_item = AsyncMock(return_value="mock-memory-item-id-12345")
    memory_manager.get_memory_item = AsyncMock(return_value=None)
    memory_manager.semantic_search = AsyncMock(return_value=[])
    memory_manager.add_raw_agent_data = AsyncMock(return_value="mock-agent-data-id-12345")
    memory_manager.check_duplicate = AsyncMock(return_value=False)
    memory_manager.cleanup_expired_items = AsyncMock(return_value=0)
    memory_manager.health_check = AsyncMock(return_value={"status": "healthy"})

    # Return mock memory manager
    return memory_manager


# Add module-level mock for patching
mock_memory_manager_instance = AsyncMock(spec=MemoryManager)
mock_memory_manager_instance.get_conversation_history.return_value = []
# Set up required abstract methods from MemoryManager
mock_memory_manager_instance.initialize = AsyncMock(return_value=None)
mock_memory_manager_instance.close = AsyncMock(return_value=None)
mock_memory_manager_instance.add_memory_item = AsyncMock(return_value="mock-memory-item-id-67890")
mock_memory_manager_instance.get_memory_item = AsyncMock(return_value=None)
mock_memory_manager_instance.semantic_search = AsyncMock(return_value=[])
mock_memory_manager_instance.add_raw_agent_data = AsyncMock(return_value="mock-agent-data-id-67890")
mock_memory_manager_instance.check_duplicate = AsyncMock(return_value=False)
mock_memory_manager_instance.cleanup_expired_items = AsyncMock(return_value=0)
mock_memory_manager_instance.health_check = AsyncMock(return_value={"status": "healthy"})


def get_memory_manager_stub():
    """
    Get a memory manager stub for tests.

    This function is used in tests to provide a consistent mock memory manager
    that can be patched in place of the real get_memory_manager function.

    Returns:
        A mocked memory manager instance
    """
    return mock_memory_manager_instance
