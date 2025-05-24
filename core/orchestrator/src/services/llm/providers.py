"""
LLM Providers for AI Orchestration System.

# AI-CONTEXT: This file defines the LLM provider interfaces and implementations.
# AI-CONTEXT: See LLM_PROVIDER_CONTEXT.md in this directory for architectural details.
# AI-CONTEXT: The system implements a sophisticated fallback mechanism between providers.
# AI-CONTEXT: Implementations include OpenRouterProvider and PortkeyProvider.

This module provides interfaces and implementations for Large Language Model providers
that can be used by agents in the orchestration system. Providers implement the Service
interface for proper lifecycle management and integrate with the unified registry system.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set

import httpx
from openai import (
    APIConnectionError,
    APIError,
    AsyncOpenAI,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    RateLimitError,
)
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
)

try:
    from portkey_ai import PortkeyAPIError, PortkeyException
except ImportError:
    PortkeyException = Exception
    PortkeyAPIError = Exception

# Import the settings instance directly
from core.orchestrator.src.config.config import settings
from core.orchestrator.src.services.llm.exceptions import (
    LLMProviderAuthenticationError,
    LLMProviderConnectionError,
    LLMProviderError,
    LLMProviderInvalidRequestError,
    LLMProviderModelError,
    LLMProviderRateLimitError,
    LLMProviderServiceError,
    LLMProviderTimeoutError,
)
from core.orchestrator.src.services.unified_registry import Service, register

# Configure logging
logger = logging.getLogger(__name__)


class LLMProviderConfig:
    """Configuration for LLM provider."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        default_model: str,
        request_timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_max_delay: float = 10.0,
        retryable_errors: Optional[Set[str]] = None,
    ):
        """
        Initialize LLM provider configuration.

        Args:
            api_key: API key for the provider
            base_url: Base URL for the API
            default_model: Default model to use
            request_timeout: Request timeout in seconds
            max_retries: Maximum number of retries for transient errors
            retry_delay: Initial retry delay in seconds
            retry_max_delay: Maximum retry delay in seconds
            retryable_errors: Set of error types that should be retried
        """
        self.api_key = api_key
        self.base_url = base_url
        self.default_model = default_model
        self.request_timeout = request_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_max_delay = retry_max_delay

        # Default retryable errors if not specified
        self.retryable_errors = retryable_errors or {
            "connection_error",
            "timeout_error",
            "rate_limit_error",
            "service_error",
        }

    def validate(self) -> None:
        """
        Validate configuration parameters.

        Raises:
            ValueError: If configuration is invalid
        """
        if not self.api_key:
            raise ValueError("API key must be provided")

        if not self.base_url:
            raise ValueError("Base URL must be provided")

        if not self.default_model:
            raise ValueError("Default model must be provided")

        if self.request_timeout <= 0:
            raise ValueError("Request timeout must be positive")

        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")


