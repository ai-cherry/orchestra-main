"""Tests for the UnifiedContextManager."""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import asyncpg
import pytest
from weaviate import Client

from factory_integration.cache_manager import CacheManager
from factory_integration.context_manager import (
    ContextMetadata,
    ContextVersion,
    UnifiedContextManager,
)

@pytest.fixture
async def mock_db_pool():
    """Create a mock database pool."""
    pool = AsyncMock(spec=asyncpg.Pool)
    conn = AsyncMock()

    # Mock connection acquisition
    pool.acquire.return_value.__aenter__.return_value = conn
    pool.acquire.return_value.__aexit__.return_value = None

    return pool

@pytest.fixture
def mock_weaviate_client():
    """Create a mock Weaviate client."""
    client = MagicMock(spec=Client)
    client.query.get.return_value.with_near_vector.return_value.with_limit.return_value.do.return_value = {
        "data": {"Get": {"FactoryContext": []}}
    }
    return client

@pytest.fixture
async def mock_cache_manager():
    """Create a mock cache manager."""
    cache = AsyncMock(spec=CacheManager)
    cache.get.return_value = None
    cache.set.return_value = None
    cache.get_metrics.return_value = {"hit_rate": 85.0}
    return cache

@pytest.fixture
async def context_manager(mock_db_pool, mock_weaviate_client, mock_cache_manager):
    """Create a UnifiedContextManager instance with mocks."""
    manager = UnifiedContextManager(
        db_pool=mock_db_pool,
        weaviate_client=mock_weaviate_client,
        cache_manager=mock_cache_manager,
        sync_interval=1,
        max_context_size=1024,
        version_retention=10,
    )
    await manager.start()
    yield manager
    await manager.stop()

