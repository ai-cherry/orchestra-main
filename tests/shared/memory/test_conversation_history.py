"""
Tests for conversation history retrieval in MemoryManager.

This module contains tests specifically focusing on the conversation history
retrieval functionality of the MemoryManager, with an emphasis on user_id handling.
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
import uuid
from unittest.mock import AsyncMock
from packages.shared.src.memory.stubs import InMemoryMemoryManagerStub
from packages.shared.src.models.base_models import MemoryItem


@pytest_asyncio.fixture
async def memory_manager():
    manager = InMemoryMemoryManagerStub()
    await manager.initialize()
    yield manager
    await manager.close()


@pytest.mark.critical
@pytest.mark.asyncio
async def test_get_conversation_history_multiple_users(memory_manager):
    """Test retrieving conversation history for different users."""
    # Use the provided memory_manager fixture
    await memory_manager.add_memory_item(MemoryItem(
        user_id="user1",
        item_type="message",
        text_content="Hello from user1"
    ))
    await memory_manager.add_memory_item(MemoryItem(
        user_id="user2", 
        item_type="message",
        text_content="Hello from user2"
    ))

    history_user1 = await memory_manager.get_conversation_history(user_id="user1")
    history_user2 = await memory_manager.get_conversation_history(user_id="user2")

    assert len(history_user1) == 1
    assert len(history_user2) == 1
    assert history_user1[0].text_content == "Hello from user1"
    assert history_user2[0].text_content == "Hello from user2"


@pytest.mark.asyncio
async def test_get_conversation_history_limit(memory_manager):
    """Test that conversation history respects the limit parameter."""
    # Create messages with timestamps that increase as we go
    # This ensures that higher numbers are more recent
    for i in range(10):
        await memory_manager.add_memory_item(MemoryItem(
            user_id="user1", 
            item_type="message",
            text_content=f"Message {i}",
            timestamp=datetime.utcnow() + timedelta(minutes=i)  # Make later messages have later timestamps
        ))

    history = await memory_manager.get_conversation_history(user_id="user1", limit=5)

    assert len(history) == 5
    # The most recent messages (9, 8, 7, 6, 5) should be returned in reverse chronological order
    assert history[0].text_content == "Message 9"
    assert history[-1].text_content == "Message 5"


@pytest.mark.asyncio
async def test_add_memory_item_with_different_users(memory_manager):
    """Test adding memory items for different users."""
    await memory_manager.add_memory_item(MemoryItem(
        user_id="user1", 
        item_type="message",
        text_content="Hello from user1"
    ))
    await memory_manager.add_memory_item(MemoryItem(
        user_id="user2", 
        item_type="message",
        text_content="Hello from user2"
    ))

    history_user1 = await memory_manager.get_conversation_history(user_id="user1")
    history_user2 = await memory_manager.get_conversation_history(user_id="user2")

    assert len(history_user1) == 1
    assert len(history_user2) == 1
    assert history_user1[0].text_content == "Hello from user1"
    assert history_user2[0].text_content == "Hello from user2"
