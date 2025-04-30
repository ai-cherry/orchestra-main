import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio
from datetime import datetime, timedelta

from packages.shared.src.memory.concrete_memory_manager import FirestoreV1MemoryManager
from packages.shared.src.models.base_models import MemoryItem, AgentData, PersonaConfig
from packages.shared.src.storage.exceptions import StorageError, ValidationError
from packages.shared.src.storage.redis.redis_client import RedisError
from packages.shared.src.storage.firestore.firestore_memory import FirestoreMemoryManager
from packages.shared.src.storage.redis.redis_client import RedisClient


# Mock the dependencies
@pytest.fixture
def mock_firestore_memory_manager():
    """Fixture for a mocked FirestoreMemoryManager."""
    mock = AsyncMock(spec=FirestoreMemoryManager)
    # Configure default return values for common methods
    mock.add_memory_item.return_value = "mock_item_id"
    mock.get_memory_item.return_value = None # Default to not found
    mock.get_conversation_history.return_value = []
    mock.semantic_search.return_value = []
    mock.add_raw_agent_data.return_value = "mock_agent_data_id"
    mock.check_duplicate.return_value = False
    mock.cleanup_expired_items.return_value = 0
    # Mock the health_check method to return a simple healthy status
    mock.health_check.return_value = {"status": "healthy", "connection": True}
    return mock

@pytest.fixture
def mock_redis_client():
    """Fixture for a mocked RedisClient."""
    mock = AsyncMock(spec=RedisClient)
    # Configure default return values for common methods
    mock.initialize.return_value = None
    mock.close.return_value = None
    mock.set.return_value = True
    mock.get.return_value = None # Default to cache miss
    mock.delete.return_value = True
    mock.exists.return_value = False
    mock.set_hash.return_value = True
    mock.get_hash.return_value = {}
    mock.set_list.return_value = True
    mock.get_list.return_value = []
    mock.flush_namespace.return_value = True
    mock.cache_conversation_history.return_value = True
    mock.get_cached_conversation_history.return_value = []
    mock.invalidate_conversation_history.return_value = True
    mock.cache_session_data.return_value = True
    mock.get_cached_session_data.return_value = {}
    mock.invalidate_session_data.return_value = True
    mock.ping.return_value = True
    return mock

@pytest.fixture
def firestore_v1_memory_manager(mock_firestore_memory_manager, mock_redis_client):
    """Fixture for FirestoreV1MemoryManager with mocked dependencies."""
    # Instantiate FirestoreV1MemoryManager with injected mocks
    manager = FirestoreV1MemoryManager(
        firestore_memory=mock_firestore_memory_manager,
        redis_host="mock_redis_host",
        redis_port=6379,
        redis_password="mock_password",
        cache_ttl=3600
    )
    # Simulate successful initialization for most tests
    manager._initialized = True
    manager._redis_available = True
    yield manager

@pytest.fixture
def uninitialized_firestore_v1_memory_manager(mock_firestore_memory_manager, mock_redis_client):
    """Fixture for an uninitialized FirestoreV1MemoryManager with mocked dependencies."""
    manager = FirestoreV1MemoryManager(
        firestore_memory=mock_firestore_memory_manager,
        redis_host="mock_redis_host",
        redis_port=6379,
        redis_password="mock_password",
        cache_ttl=3600
    )
    manager._initialized = False
    manager._redis_available = False
    yield manager


# Helper function to run async tests
def async_test(coro):
    def wrapper(*args, **kwargs):
        return asyncio.run(coro(*args, **kwargs))
    return wrapper

# --- Test Cases ---

@async_test
async def test_initialize_success(mock_firestore_memory_manager, mock_redis_client):
    """Test successful initialization."""
    # Need a fresh instance that is not pre-initialized by the fixture
    manager = FirestoreV1MemoryManager(
        firestore_memory=mock_firestore_memory_manager,
        redis_host="mock_redis_host",
        redis_port=6379,
        redis_password="mock_password",
        cache_ttl=3600
    )
    manager._initialized = False # Ensure it's not initialized
    manager._redis_available = False

    await manager.initialize()

    # Firestore initialize should NOT be called here as it's assumed to be initialized before injection
    mock_firestore_memory_manager.initialize.assert_not_called()
    mock_redis_client.initialize.assert_called_once()
    assert manager._initialized is True
    assert manager._redis_available is True

