"""
Tests for the ConversationService.

This module contains tests for the ConversationService class, which handles
conversation state management, history retrieval, and lifecycle operations.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from core.orchestrator.src.services.conversation_service import (
    ConversationService,
    ConversationState,
    get_conversation_service,
)
from packages.shared.src.models.base_models import MemoryItem


@pytest.fixture
def mock_memory_manager():
    """Create a mock memory manager with async methods."""
    mock = AsyncMock()
    # Setup default return values
    mock.add_memory_item.return_value = "test-memory-id"
    mock.get_conversation_history.return_value = []
    return mock


@pytest.fixture
def mock_event_bus():
    """Create a mock event bus with async methods."""
    mock = AsyncMock()
    mock.publish_async.return_value = 1  # Number of handlers notified
    return mock


@pytest.fixture
def conversation_service(mock_memory_manager, mock_event_bus):
    """Create a conversation service with mocked dependencies."""
    with (
        patch('core.orchestrator.src.services.conversation_service.get_memory_manager', 
              return_value=mock_memory_manager),
        patch('core.orchestrator.src.services.conversation_service.get_event_bus', 
              return_value=mock_event_bus)
    ):
        service = ConversationService()
        yield service


@pytest.mark.asyncio
async def test_start_conversation(conversation_service, mock_memory_manager, mock_event_bus):
    """Test starting a conversation."""
    # Arrange
    user_id = "test-user"
    persona_name = "test-persona"
    
    # Act
    session_id = await conversation_service.start_conversation(user_id, persona_name)
    
    # Assert
    assert isinstance(session_id, str)
    assert len(session_id) > 0
    
    # Verify memory item was created with correct data
    mock_memory_manager.add_memory_item.assert_called_once()
    memory_item_arg = mock_memory_manager.add_memory_item.call_args[0][0]
    assert isinstance(memory_item_arg, MemoryItem)
    assert memory_item_arg.user_id == user_id
    assert memory_item_arg.item_type == "conversation_event"
    assert memory_item_arg.content["event_type"] == "conversation_started"
    assert memory_item_arg.content["persona_name"] == persona_name
    assert memory_item_arg.content["session_id"] == session_id
    
    # Verify event was published with correct data
    mock_event_bus.publish_async.assert_called_once()
    event_type_arg = mock_event_bus.publish_async.call_args[0][0]
    event_data_arg = mock_event_bus.publish_async.call_args[0][1]
    assert event_type_arg == "conversation_started"
    assert event_data_arg["user_id"] == user_id
    assert event_data_arg["session_id"] == session_id
    assert event_data_arg["persona_name"] == persona_name
    
    # Verify conversation state is tracked
    assert user_id in conversation_service._active_conversations
    conversation_state = conversation_service._active_conversations[user_id]
    assert conversation_state.user_id == user_id
    assert conversation_state.session_id == session_id
    assert conversation_state.persona_active == persona_name
    assert conversation_state.turn_count == 0


@pytest.mark.asyncio
async def test_end_conversation(conversation_service, mock_memory_manager, mock_event_bus):
    """Test ending a conversation."""
    # Arrange - Setup an active conversation
    user_id = "test-user"
    session_id = await conversation_service.start_conversation(user_id, "test-persona")
    
    # Reset mocks after start_conversation
    mock_memory_manager.reset_mock()
    mock_event_bus.reset_mock()
    
    # Act
    result = await conversation_service.end_conversation(user_id, session_id)
    
    # Assert
    assert result is True
    
    # Verify memory item was created with correct data
    mock_memory_manager.add_memory_item.assert_called_once()
    memory_item_arg = mock_memory_manager.add_memory_item.call_args[0][0]
    assert memory_item_arg.item_type == "conversation_event"
    assert memory_item_arg.content["event_type"] == "conversation_ended"
    assert memory_item_arg.content["session_id"] == session_id
    
    # Verify event was published
    mock_event_bus.publish_async.assert_called_once()
    event_type_arg = mock_event_bus.publish_async.call_args[0][0]
    assert event_type_arg == "conversation_ended"
    
    # Verify conversation is no longer tracked
    assert user_id not in conversation_service._active_conversations


@pytest.mark.asyncio
async def test_end_conversation_nonexistent(conversation_service, mock_memory_manager):
    """Test ending a conversation that doesn't exist."""
    # Act
    result = await conversation_service.end_conversation("nonexistent-user", "nonexistent-session")
    
    # Assert
    assert result is False
    mock_memory_manager.add_memory_item.assert_not_called()


