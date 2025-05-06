"""
LLM Provider Exceptions for AI Orchestration System.

This module defines specific exception types for LLM provider interactions,
allowing more granular error handling and appropriate recovery strategies.
"""


class LLMProviderError(Exception):
    """Base exception for all LLM provider errors."""

    pass


class LLMProviderConnectionError(LLMProviderError):
    """Error connecting to the LLM provider service."""

    pass


class LLMProviderAuthenticationError(LLMProviderError):
    """Authentication failure with the LLM provider."""

    pass


class LLMProviderRateLimitError(LLMProviderError):
    """Rate limit exceeded for the LLM provider."""

    pass


class LLMProviderResourceExhaustedError(LLMProviderError):
    """Resource exhausted (e.g., token quota) for the LLM provider."""

    pass


class LLMProviderInvalidRequestError(LLMProviderError):
    """Invalid request parameters sent to the LLM provider."""

    pass


class LLMProviderServiceError(LLMProviderError):
    """Internal server error from the LLM provider."""

    pass


class LLMProviderTimeoutError(LLMProviderError):
    """Request to the LLM provider timed out."""

    pass


class LLMProviderModelError(LLMProviderError):
    """Error related to the specific model requested."""

    pass
