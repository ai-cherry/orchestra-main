"""
Intelligent LLM Router with Query Classification and Dynamic Model Selection

This module implements advanced routing logic for optimal LLM selection based on:
- Query type classification (creative, analytical, deep search, media)
- Cost optimization
- Performance metrics
- Latency-based failover
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging
import numpy as np
from dataclasses import dataclass
from collections import defaultdict

from core.llm_router_dynamic import DynamicLLMRouter, UseCase, ModelTier
from core.database.llm_config_models import LLMModel, LLMMetric

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Enhanced query classification types"""
    CREATIVE_SEARCH = "creative_search"
    DEEP_SEARCH = "deep_search"
    SUPER_DEEP_SEARCH = "super_deep_search"
    ANALYTICAL = "analytical"
    CONVERSATIONAL = "conversational"
    CODE_GENERATION = "code_generation"
    IMAGE_GENERATION = "image_generation"
    VIDEO_GENERATION = "video_generation"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"


@dataclass
class ModelProfile:
    """Profile for model capabilities and performance"""
    model_id: str
    provider: str
    strengths: List[QueryType]
    temperature_range: Tuple[float, float]
    max_tokens: int
    cost_per_1k: float
    avg_latency_ms: float
    success_rate: float
    supports_tools: bool = False
    supports_vision: bool = False
    supports_streaming: bool = True


@dataclass
class RoutingDecision:
    """Routing decision with reasoning"""
    primary_model: str
    fallback_models: List[str]
    temperature: float
    max_tokens: int
    reasoning: str
    estimated_cost: float
    estimated_latency_ms: float


class QueryClassifier:
    """Classifies queries into appropriate types"""
    
    def __init__(self):
        # Keywords for classification
        self.creative_keywords = [
            "creative", "imagine", "story", "poem", "design", "brainstorm",
            "innovative", "unique", "artistic", "generate ideas"
        ]
        self.analytical_keywords = [
            "analyze", "compare", "evaluate", "assess", "examine", "investigate",
            "data", "statistics", "metrics", "performance"
        ]
        self.deep_search_keywords = [
            "research", "comprehensive", "detailed", "thorough", "in-depth",
            "academic", "scholarly", "evidence", "sources"
        ]
        self.code_keywords = [
            "code", "program", "function", "class", "debug", "implement",
            "algorithm", "script", "develop", "software"
        ]
        
    async def classify(self, query: str, context: Optional[Dict[str, Any]] = None) -> QueryType:
        """Classify query into appropriate type"""
        query_lower = query.lower()
        
        # Check for explicit type in context
        if context and "query_type" in context:
            return QueryType(context["query_type"])
        
        # Image/Video generation
        if any(word in query_lower for word in ["image", "picture", "draw", "visualize"]):
            return QueryType.IMAGE_GENERATION
        if any(word in query_lower for word in ["video", "animation", "motion"]):
            return QueryType.VIDEO_GENERATION
        
        # Code generation
        if any(word in query_lower for word in self.code_keywords):
            return QueryType.CODE_GENERATION
        
        # Deep search patterns
        if any(word in query_lower for word in self.deep_search_keywords):
            if "verify" in query_lower or "validate" in query_lower:
                return QueryType.SUPER_DEEP_SEARCH
            return QueryType.DEEP_SEARCH
        
        # Creative patterns
        if any(word in query_lower for word in self.creative_keywords):
            return QueryType.CREATIVE_SEARCH
        
        # Analytical patterns
        if any(word in query_lower for word in self.analytical_keywords):
            return QueryType.ANALYTICAL
        
        # Summarization
        if any(word in query_lower for word in ["summarize", "summary", "brief", "overview"]):
            return QueryType.SUMMARIZATION
        
        # Translation
        if any(word in query_lower for word in ["translate", "translation", "language"]):
            return QueryType.TRANSLATION
        
        # Default to conversational
        return QueryType.CONVERSATIONAL


