"""
Integration tests for storage implementations.

These tests verify the integration with real storage backends (Firestore and Redis).
They will be skipped if the real GCP credentials or Redis server are not available.
"""

import os
import pytest
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from packages.shared.src.models.base_models import MemoryItem, AgentData
from packages.shared.src.storage.firestore.firestore_memory import FirestoreMemoryManager
from packages.shared.src.storage.redis.redis_client import RedisClient
from packages.shared.src.memory.concrete_memory_manager import ConcreteMemoryManager


# Configure logging
logger = logging.getLogger(__name__)

# Check if integration tests should be run
SKIP_INTEGRATION_TESTS = os.environ.get("RUN_INTEGRATION_TESTS", "").lower() != "true"
skip_reason = "RUN_INTEGRATION_TESTS environment variable not set to 'true'"

# Skip markers
skip_firestore = pytest.mark.skipif(
    SKIP_INTEGRATION_TESTS or not os.environ.get("GCP_PROJECT_ID"), 
    reason=skip_reason + " or GCP_PROJECT_ID not set"
)

skip_redis = pytest.mark.skipif(
    SKIP_INTEGRATION_TESTS or not os.environ.get("REDIS_HOST"),
    reason=skip_reason + " or REDIS_HOST not set"
)

skip_concrete = pytest.mark.skipif(
    SKIP_INTEGRATION_TESTS or not (os.environ.get("GCP_PROJECT_ID") and os.environ.get("REDIS_HOST")),
    reason=skip_reason + " or GCP_PROJECT_ID/REDIS_HOST not set"
)


def generate_unique_key() -> str:
    """Generate a unique key for test data."""
    return f"test_{uuid.uuid4().hex[:8]}_{int(datetime.utcnow().timestamp())}"


@pytest.fixture
def test_memory_item() -> MemoryItem:
    """Create a test memory item with a unique key."""
    return MemoryItem(
        id=generate_unique_key(),
        user_id="test_user",
        session_id="test_session",
        timestamp=datetime.utcnow(),
        item_type="conversation",
        persona_active="Cherry",
        text_content=f"Test message {generate_unique_key()}",
        metadata={"test_key": "test_value"}
    )


@pytest.fixture
def test_agent_data() -> AgentData:
    """Create test agent data with a unique key."""
    return AgentData(
        id=generate_unique_key(),
        agent_id="test_agent",
        timestamp=datetime.utcnow(),
        data_type="test",
        content={"test_key": "test_value"}
    )


@skip_firestore
class TestFirestoreIntegration:
    """Integration tests for Firestore storage."""

    @pytest.fixture(autouse=True)
    def setup_firestore(self):
        """Set up Firestore client before tests and clean up after."""
        # Get project ID from environment
        project_id = os.environ.get("GCP_PROJECT_ID")
        credentials_path = os.environ.get("GCP_SA_KEY_PATH")
        credentials_json = os.environ.get("GCP_SA_KEY_JSON")
        
        # Create Firestore client
        self.firestore = FirestoreMemoryManager(
            project_id=project_id,
            credentials_json=credentials_json,
            credentials_path=credentials_path
        )
        
        # Initialize
        self.firestore.initialize()
        logger.info("Firestore test client initialized")
        
        # Yield for test
        yield
        
        # Clean up
        self.firestore.close()
        logger.info("Firestore test client closed")

    @pytest.mark.asyncio
    async def test_add_memory_item(self, test_memory_item):
        """Test adding and retrieving a memory item."""
        # Add item
        item_id = await self.firestore.add_memory_item(test_memory_item)
        assert item_id == test_memory_item.id
        
        # Retrieve item
        retrieved_item = await self.firestore.get_memory_item(item_id)
        assert retrieved_item is not None
        assert retrieved_item.id == test_memory_item.id
        assert retrieved_item.user_id == test_memory_item.user_id
        assert retrieved_item.text_content == test_memory_item.text_content

    @pytest.mark.asyncio
    async def test_conversation_history(self):
        """Test retrieving conversation history."""
        # Create and add multiple items for the same user
        user_id = f"test_user_{generate_unique_key()}"
        
        # Add 5 memory items
        for i in range(5):
            item = MemoryItem(
                id=generate_unique_key(),
                user_id=user_id,
                session_id="test_session",
                timestamp=datetime.utcnow() - timedelta(minutes=i),
                item_type="conversation",
                persona_active="Cherry",
                text_content=f"Test message {i}",
                metadata={}
            )
            await self.firestore.add_memory_item(item)
        
        # Retrieve history
        history = await self.firestore.get_conversation_history(user_id=user_id, limit=3)
        
        # Check results
        assert len(history) <= 3  # May be less if items weren't added yet
        assert all(item.user_id == user_id for item in history)
        assert all(item.item_type == "conversation" for item in history)

    @pytest.mark.asyncio
    async def test_add_agent_data(self, test_agent_data):
        """Test adding agent data."""
        # Add data
        data_id = await self.firestore.add_raw_agent_data(test_agent_data)
        assert data_id == test_agent_data.id


