"""
LiteLLM Client for AI Orchestra
Provides a unified interface for accessing multiple LLM providers.
"""

import logging
import os
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import litellm
from pydantic import BaseModel, Field

from core.orchestrator.src.config.loader import get_settings

logger = logging.getLogger(__name__)


class ModelProvider(str, Enum):
    """Supported model providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE_OPENAI = "azure_openai"
    VERTEX_AI = "vertex_ai"


class ModelType(str, Enum):
    """Types of models."""

    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"


class LLMMessage(BaseModel):
    """A message for LLM interaction."""

    role: str
    content: str
    name: Optional[str] = None


class LLMResponse(BaseModel):
    """Response from an LLM."""

    model: str
    content: str
    usage: Dict[str, int] = Field(default_factory=dict)
    finish_reason: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class LLMEmbeddingResponse(BaseModel):
    """Response from an embedding model."""

    model: str
    embedding: List[float]
    usage: Dict[str, int] = Field(default_factory=dict)
    raw_response: Optional[Dict[str, Any]] = None


class LiteLLMClient:
    """
    Client for interacting with various LLM providers through LiteLLM.

    This client provides a unified interface for:
    - Chat completions
    - Text completions
    - Embeddings

    It supports multiple providers including OpenAI, Anthropic, Google, and Azure.
    """

    def __init__(
        self,
        default_model: Optional[str] = None,
        default_embedding_model: Optional[str] = None,
        api_key_openai: Optional[str] = None,
        api_key_anthropic: Optional[str] = None,
        api_key_google: Optional[str] = None,
        api_key_azure: Optional[str] = None,
        api_base_azure: Optional[str] = None,
        vertex_project: Optional[str] = None,
        vertex_location: Optional[str] = None,
    ):
        """Initialize the LiteLLM client."""
        # Load settings
        settings = get_settings()

        # Set API keys from parameters or environment variables
        self.api_keys = {
            ModelProvider.OPENAI: api_key_openai or os.environ.get("OPENAI_API_KEY"),
            ModelProvider.ANTHROPIC: api_key_anthropic
            or os.environ.get("ANTHROPIC_API_KEY"),
            ModelProvider.GOOGLE: api_key_google or os.environ.get("GEMINI_API_KEY"),
            ModelProvider.AZURE_OPENAI: api_key_azure
            or os.environ.get("AZURE_OPENAI_API_KEY"),
        }

        # Set Azure API base
        self.api_base_azure = api_base_azure or os.environ.get("AZURE_OPENAI_API_BASE")

        # Set Vertex AI project and location
        self.vertex_project = vertex_project or settings.gcp_project_id
        self.vertex_location = vertex_location or settings.gcp_region

        # Set default models
        self.default_model = default_model or "gpt-3.5-turbo"
        self.default_embedding_model = (
            default_embedding_model or "text-embedding-ada-002"
        )

        # Configure LiteLLM
        self._configure_litellm()

    def _configure_litellm(self):
        """Configure LiteLLM with API keys and settings."""
        # Set API keys
        for provider, api_key in self.api_keys.items():
            if api_key:
                if provider == ModelProvider.OPENAI:
                    litellm.openai_api_key = api_key
                elif provider == ModelProvider.ANTHROPIC:
                    litellm.anthropic_api_key = api_key
                elif provider == ModelProvider.GOOGLE:
                    os.environ["GOOGLE_API_KEY"] = api_key
                elif provider == ModelProvider.AZURE_OPENAI:
                    litellm.azure_api_key = api_key
                    if self.api_base_azure:
                        litellm.azure_api_base = self.api_base_azure

        # Configure Vertex AI if project and location are provided
        if self.vertex_project and self.vertex_location:
            os.environ["VERTEX_PROJECT"] = self.vertex_project
            os.environ["VERTEX_LOCATION"] = self.vertex_location

        # Set up logging
        litellm.set_verbose = True

    async def chat_completion(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[Union[str, List[str]]] = None,
        user: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> LLMResponse:
        """
        Generate a chat completion using the specified model.

        Args:
            messages: List of messages in the conversation
            model: Model to use (defaults to self.default_model)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum number of tokens to generate
            top_p: Nucleus sampling parameter
            frequency_penalty: Frequency penalty parameter
            presence_penalty: Presence penalty parameter
            stop: Stop sequences
            user: User identifier
            timeout: Request timeout in seconds

        Returns:
            LLMResponse object containing the model's response
        """
        model = model or self.default_model

        # Convert messages to LiteLLM format
        litellm_messages = [
            {
                "role": msg.role,
                "content": msg.content,
                **({"name": msg.name} if msg.name else {}),
            }
            for msg in messages
        ]

        try:
            response = await litellm.acompletion(
                model=model,
                messages=litellm_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                stop=stop,
                user=user,
                timeout=timeout,
            )

            # Extract content from response
            content = response.choices[0].message.content

            # Extract usage information
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

            return LLMResponse(
                model=model,
                content=content,
                usage=usage,
                finish_reason=response.choices[0].finish_reason,
                raw_response=(
                    response.model_dump()
                    if hasattr(response, "model_dump")
                    else response.dict()
                ),
            )

        except Exception as e:
            logger.error(f"Error in chat completion: {str(e)}")
            raise

    async def text_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[Union[str, List[str]]] = None,
        user: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> LLMResponse:
        """
        Generate a text completion using the specified model.

        Args:
            prompt: Text prompt
            model: Model to use (defaults to self.default_model)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum number of tokens to generate
            top_p: Nucleus sampling parameter
            frequency_penalty: Frequency penalty parameter
            presence_penalty: Presence penalty parameter
            stop: Stop sequences
            user: User identifier
            timeout: Request timeout in seconds

        Returns:
            LLMResponse object containing the model's response
        """
        # For text completion, we'll use the chat completion API with a single user message
        messages = [LLMMessage(role="user", content=prompt)]
        return await self.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            stop=stop,
            user=user,
            timeout=timeout,
        )

    async def get_embedding(
        self,
        text: str,
        model: Optional[str] = None,
        user: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> LLMEmbeddingResponse:
        """
        Generate an embedding for the given text.

        Args:
            text: Text to embed
            model: Model to use (defaults to self.default_embedding_model)
            user: User identifier
            timeout: Request timeout in seconds

        Returns:
            LLMEmbeddingResponse object containing the embedding
        """
        model = model or self.default_embedding_model

        try:
            response = await litellm.aembedding(
                model=model,
                input=text,
                user=user,
                timeout=timeout,
            )

            # Extract embedding from response
            embedding = response.data[0].embedding

            # Extract usage information
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "total_tokens": response.usage.total_tokens,
            }

            return LLMEmbeddingResponse(
                model=model,
                embedding=embedding,
                usage=usage,
                raw_response=(
                    response.model_dump()
                    if hasattr(response, "model_dump")
                    else response.dict()
                ),
            )

        except Exception as e:
            logger.error(f"Error in embedding: {str(e)}")
            raise

    def get_available_models(self) -> Dict[ModelType, List[str]]:
        """
        Get a list of available models grouped by type.

        Returns:
            Dictionary mapping model types to lists of model names
        """
        # This is a simplified implementation
        # In a real implementation, you would query the providers for available models
        return {
            ModelType.CHAT: [
                "gpt-3.5-turbo",
                "gpt-4",
                "gpt-4-turbo",
                "claude-3-opus",
                "claude-3-sonnet",
                "claude-3-haiku",
                "gemini-pro",
                "gemini-1.5-pro",
                "vertex-ai/gemini-pro",
                "vertex-ai/gemini-1.5-pro",
            ],
            ModelType.COMPLETION: [
                "gpt-3.5-turbo-instruct",
                "text-davinci-003",
            ],
            ModelType.EMBEDDING: [
                "text-embedding-ada-002",
                "text-embedding-3-small",
                "text-embedding-3-large",
                "vertex-ai/textembedding-gecko",
            ],
        }

    def get_token_limit(self, model: str) -> int:
        """
        Get the token limit for a specific model.

        Args:
            model: Model name

        Returns:
            Token limit as an integer
        """
        # This is a simplified implementation with common models
        # In a real implementation, you would use litellm.get_model_info
        token_limits = {
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384,
            "gpt-4": 8192,
            "gpt-4-32k": 32768,
            "gpt-4-turbo": 128000,
            "claude-3-opus": 200000,
            "claude-3-sonnet": 180000,
            "claude-3-haiku": 150000,
            "gemini-pro": 32768,
            "gemini-1.5-pro": 1000000,
            "vertex-ai/gemini-pro": 32768,
            "vertex-ai/gemini-1.5-pro": 1000000,
            "text-embedding-ada-002": 8191,
            "text-embedding-3-small": 8191,
            "text-embedding-3-large": 8191,
        }

        return token_limits.get(model, 4096)  # Default to 4096 if model not found
