"""
Centralized environment configuration for Orchestra AI.
Uses Pydantic BaseSettings to provide a single source of truth for all environment variables.
Import this module wherever environment configuration is needed.
"""

from pydantic import BaseSettings, Field


class OrchestraSettings(BaseSettings):
    """
    Centralized environment variables for Orchestra AI.
    All secrets and endpoints should be managed via Pulumi/environment.

    Database Priority (Weaviate-first architecture):
    1. Weaviate - Primary vector/document store with ACORN hybrid search
    2. PostgreSQL - ACID operations, structured data, pgvector fallback
    3. Dragonfly - Optional micro-cache for high-throughput scenarios
    """

    # Legacy GCP fields (deprecated, kept for compatibility)
    gcp_project_id: str = Field(default=None, env="GCP_PROJECT")
    gcp_service_account_key: str = Field(default=None, env="GOOGLE_APPLICATION_CREDENTIALS")

    # GitHub and CI/CD
    github_token: str = Field(default=None, env="GITHUB_TOKEN")
    k_service: str = Field(default=None, env="K_SERVICE")
    cloud_workstations_agent: str = Field(default=None, env="CLOUD_WORKSTATIONS_AGENT")
    ci: str = Field(default=None, env="CI")
    github_actions: str = Field(default=None, env="GITHUB_ACTIONS")

    # Weaviate Configuration (Primary Vector Database)
    weaviate_endpoint: str = Field(default=None, env="WEAVIATE_ENDPOINT")
    weaviate_api_key: str = Field(default=None, env="WEAVIATE_API_KEY")
    weaviate_grpc_endpoint: str = Field(default=None, env="WEAVIATE_GRPC_ENDPOINT")
    weaviate_batch_size: int = Field(default=100, env="WEAVIATE_BATCH_SIZE")
    weaviate_enable_acorn: bool = Field(default=True, env="WEAVIATE_ENABLE_ACORN")
    weaviate_enable_agents: bool = Field(default=True, env="WEAVIATE_ENABLE_AGENTS")

    # PostgreSQL Configuration (ACID Operations)
    postgres_dsn: str = Field(default=None, env="POSTGRES_DSN")
    postgres_host: str = Field(default=None, env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_user: str = Field(default=None, env="POSTGRES_USER")
    postgres_password: str = Field(default=None, env="POSTGRES_PASSWORD")
    postgres_db: str = Field(default=None, env="POSTGRES_DB")

    # Dragonfly Configuration (Optional Micro-Cache)
    dragonfly_url: str = Field(default=None, env="DRAGONFLY_URL")
    dragonfly_uri: str = Field(default=None, env="DRAGONFLY_URI")  # Redis-compatible URI
    enable_micro_cache: bool = Field(default=False, env="ENABLE_MICRO_CACHE")
    use_redis: bool = Field(default=False, env="USE_REDIS")

    # Legacy Vector DB endpoints (deprecated, use Weaviate instead)
    pinecone_api_key: str = Field(default=None, env="PINECONE_API_KEY")
    pinecone_environment: str = Field(default=None, env="PINECONE_ENVIRONMENT")
    qdrant_url: str = Field(default=None, env="QDRANT_URL")

    # MCP Configuration
    mcp_api_key: str = Field(default=None, env="MCP_API_KEY")
    mcp_server_endpoint: str = Field(default=None, env="MCP_SERVER_ENDPOINT")

    # Monitoring and Observability
    langfuse_host: str = Field(default=None, env="LANGFUSE_HOST")
    langfuse_public_key: str = Field(default=None, env="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field(default=None, env="LANGFUSE_SECRET_KEY")
    enable_performance_monitoring: bool = Field(default=True, env="ENABLE_PERFORMANCE_MONITORING")

    # Domain Configuration
    default_domain: str = Field(default="Personal", env="DEFAULT_DOMAIN")
    available_domains: str = Field(default="Personal,PayReady,ParagonRX", env="AVAILABLE_DOMAINS")

    # Recraft API Key for Recraft integrations (set via Pulumi Secret Manager)
    recraft_api_key: str = Field(default=None, env="RECRAFT_API_KEY")

    # Deployment Environment
    environment: str = Field(default="dev", env="ENVIRONMENT")
    paperspace_env: str = Field(default=None, env="PAPERSPACE_ENV")

    # Add all other environment variables used in the project here, with clear comments.

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton instance for use throughout the project
settings = OrchestraSettings()

# Usage example (in other modules):
# from core.env_config import settings
# weaviate_endpoint = settings.weaviate_endpoint
