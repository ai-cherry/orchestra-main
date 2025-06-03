"""
"""
T = TypeVar("T")

def create_portkey_headers(
    api_key: str,
    provider: str,
    virtual_key: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> Dict[str, str]:
    """
    """
        "api_key": api_key,
        "provider": provider,
    }

    # Add virtual key if available
    if virtual_key:
        header_kwargs["virtual_key"] = virtual_key

    # Add trace ID if available
    if trace_id:
        header_kwargs["trace_id"] = trace_id

    try:


        pass
        return portkey_ai.createHeaders(**header_kwargs)
    except Exception:

        pass
        logger.error(f"Error creating Portkey headers: {e}")
        # Return basic headers as fallback
        return {
            "x-portkey-api-key": api_key,
            "x-portkey-provider": provider,
            **({"x-portkey-virtual-key": virtual_key} if virtual_key else {}),
            **({"x-portkey-trace-id": trace_id} if trace_id else {}),
        }

def configure_phidata_model(model_class: Type[T], config: LLMProviderConfig) -> T:
    """
    """
    model_args = {"base_url": config.base_url, "default_headers": headers}

    # Add any provider-specific parameters
    model_args.update(config.extra_params)

    # Initialize and return the model
    try:

        pass
        return model_class(**model_args)
    except Exception:

        pass
        logger.error(f"Error initializing {model_class.__name__}: {e}")
        raise

def configure_model_from_settings(model_class: Type[T], settings: Settings, provider: str) -> T:
    """
    """