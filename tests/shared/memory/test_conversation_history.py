"""
Tests for conversation history retrieval in MemoryManager.

This module contains tests specifically focusing on the conversation history
retrieval functionality of the MemoryManager, with an emphasis on user_id handling.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
import uuid
from unittest.mock import patch, MagicMock, AsyncMock

from packages.shared.src.memory.memory_manager import MemoryManager
from packages.shared.src.models.base_models import MemoryItem


@pytest.fixture
def memory_items():
    """Create a set of test memory items for different users."""
    # Create items for user1
    user1_items = [
        MemoryItem(
            id=str(uuid.uuid4()),
            user_id="user1",
            session_id="session1",
            timestamp=datetime.utcnow() - timedelta(minutes=30),
            item_type="conversation",
            persona_active="Cherry",
            text_content="Hello from user1 - older",
            metadata={"llm_response": "Hi user1, how can I help?"}
        ),
        MemoryItem(
            id=str(uuid.uuid4()),
            user_id="user1",
            session_id="session1",
            timestamp=datetime.utcnow() - timedelta(minutes=5),
            item_type="conversation",
            persona_active="Cherry",
            text_content="What's the weather?",
            metadata={"llm_response": "I don't have weather information."}
        )
    ]
    
    # Create items for user2
    user2_items = [
        MemoryItem(
            id=str(uuid.uuid4()),
            user_id="user2",
            session_id="session2",
            timestamp=datetime.utcnow() - timedelta(minutes=20),
            item_type="conversation",
            persona_active="Sophia",
            text_content="Hello from user2",
            metadata={"llm_response": "Greetings, user2."}
        )
    ]
    
    # Create items for patrick (default user)
    patrick_items = [
        MemoryItem(
            id=str(uuid.uuid4()),
            user_id="patrick",
            session_id="session_patrick",
            timestamp=datetime.utcnow() - timedelta(minutes=15),
            item_type="conversation",
            persona_active="Gordon Gekko",
            text_content="How can I be more efficient?",
            metadata={"llm_response": "Cut the small talk. Focus on results."}
        )
    ]
    
    return {"user1": user1_items, "user2": user2_items, "patrick": patrick_items}


@pytest.mark.critical
@pytest.mark.asyncio
async def test_get_conversation_history_multiple_users(memory_items):
    """Test retrieving conversation history for different users."""
    # Create a memory manager with mocked storage
    memory_manager = MemoryManager()
    
    # Mock the storage to return appropriate items based on user_id
    async def mock_get_items_by_user(user_id, **kwargs):
        if user_id in memory_items:
            return memory_items[user_id]
        return []
    
    # Patch the method that retrieves items
    with patch.object(memory_manager, '_get_items_by_user', side_effect=mock_get_items_by_user):
        # Test retrieving history for user1
        user1_history = await memory_manager.get_conversation_history(user_id="user1")
        assert len(user1_history) == 2
        assert all(item.user_id == "user1" for item in user1_history)
        
        # Test retrieving history for user2
        user2_history = await memory_manager.get_conversation_history(user_id="user2")
        assert len(user2_history) == 1
        assert user2_history[0].user_id == "user2"
        
        # Test retrieving history for default user (patrick)
        patrick_history = await memory_manager.get_conversation_history(user_id="patrick")
        assert len(patrick_history) == 1
        assert patrick_history[0].user_id == "patrick"
        
        # Test retrieving history for non-existent user
        empty_history = await memory_manager.get_conversation_history(user_id="nonexistent")
        assert len(empty_history) == 0


@pytest.mark.asyncio
async def test_get_conversation_history_limit(memory_items):
    """Test that conversation history respects the limit parameter."""
    # Create a memory manager with mocked storage
    memory_manager = MemoryManager()
    
    # Mock to return all user1 items
    with patch.object(memory_manager, '_get_items_by_user', 
                     return_value=memory_items["user1"]):
        # Test with default limit
        history = await memory_manager.get_conversation_history(user_id="user1")
        assert len(history) == 2
        
        # Test with limit=1
        limited_history = await memory_manager.get_conversation_history(user_id="user1", limit=1)
        assert len(limited_history) == 1
        
        # Verify we got the most recent item (higher timestamp)
        assert limited_history[0].text_content == "What's the weather?"


@pytest.mark.asyncio
async def test_add_memory_item_with_different_users():
    """Test adding memory items for different users."""
    # Create a memory manager
    memory_manager = MemoryManager()
    
    # Mock the _store_item method
    mock_store = AsyncMock()
    memory_manager._store_item = mock_store
    
    # Add items for different users
    test_users = ["user1", "user2", "patrick"]
    
    for user_id in test_users:
        test_item = MemoryItem(
            id=str(uuid.uuid4()),
            user_id=user_id,
            session_id=f"session_{user_id}",
            timestamp=datetime.utcnow(),
            item_type="conversation",
            persona_active="Cherry",
            text_content=f"Test message from {user_id}",
            metadata={"llm_response": f"Response to {user_id}"}
        )
        
        await memory_manager.add_memory_item(test_item)
        
        # Verify the store method was called with the correct item
        mock_store.assert_called()
        # Get the most recent call's arguments
        args, _ = mock_store.call_args
        stored_item = args[0]
        assert stored_item.user_id == user_id
        assert f"Test message from {user_id}" == stored_item.text_content
        
        # Reset the mock for the next iteration
        mock_store.reset_mock()
