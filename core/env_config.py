"""
Centralized environment configuration for Orchestra AI.
Uses Pydantic BaseSettings to provide a single source of truth for all environment variables.
Import this module wherever environment configuration is needed.
"""

from pydantic import BaseSettings, Field


class OrchestraSettings(BaseSettings):
    # Example environment variables
    gcp_project_id: str = Field(default=None, env="GCP_PROJECT")
    gcp_service_account_key: str = Field(
        default=None, env="GOOGLE_APPLICATION_CREDENTIALS"
    )
    github_token: str = Field(default=None, env="GITHUB_TOKEN")
    dragonfly_url: str = Field(default=None, env="DRAGONFLY_URL")
    qdrant_url: str = Field(default=None, env="QDRANT_URL")
    # Recraft API Key for Recraft integrations (set via Pulumi Secret Manager)
    recraft_api_key: str = Field(default=None, env="RECRAFT_API_KEY")

    # Codespaces and CI/CD environment flags
    codespaces: str = Field(default=None, env="CODESPACES")
    k_service: str = Field(default=None, env="K_SERVICE")
    cloud_workstations_agent: str = Field(default=None, env="CLOUD_WORKSTATIONS_AGENT")
    ci: str = Field(default=None, env="CI")
    github_actions: str = Field(default=None, env="GITHUB_ACTIONS")
    # Add all other environment variables used in the project here, with clear comments.

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton instance for use throughout the project
settings = OrchestraSettings()

# Usage example (in other modules):
# from core.env_config import settings
# project_id = settings.gcp_project_id
