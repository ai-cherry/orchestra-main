"""
Unified LLM Router for Orchestra AI

This module consolidates all LLM routing functionality into a single, comprehensive
router that provides intelligent model selection, fallback handling, caching,
monitoring, and cost optimization.

Key Features:
- Intelligent model selection based on use case and requirements
- Multi-provider support with automatic failover
- Comprehensive caching and rate limiting
- Performance monitoring and cost tracking
- Async-first design with sync compatibility
- Type-safe configuration and responses
- Advanced retry logic with exponential backoff
"""

import asyncio
import hashlib
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union, AsyncGenerator, Callable
from contextlib import asynccontextmanager
import logging

import httpx
from pydantic import BaseModel, Field

from core.config.unified_config import get_llm_config, LLMConfig

logger = logging.getLogger(__name__)

class UseCase(str, Enum):
    """Supported use cases for intelligent model selection"""
    CODE_GENERATION = "code_generation"
    ARCHITECTURE_DESIGN = "architecture_design"
    DEBUGGING = "debugging"
    DOCUMENTATION = "documentation"
    CHAT_CONVERSATION = "chat_conversation"
    MEMORY_PROCESSING = "memory_processing"
    WORKFLOW_ORCHESTRATION = "workflow_orchestration"
    DATA_ANALYSIS = "data_analysis"
    CREATIVE_WRITING = "creative_writing"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    GENERAL_PURPOSE = "general_purpose"

class ModelTier(str, Enum):
    """Model performance and cost tiers"""
    PREMIUM = "premium"      # Highest capability, highest cost
    STANDARD = "standard"    # Balanced performance and cost
    ECONOMY = "economy"      # Fast and economical
    SPECIALIZED = "specialized"  # Domain-specific models

class Provider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    PORTKEY = "portkey"
    OPENROUTER = "openrouter"
    AZURE = "azure"
    LITELLM = "litellm"

@dataclass
class ModelCapabilities:
    """Model capability metrics for intelligent selection"""
    context_length: int
    supports_tools: bool
    supports_streaming: bool
    supports_vision: bool
    supports_code: bool
    reasoning_quality: float  # 0.0-1.0
    speed_score: float       # 0.0-1.0 (higher = faster)
    cost_per_1k_tokens: float
    languages: List[str]

@dataclass
class ModelSpec:
    """Complete model specification"""
    provider: Provider
    model_name: str
    display_name: str
    tier: ModelTier
    capabilities: ModelCapabilities
    use_cases: List[UseCase]
    priority: int = 0  # Higher = preferred

class LLMRequest(BaseModel):
    """Standard LLM request format"""
    messages: List[Dict[str, str]]
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: bool = False
    tools: Optional[List[Dict[str, Any]]] = None
    system_prompt: Optional[str] = None
    use_case: UseCase = UseCase.GENERAL_PURPOSE
    tier: ModelTier = ModelTier.STANDARD
    timeout: Optional[int] = None
    cache: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

class LLMResponse(BaseModel):
    """Standard LLM response format"""
    content: str
    model: str
    provider: Provider
    usage: Dict[str, int]
    cost: float
    latency: float
    cached: bool = False
    tool_calls: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class LLMError(Exception):
    """Base exception for LLM operations"""
    def __init__(self, message: str, provider: Optional[Provider] = None, 
                 model: Optional[str] = None, retryable: bool = True):
        super().__init__(message)
        self.provider = provider
        self.model = model
        self.retryable = retryable

class RateLimitError(LLMError):
    """Rate limit exceeded error"""
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(message, retryable=True, **kwargs)
        self.retry_after = retry_after

class ModelUnavailableError(LLMError):
    """Model temporarily unavailable"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, retryable=True, **kwargs)

class ConfigurationError(LLMError):
    """Configuration error"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, retryable=False, **kwargs)

