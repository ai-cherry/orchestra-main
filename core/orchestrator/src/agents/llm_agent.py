"""
LLM Agent for AI Orchestration System.

This module provides an agent implementation that uses LLM providers
to generate responses based on user input and conversation history.
The agent implements lifecycle methods for proper integration with
the unified registry and service management system.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set, Tuple

from core.orchestrator.src.agents.agent_base import Agent, AgentContext, AgentResponse
from core.orchestrator.src.services.llm.exceptions import (
    LLMProviderAuthenticationError,
    LLMProviderConnectionError,
    LLMProviderError,
    LLMProviderInvalidRequestError,
    LLMProviderModelError,
    LLMProviderRateLimitError,
    LLMProviderResourceExhaustedError,
    LLMProviderServiceError,
    LLMProviderTimeoutError,
)
from core.orchestrator.src.services.llm.providers import get_llm_provider
from core.orchestrator.src.services.unified_registry import Service
from packages.shared.src.models.base_models import MemoryItem, PersonaConfig

# Configure logging
logger = logging.getLogger(__name__)


class ConversationFormatter:
    """
    Utility for formatting conversations for LLM input.

    This class handles converting between conversation history formats
    and preparing context for LLM prompts.
    """

    @staticmethod
    def format_conversation_history(history: List[MemoryItem]) -> List[Dict[str, str]]:
        """
        Format conversation history into chat API message format.

        Args:
            history: List of memory items

        Returns:
            List of chat messages with roles and content
        """
        formatted = []

        for item in history:
            # Determine role based on source metadata
            role = "user" if item.metadata.get("source") == "user" else "assistant"

            # Add formatted message
            formatted.append({"role": role, "content": item.text_content})

        return formatted

    @staticmethod
    def create_system_message(persona: PersonaConfig) -> Dict[str, str]:
        """
        Create a system message based on persona.

        Args:
            persona: Persona configuration

        Returns:
            System message with persona instructions
        """
        # Create system prompt based on persona information
        system_content = (
            f"You are {persona.name}, with the following background: {persona.background}. "
            f"Your interaction style is: {persona.interaction_style}. "
        )

        # Add traits if available
        if persona.traits:
            traits_desc = ", ".join(f"{trait} ({value}/100)" for trait, value in persona.traits.items())
            system_content += f"Your traits are: {traits_desc}."

        return {"role": "system", "content": system_content}


class LLMAgent(Agent, Service):
    """
    Agent that uses LLM providers to generate responses.

    This agent connects to LLM providers like OpenRouter to generate
    responses based on user input and conversation history. It also
    implements Service interface methods for proper lifecycle management.
    """

    def __init__(self, provider_name: str = "openrouter"):
        """
        Initialize the LLM agent.

        Args:
            provider_name: Name of the LLM provider to use
        """
        self._provider_name = provider_name
        self._provider = None
        logger.info(f"LLMAgent initialized with provider: {provider_name}")

    def initialize(self) -> None:
        """
        Initialize the agent's resources.

        This method initializes the LLM provider. It's called during
        service initialization through the service registry.
        """
        try:
            # Get and initialize the provider
            self._provider = get_llm_provider(self._provider_name)
            logger.info(f"LLMAgent initialized provider: {self._provider_name}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM provider: {e}")
            # We'll handle lazy initialization in process() if this fails

    async def initialize_async(self) -> None:
        """
        Initialize the agent asynchronously.

        This method is called during async service initialization.
        """
        # Just use the synchronous method since provider initialization is already handled properly
        self.initialize()

    def close(self) -> None:
        """
        Release any resources held by the agent.

        This method is called during service shutdown.
        """
        # Providers are managed by the registry, no need to close them here
        self._provider = None
        logger.debug("LLMAgent resources released")

    @property
    def agent_type(self) -> str:
        """Get agent type."""
        return "llm_agent"

    @property
    def capabilities(self) -> Set[str]:
        """Get agent capabilities."""
        return {"text_generation", "conversation", "persona_aware", "code_generation"}

    def can_handle(self, context: AgentContext) -> float:
        """
        Check if this agent can handle the given context.

        Args:
            context: The context to check

        Returns:
            Confidence level between 0.0 and 1.0
        """
        # LLM agents are generally versatile and can handle most requests
        confidence = 0.7  # Base confidence level

        # Check for specific keywords or patterns that LLMs excel at
        if "generate" in context.user_input.lower() or "create" in context.user_input.lower():
            confidence += 0.1

        # Check for code-related queries
        code_indicators = [
            "code",
            "function",
            "class",
            "program",
            "script",
            "implement",
        ]
        if any(indicator in context.user_input.lower() for indicator in code_indicators):
            confidence += 0.2

        # Check for long or complex requests that benefit from LLM processing
        if len(context.user_input.split()) > 15:
            confidence += 0.1

        # Cap confidence at 1.0
        return min(confidence, 1.0)

    def _extract_llm_parameters(self, context: AgentContext) -> Tuple[Optional[str], float, Optional[int]]:
        """
        Extract LLM-specific parameters from context metadata.

        Args:
            context: Agent context with metadata

        Returns:
            Tuple of (model, temperature, max_tokens)
        """
        # Default values
        model = None
        temperature = 0.7
        max_tokens = None

        # Extract values from metadata if available
        if context.metadata:
            model = context.metadata.get("llm_model")

            if "llm_temperature" in context.metadata:
                try:
                    temp_value = float(context.metadata["llm_temperature"])
                    if 0.0 <= temp_value <= 2.0:  # Valid temperature range
                        temperature = temp_value
                except (ValueError, TypeError):
                    pass

            if "llm_max_tokens" in context.metadata:
                try:
                    token_value = int(context.metadata["llm_max_tokens"])
                    if token_value > 0:
                        max_tokens = token_value
                except (ValueError, TypeError):
                    pass

        return model, temperature, max_tokens

    async def _get_response_with_fallbacks(self, messages, model, temperature, max_tokens):
        """
        Try to get a response from multiple providers with cascading fallbacks.

        The cascade order is:
        1. OpenRouter (primary gateway)
        2. Portkey (secondary gateway)
        3. Direct provider APIs (OpenAI, Anthropic, Deepseek, Grok)
        """
        # Track providers tried for logging
        providers_tried = []
        last_error = None

        # Get provider instances - lazy loaded when needed
        providers = {
            "openrouter": None,
            "portkey": None,
            "openai": None,
            "anthropic": None,
            "deepseek": None,
            "grok": None,
        }

        # Define the cascade order
        provider_cascade = [
            "openrouter",
            "portkey",
            "openai",
            "anthropic",
            "deepseek",
            "grok",
        ]

        # Try each provider in order
        for provider_name in provider_cascade:
            try:
                # Skip if we've reached our retry limit
                if len(providers_tried) >= 3:
                    logger.warning(f"Reached maximum provider retry limit ({len(providers_tried)})")
                    break

                # Log the attempt
                providers_tried.append(provider_name)
                logger.info(f"Attempting request with provider: {provider_name}")

                # Lazy-load the provider if needed
                if providers[provider_name] is None:
                    providers[provider_name] = self._get_provider_instance(provider_name)

                provider = providers[provider_name]

                # Set appropriate timeouts based on provider
                timeout = 8.0 if provider_name == "openrouter" else 15.0

                # Attempt to get response with timeout
                result = await asyncio.wait_for(
                    provider.generate_chat_completion(
                        messages=messages,
                        model=self._get_model_for_provider(model, provider_name),
                        temperature=temperature,
                        max_tokens=max_tokens,
                    ),
                    timeout=timeout,
                )

                # Success! Return the result with provider info
                result["provider"] = provider_name
                return result

            except (LLMProviderError, asyncio.TimeoutError) as e:
                last_error = e
                logger.warning(f"Provider {provider_name} failed: {str(e)}")
                continue

        # If we've exhausted all options, raise the last error
        if last_error:
            logger.error(f"All providers failed. Last error: {str(last_error)}")
            raise last_error

        # Safety fallback - should never reach here
        raise LLMProviderError("All providers failed with unknown errors")

    def _get_provider_instance(self, provider_name):
        """Get a provider instance by name"""
        return get_llm_provider(provider_name)

    def _get_model_for_provider(self, requested_model, provider_name):
        """Map the requested model to provider-specific model identifier"""
        # Default to the requested model
        if not requested_model:
            # Use sensible defaults per provider
            defaults = {
                "openrouter": "openai/gpt-3.5-turbo",
                "portkey": "openai/gpt-3.5-turbo",
                "openai": "gpt-3.5-turbo",
                "anthropic": "claude-instant-1",
                "deepseek": "deepseek-chat",
                "grok": "grok-1",
            }
            return defaults.get(provider_name, "gpt-3.5-turbo")

        # Handle model mapping for different providers
        if provider_name == "openrouter":
            # OpenRouter uses provider/model format
            if "/" not in requested_model:
                return f"openai/{requested_model}"
            return requested_model
        elif provider_name == "portkey":
            # Similar to OpenRouter but may have different prefixes
            if "/" not in requested_model:
                return f"openai/{requested_model}"
            return requested_model
        elif provider_name == "openai":
            # Strip any prefix
            return requested_model.split("/")[-1]
        elif provider_name == "anthropic":
            # Map to Anthropic models if requested model looks like it
            if "claude" in requested_model.lower():
                return requested_model.split("/")[-1]
            return "claude-instant-1"  # Default Anthropic model
        # Similar handling for other providers

        # Fallback to a safe default
        return requested_model

    async def process(self, context: AgentContext) -> AgentResponse:
        """Process a request using our LLM provider cascade"""
        try:
            # Format conversation for the LLM
            messages = self._formatter.format_conversation(
                user_input=context.user_input,
                persona=context.persona,
                conversation_history=context.conversation_history,
                metadata=context.metadata,
            )

            # Extract parameters
            model, temperature, max_tokens = self._extract_llm_parameters(context)

            # Use our new cascade method instead of direct provider call
            result = await self._get_response_with_fallbacks(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Return agent response with high confidence
            return AgentResponse(
                text=result["content"],
                confidence=0.9,
                metadata={
                    "model": result.get("model", "unknown"),
                    "provider": result.get("provider", "cascade"),
                    "usage": result.get("usage", {}),
                    "finish_reason": result.get("finish_reason", "unknown"),
                    "response_time_ms": result.get("response_time_ms"),
                    "providers_tried": result.get("providers_tried", []),
                },
            )

        except LLMProviderAuthenticationError as e:
            logger.error(f"Authentication error with LLM provider: {e}")

            return AgentResponse(
                text=f"I'm experiencing authentication issues with my language service. Please try again later or contact support with the error: {str(e)}",
                confidence=0.2,
                metadata={
                    "error": "authentication_error",
                    "error_message": str(e),
                    "provider": self._provider_name,
                    "fallback": True,
                },
            )

        except LLMProviderConnectionError as e:
            logger.error(f"Connection error with LLM provider: {e}")

            return AgentResponse(
                text=f"I'm having trouble connecting to my language service. This might be due to network issues. As {context.persona.name}, I'd like to help, but need a moment for the connection to be restored.",
                confidence=0.2,
                metadata={
                    "error": "connection_error",
                    "error_message": str(e),
                    "provider": self._provider_name,
                    "fallback": True,
                },
            )

        except LLMProviderRateLimitError as e:
            logger.warning(f"Rate limit exceeded for LLM provider: {e}")

            return AgentResponse(
                text=f"I'm currently experiencing high demand and have reached my rate limit. As {context.persona.name}, I appreciate your patience. Please try again in a moment.",
                confidence=0.3,
                metadata={
                    "error": "rate_limit_error",
                    "error_message": str(e),
                    "provider": self._provider_name,
                    "fallback": True,
                },
            )

        except LLMProviderInvalidRequestError as e:
            logger.error(f"Invalid request to LLM provider: {e}")

            return AgentResponse(
                text=f"I encountered an issue with your request format. As {context.persona.name}, I'd like to help, but I need a properly formatted request.",
                confidence=0.3,
                metadata={
                    "error": "invalid_request_error",
                    "error_message": str(e),
                    "provider": self._provider_name,
                    "fallback": True,
                },
            )

        except LLMProviderTimeoutError as e:
            logger.warning(f"Request to LLM provider timed out: {e}")

            return AgentResponse(
                text=f"I need a bit more time to think about this. As {context.persona.name}, I want to give you a thoughtful response, but my language service is taking longer than expected. Please try again in a moment.",
                confidence=0.3,
                metadata={
                    "error": "timeout_error",
                    "error_message": str(e),
                    "provider": self._provider_name,
                    "fallback": True,
                },
            )

        except LLMProviderModelError as e:
            logger.error(f"Model error with LLM provider: {e}")

            # If a specific model was requested, mention it in the error
            model_mention = f" with the requested model {model}" if model else ""

            return AgentResponse(
                text=f"I'm having difficulty{model_mention}. As {context.persona.name}, I'd like to suggest trying again with a different approach or model.",
                confidence=0.3,
                metadata={
                    "error": "model_error",
                    "error_message": str(e),
                    "provider": self._provider_name,
                    "fallback": True,
                    "requested_model": model,
                },
            )

        except LLMProviderResourceExhaustedError as e:
            logger.warning(f"Resource exhausted error with LLM provider: {e}")

            return AgentResponse(
                text=f"I've used up my available resources for now. As {context.persona.name}, I appreciate your understanding. The system will reset shortly, please try again in a moment.",
                confidence=0.3,
                metadata={
                    "error": "resource_exhausted_error",
                    "error_message": str(e),
                    "provider": self._provider_name,
                    "fallback": True,
                },
            )

        except (LLMProviderServiceError, LLMProviderError) as e:
            logger.error(f"Service error or unexpected error with LLM provider: {e}")

            return AgentResponse(
                text=f"I'm sorry, but I encountered an issue while processing your request. As {context.persona.name}, I'd like to help, but I need a moment for my service to recover.",
                confidence=0.2,
                metadata={
                    "error": ("service_error" if isinstance(e, LLMProviderServiceError) else "unexpected_error"),
                    "error_message": str(e),
                    "provider": self._provider_name,
                    "fallback": True,
                },
            )

        except Exception as e:
            logger.error(f"Unhandled error in LLM agent: {str(e)}", exc_info=True)

            return AgentResponse(
                text=f"I apologize, but something unexpected happened. As {context.persona.name}, I'd like to help, but I need a moment to gather my thoughts.",
                confidence=0.1,  # Very low confidence for unhandled errors
                metadata={
                    "error": "unhandled_error",
                    "error_message": str(e),
                    "provider": self._provider_name,
                    "fallback": True,
                },
            )

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using the LLM provider.

        This is a convenience method for direct text generation
        without the full Agent context.

        Args:
            prompt: Text prompt
            **kwargs: Additional parameters for the provider

        Returns:
            Generated text

        Raises:
            LLMProviderError: If generation fails
        """
        # Ensure provider is initialized or get a new instance
        if self._provider is None:
            self._provider = get_llm_provider(self._provider_name)

        # Generate completion
        result = await self._provider.generate_completion(prompt=prompt, **kwargs)

        return result["content"]
