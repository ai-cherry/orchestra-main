"""
OpenRouter LLM client implementation.

This module provides a client for OpenRouter's API using their OpenAI SDK compatibility layer.
"""

from typing import Dict, List, Any, Optional
import logging
import time
import asyncio
from datetime import datetime

try:
    from openai import OpenAI, APITimeoutError, APIConnectionError, RateLimitError
except ImportError:
    logging.error("OpenAI SDK not found. Please install with: pip install openai")
    raise

from core.orchestrator.src.config.settings import get_settings
from .interface import LLMClient

# Configure logging
logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 3
RETRY_DELAY_BASE = 1.0  # Base delay in seconds before retrying


class OpenRouterException(Exception):
    """Base exception for OpenRouter client errors."""

    pass


class OpenRouterClient(LLMClient):
    """
    OpenRouter client using the OpenAI SDK compatibility layer.

    This client leverages OpenRouter's API which provides access to multiple
    LLM providers through a unified interface compatible with OpenAI's SDK.

    Features:
    - Automatic retries for transient errors
    - User-friendly error messages
    - Monitoring for API health
    """

    def __init__(self):
        """
        Initialize the OpenRouter client.

        Raises:
            OpenRouterException: If the OpenRouter API key is not found in settings
        """
        settings = get_settings()
        self.api_key = settings.OPENROUTER_API_KEY

        if not self.api_key:
            error_msg = (
                "OpenRouter API key not found in environment variables or .env file"
            )
            logger.error(error_msg)
            raise OpenRouterException(
                f"{error_msg}. Please add OPENROUTER_API_KEY to your environment "
                "variables or .env file. You can get a key from https://openrouter.ai."
            )

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
            timeout=30.0,  # Default timeout in seconds
        )

        # Set default headers for API requests
        self.extra_headers = {
            "HTTP-Referer": getattr(settings, "SITE_URL", "http://localhost"),
            "X-Title": getattr(settings, "SITE_TITLE", "Orchestra-Main Development"),
        }

        # Track health status
        self.last_error_time = None
        self.error_count = 0
        self.max_errors_before_unhealthy = 5

        logger.info("OpenRouter client initialized")

    async def generate_response(
        self, model: str, messages: List[Dict[str, str]], **kwargs
    ) -> str:
        """
        Generate a response from the specified LLM based on the provided messages.

        Args:
            model: The model identifier to use for generation
            messages: A list of message dictionaries in the ChatML format
                     (each with 'role' and 'content' keys)
            **kwargs: Additional model-specific parameters (e.g., temperature, max_tokens)

        Returns:
            The generated text response from the LLM

        Raises:
            OpenRouterException: If there's an unrecoverable error communicating with OpenRouter
        """
        logger.debug(f"Generating response with model: {model}")

        # Set default retry parameters
        retries_left = MAX_RETRIES
        retry_delay = RETRY_DELAY_BASE
        last_exception = None

        while retries_left > 0:
            try:
                # Create the completion using the OpenAI-compatible API
                completion = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    extra_headers=self.extra_headers,
                    **kwargs,  # Pass through temperature, max_tokens, etc.
                )

                # Extract and return the response text
                if completion.choices and completion.choices[0].message:
                    # Reset error tracking on successful completion
                    self.error_count = 0
                    self.last_error_time = None

                    logger.debug("Successfully received response from OpenRouter")
                    return completion.choices[0].message.content or ""
                else:
                    error_msg = f"Received invalid response format from OpenRouter"
                    logger.error(f"{error_msg}. Completion: {completion}")
                    # Record error for health tracking
                    self._track_error()
                    return self._user_friendly_error(
                        "The AI system received an incomplete response. Please try again. "
                        "If this problem persists, contact support."
                    )

            except APITimeoutError:
                logger.warning(
                    f"Request to OpenRouter timed out (retries left: {retries_left-1})"
                )
                retries_left -= 1
                last_exception = "timeout"
                # Record error for health tracking
                self._track_error()
                # Add jitter to retry delay
                await asyncio.sleep(
                    retry_delay * (0.9 + 0.2 * (hash(str(time.time())) % 10) / 10)
                )
                retry_delay *= 1.5  # Exponential backoff

            except APIConnectionError as e:
                logger.warning(
                    f"Could not connect to OpenRouter: {e} (retries left: {retries_left-1})"
                )
                retries_left -= 1
                last_exception = "connection"
                # Record error for health tracking
                self._track_error()
                # Add jitter to retry delay
                await asyncio.sleep(
                    retry_delay * (0.9 + 0.2 * (hash(str(time.time())) % 10) / 10)
                )
                retry_delay *= 1.5  # Exponential backoff

            except RateLimitError:
                logger.error("OpenRouter rate limit exceeded")
                # This is not a transient error - don't retry
                retries_left = 0
                last_exception = "rate_limit"
                # Record error for health tracking
                self._track_error()

            except Exception as e:
                logger.error(
                    f"An unexpected error occurred communicating with OpenRouter: {e}"
                )
                retries_left -= 1
                last_exception = "unknown"
                # Record error for health tracking
                self._track_error()
                # Add jitter to retry delay
                await asyncio.sleep(
                    retry_delay * (0.9 + 0.2 * (hash(str(time.time())) % 10) / 10)
                )
                retry_delay *= 1.5  # Exponential backoff

        # If we've exhausted retries, return a user-friendly error message
        if last_exception == "timeout":
            return self._user_friendly_error(
                "The AI system is taking longer than expected to respond. "
                "Please try again in a moment."
            )
        elif last_exception == "connection":
            return self._user_friendly_error(
                "Cannot connect to the AI system at the moment. "
                "Please check your internet connection and try again."
            )
        elif last_exception == "rate_limit":
            return self._user_friendly_error(
                "The AI system is currently receiving too many requests. "
                "Please try again in a few minutes."
            )
        else:
            return self._user_friendly_error(
                "The AI system encountered an unexpected error. "
                "Please try again. If the problem persists, contact support."
            )

    def _track_error(self):
        """Track errors for health monitoring."""
        self.error_count += 1
        self.last_error_time = datetime.utcnow()

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
        Check the health of the OpenRouter client.

        Returns:
            Dict with health status
        """
        health_info = {
            "status": "healthy",
            "api_key_configured": bool(self.api_key),
            "error_count": self.error_count,
            "last_error": (
                self.last_error_time.isoformat() if self.last_error_time else None
            ),
        }

        # Check if we've seen too many errors recently
        if self.error_count >= self.max_errors_before_unhealthy:
            health_info["status"] = "degraded"

        return health_info
