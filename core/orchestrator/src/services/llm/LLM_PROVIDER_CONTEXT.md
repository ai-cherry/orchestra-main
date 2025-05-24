# LLM Provider System Architecture

This document explains the LLM Provider architecture for AI coding assistants.

## Overview

The LLM Provider system creates an abstraction layer between the orchestration system and various Large Language Model providers. It handles authentication, request formatting, error handling, fallback mechanisms, and response parsing.

## Key Components

### LLMProvider Interface

Base abstract class that defines the provider interface:

- Initialization and shutdown lifecycle
- Text completion generation
- Chat completion generation
- Error handling and retry logic

### Provider Implementations

1. **OpenRouterProvider**

   - Primary LLM provider
   - Connects to multiple models through OpenRouter's API
   - Sophisticated error handling and retry mechanisms
   - Support for OpenRouter Pro Tier features
   - Agent-specific model routing

2. **PortkeyProvider**
   - Secondary/fallback LLM provider
   - Unified interface to multiple LLM providers
   - Simplified implementation for developer use

### Configuration System

The `LLMProviderConfig` class manages provider-specific settings:

- API keys and base URLs
- Default models
- Request timeouts
- Retry policies
- Error type classification

## Fallback Mechanism

The system includes a sophisticated fallback system:

1. Primary provider is attempted first (usually OpenRouter)
2. On failure, system falls back to secondary provider (usually Portkey)
3. Each provider has its own internal retry mechanism for transient errors
4. Errors are classified to determine if they should trigger retries or fallbacks

## Error Handling

The system defines a hierarchy of error types:

- `LLMProviderError`: Base exception class
- `LLMProviderConnectionError`: Network/connection issues
- `LLMProviderAuthenticationError`: Auth failures
- `LLMProviderRateLimitError`: Rate limiting
- `LLMProviderResourceExhaustedError`: Resource limits
- `LLMProviderInvalidRequestError`: Invalid requests
- `LLMProviderServiceError`: Provider-side errors
- `LLMProviderTimeoutError`: Request timeouts
- `LLMProviderModelError`: Issues with specific models

## Registry System

Providers are registered with a unified registry:

- `register_llm_provider(provider)` for registration
- `get_llm_provider(provider_name)` for retrieval
- Automatic initialization during application startup

## Usage Patterns

When requesting completions from LLM providers:

1. Use the `get_llm_provider()` function to get the appropriate provider
2. Always handle provider errors using try/except blocks
3. Use the async methods for non-blocking operation
4. Provide appropriate timeouts for user-facing interactions
5. Include proper context in the request to get quality responses

## Configuration Options

Key environment variables that affect provider behavior:

- `PREFERRED_LLM_PROVIDER`: Selects the default provider
- `OPENROUTER_API_KEY`: Authentication for OpenRouter
- `PORTKEY_API_KEY`: Authentication for Portkey
- `LLM_REQUEST_TIMEOUT`: Maximum wait time for responses
- `LLM_MAX_RETRIES`: Number of retry attempts
- `LLM_RETRY_DELAY`: Initial backoff delay
- `LLM_RETRY_MAX_DELAY`: Maximum backoff delay
- `OPENROUTER_DEFAULT_MODEL`: Default model to use

## Implementation Notes

1. **Retry Mechanism**: Uses exponential backoff with jitter
2. **Request Tracking**: Includes timing and token usage metrics
3. **Custom Headers**: Supports OpenRouter Pro Tier features
4. **Agent-Model Mapping**: Different models can be used for different agent types
5. **Graceful Degradation**: System continues functioning even if some providers fail
