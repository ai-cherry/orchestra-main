"""
Interaction Service for AI Orchestration System.

This module provides a service for handling user interactions,
following the hexagonal architecture pattern by separating business logic
from infrastructure concerns.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from packages.shared.src.llm_client.interface import LLMClient
from packages.shared.src.memory.services.memory_service import MemoryService
from packages.shared.src.models.base_models import MemoryItem, PersonaConfig

# Configure logging
logger = logging.getLogger(__name__)


class InteractionService:
    """
    Service for handling user interactions.

    This class encapsulates the business logic for processing user interactions,
    following the hexagonal architecture pattern by depending on abstractions
    rather than concrete implementations.
    """

    def __init__(
        self,
        memory_service: MemoryService,
        llm_client: LLMClient,
        default_model: str,
    ):
        """
        Initialize the interaction service.

        Args:
            memory_service: Memory service for storing and retrieving conversation history
            llm_client: LLM client for generating responses
            default_model: Default LLM model to use
        """
        self._memory = memory_service
        self._llm_client = llm_client
        self._default_model = default_model
        logger.debug("InteractionService initialized")

    async def process_interaction(
        self,
        user_id: str,
        user_message: str,
        persona_config: PersonaConfig,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        history_limit: int = 10,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Tuple[str, str]:
        """
        Process a user interaction.

        This method handles the business logic of processing a user interaction,
        including retrieving conversation history, calling the LLM, and storing
        the response.

        Args:
            user_id: The ID of the user
            user_message: The user's message
            persona_config: The active persona configuration
            session_id: Optional session ID
            request_id: Optional request ID for tracing
            history_limit: Maximum number of history items to retrieve
            temperature: Temperature for LLM sampling
            max_tokens: Maximum tokens for LLM response

        Returns:
            Tuple of (response text, persona name)

        Raises:
            Exception: If processing fails
        """
        # Log the interaction
        logger.info(f"Processing interaction with persona: {persona_config.name} for user: {user_id}")

        # Get conversation history using our memory service
        history_items = await self._memory.get_conversation_history_async(
            user_id=user_id,
            session_id=session_id,
            limit=history_limit,
            persona_name=persona_config.name,
        )

        # Format history for LLM
        # This is a business rule: how to format conversation history for the LLM
        formatted_history = self._format_history_for_llm(history_items, persona_config.name)

        # Construct system prompt using persona_config
        system_message = {
            "role": "system",
            "content": f"You are {persona_config.name}. {persona_config.description}",
        }

        # Add current user message
        user_message_dict = {"role": "user", "content": user_message}

        # Combine messages
        messages = [system_message] + formatted_history + [user_message_dict]

        # Call LLM
        llm_response_text = await self._llm_client.generate_response(
            model=self._default_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            user_id=user_id,
            active_persona_name=persona_config.name,
        )

        # Create memory item for the response
        memory_item = MemoryItem(
            user_id=user_id,
            session_id=session_id,
            item_type="conversation",
            persona_active=persona_config.name,
            text_content=llm_response_text,
            timestamp=datetime.utcnow(),
            metadata={
                "source": "llm",
                "model": self._default_model,  # Store the actual model used
                "request_id": request_id,
            },
        )

        # Also create a memory item for the user message to maintain complete history
        user_memory_item = MemoryItem(
            user_id=user_id,
            session_id=session_id,
            item_type="conversation",
            persona_active="user",  # Distinguishing user messages
            text_content=user_message,
            timestamp=datetime.utcnow(),
            metadata={"source": "user", "request_id": request_id},
        )

        # Save to memory
        await self._memory.add_memory_item_async(user_memory_item)
        await self._memory.add_memory_item_async(memory_item)

        # Return response and persona
        return llm_response_text, persona_config.name

    def _format_history_for_llm(self, history_items: List[MemoryItem], persona_name: str) -> List[Dict[str, str]]:
        """
        Format conversation history for the LLM.

        Args:
            history_items: List of history items to format
            persona_name: Name of the active persona

        Returns:
            Formatted history for the LLM
        """
        formatted_history = []

        # Process items in order (oldest to newest)
        for item in reversed(history_items):
            if item.persona_active == persona_name:
                formatted_history.append({"role": "assistant", "content": item.text_content})
            else:
                formatted_history.append({"role": "user", "content": item.text_content})

        return formatted_history
