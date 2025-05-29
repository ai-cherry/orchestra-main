"""
Centralized environment configuration for Orchestra AI.
Uses Pydantic BaseSettings to provide a single source of truth for all environment variables.
Import this module wherever environment configuration is needed.

Environment variables are sourced from:
1. GitHub organization secrets (preferred for production/CI)
2. Pulumi-managed secrets (for infrastructure resources)
3. Local .env files (for development only)
"""

import warnings
from typing import Optional
from pydantic import BaseSettings, Field, validator


class OrchestraSettings(BaseSettings):
    """
    Centralized environment variables for Orchestra AI.
    
    All secrets should be managed via:
    - GitHub organization secrets (for CI/CD pipelines)
    - Pulumi config/secrets (for infrastructure)
    - DigitalOcean App Platform environment variables (for runtime)
    
    DO NOT hardcode secrets or use service-specific environment files.
    """

    # ======================================================================
    # DEPRECATED: Legacy GCP fields - scheduled for removal in v2.0
    # These are maintained only for backward compatibility
    # ======================================================================
    gcp_project_id: Optional[str] = Field(
        default=None, 
        env="GCP_PROJECT", 
        deprecated=True,
        description="DEPRECATED: Use DigitalOcean resources instead of GCP"
    )
    gcp_service_account_key: Optional[str] = Field(
        default=None, 
        env="GOOGLE_APPLICATION_CREDENTIALS",
        deprecated=True,
        description="DEPRECATED: Use DigitalOcean resources instead of GCP"
    )

    @validator("gcp_project_id", "gcp_service_account_key")
    def warn_deprecated_gcp(cls, v, values, **kwargs):
        if v is not None:
            warnings.warn(
                f"GCP credentials are deprecated and scheduled for removal in v2.0. "
                f"Orchestra now uses DigitalOcean for all infrastructure.",
                DeprecationWarning, 
                stacklevel=2
            )
        return v

    # ======================================================================
    # CI/CD Environment Detection
    # ======================================================================
    github_token: Optional[str] = Field(
        default=None, 
        env="GITHUB_TOKEN",
        description="GitHub token for API access during CI/CD"
    )
    ci: Optional[str] = Field(
        default=None, 
        env="CI",
        description="Set by CI systems to indicate running in CI environment"
    )
    github_actions: Optional[str] = Field(
        default=None, 
        env="GITHUB_ACTIONS",
        description="Set by GitHub Actions to indicate running in GitHub Actions"
    )

    # ======================================================================
    # Database & Memory Storage Endpoints
    # ======================================================================
    # Primary vector/memory storage
    weaviate_endpoint: Optional[str] = Field(
        default=None, 
        env="WEAVIATE_ENDPOINT",
        description="Weaviate vector database endpoint URL"
    )
    weaviate_api_key: Optional[str] = Field(
        default=None, 
        env="WEAVIATE_API_KEY",
        description="Weaviate authentication API key"
    )
    
    # Caching layer
    dragonfly_url: Optional[str] = Field(
        default=None, 
        env="DRAGONFLY_URL",
        description="Dragonfly Redis-compatible caching endpoint"
    )
    
    # Alternative vector stores (used by specific components)
    pinecone_api_key: Optional[str] = Field(
        default=None, 
        env="PINECONE_API_KEY",
        description="Pinecone vector DB API key (if used)"
    )
    pinecone_environment: Optional[str] = Field(
        default=None, 
        env="PINECONE_ENVIRONMENT",
        description="Pinecone environment name (if used)"
    )
    
    # Deprecated vector store - use Weaviate instead
    qdrant_url: Optional[str] = Field(
        default=None, 
        env="QDRANT_URL", 
        deprecated=True,
        description="DEPRECATED: Use Weaviate instead of Qdrant"
    )

    # ======================================================================
    # API Keys & Integration Secrets
    # ======================================================================
    # MCP API key for internal services
    mcp_api_key: Optional[str] = Field(
        default=None, 
        env="MCP_API_KEY",
        description="API key for MCP server authentication"
    )
    
    # Recraft API for programmatic asset generation
    recraft_api_key: Optional[str] = Field(
        default=None, 
        env="RECRAFT_API_KEY",
        description="Recraft.ai API key for image generation"
    )

    # ======================================================================
    # Configuration Options
    # ======================================================================
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Enable case-insensitive environment variables
        case_sensitive = False
        # Enable validation of field values
        validate_assignment = True


# Singleton instance for use throughout the project
settings = OrchestraSettings()

# Usage examples:
# from core.env_config import settings
# 
# # Access settings
# weaviate_url = settings.weaviate_endpoint
# 
# # Check if running in CI
# is_ci = settings.ci is not None
