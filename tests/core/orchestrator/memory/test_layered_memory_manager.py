"""
Tests for the LayeredMemoryManager class.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from google.cloud.firestore import DocumentSnapshot

from core.orchestrator.src.memory.layered_memory_manager import LayeredMemoryManager
from core.orchestrator.src.memory.models import MemoryEntry, MemoryType, MemorySearchResult


@pytest.fixture
def memory_manager():
    """Create a memory manager for testing."""
    manager = LayeredMemoryManager(
        agent_id="test-agent",
        conversation_id="test-conversation",
        redis_url="redis://localhost:6379",
        project_id="test-project",
        vector_index_endpoint="test-endpoint",
        vector_deployed_index_id="test-deployed-index",
    )
    return manager


@pytest.fixture
def sample_memory_entry():
    """Create a sample memory entry for testing."""
    return MemoryEntry(
        id="test-memory-id",
        agent_id="test-agent",
        conversation_id="test-conversation",
        content="This is a test memory",
        memory_type=MemoryType.SHORT_TERM,
        metadata={"source": "test", "importance": "high"},
        timestamp=datetime.utcnow().isoformat(),
        embedding=[0.1, 0.2, 0.3, 0.4],
    )


@pytest.mark.asyncio
async def test_connect(memory_manager):
    """Test connecting to Redis and initializing Vector Search."""
    with patch("aioredis.from_url", return_value=AsyncMock()) as mock_redis, \
         patch("google.cloud.aiplatform.init") as mock_aiplatform_init:
        
        await memory_manager.connect()
        
        # Check that Redis was initialized
        mock_redis.assert_called_once_with(
            "redis://localhost:6379", decode_responses=True
        )
        
        # Check that Vector Search was initialized
        mock_aiplatform_init.assert_called_once_with(
            project="test-project", location=memory_manager.region
        )
        
        assert memory_manager.vector_search_initialized is True


@pytest.mark.asyncio
async def test_disconnect(memory_manager):
    """Test disconnecting from Redis."""
    memory_manager.redis_pool = AsyncMock()
    
    await memory_manager.disconnect()
    
    # Check that Redis connection was closed
    memory_manager.redis_pool.close.assert_called_once()


@pytest.mark.asyncio
async def test_store_memory_short_term(memory_manager, sample_memory_entry):
    """Test storing a memory in the short-term storage (Redis)."""
    memory_manager.redis_pool = AsyncMock()
    
    with patch("uuid.uuid4", return_value=uuid.UUID("12345678-1234-5678-1234-567812345678")):
        memory_id = await memory_manager.store_memory(
            content=sample_memory_entry.content,
            memory_type=MemoryType.SHORT_TERM,
            metadata=sample_memory_entry.metadata,
        )
    
    # Check that the memory was stored in Redis
    assert memory_manager.redis_pool.set.called
    assert memory_manager.redis_pool.sadd.called
    assert memory_id == "12345678-1234-5678-1234-567812345678"


@pytest.mark.asyncio
async def test_store_memory_mid_term(memory_manager, sample_memory_entry):
    """Test storing a memory in the mid-term storage (Firestore)."""
    memory_manager.firestore_client = MagicMock()
    collection_mock = MagicMock()
    document_mock = MagicMock()
    memory_manager.firestore_client.collection.return_value = collection_mock
    collection_mock.document.return_value = document_mock
    
    with patch("uuid.uuid4", return_value=uuid.UUID("12345678-1234-5678-1234-567812345678")):
        memory_id = await memory_manager.store_memory(
            content=sample_memory_entry.content,
            memory_type=MemoryType.MID_TERM,
            metadata=sample_memory_entry.metadata,
        )
    
    # Check that the memory was stored in Firestore
    memory_manager.firestore_client.collection.assert_called_once_with("memories")
    collection_mock.document.assert_called_once()
    document_mock.set.assert_called_once()
    assert memory_id == "12345678-1234-5678-1234-567812345678"


@pytest.mark.asyncio
async def test_store_memory_long_term(memory_manager, sample_memory_entry):
    """Test storing a memory in the long-term storage (Firestore + Vector Search)."""
    memory_manager.firestore_client = MagicMock()
    collection_mock = MagicMock()
    document_mock = MagicMock()
    memory_manager.firestore_client.collection.return_value = collection_mock
    collection_mock.document.return_value = document_mock
    memory_manager.vector_search_initialized = True
    
    with patch("uuid.uuid4", return_value=uuid.UUID("12345678-1234-5678-1234-567812345678")), \
         patch.object(memory_manager, "_store_in_vector_search", AsyncMock()) as mock_vector_store:
        
        memory_id = await memory_manager.store_memory(
            content=sample_memory_entry.content,
            memory_type=MemoryType.LONG_TERM,
            metadata=sample_memory_entry.metadata,
            embedding=sample_memory_entry.embedding,
        )
    
    # Check that the memory was stored in Firestore and Vector Search
    memory_manager.firestore_client.collection.assert_called_once_with("memories")
    collection_mock.document.assert_called_once()
    document_mock.set.assert_called_once()
    mock_vector_store.assert_called_once()
    assert memory_id == "12345678-1234-5678-1234-567812345678"


@pytest.mark.asyncio
async def test_store_memory_long_term_no_embedding(memory_manager):
    """Test that storing a long-term memory without an embedding raises an error."""
    with pytest.raises(ValueError, match="Embedding is required for LONG_TERM memory"):
        await memory_manager.store_memory(
            content="Test memory",
            memory_type=MemoryType.LONG_TERM,
            metadata={"source": "test"},
        )


@pytest.mark.asyncio
async def test_retrieve_memory_from_redis(memory_manager, sample_memory_entry):
    """Test retrieving a memory from Redis."""
    memory_manager.redis_pool = AsyncMock()
    memory_manager.redis_pool.get.return_value = sample_memory_entry.model_dump_json()
    
    memory = await memory_manager.retrieve_memory(sample_memory_entry.id)
    
    # Check that the memory was retrieved from Redis
    memory_manager.redis_pool.get.assert_called_once_with(f"memory:{sample_memory_entry.id}")
    assert memory.id == sample_memory_entry.id
    assert memory.content == sample_memory_entry.content


@pytest.mark.asyncio
async def test_retrieve_memory_from_firestore(memory_manager, sample_memory_entry):
    """Test retrieving a memory from Firestore when not found in Redis."""
    # Redis returns None
    memory_manager.redis_pool = AsyncMock()
    memory_manager.redis_pool.get.return_value = None
    
    # Firestore returns the memory
    memory_manager.firestore_client = MagicMock()
    collection_mock = MagicMock()
    document_mock = MagicMock()
    doc_snapshot = MagicMock(spec=DocumentSnapshot)
    doc_snapshot.exists = True
    doc_snapshot.to_dict.return_value = sample_memory_entry.model_dump(exclude={"embedding"})
    
    memory_manager.firestore_client.collection.return_value = collection_mock
    collection_mock.document.return_value = document_mock
    document_mock.get.return_value = doc_snapshot
    
    memory = await memory_manager.retrieve_memory(sample_memory_entry.id)
    
    # Check that the memory was retrieved from Firestore
    memory_manager.redis_pool.get.assert_called_once_with(f"memory:{sample_memory_entry.id}")
    memory_manager.firestore_client.collection.assert_called_once_with("memories")
    collection_mock.document.assert_called_once_with(sample_memory_entry.id)
    document_mock.get.assert_called_once()
    assert memory.id == sample_memory_entry.id
    assert memory.content == sample_memory_entry.content


@pytest.mark.asyncio
async def test_retrieve_memory_not_found(memory_manager):
    """Test retrieving a memory that doesn't exist."""
    # Redis returns None
    memory_manager.redis_pool = AsyncMock()
    memory_manager.redis_pool.get.return_value = None
    
    # Firestore returns None
    memory_manager.firestore_client = MagicMock()
    collection_mock = MagicMock()
    document_mock = MagicMock()
    doc_snapshot = MagicMock(spec=DocumentSnapshot)
    doc_snapshot.exists = False
    
    memory_manager.firestore_client.collection.return_value = collection_mock
    collection_mock.document.return_value = document_mock
    document_mock.get.return_value = doc_snapshot
    
    memory = await memory_manager.retrieve_memory("non-existent-id")
    
    # Check that both Redis and Firestore were queried
    memory_manager.redis_pool.get.assert_called_once_with("memory:non-existent-id")
    memory_manager.firestore_client.collection.assert_called_once_with("memories")
    collection_mock.document.assert_called_once_with("non-existent-id")
    document_mock.get.assert_called_once()
    assert memory is None


