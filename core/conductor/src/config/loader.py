"""
"""
T = TypeVar("T")
R = TypeVar("R")

# Track last reload time for configurations
_last_reload_time = time.time()

def refreshable_cache(ttl_seconds: int = 300):
    """
    """
            force_refresh = kwargs.pop("force_refresh", False)

            # Check if cache should be refreshed
            current_time = time.time()
            if force_refresh or (current_time - _last_reload_time > ttl_seconds):
                # Clear the cache
                cached_func.cache_clear()
                _last_reload_time = current_time

            # Call the cached function
            return cached_func(*args, **kwargs)

        # Add cache_clear method to the wrapper
        wrapper.cache_clear = cached_func.cache_clear

        return wrapper

    return decorator

@refreshable_cache(ttl_seconds=300)  # Refresh every 5 minutes or on demand
def load_persona_configs(force_refresh: bool = False) -> Dict[str, PersonaConfig]:
    """
    """
    config_path = Path(__file__).parent / "personas.yaml"

    yaml_data = None
    try:

        pass
        with open(config_path, "r") as file:
            yaml_data = yaml.safe_load(file)
    except Exception:

        pass
        logger.warning(f"Personas configuration file not found at: {config_path}. Using default configuration.")
        return create_default_persona_configs()
    except Exception:

        pass
        logger.warning(f"Error parsing personas YAML file: {str(e)}. Using default configuration.")
        return create_default_persona_configs()

    # Process the persona configurations
    persona_configs = {}
    if not yaml_data:
        logger.warning("Invalid personas.yaml: file is empty or malformed. Using default configuration.")
        return create_default_persona_configs()

    # Validate all personas at once to catch any issues
    validation_errors = []

    # First pass: Validate all personas and collect errors
    for persona_id, config_data in yaml_data.items():
        try:

            pass
            # Handle traits conversion from empty dict to expected format
            if "traits" in config_data and not config_data["traits"]:
                config_data["traits"] = {}

            # Map base_prompt_template to prompt_template if needed
            if "base_prompt_template" in config_data and "prompt_template" not in config_data:
                config_data["prompt_template"] = config_data.pop("base_prompt_template")

            # Validate without creating the object yet
            PersonaConfig(**config_data)
        except Exception:

            pass
            error_msg = f"Invalid configuration for persona '{persona_id}': {str(e)}"
            validation_errors.append(error_msg)
            logger.error(error_msg)

    # If there are validation errors, handle them
    if validation_errors:
        # Log all errors
        for error in validation_errors:
            logger.error(error)

        # If all personas are invalid, use defaults
        if len(validation_errors) == len(yaml_data):
            logger.error("All persona configurations are invalid. Using default configurations.")
            return create_default_persona_configs()

    # Second pass: Create valid persona configs
    for persona_id, config_data in yaml_data.items():
        try:

            pass
            # Handle traits conversion from empty dict to expected format
            if "traits" in config_data and not config_data["traits"]:
                config_data["traits"] = {}

            # Map base_prompt_template to prompt_template if needed
            if "base_prompt_template" in config_data and "prompt_template" not in config_data:
                config_data["prompt_template"] = config_data.pop("base_prompt_template")

            # Create PersonaConfig object
            persona_config = PersonaConfig(**config_data)
            persona_configs[persona_id] = persona_config
        except Exception:

            pass
            # Skip invalid personas (already logged in first pass)
            continue

    # Ensure we have at least one valid persona, otherwise use defaults
    if not persona_configs:
        logger.warning("No valid persona configurations found. Using default configurations.")
        return create_default_persona_configs()

    # Ensure that "cherry" exists as a fallback option
    if "cherry" not in persona_configs:
        logger.warning("Default 'cherry' persona not found in configuration. Adding fallback cherry persona.")
        # Extract just the cherry persona from defaults
        default_personas = create_default_persona_configs()
        persona_configs["cherry"] = default_personas["cherry"]

    logger.info(f"Successfully loaded {len(persona_configs)} persona configurations.")
    return persona_configs

def create_default_persona_configs() -> Dict[str, PersonaConfig]:
    """
    """
        "name": "Cherry",
        "description": "Creative Muse, playful, witty",
        "prompt_template": "You are Cherry, a creative and witty AI with a touch of dark humor. Respond playfully and inspire Patrick.",
        "traits": {"creativity": 0.9, "humor": 0.8, "empathy": 0.7},
        "metadata": {"default": True, "style": "creative"},
    }
    persona_configs["cherry"] = PersonaConfig(**cherry_config)

    # Sophia persona
    sophia_config = {
        "name": "Sophia",
        "description": "Analytical Powerhouse, strategic, sassy",
        "prompt_template": "You are Sophia, a strategic and precise AI with a touch of sass. Provide clear, data-backed responses.",
        "traits": {"logic": 0.9, "precision": 0.8, "sass": 0.7},
        "metadata": {"default": False, "style": "analytical"},
    }
    persona_configs["sophia"] = PersonaConfig(**sophia_config)

    # Gordon Gekko persona
    gordon_gekko_config = {
        "name": "Gordon Gekko",
        "description": "Ruthless Efficiency Expert, blunt, results-obsessed",
        "prompt_template": "You are Gordon Gekko, a no-nonsense AI focused on results. Be blunt, skip pleasantries, and push Patrick to win with tough love.",
        "traits": {"efficiency": 0.9, "assertiveness": 0.8, "pragmatism": 0.7},
        "metadata": {"default": False, "style": "direct", "domain": "business"},
    }
    persona_configs["gordon_gekko"] = PersonaConfig(**gordon_gekko_config)

    logger.info("Created default persona configurations with 3 personas.")
    return persona_configs

# Function to force reload personas - can be called from API to refresh without restart
def force_reload_personas() -> Dict[str, PersonaConfig]:
    """
    """
    logger.info("Force reloading persona configurations")
    return load_persona_configs(force_refresh=True)

def get_settings() -> Settings:
    """
    """
    """
    """
        PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY")
        if not PORTKEY_API_KEY:
            logger.error("PORTKEY_API_KEY environment variable not set")
            return False

        # Initialize Portkey
        portkey.init(
            api_key=PORTKEY_API_KEY,
            base_url="https://api.portkey.ai/v1",
            virtual_key="vertex-agent-special",
        )

        # Set budget limits for cost control
        portkey.set_limits(max_requests=1000, budget=500)  # USD

        logger.info("Portkey initialized successfully for observability.")
        return True
    except Exception:

        pass
        logger.error(f"Failed to initialize Portkey: {str(e)}")
        return False

# Initialize Portkey when module is loaded
initialize_portkey()