class LLMProvider(Service, ABC):
    """
    Abstract base class for LLM providers.

    Implements the Service interface to ensure proper lifecycle management
    and integration with the unified registry system.
    """

    def initialize(self) -> None:
        """
        Initialize the provider.

        This method is called during service initialization.
        Override to perform provider-specific setup.
        """

    async def initialize_async(self) -> None:
        """
        Initialize the provider asynchronously.

        This method is called during async service initialization.
        The default implementation calls the synchronous initialize method.
        """
        if hasattr(self, "initialize") and callable(self.initialize):
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.initialize)

    def close(self) -> None:
        """
        Close the provider and release resources.

        This method is called during service shutdown.
        Override to perform provider-specific cleanup.
        """

    async def close_async(self) -> None:
        """
        Close the provider asynchronously.

        This method is called during async service shutdown.
        The default implementation calls the synchronous close method.
        """
        if hasattr(self, "close") and callable(self.close):
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.close)

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get provider name."""

    @property
    def default_model(self) -> str:
        """Get default model name."""
        return "unknown"

    @abstractmethod
    async def generate_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate text completion.

        Args:
            prompt: Prompt text
            model: Model to use
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            Dictionary containing response text and metadata

        Raises:
            LLMProviderError: Base class for all LLM provider errors
        """

    @abstractmethod
    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate chat completion.

        Args:
            messages: List of message objects with role and content
            model: Model to use
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            Dictionary containing response content and metadata

        Raises:
            LLMProviderError: Base class for all LLM provider errors
        """


class OpenRouterProvider(LLMProvider):
    """
    OpenRouter LLM provider implementation with robust error handling and retries.

    This provider interfaces with the OpenRouter API, which provides access to
    various LLM models from different providers through a unified interface.

    Enhanced for Pro Tier with improved rate limit handling and model routing.
    """

    def __init__(self, config: LLMProviderConfig, headers: Optional[Dict[str, str]] = None):
        """
        Initialize OpenRouter provider.

        Args:
            config: Provider configuration
            headers: Optional custom headers for OpenRouter requests
        """
        self.config = config
        self._client = None
        self.custom_headers = headers or {}
        self.agent_model_map = {}

        # Validate configuration
        config.validate()

    def initialize(self) -> None:
        """
        Initialize the provider.

        This creates the OpenAI client and validates the configuration.
        """
        try:
            # Set up httpx client with timeout
            client_timeout = httpx.Timeout(
                timeout=self.config.request_timeout,
                connect=min(5.0, self.config.request_timeout / 2),
            )

            # Initialize OpenAI client for OpenRouter
            self._client = AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=client_timeout,
                max_retries=0,  # We handle retries ourselves with more control
            )

            # Access the global settings instance directly
            # settings = get_settings() # Removed this line

            # Load agent-to-model mapping if available
            # Assuming settings instance has get_agent_model_map method
            self.agent_model_map = settings.get_agent_model_map()

            logger.info(f"Initialized {self.provider_name} provider with model {self.config.default_model}")
            logger.info(f"OpenRouter Pro Tier configuration active with {len(self.custom_headers)} custom headers")
        except Exception as e:
            logger.error(
                f"Failed to initialize {self.provider_name} provider: {e}",
                exc_info=True,
            )
            logger.warning(
                f"{self.provider_name} provider initialization failed; AI functionalities may be limited or unavailable."
            )

    def close(self) -> None:
        """
        Close the provider and release resources.

        This closes the OpenAI client and releases associated resources.
        """
        if hasattr(self._client, "close") and callable(self._client.close):
            try:
                self._client.close()
                logger.debug(f"Closed {self.provider_name} provider client")
            except Exception as e:
                logger.warning(f"Error closing {self.provider_name} provider client: {e}")

        self._client = None

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "openrouter"

    @property
    def default_model(self) -> str:
        """Get default model name."""
        return self.config.default_model

    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        return self._client is not None

    def get_model_for_agent(self, agent_type: Optional[str] = None, mode: Optional[str] = None) -> str:
        """
        Get the appropriate model for a specific agent type or mode.

        Args:
            agent_type: The type of agent making the request
            mode: The current Roo mode (orchestrator, reviewer, etc.)

        Returns:
            The model identifier to use
        """
        # Check settings for mode-specific model mapping
        mode_model_map = settings.get_mode_model_map()

        # Mode-specific model takes highest priority
        if mode and mode in mode_model_map:
            return mode_model_map[mode]["model"]

        # Agent-specific model takes second priority
        if agent_type and agent_type in self.agent_model_map:
            return self.agent_model_map[agent_type]

        # Default to provider's default model
        return self.default_model

    def _should_retry(self, exception: Exception) -> bool:
        """
        Determine if an exception should be retried.

        Args:
            exception: The exception to check

        Returns:
            True if the exception should be retried, False otherwise
        """
        if isinstance(exception, LLMProviderConnectionError) and "connection_error" in self.config.retryable_errors:
            return True
        elif isinstance(exception, LLMProviderTimeoutError) and "timeout_error" in self.config.retryable_errors:
            return True
        elif isinstance(exception, LLMProviderRateLimitError) and "rate_limit_error" in self.config.retryable_errors:
            return True
        elif isinstance(exception, LLMProviderServiceError) and "service_error" in self.config.retryable_errors:
            return True
        return False

    def _get_retry_decorator(self):
        """
        Create a retry decorator based on configuration.

        Returns:
            A configured retry decorator
        """
        return retry(
            retry=lambda e: self._should_retry(e),
            stop=stop_after_attempt(self.config.max_retries),
            wait=wait_exponential(
                multiplier=self.config.retry_delay,
                min=self.config.retry_delay,
                max=self.config.retry_max_delay,
            ),
            reraise=True,
            before_sleep=lambda retry_state: logger.info(
                f"Retrying after error, attempt {retry_state.attempt_number} of {self.config.max_retries}"
            ),
        )

    async def generate_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        agent_type: Optional[str] = None,
        mode: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate text completion.

        Args:
            prompt: Prompt text
            model: Model to use
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            agent_type: Type of agent making the request (for model routing)
            mode: Current Roo mode (orchestrator, reviewer, etc.) for model selection
            **kwargs: Additional parameters to pass to the API

        Returns:
            Dictionary containing response text and metadata

        Raises:
            LLMProviderError: If the API call fails
        """
        # Ensure provider is initialized
        if not self.is_initialized:
            self.initialize()

        # If no model specified, check mode first, then agent_type
        if not model:
            model = self.get_model_for_agent(agent_type, mode)

        # For OpenRouter, we'll adapt the prompt to chat format
        messages = [{"role": "user", "content": prompt}]
        return await self.generate_chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            agent_type=agent_type,
            **kwargs,
        )

    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        agent_type: Optional[str] = None,
        mode: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate chat completion with robust error handling.

        Args:
            messages: List of message objects with role and content
            model: Model to use (overrides other selectors if provided)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            agent_type: Type of agent making the request (for model routing)
            mode: Current Roo mode (orchestrator, reviewer, etc.) for model selection
            **kwargs: Additional parameters to pass to the API

        Returns:
            Dictionary containing response content and metadata

        Raises:
            LLMProviderAuthenticationError: If authentication fails
            LLMProviderConnectionError: If connection to the API fails
            LLMProviderRateLimitError: If rate limits are exceeded
            LLMProviderInvalidRequestError: If the request is invalid
            LLMProviderServiceError: If the API returns a server error
            LLMProviderTimeoutError: If the request times out
            LLMProviderError: For other unexpected errors
        """
        # If model not explicitly specified, use mode/agent-based selection
        if not model:
            model = self.get_model_for_agent(agent_type, mode)
        else:
            # Use provided model or fallback to default
            model = model or self.config.default_model

        # Check if mode requires a different provider
        if mode:
            mode_model_map = settings.get_mode_model_map()
            if mode in mode_model_map and mode_model_map[mode]["provider"] != self.provider_name:
                logger.info(
                    f"Mode '{mode}' requires provider '{mode_model_map[mode]['provider']}' instead of '{self.provider_name}'"
                )
                # We continue with the current provider but log the mismatch

        # Validate messages
        if not messages or not isinstance(messages, list):
            raise LLMProviderInvalidRequestError("Messages must be a non-empty list")

        for msg in messages:
            if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                raise LLMProviderInvalidRequestError("Each message must be a dict with 'role' and 'content' keys")

        # Apply retry decorator dynamically
        retry_decorator = self._get_retry_decorator()

        # This will apply the retry logic to an inner function that handles the actual API call
        @retry_decorator
        async def _make_api_call():
            # Ensure provider is initialized
            if not self.is_initialized:
                self.initialize()

            try:
                # Measure request time for logging and monitoring
                start_time = time.time()

                # Create parameters dictionary with all options
                params = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    **kwargs,
                }

                # Add max_tokens if provided
                if max_tokens is not None:
                    params["max_tokens"] = max_tokens

                # Combine default and custom headers
                headers = self.custom_headers.copy()

                # Make the API call
                response = await self._client.chat.completions.create(**params, extra_headers=headers)

                # Calculate request duration
                duration_ms = int((time.time() - start_time) * 1000)

                # Log success with timing information
                logger.info(
                    f"LLM request successful: model={model}, "
                    f"tokens={response.usage.total_tokens}, "
                    f"time={duration_ms}ms"
                )

                # Format and return the response
                return {
                    "content": response.choices[0].message.content,
                    "model": response.model,
                    "provider": self.provider_name,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    },
                    "finish_reason": response.choices[0].finish_reason,
                    "response_time_ms": duration_ms,
                }

            except AuthenticationError as e:
                logger.error(f"Authentication error with {self.provider_name}: {str(e)}")
                raise LLMProviderAuthenticationError(f"API authentication failed: {str(e)}")

            except APIConnectionError as e:
                logger.error(f"Connection error with {self.provider_name}: {str(e)}")
                raise LLMProviderConnectionError(f"API connection failed: {str(e)}")

            except RateLimitError as e:
                logger.warning(f"Rate limit exceeded for {self.provider_name}: {str(e)}")
                # This will be retried by the decorator if configured
                raise LLMProviderRateLimitError(f"Rate limit exceeded: {str(e)}")

            except BadRequestError as e:
                logger.error(f"Invalid request to {self.provider_name}: {str(e)}")
                raise LLMProviderInvalidRequestError(f"Invalid request: {str(e)}")

            except InternalServerError as e:
                logger.error(f"Internal server error from {self.provider_name}: {str(e)}")
                # This will be retried by the decorator if configured
                raise LLMProviderServiceError(f"Service error: {str(e)}")

            except asyncio.TimeoutError:
                logger.error(f"Request to {self.provider_name} timed out after {self.config.request_timeout}s")
                # This will be retried by the decorator if configured
                raise LLMProviderTimeoutError(f"Request timed out after {self.config.request_timeout} seconds")

            except APIError as e:
                if "model" in str(e).lower():
                    logger.error(f"Model error with {self.provider_name}: {str(e)}")
                    raise LLMProviderModelError(f"Model error: {str(e)}")
                else:
                    logger.error(f"API error with {self.provider_name}: {str(e)}")
                    raise LLMProviderServiceError(f"API error: {str(e)}")

            except Exception as e:
                logger.error(
                    f"Unexpected error with {self.provider_name}: {str(e)}",
                    exc_info=True,
                )
                raise LLMProviderError(f"Unexpected error: {str(e)}")

        # Call the decorated function
        return await _make_api_call()


class PortkeyProvider(LLMProvider):
    """
    Portkey LLM provider implementation with basic functionality.

    This provider interfaces with Portkey's API, which provides a unified interface
    for multiple LLM providers. Simplified for single-developer use case.
    """

    def __init__(self, config: LLMProviderConfig, fallback_config=None):
        """
        Initialize Portkey provider.

        Args:
            config: Provider configuration
            fallback_config: Optional fallback configuration
        """
        self.config = config
        self._client = None
        self.fallback_config = fallback_config
        self.settings_instance = settings  # Store reference to settings

        # Validate configuration
        config.validate()

    def initialize(self) -> None:
        """
        Initialize the provider.
        """
        try:
            from portkey import Portkey
        except ImportError:
            error_msg = "Portkey package not installed. Please install with: pip install portkey>=1.0.0"
            logger.error(error_msg)
            raise ImportError(error_msg)

        # Configure Portkey client with simplified settings
        portkey_config = {
            "api_key": self.config.api_key,
            # Simple retry configuration
            "retry": {
                "attempts": self.config.max_retries,
            },
            "trace_id": self.settings_instance.TRACE_ID if hasattr(self.settings_instance, "TRACE_ID") else None,
            "virtual_key": (
                self.settings_instance.PORTKEY_VIRTUAL_KEY_OPENROUTER
                if hasattr(self.settings_instance, "PORTKEY_VIRTUAL_KEY_OPENROUTER")
                else None
            ),
            "provider": "openrouter",  # Set default provider
        }

        # Add fallbacks if provided
        if self.fallback_config:
            portkey_config["fallbacks"] = self.fallback_config
            portkey_config["strategy"] = {"mode": "fallback"}

        # Initialize Portkey client
        self._client = Portkey(**portkey_config)

        logger.info(f"Initialized {self.provider_name} provider with model {self.config.default_model}")

    def close(self) -> None:
        """
        Close the provider and release resources.
        """
        self._client = None
        logger.debug(f"Closed {self.provider_name} provider client")

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "portkey"

    @property
    def default_model(self) -> str:
        """Get default model name."""
        return self.config.default_model

    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        return self._client is not None

    def get_model_for_mode(self, agent_type: Optional[str] = None, mode: Optional[str] = None) -> str:
        """
        Get the appropriate model based on Roo mode and agent type.

        Args:
            agent_type: The type of agent making the request
            mode: The current Roo mode (orchestrator, reviewer, etc.)

        Returns:
            The model identifier to use
        """
        # Check settings for mode-specific model mapping
        mode_model_map = settings.get_mode_model_map()

        # Mode-specific model takes highest priority
        if mode and mode in mode_model_map:
            return mode_model_map[mode]["model"]

        # Default to provider's default model
        return self.default_model

    async def generate_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        agent_type: Optional[str] = None,
        mode: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate text completion.

        Args:
            prompt: Prompt text
            model: Model to use
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            agent_type: Type of agent making the request
            mode: Current Roo mode (orchestrator, reviewer, etc.)
            **kwargs: Additional parameters
        """
        # Ensure provider is initialized
        if not self.is_initialized:
            self.initialize()

        # If no model specified, check mode first
        if not model:
            model = self.get_model_for_mode(agent_type, mode)

        # Adapt the prompt to chat format
        messages = [{"role": "user", "content": prompt}]
        return await self.generate_chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            agent_type=agent_type,
            mode=mode,
            **kwargs,
        )

    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        agent_type: Optional[str] = None,
        mode: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate chat completion with basic error handling.

        Args:
            messages: List of message objects with role and content
            model: Model to use (overrides other selectors if provided)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            agent_type: Type of agent making the request
            mode: Current Roo mode (orchestrator, reviewer, etc.)
            **kwargs: Additional parameters
        """
        # If no model specified, use mode-based selection
        if not model:
            model = self.get_model_for_mode(agent_type, mode)
        else:
            model = model or self.config.default_model

        # Check if mode requires a different provider
        if mode:
            mode_model_map = settings.get_mode_model_map()
            if mode in mode_model_map and mode_model_map[mode]["provider"] != self.provider_name:
                logger.info(
                    f"Mode '{mode}' requires provider '{mode_model_map[mode]['provider']}' instead of '{self.provider_name}'"
                )
                # We continue with the current provider but log the mismatch

        # Validate messages
        if not messages or not isinstance(messages, list):
            raise LLMProviderInvalidRequestError("Messages must be a non-empty list")

        # Ensure provider is initialized
        if not self.is_initialized:
            self.initialize()

        try:
            # Measure request time for logging and monitoring
            start_time = time.time()

            # Create parameters dictionary with all options
            params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                **kwargs,
            }

            # Add max_tokens if provided
            if max_tokens is not None:
                params["max_tokens"] = max_tokens

            # Make the API call with config ID applied per-request
            client = self._client.with_options(default_headers={"model": model})

            # Apply the config ID if available
            if hasattr(self.settings_instance, "PORTKEY_CONFIG_ID") and self.settings_instance.PORTKEY_CONFIG_ID:
                client = client.with_options(config=self.settings_instance.PORTKEY_CONFIG_ID)

            response = await client.chat.completions.create(**params)

            # Calculate request duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log success with timing information
            logger.info(
                f"LLM request successful: model={model}, "
                f"tokens={response.usage.total_tokens}, "
                f"time={duration_ms}ms"
            )

            # Format and return the response
            return {
                "content": response.choices[0].message.content,
                "model": response.model,
                "provider": self.provider_name,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                "finish_reason": response.choices[0].finish_reason,
                "response_time_ms": duration_ms,
            }

        except Exception as exc:
            logger.error(f"Error with {self.provider_name}: {str(exc)}", exc_info=True)
            raise LLMProviderError(f"API error: {str(exc)}")


def get_provider_for_mode(mode: Optional[str] = None) -> str:
    """
    Determine the appropriate provider based on the Roo mode.

    Args:
        mode: The current Roo mode (orchestrator, reviewer, etc.)

    Returns:
        The provider name to use
    """
    if not mode:
        return getattr(settings, "PREFERRED_LLM_PROVIDER", "openrouter")

    # Get the mode-to-model mapping
    mode_model_map = settings.get_mode_model_map()

    # Check if the mode exists in the mapping
    if mode in mode_model_map and "provider" in mode_model_map[mode]:
        provider = mode_model_map[mode]["provider"]
        logger.info(f"Using provider '{provider}' for mode '{mode}'")
        return provider

    # Default to preferred provider
    return getattr(settings, "PREFERRED_LLM_PROVIDER", "openrouter")


def _validate_openrouter_environment(settings_instance) -> None:
    """
    Validate OpenRouter environment settings.

    Args:
        settings_instance: The global settings instance

    Raises:
        ValueError: If required settings are missing
    """
    # Use the settings_instance directly
    if not hasattr(settings_instance, "OPENROUTER_API_KEY") or not settings_instance.OPENROUTER_API_KEY:
        raise ValueError("OpenRouter API key not configured. Please set OPENROUTER_API_KEY in your environment.")


def _validate_portkey_environment(settings_instance) -> None:
    """
    Validate Portkey environment settings.

    Args:
        settings_instance: The global settings instance

    Raises:
        ValueError: If required settings are missing
    """
    # Use the settings_instance directly
    if not hasattr(settings_instance, "PORTKEY_API_KEY") or not settings_instance.PORTKEY_API_KEY:
        raise ValueError("Portkey API key not configured. Please set PORTKEY_API_KEY in your environment.")


# Global provider registry - this will be managed through the unified registry now
_llm_providers: Dict[str, LLMProvider] = {}


def register_llm_provider(provider: LLMProvider) -> LLMProvider:
    """
    Register an LLM provider with both the global registry and the unified registry.

    Args:
        provider: Provider to register

    Returns:
        The registered provider (for chaining)
    """
    # Use the global registry to store providers

    # Register with legacy registry
    _llm_providers[provider.provider_name] = provider

    # Also register with unified registry
    register(provider)

    logger.info(f"Registered LLM provider: {provider.provider_name}")
    return provider


def get_llm_provider(provider_name: str = None) -> LLMProvider:
    """
    Get an LLM provider by name with proper error handling.

    Args:
        provider_name: Name of the provider to get. If None, will use PREFERRED_LLM_PROVIDER from settings

    Returns:
        LLM provider instance

    Raises:
        LLMProviderError: If the provider is not properly configured or registered
    """
    # Access the global settings instance directly
    # settings = get_settings() # Removed this line

    # If provider_name is not provided, use preferred provider from settings
    if provider_name is None:
        provider_name = getattr(settings, "PREFERRED_LLM_PROVIDER", "openrouter")

    # Return existing provider if already registered
    if provider_name in _llm_providers:
        return _llm_providers[provider_name]

    # Initialize OpenRouter provider if requested and not already registered
    if provider_name == "openrouter":
        # Validate environment
        try:
            _validate_openrouter_environment(settings)
        except ValueError as e:
            logger.error(f"OpenRouter environment validation failed: {str(e)}")
            raise LLMProviderAuthenticationError(str(e))

        # Get default model and other settings from the settings instance
        default_model = getattr(settings, "OPENROUTER_DEFAULT_MODEL", "openai/gpt-3.5-turbo")
        request_timeout = getattr(settings, "LLM_REQUEST_TIMEOUT", 30)
        max_retries = getattr(settings, "LLM_MAX_RETRIES", 3)
        retry_delay = getattr(settings, "LLM_RETRY_DELAY", 1.0)
        retry_max_delay = getattr(settings, "LLM_RETRY_MAX_DELAY", 60.0)  # Increased for Pro Tier

        # Get retryable error types if configured
        retryable_errors = None
        if hasattr(settings, "LLM_RETRYABLE_ERRORS"):
            retryable_errors = set(settings.LLM_RETRYABLE_ERRORS.split(","))

        # Create configuration
        config = LLMProviderConfig(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            default_model=default_model,
            request_timeout=request_timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            retry_max_delay=retry_max_delay,
            retryable_errors=retryable_errors,
        )

        try:
            # Get custom headers for OpenRouter Pro Tier
            # Assuming settings instance has get_openrouter_headers method
            custom_headers = settings.get_openrouter_headers()

            # Create provider with custom headers
            provider = OpenRouterProvider(config, headers=custom_headers)

            # Initialize the provider
            provider.initialize()

            # Register provider with both registries
            register_llm_provider(provider)

            return provider
        except Exception as e:
            logger.error(f"Failed to initialize OpenRouter provider: {str(e)}", exc_info=True)
            raise LLMProviderError(f"Failed to initialize provider: {str(e)}")

    # Initialize Portkey provider if requested
    elif provider_name == "portkey":
        # Validate environment
        try:
            _validate_portkey_environment(settings)
        except ValueError as e:
            logger.error(f"Portkey environment validation failed: {str(e)}")
            raise LLMProviderAuthenticationError(str(e))

        # Get default model and other settings from the settings instance
        default_model = getattr(
            settings, "OPENROUTER_DEFAULT_MODEL", "gpt-4o"
        )  # Use the same default model setting as OpenRouter
        request_timeout = getattr(settings, "LLM_REQUEST_TIMEOUT", 30)
        max_retries = getattr(settings, "LLM_MAX_RETRIES", 3)
        retry_delay = getattr(settings, "LLM_RETRY_DELAY", 1.0)
        retry_max_delay = getattr(settings, "LLM_RETRY_MAX_DELAY", 10.0)

        # Get retryable error types if configured
        retryable_errors = None
        if hasattr(settings, "LLM_RETRYABLE_ERRORS"):
            retryable_errors = set(settings.LLM_RETRYABLE_ERRORS.split(","))

        # Create configuration
        config = LLMProviderConfig(
            api_key=settings.PORTKEY_API_KEY,
            base_url="",  # Portkey manages base URLs internally
            default_model=default_model,
            request_timeout=request_timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            retry_max_delay=retry_max_delay,
            retryable_errors=retryable_errors,
        )

        try:
            # Create provider
            provider = PortkeyProvider(config)

            # Initialize the provider
            provider.initialize()

            # Register provider with both registries
            register_llm_provider(provider)

            return provider
        except Exception as e:
            logger.error(f"Failed to initialize Portkey provider: {str(e)}", exc_info=True)
            raise LLMProviderError(f"Failed to initialize provider: {str(e)}")

    # Raise error if provider not found
    raise LLMProviderError(f"LLM provider '{provider_name}' not registered and no factory available")


def initialize_llm_providers() -> None:
    """
    Initialize LLM providers during application startup.

    This function is called during application initialization to
    set up and register default LLM providers.
    """
    try:
        # Access the global settings instance directly
        # settings = get_settings() # Removed this line
        preferred_provider = getattr(settings, "PREFERRED_LLM_PROVIDER", "openrouter")

        # Initialize the preferred provider first (usually openrouter or portkey)
        get_llm_provider(preferred_provider)
        logger.info(f"Initialized preferred LLM provider: {preferred_provider}")

        # Also initialize Portkey provider if configured and not already loaded
        if preferred_provider != "portkey" and hasattr(settings, "PORTKEY_API_KEY") and settings.PORTKEY_API_KEY:
            try:
                get_llm_provider("portkey")
                logger.info("Portkey provider initialized as fallback")
            except Exception as e:
                logger.warning(f"Failed to initialize Portkey provider: {str(e)}")

        # Also initialize OpenRouter if not already loaded and key is available
        if (
            preferred_provider != "openrouter"
            and hasattr(settings, "OPENROUTER_API_KEY")
            and settings.OPENROUTER_API_KEY
        ):
            try:
                get_llm_provider("openrouter")
                logger.info("OpenRouter provider initialized as fallback")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenRouter provider: {str(e)}")

        logger.info("LLM providers initialization completed")
    except Exception as e:
        # Log but don't fail startup - LLM features will be degraded but system can still function
        logger.warning(f"Failed to initialize default LLM providers: {str(e)}")