@pytest.mark.asyncio
async def test_search_memory(memory_manager, sample_memory_entry):
    """Test searching for memories across all storage layers."""
    # Mock Redis search
    redis_result = MemorySearchResult(
        memory=sample_memory_entry,
        relevance=0.8,
    )
    memory_manager._search_in_redis = AsyncMock(return_value=[redis_result])
    
    # Mock Firestore search
    firestore_result = MemorySearchResult(
        memory=sample_memory_entry,
        relevance=0.6,
    )
    memory_manager._search_in_firestore = MagicMock(return_value=[firestore_result])
    
    # Mock Vector Search
    vector_result = MemorySearchResult(
        memory=sample_memory_entry,
        relevance=0.9,
    )
    memory_manager._search_in_vector_search = AsyncMock(return_value=[vector_result])
    memory_manager.vector_search_initialized = True
    
    results = await memory_manager.search_memory(
        query="test",
        embedding=[0.1, 0.2, 0.3, 0.4],
        limit=5,
        metadata_filter={"source": "test"},
    )
    
    # Check that all storage layers were searched
    memory_manager._search_in_redis.assert_called_once()
    memory_manager._search_in_firestore.assert_called()
    memory_manager._search_in_vector_search.assert_called_once()
    
    # Check that results are sorted by relevance
    assert len(results) == 3
    assert results[0].relevance == 0.9  # Vector Search result
    assert results[1].relevance == 0.8  # Redis result
    assert results[2].relevance == 0.6  # Firestore result


