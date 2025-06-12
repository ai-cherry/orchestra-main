#!/usr/bin/env python3
"""
OpenRouter Integration with Intelligent Fallback System
Provides cost-optimized AI interactions with smart routing to direct APIs

Author: Orchestra AI Team
Version: 1.0.0
"""

import asyncio
import httpx
import logging
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

from utils.fast_secrets import secrets, get_api_config
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class ModelProvider(Enum):
    """Available AI model providers."""
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROK = "grok"
    PERPLEXITY = "perplexity"

class UseCase(Enum):
    """Different use cases for AI interactions."""
    CASUAL_CHAT = "casual_chat"
    BUSINESS_ANALYSIS = "business_analysis"
    MEDICAL_COMPLIANCE = "medical_compliance"
    CREATIVE_WRITING = "creative_writing"
    CODE_GENERATION = "code_generation"
    RESEARCH_SEARCH = "research_search"
    STRATEGIC_PLANNING = "strategic_planning"
    QUICK_RESPONSE = "quick_response"

@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    provider: ModelProvider
    model_name: str
    cost_per_million: float
    max_tokens: int
    temperature: float
    strengths: List[str]
    use_cases: List[UseCase]

@dataclass
class ChatRequest:
    """Chat request structure."""
    persona: str
    message: str
    use_case: UseCase
    complexity: str = "medium"
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    fallback_allowed: bool = True

@dataclass
class ChatResponse:
    """Chat response structure."""
    content: str
    provider: ModelProvider
    model_used: str
    tokens_used: int
    cost: float
    response_time_ms: int
    fallback_used: bool = False
    error: Optional[str] = None

