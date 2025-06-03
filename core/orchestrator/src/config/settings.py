"""
"""
    """
    """
    APP_NAME: str = "AI Orchestration System"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Storage configuration
    REDIS_ENABLED: bool = True
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # Resource paths
    PERSONA_CONFIG_PATH: str = "core/orchestrator/src/config/personas"

    # Memory settings
    MEMORY_PROVIDER: str = "in_memory"  # For orchestrator's internal/simple memory needs
    CONVERSATION_HISTORY_LIMIT: int = 10
    MEMORY_CACHE_TTL: int = 3600  # 1 hour default
    REDIS_PASSWORD: Optional[str] = None

    # Enhanced memory settings
    USE_RESILIENT_ADAPTER: bool = True  # Whether to use circuit breaker pattern
    EMBEDDING_DIMENSION: int = 768  # Dimension of embedding vectors
    ENABLE_MEMORY_MONITORING: bool = True  # Whether to enable memory monitoring

    # Agent settings
    DEFAULT_AGENT_TYPE: str = "simple_text"
    PREFERRED_AGENTS_ENABLED: bool = True
    AGENT_TIMEOUT_SECONDS: int = 30

    # LLM settings
    OPENROUTER_API_KEY: Optional[SecretStr] = None
    DEFAULT_LLM_MODEL: str = "openai/gpt-3.5-turbo"

    # API settings
    CORS_ORIGINS: List[str] = ["*"]
    API_PREFIX: str = "/api"

    # Configure Pydantic to load from .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=True)

def load_all_persona_configs(settings_instance: Settings) -> Dict[str, PersonaConfig]:
    """
    """
        logger.warning(f"Persona config directory '{persona_dir}' not found")
        return personas

    # Scan the directory for YAML files
    for filename in os.listdir(persona_dir):
        if filename.endswith((".yaml", ".yml")):
            file_path = os.path.join(persona_dir, filename)
            try:

                pass
                with open(file_path, "r") as file:
                    # Load YAML content
                    yaml_data = yaml.safe_load(file)

                    # Create PersonaConfig from YAML data
                    persona_config = PersonaConfig(**yaml_data)

                    # Use lowercase filename (without extension) as the key
                    persona_name = os.path.splitext(filename)[0].lower()
                    personas[persona_name] = persona_config

                    logger.info(f"Loaded persona configuration for '{persona_name}'")
            except Exception:

                pass
                logger.error(f"Error loading persona config from {file_path}: {str(e)}")

    if not personas:
        logger.warning("No persona configurations found")

    return personas

# Global settings instance for singleton pattern
settings = Settings()

# Log that settings have been loaded
logger.info(f"Loaded configuration for {settings.APP_NAME} in {settings.ENVIRONMENT} environment")

def get_settings() -> Settings:
    """
    """
    """
    """