@pytest.mark.asyncio
async def test_delete_memory(memory_manager):
    """Test deleting a memory from all storage layers."""
    memory_manager.redis_pool = AsyncMock()
    memory_manager.redis_pool.exists.return_value = True
    memory_manager.firestore_client = MagicMock()
    memory_manager.vector_search_initialized = True
    memory_manager._delete_from_vector_search = AsyncMock(return_value=True)
    
    collection_mock = MagicMock()
    document_mock = MagicMock()
    doc_snapshot = MagicMock(spec=DocumentSnapshot)
    doc_snapshot.exists = True
    
    memory_manager.firestore_client.collection.return_value = collection_mock
    collection_mock.document.return_value = document_mock
    document_mock.get.return_value = doc_snapshot
    
    result = await memory_manager.delete_memory("test-memory-id")
    
    # Check that the memory was deleted from all storage layers
    memory_manager.redis_pool.delete.assert_called_once()
    memory_manager.redis_pool.srem.assert_called()
    document_mock.delete.assert_called_once()
    memory_manager._delete_from_vector_search.assert_called_once_with("test-memory-id")
    assert result is True


@pytest.mark.asyncio
async def test_calculate_text_relevance():
    """Test the text relevance calculation function."""
    memory_manager = LayeredMemoryManager(agent_id="test-agent")
    
    # Exact match
    assert memory_manager._calculate_text_relevance("test", "test") == 1.0
    
    # Contained match
    assert memory_manager._calculate_text_relevance("test", "this is a test") < 1.0
    assert memory_manager._calculate_text_relevance("test", "this is a test") > 0.0
    
    # Word overlap
    assert memory_manager._calculate_text_relevance("red car", "blue car") > 0.0
    assert memory_manager._calculate_text_relevance("red car", "blue car") < 1.0
    
    # No match
    assert memory_manager._calculate_text_relevance("apple", "banana") == 0.0