@async_test
async def test_initialize_redis_fails(mock_firestore_memory_manager, mock_redis_client):
    """Test initialization succeeds but Redis is unavailable if Redis initialization fails."""
    mock_redis_client.initialize.side_effect = RedisError("Redis connection failed")

    manager = FirestoreV1MemoryManager(
        firestore_memory=mock_firestore_memory_manager,
        redis_host="mock_redis_host",
        redis_port=6379,
        redis_password="mock_password",
        cache_ttl=3600
    )
    manager._initialized = False
    manager._redis_available = False

    await manager.initialize()

    mock_firestore_memory_manager.initialize.assert_not_called()
    mock_redis_client.initialize.assert_called_once()
    assert manager._initialized is True
    assert manager._redis_available is False # Redis should be marked as unavailable

@async_test
async def test_close(firestore_v1_memory_manager, mock_firestore_memory_manager, mock_redis_client):
    """Test closing the memory manager."""
    await firestore_v1_memory_manager.close()

    # Firestore close should NOT be called here as the injected instance's lifecycle is managed elsewhere
    mock_firestore_memory_manager.close.assert_not_called()
    mock_redis_client.close.assert_called_once()
    assert firestore_v1_memory_manager._initialized is False
    assert firestore_v1_memory_manager._redis_available is False

@async_test
async def test_close_redis_unavailable(firestore_v1_memory_manager, mock_firestore_memory_manager, mock_redis_client):
    """Test closing when Redis was unavailable."""
    firestore_v1_memory_manager._redis_available = False # Simulate Redis being unavailable
    await firestore_v1_memory_manager.close()

    mock_firestore_memory_manager.close.assert_not_called()
    mock_redis_client.close.assert_not_called() # Redis close should not be called if unavailable
    assert firestore_v1_memory_manager._initialized is False
    assert firestore_v1_memory_manager._redis_available is False

@async_test
async def test_add_memory_item_success(firestore_v1_memory_manager, mock_firestore_memory_manager, mock_redis_client):
    """Test adding a memory item successfully."""
    item = MemoryItem(user_id="user1", item_type="conversation", text_content="Hello")
    mock_firestore_memory_manager.add_memory_item.return_value = "new_item_id"

    item_id = await firestore_v1_memory_manager.add_memory_item(item)

    mock_firestore_memory_manager.add_memory_item.assert_called_once_with(item)
    mock_redis_client.get_cached_conversation_history.assert_called_once()
    mock_redis_client.cache_conversation_history.assert_called_once()
    assert item_id == "new_item_id"
    assert item.id is not None # Ensure ID was generated if not provided

@async_test
async def test_add_memory_item_firestore_fails(firestore_v1_memory_manager, mock_firestore_memory_manager, mock_redis_client):
    """Test adding a memory item fails if Firestore fails."""
    item = MemoryItem(user_id="user1", item_type="conversation", text_content="Hello")
    mock_firestore_memory_manager.add_memory_item.side_effect = StorageError("Firestore write failed")

    with pytest.raises(StorageError):
        await firestore_v1_memory_manager.add_memory_item(item)

    mock_firestore_memory_manager.add_memory_item.assert_called_once_with(item)
    mock_redis_client.get_cached_conversation_history.assert_not_called() # Redis should not be called if Firestore fails
    mock_redis_client.cache_conversation_history.assert_not_called()
    assert firestore_v1_memory_manager._error_count == 1

