"""
"""
    """Provider-specific configuration for LLM models."""
    """
    """
        "openai": "PORTKEY_VIRTUAL_KEY_OPENAI",
        "anthropic": "PORTKEY_VIRTUAL_KEY_ANTHROPIC",
        "openrouter": "PORTKEY_VIRTUAL_KEY_OPENROUTER",
        "mistral": "PORTKEY_VIRTUAL_KEY_MISTRAL",
        "huggingface": "PORTKEY_VIRTUAL_KEY_HUGGINGFACE",
        "cohere": "PORTKEY_VIRTUAL_KEY_COHERE",
        "perplexity": "PORTKEY_VIRTUAL_KEY_PERPLEXITY",
        "google": "PORTKEY_VIRTUAL_KEY_GOOGLE",
    }

    # Map of provider names to their default model attribute names in settings
    default_model_attrs = {
        "openai": "DEFAULT_LLM_MODEL_FALLBACK_OPENAI",
        "anthropic": "DEFAULT_LLM_MODEL_FALLBACK_ANTHROPIC",
        "openrouter": "DEFAULT_LLM_MODEL_PRIMARY",
    }

    # Get the virtual key for this provider if available
    virtual_key = None
    if provider_lower in virtual_key_attrs:
        virtual_key_attr = virtual_key_attrs[provider_lower]
        virtual_key = getattr(settings, virtual_key_attr, None)

    # Get the default model for this provider if available
    default_model = None
    if provider_lower in default_model_attrs:
        default_model_attr = default_model_attrs[provider_lower]
        default_model = getattr(settings, default_model_attr, None)

    # If no provider-specific model is found, use the default
    if not default_model:
        default_model = settings.DEFAULT_LLM_MODEL

    # Portkey API Gateway URL
    portkey_gateway_url = "https://api.portkey.ai/v1/gateway"

    return LLMProviderConfig(
        provider=provider_lower,
        api_key=settings.PORTKEY_API_KEY,
        base_url=portkey_gateway_url,
        virtual_key=virtual_key,
        default_model=default_model,
        extra_params={},
    )

def get_model_name_for_provider(model_name: str, provider: str) -> str:
    """
    """
    if "/" not in model_name:
        return f"{provider}/{model_name}"
    return model_name
