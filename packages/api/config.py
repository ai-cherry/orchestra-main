"""
Configuration settings for the AI Orchestra API.

This module defines the application settings using Pydantic's BaseSettings.
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """
    Application settings using Pydantic's BaseSettings for environment variable loading.
    """

    # Basic settings
    environment: str = Field(default="dev", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")

    # GCP settings
    project_id: str = Field(default="cherry-ai-project", env="PROJECT_ID")
    region: str = Field(default="us-central1", env="REGION")

    # Vertex AI settings
    vertex_endpoint: Optional[str] = Field(default=None, env="VERTEX_ENDPOINT")
    vertex_location: str = Field(default="us-central1", env="VERTEX_LOCATION")

    # API settings
    api_prefix: str = Field(default="/api", env="API_PREFIX")

    # Security settings
    cors_origins: list[str] = Field(default=["*"], env="CORS_ORIGINS")

    class Config:
        """Pydantic config"""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings with caching for performance.

    Returns:
        Settings: Application settings
    """
    return Settings()
