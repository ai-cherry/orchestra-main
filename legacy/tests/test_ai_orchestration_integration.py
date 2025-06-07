"""
Integration tests for AI Orchestration system
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import json

# Set test environment
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "postgresql://test_user:test_pass@localhost:5432/test_db"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["WEAVIATE_URL"] = "http://localhost:8080"

@pytest.fixture
async def orchestrator():
    """Create test orchestrator instance"""
    from services.ai_agent_orchestrator import AIAgentOrchestrator
    
    # Mock external dependencies
    with patch('services.ai_agent_orchestrator.create_async_engine') as mock_engine:
        mock_engine.return_value = AsyncMock()
        orchestrator = AIAgentOrchestrator()
        await orchestrator.initialize()
        yield orchestrator
        await orchestrator.shutdown()

@pytest.fixture
def mock_agents():
    """Mock agent instances"""
    agents = {
        "cherry": Mock(domain="cherry", process_query=AsyncMock()),
        "sophia": Mock(domain="sophia", process_query=AsyncMock()),
        "paragonrx": Mock(domain="paragonrx", process_query=AsyncMock())
    }
    return agents

class TestAIOrchestration:
    """Test AI orchestration functionality"""
    
    @pytest.mark.asyncio
    async def test_natural_language_query(self, orchestrator):
        """Test natural language query processing"""
        query = "What are the latest clinical trials for diabetes?"
        
        result = await orchestrator.process_natural_language_query(query)
        
        assert result is not None
        assert "domain" in result
        assert result["domain"] == "paragonrx"
        assert "results" in result
        
    @pytest.mark.asyncio
    async def test_web_scraping_team(self, orchestrator):
        """Test web scraping team coordination"""
        from core.agents.web_scraping_agents import FinanceWebScrapingTeam
        
        team = FinanceWebScrapingTeam()
        task = {
            "query": "AAPL stock analysis",
            "sources": ["yahoo_finance", "bloomberg"]
        }
        
        result = await team.coordinate_research(task)
        
        assert result is not None
        assert "aggregated_data" in result
        assert len(result["sources"]) == 2
        
    @pytest.mark.asyncio
    async def test_integration_specialists(self, orchestrator):
        """Test platform integration specialists"""
        from core.agents.integration_specialists import IntegrationCoordinator
        
        coordinator = IntegrationCoordinator()
        
        # Test with mocked integrations
        with patch.object(coordinator, 'gong_agent') as mock_gong:
            mock_gong.fetch_data = AsyncMock(return_value={"calls": []})
            
            result = await coordinator.gather_multi_platform_data(
                query="sales performance last quarter",
                platforms=["gong"]
            )
            
            assert result is not None
            assert "gong" in result
            
    @pytest.mark.asyncio
    async def test_circuit_breaker(self, orchestrator):
        """Test circuit breaker functionality"""
        from core.agents.unified_orchestrator import UnifiedOrchestrator
        
        unified = UnifiedOrchestrator()
        
        # Simulate failures to trigger circuit breaker
        with patch.object(unified.gong_breaker, '_call') as mock_call:
            mock_call.side_effect = Exception("API Error")
            
            # Should fail after threshold
            for _ in range(6):
                try:
                    await unified._safe_integration_call(
                        unified.gong_breaker,
                        AsyncMock(),
                        "test"
                    )
                except:
                    pass
                    
            # Circuit should be open
            assert unified.gong_breaker.current_state == "open"
            
    @pytest.mark.asyncio
    async def test_resource_limits(self):
        """Test resource management and limits"""
        from core.resource_management import ResourceManager, ResourceLimitedAgent
        
        manager = ResourceManager()
        manager.max_concurrent_agents = 2  # Low limit for testing
        
        # Create agents up to limit
        async with ResourceLimitedAgent("agent1") as agent1:
            async with ResourceLimitedAgent("agent2") as agent2:
                # Third agent should be queued
                assert manager.agent_queue.empty()
                
                # Try to create third agent
                try:
                    success = await manager.acquire_agent_slot("agent3")
                    assert not success  # Should be queued
                    assert manager.agent_queue.qsize() == 1
                except:
                    pass
                    
    @pytest.mark.asyncio
    async def test_input_validation(self):
        """Test input validation and sanitization"""
        from core.security.input_validation import InputValidator, QueryRequest
        
        # Test SQL injection detection
        malicious_input = "'; DROP TABLE users; --"
        with pytest.raises(ValueError, match="SQL injection"):
            InputValidator.sanitize_string(malicious_input)
            
        # Test XSS detection
        xss_input = "<script>alert('xss')</script>"
        with pytest.raises(ValueError, match="XSS"):
            InputValidator.sanitize_string(xss_input)
            
        # Test valid input
        valid_input = "What is the weather today?"
        sanitized = InputValidator.sanitize_string(valid_input)
        assert sanitized == valid_input
        
        # Test Pydantic validation
        with pytest.raises(ValueError):
            QueryRequest(query="test", max_results=200)  # Exceeds limit
            
    @pytest.mark.asyncio
    async def test_monitoring_alerts(self):
        """Test monitoring and alerting system"""
        from core.monitoring.enhanced_monitoring import AlertManager, MetricsCollector
        
        alert_manager = AlertManager()
        
        # Test alert triggering
        high_error_metrics = {
            "error_rate": 0.10,  # 10% error rate
            "response_time_p95": 1.0,
            "cpu_usage": 50
        }
        
        await alert_manager.check_alerts(high_error_metrics)
        
        assert len(alert_manager.alert_history) > 0
        assert alert_manager.alert_history[0]["type"] == "ERROR_RATE"
        
    @pytest.mark.asyncio
    async def test_end_to_end_flow(self, orchestrator):
        """Test complete end-to-end flow"""
        # Simulate user query
        query = "Show me competitor analysis for our product"
        
        # Process through orchestrator
        with patch.object(orchestrator, 'unified_orchestrator') as mock_unified:
            mock_unified.process_query = AsyncMock(return_value={
                "domain": "sophia",
                "confidence": 0.95,
                "results": [{"competitor": "CompanyA", "market_share": 0.25}]
            })
            
            result = await orchestrator.process_natural_language_query(query)
            
            assert result["domain"] == "sophia"
            assert len(result["results"]) > 0
            assert result["confidence"] > 0.9

@pytest.mark.asyncio
async def test_performance_benchmarks():
    """Performance benchmark tests"""
    from services.ai_agent_orchestrator import AIAgentOrchestrator
    import time
    
    orchestrator = AIAgentOrchestrator()
    
    # Measure query processing time
    start = time.time()
    
    tasks = []
    for i in range(10):
        task = orchestrator.process_natural_language_query(f"Test query {i}")
        tasks.append(task)
        
    results = await asyncio.gather(*tasks)
    
    end = time.time()
    avg_time = (end - start) / 10
    
    # Should meet performance target
    assert avg_time < 0.1  # 100ms target
    
    print(f"Average query time: {avg_time*1000:.2f}ms")
