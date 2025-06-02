"""
LLM Provider Exceptions for AI Orchestration System.

This module defines specific exception types for LLM provider interactions,
allowing more granular error handling and appropriate recovery strategies.
"""

class LLMProviderError(Exception):
    """Base exception for all LLM provider errors."""

class LLMProviderConnectionError(LLMProviderError):
    """Error connecting to the LLM provider service."""

class LLMProviderAuthenticationError(LLMProviderError):
    """Authentication failure with the LLM provider."""

class LLMProviderRateLimitError(LLMProviderError):
    """Rate limit exceeded for the LLM provider."""

class LLMProviderResourceExhaustedError(LLMProviderError):
    """Resource exhausted (e.g., token quota) for the LLM provider."""

class LLMProviderInvalidRequestError(LLMProviderError):
    """Invalid request parameters sent to the LLM provider."""

class LLMProviderServiceError(LLMProviderError):
    """Internal server error from the LLM provider."""

class LLMProviderTimeoutError(LLMProviderError):
    """Request to the LLM provider timed out."""

class LLMProviderModelError(LLMProviderError):
    """Error related to the specific model requested."""