@async_test
async def test_add_memory_item_redis_fails(firestore_v1_memory_manager, mock_firestore_memory_manager, mock_redis_client):
    """Test adding a memory item succeeds even if Redis caching fails."""
    item = MemoryItem(user_id="user1", item_type="conversation", text_content="Hello")
    mock_firestore_memory_manager.add_memory_item.return_value = "new_item_id"
    mock_redis_client.cache_conversation_history.side_effect = RedisError("Redis cache failed")

    item_id = await firestore_v1_memory_manager.add_memory_item(item)

    mock_firestore_memory_manager.add_memory_item.assert_called_once_with(item)
    mock_redis_client.get_cached_conversation_history.assert_called_once()
    mock_redis_client.cache_conversation_history.assert_called_once()
    assert item_id == "new_item_id"
    assert firestore_v1_memory_manager._error_count == 1 # Error should be tracked

@async_test
async def test_get_memory_item_found(firestore_v1_memory_manager, mock_firestore_memory_manager):
    """Test retrieving a memory item that exists."""
    expected_item = MemoryItem(id="item1", user_id="user1", item_type="note", text_content="Note content")
    mock_firestore_memory_manager.get_memory_item.return_value = expected_item

    item = await firestore_v1_memory_manager.get_memory_item("item1")

    mock_firestore_memory_manager.get_memory_item.assert_called_once_with("item1")
    assert item == expected_item

@async_test
async def test_get_memory_item_not_found(firestore_v1_memory_manager, mock_firestore_memory_manager):
    """Test retrieving a memory item that does not exist."""
    mock_firestore_memory_manager.get_memory_item.return_value = None

    item = await firestore_v1_memory_manager.get_memory_item("non_existent_item")

    mock_firestore_memory_manager.get_memory_item.assert_called_once_with("non_existent_item")
    assert item is None
    assert firestore_v1_memory_manager._error_count == 0 # "Not found" is not tracked as an error

@async_test
async def test_get_memory_item_firestore_fails(firestore_v1_memory_manager, mock_firestore_memory_manager):
    """Test retrieving a memory item fails if Firestore fails."""
    mock_firestore_memory_manager.get_memory_item.side_effect = StorageError("Firestore read failed")

    with pytest.raises(StorageError):
        await firestore_v1_memory_manager.get_memory_item("item1")

    mock_firestore_memory_manager.get_memory_item.assert_called_once_with("item1")
    assert firestore_v1_memory_manager._error_count == 1

@async_test
async def test_get_conversation_history_cache_hit(firestore_v1_memory_manager, mock_firestore_memory_manager, mock_redis_client):
    """Test retrieving conversation history with a cache hit."""
    cached_history = [
        MemoryItem(id="item1", user_id="user1", item_type="conversation", text_content="Hi"),
        MemoryItem(id="item2", user_id="user1", item_type="conversation", text_content="Hello")
    ]
    mock_redis_client.get_cached_conversation_history.return_value = cached_history

    history = await firestore_v1_memory_manager.get_conversation_history("user1")

    mock_redis_client.get_cached_conversation_history.assert_called_once()
    mock_firestore_memory_manager.get_conversation_history.assert_not_called() # Firestore should not be called on cache hit
    mock_redis_client.cache_conversation_history.assert_not_called() # Should not cache on cache hit
    assert history == cached_history

@async_test
async def test_get_conversation_history_cache_miss(firestore_v1_memory_manager, mock_firestore_memory_manager, mock_redis_client):
    """Test retrieving conversation history with a cache miss."""
    firestore_history = [
        MemoryItem(id="item1", user_id="user1", item_type="conversation", text_content="Hi"),
        MemoryItem(id="item2", user_id="user1", item_type="conversation", text_content="Hello")
    ]
    mock_redis_client.get_cached_conversation_history.return_value = [] # Simulate cache miss
    mock_firestore_memory_manager.get_conversation_history.return_value = firestore_history

    history = await firestore_v1_memory_manager.get_conversation_history("user1")

    mock_redis_client.get_cached_conversation_history.assert_called_once()
    mock_firestore_memory_manager.get_conversation_history.assert_called_once()
    mock_redis_client.cache_conversation_history.assert_called_once_with(
        user_id="user1", history_items=firestore_history, session_id=None, ttl=firestore_v1_memory_manager._cache_ttl
    )
    assert history == firestore_history

