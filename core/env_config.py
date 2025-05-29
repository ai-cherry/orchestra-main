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
    """

    # Legacy GCP fields (deprecated, kept for compatibility)
    gcp_project_id: str = Field(default=None, env="GCP_PROJECT")
    gcp_service_account_key: str = Field(default=None, env="GOOGLE_APPLICATION_CREDENTIALS")

    # GitHub and CI/CD
    github_token: str = Field(default=None, env="GITHUB_TOKEN")
    codespaces: str = Field(default=None, env="CODESPACES")
    k_service: str = Field(default=None, env="K_SERVICE")
    cloud_workstations_agent: str = Field(default=None, env="CLOUD_WORKSTATIONS_AGENT")
    ci: str = Field(default=None, env="CI")
    github_actions: str = Field(default=None, env="GITHUB_ACTIONS")

    # Stack-native memory/vector DB endpoints and keys
    dragonfly_url: str = Field(default=None, env="DRAGONFLY_URL")
    weaviate_endpoint: str = Field(default=None, env="WEAVIATE_ENDPOINT")
    weaviate_api_key: str = Field(default=None, env="WEAVIATE_API_KEY")
    pinecone_api_key: str = Field(default=None, env="PINECONE_API_KEY")
    pinecone_environment: str = Field(default=None, env="PINECONE_ENVIRONMENT")
    mcp_api_key: str = Field(default=None, env="MCP_API_KEY")
    # Qdrant is deprecated; use Weaviate
    qdrant_url: str = Field(default=None, env="QDRANT_URL")

    # Recraft API Key for Recraft integrations (set via Pulumi Secret Manager)
    recraft_api_key: str = Field(default=None, env="RECRAFT_API_KEY")

    # Add all other environment variables used in the project here, with clear comments.

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton instance for use throughout the project
settings = OrchestraSettings()

# Usage example (in other modules):
# from core.env_config import settings
# project_id = settings.gcp_project_id
