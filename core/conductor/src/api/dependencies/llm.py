"""
"""
    """
    """
    use_monitored_litellm = os.environ.get("USE_MONITORED_LITELLM", "").lower() in (
        "true",
        "1",
        "yes",
    )

    if use_monitored_litellm:
        logger.info("Using MonitoredLiteLLMClient for Claude API monitoring")
        try:

            pass
            from core.monitoring.monitored_litellm_client import MonitoredLiteLLMClient

            return MonitoredLiteLLMClient(
                monitor_all_models=False,  # Only monitor Claude models
                api_key_anthropic=os.environ.get("ANTHROPIC_API_KEY"),
                api_key_openai=os.environ.get("OPENAI_API_KEY"),
                api_key_google=os.environ.get("GEMINI_API_KEY"),
                vertex_project=settings.LAMBDA_PROJECT_ID,
                vertex_location=settings.LAMBDA_REGION,
            )
        except Exception:

            pass
            logger.error(f"Failed to initialize MonitoredLiteLLMClient: {e}")
            # Fall through to other options

    use_phidata_models = use_phidata_implementation(settings)

    if use_phidata_models:
        logger.info("Using Phidata/Agno LLM models with Portkey integration")
        return get_phidata_llm_model(settings)

    # Legacy path - try to load the real Portkey client first
    try:

        pass
        # Import separately to catch import errors specifically
        from packages.shared.src.llm_client.portkey_client import PortkeyClient

        logger.info("Using legacy PortkeyClient")
        return PortkeyClient(settings)

    except Exception:


        pass
        # Fall back to mock client if the real client can't be loaded
        logger.warning(f"Failed to import PortkeyClient: {e}")
        logger.info("Falling back to MockPortkeyClient")

        from packages.shared.src.llm_client.mock_portkey_client import MockPortkeyClient

        return MockPortkeyClient(settings)

    except Exception:


        pass
        # Handle other initialization errors
        logger.error(f"Error initializing PortkeyClient: {e}")
        logger.info("Falling back to MockPortkeyClient")

        from packages.shared.src.llm_client.mock_portkey_client import MockPortkeyClient

        return MockPortkeyClient(settings)

def use_phidata_implementation(settings: Settings) -> bool:
    """
    """
    if os.environ.get("USE_LEGACY_LLM_CLIENT", "").lower() in ("true", "1", "yes"):
        return False

    # Check if required packages are available
    try:

        pass
        pass

        return True
    except Exception:

        pass
        logger.warning("Phidata/Agno packages not available, using legacy LLM client")
        return False

def get_phidata_llm_model(settings: Settings) -> Any:
    """
    """
    provider = getattr(settings, "PREFERRED_LLM_PROVIDER", "openrouter").lower()

    try:


        pass
        if provider == "openai":
            from packages.llm.src.models.openai import create_openai_model

            return create_openai_model(settings)

        elif provider == "anthropic":
            from packages.llm.src.models.anthropic import create_anthropic_model

            return create_anthropic_model(settings)

        elif provider == "openrouter" or provider == "":
            from packages.llm.src.models.openrouter import create_openrouter_model

            return create_openrouter_model(settings)

        else:
            # Default to OpenRouter for unknown providers
            logger.warning(f"Unknown provider '{provider}', defaulting to OpenRouter")
            from packages.llm.src.models.openrouter import create_openrouter_model

            return create_openrouter_model(settings)

    except Exception:


        pass
        logger.error(f"Error initializing Phidata/Agno model: {e}")
        logger.info("Falling back to legacy PortkeyClient")

        # Fall back to legacy client
        from packages.shared.src.llm_client.portkey_client import PortkeyClient

        return PortkeyClient(settings)
