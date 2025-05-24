"""
Settings configuration for the AI Orchestration System.

This module defines the application settings using Pydantic's BaseSettings,
which automatically loads values from environment variables.

# AI-CONTEXT: This file manages the central configuration for the entire orchestra system.
# AI-CONTEXT: See CONFIG_CONTEXT.md in this directory for architectural details.
# AI-CONTEXT: Settings are accessed via dependency injection using get_settings()
# AI-CONTEXT: All settings come from environment variables or .env files

Best Practices:
- Use clear and descriptive names for all settings.
- Document expected value types and default values.
- Maintain consistency with environment variable names.

Lifecycle and Dependency Injection:
- Configuration settings should support both synchronous and asynchronous lifecycle management.
- Use dependency injection patterns consistently to allow easy testing and extension.

Error Handling:
- Document expected error conditions for each setting where applicable.
- Provide guidance on fallback or default behaviors.

Example:
  DEFAULT_AGENT_TYPE: str = "simple_text"  # Default agent type used if none specified

Please maintain this documentation as the configuration evolves.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Automatically reads from .env file when present.
    """

    # General settings
    ENVIRONMENT: str = "development"
    DEFAULT_LLM_MODEL: str = "gpt-4"  # Default model to use for LLM interactions
    DEFAULT_LLM_MODEL_PRIMARY: str = "openai/gpt-4o"  # Default model for OpenRouter (primary route)
    DEFAULT_LLM_MODEL_FALLBACK_OPENAI: Optional[str] = "gpt-4o"  # Fallback model for OpenAI
    DEFAULT_LLM_MODEL_FALLBACK_ANTHROPIC: Optional[str] = "claude-3-5-sonnet-20240620"  # Fallback model for Anthropic

    # API keys
    OPENROUTER_API_KEY: Optional[str] = None
    PORTKEY_API_KEY: Optional[str] = None

    # GCP Settings
    GCP_PROJECT_ID: Optional[str] = None
    GCP_SA_KEY_JSON: Optional[str] = None  # Service account key JSON content
    GCP_LOCATION: str = "us-central1"  # Default GCP region (changed to match deployment)
    GOOGLE_CLOUD_PROJECT: Optional[str] = None  # Alias for GCP_PROJECT_ID (for compatibility)
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None  # Path to credentials file (for compatibility)

    # Cloud Infrastructure Settings
    FIRESTORE_NAMESPACE: str = "orchestra-local"  # Namespace for Firestore collections
    FIRESTORE_TTL_DAYS: int = 30  # TTL for Firestore documents (in days)

    # Redis Cache Settings
    REDIS_HOST: Optional[str] = None  # Redis host address
    REDIS_PORT: int = 6379  # Redis port
    REDIS_AUTH_SECRET: Optional[str] = None  # Secret name containing Redis auth password
    REDIS_CACHE_TTL: int = 3600  # Default TTL for Redis cache (in seconds)
    REDIS_CACHE_ENABLED: bool = False  # Whether Redis caching is enabled

    # Vertex AI Vector Search Settings
    VECTOR_INDEX_NAME: Optional[str] = None  # Name of the Vertex AI Vector Search index
    VECTOR_DIMENSION: int = 1536  # Dimension of embeddings
    VECTOR_DISTANCE_TYPE: str = "COSINE"  # Distance measure type for vector search

    # VPC and Networking
    VPC_CONNECTOR: Optional[str] = None  # VPC connector for Cloud Run
    VPC_EGRESS: str = "private-ranges-only"  # VPC egress setting

    # OpenRouter Pro Configuration
    OPENROUTER_HEADERS: Optional[str] = None  # JSON string of custom headers
    OPENROUTER_DEFAULT_MODEL: str = "openai/gpt-3.5-turbo"
    OPENROUTER_FREE_FALLBACKS: Optional[str] = None  # Comma-separated list of free models to use as fallbacks
    PREFERRED_LLM_PROVIDER: str = "openrouter"  # Default provider to use

    # Mode-specific model mapping
    MODE_MODEL_MAP: Optional[str] = None  # JSON string mapping Roo modes to models and providers
    MODE_MODEL_MAP_DEFAULT: Dict[str, Dict[str, str]] = {
        "orchestrator": {
            "model": "google/gemini-pro-2.5-preview",
            "provider": "vertex",
        },
        "reviewer": {"model": "google/gemini-pro-2.5-preview", "provider": "vertex"},
        "strategy": {"model": "google/gemini-pro-2.5-preview", "provider": "vertex"},
        "code": {"model": "openai/gpt-4-1106-preview", "provider": "openai"},
        "debug": {"model": "openai/gpt-4-1106-preview", "provider": "openai"},
    }

    # Agent-specific model mapping
    AGENT_MODEL_MAP: Optional[str] = None  # JSON string mapping agent roles to models

    # LLM request parameters
    LLM_REQUEST_TIMEOUT: int = 30  # Default timeout in seconds
    LLM_MAX_RETRIES: int = 3
    LLM_RETRY_DELAY: float = 1.0
    LLM_RETRY_MAX_DELAY: float = 60.0  # Increased for Pro Tier
    LLM_RETRYABLE_ERRORS: str = "connection_error,timeout_error,rate_limit_error,service_error"

    # Enable semantic caching to reduce API calls and avoid rate limits
    LLM_SEMANTIC_CACHE_ENABLED: bool = False
    LLM_SEMANTIC_CACHE_THRESHOLD: float = 0.85  # Similarity threshold for cache hits
    LLM_SEMANTIC_CACHE_TTL: int = 3600  # Cache TTL in seconds

    # Portkey configuration
    TRACE_ID: Optional[str] = None

    # Main Portkey configuration
    MASTER_PORTKEY_ADMIN_KEY: Optional[str] = None  # Admin API key for managing virtual keys
    PORTKEY_CONFIG_ID: Optional[str] = None  # Gateway Config ID for retries/fallbacks
    PORTKEY_STRATEGY: str = "fallback"  # Strategy for Portkey: fallback, loadbalance, or cost_aware
    PORTKEY_CACHE_ENABLED: bool = False  # Enable Portkey's built-in caching

    # Virtual Keys for different providers
    PORTKEY_VIRTUAL_KEY_OPENAI: Optional[str] = None  # Virtual Key ID for OpenAI
    PORTKEY_VIRTUAL_KEY_ANTHROPIC: Optional[str] = None  # Virtual Key ID for Anthropic
    PORTKEY_VIRTUAL_KEY_MISTRAL: Optional[str] = None  # Virtual Key ID for Mistral
    PORTKEY_VIRTUAL_KEY_HUGGINGFACE: Optional[str] = None  # Virtual Key ID for HuggingFace
    PORTKEY_VIRTUAL_KEY_COHERE: Optional[str] = None  # Virtual Key ID for Cohere
    PORTKEY_VIRTUAL_KEY_OPENROUTER: Optional[str] = None  # Virtual Key ID for OpenRouter
    PORTKEY_VIRTUAL_KEY_PERPLEXITY: Optional[str] = None  # Virtual Key ID for Perplexity
    PORTKEY_VIRTUAL_KEY_DEEPSEEK: Optional[str] = None  # Virtual Key ID for DeepSeek
    PORTKEY_VIRTUAL_KEY_CODESTRAL: Optional[str] = None  # Virtual Key ID for Codestral
    PORTKEY_VIRTUAL_KEY_CODY: Optional[str] = None  # Virtual Key ID for Cody
    PORTKEY_VIRTUAL_KEY_CONTINUE: Optional[str] = None  # Virtual Key ID for Continue
    PORTKEY_VIRTUAL_KEY_GROK: Optional[str] = None  # Virtual Key ID for Grok
    PORTKEY_VIRTUAL_KEY_GOOGLE: Optional[str] = None  # Virtual Key ID for Google (Vertex AI)
    PORTKEY_VIRTUAL_KEY_AZURE: Optional[str] = None  # Virtual Key ID for Azure
    PORTKEY_VIRTUAL_KEY_AWS: Optional[str] = None  # Virtual Key ID for AWS (Bedrock)
    PORTKEY_VIRTUAL_KEY_PINECONE: Optional[str] = None  # Virtual Key ID for Pinecone
    PORTKEY_VIRTUAL_KEY_WEAVIATE: Optional[str] = None  # Virtual Key ID for Weaviate
    PORTKEY_VIRTUAL_KEY_ELEVENLABS: Optional[str] = None  # Virtual Key ID for ElevenLabs

    # Legacy fields (keeping for backward compatibility)
    VIRTUAL_KEY: Optional[str] = None  # Existing virtual key field, keeping for now
    PORTKEY_FALLBACKS: Optional[str] = None  # JSON string of fallback config, keeping for now

    # Site information (used for API request headers)
    SITE_URL: str = "http://localhost"
    SITE_TITLE: str = "Orchestra-Main Development"

    # Configuration using Pydantic v2 syntax
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",  # Allow extra fields that aren't defined in the model
    )

    def get_portkey_fallbacks(self) -> Optional[List[Dict[str, Any]]]:
        """
        Parse and return the Portkey fallback configuration.

        Returns:
            Optional[List[Dict[str, Any]]]: List of fallback configurations or None if not set
        """
        if not self.PORTKEY_FALLBACKS:
            return None

        try:
            return json.loads(self.PORTKEY_FALLBACKS)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse PORTKEY_FALLBACKS: {e}")
            return None

    def get_openrouter_headers(self) -> Dict[str, str]:
        """
        Get OpenRouter custom headers.

        Returns:
            Dict[str, str]: Dictionary of headers to include with OpenRouter requests
        """
        # Default headers
        headers = {
            "HTTP-Referer": self.SITE_URL,
            "X-Title": self.SITE_TITLE,
        }

        # Add free model fallbacks if specified
        if self.OPENROUTER_FREE_FALLBACKS:
            # Convert comma-separated list to colon-separated format required by OpenRouter
            free_models = self.OPENROUTER_FREE_FALLBACKS.replace(" ", "").split(",")
            if free_models:
                headers["fallback_providers"] = ":".join(free_models)

        # Add custom headers if specified
        if self.OPENROUTER_HEADERS:
            try:
                custom_headers = json.loads(self.OPENROUTER_HEADERS)
                headers.update(custom_headers)
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse OPENROUTER_HEADERS: {e}")

        return headers

    def get_agent_model_map(self) -> Dict[str, str]:
        """
        Parse and return the agent-to-model mapping.

        Returns:
            Dict[str, str]: Dictionary mapping agent roles to specific models
        """
        if not self.AGENT_MODEL_MAP:
            return {}

        try:
            return json.loads(self.AGENT_MODEL_MAP)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse AGENT_MODEL_MAP: {e}")
            return {}

    def get_mode_model_map(self) -> Dict[str, Dict[str, str]]:
        """
        Parse and return the mode-to-model mapping.

        Returns:
            Dict[str, Dict[str, str]]: Dictionary mapping Roo modes to specific models and providers
        """
        if not self.MODE_MODEL_MAP:
            return self.MODE_MODEL_MAP_DEFAULT

        try:
            return json.loads(self.MODE_MODEL_MAP)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse MODE_MODEL_MAP: {e}")
            return self.MODE_MODEL_MAP_DEFAULT

    def get_portkey_strategy_config(self) -> Dict[str, Any]:
        """
        Get Portkey strategy configuration.

        Returns:
            Dict[str, Any]: Dictionary with Portkey strategy configuration
        """
        config = {"mode": self.PORTKEY_STRATEGY}

        # For load balancing strategy, we can get weights from the fallbacks
        if self.PORTKEY_STRATEGY == "loadbalance" and self.get_portkey_fallbacks():
            weights = {}
            for item in self.get_portkey_fallbacks():
                model = item.get("model")
                weight = item.get("weight", 1)
                if model:
                    weights[model] = weight

            if weights:
                config["weights"] = weights

        return config

    def get_gcp_project_id(self) -> Optional[str]:
        """
        Get the Google Cloud project ID from settings.

        Checks GCP_PROJECT_ID first, then falls back to GOOGLE_CLOUD_PROJECT
        if available.

        Returns:
            Optional[str]: Project ID or None if not set
        """
        return self.GCP_PROJECT_ID or self.GOOGLE_CLOUD_PROJECT

    def get_gcp_credentials_info(self) -> Dict[str, Any]:
        """
        Get GCP credentials information from settings.

        Returns:
            Dict[str, Any]: Dictionary with GCP credentials information
        """
        return {
            "project_id": self.get_gcp_project_id(),
            "credentials_path": self.GOOGLE_APPLICATION_CREDENTIALS,
            "service_account_json": self.GCP_SA_KEY_JSON,
            "location": self.GCP_LOCATION,
        }


def get_settings() -> Settings:
    """
    Get application settings.

    Returns:
        Settings: Application settings instance.
    """
    return Settings()