@async_test
async def test_get_conversation_history_redis_unavailable(firestore_v1_memory_manager, mock_firestore_memory_manager, mock_redis_client):
    """Test retrieving conversation history when Redis is unavailable."""
    firestore_v1_memory_manager._redis_available = False # Simulate Redis unavailable
    firestore_history = [
        MemoryItem(id="item1", user_id="user1", item_type="conversation", text_content="Hi")
    ]
    mock_firestore_memory_manager.get_conversation_history.return_value = firestore_history

    history = await firestore_v1_memory_manager.get_conversation_history("user1")

    mock_redis_client.get_cached_conversation_history.assert_not_called() # Redis should not be called
    mock_firestore_memory_manager.get_conversation_history.assert_called_once()
    mock_redis_client.cache_conversation_history.assert_not_called() # Redis should not be called
    assert history == firestore_history

@async_test
async def test_get_conversation_history_with_filters(firestore_v1_memory_manager, mock_firestore_memory_manager, mock_redis_client):
    """Test retrieving conversation history with custom filters (should bypass cache)."""
    filters = {"item_type": "system"}
    firestore_history = [
        MemoryItem(id="item1", user_id="user1", item_type="system", text_content="System message")
    ]
    mock_firestore_memory_manager.get_conversation_history.return_value = firestore_history

    history = await firestore_v1_memory_manager.get_conversation_history("user1", filters=filters)

    mock_redis_client.get_cached_conversation_history.assert_not_called() # Should bypass cache
    mock_firestore_memory_manager.get_conversation_history.assert_called_once_with(
        user_id="user1", session_id=None, limit=20, filters=filters
    )
    mock_redis_client.cache_conversation_history.assert_not_called() # Should not cache filtered results
    assert history == firestore_history

@async_test
async def test_get_conversation_history_firestore_fails(firestore_v1_memory_manager, mock_firestore_memory_manager, mock_redis_client):
    """Test retrieving conversation history fails if Firestore fails."""
    mock_redis_client.get_cached_conversation_history.return_value = [] # Simulate cache miss
    mock_firestore_memory_manager.get_conversation_history.side_effect = StorageError("Firestore read failed")

    with pytest.raises(StorageError):
        await firestore_v1_memory_manager.get_conversation_history("user1")

    mock_redis_client.get_cached_conversation_history.assert_called_once()
    mock_firestore_memory_manager.get_conversation_history.assert_called_once()
    mock_redis_client.cache_conversation_history.assert_not_called()
    assert firestore_v1_memory_manager._error_count == 1

@async_test
async def test_semantic_search(firestore_v1_memory_manager, mock_firestore_memory_manager):
    """Test semantic search."""
    query_embedding = [0.1, 0.2, 0.3]
    firestore_results = [
        MemoryItem(id="item1", user_id="user1", item_type="note", text_content="Note 1"),
        MemoryItem(id="item2", user_id="user1", item_type="note", text_content="Note 2")
    ]
    mock_firestore_memory_manager.semantic_search.return_value = firestore_results

    results = await firestore_v1_memory_manager.semantic_search("user1", query_embedding)

    mock_firestore_memory_manager.semantic_search.assert_called_once_with(
        user_id="user1", query_embedding=query_embedding, persona_context=None, top_k=5
    )
    assert results == firestore_results

@async_test
async def test_semantic_search_firestore_fails(firestore_v1_memory_manager, mock_firestore_memory_manager):
    """Test semantic search fails if Firestore fails."""
    query_embedding = [0.1, 0.2, 0.3]
    mock_firestore_memory_manager.semantic_search.side_effect = StorageError("Firestore search failed")

    with pytest.raises(StorageError):
        await firestore_v1_memory_manager.semantic_search("user1", query_embedding)

    mock_firestore_memory_manager.semantic_search.assert_called_once_with(
        user_id="user1", query_embedding=query_embedding, persona_context=None, top_k=5
    )
    assert firestore_v1_memory_manager._error_count == 1

