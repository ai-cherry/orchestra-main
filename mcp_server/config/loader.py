"""
"""
    """
    """
    with open(file_path, "r") as f:
        config = json.load(f)
    return config

def load_config_from_env() -> Dict[str, Any]:
    """
    """
    config = {}

    # Main config
    if "MCP_DEBUG" in os.environ:
        config["debug"] = os.environ["MCP_DEBUG"].lower() == "true"

    if "MCP_LOG_LEVEL" in os.environ:
        config["log_level"] = os.environ["MCP_LOG_LEVEL"]

    if "MCP_PORT" in os.environ:
        config["port"] = int(os.environ["MCP_PORT"])

    if "MCP_HOST" in os.environ:
        config["host"] = os.environ["MCP_HOST"]

    # Storage config
    storage_config = {}
    if "MCP_STORAGE_TYPE" in os.environ:
        storage_config["type"] = os.environ["MCP_STORAGE_TYPE"]

    if "MCP_STORAGE_CONNECTION_STRING" in os.environ:
        storage_config["connection_string"] = os.environ["MCP_STORAGE_CONNECTION_STRING"]

    if "MCP_STORAGE_MAX_ENTRIES" in os.environ:
        storage_config["max_entries"] = int(os.environ["MCP_STORAGE_MAX_ENTRIES"])

    if "MCP_STORAGE_TTL_SECONDS" in os.environ:
        storage_config["ttl_seconds"] = int(os.environ["MCP_STORAGE_TTL_SECONDS"])

    if storage_config:
        config["storage"] = storage_config

    # Copilot config
    copilot_config = {}
    if "MCP_COPILOT_ENABLED" in os.environ:
        copilot_config["enabled"] = os.environ["MCP_COPILOT_ENABLED"].lower() == "true"

    if "MCP_COPILOT_API_KEY" in os.environ:
        copilot_config["api_key"] = os.environ["MCP_COPILOT_API_KEY"]
    elif "OPENAI_API_KEY" in os.environ:  # Fallback to OpenAI key if available
        copilot_config["api_key"] = os.environ["OPENAI_API_KEY"]

    if "MCP_COPILOT_TOKEN_LIMIT" in os.environ:
        copilot_config["token_limit"] = int(os.environ["MCP_COPILOT_TOKEN_LIMIT"])

    if "MCP_COPILOT_VSCODE_EXTENSION_PATH" in os.environ:
        copilot_config["vscode_extension_path"] = os.environ["MCP_COPILOT_VSCODE_EXTENSION_PATH"]

    if "MCP_COPILOT_USE_OPENAI_FALLBACK" in os.environ:
        copilot_config["use_openai_fallback"] = os.environ["MCP_COPILOT_USE_OPENAI_FALLBACK"].lower() == "true"

    if "MCP_COPILOT_OPENAI_MODEL" in os.environ:
        copilot_config["openai_model"] = os.environ["MCP_COPILOT_OPENAI_MODEL"]

    if copilot_config:
        config["copilot"] = copilot_config

    # Gemini config
    gemini_config = {}
    if "MCP_GEMINI_ENABLED" in os.environ:
        gemini_config["enabled"] = os.environ["MCP_GEMINI_ENABLED"].lower() == "true"

    if "MCP_GEMINI_API_KEY" in os.environ:
        gemini_config["api_key"] = os.environ["MCP_GEMINI_API_KEY"]
    elif "GOOGLE_AI_API_KEY" in os.environ:  # Fallback to Google AI key if available
        gemini_config["api_key"] = os.environ["GOOGLE_AI_API_KEY"]

    if "MCP_GEMINI_MODEL" in os.environ:
        gemini_config["model"] = os.environ["MCP_GEMINI_MODEL"]

    if "MCP_GEMINI_EMBEDDINGS_MODEL" in os.environ:
        gemini_config["embeddings_model"] = os.environ["MCP_GEMINI_EMBEDDINGS_MODEL"]

    if "MCP_GEMINI_TOKEN_LIMIT" in os.environ:
        gemini_config["token_limit"] = int(os.environ["MCP_GEMINI_TOKEN_LIMIT"])

    if gemini_config:
        config["gemini"] = gemini_config

    return config

def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    """
    result = base_config.copy()

    for key, value in override_config.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            # Recursively merge nested dictionaries
            result[key] = merge_configs(result[key], value)
        else:
            # Override base value with override value
            result[key] = value

    return result

def load_config(config_path: Optional[str] = "mcp_config.json") -> MCPConfig:
    """
    """
            logger.info(f"Loaded configuration from file: {config_path}")
        except Exception:

            pass
            logger.warning(f"Config file not found: {config_path}")
        except Exception:

            pass
            logger.error(f"Invalid JSON in config file: {config_path}")
        except Exception:

            pass
            logger.error(f"Error loading config file: {e}")

    # Load from environment variables
    try:

        pass
        env_config = load_config_from_env()
        config_dict = merge_configs(config_dict, env_config)

        # Log if we found API keys
        if "copilot" in env_config and "api_key" in env_config["copilot"]:
            logger.info("Found Copilot API key in environment")

        if "gemini" in env_config and "api_key" in env_config["gemini"]:
            logger.info("Found Gemini API key in environment")

    except Exception:


        pass
        logger.error(f"Error loading config from environment: {e}")

    # Create and validate the config model
    try:

        pass
        config = MCPConfig(**config_dict)
        logger.info("Configuration loaded and validated successfully")
        return config
    except Exception:

        pass
        logger.error(f"Error validating configuration: {e}")
        # Fall back to default config
        logger.warning("Using default configuration")
        return MCPConfig()
