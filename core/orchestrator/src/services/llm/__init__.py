"""
LLM Services for AI Orchestration System.

This module provides LLM provider interfaces and implementations
that can be used to generate text responses for agents.
"""

from core.orchestrator.src.services.llm.exceptions import (
    LLMProviderError,
    LLMProviderAuthenticationError,
    LLMProviderConnectionError,
    LLMProviderRateLimitError,
    LLMProviderResourceExhaustedError,
    LLMProviderInvalidRequestError,
    LLMProviderServiceError,
    LLMProviderTimeoutError,
    LLMProviderModelError,
)

from core.orchestrator.src.services.llm.providers import (
    LLMProvider,
    OpenRouterProvider,
    get_llm_provider,
    register_llm_provider,
)

__all__ = [
    # Provider interface and implementations
    "LLMProvider",
    "OpenRouterProvider",
    # Provider factory functions
    "get_llm_provider",
    "register_llm_provider",
    # Exception types
    "LLMProviderError",
    "LLMProviderAuthenticationError",
    "LLMProviderConnectionError",
    "LLMProviderRateLimitError",
    "LLMProviderResourceExhaustedError",
    "LLMProviderInvalidRequestError",
    "LLMProviderServiceError",
    "LLMProviderTimeoutError",
    "LLMProviderModelError",
]