@async_test
async def test_add_raw_agent_data(firestore_v1_memory_manager, mock_firestore_memory_manager):
    """Test adding raw agent data."""
    agent_data = AgentData(agent_id="agent1", data_type="log", content={"message": "Agent started"})
    mock_firestore_memory_manager.add_raw_agent_data.return_value = "new_agent_data_id"

    data_id = await firestore_v1_memory_manager.add_raw_agent_data(agent_data)

    mock_firestore_memory_manager.add_raw_agent_data.assert_called_once_with(agent_data)
    assert data_id == "new_agent_data_id"

@async_test
async def test_add_raw_agent_data_firestore_fails(firestore_v1_memory_manager, mock_firestore_memory_manager):
    """Test adding raw agent data fails if Firestore fails."""
    agent_data = AgentData(agent_id="agent1", data_type="log", content={"message": "Agent started"})
    mock_firestore_memory_manager.add_raw_agent_data.side_effect = StorageError("Firestore write failed")

    with pytest.raises(StorageError):
        await firestore_v1_memory_manager.add_raw_agent_data(agent_data)

    mock_firestore_memory_manager.add_raw_agent_data.assert_called_once_with(agent_data)
    assert firestore_v1_memory_manager._error_count == 1

@async_test
async def test_check_duplicate_exists(firestore_v1_memory_manager, mock_firestore_memory_manager):
    """Test checking for duplicate when one exists."""
    item = MemoryItem(user_id="user1", item_type="conversation", text_content="Duplicate message")
    mock_firestore_memory_manager.check_duplicate.return_value = True

    is_duplicate = await firestore_v1_memory_manager.check_duplicate(item)

    mock_firestore_memory_manager.check_duplicate.assert_called_once_with(item)
    assert is_duplicate is True

@async_test
async def test_check_duplicate_not_exists(firestore_v1_memory_manager, mock_firestore_memory_manager):
    """Test checking for duplicate when none exists."""
    item = MemoryItem(user_id="user1", item_type="conversation", text_content="Unique message")
    mock_firestore_memory_manager.check_duplicate.return_value = False

    is_duplicate = await firestore_v1_memory_manager.check_duplicate(item)

    mock_firestore_memory_manager.check_duplicate.assert_called_once_with(item)
    assert is_duplicate is False

@async_test
async def test_check_duplicate_firestore_fails(firestore_v1_memory_manager, mock_firestore_memory_manager):
    """Test checking for duplicate fails if Firestore fails."""
    item = MemoryItem(user_id="user1", item_type="conversation", text_content="Message")
    mock_firestore_memory_manager.check_duplicate.side_effect = StorageError("Firestore check failed")

    with pytest.raises(StorageError):
        await firestore_v1_memory_manager.check_duplicate(item)

    mock_firestore_memory_manager.check_duplicate.assert_called_once_with(item)
    assert firestore_v1_memory_manager._error_count == 1

@async_test
async def test_cleanup_expired_items(firestore_v1_memory_manager, mock_firestore_memory_manager, mock_redis_client):
    """Test cleaning up expired items."""
    mock_firestore_memory_manager.cleanup_expired_items.return_value = 5

    count = await firestore_v1_memory_manager.cleanup_expired_items()

    mock_firestore_memory_manager.cleanup_expired_items.assert_called_once()
    mock_redis_client.flush_namespace.assert_called_once() # Redis cache should be flushed
    assert count == 5

@async_test
async def test_cleanup_expired_items_firestore_fails(firestore_v1_memory_manager, mock_firestore_memory_manager, mock_redis_client):
    """Test cleaning up expired items fails if Firestore fails."""
    mock_firestore_memory_manager.cleanup_expired_items.side_effect = StorageError("Firestore cleanup failed")

    with pytest.raises(StorageError):
        await firestore_v1_memory_manager.cleanup_expired_items()

    mock_firestore_memory_manager.cleanup_expired_items.assert_called_once()
    mock_redis_client.flush_namespace.assert_not_called() # Redis should not be flushed if Firestore fails
    assert firestore_v1_memory_manager._error_count == 1