class IntelligentAIRouter:
    """Intelligent AI router with OpenRouter optimization and smart fallbacks."""
    
    def __init__(self):
        self.model_configs = self._initialize_model_configs()
        self.provider_status = {}
        self.cost_tracking = {
            "total_cost": 0.0,
            "total_savings": 0.0,
            "requests_count": 0,
            "provider_usage": {}
        }
        
    def _initialize_model_configs(self) -> Dict[str, ModelConfig]:
        """Initialize model configurations with costs and capabilities."""
        return {
            # OpenRouter Models (Cost-Optimized)
            "claude-3-haiku-or": ModelConfig(
                provider=ModelProvider.OPENROUTER,
                model_name="anthropic/claude-3-haiku",
                cost_per_million=0.25,
                max_tokens=1000,
                temperature=0.7,
                strengths=["fast", "cheap", "general"],
                use_cases=[UseCase.CASUAL_CHAT, UseCase.QUICK_RESPONSE]
            ),
            "claude-3-sonnet-or": ModelConfig(
                provider=ModelProvider.OPENROUTER,
                model_name="anthropic/claude-3-sonnet",
                cost_per_million=3.00,
                temperature=0.3,
                max_tokens=1500,
                strengths=["analysis", "reasoning", "accuracy"],
                use_cases=[UseCase.BUSINESS_ANALYSIS, UseCase.MEDICAL_COMPLIANCE, UseCase.STRATEGIC_PLANNING]
            ),
            "gpt-4-turbo-or": ModelConfig(
                provider=ModelProvider.OPENROUTER,
                model_name="openai/gpt-4-turbo",
                cost_per_million=10.00,
                max_tokens=1200,
                temperature=0.2,
                strengths=["complex_reasoning", "accuracy", "comprehensive"],
                use_cases=[UseCase.STRATEGIC_PLANNING, UseCase.MEDICAL_COMPLIANCE]
            ),
            "deepseek-coder-or": ModelConfig(
                provider=ModelProvider.OPENROUTER,
                model_name="deepseek/deepseek-coder",
                cost_per_million=0.14,
                max_tokens=1500,
                temperature=0.1,
                strengths=["coding", "technical", "cheap"],
                use_cases=[UseCase.CODE_GENERATION]
            ),
            "llama-70b-or": ModelConfig(
                provider=ModelProvider.OPENROUTER,
                model_name="meta-llama/llama-2-70b-chat",
                cost_per_million=0.70,
                max_tokens=1200,
                temperature=0.8,
                strengths=["creative", "open_source", "versatile"],
                use_cases=[UseCase.CREATIVE_WRITING, UseCase.CASUAL_CHAT]
            ),
            
            # Direct API Fallbacks
            "gpt-4-direct": ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4-turbo-preview",
                cost_per_million=30.00,
                max_tokens=1200,
                temperature=0.2,
                strengths=["reliability", "accuracy", "comprehensive"],
                use_cases=[UseCase.STRATEGIC_PLANNING, UseCase.BUSINESS_ANALYSIS]
            ),
            "grok-beta": ModelConfig(
                provider=ModelProvider.GROK,
                model_name="grok-beta",
                cost_per_million=5.00,  # Estimated
                max_tokens=1000,
                temperature=0.7,
                strengths=["real_time", "current_events", "witty"],
                use_cases=[UseCase.RESEARCH_SEARCH, UseCase.CASUAL_CHAT]
            ),
            "perplexity-sonar": ModelConfig(
                provider=ModelProvider.PERPLEXITY,
                model_name="llama-3-sonar-large-32k-online",
                cost_per_million=1.00,
                max_tokens=1000,
                temperature=0.2,
                strengths=["search", "current_info", "citations"],
                use_cases=[UseCase.RESEARCH_SEARCH, UseCase.BUSINESS_ANALYSIS]
            )
        }
    
    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """Main chat completion with intelligent routing and fallbacks."""
        start_time = datetime.now()
        
        try:
            # Select optimal model based on use case
            primary_model = self._select_optimal_model(request)
            
            # Try primary model (usually OpenRouter)
            try:
                response = await self._call_model(primary_model, request)
                response.fallback_used = False
                
                # Track successful usage
                await self._track_usage(response, request)
                return response
                
            except Exception as primary_error:
                logger.warning(f"Primary model {primary_model} failed: {primary_error}")
                
                if not request.fallback_allowed:
                    raise primary_error
                
                # Try fallback models
                fallback_models = self._get_fallback_models(request)
                
                for fallback_model in fallback_models:
                    try:
                        logger.info(f"Trying fallback model: {fallback_model}")
                        response = await self._call_model(fallback_model, request)
                        response.fallback_used = True
                        
                        # Track fallback usage
                        await self._track_usage(response, request)
                        return response
                        
                    except Exception as fallback_error:
                        logger.warning(f"Fallback model {fallback_model} failed: {fallback_error}")
                        continue
                
                # All models failed
                raise HTTPException(
                    status_code=503,
                    detail="All AI providers are currently unavailable"
                )
                
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            raise
        
        finally:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(f"Total response time: {response_time:.2f}ms")
    
    def _select_optimal_model(self, request: ChatRequest) -> str:
        """Select the optimal model based on use case, persona, and cost."""
        
        # Get models suitable for this use case
        suitable_models = [
            model_id for model_id, config in self.model_configs.items()
            if request.use_case in config.use_cases
        ]
        
        if not suitable_models:
            # Fallback to general-purpose model
            return "claude-3-haiku-or"
        
        # Persona-specific preferences
        persona_preferences = {
            "cherry": {
                UseCase.CASUAL_CHAT: "claude-3-haiku-or",
                UseCase.CREATIVE_WRITING: "llama-70b-or",
                UseCase.QUICK_RESPONSE: "claude-3-haiku-or"
            },
            "sophia": {
                UseCase.BUSINESS_ANALYSIS: "claude-3-sonnet-or",
                UseCase.STRATEGIC_PLANNING: "gpt-4-turbo-or",
                UseCase.RESEARCH_SEARCH: "perplexity-sonar"
            },
            "karen": {
                UseCase.MEDICAL_COMPLIANCE: "gpt-4-turbo-or",
                UseCase.BUSINESS_ANALYSIS: "claude-3-sonnet-or",
                UseCase.RESEARCH_SEARCH: "perplexity-sonar"
            }
        }
        
        # Check persona-specific preference
        persona_prefs = persona_preferences.get(request.persona, {})
        if request.use_case in persona_prefs:
            preferred_model = persona_prefs[request.use_case]
            if preferred_model in suitable_models:
                return preferred_model
        
        # Complexity-based selection
        if request.complexity == "high":
            # Prefer more powerful models for complex tasks
            high_quality_models = [m for m in suitable_models if "gpt-4" in m or "sonnet" in m]
            if high_quality_models:
                return min(high_quality_models, key=lambda m: self.model_configs[m].cost_per_million)
        
        elif request.complexity == "low":
            # Prefer cheaper models for simple tasks
            return min(suitable_models, key=lambda m: self.model_configs[m].cost_per_million)
        
        # Default: balance cost and quality
        return min(suitable_models, key=lambda m: self.model_configs[m].cost_per_million)
    
    def _get_fallback_models(self, request: ChatRequest) -> List[str]:
        """Get ordered list of fallback models for the use case."""
        
        fallback_strategies = {
            UseCase.CASUAL_CHAT: ["gpt-4-direct", "grok-beta"],
            UseCase.BUSINESS_ANALYSIS: ["gpt-4-direct", "perplexity-sonar"],
            UseCase.MEDICAL_COMPLIANCE: ["gpt-4-direct"],
            UseCase.CREATIVE_WRITING: ["gpt-4-direct", "grok-beta"],
            UseCase.CODE_GENERATION: ["gpt-4-direct"],
            UseCase.RESEARCH_SEARCH: ["perplexity-sonar", "grok-beta", "gpt-4-direct"],
            UseCase.STRATEGIC_PLANNING: ["gpt-4-direct"],
            UseCase.QUICK_RESPONSE: ["gpt-4-direct", "grok-beta"]
        }
        
        return fallback_strategies.get(request.use_case, ["gpt-4-direct"])
    
    async def _call_model(self, model_id: str, request: ChatRequest) -> ChatResponse:
        """Call a specific model and return response."""
        config = self.model_configs[model_id]
        start_time = datetime.now()
        
        if config.provider == ModelProvider.OPENROUTER:
            return await self._call_openrouter(config, request, start_time)
        elif config.provider == ModelProvider.OPENAI:
            return await self._call_openai(config, request, start_time)
        elif config.provider == ModelProvider.GROK:
            return await self._call_grok(config, request, start_time)
        elif config.provider == ModelProvider.PERPLEXITY:
            return await self._call_perplexity(config, request, start_time)
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")
    
    async def _call_openrouter(self, config: ModelConfig, request: ChatRequest, start_time: datetime) -> ChatResponse:
        """Call OpenRouter API."""
        openrouter_config = get_api_config('openrouter')
        if not openrouter_config['api_key']:
            raise Exception("OpenRouter not configured")
        
        headers = {
            'Authorization': f"Bearer {openrouter_config['api_key']}",
            'Content-Type': 'application/json',
            'HTTP-Referer': openrouter_config.get('site_url', 'https://orchestra-ai.dev'),
            'X-Title': openrouter_config.get('app_name', 'Orchestra AI')
        }
        
        payload = {
            "model": config.model_name,
            "messages": [
                {"role": "system", "content": self._get_persona_prompt(request.persona, request.use_case)},
                {"role": "user", "content": request.message}
            ],
            "temperature": request.temperature or config.temperature,
            "max_tokens": request.max_tokens or config.max_tokens
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{openrouter_config['base_url']}/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")
            
            result = response.json()
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ChatResponse(
                content=result["choices"][0]["message"]["content"],
                provider=ModelProvider.OPENROUTER,
                model_used=config.model_name,
                tokens_used=result.get("usage", {}).get("total_tokens", 0),
                cost=self._calculate_cost(result.get("usage", {}).get("total_tokens", 0), config),
                response_time_ms=int(response_time)
            )
    
    async def _call_openai(self, config: ModelConfig, request: ChatRequest, start_time: datetime) -> ChatResponse:
        """Call OpenAI API directly."""
        openai_config = get_api_config('openai')
        if not openai_config['api_key']:
            raise Exception("OpenAI not configured")
        
        headers = {
            'Authorization': f"Bearer {openai_config['api_key']}",
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": config.model_name,
            "messages": [
                {"role": "system", "content": self._get_persona_prompt(request.persona, request.use_case)},
                {"role": "user", "content": request.message}
            ],
            "temperature": request.temperature or config.temperature,
            "max_tokens": request.max_tokens or config.max_tokens
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{openai_config['base_url']}/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
            
            result = response.json()
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ChatResponse(
                content=result["choices"][0]["message"]["content"],
                provider=ModelProvider.OPENAI,
                model_used=config.model_name,
                tokens_used=result.get("usage", {}).get("total_tokens", 0),
                cost=self._calculate_cost(result.get("usage", {}).get("total_tokens", 0), config),
                response_time_ms=int(response_time)
            )
    
    async def _call_grok(self, config: ModelConfig, request: ChatRequest, start_time: datetime) -> ChatResponse:
        """Call Grok xAI API."""
        grok_api_key = secrets.get('grok', 'api_key')
        if not grok_api_key:
            raise Exception("Grok xAI not configured")
        
        headers = {
            'Authorization': f"Bearer {grok_api_key}",
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": config.model_name,
            "messages": [
                {"role": "system", "content": self._get_persona_prompt(request.persona, request.use_case)},
                {"role": "user", "content": request.message}
            ],
            "temperature": request.temperature or config.temperature,
            "max_tokens": request.max_tokens or config.max_tokens
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"Grok API error: {response.status_code} - {response.text}")
            
            result = response.json()
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ChatResponse(
                content=result["choices"][0]["message"]["content"],
                provider=ModelProvider.GROK,
                model_used=config.model_name,
                tokens_used=result.get("usage", {}).get("total_tokens", 0),
                cost=self._calculate_cost(result.get("usage", {}).get("total_tokens", 0), config),
                response_time_ms=int(response_time)
            )
    
    async def _call_perplexity(self, config: ModelConfig, request: ChatRequest, start_time: datetime) -> ChatResponse:
        """Call Perplexity API."""
        perplexity_config = get_api_config('perplexity')
        if not perplexity_config['api_key']:
            raise Exception("Perplexity not configured")
        
        headers = {
            'Authorization': f"Bearer {perplexity_config['api_key']}",
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": config.model_name,
            "messages": [
                {"role": "system", "content": self._get_persona_prompt(request.persona, request.use_case)},
                {"role": "user", "content": request.message}
            ],
            "temperature": request.temperature or config.temperature,
            "max_tokens": request.max_tokens or config.max_tokens
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{perplexity_config['base_url']}/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"Perplexity API error: {response.status_code} - {response.text}")
            
            result = response.json()
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ChatResponse(
                content=result["choices"][0]["message"]["content"],
                provider=ModelProvider.PERPLEXITY,
                model_used=config.model_name,
                tokens_used=result.get("usage", {}).get("total_tokens", 0),
                cost=self._calculate_cost(result.get("usage", {}).get("total_tokens", 0), config),
                response_time_ms=int(response_time)
            )
    
    def _get_persona_prompt(self, persona: str, use_case: UseCase) -> str:
        """Get persona-specific system prompt based on use case."""
        base_prompts = {
            "cherry": "You are Cherry, a warm, playful, and empathetic personal life coach.",
            "sophia": "You are Sophia, a strategic business advisor for PayReady.",
            "karen": "You are Karen, a healthcare compliance expert for ParagonRX."
        }
        
        use_case_modifiers = {
            UseCase.CASUAL_CHAT: "Keep the conversation light, friendly, and engaging.",
            UseCase.BUSINESS_ANALYSIS: "Provide detailed business analysis with actionable insights.",
            UseCase.MEDICAL_COMPLIANCE: "Ensure medical accuracy and regulatory compliance.",
            UseCase.CREATIVE_WRITING: "Be imaginative, creative, and inspiring.",
            UseCase.CODE_GENERATION: "Focus on clean, efficient, and well-documented code.",
            UseCase.RESEARCH_SEARCH: "Provide comprehensive research with citations when possible.",
            UseCase.STRATEGIC_PLANNING: "Think strategically with long-term vision and planning.",
            UseCase.QUICK_RESPONSE: "Be concise and direct while maintaining helpfulness."
        }
        
        base = base_prompts.get(persona, base_prompts["cherry"])
        modifier = use_case_modifiers.get(use_case, "")
        
        return f"{base} {modifier}".strip()
    
    def _calculate_cost(self, tokens_used: int, config: ModelConfig) -> float:
        """Calculate cost for tokens used."""
        return (tokens_used / 1_000_000) * config.cost_per_million
    
    async def _track_usage(self, response: ChatResponse, request: ChatRequest):
        """Track usage statistics and cost savings."""
        self.cost_tracking["total_cost"] += response.cost
        self.cost_tracking["requests_count"] += 1
        
        # Track provider usage
        provider_name = response.provider.value
        if provider_name not in self.cost_tracking["provider_usage"]:
            self.cost_tracking["provider_usage"][provider_name] = {
                "requests": 0,
                "total_cost": 0.0,
                "total_tokens": 0
            }
        
        self.cost_tracking["provider_usage"][provider_name]["requests"] += 1
        self.cost_tracking["provider_usage"][provider_name]["total_cost"] += response.cost
        self.cost_tracking["provider_usage"][provider_name]["total_tokens"] += response.tokens_used
        
        # Calculate savings if using OpenRouter
        if response.provider == ModelProvider.OPENROUTER:
            # Compare to direct OpenAI cost
            direct_cost = (response.tokens_used / 1_000_000) * 30.0  # GPT-4 direct pricing
            savings = direct_cost - response.cost
            self.cost_tracking["total_savings"] += savings
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        return {
            "cost_tracking": self.cost_tracking,
            "provider_status": self.provider_status,
            "model_configs": {
                model_id: {
                    "provider": config.provider.value,
                    "cost_per_million": config.cost_per_million,
                    "strengths": config.strengths,
                    "use_cases": [uc.value for uc in config.use_cases]
                }
                for model_id, config in self.model_configs.items()
            }
        }

# Global router instance
ai_router = IntelligentAIRouter()

# Convenience functions for different use cases
async def chat_casual(persona: str, message: str, **kwargs) -> ChatResponse:
    """Casual chat interaction."""
    request = ChatRequest(
        persona=persona,
        message=message,
        use_case=UseCase.CASUAL_CHAT,
        **kwargs
    )
    return await ai_router.chat_completion(request)

async def chat_business(persona: str, message: str, **kwargs) -> ChatResponse:
    """Business analysis interaction."""
    request = ChatRequest(
        persona=persona,
        message=message,
        use_case=UseCase.BUSINESS_ANALYSIS,
        **kwargs
    )
    return await ai_router.chat_completion(request)

async def chat_medical(persona: str, message: str, **kwargs) -> ChatResponse:
    """Medical compliance interaction."""
    request = ChatRequest(
        persona=persona,
        message=message,
        use_case=UseCase.MEDICAL_COMPLIANCE,
        **kwargs
    )
    return await ai_router.chat_completion(request)

async def chat_research(persona: str, message: str, **kwargs) -> ChatResponse:
    """Research and search interaction."""
    request = ChatRequest(
        persona=persona,
        message=message,
        use_case=UseCase.RESEARCH_SEARCH,
        **kwargs
    )
    return await ai_router.chat_completion(request)

async def chat_code(persona: str, message: str, **kwargs) -> ChatResponse:
    """Code generation interaction."""
    request = ChatRequest(
        persona=persona,
        message=message,
        use_case=UseCase.CODE_GENERATION,
        **kwargs
    )
    return await ai_router.chat_completion(request) 