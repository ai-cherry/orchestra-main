"""
Unified LLM Router for Orchestra Project

This module provides a unified interface for routing LLM requests through
Portkey (primary) and OpenRouter (fallback), with dynamic model selection
based on use case requirements.

Key Features:
- Automatic model selection based on use case
- Fallback routing for high availability
- Cost optimization through model tiering
- Performance monitoring and caching
- Unified interface for all LLM operations
"""

import os
import json
import time
import asyncio
from typing import Dict, Any, Optional, List, Union, Literal
from enum import Enum
import logging
from functools import lru_cache

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class UseCase(str, Enum):
    """Defined use cases with specific model requirements"""
    CODE_GENERATION = "code_generation"
    ARCHITECTURE_DESIGN = "architecture_design"
    DEBUGGING = "debugging"
    DOCUMENTATION = "documentation"
    CHAT_CONVERSATION = "chat_conversation"
    MEMORY_PROCESSING = "memory_processing"
    WORKFLOW_ORCHESTRATION = "workflow_orchestration"
    GENERAL_PURPOSE = "general_purpose"


class ModelTier(str, Enum):
    """Model tiers for cost optimization"""
    PREMIUM = "premium"  # Most capable, highest cost
    STANDARD = "standard"  # Balanced performance/cost
    ECONOMY = "economy"  # Fast, low cost


class RouterConfig(BaseModel):
    """Configuration for the unified LLM router"""
    portkey_api_key: str = Field(default_factory=lambda: os.getenv("PORTKEY_API_KEY", ""))
    portkey_config: str = Field(default_factory=lambda: os.getenv("PORTKEY_CONFIG", ""))
    openrouter_api_key: str = Field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))
    enable_fallback: bool = True
    enable_caching: bool = True
    cache_ttl: int = 3600  # 1 hour
    max_retries: int = 3
    timeout: int = 30
    enable_monitoring: bool = True


class ModelMapping(BaseModel):
    """Model mapping for each use case and tier"""
    use_case: UseCase
    tier: ModelTier
    primary_model: str
    fallback_models: List[str]
    max_tokens: int
    temperature: float
    system_prompt: Optional[str] = None


