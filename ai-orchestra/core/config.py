"""
Configuration management for AI Orchestra.

This module provides configuration management using Pydantic models.
It includes comprehensive validation and caching for optimal performance.
"""

import os
import re
from functools import lru_cache
from typing import Dict, List, Optional, Set, Union, Any

from pydantic import BaseSettings, Field, validator, root_validator


class GCPSettings(BaseSettings):
    """GCP configuration settings."""

    project_id: str = Field(..., description="GCP project ID")
    region: str = Field("us-west4", description="GCP region")
    use_workload_identity: bool = Field(True, description="Use Workload Identity Federation")
    service_account_email: Optional[str] = Field(None, description="Service account email")

    @validator("project_id")
    def validate_project_id(cls, v: str) -> str:
        """Validate project ID format."""
        if not v.startswith("cherry-"):
            raise ValueError("Project ID must start with 'cherry-'")
        if not re.match(r"^[a-z][-a-z0-9]{4,28}[a-z0-9]$", v):
            raise ValueError("Project ID must match GCP naming requirements")
        return v

    @validator("region")
    def validate_region(cls, v: str) -> str:
        """Validate GCP region."""
        valid_regions = {"us-west1", "us-west2", "us-west3", "us-west4", "us-central1"}
        if v not in valid_regions:
            raise ValueError(f"Region must be one of: {', '.join(valid_regions)}")
        return v

    @validator("service_account_email")
    def validate_service_account_email(cls, v: Optional[str]) -> Optional[str]:
        """Validate service account email format."""
        if v is None:
            return v
        if not re.match(r"^[a-zA-Z0-9-]+@[a-zA-Z0-9-]+\.iam\.gserviceaccount\.com$", v):
            raise ValueError("Invalid service account email format")
        return v

    class Config:
        env_prefix = "GCP_"
        env_file = ".env"
        case_sensitive = False


class AISettings(BaseSettings):
    """AI service configuration settings."""

    default_model: str = Field("gemini-pro", description="Default AI model")
    api_key: Optional[str] = Field(None, description="API key for AI service")
    use_vertex_ai: bool = Field(True, description="Use Vertex AI for model serving")
    max_tokens: int = Field(1024, description="Default maximum tokens for generation")
    temperature: float = Field(0.7, description="Default temperature for generation")

    @validator("temperature")
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Temperature must be between 0.0 and 1.0")
        return v

    @validator("max_tokens")
    def validate_max_tokens(cls, v: int) -> int:
        """Validate max tokens range."""
        if v <= 0:
            raise ValueError("Max tokens must be greater than 0")
        return v

    @validator("default_model")
    def validate_default_model(cls, v: str) -> str:
        """Validate default model."""
        valid_models = {"gemini-pro", "gemini-pro-vision", "text-bison", "chat-bison"}
        if v not in valid_models:
            raise ValueError(f"Default model must be one of: {', '.join(valid_models)}")
        return v

    class Config:
        env_prefix = "AI_"
        env_file = ".env"
        case_sensitive = False


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    firestore_database: str = Field("firestore", description="Firestore database name")
    use_firestore_emulator: bool = Field(False, description="Use Firestore emulator")
    firestore_emulator_host: Optional[str] = Field(None, description="Firestore emulator host")

    @validator("firestore_emulator_host")
    def validate_firestore_emulator_host(cls, v: Optional[str], values: Dict[str, Any]) -> Optional[str]:
        """Validate Firestore emulator host."""
        if values.get("use_firestore_emulator", False) and not v:
            raise ValueError("Firestore emulator host must be provided when use_firestore_emulator is True")
        return v

    class Config:
        env_prefix = "DB_"
        env_file = ".env"
        case_sensitive = False


class RedisSettings(BaseSettings):
    """Redis configuration settings."""

    host: str = Field("localhost", description="Redis host")
    port: int = Field(6379, description="Redis port")
    password: Optional[str] = Field(None, description="Redis password")
    db: int = Field(0, description="Redis database")
    use_connection_pool: bool = Field(True, description="Use Redis connection pool")
    max_connections: int = Field(50, description="Maximum connections in the pool")

    @validator("port")
    def validate_port(cls, v: int) -> int:
        """Validate port range."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @validator("db")
    def validate_db(cls, v: int) -> int:
        """Validate database index."""
        if v < 0:
            raise ValueError("Database index must be non-negative")
        return v

    @validator("max_connections")
    def validate_max_connections(cls, v: int) -> int:
        """Validate max connections."""
        if v <= 0:
            raise ValueError("Max connections must be greater than 0")
        return v

    class Config:
        env_prefix = "REDIS_"
        env_file = ".env"
        case_sensitive = False


class APISettings(BaseSettings):
    """API configuration settings."""

    host: str = Field("0.0.0.0", description="API host")
    port: int = Field(8000, description="API port")
    debug: bool = Field(False, description="Enable debug mode")
    cors_origins: List[str] = Field(["*"], description="CORS allowed origins")

    @validator("port")
    def validate_port(cls, v: int) -> int:
        """Validate port range."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    class Config:
        env_prefix = "API_"
        env_file = ".env"
        case_sensitive = False


class Settings(BaseSettings):
    """Main application settings."""

    app_name: str = Field("AI Orchestra", description="Application name")
    environment: str = Field("development", description="Environment (development, staging, production)")
    log_level: str = Field("INFO", description="Logging level")

    gcp: GCPSettings = Field(default_factory=GCPSettings)
    ai: AISettings = Field(default_factory=AISettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    api: APISettings = Field(default_factory=APISettings)

    @validator("environment")
    def validate_environment(cls, v: str) -> str:
        """Validate environment."""
        valid_environments = {"development", "staging", "production"}
        if v not in valid_environments:
            raise ValueError(f"Environment must be one of: {', '.join(valid_environments)}")
        return v

    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v = v.upper()
        if v not in valid_log_levels:
            raise ValueError(f"Log level must be one of: {', '.join(valid_log_levels)}")
        return v

    @root_validator
    def validate_settings(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate settings consistency."""
        # In production, debug should be False
        if values.get("environment") == "production" and values.get("api").debug:
            values["api"].debug = False

        # In production, use_firestore_emulator should be False
        if values.get("environment") == "production" and values.get("database").use_firestore_emulator:
            values["database"].use_firestore_emulator = False

        return values

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get the application settings.

    This function is used for dependency injection in FastAPI.
    The result is cached to avoid reloading environment variables
    on each request.

    Returns:
        The application settings
    """
    return Settings()