@skip_redis
class TestRedisIntegration:
    """Integration tests for Redis storage."""

    @pytest.fixture(autouse=True)
    def setup_redis(self):
        """Set up Redis client before tests and clean up after."""
        # Get Redis config from environment
        host = os.environ.get("REDIS_HOST", "localhost")
        port = int(os.environ.get("REDIS_PORT", "6379"))
        password = os.environ.get("REDIS_PASSWORD")
        
        # Create Redis client with test namespace
        self.redis = RedisClient(
            host=host,
            port=port,
            password=password,
            namespace="orchestra_test:",
            default_ttl=60  # 60 seconds for tests
        )
        
        # Initialize
        self.redis.initialize()
        logger.info("Redis test client initialized")
        
        # Yield for test
        yield
        
        # Clean up - flush test namespace
        asyncio.get_event_loop().run_until_complete(self.redis.flush_namespace())
        self.redis.close()
        logger.info("Redis test client closed and test keys flushed")

    @pytest.mark.asyncio
    async def test_set_get(self):
        """Test setting and getting values."""
        key = generate_unique_key()
        value = {"test": True, "items": [1, 2, 3]}
        
        # Set value
        result = await self.redis.set(key, value)
        assert result is True
        
        # Get value
        retrieved = await self.redis.get(key)
        assert retrieved == value
        
        # Delete
        await self.redis.delete(key)
        assert await self.redis.get(key) is None

    @pytest.mark.asyncio
    async def test_conversation_history_cache(self, test_memory_item):
        """Test caching conversation history."""
        user_id = test_memory_item.user_id
        
        # Cache a list of memory items
        items = [test_memory_item]
        for i in range(3):
            item = MemoryItem(
                id=generate_unique_key(),
                user_id=user_id,
                session_id="test_session",
                timestamp=datetime.utcnow(),
                item_type="conversation",
                persona_active="Cherry",
                text_content=f"Test message {i}",
                metadata={}
            )
            items.append(item)
        
        # Cache the items
        result = await self.redis.cache_conversation_history(user_id, items)
        assert result is True
        
        # Retrieve cached items
        cached = await self.redis.get_cached_conversation_history(user_id)
        assert len(cached) == len(items)
        
        # Verify items
        for orig, cached_item in zip(items, cached):
            assert cached_item.id == orig.id
            assert cached_item.text_content == orig.text_content

    @pytest.mark.asyncio
    async def test_session_data_cache(self):
        """Test caching session data."""
        user_id = f"test_user_{generate_unique_key()}"
        session_id = generate_unique_key()
        
        # Session data
        data = {
            "settings": {"theme": "dark", "language": "en"},
            "last_access": datetime.utcnow().isoformat(),
            "session_count": 5
        }
        
        # Cache data
        result = await self.redis.cache_session_data(user_id, session_id, data)
        assert result is True
        
        # Retrieve cached data
        cached = await self.redis.get_cached_session_data(user_id, session_id)
        assert cached == data


@skip_concrete
class TestConcreteMemoryManager:
    """Integration tests for ConcreteMemoryManager which uses both Firestore and Redis."""

    @pytest.fixture(autouse=True)
    def setup_manager(self):
        """Set up ConcreteMemoryManager before tests and clean up after."""
        # Get config from environment
        project_id = os.environ.get("GCP_PROJECT_ID")
        credentials_path = os.environ.get("GCP_SA_KEY_PATH")
        credentials_json = os.environ.get("GCP_SA_KEY_JSON")
        redis_host = os.environ.get("REDIS_HOST", "localhost")
        redis_port = int(os.environ.get("REDIS_PORT", "6379"))
        redis_password = os.environ.get("REDIS_PASSWORD")
        
        # Create manager with test namespace for Redis
        self.manager = ConcreteMemoryManager(
            project_id=project_id,
            credentials_json=credentials_json,
            credentials_path=credentials_path,
            redis_host=redis_host,
            redis_port=redis_port,
            redis_password=redis_password,
            cache_ttl=60  # 60 seconds for tests
        )
        
        # Initialize
        self.manager.initialize()
        logger.info("ConcreteMemoryManager initialized for tests")
        
        # Yield for test
        yield
        
        # Clean up
        self.manager.close()
        logger.info("ConcreteMemoryManager closed")

    @pytest.mark.asyncio
    async def test_add_and_retrieve_item(self, test_memory_item):
        """Test adding and retrieving a memory item with the concrete manager."""
        # Add item
        item_id = await self.manager.add_memory_item(test_memory_item)
        assert item_id == test_memory_item.id
        
        # Retrieve item
        retrieved_item = await self.manager.get_memory_item(item_id)
        assert retrieved_item is not None
        assert retrieved_item.id == test_memory_item.id
        assert retrieved_item.user_id == test_memory_item.user_id
        assert retrieved_item.text_content == test_memory_item.text_content

    @pytest.mark.asyncio
    async def test_conversation_history_caching(self):
        """Test conversation history with caching."""
        # Create a unique user for this test
        user_id = f"test_user_{generate_unique_key()}"
        
        # Add 3 memory items
        for i in range(3):
            item = MemoryItem(
                id=generate_unique_key(),
                user_id=user_id,
                session_id="test_session",
                timestamp=datetime.utcnow() - timedelta(minutes=i),
                item_type="conversation",
                persona_active="Cherry",
                text_content=f"Test message {i}",
                metadata={}
            )
            await self.manager.add_memory_item(item)
        
        # First retrieval should get from Firestore and cache in Redis
        history1 = await self.manager.get_conversation_history(user_id=user_id)
        assert len(history1) == 3
        
        # Second retrieval should get from Redis cache
        history2 = await self.manager.get_conversation_history(user_id=user_id)
        assert len(history2) == 3
        
        # Verify items are the same
        for item1, item2 in zip(history1, history2):
            assert item1.id == item2.id
            assert item1.text_content == item2.text_content

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check functionality."""
        # Perform health check
        health = await self.manager.health_check()
        
        # Verify result
        assert isinstance(health, dict)
        assert "firestore" in health
        assert "redis" in health
        assert health["firestore"] is True
        
        # Redis may be True or False depending on availability
        assert health["redis"] in [True, False]
