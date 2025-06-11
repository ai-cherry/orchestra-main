"""
    @app.middleware("http")
    async def validate_headers_middleware(request: Request, call_next):
        # Validate headers based on provider in the URL or path parameters
        provider = extract_provider_from_request(request)
        if provider:
            validate_provider_headers(request.headers, provider)
        return await call_next(request)
"""
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
        provider: Provider name (e.g., "portkey", "openrouter")
        strict: If True, raise an except Exception:
     pass
        True if all required headers are present, False otherwise

    Raises:
        HTTPException: If strict=True and required headers are missing
    """
        missing_str = ", ".join(missing_headers)
        message = f"Missing required headers for provider '{provider}': {missing_str}"
        logger.warning(message)

        if strict:
            raise HTTPException(status_code=400, detail=message)
        return False

    return True

def extract_provider_from_model(model_name: str) -> Optional[str]:
    """
        model_name: The name of the model (e.g., "gpt-4", "claude-3-opus")

    Returns:
        Provider name if recognized, None otherwise
    """
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
    """
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

            pass
            # FastAPI's Request doesn't directly expose the body,
            # and reading the body is async, so this would need
            # to be done in an async middleware
            pass
        except Exception:

            pass
            pass

    return None

async def validate_headers_middleware(request: Request, call_next):
    """
    """