@async_test
async def test_cleanup_expired_items_redis_fails(firestore_v1_memory_manager, mock_firestore_memory_manager, mock_redis_client):
    """Test cleaning up expired items succeeds even if Redis flush fails."""
    mock_firestore_memory_manager.cleanup_expired_items.return_value = 5
    mock_redis_client.flush_namespace.side_effect = RedisError("Redis flush failed")

    count = await firestore_v1_memory_manager.cleanup_expired_items()

    mock_firestore_memory_manager.cleanup_expired_items.assert_called_once()
    mock_redis_client.flush_namespace.assert_called_once()
    assert count == 5
    assert firestore_v1_memory_manager._error_count == 1 # Error should be tracked

@async_test
async def test_health_check_healthy(firestore_v1_memory_manager, mock_firestore_memory_manager, mock_redis_client):
    """Test health check when both backends are healthy."""
    # Mock the injected FirestoreMemoryManager's health_check
    mock_firestore_memory_manager.health_check.return_value = {"status": "healthy", "connection": True, "details": {"firestore_details": "ok"}}
    mock_redis_client.ping.return_value = True

    health = await firestore_v1_memory_manager.health_check()

    # The injected firestore_memory's health_check should be called
    mock_firestore_memory_manager.health_check.assert_called_once()
    mock_redis_client.ping.assert_called_once()
    assert health["status"] == "healthy"
    assert health["firestore"] is True
    assert health["redis"] is True
    assert health["error_count"] == 0

@async_test
async def test_health_check_firestore_unhealthy(firestore_v1_memory_manager, mock_firestore_memory_manager, mock_redis_client):
    """Test health check when injected Firestore is unhealthy."""
    mock_firestore_memory_manager.health_check.return_value = {"status": "unhealthy", "connection": False, "details": {"firestore_details": "error"}}
    mock_redis_client.ping.return_value = True

    health = await firestore_v1_memory_manager.health_check()

    mock_firestore_memory_manager.health_check.assert_called_once()
    mock_redis_client.ping.assert_called_once()
    assert health["status"] == "unhealthy"
    assert health["firestore"] is False
    assert health["redis"] is True

@async_test
async def test_health_check_redis_degraded(firestore_v1_memory_manager, mock_firestore_memory_manager, mock_redis_client):
    """Test health check when Redis is unhealthy (should be degraded)."""
    mock_firestore_memory_manager.health_check.return_value = {"status": "healthy", "connection": True, "details": {"firestore_details": "ok"}}
    mock_redis_client.ping.return_value = False # Simulate Redis ping failure

    health = await firestore_v1_memory_manager.health_check()

    mock_firestore_memory_manager.health_check.assert_called_once()
    mock_redis_client.ping.assert_called_once()
    assert health["status"] == "degraded"
    assert health["firestore"] is True
    assert health["redis"] is False

@async_test
async def test_health_check_redis_unavailable(firestore_v1_memory_manager, mock_firestore_memory_manager, mock_redis_client):
    """Test health check when Redis was never available."""
    firestore_v1_memory_manager._redis_available = False # Simulate Redis unavailable
    mock_firestore_memory_manager.health_check.return_value = {"status": "healthy", "connection": True, "details": {"firestore_details": "ok"}}

    health = await firestore_v1_memory_manager.health_check()

    mock_firestore_memory_manager.health_check.assert_called_once()
    mock_redis_client.ping.assert_not_called() # Redis ping should not be called
    assert health["status"] == "healthy" # Should still be healthy if Firestore is ok and Redis wasn't configured
    assert health["firestore"] is True
    assert health["redis"] is False # Redis is reported as not available

@async_test
async def test_health_check_not_initialized(uninitialized_firestore_v1_memory_manager, mock_firestore_memory_manager, mock_redis_client):
    """Test health check when the manager is not initialized."""
    # The health check itself should attempt initialization of Redis
    mock_redis_client.initialize.return_value = None
    mock_firestore_memory_manager.health_check.return_value = {"status": "healthy", "connection": True, "details": {"firestore_details": "ok"}}
    mock_redis_client.ping.return_value = True


    health = await uninitialized_firestore_v1_memory_manager.health_check()

    mock_redis_client.initialize.assert_called_once()
    mock_firestore_memory_manager.health_check.assert_called_once()
    mock_redis_client.ping.assert_called_once()
    assert health["status"] == "healthy"
    assert health["firestore"] is True
    assert health["redis"] is True
    assert "Initialized during health check" in health["details"].get("initialization", "")


