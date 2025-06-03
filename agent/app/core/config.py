# TODO: Consider adding connection pooling configuration
"""
"""
API_PORT = int(os.getenv("API_PORT", "8000"))
API_URL = os.getenv("API_URL", "http://localhost:3000")
SERVER_HOST = os.getenv("SERVER_HOST", "45.32.69.157")
ENVIRONMENT = os.getenv("ENVIRONMENT", "unified")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://orchestra:your_secure_password@localhost:5432/orchestra")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "orchestrator")
POSTGRES_USER = os.getenv("POSTGRES_USER", "orchestrator")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "orch3str4_2024")

# Weaviate Configuration
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", "")

# Authentication
JWT_SECRET = os.getenv("JWT_SECRET", "your-jwt-secret-here-change-in-production")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")
API_KEY = os.getenv("API_KEY", "")

# Portkey Configuration (LLM Gateway)
PORTKEY_API_KEY = os.getenv("PORTKEY_API_KEY", "")
PORTKEY_BASE_URL = os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1")
PORTKEY_OPENAI_VIRTUAL_KEY = os.getenv("PORTKEY_OPENAI_VIRTUAL_KEY", "")
PORTKEY_ANTHROPIC_VIRTUAL_KEY = os.getenv("PORTKEY_ANTHROPIC_VIRTUAL_KEY", "")
PORTKEY_GEMINI_VIRTUAL_KEY = os.getenv("PORTKEY_GEMINI_VIRTUAL_KEY", "")
PORTKEY_PERPLEXITY_VIRTUAL_KEY = os.getenv("PORTKEY_PERPLEXITY_VIRTUAL_KEY", "")

# Direct API Keys (optional, if not using Portkey)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Feature Flags
ENABLE_IMAGE_GEN = os.getenv("ENABLE_IMAGE_GEN", "true").lower() == "true"
ENABLE_VIDEO_SYNTH = os.getenv("ENABLE_VIDEO_SYNTH", "true").lower() == "true"
ENABLE_ADVANCED_SEARCH = os.getenv("ENABLE_ADVANCED_SEARCH", "true").lower() == "true"
ENABLE_MULTIMODAL = os.getenv("ENABLE_MULTIMODAL", "true").lower() == "true"

# Media Services
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

# Monitoring
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
SENTRY_DSN = os.getenv("SENTRY_DSN", "")

# Cost Management
DAILY_COST_LIMIT_USD = float(os.getenv("DAILY_COST_LIMIT_USD", "100"))
COST_ALERT_THRESHOLD = float(os.getenv("COST_ALERT_THRESHOLD", "0.8"))
MAX_DALLE_REQUESTS_PER_DAY = int(os.getenv("MAX_DALLE_REQUESTS_PER_DAY", "1000"))
MAX_GPT4_TOKENS_PER_DAY = int(os.getenv("MAX_GPT4_TOKENS_PER_DAY", "1000000"))

# Caching (handled by PostgreSQL + Weaviate)
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

# Persona Schemas
POSTGRES_SCHEMA_CHERRY = os.getenv("POSTGRES_SCHEMA_CHERRY", "cherry")
POSTGRES_SCHEMA_SOPHIA = os.getenv("POSTGRES_SCHEMA_SOPHIA", "sophia")
POSTGRES_SCHEMA_KAREN = os.getenv("POSTGRES_SCHEMA_KAREN", "karen")

def get_database_url(schema: Optional[str] = None) -> str:
    """
    """
        return f"{DATABASE_URL}?options=-csearch_path%3D{schema}"
    return DATABASE_URL

def is_production() -> bool:
    """Check if running in production environment"""
    return ENVIRONMENT.lower() in ["production", "prod"]

def is_development() -> bool:
    """Check if running in development environment"""
    return ENVIRONMENT.lower() in ["development", "dev", "unified"]
