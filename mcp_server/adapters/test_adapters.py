"""Tests for Factory AI MCP Server Adapters.

This module contains comprehensive tests for all adapter implementations,
including circuit breaker functionality, metrics collection, and fallback mechanisms.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

from mcp_server.adapters import (
    FactoryMCPAdapter,
    CircuitBreaker,
    CircuitBreakerError,
    ArchitectAdapter,
    CodeAdapter,
    DebugAdapter,
    ReliabilityAdapter,
    KnowledgeAdapter,
)
from mcp_server.adapters.factory_mcp_adapter import CircuitState


class MockMCPServer:
    """Mock MCP server for testing."""

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Mock request handler."""
        return {"result": {"mock": True, "method": request.get("method")}}


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state allows calls."""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

        async def success_func():
            return "success"

        result = await cb.call(success_func)
        assert result == "success"
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures."""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

        async def failing_func():
            raise Exception("Test failure")

        # Fail 3 times to open circuit
        for _ in range(3):
            with pytest.raises(Exception):
                await cb.call(failing_func)

        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 3

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_after_timeout(self):
        """Test circuit breaker enters half-open state after timeout."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=1)

        async def failing_func():
            raise Exception("Test failure")

        # Open the circuit
        with pytest.raises(Exception):
            await cb.call(failing_func)

        # Wait for recovery timeout
        await asyncio.sleep(1.1)

        # Should attempt reset on next call
        async def success_func():
            return "recovered"

        result = await cb.call(success_func)
        assert result == "recovered"
        assert cb.state == CircuitState.CLOSED


class TestFactoryMCPAdapter:
    """Test base adapter functionality."""

    @pytest.fixture
    def mock_adapter(self):
        """Create a mock adapter for testing."""

        class TestAdapter(FactoryMCPAdapter):
            async def translate_to_factory(self, mcp_request: Dict[str, Any]) -> Dict[str, Any]:
                return {"translated": "to_factory", **mcp_request}

            async def translate_to_mcp(self, factory_response: Dict[str, Any]) -> Dict[str, Any]:
                return {"translated": "to_mcp", **factory_response}

            async def _call_factory_droid(self, factory_request: Dict[str, Any]) -> Dict[str, Any]:
                return {"result": {"success": True}}

        mcp_server = MockMCPServer()
        droid_config = {"failure_threshold": 3, "recovery_timeout": 60}
        return TestAdapter(mcp_server, droid_config, "test")

    @pytest.mark.asyncio
    async def test_successful_request_processing(self, mock_adapter):
        """Test successful request processing through adapter."""
        request = {"method": "test_method", "params": {"test": "value"}}

        response = await mock_adapter.process_request(request)

        assert "translated" in response
        assert response["translated"] == "to_mcp"
        assert mock_adapter.metrics["requests"] == 1
        assert mock_adapter.metrics["successes"] == 1
        assert mock_adapter.metrics["failures"] == 0

    @pytest.mark.asyncio
    async def test_fallback_on_error(self, mock_adapter):
        """Test fallback to MCP server on error."""
        # Make factory call fail
        mock_adapter._call_factory_droid = AsyncMock(side_effect=Exception("Factory error"))

        request = {"method": "test_method", "params": {"test": "value"}}
        response = await mock_adapter.process_request(request)

        # Should fallback to MCP server
        assert response["result"]["mock"] is True
        assert mock_adapter.metrics["failures"] == 1
        assert mock_adapter.metrics["fallback_count"] == 1

    def test_metrics_calculation(self, mock_adapter):
        """Test metrics calculation."""
        mock_adapter.metrics = {
            "requests": 100,
            "successes": 85,
            "failures": 15,
            "total_latency": 50.0,
            "fallback_count": 5,
        }

        metrics = mock_adapter.get_metrics()

        assert metrics["total_requests"] == 100
        assert metrics["successful_requests"] == 85
        assert metrics["failed_requests"] == 15
        assert metrics["average_latency_seconds"] == 0.5
        assert metrics["success_rate"] == 0.85


class TestArchitectAdapter:
    """Test Architect adapter functionality."""

    @pytest.fixture
    def architect_adapter(self):
        """Create Architect adapter for testing."""
        mcp_server = MockMCPServer()
        droid_config = {"api_key": "test_key"}
        return ArchitectAdapter(mcp_server, droid_config)

    @pytest.mark.asyncio
    async def test_design_system_translation(self, architect_adapter):
        """Test design system request translation."""
        mcp_request = {
            "method": "design_system",
            "params": {
                "project_type": "microservices",
                "requirements": ["scalable", "fault-tolerant"],
                "cloud_provider": "vultr",
            },
        }

        factory_request = await architect_adapter.translate_to_factory(mcp_request)

        assert factory_request["droid"] == "architect"
        assert factory_request["action"] == "design_architecture"
        assert factory_request["context"]["project_type"] == "microservices"
        assert factory_request["options"]["cloud_provider"] == "vultr"

    @pytest.mark.asyncio
    async def test_infrastructure_generation(self, architect_adapter):
        """Test infrastructure code generation translation."""
        mcp_request = {
            "method": "generate_infrastructure",
            "params": {
                "stack_name": "production",
                "resources": ["vpc", "instances", "database"],
                "pulumi_config": {"region": "ewr"},
            },
        }

        factory_request = await architect_adapter.translate_to_factory(mcp_request)

        assert factory_request["action"] == "generate_iac"
        assert factory_request["context"]["stack_name"] == "production"
        assert factory_request["options"]["pulumi_config"]["region"] == "ewr"


class TestCodeAdapter:
    """Test Code adapter functionality."""

    @pytest.fixture
    def code_adapter(self):
        """Create Code adapter for testing."""
        mcp_server = MockMCPServer()
        droid_config = {"streaming": True, "chunk_size": 1024}
        return CodeAdapter(mcp_server, droid_config)

    @pytest.mark.asyncio
    async def test_code_generation_translation(self, code_adapter):
        """Test code generation request translation."""
        mcp_request = {
            "method": "generate_code",
            "params": {
                "language": "python",
                "requirements": ["async", "type hints"],
                "template": "fastapi_endpoint",
            },
        }

        factory_request = await code_adapter.translate_to_factory(mcp_request)

        assert factory_request["droid"] == "code"
        assert factory_request["action"] == "generate"
        assert factory_request["context"]["language"] == "python"
        assert factory_request["context"]["template"] == "fastapi_endpoint"

    @pytest.mark.asyncio
    async def test_streaming_response_handling(self, code_adapter):
        """Test streaming response handling."""
        factory_response = {
            "result": {
                "streaming": True,
                "stream_id": "stream_123",
            }
        }

        mcp_response = await code_adapter.translate_to_mcp(factory_response)

        assert mcp_response["result"]["streaming"] is True
        assert mcp_response["result"]["stream_id"] == "stream_123"


class TestDebugAdapter:
    """Test Debug adapter functionality."""

    @pytest.fixture
    def debug_adapter(self):
        """Create Debug adapter for testing."""
        mcp_server = MockMCPServer()
        droid_config = {"profiling_enabled": True, "max_stack_depth": 50}
        return DebugAdapter(mcp_server, droid_config)

    @pytest.mark.asyncio
    async def test_error_diagnosis_translation(self, debug_adapter):
        """Test error diagnosis request translation."""
        mcp_request = {
            "method": "diagnose_error",
            "params": {
                "error_type": "ConnectionError",
                "stack_trace": "Traceback...",
                "environment": "production",
            },
        }

        factory_request = await debug_adapter.translate_to_factory(mcp_request)

        assert factory_request["droid"] == "debug"
        assert factory_request["action"] == "diagnose"
        assert factory_request["context"]["error_type"] == "ConnectionError"
        assert factory_request["options"]["deep_analysis"] is True

    @pytest.mark.asyncio
    async def test_query_optimization_translation(self, debug_adapter):
        """Test query optimization request translation."""
        mcp_request = {
            "method": "optimize_query",
            "params": {
                "query": "SELECT * FROM users WHERE...",
                "query_type": "sql",
                "schema": {"users": ["id", "name", "email"]},
            },
        }

        factory_request = await debug_adapter.translate_to_factory(mcp_request)

        assert factory_request["action"] == "optimize_query"
        assert factory_request["context"]["query_type"] == "sql"
        assert "users" in factory_request["context"]["schema"]


class TestReliabilityAdapter:
    """Test Reliability adapter functionality."""

    @pytest.fixture
    def reliability_adapter(self):
        """Create Reliability adapter for testing."""
        mcp_server = MockMCPServer()
        droid_config = {"alert_threshold": 5, "auto_remediation": True}
        return ReliabilityAdapter(mcp_server, droid_config)

    @pytest.mark.asyncio
    async def test_incident_detection_translation(self, reliability_adapter):
        """Test incident detection request translation."""
        mcp_request = {
            "method": "detect_incident",
            "params": {
                "system_state": {"cpu": 95, "memory": 85},
                "alerts": [{"type": "high_cpu", "severity": "high"}],
            },
        }

        factory_request = await reliability_adapter.translate_to_factory(mcp_request)

        assert factory_request["droid"] == "reliability"
        assert factory_request["action"] == "detect"
        assert factory_request["context"]["system_state"]["cpu"] == 95
        assert factory_request["options"]["auto_remediate"] is True

    @pytest.mark.asyncio
    async def test_alert_aggregation(self, reliability_adapter):
        """Test alert aggregation functionality."""
        alerts = [
            {"id": "alert1", "message": "High CPU"},
            {"id": "alert2", "message": "High Memory"},
            {"id": "alert3", "message": "Disk Space Low"},
        ]

        # Add alerts to buffer
        reliability_adapter.alert_buffer = alerts

        # Process when threshold is reached
        reliability_adapter.alert_threshold = 3
        result = await reliability_adapter.process_alert_stream([])

        assert "result" in result
        assert len(reliability_adapter.alert_buffer) == 0  # Buffer cleared


class TestKnowledgeAdapter:
    """Test Knowledge adapter functionality."""

    @pytest.fixture
    def knowledge_adapter(self):
        """Create Knowledge adapter for testing."""
        mcp_server = MockMCPServer()
        droid_config = {
            "vector_dimension": 1536,
            "embedding_model": "text-embedding-ada-002",
            "cache_embeddings": True,
        }
        return KnowledgeAdapter(mcp_server, droid_config)

    @pytest.mark.asyncio
    async def test_store_knowledge_translation(self, knowledge_adapter):
        """Test store knowledge request translation."""
        mcp_request = {
            "method": "store_knowledge",
            "params": {
                "content": "PostgreSQL best practices...",
                "collection": "documentation",
                "metadata": {"category": "database"},
            },
        }

        factory_request = await knowledge_adapter.translate_to_factory(mcp_request)

        assert factory_request["droid"] == "knowledge"
        assert factory_request["action"] == "store"
        assert factory_request["context"]["collection"] == "documentation"
        assert factory_request["options"]["auto_chunk"] is True

    @pytest.mark.asyncio
    async def test_search_knowledge_translation(self, knowledge_adapter):
        """Test search knowledge request translation."""
        mcp_request = {
            "method": "search_knowledge",
            "params": {
                "query": "connection pooling",
                "search_type": "semantic",
                "max_results": 5,
            },
        }

        factory_request = await knowledge_adapter.translate_to_factory(mcp_request)

        assert factory_request["action"] == "search"
        assert factory_request["context"]["query"] == "connection pooling"
        assert factory_request["options"]["max_results"] == 5

    @pytest.mark.asyncio
    async def test_embedding_cache(self, knowledge_adapter):
        """Test embedding cache functionality."""
        documents = [
            {"content": "Test document 1"},
            {"content": "Test document 2"},
        ]

        # Pre-populate cache
        knowledge_adapter.embedding_cache["Test document 1"] = [0.1] * 1536

        result = await knowledge_adapter.optimize_embeddings(documents)

        assert result["result"]["cache_stats"]["cached"] == 1
        assert result["result"]["cache_stats"]["processed"] == 1


# Integration tests
class TestIntegration:
    """Integration tests for adapter system."""

    @pytest.mark.asyncio
    async def test_adapter_health_checks(self):
        """Test health check functionality across all adapters."""
        mcp_server = MockMCPServer()
        droid_config = {"api_key": "test"}

        adapters = [
            ArchitectAdapter(mcp_server, droid_config),
            CodeAdapter(mcp_server, droid_config),
            DebugAdapter(mcp_server, droid_config),
            ReliabilityAdapter(mcp_server, droid_config),
            KnowledgeAdapter(mcp_server, droid_config),
        ]

        for adapter in adapters:
            health = await adapter.health_check()
            assert "healthy" in health
            assert "metrics" in health
            assert "timestamp" in health

    @pytest.mark.asyncio
    async def test_circuit_breaker_across_adapters(self):
        """Test circuit breaker behavior is consistent across adapters."""
        mcp_server = MockMCPServer()
        droid_config = {"failure_threshold": 2, "recovery_timeout": 1}

        adapters = [
            ArchitectAdapter(mcp_server, droid_config),
            CodeAdapter(mcp_server, droid_config),
        ]

        for adapter in adapters:
            # Make factory calls fail
            adapter._call_factory_droid = AsyncMock(side_effect=Exception("Test failure"))

            # Process requests until circuit opens
            for _ in range(3):
                response = await adapter.process_request({"method": "test"})
                assert "result" in response  # Should fallback

            # Circuit should be open
            assert adapter.circuit_breaker.state == CircuitState.OPEN
            assert adapter.metrics["fallback_count"] >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
