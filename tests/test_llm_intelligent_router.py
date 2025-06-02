"""
Unit tests for the Intelligent LLM Router
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from core.llm_intelligent_router import (
    IntelligentLLMRouter,
    QueryClassifier,
    QueryType,
    ModelProfile,
    RoutingDecision
)

class TestQueryClassifier:
    """Test the query classification functionality"""
    
    @pytest.fixture
    def classifier(self):
        return QueryClassifier()
    
    @pytest.mark.asyncio
    async def test_creative_query_classification(self, classifier):
        """Test classification of creative queries"""
        queries = [
            "Write a creative story about dragons",
            "Imagine a world where AI rules",
            "Create a poem about love"
        ]
        
        for query in queries:
            result = await classifier.classify(query)
            assert result == QueryType.CREATIVE_SEARCH
    
    @pytest.mark.asyncio
    async def test_analytical_query_classification(self, classifier):
        """Test classification of analytical queries"""
        queries = [
            "Analyze the performance metrics",
            "Compare these two datasets",
            "Evaluate the effectiveness of the campaign"
        ]
        
        for query in queries:
            result = await classifier.classify(query)
            assert result == QueryType.ANALYTICAL
    
    @pytest.mark.asyncio
    async def test_deep_search_classification(self, classifier):
        """Test classification of deep search queries"""
        queries = [
            "Research the history of quantum computing",
            "Provide a comprehensive analysis of climate change",
            "Detailed investigation of market trends"
        ]
        
        for query in queries:
            result = await classifier.classify(query)
            assert result == QueryType.DEEP_SEARCH
    
    @pytest.mark.asyncio
    async def test_code_generation_classification(self, classifier):
        """Test classification of code generation queries"""
        queries = [
            "Write a Python function to sort a list",
            "Debug this JavaScript code",
            "Implement a binary search algorithm"
        ]
        
        for query in queries:
            result = await classifier.classify(query)
            assert result == QueryType.CODE_GENERATION
    
    @pytest.mark.asyncio
    async def test_context_override(self, classifier):
        """Test that context can override classification"""
        query = "Tell me about something"
        context = {"query_type": QueryType.SUPER_DEEP_SEARCH.value}
        
        result = await classifier.classify(query, context)
        assert result == QueryType.SUPER_DEEP_SEARCH

class TestIntelligentLLMRouter:
    """Test the intelligent routing functionality"""
    
    @pytest.fixture
    def router(self):
        with patch('core.llm_intelligent_router.DynamicLLMRouter.__init__', return_value=None):
            router = IntelligentLLMRouter()
            router.config = Mock()
            router.config.portkey_api_key = "test_key"
            router.config.openrouter_api_key = "test_key"
            return router
    
    @pytest.mark.asyncio
    async def test_model_selection_for_creative_query(self, router):
        """Test that creative queries select appropriate models"""
        decision = await router._select_optimal_model(QueryType.CREATIVE_SEARCH)
        
        assert decision.primary_model in ["claude-3-opus-20240229", "gpt-4"]
        assert decision.temperature >= 0.7
        assert decision.max_tokens >= 2000
        assert "creative_search" in decision.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_model_selection_for_analytical_query(self, router):
        """Test that analytical queries select appropriate models"""
        decision = await router._select_optimal_model(QueryType.ANALYTICAL)
        
        assert decision.temperature <= 0.3
        assert decision.max_tokens >= 3000
        assert "analytical" in decision.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_performance_tracking(self, router):
        """Test that performance metrics are tracked correctly"""
        model_id = "gpt-3.5-turbo"
        
        # Simulate successful request
        router.performance_cache[model_id]["latencies"].append(100)
        router.performance_cache[model_id]["successes"] += 1
        
        # Check metrics
        assert len(router.performance_cache[model_id]["latencies"]) == 1
        assert router.performance_cache[model_id]["successes"] == 1
        assert router.performance_cache[model_id]["failures"] == 0
    
    @pytest.mark.asyncio
    async def test_routing_history(self, router):
        """Test that routing decisions are recorded"""
        with patch.object(router, 'classifier') as mock_classifier:
            mock_classifier.classify = AsyncMock(return_value=QueryType.CONVERSATIONAL)
            
            with patch.object(router, '_select_optimal_model') as mock_select:
                mock_select.return_value = RoutingDecision(
                    primary_model="gpt-3.5-turbo",
                    fallback_models=["claude-3-sonnet-20240229"],
                    temperature=0.7,
                    max_tokens=1000,
                    reasoning="Test reasoning",
                    estimated_cost=0.001,
                    estimated_latency_ms=500
                )
                
                with patch('core.llm_intelligent_router.DynamicLLMRouter.complete') as mock_complete:
                    mock_complete.return_value = {
                        "choices": [{"message": {"content": "Test response"}}],
                        "model": "gpt-3.5-turbo"
                    }
                    
                    await router.route_query("Test query")
                    
                    assert len(router.routing_history) == 1
                    assert router.routing_history[0]["query_type"] == QueryType.CONVERSATIONAL.value
    
    @pytest.mark.asyncio
    async def test_failover_mechanism(self, router):
        """Test that failover works when primary model fails"""
        with patch.object(router, 'classifier') as mock_classifier:
            mock_classifier.classify = AsyncMock(return_value=QueryType.CONVERSATIONAL)
            
            with patch.object(router, '_select_optimal_model') as mock_select:
                mock_select.return_value = RoutingDecision(
                    primary_model="gpt-4",
                    fallback_models=["gpt-3.5-turbo", "claude-3-sonnet-20240229"],
                    temperature=0.7,
                    max_tokens=1000,
                    reasoning="Test reasoning",
                    estimated_cost=0.001,
                    estimated_latency_ms=500
                )
                
                with patch('core.llm_intelligent_router.DynamicLLMRouter.complete') as mock_complete:
                    # First call fails, second succeeds
                    mock_complete.side_effect = [
                        Exception("Model failed"),
                        {"choices": [{"message": {"content": "Fallback response"}}], "model": "gpt-3.5-turbo"}
                    ]
                    
                    result = await router.route_query("Test query")
                    
                    assert result["routing_metadata"]["model_used"] == "gpt-3.5-turbo"
                    assert mock_complete.call_count == 2
    
    @pytest.mark.asyncio
    async def test_analytics_generation(self, router):
        """Test analytics data generation"""
        # Add some test data
        router.routing_history = [
            {"query_type": "creative_search", "timestamp": datetime.utcnow()},
            {"query_type": "analytical", "timestamp": datetime.utcnow()},
            {"query_type": "creative_search", "timestamp": datetime.utcnow()}
        ]
        
        router.performance_cache["gpt-3.5-turbo"] = {
            "latencies": [100, 200, 150],
            "successes": 3,
            "failures": 0
        }
        
        analytics = await router.get_routing_analytics()
        
        assert analytics["query_type_distribution"]["creative_search"] == 2
        assert analytics["query_type_distribution"]["analytical"] == 1
        assert "gpt-3.5-turbo" in analytics["model_performance"]
        assert analytics["total_queries_routed"] == 3

@pytest.mark.asyncio
async def test_model_profile_initialization():
    """Test that model profiles are initialized correctly"""
    with patch('core.llm_intelligent_router.DynamicLLMRouter.__init__', return_value=None):
        router = IntelligentLLMRouter()
        
        # Check that key models are present
        assert "gpt-4-turbo-preview" in router.model_profiles
        assert "claude-3-opus-20240229" in router.model_profiles
        assert "gpt-3.5-turbo" in router.model_profiles
        
        # Check model capabilities
        gpt4_profile = router.model_profiles["gpt-4-turbo-preview"]
        assert QueryType.DEEP_SEARCH in gpt4_profile.strengths
        assert gpt4_profile.supports_tools is True
        assert gpt4_profile.supports_vision is True
        assert gpt4_profile.max_tokens == 128000

if __name__ == "__main__":
    pytest.main([__file__, "-v"])