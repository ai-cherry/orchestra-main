"""
Header Validation for LLM Providers
-----------------------------------

This module provides middleware that validates request headers for different LLM providers,
ensuring that all required headers for each provider are present before processing requests.
It helps prevent hard-to-diagnose errors when calling provider APIs.

Usage:
    from fastapi import FastAPI, Request
    from core.orchestrator.src.services.llm.header_validation import validate_provider_headers

    app = FastAPI()

    @app.middleware("http")
    async def validate_headers_middleware(request: Request, call_next):
        # Validate headers based on provider in the URL or path parameters
        provider = extract_provider_from_request(request)
        if provider:
            validate_provider_headers(request.headers, provider)
        return await call_next(request)
"""

import logging
from typing import Dict, List, Mapping, Optional, Set, Union
from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)

# Define required headers for each provider
PROVIDER_REQUIRED_HEADERS = {
    "portkey": {"x-portkey-provider", "x-portkey-config"},
    "openrouter": {"referer", "http-referer"},  # Only one of these is actually needed
    "anthropic": {"anthropic-version"},
    "openai": {"openai-organization"},  # Only required for some org accounts
}

# Map model prefixes to providers
MODEL_PROVIDER_MAP = {
    "gpt-": "openai",
    "claude-": "anthropic",
    "llama-": "openrouter",
    "mistral-": "openrouter",
}


def validate_provider_headers(headers: Mapping[str, str], provider: str, strict: bool = False) -> bool:
    """
    Validate that all required headers for a given provider are present.

    Args:
        headers: HTTP headers dictionary or mapping
        provider: Provider name (e.g., "portkey", "openrouter")
        strict: If True, raise an exception if required headers are missing
               If False, just log a warning and return status

    Returns:
        True if all required headers are present, False otherwise

    Raises:
        HTTPException: If strict=True and required headers are missing
    """
    provider = provider.lower()

    # Get the required headers for this provider
    required_headers = PROVIDER_REQUIRED_HEADERS.get(provider, set())
    if not required_headers:
        # No specific headers required for this provider
        return True

    # Convert headers to lowercase for case-insensitive comparison
    normalized_headers = {k.lower(): v for k, v in headers.items()}

    # Check if all required headers are present
    missing_headers = [h for h in required_headers if h.lower() not in normalized_headers]

    if missing_headers:
        missing_str = ", ".join(missing_headers)
        message = f"Missing required headers for provider '{provider}': {missing_str}"
        logger.warning(message)

        if strict:
            raise HTTPException(status_code=400, detail=message)
        return False

    return True


def extract_provider_from_model(model_name: str) -> Optional[str]:
    """
    Extract the provider name from a model name.

    Args:
        model_name: The name of the model (e.g., "gpt-4", "claude-3-opus")

    Returns:
        Provider name if recognized, None otherwise
    """
    if not model_name:
        return None

    # Check for explicit provider prefix (e.g., "openai/gpt-4")
    if "/" in model_name:
        parts = model_name.split("/", 1)
        if len(parts) > 0:
            return parts[0].lower()

    # Check for model pattern (e.g., "gpt-" -> "openai")
    for prefix, provider in MODEL_PROVIDER_MAP.items():
        if model_name.lower().startswith(prefix.lower()):
            return provider

    return None


def extract_provider_from_request(request: Request) -> Optional[str]:
    """
    Extract the provider from a request object. Tries to determine the provider from:
    1. URL path parameters
    2. Query parameters
    3. Request body (if JSON)

    Args:
        request: FastAPI Request object

    Returns:
        Provider name if it can be determined, None otherwise
    """
    # Check path parameters
    provider = request.path_params.get("provider")
    if provider:
        return provider.lower()

    # Check query parameters
    provider_query = request.query_params.get("provider")
    if provider_query:
        return provider_query.lower()

    # Check model name in query parameters
    model = request.query_params.get("model")
    if model:
        provider = extract_provider_from_model(model)
        if provider:
            return provider

    # Try to get from body if it's a JSON request
    if request.headers.get("content-type") == "application/json":
        try:
            # FastAPI's Request doesn't directly expose the body,
            # and reading the body is async, so this would need
            # to be done in an async middleware
            pass
        except Exception:
            pass

    return None


async def validate_headers_middleware(request: Request, call_next):
    """
    FastAPI middleware to validate headers based on the provider.

    Args:
        request: FastAPI Request object
        call_next: Next middleware or route handler

    Returns:
        Response from the next middleware or route handler
    """
    provider = extract_provider_from_request(request)
    if provider:
        # Log but don't block if headers are missing
        validate_provider_headers(request.headers, provider, strict=False)

    response = await call_next(request)
    return response