@pytest.mark.asyncio
async def test_record_message(conversation_service, mock_memory_manager, mock_event_bus):
    """Test recording a message in a conversation."""
    # Arrange - Setup an active conversation
    user_id = "test-user"
    session_id = await conversation_service.start_conversation(user_id, "test-persona")
    
    # Reset mocks after start_conversation
    mock_memory_manager.reset_mock()
    mock_event_bus.reset_mock()
    
    # Act
    message_content = "Hello, world!"
    is_user = True
    metadata = {"key": "value"}
    message_id = await conversation_service.record_message(
        user_id=user_id,
        content=message_content,
        is_user=is_user,
        metadata=metadata,
    )
    
    # Assert
    assert message_id == "test-memory-id"
    
    # Verify memory item was created with correct data
    mock_memory_manager.add_memory_item.assert_called_once()
    memory_item_arg = mock_memory_manager.add_memory_item.call_args[0][0]
    assert memory_item_arg.item_type == "conversation_message"
    assert memory_item_arg.content["message"] == message_content
    assert memory_item_arg.content["is_user"] == is_user
    assert memory_item_arg.content["session_id"] == session_id
    assert memory_item_arg.content["metadata"] == metadata
    assert memory_item_arg.content["persona_name"] == "test-persona"
    
    # Verify event was published
    mock_event_bus.publish_async.assert_called_once()
    event_type_arg = mock_event_bus.publish_async.call_args[0][0]
    event_data_arg = mock_event_bus.publish_async.call_args[0][1]
    assert event_type_arg == "conversation_message_added"
    assert event_data_arg["message_id"] == "test-memory-id"
    assert event_data_arg["is_user"] == is_user
    
    # Verify turn count is incremented for user messages
    conversation_state = conversation_service._active_conversations[user_id]
    assert conversation_state.turn_count == 1


@pytest.mark.asyncio
async def test_record_message_system(conversation_service, mock_memory_manager):
    """Test recording a system message in a conversation."""
    # Arrange - Setup an active conversation
    user_id = "test-user"
    session_id = await conversation_service.start_conversation(user_id, "test-persona")
    
    # Reset mocks after start_conversation
    mock_memory_manager.reset_mock()
    
    # Act
    await conversation_service.record_message(
        user_id=user_id,
        content="System message",
        is_user=False,
    )
    
    # Verify turn count is not incremented for system messages
    conversation_state = conversation_service._active_conversations[user_id]
    assert conversation_state.turn_count == 0


@pytest.mark.asyncio
async def test_get_conversation_history(conversation_service, mock_memory_manager):
    """Test retrieving conversation history."""
    # Arrange
    user_id = "test-user"
    session_id = "test-session"
    limit = 10
    persona_name = "test-persona"
    
    # Create mock memory items to return
    mock_item1 = MagicMock()
    mock_item1.id = "msg-1"
    mock_item1.item_type = "conversation_message"
    mock_item1.content = {
        "message": "User message",
        "is_user": True,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    mock_item2 = MagicMock()
    mock_item2.id = "msg-2"
    mock_item2.item_type = "conversation_message"
    mock_item2.content = {
        "message": "Assistant response",
        "is_user": False,
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": {"source": "llm"},
    }
    
    mock_memory_manager.get_conversation_history.return_value = [mock_item1, mock_item2]
    
    # Act
    history = await conversation_service.get_conversation_history(
        user_id=user_id,
        session_id=session_id,
        limit=limit,
        persona_name=persona_name,
    )
    
    # Assert
    assert len(history) == 2
    
    # Verify memory manager was called with correct parameters
    mock_memory_manager.get_conversation_history.assert_called_once()
    call_args = mock_memory_manager.get_conversation_history.call_args
    assert call_args[1]["user_id"] == user_id
    assert call_args[1]["session_id"] == session_id
    assert call_args[1]["limit"] == limit
    assert call_args[1]["filters"] == {"persona_name": persona_name}
    
    # Verify history is properly formatted
    assert history[0]["id"] == "msg-1"
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "User message"
    
    assert history[1]["id"] == "msg-2"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "Assistant response"
    assert history[1]["metadata"] == {"source": "llm"}


@pytest.mark.asyncio
async def test_add_memory_item_async(conversation_service, mock_memory_manager):
    """Test adding a memory item asynchronously."""
    # Arrange
    test_item = MemoryItem(
        user_id="test-user",
        item_type="test_item",
        content={"test": "data"}
    )
    mock_memory_manager.add_memory_item.return_value = "test-async-id"
    
    # Act
    result = await conversation_service.add_memory_item_async(test_item)
    
    # Assert
    assert result == "test-async-id"
    mock_memory_manager.add_memory_item.assert_called_once_with(test_item)


def test_get_active_conversation(conversation_service):
    """Test getting the active conversation state."""
    # Arrange - Create a conversation state manually
    user_id = "test-user"
    session_id = "test-session"
    conversation_state = ConversationState(
        user_id=user_id,
        session_id=session_id,
        persona_active="test-persona",
    )
    conversation_service._active_conversations[user_id] = conversation_state
    
    # Act
    result = conversation_service.get_active_conversation(user_id)
    
    # Assert
    assert result is conversation_state
    assert result.user_id == user_id
    assert result.session_id == session_id
    
    # Test nonexistent user
    assert conversation_service.get_active_conversation("nonexistent-user") is None


def test_get_conversation_service_singleton():
    """Test that get_conversation_service returns a singleton instance."""
    # Act
    service1 = get_conversation_service()
    service2 = get_conversation_service()
    
    # Assert
    assert service1 is service2
    assert isinstance(service1, ConversationService)