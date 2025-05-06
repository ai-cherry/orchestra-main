"""
Portkey LLM client implementation.

This module provides a client for Portkey's API with built-in retry logic and model fallback
capabilities to handle rate limits and service interruptions gracefully.
"""

from typing import Dict, List, Any, Optional, Union
import os
import logging
import asyncio
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryError,
)

try:
    from openai import (
        OpenAI,
        APITimeoutError,
        APIConnectionError,
        RateLimitError,
        APIStatusError,
    )
    from portkey_ai import Portkey
    from portkey_ai.api_resources.exceptions import APIError as PortkeyAPIError
except ImportError:
    logging.error(
        "Required packages not found. Please install with: pip install openai portkey tenacity"
    )
    raise

from core.orchestrator.src.config.settings import Settings, get_settings
from .interface import LLMClient
from infra.modules.advanced-monitoring.auto_instrumentation import llm_call

# Configure logging
logger = logging.getLogger(__name__)


class PortkeyClientException(Exception):
    """Base exception for Portkey client errors."""

    pass


class PortkeyClient(LLMClient):
    """
    Portkey client implementation with robust error handling.

    This client leverages Portkey's API which provides access to multiple
    LLM providers with built-in routing, fallback capabilities, and observability.

    Features:
    - Automatic retries and fallbacks via Portkey Gateway Configs
    - Detailed error reporting and logging
    """

    def __init__(self, settings: Settings):
        """
        Initialize the Portkey client using application settings.

        Args:
            settings: Application settings instance containing Portkey configuration.

        Raises:
            PortkeyClientException: If the Portkey API key is not found in settings.
        """
        self.settings = settings  # Store settings object

        # Try to get the Portkey API key from various sources
        self.api_key = self._get_portkey_api_key(settings)

        if not self.api_key:
            error_msg = (
                "Portkey API key not found in environment variables, .env file, or organization secrets"
            )
            logger.error(error_msg)
            raise PortkeyClientException(
                f"{error_msg}. Please add PORTKEY_API_KEY to your environment "
                "variables, .env file, or GitHub organization secrets. "
                "You can get a key from https://portkey.ai."
            )

        # Base configuration with API key and trace ID
        portkey_config = {
            "api_key": self.api_key,
            "trace_id": settings.TRACE_ID,
        }

        # First approach: Use CONFIG_ID if available
        if settings.PORTKEY_CONFIG_ID:
            portkey_config["config"] = settings.PORTKEY_CONFIG_ID
            logger.info(
                f"Initializing Portkey client with Config ID: {settings.PORTKEY_CONFIG_ID}")
        else:
            # Second approach: Build dynamic config with targets, fallbacks, caching
            targets = []

            # Add OpenRouter as primary target if virtual key exists
            if settings.PORTKEY_VIRTUAL_KEY_OPENROUTER:
                targets.append({
                    "provider": "openrouter",
                    "virtual_key": settings.PORTKEY_VIRTUAL_KEY_OPENROUTER
                    # Model will come from the API call
                })

            # Add fallbacks conditionally if their virtual keys exist
            if settings.PORTKEY_VIRTUAL_KEY_OPENAI:
                targets.append({
                    "provider": "openai",
                    "virtual_key": settings.PORTKEY_VIRTUAL_KEY_OPENAI,
                    "override_params": {"model": settings.DEFAULT_LLM_MODEL_FALLBACK_OPENAI}
                })

            if settings.PORTKEY_VIRTUAL_KEY_ANTHROPIC:
                targets.append({
                    "provider": "anthropic",
                    "virtual_key": settings.PORTKEY_VIRTUAL_KEY_ANTHROPIC,
                    "override_params": {"model": settings.DEFAULT_LLM_MODEL_FALLBACK_ANTHROPIC}
                })

            # Only configure strategy if we have multiple targets
            if len(targets) > 1:
                strategy_config = {
                    "mode": "fallback",
                    "on_status_codes": [429, 500, 503]
                }

                portkey_config["strategy"] = strategy_config
                portkey_config["targets"] = targets
                portkey_config["retry"] = {"attempts": 3}

                # Add caching if enabled
                if settings.PORTKEY_CACHE_ENABLED or settings.LLM_SEMANTIC_CACHE_ENABLED:
                    portkey_config["cache"] = {
                        "mode": "semantic",
                        "fallback": "openai",
                        "threshold": settings.LLM_SEMANTIC_CACHE_THRESHOLD,
                        "ttl": settings.LLM_SEMANTIC_CACHE_TTL
                    }

                logger.info(
                    f"Initialized Portkey client with fallback strategy and {len(targets)} targets")
            elif len(targets) == 1:
                logger.warning(
                    "Only one target provider configured. Fallback strategy disabled.")
                # Still set the single target to use the virtual key
                portkey_config["provider"] = targets[0]["provider"]
                portkey_config["virtual_key"] = targets[0]["virtual_key"]
            else:
                # No targets configured
                logger.warning(
                    "No provider targets configured. Using default Portkey behavior.")
                # Use legacy VIRTUAL_KEY if available
                if settings.VIRTUAL_KEY:
                    portkey_config["virtual_key"] = settings.VIRTUAL_KEY
                    logger.warning(
                        "Using deprecated VIRTUAL_KEY setting. Please update to provider-specific virtual keys.")

        # Initialize Portkey client with configured settings
        self._portkey_client = Portkey(**portkey_config)

        # Store provider-to-virtual-key mapping for dynamic selection
        self._provider_virtual_keys = {
            "openai": settings.PORTKEY_VIRTUAL_KEY_OPENAI,
            "anthropic": settings.PORTKEY_VIRTUAL_KEY_ANTHROPIC,
            "mistral": settings.PORTKEY_VIRTUAL_KEY_MISTRAL,
            "huggingface": settings.PORTKEY_VIRTUAL_KEY_HUGGINGFACE,
            "cohere": settings.PORTKEY_VIRTUAL_KEY_COHERE,
            "openrouter": settings.PORTKEY_VIRTUAL_KEY_OPENROUTER,
            "perplexity": settings.PORTKEY_VIRTUAL_KEY_PERPLEXITY,
            "deepseek": settings.PORTKEY_VIRTUAL_KEY_DEEPSEEK,
            "codestral": settings.PORTKEY_VIRTUAL_KEY_CODESTRAL,
            "cody": settings.PORTKEY_VIRTUAL_KEY_CODY,
            "continue": settings.PORTKEY_VIRTUAL_KEY_CONTINUE,
            "grok": settings.PORTKEY_VIRTUAL_KEY_GROK,
            "google": settings.PORTKEY_VIRTUAL_KEY_GOOGLE,
            "azure": settings.PORTKEY_VIRTUAL_KEY_AZURE,
            "aws": settings.PORTKEY_VIRTUAL_KEY_AWS,
            "pinecone": settings.PORTKEY_VIRTUAL_KEY_PINECONE,
            "weaviate": settings.PORTKEY_VIRTUAL_KEY_WEAVIATE,
            "elevenlabs": settings.PORTKEY_VIRTUAL_KEY_ELEVENLABS,
        }

        # For backward compatibility
        if settings.VIRTUAL_KEY and not any(self._provider_virtual_keys.values()):
            logger.warning(
                "Using deprecated VIRTUAL_KEY setting. Please update to provider-specific virtual keys.")
            self._default_virtual_key = settings.VIRTUAL_KEY
        else:
            self._default_virtual_key = None

        # Log initialization
        logger.info(
            "Portkey client initialized with: "
            f"API Key (masked): {'*' * (len(self.api_key) - 4) + self.api_key[-4:]}, "
            f"Config ID: {self.settings.PORTKEY_CONFIG_ID}, "
            f"Available virtual keys: {[k for k, v in self._provider_virtual_keys.items() if v]}"
        )

    def _get_portkey_api_key(self, settings: Settings) -> Optional[str]:
        """Get Portkey API key from settings, environment, or organization secrets."""
        # First try from settings
        if settings.PORTKEY_API_KEY:
            return settings.PORTKEY_API_KEY

        # Then try environment variables with common naming patterns
        for key_name in [
            "PORTKEY_API_KEY",
            "PORTKEY_KEY",
            "PORTKEY_SECRET",
            "ORG_PORTKEY_API_KEY",
            "GITHUB_PORTKEY_API_KEY",
            "GH_PORTKEY_API_KEY"
        ]:
            value = os.environ.get(key_name)
            if value:
                logger.info(
                    f"Using Portkey API key from environment variable: {key_name}")
                return value

        # Check for GitHub Actions secret format: ${{ secrets.KEY_NAME }}
        for env_key, env_value in os.environ.items():
            if isinstance(env_value, str) and env_value.startswith("${{") and "secrets.PORTKEY" in env_value:
                import re
                match = re.search(r'secrets\.([A-Za-z0-9_]+)', env_value)
                if match:
                    secret_name = match.group(1)
                    secret_value = os.environ.get(secret_name)
                    if secret_value:
                        logger.info(
                            f"Using Portkey API key from GitHub secret: {secret_name}")
                        return secret_value

        return None

    def _get_provider_from_model(self, model: str) -> str:
        """
        Determine the provider based on the model name.

        Args:
            model: Model identifier (e.g., 'gpt-4', 'claude-3-opus', 'mistral-large')

        Returns:
            The provider name (e.g., 'openai', 'anthropic', 'mistral')
        """
        model_lower = model.lower()

        # Check for provider prefixes in format "provider/model"
        if "/" in model_lower:
            provider, _ = model_lower.split("/", 1)
            return provider

        # Match based on model name patterns
        if any(name in model_lower for name in ["gpt-", "ft:gpt-", "text-davinci", "text-embedding"]):
            return "openai"
        elif any(name in model_lower for name in ["claude", "anthropic"]):
            return "anthropic"
        elif any(name in model_lower for name in ["mistral", "mixtral"]):
            return "mistral"
        elif "cohere" in model_lower or model_lower.startswith("command-"):
            return "cohere"
        elif "gemini" in model_lower or "palm" in model_lower:
            return "google"
        elif "llama" in model_lower and "meta" in model_lower:
            return "meta"
        elif "j2" in model_lower and "ai21" in model_lower:
            return "ai21"
        elif any(name in model_lower for name in ["deepseek"]):
            return "deepseek"
        elif any(name in model_lower for name in ["perplexity"]):
            return "perplexity"
        elif any(name in model_lower for name in ["codestral"]):
            return "codestral"

        # Default to openrouter if we can't determine
        return "openrouter"

    @retry(
        retry=retry_if_exception_type(
            (APITimeoutError, APIConnectionError, APIStatusError)
        ),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    @llm_call(provider="portkey", track_prompt=True, track_response=False, error_threshold_ms=5000)
    async def generate_response(
        self,
        model: str,
        messages: List[Dict[str, str]],
        user_id: Optional[str] = None,
        active_persona_name: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Generate a response from the specified LLM based on the provided messages.

        This method includes automatic retry logic with exponential backoff for
        transient errors such as timeouts and connection issues, and injects metadata.
        It automatically selects the appropriate virtual key based on the model provider.

        Args:
            model: The model identifier to use for generation
            messages: A list of message dictionaries in the ChatML format
                     (each with 'role' and 'content' keys)
            user_id: Optional user ID for metadata.
            active_persona_name: Optional active persona name for metadata.
            **kwargs: Additional model-specific parameters (e.g., temperature, max_tokens)

        Returns:
            The generated text response from the LLM

        Raises:
            PortkeyClientException: If there's an unrecoverable error communicating with the API
        """
        logger.debug(f"Generating response with model: {model}")

        # Prepare metadata for Portkey
        metadata = {
            "trace_source": "orchestra_main_api",
        }
        if user_id:
            metadata["user_id"] = user_id
        if active_persona_name:
            metadata["active_persona"] = active_persona_name
        # Add other relevant context like agent_id if applicable - needs to be passed in if required

        try:
            # Determine provider and virtual key
            provider = self._get_provider_from_model(model)
            virtual_key = self._provider_virtual_keys.get(
                provider) or self._default_virtual_key

            # Set up client options with model
            client_options = {
                "default_headers": {"model": model}
            }

            # Set up Portkey client with appropriate configuration
            client = self._portkey_client

            # Add config ID if available
            if self.settings.PORTKEY_CONFIG_ID:
                client = client.with_options(
                    config=self.settings.PORTKEY_CONFIG_ID)

            # Add virtual key and provider if available
            if virtual_key:
                logger.debug(
                    f"Using virtual key for provider {provider}: {virtual_key}")
                client = client.with_options(
                    virtual_key=virtual_key, provider=provider)
            elif provider == "openrouter" and self.settings.OPENROUTER_API_KEY:
                # Special case for OpenRouter - use direct API key if virtual key not available
                logger.debug(
                    "Using direct OpenRouter API key (no virtual key found)")
                # This ensures backward compatibility with existing OpenRouter integration
                client = client.with_options(provider="openrouter")

            # Create the completion
            completion = await client.chat.completions.create(
                model=model,
                messages=messages,
                metadata=metadata,  # Inject metadata here
                **kwargs,  # Pass through temperature, max_tokens, etc.
            )

            # Extract and return the response text
            if completion.choices and completion.choices[0].message:
                logger.debug("Successfully received response from Portkey")
                return completion.choices[0].message.content or ""
            else:
                error_msg = "Received invalid response format from Portkey"
                logger.error(f"{error_msg}. Completion: {completion}")
                return self._user_friendly_error(
                    "The AI system received an incomplete response. Please try again."
                )

        except RateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}")
            # This exception is not retried by the decorator as it's not temporary
            # and requires fallback or waiting for rate limit reset
            return self._user_friendly_error(
                "The AI system is currently receiving too many requests. "
                "Please try again in a few minutes."
            )

        except (APITimeoutError, APIConnectionError, APIStatusError) as e:
            # These exceptions will be caught and retried by the decorator
            logger.warning(
                f"Retryable error occurred: {type(e).__name__}: {e}")
            raise

        except PortkeyAPIError as e:
            # Portkey-specific exceptions
            logger.error(f"Portkey API error: {e}")
            return self._user_friendly_error(
                "There was an issue with the AI service. Please try again later."
            )

        except Exception as e:
            # Catch-all for unexpected errors
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
            return self._user_friendly_error(
                "The AI system encountered an unexpected error. "
                "Please try again. If the problem persists, contact support."
            )

    def _user_friendly_error(self, message: str) -> str:
        """
        Format a user-friendly error message.

        Args:
            message: The error message to format

        Returns:
            A formatted error message for the user
        """
        return f"⚠️ {message}"

    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health status of the Portkey client.

        Returns:
            Dict with health status information
        """
        return {
            "status": "healthy",
            "api_key_configured": bool(self.api_key),
            "fallback_configured": "fallbacks"
            in getattr(self._portkey_client, "config", {}),
        }
