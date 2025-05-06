"""
Tests for the memory manager factory and configuration system.

This module contains tests for the memory manager factory, configuration system,
and telemetry integration introduced in Phase 3 of the memory management
consolidation plan.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from packages.shared.src.memory.config import (
    MemoryConfig,
    MemoryBackendType,
    FirestoreConfig,
    RedisConfig,
    InMemoryConfig,
    VectorSearchConfig,
    VectorSearchType,
    TelemetryConfig
)
from packages.shared.src.memory.factory import MemoryManagerFactory
from packages.shared.src.memory.telemetry import (
    configure_telemetry,
    trace_operation,
    trace_context,
    log_operation
)


class TestMemoryConfig:
    """Tests for the memory configuration system."""

    def test_default_config(self):
        """Test creating a default configuration."""
        config = MemoryConfig()
        
        # Check default values
        assert config.backend == MemoryBackendType.FIRESTORE
        assert config.firestore is not None
        assert config.vector_search is not None
        assert config.telemetry is not None
        
    def test_custom_config(self):
        """Test creating a custom configuration."""
        config = MemoryConfig(
            backend=MemoryBackendType.REDIS,
            redis=RedisConfig(
                host="redis.example.com",
                port=6380,
                namespace="test"
            ),
            vector_search=VectorSearchConfig(
                provider=VectorSearchType.VERTEX,
                vertex={
                    "index_endpoint_id": "test-endpoint",
                    "index_id": "test-index"
                }
            )
        )
        
        # Check custom values
        assert config.backend == MemoryBackendType.REDIS
        assert config.redis is not None
        assert config.redis.host == "redis.example.com"
        assert config.redis.port == 6380
        assert config.redis.namespace == "test"
        assert config.vector_search.provider == VectorSearchType.VERTEX
        assert config.vector_search.vertex is not None
        assert config.vector_search.vertex.index_endpoint_id == "test-endpoint"
        assert config.vector_search.vertex.index_id == "test-index"
        
    def test_config_from_env(self):
        """Test creating a configuration from environment variables."""
        # Set environment variables
        with patch.dict(os.environ, {
            "MEMORY_BACKEND": "redis",
            "REDIS_HOST": "redis.example.com",
            "REDIS_PORT": "6380",
            "VECTOR_SEARCH_PROVIDER": "vertex",
            "VECTOR_SEARCH_INDEX_ENDPOINT_ID": "test-endpoint",
            "VECTOR_SEARCH_INDEX_ID": "test-index"
        }):
            config = MemoryConfig.from_env()
            
            # Check values from environment variables
            assert config.backend == MemoryBackendType.REDIS
            assert config.redis is not None
            assert config.redis.host == "redis.example.com"
            assert config.redis.port == 6380
            assert config.vector_search.provider == VectorSearchType.VERTEX
            assert config.vector_search.vertex is not None
            assert config.vector_search.vertex.index_endpoint_id == "test-endpoint"
            assert config.vector_search.vertex.index_id == "test-index"
            
    def test_validation(self):
        """Test configuration validation."""
        # Test invalid vector search configuration
        with pytest.raises(ValueError):
            MemoryConfig(
                vector_search=VectorSearchConfig(
                    provider=VectorSearchType.VERTEX
                    # Missing vertex configuration
                )
            )


class TestMemoryManagerFactory:
    """Tests for the memory manager factory."""

    @pytest.mark.asyncio
    async def test_create_firestore_memory_manager(self):
        """Test creating a Firestore memory manager."""
        # Mock FirestoreMemoryManagerV2
        with patch("packages.shared.src.memory.factory.FirestoreMemoryManagerV2") as mock_firestore:
            # Mock instance
            mock_instance = MagicMock()
            mock_firestore.return_value = mock_instance
            
            # Create memory manager
            config = MemoryConfig(
                backend=MemoryBackendType.FIRESTORE,
                firestore=FirestoreConfig(
                    namespace="test"
                )
            )
            
            memory_manager = await MemoryManagerFactory.create_memory_manager(config)
            
            # Check that FirestoreMemoryManagerV2 was created with correct parameters
            mock_firestore.assert_called_once()
            assert mock_firestore.call_args[1]["namespace"] == "test"
            
            # Check that initialize was called
            mock_instance.initialize.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_create_redis_memory_manager(self):
        """Test creating a Redis memory manager."""
        # Mock ConcreteMemoryManager and AsyncRedisClient
        with patch("packages.shared.src.memory.factory.ConcreteMemoryManager") as mock_concrete, \
             patch("packages.shared.src.memory.factory.AsyncRedisClient") as mock_redis:
            # Mock instance
            mock_instance = MagicMock()
            mock_concrete.return_value = mock_instance
            
            # Create memory manager
            config = MemoryConfig(
                backend=MemoryBackendType.REDIS,
                redis=RedisConfig(
                    host="redis.example.com",
                    port=6380,
                    namespace="test"
                )
            )
            
            memory_manager = await MemoryManagerFactory.create_memory_manager(config)
            
            # Check that AsyncRedisClient was created with correct parameters
            mock_redis.assert_called_once()
            assert mock_redis.call_args[1]["host"] == "redis.example.com"
            assert mock_redis.call_args[1]["port"] == 6380
            assert mock_redis.call_args[1]["namespace"] == "test"
            
            # Check that ConcreteMemoryManager was created with correct parameters
            mock_concrete.assert_called_once()
            assert mock_concrete.call_args[1]["namespace"] == "test"
            
            # Check that initialize was called
            mock_instance.initialize.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_create_in_memory_manager(self):
        """Test creating an in-memory manager."""
        # Mock ConcreteMemoryManager
        with patch("packages.shared.src.memory.factory.ConcreteMemoryManager") as mock_concrete:
            # Mock instance
            mock_instance = MagicMock()
            mock_concrete.return_value = mock_instance
            
            # Create memory manager
            config = MemoryConfig(
                backend=MemoryBackendType.IN_MEMORY,
                in_memory=InMemoryConfig(
                    namespace="test",
                    max_items=1000
                )
            )
            
            memory_manager = await MemoryManagerFactory.create_memory_manager(config)
            
            # Check that ConcreteMemoryManager was created with correct parameters
            mock_concrete.assert_called_once()
            assert mock_concrete.call_args[1]["namespace"] == "test"
            assert mock_concrete.call_args[1]["max_items"] == 1000
            
            # Check that initialize was called
            mock_instance.initialize.assert_called_once()
            
    def test_detect_capabilities(self):
        """Test detecting capabilities."""
        # Mock imports
        with patch.dict("sys.modules", {
            "google.cloud.firestore": MagicMock(),
            "redis": MagicMock(),
            "google.cloud.aiplatform": MagicMock()
        }):
            capabilities = MemoryManagerFactory.detect_capabilities()
            
            # Check capabilities
            assert capabilities["firestore"] is True
            assert capabilities["redis"] is True
            assert capabilities["vector_search"]["in_memory"] is True
            assert capabilities["vector_search"]["vertex"] is True
            
    def test_get_available_backends(self):
        """Test getting available backends."""
        # Mock detect_capabilities
        with patch.object(
            MemoryManagerFactory,
            "detect_capabilities",
            return_value={
                "firestore": True,
                "redis": False,
                "vector_search": {
                    "in_memory": True,
                    "vertex": False
                }
            }
        ):
            backends = MemoryManagerFactory.get_available_backends()
            
            # Check backends
            assert MemoryBackendType.IN_MEMORY in backends
            assert MemoryBackendType.FIRESTORE in backends
            assert MemoryBackendType.REDIS not in backends
            
    def test_get_available_vector_search_providers(self):
        """Test getting available vector search providers."""
        # Mock detect_capabilities
        with patch.object(
            MemoryManagerFactory,
            "detect_capabilities",
            return_value={
                "firestore": True,
                "redis": True,
                "vector_search": {
                    "in_memory": True,
                    "vertex": True
                }
            }
        ):
            providers = MemoryManagerFactory.get_available_vector_search_providers()
            
            # Check providers
            assert VectorSearchType.IN_MEMORY in providers
            assert VectorSearchType.VERTEX in providers
            assert VectorSearchType.NONE in providers


class TestTelemetry:
    """Tests for the telemetry integration."""

    def test_configure_telemetry(self):
        """Test configuring telemetry."""
        # Configure telemetry
        config = TelemetryConfig(
            enabled=True,
            log_level="DEBUG"
        )
        
        configure_telemetry(config)
        
        # No assertions needed, just checking that it doesn't raise exceptions
        
    def test_trace_operation_decorator(self):
        """Test trace_operation decorator."""
        # Mock OpenTelemetry
        with patch("packages.shared.src.memory.telemetry.OPENTELEMETRY_AVAILABLE", True), \
             patch("packages.shared.src.memory.telemetry.trace") as mock_trace:
            # Mock tracer and span
            mock_tracer = MagicMock()
            mock_span = MagicMock()
            mock_trace.get_tracer.return_value = mock_tracer
            mock_tracer.start_span.return_value = mock_span
            
            # Define decorated function
            @trace_operation("test_operation")
            def test_function():
                return "test"
                
            # Call function
            result = test_function()
            
            # Check result
            assert result == "test"
            
            # Check that span was created and ended
            mock_trace.get_tracer.assert_called_once_with("memory")
            mock_tracer.start_span.assert_called_once_with("test_operation", kind="internal")
            mock_span.end.assert_called_once()
            
    def test_trace_context_manager(self):
        """Test trace_context context manager."""
        # Mock OpenTelemetry
        with patch("packages.shared.src.memory.telemetry.OPENTELEMETRY_AVAILABLE", True), \
             patch("packages.shared.src.memory.telemetry.trace") as mock_trace:
            # Mock tracer and span
            mock_tracer = MagicMock()
            mock_span = MagicMock()
            mock_trace.get_tracer.return_value = mock_tracer
            mock_tracer.start_span.return_value = mock_span
            
            # Use context manager
            with trace_context("test_operation"):
                pass
                
            # Check that span was created and ended
            mock_trace.get_tracer.assert_called_once_with("memory")
            mock_tracer.start_span.assert_called_once_with("test_operation", kind="internal")
            mock_span.end.assert_called_once()
            
    def test_log_operation(self):
        """Test log_operation function."""
        # Mock logger
        with patch("packages.shared.src.memory.telemetry.telemetry.logger") as mock_logger:
            # Log operation
            log_operation(
                level=20,  # INFO
                message="Test message",
                operation="test_operation",
                user_id="user123"
            )
            
            # Check that logger was called
            mock_logger.log.assert_called_once_with(
                20,
                "Test message",
                extra={"data": {"operation": "test_operation", "user_id": "user123"}}
            )