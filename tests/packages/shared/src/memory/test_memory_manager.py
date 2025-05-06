import pytest
from unittest.mock import MagicMock, call

from packages.shared.src.memory.memory_manager import MemoryManager


def test_add_message_to_conversation():
    mock_firestore_memory = MagicMock()
    memory_manager = MemoryManager()
    memory_manager.firestore_memory = mock_firestore_memory
    conversation_id = "test_conversation"
    message = {"role": "user", "content": "test message"}
    memory_manager.add_message_to_conversation(conversation_id, message)
    mock_firestore_memory.add_message_to_conversation.assert_called_once_with(conversation_id, message)