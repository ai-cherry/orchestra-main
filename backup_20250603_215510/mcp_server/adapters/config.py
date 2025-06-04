"""
"""
    """Configuration for circuit breaker functionality."""
    """Base configuration for Factory AI droids."""
    api_key: str = field(default_factory=lambda: os.getenv("FACTORY_AI_API_KEY", ""))
    base_url: str = "https://api.factory.ai"
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    timeout: int = 30
    max_retries: int = 3

@dataclass
class ArchitectConfig(DroidConfig):
    """Configuration for Architect droid adapter."""
    default_cloud_provider: str = "vultr"
    output_format: str = "pulumi"

@dataclass
class CodeConfig(DroidConfig):
    """Configuration for Code droid adapter."""
    default_language: str = "python"
    optimization_level: str = "balanced"
    include_tests: bool = True
    include_docs: bool = True
    max_tokens: int = 4096

@dataclass
class DebugConfig(DroidConfig):
    """Configuration for Debug droid adapter."""
    profile_depth: str = "detailed"
    max_solutions: int = 5

@dataclass
class ReliabilityConfig(DroidConfig):
    """Configuration for Reliability droid adapter."""
    runbook_format: str = "markdown"
    severity_threshold: str = "medium"

@dataclass
class KnowledgeConfig(DroidConfig):
    """Configuration for Knowledge droid adapter."""
    embedding_model: str = "text-embedding-ada-002"
    cache_embeddings: bool = True
    similarity_threshold: float = 0.7
    max_results: int = 10
    auto_chunk: bool = True
    chunk_size: int = 512
    weaviate: Dict[str, Any] = field(
        default_factory=lambda: {
            "url": os.getenv("WEAVIATE_URL", "http://localhost:8080"),
            "api_key": os.getenv("WEAVIATE_API_KEY", ""),
        }
    )

@dataclass
class AdapterSystemConfig:
    """Complete configuration for the adapter system."""
    log_level: str = "INFO"
    health_check_interval: int = 60

def load_config_from_env() -> AdapterSystemConfig:
    """
    """
    api_key = os.getenv("FACTORY_AI_API_KEY", "")
    if api_key:
        for droid_config in [
            config.architect,
            config.code,
            config.debug,
            config.reliability,
            config.knowledge,
        ]:
            droid_config.api_key = api_key

    # Load specific overrides
    if base_url := os.getenv("FACTORY_AI_BASE_URL"):
        for droid_config in [
            config.architect,
            config.code,
            config.debug,
            config.reliability,
            config.knowledge,
        ]:
            droid_config.base_url = base_url

    # Circuit breaker settings
    if failure_threshold := os.getenv("CIRCUIT_BREAKER_THRESHOLD"):
        threshold = int(failure_threshold)
        for droid_config in [
            config.architect,
            config.code,
            config.debug,
            config.reliability,
            config.knowledge,
        ]:
            droid_config.circuit_breaker.failure_threshold = threshold

    # Adapter-specific settings
    if streaming := os.getenv("CODE_ADAPTER_STREAMING"):
        config.code.streaming = streaming.lower() == "true"

    if auto_remediation := os.getenv("RELIABILITY_AUTO_REMEDIATION"):
        config.reliability.auto_remediation = auto_remediation.lower() == "true"

    if embedding_model := os.getenv("KNOWLEDGE_EMBEDDING_MODEL"):
        config.knowledge.embedding_model = embedding_model

    # Global settings
    if metrics_enabled := os.getenv("ADAPTER_METRICS_ENABLED"):
        config.enable_metrics = metrics_enabled.lower() == "true"

    if log_level := os.getenv("ADAPTER_LOG_LEVEL"):
        config.log_level = log_level.upper()

    return config

def validate_config(config: AdapterSystemConfig) -> None:
    """
    """
        ("architect", config.architect),
        ("code", config.code),
        ("debug", config.debug),
        ("reliability", config.reliability),
        ("knowledge", config.knowledge),
    ]:
        if not droid_config.api_key:
            raise ValueError(f"API key required for {name} adapter")

    # Validate circuit breaker settings
    for name, droid_config in [
        ("architect", config.architect),
        ("code", config.code),
        ("debug", config.debug),
        ("reliability", config.reliability),
        ("knowledge", config.knowledge),
    ]:
        if droid_config.circuit_breaker.failure_threshold < 1:
            raise ValueError(f"Invalid failure threshold for {name} adapter")
        if droid_config.circuit_breaker.recovery_timeout < 1:
            raise ValueError(f"Invalid recovery timeout for {name} adapter")

    # Validate adapter-specific settings
    if config.code.chunk_size < 1:
        raise ValueError("Code adapter chunk size must be positive")

    if config.knowledge.vector_dimension < 1:
        raise ValueError("Knowledge adapter vector dimension must be positive")

    if not 0 <= config.knowledge.similarity_threshold <= 1:
        raise ValueError("Knowledge adapter similarity threshold must be between 0 and 1")

# Default configuration instance
DEFAULT_CONFIG = AdapterSystemConfig()

# Example configuration for different environments
DEVELOPMENT_CONFIG = AdapterSystemConfig(
    architect=ArchitectConfig(
        api_key="dev-key",
        circuit_breaker=CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=30,
        ),
    ),
    code=CodeConfig(
        api_key="dev-key",
        streaming=True,
        optimization_level="fast",
    ),
    debug=DebugConfig(
        api_key="dev-key",
        profiling_enabled=True,
        deep_analysis=True,
    ),
    reliability=ReliabilityConfig(
        api_key="dev-key",
        auto_remediation=False,  # Disable in dev
        alert_threshold=3,
    ),
    knowledge=KnowledgeConfig(
        api_key="dev-key",
        cache_embeddings=True,
        max_results=5,
    ),
    enable_metrics=True,
    log_level="INFO",
)

PRODUCTION_CONFIG = AdapterSystemConfig(
    architect=ArchitectConfig(
        circuit_breaker=CircuitBreakerConfig(
            failure_threshold=10,
            recovery_timeout=120,
        ),
    ),
    code=CodeConfig(
        streaming=True,
        optimization_level="balanced",
        max_tokens=8192,
    ),
    debug=DebugConfig(
        profiling_enabled=True,
        max_stack_depth=100,
    ),
    reliability=ReliabilityConfig(
        auto_remediation=True,
        alert_threshold=10,
        correlation_window=600,
    ),
    knowledge=KnowledgeConfig(
        cache_embeddings=True,
        similarity_threshold=0.8,
        max_results=20,
    ),
    enable_metrics=True,
    log_level="WARNING",
    health_check_interval=30,
)