class UnifiedLLMRouter:
    """
    Unified router for all LLM operations in Orchestra.
    
    This router automatically selects the best model based on use case,
    handles fallbacks, and provides a consistent interface across the project.
    """
    
    # Model mappings for each use case and tier
    MODEL_MAPPINGS: Dict[UseCase, Dict[ModelTier, ModelMapping]] = {
        UseCase.CODE_GENERATION: {
            ModelTier.PREMIUM: ModelMapping(
                use_case=UseCase.CODE_GENERATION,
                tier=ModelTier.PREMIUM,
                primary_model="anthropic/claude-3-opus",
                fallback_models=["openai/gpt-4-turbo", "google/gemini-1.5-pro"],
                max_tokens=4096,
                temperature=0.2,
                system_prompt="You are an expert software engineer focused on writing clean, efficient, and well-documented code."
            ),
            ModelTier.STANDARD: ModelMapping(
                use_case=UseCase.CODE_GENERATION,
                tier=ModelTier.STANDARD,
                primary_model="anthropic/claude-3-sonnet",
                fallback_models=["openai/gpt-4", "google/gemini-1.5-flash"],
                max_tokens=2048,
                temperature=0.3
            ),
            ModelTier.ECONOMY: ModelMapping(
                use_case=UseCase.CODE_GENERATION,
                tier=ModelTier.ECONOMY,
                primary_model="anthropic/claude-3-haiku",
                fallback_models=["openai/gpt-3.5-turbo", "mistralai/mixtral-8x7b"],
                max_tokens=1024,
                temperature=0.3
            )
        },
        UseCase.ARCHITECTURE_DESIGN: {
            ModelTier.PREMIUM: ModelMapping(
                use_case=UseCase.ARCHITECTURE_DESIGN,
                tier=ModelTier.PREMIUM,
                primary_model="google/gemini-1.5-pro",
                fallback_models=["anthropic/claude-3-opus", "openai/gpt-4-turbo"],
                max_tokens=8192,
                temperature=0.7,
                system_prompt="You are a senior software architect with expertise in distributed systems and cloud architecture."
            ),
            ModelTier.STANDARD: ModelMapping(
                use_case=UseCase.ARCHITECTURE_DESIGN,
                tier=ModelTier.STANDARD,
                primary_model="google/gemini-1.5-flash",
                fallback_models=["anthropic/claude-3-sonnet", "openai/gpt-4"],
                max_tokens=4096,
                temperature=0.6
            )
        },
        UseCase.DEBUGGING: {
            ModelTier.PREMIUM: ModelMapping(
                use_case=UseCase.DEBUGGING,
                tier=ModelTier.PREMIUM,
                primary_model="openai/gpt-4-turbo",
                fallback_models=["anthropic/claude-3-opus", "google/gemini-1.5-pro"],
                max_tokens=4096,
                temperature=0.1,
                system_prompt="You are an expert debugger. Analyze code systematically and provide precise solutions."
            )
        },
        UseCase.DOCUMENTATION: {
            ModelTier.STANDARD: ModelMapping(
                use_case=UseCase.DOCUMENTATION,
                tier=ModelTier.STANDARD,
                primary_model="anthropic/claude-3-sonnet",
                fallback_models=["openai/gpt-4", "google/gemini-1.5-flash"],
                max_tokens=4096,
                temperature=0.5,
                system_prompt="You are a technical writer creating clear, comprehensive documentation."
            )
        },
        UseCase.CHAT_CONVERSATION: {
            ModelTier.STANDARD: ModelMapping(
                use_case=UseCase.CHAT_CONVERSATION,
                tier=ModelTier.STANDARD,
                primary_model="anthropic/claude-3-sonnet",
                fallback_models=["openai/gpt-4", "google/gemini-1.5-flash"],
                max_tokens=2048,
                temperature=0.7
            ),
            ModelTier.ECONOMY: ModelMapping(
                use_case=UseCase.CHAT_CONVERSATION,
                tier=ModelTier.ECONOMY,
                primary_model="anthropic/claude-3-haiku",
                fallback_models=["openai/gpt-3.5-turbo", "mistralai/mixtral-8x7b"],
                max_tokens=1024,
                temperature=0.7
            )
        },
        UseCase.MEMORY_PROCESSING: {
            ModelTier.STANDARD: ModelMapping(
                use_case=UseCase.MEMORY_PROCESSING,
                tier=ModelTier.STANDARD,
                primary_model="google/gemini-1.5-flash",
                fallback_models=["anthropic/claude-3-haiku", "openai/gpt-3.5-turbo"],
                max_tokens=2048,
                temperature=0.3,
                system_prompt="Extract and structure information efficiently for memory storage."
            )
        },
        UseCase.WORKFLOW_ORCHESTRATION: {
            ModelTier.PREMIUM: ModelMapping(
                use_case=UseCase.WORKFLOW_ORCHESTRATION,
                tier=ModelTier.PREMIUM,
                primary_model="google/gemini-1.5-pro",
                fallback_models=["anthropic/claude-3-opus", "openai/gpt-4-turbo"],
                max_tokens=8192,
                temperature=0.4,
                system_prompt="You are an AI workflow orchestrator. Break down complex tasks and coordinate execution."
            )
        }
    }
    
    def __init__(self, config: Optional[RouterConfig] = None):
        """Initialize the unified LLM router"""
        self.config = config or RouterConfig()
        self._validate_config()
        
        # Initialize HTTP clients
        self.portkey_client = httpx.AsyncClient(
            base_url="https://api.portkey.ai/v1",
            headers={
                "x-portkey-api-key": self.config.portkey_api_key,
                "x-portkey-config": self.config.portkey_config,
                "Content-Type": "application/json"
            },
            timeout=self.config.timeout
        )
        
        self.openrouter_client = httpx.AsyncClient(
            base_url="https://openrouter.ai/api/v1",
            headers={
                "Authorization": f"Bearer {self.config.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": os.getenv("OR_SITE_URL", "https://orchestra.ai"),
                "X-Title": os.getenv("OR_APP_NAME", "Orchestra AI")
            },
            timeout=self.config.timeout
        )
        
        # Cache for responses
        self._cache: Dict[str, Any] = {}
        
        # Metrics tracking
        self.metrics = {
            "requests": 0,
            "successes": 0,
            "failures": 0,
            "fallbacks": 0,
            "cache_hits": 0,
            "total_tokens": 0,
            "total_cost": 0.0
        }
    
    def _validate_config(self):
        """Validate router configuration"""
        if not self.config.portkey_api_key and not self.config.openrouter_api_key:
            raise ValueError("At least one API key (Portkey or OpenRouter) must be provided")
    
    @lru_cache(maxsize=128)
    def get_model_mapping(
        self, 
        use_case: UseCase, 
        tier: ModelTier = ModelTier.STANDARD
    ) -> ModelMapping:
        """Get model mapping for a specific use case and tier"""
        use_case_mappings = self.MODEL_MAPPINGS.get(use_case, {})
        
        # Fall back to standard tier if requested tier not available
        if tier not in use_case_mappings and ModelTier.STANDARD in use_case_mappings:
            tier = ModelTier.STANDARD
        
        # Fall back to general purpose if use case not found
        if not use_case_mappings:
            use_case = UseCase.GENERAL_PURPOSE
            use_case_mappings = self.MODEL_MAPPINGS.get(use_case, {})
        
        mapping = use_case_mappings.get(tier)
        if not mapping:
            # Create default mapping
            mapping = ModelMapping(
                use_case=use_case,
                tier=tier,
                primary_model="anthropic/claude-3-sonnet",
                fallback_models=["openai/gpt-4", "google/gemini-1.5-flash"],
                max_tokens=2048,
                temperature=0.5
            )
        
        return mapping
    
    def _get_cache_key(self, **kwargs) -> str:
        """Generate cache key from request parameters"""
        # Create deterministic cache key
        key_parts = []
        for k, v in sorted(kwargs.items()):
            if k not in ["stream", "cache"]:  # Exclude non-deterministic params
                if isinstance(v, (list, dict)):
                    v = json.dumps(v, sort_keys=True)
                key_parts.append(f"{k}:{v}")
        return ":".join(key_parts)
    
    async def _make_portkey_request(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """Make request through Portkey"""
        payload = {
            "model": model,
            "messages": messages,
            **kwargs
        }
        
        response = await self.portkey_client.post("/chat/completions", json=payload)
        response.raise_for_status()
        return response.json()
    
    async def _make_openrouter_request(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """Make request through OpenRouter"""
        # OpenRouter uses different model naming
        model_map = {
            "anthropic/claude-3-opus": "anthropic/claude-3-opus:beta",
            "anthropic/claude-3-sonnet": "anthropic/claude-3-sonnet:beta",
            "anthropic/claude-3-haiku": "anthropic/claude-3-haiku:beta",
            "google/gemini-1.5-pro": "google/gemini-pro-1.5",
            "google/gemini-1.5-flash": "google/gemini-flash-1.5"
        }
        
        payload = {
            "model": model_map.get(model, model),
            "messages": messages,
            **kwargs
        }
        
        response = await self.openrouter_client.post("/chat/completions", json=payload)
        response.raise_for_status()
        return response.json()
    
    async def complete(
        self,
        messages: Union[str, List[Dict[str, str]]],
        use_case: UseCase = UseCase.GENERAL_PURPOSE,
        tier: ModelTier = ModelTier.STANDARD,
        model_override: Optional[str] = None,
        temperature_override: Optional[float] = None,
        max_tokens_override: Optional[int] = None,
        system_prompt_override: Optional[str] = None,
        stream: bool = False,
        cache: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Main method for LLM completion with automatic routing.
        
        Args:
            messages: Either a string prompt or list of message dicts
            use_case: The use case for model selection
            tier: Model tier for cost/performance tradeoff
            model_override: Override automatic model selection
            temperature_override: Override default temperature
            max_tokens_override: Override default max tokens
            system_prompt_override: Override default system prompt
            stream: Whether to stream the response
            cache: Whether to use caching
            **kwargs: Additional parameters to pass to the LLM
        
        Returns:
            Dict containing the completion response
        """
        start_time = time.time()
        self.metrics["requests"] += 1
        
        # Convert string to messages format
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        
        # Get model mapping
        mapping = self.get_model_mapping(use_case, tier)
        
        # Apply overrides
        model = model_override or mapping.primary_model
        temperature = temperature_override or mapping.temperature
        max_tokens = max_tokens_override or mapping.max_tokens
        
        # Add system prompt if provided
        if system_prompt_override or mapping.system_prompt:
            system_prompt = system_prompt_override or mapping.system_prompt
            if messages[0].get("role") != "system":
                messages.insert(0, {"role": "system", "content": system_prompt})
        
        # Check cache
        if cache and self.config.enable_caching and not stream:
            cache_key = self._get_cache_key(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            if cache_key in self._cache:
                self.metrics["cache_hits"] += 1
                logger.debug(f"Cache hit for {use_case.value} request")
                return self._cache[cache_key]
        
        # Prepare request parameters
        request_params = {
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
            **kwargs
        }
        
        # Try primary model through Portkey
        last_error = None
        models_to_try = [model] + mapping.fallback_models
        
        for i, current_model in enumerate(models_to_try):
            try:
                if i == 0 and self.config.portkey_api_key:
                    # Try Portkey first
                    logger.debug(f"Trying {current_model} via Portkey for {use_case.value}")
                    response = await self._make_portkey_request(
                        current_model, messages, **request_params
                    )
                elif self.config.openrouter_api_key and self.config.enable_fallback:
                    # Fallback to OpenRouter
                    logger.debug(f"Trying {current_model} via OpenRouter for {use_case.value}")
                    self.metrics["fallbacks"] += 1
                    response = await self._make_openrouter_request(
                        current_model, messages, **request_params
                    )
                else:
                    continue
                
                # Success - update metrics
                self.metrics["successes"] += 1
                
                # Extract token usage
                usage = response.get("usage", {})
                self.metrics["total_tokens"] += usage.get("total_tokens", 0)
                
                # Cache successful response
                if cache and self.config.enable_caching and not stream:
                    self._cache[cache_key] = response
                
                # Log performance
                elapsed = time.time() - start_time
                logger.info(
                    f"LLM request completed: use_case={use_case.value}, "
                    f"model={current_model}, elapsed={elapsed:.2f}s, "
                    f"tokens={usage.get('total_tokens', 0)}"
                )
                
                return response
                
            except Exception as e:
                last_error = e
                logger.warning(f"Failed with {current_model}: {str(e)}")
                
                # Exponential backoff for retries
                if i < len(models_to_try) - 1:
                    await asyncio.sleep(2 ** i)
        
        # All attempts failed
        self.metrics["failures"] += 1
        logger.error(f"All models failed for {use_case.value}: {str(last_error)}")
        raise Exception(f"LLM request failed after trying all models: {str(last_error)}")
    
    async def complete_with_tools(
        self,
        messages: Union[str, List[Dict[str, str]]],
        tools: List[Dict[str, Any]],
        use_case: UseCase = UseCase.GENERAL_PURPOSE,
        **kwargs
    ) -> Dict[str, Any]:
        """Complete with tool/function calling support"""
        # Only premium models support tools reliably
        return await self.complete(
            messages=messages,
            use_case=use_case,
            tier=ModelTier.PREMIUM,
            tools=tools,
            **kwargs
        )
    
    async def embed(
        self,
        text: Union[str, List[str]],
        model: str = "openai/text-embedding-3-small"
    ) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for text"""
        is_single = isinstance(text, str)
        texts = [text] if is_single else text
        
        payload = {
            "model": model,
            "input": texts
        }
        
        # Try Portkey first, then OpenRouter
        try:
            if self.config.portkey_api_key:
                response = await self.portkey_client.post("/embeddings", json=payload)
            else:
                response = await self.openrouter_client.post("/embeddings", json=payload)
            
            response.raise_for_status()
            data = response.json()
            
            embeddings = [item["embedding"] for item in data["data"]]
            return embeddings[0] if is_single else embeddings
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get router metrics"""
        return {
            **self.metrics,
            "success_rate": (
                self.metrics["successes"] / self.metrics["requests"] 
                if self.metrics["requests"] > 0 else 0
            ),
            "cache_hit_rate": (
                self.metrics["cache_hits"] / self.metrics["requests"]
                if self.metrics["requests"] > 0 else 0
            ),
            "average_tokens": (
                self.metrics["total_tokens"] / self.metrics["successes"]
                if self.metrics["successes"] > 0 else 0
            )
        }
    
    async def close(self):
        """Close HTTP clients"""
        await self.portkey_client.aclose()
        await self.openrouter_client.aclose()


# Singleton instance
_router_instance: Optional[UnifiedLLMRouter] = None


def get_llm_router(config: Optional[RouterConfig] = None) -> UnifiedLLMRouter:
    """Get or create the singleton LLM router instance"""
    global _router_instance
    if _router_instance is None:
        _router_instance = UnifiedLLMRouter(config)
    return _router_instance


# Convenience functions for common use cases
async def generate_code(
    prompt: str,
    tier: ModelTier = ModelTier.STANDARD,
    **kwargs
) -> str:
    """Generate code using the appropriate model"""
    router = get_llm_router()
    response = await router.complete(
        prompt,
        use_case=UseCase.CODE_GENERATION,
        tier=tier,
        **kwargs
    )
    return response["choices"][0]["message"]["content"]


async def design_architecture(
    requirements: str,
    tier: ModelTier = ModelTier.PREMIUM,
    **kwargs
) -> str:
    """Design system architecture based on requirements"""
    router = get_llm_router()
    response = await router.complete(
        requirements,
        use_case=UseCase.ARCHITECTURE_DESIGN,
        tier=tier,
        **kwargs
    )
    return response["choices"][0]["message"]["content"]


async def debug_code(
    code: str,
    error: str,
    **kwargs
) -> str:
    """Debug code with error context"""
    router = get_llm_router()
    prompt = f"Debug this code:\n\n{code}\n\nError:\n{error}"
    response = await router.complete(
        prompt,
        use_case=UseCase.DEBUGGING,
        tier=ModelTier.PREMIUM,
        **kwargs
    )
    return response["choices"][0]["message"]["content"]


async def chat(
    message: str,
    history: Optional[List[Dict[str, str]]] = None,
    tier: ModelTier = ModelTier.STANDARD,
    **kwargs
) -> str:
    """Chat conversation with context"""
    router = get_llm_router()
    messages = history or []
    messages.append({"role": "user", "content": message})
    
    response = await router.complete(
        messages,
        use_case=UseCase.CHAT_CONVERSATION,
        tier=tier,
        **kwargs
    )
    return response["choices"][0]["message"]["content"]