class IntelligentLLMRouter(DynamicLLMRouter):
    """
    Enhanced LLM Router with intelligent query classification and routing
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.classifier = QueryClassifier()
        self.model_profiles = self._initialize_model_profiles()
        self.performance_cache = defaultdict(lambda: {"latencies": [], "successes": 0, "failures": 0})
        self.routing_history = []
        
    def _initialize_model_profiles(self) -> Dict[str, ModelProfile]:
        """Initialize model profiles with capabilities"""
        return {
            # OpenAI Models
            "gpt-4-turbo-preview": ModelProfile(
                model_id="gpt-4-turbo-preview",
                provider="openai",
                strengths=[QueryType.DEEP_SEARCH, QueryType.ANALYTICAL, QueryType.CODE_GENERATION],
                temperature_range=(0.0, 1.0),
                max_tokens=128000,
                cost_per_1k=0.01,
                avg_latency_ms=2000,
                success_rate=0.98,
                supports_tools=True,
                supports_vision=True
            ),
            "gpt-4": ModelProfile(
                model_id="gpt-4",
                provider="openai",
                strengths=[QueryType.SUPER_DEEP_SEARCH, QueryType.ANALYTICAL],
                temperature_range=(0.0, 1.0),
                max_tokens=8192,
                cost_per_1k=0.03,
                avg_latency_ms=3000,
                success_rate=0.99,
                supports_tools=True
            ),
            "gpt-3.5-turbo": ModelProfile(
                model_id="gpt-3.5-turbo",
                provider="openai",
                strengths=[QueryType.CONVERSATIONAL, QueryType.SUMMARIZATION],
                temperature_range=(0.0, 2.0),
                max_tokens=16384,
                cost_per_1k=0.0005,
                avg_latency_ms=500,
                success_rate=0.95
            ),
            
            # Anthropic Models
            "claude-3-opus-20240229": ModelProfile(
                model_id="claude-3-opus-20240229",
                provider="anthropic",
                strengths=[QueryType.CREATIVE_SEARCH, QueryType.DEEP_SEARCH],
                temperature_range=(0.0, 1.0),
                max_tokens=200000,
                cost_per_1k=0.015,
                avg_latency_ms=2500,
                success_rate=0.97,
                supports_vision=True
            ),
            "claude-3-sonnet-20240229": ModelProfile(
                model_id="claude-3-sonnet-20240229",
                provider="anthropic",
                strengths=[QueryType.ANALYTICAL, QueryType.CODE_GENERATION],
                temperature_range=(0.0, 1.0),
                max_tokens=200000,
                cost_per_1k=0.003,
                avg_latency_ms=1500,
                success_rate=0.96,
                supports_vision=True
            ),
            
            # Open Source Models (via OpenRouter)
            "mistralai/mixtral-8x7b-instruct": ModelProfile(
                model_id="mistralai/mixtral-8x7b-instruct",
                provider="openrouter",
                strengths=[QueryType.CONVERSATIONAL, QueryType.CODE_GENERATION],
                temperature_range=(0.0, 1.0),
                max_tokens=32768,
                cost_per_1k=0.0006,
                avg_latency_ms=800,
                success_rate=0.92
            ),
            
            # Specialized Models
            "dall-e-3": ModelProfile(
                model_id="dall-e-3",
                provider="openai",
                strengths=[QueryType.IMAGE_GENERATION],
                temperature_range=(0.0, 1.0),
                max_tokens=0,
                cost_per_1k=0.04,  # Per image
                avg_latency_ms=5000,
                success_rate=0.95
            ),
        }
    
    async def _select_optimal_model(
        self,
        query_type: QueryType,
        context: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """Select optimal model based on query type and current metrics"""
        
        # Filter models by capability
        capable_models = [
            profile for profile in self.model_profiles.values()
            if query_type in profile.strengths
        ]
        
        if not capable_models:
            # Fallback to general purpose models
            capable_models = [
                self.model_profiles.get("gpt-3.5-turbo"),
                self.model_profiles.get("claude-3-sonnet-20240229")
            ]
        
        # Score models based on multiple factors
        model_scores = []
        for profile in capable_models:
            if not profile:
                continue
                
            # Base score
            score = 100.0
            
            # Performance score (40% weight)
            perf_data = self.performance_cache[profile.model_id]
            if perf_data["latencies"]:
                avg_latency = np.mean(perf_data["latencies"][-10:])  # Last 10 requests
                latency_score = max(0, 100 - (avg_latency / 50))  # 50ms = 1 point penalty
                score += latency_score * 0.4
            
            # Success rate score (30% weight)
            total_requests = perf_data["successes"] + perf_data["failures"]
            if total_requests > 0:
                success_rate = perf_data["successes"] / total_requests
                score += success_rate * 100 * 0.3
            else:
                score += profile.success_rate * 100 * 0.3
            
            # Cost score (20% weight) - inverse relationship
            cost_score = max(0, 100 - (profile.cost_per_1k * 1000))
            score += cost_score * 0.2
            
            # Capability match score (10% weight)
            if query_type == profile.strengths[0]:  # Primary strength
                score += 10
            
            model_scores.append((profile, score))
        
        # Sort by score
        model_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Select primary and fallback models
        primary_model = model_scores[0][0]
        fallback_models = [m[0].model_id for m in model_scores[1:4]]  # Top 3 fallbacks
        
        # Determine temperature based on query type
        temperature_map = {
            QueryType.CREATIVE_SEARCH: 0.9,
            QueryType.DEEP_SEARCH: 0.3,
            QueryType.SUPER_DEEP_SEARCH: 0.1,
            QueryType.ANALYTICAL: 0.2,
            QueryType.CONVERSATIONAL: 0.7,
            QueryType.CODE_GENERATION: 0.2,
            QueryType.SUMMARIZATION: 0.3,
            QueryType.TRANSLATION: 0.1,
        }
        temperature = temperature_map.get(query_type, 0.5)
        
        # Determine max tokens
        max_tokens_map = {
            QueryType.CREATIVE_SEARCH: 2000,
            QueryType.DEEP_SEARCH: 4000,
            QueryType.SUPER_DEEP_SEARCH: 8000,
            QueryType.ANALYTICAL: 3000,
            QueryType.CONVERSATIONAL: 1000,
            QueryType.CODE_GENERATION: 2000,
            QueryType.SUMMARIZATION: 500,
            QueryType.TRANSLATION: 1000,
        }
        max_tokens = min(max_tokens_map.get(query_type, 1500), primary_model.max_tokens)
        
        # Build reasoning
        reasoning = (
            f"Selected {primary_model.model_id} for {query_type.value} query. "
            f"Score: {model_scores[0][1]:.1f}/100. "
            f"Estimated latency: {primary_model.avg_latency_ms}ms, "
            f"cost: ${primary_model.cost_per_1k * max_tokens / 1000:.4f}"
        )
        
        return RoutingDecision(
            primary_model=primary_model.model_id,
            fallback_models=fallback_models,
            temperature=temperature,
            max_tokens=max_tokens,
            reasoning=reasoning,
            estimated_cost=primary_model.cost_per_1k * max_tokens / 1000,
            estimated_latency_ms=primary_model.avg_latency_ms
        )
    
    async def route_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Route query with intelligent model selection"""
        
        # Classify query
        query_type = await self.classifier.classify(query, context)
        logger.info(f"Classified query as: {query_type.value}")
        
        # Select optimal model
        routing_decision = await self._select_optimal_model(query_type, context)
        logger.info(f"Routing decision: {routing_decision.reasoning}")
        
        # Record routing decision
        self.routing_history.append({
            "timestamp": datetime.utcnow(),
            "query_type": query_type.value,
            "decision": routing_decision,
            "query_preview": query[:100] + "..." if len(query) > 100 else query
        })
        
        # Prepare messages
        if isinstance(query, str):
            messages = [{"role": "user", "content": query}]
        else:
            messages = query
        
        # Execute with failover
        start_time = time.time()
        last_error = None
        
        for model in [routing_decision.primary_model] + routing_decision.fallback_models:
            try:
                response = await super().complete(
                    messages=messages,
                    model_override=model,
                    temperature_override=routing_decision.temperature,
                    max_tokens_override=routing_decision.max_tokens,
                    **kwargs
                )
                
                # Record success
                latency_ms = (time.time() - start_time) * 1000
                self.performance_cache[model]["latencies"].append(latency_ms)
                self.performance_cache[model]["successes"] += 1
                
                # Add routing metadata
                response["routing_metadata"] = {
                    "query_type": query_type.value,
                    "model_used": model,
                    "temperature": routing_decision.temperature,
                    "max_tokens": routing_decision.max_tokens,
                    "latency_ms": latency_ms,
                    "reasoning": routing_decision.reasoning
                }
                
                return response
                
            except Exception as e:
                last_error = e
                self.performance_cache[model]["failures"] += 1
                logger.warning(f"Model {model} failed: {str(e)}, trying fallback")
                continue
        
        # All models failed
        raise Exception(f"All models failed. Last error: {str(last_error)}")
    
    async def get_routing_analytics(self) -> Dict[str, Any]:
        """Get analytics on routing decisions and performance"""
        
        # Query type distribution
        query_type_counts = defaultdict(int)
        for entry in self.routing_history[-1000:]:  # Last 1000 queries
            query_type_counts[entry["query_type"]] += 1
        
        # Model performance summary
        model_performance = {}
        for model_id, perf_data in self.performance_cache.items():
            if perf_data["latencies"]:
                model_performance[model_id] = {
                    "avg_latency_ms": np.mean(perf_data["latencies"][-100:]),
                    "p95_latency_ms": np.percentile(perf_data["latencies"][-100:], 95),
                    "success_rate": perf_data["successes"] / max(1, perf_data["successes"] + perf_data["failures"]),
                    "total_requests": perf_data["successes"] + perf_data["failures"]
                }
        
        return {
            "query_type_distribution": dict(query_type_counts),
            "model_performance": model_performance,
            "recent_routing_decisions": [
                {
                    "timestamp": entry["timestamp"].isoformat(),
                    "query_type": entry["query_type"],
                    "model": entry["decision"].primary_model,
                    "reasoning": entry["decision"].reasoning
                }
                for entry in self.routing_history[-10:]
            ],
            "total_queries_routed": len(self.routing_history)
        }


# Singleton instance
_intelligent_router_instance: Optional[IntelligentLLMRouter] = None


def get_intelligent_llm_router() -> IntelligentLLMRouter:
    """Get or create the singleton intelligent LLM router instance"""
    global _intelligent_router_instance
    if _intelligent_router_instance is None:
        _intelligent_router_instance = IntelligentLLMRouter()
    return _intelligent_router_instance