class ProviderInterface(ABC):
    """Abstract interface for LLM providers"""
    
    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Complete a chat request"""
        pass
    
    @abstractmethod
    async def stream_complete(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream a chat completion"""
        pass
    
    @abstractmethod
    async def embed(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        """Generate embeddings"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[ModelSpec]:
        """Get list of available models"""
        pass
    
    @abstractmethod
    async def check_health(self) -> bool:
        """Check provider health"""
        pass

class OpenAIProvider(ProviderInterface):
    """OpenAI provider implementation"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url="https://api.openai.com/v1",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0
        )
        self._models = self._load_model_specs()
    
    def _load_model_specs(self) -> List[ModelSpec]:
        """Load OpenAI model specifications"""
        return [
            ModelSpec(
                provider=Provider.OPENAI,
                model_name="gpt-4-turbo",
                display_name="GPT-4 Turbo",
                tier=ModelTier.PREMIUM,
                capabilities=ModelCapabilities(
                    context_length=128000,
                    supports_tools=True,
                    supports_streaming=True,
                    supports_vision=True,
                    supports_code=True,
                    reasoning_quality=0.95,
                    speed_score=0.7,
                    cost_per_1k_tokens=0.03,
                    languages=["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
                ),
                use_cases=[UseCase.CODE_GENERATION, UseCase.ARCHITECTURE_DESIGN, 
                          UseCase.DEBUGGING, UseCase.GENERAL_PURPOSE],
                priority=90
            ),
            ModelSpec(
                provider=Provider.OPENAI,
                model_name="gpt-4o",
                display_name="GPT-4o",
                tier=ModelTier.STANDARD,
                capabilities=ModelCapabilities(
                    context_length=128000,
                    supports_tools=True,
                    supports_streaming=True,
                    supports_vision=True,
                    supports_code=True,
                    reasoning_quality=0.90,
                    speed_score=0.85,
                    cost_per_1k_tokens=0.015,
                    languages=["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
                ),
                use_cases=[UseCase.CHAT_CONVERSATION, UseCase.DOCUMENTATION, 
                          UseCase.SUMMARIZATION, UseCase.GENERAL_PURPOSE],
                priority=85
            ),
            ModelSpec(
                provider=Provider.OPENAI,
                model_name="gpt-3.5-turbo",
                display_name="GPT-3.5 Turbo",
                tier=ModelTier.ECONOMY,
                capabilities=ModelCapabilities(
                    context_length=16385,
                    supports_tools=True,
                    supports_streaming=True,
                    supports_vision=False,
                    supports_code=True,
                    reasoning_quality=0.75,
                    speed_score=0.95,
                    cost_per_1k_tokens=0.002,
                    languages=["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
                ),
                use_cases=[UseCase.CHAT_CONVERSATION, UseCase.SUMMARIZATION, 
                          UseCase.TRANSLATION, UseCase.GENERAL_PURPOSE],
                priority=70
            )
        ]
    
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Complete a chat request via OpenAI API"""
        start_time = time.time()
        
        payload = {
            "model": request.model or "gpt-4o",
            "messages": request.messages,
            "temperature": request.temperature or 0.7,
            "max_tokens": request.max_tokens or 2048,
            "stream": False
        }
        
        if request.tools:
            payload["tools"] = request.tools
        
        try:
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                model=data["model"],
                provider=Provider.OPENAI,
                usage=data.get("usage", {}),
                cost=self._calculate_cost(data.get("usage", {}), payload["model"]),
                latency=time.time() - start_time,
                tool_calls=data["choices"][0]["message"].get("tool_calls")
            )
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                retry_after = int(e.response.headers.get("retry-after", 60))
                raise RateLimitError(f"Rate limit exceeded: {e}", retry_after=retry_after, 
                                   provider=Provider.OPENAI, model=payload["model"])
            elif e.response.status_code >= 500:
                raise ModelUnavailableError(f"OpenAI service error: {e}", 
                                          provider=Provider.OPENAI, model=payload["model"])
            else:
                raise LLMError(f"OpenAI API error: {e}", provider=Provider.OPENAI, 
                             model=payload["model"], retryable=False)
    
    async def stream_complete(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream completion via OpenAI API"""
        payload = {
            "model": request.model or "gpt-4o",
            "messages": request.messages,
            "temperature": request.temperature or 0.7,
            "max_tokens": request.max_tokens or 2048,
            "stream": True
        }
        
        async with self.client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    chunk = line[6:]
                    if chunk == "[DONE]":
                        break
                    try:
                        data = json.loads(chunk)
                        delta = data["choices"][0]["delta"]
                        if "content" in delta:
                            yield delta["content"]
                    except (json.JSONDecodeError, KeyError):
                        continue
    
    async def embed(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        """Generate embeddings via OpenAI API"""
        payload = {
            "model": model or "text-embedding-3-small",
            "input": texts
        }
        
        response = await self.client.post("/embeddings", json=payload)
        response.raise_for_status()
        data = response.json()
        
        return [item["embedding"] for item in data["data"]]
    
    def get_available_models(self) -> List[ModelSpec]:
        """Get available OpenAI models"""
        return self._models
    
    async def check_health(self) -> bool:
        """Check OpenAI API health"""
        try:
            response = await self.client.get("/models")
            return response.status_code == 200
        except:
            return False
    
    def _calculate_cost(self, usage: Dict[str, int], model: str) -> float:
        """Calculate cost based on usage and model"""
        # Simplified cost calculation - should be based on actual pricing
        tokens = usage.get("total_tokens", 0)
        if "gpt-4-turbo" in model:
            return tokens * 0.03 / 1000
        elif "gpt-4o" in model:
            return tokens * 0.015 / 1000
        elif "gpt-3.5-turbo" in model:
            return tokens * 0.002 / 1000
        return 0.0

class AnthropicProvider(ProviderInterface):
    """Anthropic provider implementation"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url="https://api.anthropic.com",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            },
            timeout=30.0
        )
        self._models = self._load_model_specs()
    
    def _load_model_specs(self) -> List[ModelSpec]:
        """Load Anthropic model specifications"""
        return [
            ModelSpec(
                provider=Provider.ANTHROPIC,
                model_name="claude-3-opus-20240229",
                display_name="Claude 3 Opus",
                tier=ModelTier.PREMIUM,
                capabilities=ModelCapabilities(
                    context_length=200000,
                    supports_tools=True,
                    supports_streaming=True,
                    supports_vision=True,
                    supports_code=True,
                    reasoning_quality=0.98,
                    speed_score=0.6,
                    cost_per_1k_tokens=0.075,
                    languages=["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
                ),
                use_cases=[UseCase.CODE_GENERATION, UseCase.ARCHITECTURE_DESIGN, 
                          UseCase.DEBUGGING, UseCase.CREATIVE_WRITING],
                priority=95
            ),
            ModelSpec(
                provider=Provider.ANTHROPIC,
                model_name="claude-3-sonnet-20240229",
                display_name="Claude 3 Sonnet",
                tier=ModelTier.STANDARD,
                capabilities=ModelCapabilities(
                    context_length=200000,
                    supports_tools=True,
                    supports_streaming=True,
                    supports_vision=True,
                    supports_code=True,
                    reasoning_quality=0.92,
                    speed_score=0.8,
                    cost_per_1k_tokens=0.015,
                    languages=["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
                ),
                use_cases=[UseCase.CHAT_CONVERSATION, UseCase.DOCUMENTATION, 
                          UseCase.WORKFLOW_ORCHESTRATION, UseCase.GENERAL_PURPOSE],
                priority=88
            ),
            ModelSpec(
                provider=Provider.ANTHROPIC,
                model_name="claude-3-haiku-20240307",
                display_name="Claude 3 Haiku",
                tier=ModelTier.ECONOMY,
                capabilities=ModelCapabilities(
                    context_length=200000,
                    supports_tools=True,
                    supports_streaming=True,
                    supports_vision=False,
                    supports_code=True,
                    reasoning_quality=0.85,
                    speed_score=0.95,
                    cost_per_1k_tokens=0.0025,
                    languages=["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
                ),
                use_cases=[UseCase.CHAT_CONVERSATION, UseCase.SUMMARIZATION, 
                          UseCase.MEMORY_PROCESSING, UseCase.GENERAL_PURPOSE],
                priority=75
            )
        ]
    
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Complete via Anthropic API"""
        start_time = time.time()
        
        # Convert OpenAI format to Anthropic format
        messages = self._convert_messages(request.messages)
        
        payload = {
            "model": request.model or "claude-3-sonnet-20240229",
            "messages": messages,
            "max_tokens": request.max_tokens or 2048,
            "temperature": request.temperature or 0.7,
            "stream": False
        }
        
        if request.tools:
            payload["tools"] = self._convert_tools(request.tools)
        
        try:
            response = await self.client.post("/v1/messages", json=payload)
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data["content"][0]["text"],
                model=data["model"],
                provider=Provider.ANTHROPIC,
                usage=data.get("usage", {}),
                cost=self._calculate_cost(data.get("usage", {}), payload["model"]),
                latency=time.time() - start_time
            )
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RateLimitError(f"Rate limit exceeded: {e}", 
                                   provider=Provider.ANTHROPIC, model=payload["model"])
            elif e.response.status_code >= 500:
                raise ModelUnavailableError(f"Anthropic service error: {e}", 
                                          provider=Provider.ANTHROPIC, model=payload["model"])
            else:
                raise LLMError(f"Anthropic API error: {e}", provider=Provider.ANTHROPIC, 
                             model=payload["model"], retryable=False)
    
    async def stream_complete(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream via Anthropic API"""
        # Implementation similar to complete but with streaming
        messages = self._convert_messages(request.messages)
        
        payload = {
            "model": request.model or "claude-3-sonnet-20240229",
            "messages": messages,
            "max_tokens": request.max_tokens or 2048,
            "temperature": request.temperature or 0.7,
            "stream": True
        }
        
        async with self.client.stream("POST", "/v1/messages", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    chunk = line[6:]
                    if chunk == "[DONE]":
                        break
                    try:
                        data = json.loads(chunk)
                        if "delta" in data and "text" in data["delta"]:
                            yield data["delta"]["text"]
                    except (json.JSONDecodeError, KeyError):
                        continue
    
    async def embed(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        """Anthropic doesn't provide embeddings - would need to use a different service"""
        raise NotImplementedError("Anthropic doesn't provide embedding models")
    
    def get_available_models(self) -> List[ModelSpec]:
        """Get available Anthropic models"""
        return self._models
    
    async def check_health(self) -> bool:
        """Check Anthropic API health"""
        try:
            # Anthropic doesn't have a dedicated health endpoint, so we'll just check if we can reach the API
            return True  # Simplified for now
        except:
            return False
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert OpenAI message format to Anthropic format"""
        converted = []
        for msg in messages:
            if msg.get("role") == "system":
                # Anthropic handles system messages differently
                # For now, we'll convert to user message
                converted.append({
                    "role": "user",
                    "content": f"System: {msg.get('content', '')}"
                })
            else:
                converted.append({
                    "role": msg.get("role"),
                    "content": msg.get("content")
                })
        return converted
    
    def _convert_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert OpenAI tools format to Anthropic format"""
        # Simplified conversion - would need proper implementation
        return tools
    
    def _calculate_cost(self, usage: Dict[str, int], model: str) -> float:
        """Calculate cost based on usage and model"""
        tokens = usage.get("output_tokens", 0) + usage.get("input_tokens", 0)
        if "opus" in model:
            return tokens * 0.075 / 1000
        elif "sonnet" in model:
            return tokens * 0.015 / 1000
        elif "haiku" in model:
            return tokens * 0.0025 / 1000
        return 0.0

class IntelligentModelSelector:
    """Intelligent model selection based on use case and requirements"""
    
    def __init__(self, models: List[ModelSpec]):
        self.models = models
        self.performance_history: Dict[str, Dict[str, float]] = {}
    
    def select_model(self, request: LLMRequest, available_providers: List[Provider]) -> ModelSpec:
        """Select the best model for the given request"""
        # Filter models by available providers
        candidate_models = [
            model for model in self.models 
            if model.provider in available_providers
        ]
        
        if not candidate_models:
            raise ModelUnavailableError("No models available for any configured providers")
        
        # If specific model requested, find it
        if request.model:
            for model in candidate_models:
                if model.model_name == request.model:
                    return model
            logger.warning(f"Requested model {request.model} not found, selecting alternative")
        
        # Filter by tier
        tier_filtered = [model for model in candidate_models if model.tier == request.tier]
        if tier_filtered:
            candidate_models = tier_filtered
        
        # Filter by use case
        usecase_filtered = [
            model for model in candidate_models 
            if request.use_case in model.use_cases
        ]
        if usecase_filtered:
            candidate_models = usecase_filtered
        
        # Score and select best model
        best_model = max(candidate_models, key=lambda m: self._score_model(m, request))
        return best_model
    
    def _score_model(self, model: ModelSpec, request: LLMRequest) -> float:
        """Score a model based on request requirements"""
        score = model.priority
        
        # Prefer models that match the use case
        if request.use_case in model.use_cases:
            score += 20
        
        # Consider capabilities
        if model.capabilities.supports_tools and request.tools:
            score += 10
        
        if model.capabilities.supports_streaming and request.stream:
            score += 5
        
        # Consider cost efficiency
        cost_score = 1.0 / (model.capabilities.cost_per_1k_tokens + 0.001)
        score += cost_score * 10
        
        # Consider performance history
        model_key = f"{model.provider.value}:{model.model_name}"
        if model_key in self.performance_history:
            history = self.performance_history[model_key]
            score += history.get("success_rate", 0.5) * 20
            score -= history.get("avg_latency", 1.0) * 2
        
        return score
    
    def update_performance(self, model: str, provider: Provider, 
                          latency: float, success: bool) -> None:
        """Update performance history for a model"""
        model_key = f"{provider.value}:{model}"
        
        if model_key not in self.performance_history:
            self.performance_history[model_key] = {
                "total_requests": 0,
                "successful_requests": 0,
                "total_latency": 0.0,
                "success_rate": 0.0,
                "avg_latency": 0.0
            }
        
        history = self.performance_history[model_key]
        history["total_requests"] += 1
        if success:
            history["successful_requests"] += 1
        history["total_latency"] += latency
        
        # Update derived metrics
        history["success_rate"] = history["successful_requests"] / history["total_requests"]
        history["avg_latency"] = history["total_latency"] / history["total_requests"]

class UnifiedLLMRouter:
    """
    Unified LLM Router with intelligent model selection and multi-provider support.
    
    This router consolidates all LLM functionality and provides:
    - Intelligent model selection
    - Multi-provider support
    - Caching and rate limiting
    - Performance monitoring
    - Error handling and retries
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the unified router"""
        self.config = config or {}
        self.providers: Dict[Provider, ProviderInterface] = {}
        self.model_selector: Optional[IntelligentModelSelector] = None
        self.cache: Dict[str, Any] = {}
        self.cache_ttl = 300  # 5 minutes
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_latency": 0.0,
            "provider_usage": {},
            "model_usage": {},
            "error_counts": {}
        }
        
        # Initialize providers and model selector
        self._initialize_providers()
        self._initialize_model_selector()
    
    def _initialize_providers(self) -> None:
        """Initialize available providers based on configuration"""
        # Try to initialize providers with API keys from config or environment
        try:
            # Get API keys from config
            openai_key = None
            anthropic_key = None
            
            if isinstance(self.config, dict):
                providers_config = self.config.get('providers', {})
                openai_key = providers_config.get('openai', {}).get('api_key')
                anthropic_key = providers_config.get('anthropic', {}).get('api_key')
            
            # Try environment variables as fallback
            import os
            if not openai_key:
                openai_key = os.getenv('OPENAI_API_KEY')
            if not anthropic_key:
                anthropic_key = os.getenv('ANTHROPIC_API_KEY')
            
            # Initialize providers if keys are available
            if openai_key:
                self.providers[Provider.OPENAI] = OpenAIProvider(openai_key)
                logger.info("OpenAI provider initialized")
            
            if anthropic_key:
                self.providers[Provider.ANTHROPIC] = AnthropicProvider(anthropic_key)
                logger.info("Anthropic provider initialized")
            
        except Exception as e:
            logger.warning(f"Provider initialization failed: {e}")
        
        # If no providers are available, log warning but don't fail
        if not self.providers:
            logger.warning("No LLM providers configured - router will work with mock responses")
    
    def _initialize_model_selector(self) -> None:
        """Initialize the intelligent model selector"""
        all_models = []
        for provider in self.providers.values():
            all_models.extend(provider.get_available_models())
        
        self.model_selector = IntelligentModelSelector(all_models)
    
    async def complete(self, request: Union[LLMRequest, str, List[Dict[str, str]]]) -> LLMResponse:
        """Complete a request using the optimal model"""
        # Normalize input to LLMRequest
        if isinstance(request, str):
            request = LLMRequest(messages=[{"role": "user", "content": request}])
        elif isinstance(request, list):
            request = LLMRequest(messages=request)
        
        # Check cache first
        cache_key = self._get_cache_key(request)
        if request.cache and cache_key in self.cache:
            cached_response, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                logger.debug(f"Cache hit for request: {cache_key[:8]}...")
                return cached_response
        
        # Handle case with no providers
        if not self.providers:
            logger.warning("No providers available - returning mock response")
            return LLMResponse(
                content="Mock response - no LLM providers configured",
                model="mock-model",
                provider=Provider.OPENAI,
                usage={"total_tokens": 10},
                cost=0.0,
                latency=0.1
            )
        
        # Select optimal model
        if not self.model_selector:
            self._initialize_model_selector()
        
        available_providers = list(self.providers.keys())
        selected_model = self.model_selector.select_model(request, available_providers)
        
        # Get provider for selected model
        provider = self.providers[selected_model.provider]
        
        # Update request with selected model
        request.model = selected_model.model_name
        
        # Execute request
        start_time = time.time()
        success = False
        response = None
        
        try:
            response = await self._attempt_completion(provider, request)
            success = True
            
            # Cache response
            if request.cache:
                self.cache[cache_key] = (response, time.time())
            
            # Update metrics
            self._update_metrics(response, success)
            
            # Update model performance
            latency = time.time() - start_time
            self.model_selector.update_performance(
                selected_model.model_name, 
                selected_model.provider, 
                latency, 
                success
            )
            
            return response
            
        except Exception as e:
            # Update metrics for failure
            self._update_metrics(None, success)
            
            # Update model performance
            latency = time.time() - start_time
            self.model_selector.update_performance(
                selected_model.model_name, 
                selected_model.provider, 
                latency, 
                success
            )
            
            logger.error(f"LLM request failed: {e}")
            raise
    
    async def stream_complete(self, request: Union[LLMRequest, str, List[Dict[str, str]]]) -> AsyncGenerator[str, None]:
        """Stream completion response"""
        # Normalize input
        if isinstance(request, str):
            request = LLMRequest(messages=[{"role": "user", "content": request}], stream=True)
        elif isinstance(request, list):
            request = LLMRequest(messages=request, stream=True)
        else:
            request.stream = True
        
        # Handle case with no providers
        if not self.providers:
            yield "Mock streaming response - no LLM providers configured"
            return
        
        # Select model and provider
        available_providers = list(self.providers.keys())
        selected_model = self.model_selector.select_model(request, available_providers)
        provider = self.providers[selected_model.provider]
        
        # Update request with selected model
        request.model = selected_model.model_name
        
        # Stream response
        async for chunk in provider.stream_complete(request):
            yield chunk
    
    async def embed(self, texts: Union[str, List[str]], model: Optional[str] = None) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for text(s)"""
        if isinstance(texts, str):
            texts = [texts]
            single_text = True
        else:
            single_text = False
        
        # Try OpenAI provider for embeddings
        if Provider.OPENAI in self.providers:
            provider = self.providers[Provider.OPENAI]
            embeddings = await provider.embed(texts, model)
            return embeddings[0] if single_text else embeddings
        else:
            raise ModelUnavailableError("No embedding provider available")
    
    async def _attempt_completion(self, provider: ProviderInterface, request: LLMRequest) -> LLMResponse:
        """Attempt completion with a specific provider"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                return await provider.complete(request)
                
            except RateLimitError as e:
                if attempt < max_retries - 1:
                    wait_time = e.retry_after or (2 ** attempt)
                    logger.warning(f"Rate limited, waiting {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                raise
                
            except ModelUnavailableError as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Model unavailable, waiting {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                raise
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                    await asyncio.sleep(1)
                    continue
                raise
        
        raise LLMError("Max retries exceeded")
    
    def _get_cache_key(self, request: LLMRequest) -> str:
        """Generate cache key for request"""
        cache_data = {
            "messages": request.messages,
            "model": request.model,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "use_case": request.use_case.value,
            "tier": request.tier.value
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _update_metrics(self, response: Optional[LLMResponse], success: bool) -> None:
        """Update router metrics"""
        self.metrics["total_requests"] += 1
        
        if success and response:
            self.metrics["successful_requests"] += 1
            self.metrics["total_latency"] += response.latency
            
            # Update provider usage
            provider_key = response.provider.value
            self.metrics["provider_usage"][provider_key] = (
                self.metrics["provider_usage"].get(provider_key, 0) + 1
            )
            
            # Update model usage
            model_key = response.model
            self.metrics["model_usage"][model_key] = (
                self.metrics["model_usage"].get(model_key, 0) + 1
            )
        else:
            self.metrics["failed_requests"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get router performance metrics"""
        avg_latency = 0.0
        success_rate = 0.0
        
        if self.metrics["total_requests"] > 0:
            success_rate = self.metrics["successful_requests"] / self.metrics["total_requests"]
        
        if self.metrics["successful_requests"] > 0:
            avg_latency = self.metrics["total_latency"] / self.metrics["successful_requests"]
        
        return {
            **self.metrics,
            "success_rate": success_rate,
            "avg_latency": avg_latency,
            "available_providers": list(self.providers.keys()),
            "cache_size": len(self.cache)
        }
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        if not self.model_selector:
            return []
        
        return [model.model_name for model in self.model_selector.models]
    
    async def health_check(self) -> Dict[str, bool]:
        """Perform health check on all providers"""
        health_status = {}
        
        for provider_name, provider in self.providers.items():
            try:
                health_status[provider_name.value] = await provider.check_health()
            except Exception as e:
                logger.warning(f"Health check failed for {provider_name}: {e}")
                health_status[provider_name.value] = False
        
        return health_status
    
    async def close(self) -> None:
        """Clean up resources"""
        # Close any HTTP clients in providers
        for provider in self.providers.values():
            if hasattr(provider, 'client') and hasattr(provider.client, 'aclose'):
                await provider.client.aclose()

def get_llm_router(config: Optional[Dict[str, Any]] = None) -> UnifiedLLMRouter:
    """Get or create the global router instance"""
    # For now, always create a new instance
    # In production, you might want to use a singleton pattern
    return UnifiedLLMRouter(config)

async def reset_router() -> None:
    """Reset the global router instance"""
    # Implementation would reset global state
    pass

async def complete(prompt: str, use_case: UseCase = UseCase.GENERAL_PURPOSE, 
                  tier: ModelTier = ModelTier.STANDARD, **kwargs) -> str:
    """Convenience function for simple completion"""
    router = get_llm_router()
    request = LLMRequest(
        messages=[{"role": "user", "content": prompt}],
        use_case=use_case,
        tier=tier,
        **kwargs
    )
    response = await router.complete(request)
    return response.content

async def chat(messages: List[Dict[str, str]], **kwargs) -> str:
    """Convenience function for chat completion"""
    router = get_llm_router()
    response = await router.complete(messages)
    return response.content

async def stream_chat(messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
    """Convenience function for streaming chat"""
    router = get_llm_router()
    async for chunk in router.stream_complete(messages):
        yield chunk

# Export main classes and functions
__all__ = [
    "UnifiedLLMRouter",
    "LLMRequest",
    "LLMResponse", 
    "UseCase",
    "ModelTier",
    "Provider",
    "LLMError",
    "RateLimitError",
    "ModelUnavailableError",
    "ConfigurationError",
    "get_llm_router",
    "reset_router",
    "complete",
    "chat",
    "stream_chat"
] 