class TestUnifiedContextManager:
    """Test cases for UnifiedContextManager."""

    async def test_store_context_new(self, context_manager, mock_db_pool):
        """Test storing a new context."""
        # Setup mock responses
        conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        conn.fetchrow.side_effect = [
            None,  # No existing context
            {
                "id": "123",
                "context_id": "ctx_test",
                "parent_id": None,
                "version": 1,
                "source": "factory",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "data": {"test": "data"},
                "embeddings": None,
            },
        ]

        # Store context
        metadata = await context_manager.store_context(
            context_id="ctx_test",
            data={"test": "data"},
            source="factory",
        )

        # Verify
        assert metadata.context_id == "ctx_test"
        assert metadata.version == 1
        assert metadata.source == "factory"
        assert conn.execute.called

    async def test_store_context_update(self, context_manager, mock_db_pool):
        """Test updating an existing context."""
        # Setup mock responses
        conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        existing_metadata = {
            "context_id": "ctx_test",
            "version": 1,
            "source": "factory",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        conn.fetchrow.side_effect = [
            existing_metadata,  # Existing context
            {**existing_metadata, "version": 2},  # Updated context
        ]

        # Store context
        metadata = await context_manager.store_context(
            context_id="ctx_test",
            data={"test": "updated"},
            source="factory",
        )

        # Verify
        assert metadata.version == 2

    async def test_store_context_size_limit(self, context_manager):
        """Test context size limit validation."""
        # Create data that exceeds size limit
        large_data = {"data": "x" * 2000}

        # Should raise ValueError
        with pytest.raises(ValueError, match="exceeds limit"):
            await context_manager.store_context(
                context_id="ctx_large",
                data=large_data,
                source="factory",
            )

    async def test_get_context_from_cache(self, context_manager, mock_cache_manager):
        """Test getting context from cache."""
        # Setup cache hit
        cached_data = {"metadata": {"context_id": "ctx_test"}, "data": {"test": "data"}}
        mock_cache_manager.get.return_value = cached_data

        # Get context
        result = await context_manager.get_context("ctx_test")

        # Verify
        assert result == cached_data
        mock_cache_manager.get.assert_called_once_with("context:ctx_test")

    async def test_get_context_from_db(self, context_manager, mock_db_pool, mock_cache_manager):
        """Test getting context from database when not in cache."""
        # Setup cache miss
        mock_cache_manager.get.return_value = None

        # Setup database response
        conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        conn.fetchrow.side_effect = [
            {
                "context_id": "ctx_test",
                "version": 1,
                "source": "factory",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            },
            {"data": {"test": "data"}},
        ]

        # Get context
        result = await context_manager.get_context("ctx_test")

        # Verify
        assert result == {"test": "data"}
        mock_cache_manager.set.assert_called_once()

    async def test_get_context_specific_version(self, context_manager, mock_db_pool):
        """Test getting a specific version of context."""
        # Setup database response
        conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        conn.fetchrow.return_value = {"data": {"test": "version2"}}

        # Get specific version
        result = await context_manager.get_context("ctx_test", version=2)

        # Verify
        assert result == {"test": "version2"}

    async def test_search_similar_contexts(self, context_manager, mock_weaviate_client):
        """Test searching for similar contexts."""
        # Setup Weaviate response
        mock_weaviate_client.query.get.return_value.with_near_vector.return_value.with_limit.return_value.do.return_value = {
            "data": {
                "Get": {
                    "FactoryContext": [
                        {
                            "contextId": "ctx_1",
                            "metadata": {"test": "data1"},
                            "_additional": {"certainty": 0.95},
                        },
                        {
                            "contextId": "ctx_2",
                            "metadata": {"test": "data2"},
                            "_additional": {"certainty": 0.85},
                        },
                    ]
                }
            }
        }

        # Search
        results = await context_manager.search_similar_contexts(query_embeddings=[0.1] * 1536, limit=5, threshold=0.8)

        # Verify
        assert len(results) == 2
        assert results[0][0] == "ctx_1"
        assert results[0][1] == 0.95
        assert results[1][0] == "ctx_2"
        assert results[1][1] == 0.85

    async def test_merge_contexts_latest_strategy(self, context_manager):
        """Test merging contexts with latest strategy."""
        # Mock get_context to return test data
        context_manager.get_context = AsyncMock()
        context_manager.get_context.side_effect = [
            {"data": {"a": 1, "b": 2}},
            {"data": {"b": 3, "c": 4}},
        ]

        # Mock store_context
        context_manager.store_context = AsyncMock()
        context_manager.store_context.return_value = ContextMetadata(context_id="merged_test", version=1, source="mcp")

        # Merge contexts
        new_id = await context_manager.merge_contexts(["ctx_1", "ctx_2"], "latest")

        # Verify
        assert new_id.startswith("merged_")
        context_manager.store_context.assert_called_once()
        call_args = context_manager.store_context.call_args[1]
        assert call_args["data"] == {"b": 3, "c": 4}  # Latest context data

    async def test_merge_contexts_union_strategy(self, context_manager):
        """Test merging contexts with union strategy."""
        # Mock get_context to return test data
        context_manager.get_context = AsyncMock()
        context_manager.get_context.side_effect = [
            {"data": {"a": 1, "b": 2}},
            {"data": {"b": 3, "c": 4}},
        ]

        # Mock store_context
        context_manager.store_context = AsyncMock()

        # Merge contexts
        await context_manager.merge_contexts(["ctx_1", "ctx_2"], "union")

        # Verify
        call_args = context_manager.store_context.call_args[1]
        assert call_args["data"] == {"a": 1, "b": 3, "c": 4}  # Union of all keys

    async def test_sync_with_factory(self, context_manager):
        """Test syncing Factory AI context to MCP."""
        # Mock store_context and _generate_embeddings
        context_manager.store_context = AsyncMock()
        context_manager._generate_embeddings = AsyncMock(return_value=[0.1] * 1536)

        # Sync Factory context
        factory_context = {"id": "factory_123", "data": {"test": "factory_data"}}
        await context_manager.sync_with_factory(factory_context)

        # Verify
        context_manager.store_context.assert_called_once_with(
            "factory_123",
            {"test": "factory_data"},
            "factory",
            embeddings=[0.1] * 1536,
        )

    async def test_sync_to_factory(self, context_manager):
        """Test syncing MCP context to Factory AI format."""
        # Mock get_context
        context_manager.get_context = AsyncMock(
            return_value={
                "data": {"test": "mcp_data"},
                "metadata": {"version": 1},
            }
        )

        # Sync to Factory
        factory_format = await context_manager.sync_to_factory("mcp_123")

        # Verify
        assert factory_format["id"] == "mcp_123"
        assert factory_format["data"] == {"test": "mcp_data"}
        assert "timestamp" in factory_format

    async def test_cleanup_old_versions(self, context_manager, mock_db_pool):
        """Test cleaning up old context versions."""
        # Setup database response
        conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        conn.fetch.return_value = [
            {"context_id": "ctx_1", "version_count": 15},
            {"context_id": "ctx_2", "version_count": 12},
        ]

        # Run cleanup
        cleaned = await context_manager.cleanup_old_versions()

        # Verify
        assert conn.execute.call_count == 2  # Two contexts to clean
        assert cleaned == 0  # Mock doesn't return actual count

    async def test_get_metrics(self, context_manager, mock_db_pool, mock_cache_manager):
        """Test getting context manager metrics."""
        # Setup database responses
        conn = mock_db_pool.acquire.return_value.__aenter__.return_value
        conn.fetchval.side_effect = [100, 500]  # context count, version count

        # Get metrics
        metrics = await context_manager.get_metrics()

        # Verify
        assert metrics["contexts"]["total"] == 100
        assert metrics["contexts"]["versions"] == 500
        assert metrics["contexts"]["avg_versions_per_context"] == 5.0
        assert "cache" in metrics
        assert metrics["sync"]["interval"] == 1
        assert metrics["sync"]["running"] is True

    async def test_context_manager_lifecycle(self, mock_db_pool, mock_weaviate_client, mock_cache_manager):
        """Test context manager start/stop lifecycle."""
        manager = UnifiedContextManager(
            db_pool=mock_db_pool,
            weaviate_client=mock_weaviate_client,
            cache_manager=mock_cache_manager,
        )

        # Test context manager usage
        async with manager as cm:
            assert cm._running is True
            assert cm._sync_task is not None

        # After exit, should be stopped
        assert manager._running is False
        assert manager._sync_task.cancelled()

    @patch("factory_integration.context_manager.logger")
    async def test_sync_loop_error_handling(self, mock_logger, context_manager):
        """Test error handling in sync loop."""
        # Let sync loop run briefly
        await asyncio.sleep(0.1)

        # Verify it's still running despite no actual sync logic
        assert context_manager._running is True

        # Stop and verify no errors logged
        await context_manager.stop()
        mock_logger.error.assert_not_called()
