"""
LLM provider integration using Portkey.

This module provides a unified interface for LLM providers
using Portkey for intelligent routing and fallbacks.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from portkey_ai import Portkey

from core.business.personas.base import PersonaConfig
from core.infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    GOOGLE = "google"
    COHERE = "cohere"

class CompletionMode(Enum):
    """Completion modes for different use cases."""

    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"

@dataclass
class LLMRequest:
    """Request to an LLM provider."""

    prompt: str
    mode: CompletionMode = CompletionMode.CHAT
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    stop_sequences: Optional[List[str]] = None
    system_prompt: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class LLMResponse:
    """Response from an LLM provider."""

    text: str
    provider: LLMProvider
    model: str
    usage: Dict[str, int]
    latency_ms: float
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class LLMService:
    """
    Unified LLM service using Portkey for routing.

    Features:
    - Automatic provider selection
    - Fallback handling
    - Cost optimization
    - Response caching
    - Usage tracking
    """

    def __init__(self):
        self.settings = get_settings()
        self._portkey_client = None
        self._provider_configs = {}
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Initialize provider configurations."""
        # OpenAI configuration
        if self.settings.llm.openai_api_key:
            self._provider_configs[LLMProvider.OPENAI] = {
                "api_key": self.settings.llm.openai_api_key.get_secret_value(),
                "models": ["gpt-4", "gpt-3.5-turbo"],
                "priority": 1,
            }

        # Anthropic configuration
        if self.settings.llm.anthropic_api_key:
            self._provider_configs[LLMProvider.ANTHROPIC] = {
                "api_key": self.settings.llm.anthropic_api_key.get_secret_value(),
                "models": ["claude-3-opus", "claude-3-sonnet"],
                "priority": 2,
            }

        # OpenRouter configuration
        if self.settings.llm.openrouter_api_key:
            self._provider_configs[LLMProvider.OPENROUTER] = {
                "api_key": self.settings.llm.openrouter_api_key.get_secret_value(),
                "models": ["openrouter/auto"],
                "priority": 3,
            }

        # Initialize Portkey client if API key is available
        if self.settings.llm.portkey_api_key:
            self._portkey_client = Portkey(
                api_key=self.settings.llm.portkey_api_key.get_secret_value(),
                config={
                    "retry": {
                        "attempts": 3,
                        "on_status_codes": [429, 500, 502, 503, 504],
                    },
                    "cache": {"mode": "semantic", "max_age": 3600},
                },
            )

    async def complete(
        self,
        request: LLMRequest,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
    ) -> LLMResponse:
        """
        Complete a request using the specified or best available provider.

        Args:
            request: The LLM request
            provider: Specific provider to use (auto-selected if None)
            model: Specific model to use (auto-selected if None)

        Returns:
            LLM response with completion text and metadata
        """
        # Use Portkey if available
        if self._portkey_client:
            return await self._complete_with_portkey(request, provider, model)

        # Fallback to direct provider calls
        return await self._complete_direct(request, provider, model)

    async def _complete_with_portkey(
        self,
        request: LLMRequest,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
    ) -> LLMResponse:
        """Complete using Portkey for intelligent routing."""
        import time

        start_time = time.time()

        # Build Portkey configuration
        config = {"mode": "fallback", "targets": []}

        # Add providers based on priority
        sorted_providers = sorted(self._provider_configs.items(), key=lambda x: x[1].get("priority", 999))

        for provider_enum, provider_config in sorted_providers:
            if provider and provider != provider_enum:
                continue

            target = {
                "provider": provider_enum.value,
                "api_key": provider_config["api_key"],
            }

            if model:
                target["model"] = model
            else:
                # Use first available model
                target["model"] = provider_config["models"][0]

            config["targets"].append(target)

        # Make the request
        try:
            if request.mode == CompletionMode.CHAT:
                messages = []

                if request.system_prompt:
                    messages.append({"role": "system", "content": request.system_prompt})

                messages.append({"role": "user", "content": request.prompt})

                response = await self._portkey_client.chat.completions.create(
                    messages=messages,
                    max_tokens=request.max_tokens or self.settings.llm.max_tokens,
                    temperature=request.temperature or self.settings.llm.temperature,
                    top_p=request.top_p,
                    stop=request.stop_sequences,
                    config=config,
                )

                # Extract response
                text = response.choices[0].message.content
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            else:
                # Text completion mode
                response = await self._portkey_client.completions.create(
                    prompt=request.prompt,
                    max_tokens=request.max_tokens or self.settings.llm.max_tokens,
                    temperature=request.temperature or self.settings.llm.temperature,
                    top_p=request.top_p,
                    stop=request.stop_sequences,
                    config=config,
                )

                text = response.choices[0].text
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            latency_ms = (time.time() - start_time) * 1000

            # Determine which provider was actually used
            actual_provider = LLMProvider.OPENAI  # Default
            actual_model = response.model

            # Parse provider from model name if available
            if "/" in actual_model:
                provider_str = actual_model.split("/")[0]
                for p in LLMProvider:
                    if p.value == provider_str:
                        actual_provider = p
                        break

            return LLMResponse(
                text=text,
                provider=actual_provider,
                model=actual_model,
                usage=usage,
                latency_ms=latency_ms,
                metadata={
                    "portkey_request_id": response.id,
                    "cached": getattr(response, "_cached", False),
                },
            )

        except Exception as e:
            logger.error(f"Portkey completion failed: {e}")
            raise

    async def _complete_direct(
        self,
        request: LLMRequest,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
    ) -> LLMResponse:
        """Direct completion without Portkey (fallback)."""
        # This would implement direct API calls to providers
        # For now, we'll raise an error
        raise NotImplementedError("Direct provider calls not yet implemented")

    async def complete_with_persona(
        self,
        prompt: str,
        persona: PersonaConfig,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
    ) -> LLMResponse:
        """Complete a request with persona configuration."""
        # Build system prompt from persona
        system_prompt = self._build_system_prompt(persona)

        # Create request
        request = LLMRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=persona.temperature,
            max_tokens=persona.max_tokens,
            metadata={"persona_id": persona.id},
        )

        # Complete the request
        response = await self.complete(request, provider, model)

        # Add persona info to response metadata
        response.metadata["persona_id"] = persona.id
        response.metadata["persona_name"] = persona.name

        return response

    def _build_system_prompt(self, persona: PersonaConfig) -> str:
        """Build system prompt from persona configuration."""
        if persona.system_prompt:
            return persona.system_prompt

        # Build default system prompt from traits and style
        prompt_parts = [
            f"You are {persona.name}, {persona.description}.",
            f"Your communication style is {persona.style.value}.",
        ]

        if persona.traits:
            traits_str = ", ".join(trait.value for trait in persona.traits)
            prompt_parts.append(f"Your key traits are: {traits_str}.")

        return " ".join(prompt_parts)

    def estimate_cost(self, request: LLMRequest, provider: LLMProvider, model: str) -> float:
        """Estimate the cost of a request."""
        # Token estimation (rough)
        prompt_tokens = len(request.prompt.split()) * 1.3
        completion_tokens = (request.max_tokens or 500) * 0.7

        # Cost per 1K tokens (example rates)
        cost_rates = {
            ("openai", "gpt-4"): {"prompt": 0.03, "completion": 0.06},
            ("openai", "gpt-3.5-turbo"): {"prompt": 0.0015, "completion": 0.002},
            ("anthropic", "claude-3-opus"): {"prompt": 0.015, "completion": 0.075},
            ("anthropic", "claude-3-sonnet"): {"prompt": 0.003, "completion": 0.015},
        }

        # Get rate for provider/model
        key = (provider.value, model)
        rates = cost_rates.get(key, {"prompt": 0.001, "completion": 0.002})

        # Calculate cost
        prompt_cost = (prompt_tokens / 1000) * rates["prompt"]
        completion_cost = (completion_tokens / 1000) * rates["completion"]

        return prompt_cost + completion_cost

# Global instance
_llm_service: Optional[LLMService] = None

def get_llm_service() -> LLMService:
    """Get the global LLM service instance."""
    global _llm_service

    if _llm_service is None:
        _llm_service = LLMService()

    return _llm_service