@async_test
async def test_health_check_initialization_fails(uninitialized_firestore_v1_memory_manager, mock_firestore_memory_manager, mock_redis_client):
    """Test health check fails if initialization within health check fails."""
    mock_redis_client.initialize.side_effect = RedisError("Init failed")
    mock_firestore_memory_manager.health_check.return_value = {"status": "healthy", "connection": True, "details": {"firestore_details": "ok"}}


    health = await uninitialized_firestore_v1_memory_manager.health_check()

    mock_redis_client.initialize.assert_called_once()
    mock_firestore_memory_manager.health_check.assert_called_once()
    mock_redis_client.ping.assert_not_called()
    assert health["status"] == "degraded" # Redis failed, Firestore is ok
    assert "Init failed" in health["details"].get("redis_error", "")


@async_test
async def test_methods_require_initialization(uninitialized_firestore_v1_memory_manager):
    """Test that methods raise RuntimeError if not initialized."""
    item = MemoryItem(user_id="user1", item_type="conversation", text_content="Hello")
    agent_data = AgentData(agent_id="agent1", data_type="log", content={})
    embedding = [0.1, 0.2]

    # These methods should NOT require the FirestoreV1MemoryManager's own initialize() to be called,
    # as they rely on the injected FirestoreMemoryManager which is assumed initialized.
    # The _check_initialized method in the original ConcreteMemoryManager was checking the
    # ConcreteMemoryManager's own initialization status, which is now only for Redis.
    # We need to update the tests to reflect this.

    # Re-evaluate the need for _check_initialized in FirestoreV1MemoryManager.
    # If FirestoreMemoryManager is injected and assumed initialized, and Redis is optional,
    # maybe _check_initialized is not needed or should only check Redis availability for caching-related methods.

    # For now, let's assume the _check_initialized method remains and tests Redis initialization.
    # The methods that interact with Firestore directly should not raise this error if Firestore is initialized.
    # Methods that interact with Redis might.

    # Based on the refactored code provided earlier, _check_initialized is still present
    # and checks self._initialized, which is set after Redis initialization.
    # So, methods will still raise RuntimeError if Redis initialization failed.

    # Let's test the methods that rely on Redis first.
    # add_memory_item uses Redis caching
    with pytest.raises(RuntimeError, match="Memory manager not initialized"):
         await uninitialized_firestore_v1_memory_manager.add_memory_item(item)

    # get_conversation_history uses Redis caching
    with pytest.raises(RuntimeError, match="Memory manager not initialized"):
         await uninitialized_firestore_v1_memory_manager.get_conversation_history("user1")

    # cleanup_expired_items flushes Redis cache
    with pytest.raises(RuntimeError, match="Memory manager not initialized"):
         await uninitialized_firestore_v1_memory_manager.cleanup_expired_items()

    # Methods that only interact with Firestore should NOT raise this error
    # get_memory_item
    # semantic_search
    # add_raw_agent_data
    # check_duplicate

    # Let's adjust the fixture to simulate Firestore being initialized but Redis not.
    # This requires a new fixture or modifying the existing uninitialized one.
    # Let's modify the existing uninitialized fixture setup slightly for these specific tests.

    # Temporarily override _initialized for these tests
    uninitialized_firestore_v1_memory_manager._initialized = False # Ensure Redis is not initialized

    # These should now pass without raising RuntimeError if Firestore mock is configured
    await uninitialized_firestore_v1_memory_manager.get_memory_item("item1")
    await uninitialized_firestore_v1_memory_manager.semantic_search("user1", embedding)
    await uninitialized_firestore_v1_memory_manager.add_raw_agent_data(agent_data)
    await uninitialized_firestore_v1_memory_manager.check_duplicate(item)

    # health_check is an exception, it should attempt initialization
    health = await uninitialized_firestore_v1_memory_manager.health_check()
    assert health["status"] != "error" # Assuming initialization within health check succeeds in this case
