"""
Application settings for the Admin API.
"""
import logging
from typing import Dict, List, Optional, Union
from functools import lru_cache

from pydantic import AnyHttpUrl, computed_field, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    # Project settings
    PROJECT_ID: str = Field(..., description="GCP Project ID")
    REGION: str = Field("us-central1", description="GCP Region")
    ENV: str = Field("dev", description="Environment (dev, staging, prod)")
    
    # API settings
    API_URL: str = Field("http://localhost:8080", description="API base URL")
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = Field(["*"], description="CORS origins")
    
    # Database settings (Cloud SQL PostgreSQL)
    DATABASE_URL: str = Field(
        "postgresql://user:password@localhost/dbname",
        description="PostgreSQL connection string"
    )
    
    # Firestore settings
    FIRESTORE_COLLECTION: str = Field("memory", description="Firestore collection name")
    FIRESTORE_POOL_SIZE: int = Field(10, description="Firestore connection pool size")
    
    # Redis settings for caching
    REDIS_URL: Optional[str] = Field(
        None,
        description="Redis connection URL for caching (optional)"
    )
    REDIS_TTL: int = Field(3600, description="Default Redis cache TTL in seconds")
    
    # Gemini settings
    GEMINI_MODEL_ID: str = Field(
        "gemini-2.5-pro-preview-05-06",
        description="Gemini model ID"
    )
    GEMINI_LOCATION: str = Field("us-central1", description="Gemini API location")
    GEMINI_CACHE_ENABLED: bool = Field(True, description="Enable Gemini response caching")
    
    # Logging
    LOG_LEVEL: str = Field("INFO", description="Logging level")
    
    # Cached properties to avoid recalculations
    _cors_origins: Optional[List[AnyHttpUrl]] = None
    _gemini_endpoint: Optional[str] = None
    
    @computed_field
    @property
    def CORS_ORIGINS(self) -> List[AnyHttpUrl]:
        """
        Parse BACKEND_CORS_ORIGINS into a list of URLs.
        Cached to improve performance.
        """
        if self._cors_origins is None:
            if isinstance(self.BACKEND_CORS_ORIGINS, str):
                self._cors_origins = [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]
            else:
                self._cors_origins = self.BACKEND_CORS_ORIGINS
        return self._cors_origins
    
    @computed_field
    @property
    def GEMINI_API_ENDPOINT(self) -> str:
        """
        Return the Gemini API endpoint URL.
        Cached to avoid string formatting on every access.
        """
        if self._gemini_endpoint is None:
            self._gemini_endpoint = (
                f"https://{self.GEMINI_LOCATION}-aiplatform.googleapis.com/v1/projects/"
                f"{self.PROJECT_ID}/locations/{self.GEMINI_LOCATION}/publishers/google/"
                f"models/{self.GEMINI_MODEL_ID}"
            )
        return self._gemini_endpoint
    
    @computed_field
    @property
    def DEBUG_MODE(self) -> bool:
        """Whether the application is running in debug mode."""
        return self.ENV.lower() == "dev"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True,
    )
    
    def log_config(self) -> None:
        """Log the configuration settings (excluding sensitive values)."""
        sensitive_keys = {"DATABASE_URL", "REDIS_URL"}
        config_dict = self.model_dump()
        safe_config = {
            k: "***REDACTED***" if k in sensitive_keys else v
            for k, v in config_dict.items()
        }
        logger.info(f"Application configuration loaded: {safe_config}")


# Create settings instance
settings = Settings()