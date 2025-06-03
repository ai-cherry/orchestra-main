"""Tests for Roo AI Orchestrator integration."""

import asyncio
import json
import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import Response

from ai_components.orchestration.mode_transition_manager import (
    ModeTransitionManager,
    TransitionState,
    TransitionType,
)
from ai_components.orchestration.roo_mcp_adapter import (
    RooContext,
    RooMCPAdapter,
    RooMode,
)
from ai_components.orchestration.unified_api_router import (
    CircuitState,
    ServiceType,
    UnifiedAPIRouter,
)


class TestRooMCPAdapter:
    """Test cases for RooMCPAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create adapter instance."""
        return RooMCPAdapter("test_api_key")

    @pytest.mark.asyncio
    async def test_wrap_mode_as_agent(self, adapter):
        """Test wrapping Roo mode as MCP agent."""
        agent_id, capabilities = await adapter.wrap_mode_as_agent(RooMode.CODE)

        assert agent_id == "roo_code_agent"
        assert len(capabilities) == 5
        assert any(cap.name == "code_generation" for cap in capabilities)

    @pytest.mark.asyncio
    async def test_transform_context_roo_to_mcp(self, adapter):
        """Test context transformation from Roo to MCP format."""
        roo_context = {
            "mode": "code",
            "task": "Write a function",
            "history": [{"role": "user", "content": "Test"}],
            "files": ["test.py"],
            "environment": {"os": "linux"},
        }

        mcp_context = await adapter.transform_context("roo", "mcp", roo_context)

        assert mcp_context["agent_id"] == "roo_code_agent"
        assert mcp_context["messages"][0]["content"] == "Write a function"
        assert len(mcp_context["resources"]) == 1
        assert mcp_context["metadata"]["mode"] == "code"

    @pytest.mark.asyncio
    async def test_transform_context_mcp_to_roo(self, adapter):
        """Test context transformation from MCP to Roo format."""
        mcp_context = {
            "agent_id": "roo_code_agent",
            "task_id": "task_123",
            "messages": [
                {"role": "user", "content": "Write a function"},
                {"role": "assistant", "content": "Here's the function"},
            ],
            "resources": [{"type": "file", "path": "test.py"}],
            "metadata": {"mode": "code", "environment": {"os": "linux"}},
        }

        roo_context = await adapter.transform_context("mcp", "roo", mcp_context)

        assert roo_context["mode"] == "code"
        assert roo_context["task"] == "Write a function"
        assert len(roo_context["history"]) == 1
        assert roo_context["files"] == ["test.py"]

    @pytest.mark.asyncio
    async def test_execute_mode_task(self, adapter):
        """Test executing a task with a specific mode."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Task completed"}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(adapter.client, "post", return_value=mock_response):
            with patch("shared.database.UnifiedDatabase") as mock_db:
                mock_db.return_value.__aenter__.return_value.execute = AsyncMock()

                result = await adapter.execute_mode_task(
                    RooMode.CODE, "Write a test function"
                )

                assert result["result"] == "Task completed"
                assert result["mode"] == "code"

    @pytest.mark.asyncio
    async def test_session_management(self, adapter):
        """Test session creation and management."""
        session_id = await adapter.create_session(RooMode.CODE, "Test task")

        assert session_id.startswith("session_")
        assert session_id in adapter.active_sessions

        await adapter.update_session(
            session_id, {"role": "assistant", "content": "Response"}
        )

        assert len(adapter.active_sessions[session_id].history) == 1

        await adapter.close_session(session_id)
        assert session_id not in adapter.active_sessions


class TestUnifiedAPIRouter:
    """Test cases for UnifiedAPIRouter."""

    @pytest.fixture
    def router(self):
        """Create router instance."""
        return UnifiedAPIRouter(
            "test_api_key", "http://localhost:8000", "https://openrouter.ai/api/v1"
        )

    @pytest.mark.asyncio
    async def test_routing_decision_orchestrator(self, router):
        """Test routing decision for orchestrator tasks."""
        decision = router._make_routing_decision(
            "workflow", {"task": "coordinate multiple agents"}
        )

        assert decision.service == ServiceType.ORCHESTRATOR
        assert decision.confidence > 0
        assert ServiceType.OPENROUTER in decision.fallback_options

    @pytest.mark.asyncio
    async def test_routing_decision_openrouter(self, router):
        """Test routing decision for direct model calls."""
        decision = router._make_routing_decision(
            "completion", {"prompt": "Generate text"}
        )

        assert decision.service == ServiceType.OPENROUTER
        assert ServiceType.ORCHESTRATOR in decision.fallback_options

    def test_circuit_breaker_functionality(self, router):
        """Test circuit breaker state transitions."""
        breaker = router.circuit_breakers[ServiceType.OPENROUTER]

        # Initially closed
        assert breaker.state == CircuitState.CLOSED
        assert breaker.can_request()

        # Record failures
        for _ in range(5):
            breaker.record_failure()

        # Should be open after threshold
        assert breaker.state == CircuitState.OPEN
        assert not breaker.can_request()

        # Test recovery timeout
        breaker.last_failure_time = datetime.utcnow()
        breaker.recovery_timeout = -1  # Force immediate recovery
        assert breaker.can_request()
        assert breaker.state == CircuitState.HALF_OPEN

    def test_retry_strategy(self, router):
        """Test retry strategy with exponential backoff."""
        strategy = router.retry_strategies[ServiceType.OPENROUTER]

        delays = [strategy.get_delay(i) for i in range(4)]

        assert delays[0] == 1.0  # Base delay
        assert delays[1] == 2.0  # 1 * 2^1
        assert delays[2] == 4.0  # 1 * 2^2
        assert delays[3] == 8.0  # 1 * 2^3

    @pytest.mark.asyncio
    async def test_route_request_with_fallback(self, router):
        """Test request routing with fallback."""
        # Mock failed primary service
        async def mock_call_orchestrator(*args, **kwargs):
            raise Exception("Service unavailable")

        # Mock successful fallback
        async def mock_call_openrouter(*args, **kwargs):
            return {"result": "success"}

        router._call_orchestrator = mock_call_orchestrator
        router._call_openrouter = mock_call_openrouter

        response, decision = await router.route_request(
            "workflow", {"task": "test"}
        )

        assert response["result"] == "success"
        assert decision.service == ServiceType.OPENROUTER
        assert "Fallback" in decision.reason


class TestModeTransitionManager:
    """Test cases for ModeTransitionManager."""

    @pytest.fixture
    def manager(self):
        """Create transition manager instance."""
        return ModeTransitionManager()

    @pytest.mark.asyncio
    async def test_initiate_transition(self, manager):
        """Test initiating a mode transition."""
        with patch("shared.database.UnifiedDatabase") as mock_db:
            mock_db.return_value.__aenter__.return_value.execute = AsyncMock()

            transition_id = await manager.initiate_transition(
                "session_123",
                RooMode.CODE,
                RooMode.DEBUG,
                {"task": "Debug error", "error": "Test error"},
            )

            assert transition_id.startswith("trans_")
            assert transition_id in manager.active_transitions
            assert len(manager.transition_history) == 1

    @pytest.mark.asyncio
    async def test_execute_transition(self, manager):
        """Test executing a transition."""
        with patch("shared.database.UnifiedDatabase") as mock_db:
            mock_db.return_value.__aenter__.return_value.execute = AsyncMock()

            # First initiate
            transition_id = await manager.initiate_transition(
                "session_123",
                RooMode.CODE,
                RooMode.DEBUG,
                {"task": "Debug error"},
            )

            # Then execute
            context = await manager.execute_transition(transition_id)

            assert context.from_mode == RooMode.CODE
            assert context.to_mode == RooMode.DEBUG
            assert "handoff_time" in context.artifacts

            # Check history updated
            history = next(
                h for h in manager.transition_history if h.id == transition_id
            )
            assert history.state == TransitionState.COMPLETED
            assert history.duration_ms is not None

    @pytest.mark.asyncio
    async def test_suggest_transition(self, manager):
        """Test automatic transition suggestions."""
        # Test code error to debug suggestion
        suggestion = await manager.suggest_transition(
            "session_123",
            RooMode.CODE,
            {"last_result": {"error": "Syntax error"}},
        )

        assert suggestion is not None
        assert suggestion[0] == RooMode.DEBUG
        assert "debug" in suggestion[1].lower()

        # Test no suggestion case
        no_suggestion = await manager.suggest_transition(
            "session_123", RooMode.ASK, {"normal": "context"}
        )

        assert no_suggestion is None

    @pytest.mark.asyncio
    async def test_transition_patterns_analysis(self, manager):
        """Test analyzing transition patterns."""
        with patch("shared.database.UnifiedDatabase") as mock_db:
            mock_fetch = AsyncMock(
                return_value=[
                    {
                        "from_mode": "code",
                        "to_mode": "debug",
                        "count": 10,
                        "avg_duration": 500,
                        "failures": 1,
                    }
                ]
            )
            mock_db.return_value.__aenter__.return_value.fetch_all = mock_fetch

            analysis = await manager.analyze_transition_patterns()

            assert "transition_stats" in analysis
            assert "success_rates" in analysis
            assert analysis["total_transitions"] == 10

    def test_preserve_context(self, manager):
        """Test context preservation during transitions."""
        from ai_components.orchestration.mode_transition_manager import (
            TransitionContext,
        )

        transition = TransitionContext(
            session_id="test_123",
            from_mode=RooMode.CODE,
            to_mode=RooMode.DEBUG,
            task="Debug code",
            artifacts={"last_code": "def test(): pass", "errors": ["SyntaxError"]},
            files=["test.py"],
        )

        # Run synchronously for testing
        preserved = asyncio.run(manager._preserve_context(transition))

        assert preserved["session_id"] == "test_123"
        assert preserved["from_mode"] == "code"
        assert "code_context" in preserved
        assert preserved["code_context"]["last_code"] == "def test(): pass"
        assert len(preserved["code_context"]["errors"]) == 1


class TestIntegration:
    """Integration tests for the complete Roo orchestrator system."""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete workflow from request to execution."""
        # This would be a more comprehensive integration test
        # involving all components working together
        pass

    @pytest.mark.asyncio
    async def test_mode_transition_with_context_sync(self):
        """Test mode transition with bidirectional context sync."""
        # Test the full flow of transitioning between modes
        # while maintaining context through UnifiedContextManager
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])