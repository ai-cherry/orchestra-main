"""
Agent Orchestration Service for AI Orchestration System.

This module provides coordination of multiple AI agents, managing their
interactions, selection, and communication based on personas and context.
"""

import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.orchestrator.src.agents.agent_base import AgentResponse
from core.orchestrator.src.agents.enhanced_agent_registry import get_enhanced_agent_registry, select_agent_for_context

# Import the settings instance directly
from core.orchestrator.src.personas.dependency import get_persona_manager
from core.orchestrator.src.services.base_orchestrator import BaseOrchestrator
from packages.shared.src.models.base_models import MemoryItem, PersonaConfig

# Configure logging
logger = logging.getLogger(__name__)


class AgentOrchestrator(BaseOrchestrator):
    """
    Orchestrates interactions between different AI agents and components.

    This class is responsible for:
    1. Coordinating the flow of information between components
    2. Managing the execution of AI agent tasks
    3. Handling fallbacks and error recovery
    4. Ensuring appropriate agent selection based on context
    """

    def __init__(self):
        """Initialize the agent orchestrator."""
        super().__init__()
        self._persona_manager = get_persona_manager()

    async def process_interaction(
        self,
        user_input: str,
        user_id: str,
        session_id: Optional[str] = None,
        persona_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a user interaction and generate a response.

        This method orchestrates the complete interaction flow:
        1. Select appropriate persona
        2. Record user input in memory
        3. Retrieve relevant context from memory
        4. Generate response using appropriate agent(s)
        5. Record response in memory
        6. Return formatted response with metadata

        Args:
            user_input: The user's input message
            user_id: The ID of the user
            session_id: Optional session ID for conversation continuity
            persona_id: Optional ID of persona to use
            context: Additional context for the interaction

        Returns:
            Dict containing the response and metadata

        Raises:
            ValueError: If required parameters are invalid
            RuntimeError: If processing fails
        """
        # Generate IDs if not provided
        session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
        interaction_id = f"interaction_{uuid.uuid4().hex}"
        context = context or {}

        try:
            # Select persona
            persona = self._persona_manager.get_persona(persona_id)
            logger.info(f"Using persona {persona.name} for interaction {interaction_id}")

            # Store user message in memory
            user_memory_item = MemoryItem(
                user_id=user_id,
                session_id=session_id,
                item_type="conversation",
                persona_active=persona.name,
                text_content=user_input,
                metadata={
                    "source": "user",
                    "interaction_id": interaction_id,
                    **context,
                },
            )

            user_memory_id = await self._add_memory_async(user_memory_item)

            # Retrieve relevant context from memory
            relevant_context = await self._retrieve_context(
                user_id=user_id,
                session_id=session_id,
                current_input=user_input,
                persona=persona,
            )

            # Generate response
            agent_response = await self._execute_agent(
                user_input=user_input,
                user_id=user_id,
                persona=persona,
                session_id=session_id,
                interaction_id=interaction_id,
                relevant_context=relevant_context,
                context=context,
            )

            # Store agent response in memory
            response_memory_item = MemoryItem(
                user_id=user_id,
                session_id=session_id,
                item_type="conversation",
                persona_active=persona.name,
                text_content=agent_response.text,
                metadata={
                    "source": "system",
                    "interaction_id": interaction_id,
                    "confidence": agent_response.confidence,
                    **agent_response.metadata,
                    **context,
                },
            )

            response_memory_id = await self._add_memory_async(response_memory_item)

            # Publish interaction complete event
            self._publish_interaction_complete(
                user_id=user_id,
                session_id=session_id,
                interaction_id=interaction_id,
                persona_name=persona.name,
                user_memory_id=user_memory_id,
                response_memory_id=response_memory_id,
            )

            # Prepare and return response
            return {
                "message": agent_response.text,
                "persona_id": persona_id or "default",
                "persona_name": persona.name,
                "session_id": session_id,
                "interaction_id": interaction_id,
                "timestamp": datetime.utcnow(),
                "conversation_context": {
                    "relevant_items_count": len(relevant_context),
                    "confidence": agent_response.confidence,
                    **agent_response.metadata,
                },
            }
        except Exception as e:
            logger.error(f"Error processing interaction: {e}", exc_info=True)
            # Publish interaction error event
            self._publish_interaction_error(
                user_id=user_id,
                session_id=session_id,
                interaction_id=interaction_id,
                error=str(e),
            )
            raise

    async def _execute_agent(
        self,
        user_input: str,
        user_id: str,
        persona: PersonaConfig,
        session_id: str,
        interaction_id: str,
        relevant_context: List[MemoryItem],
        context: Dict[str, Any],
    ) -> AgentResponse:
        """
        Execute the appropriate agent based on the selected persona and context.

        This method:
        1. Creates an agent context with all relevant information
        2. Selects the most appropriate agent for the interaction
        3. Executes the agent to generate a response
        4. Handles any agent-specific processing

        Args:
            user_input: The user's input message
            user_id: The ID of the user
            persona: The selected persona
            session_id: The session ID
            interaction_id: The unique interaction ID
            relevant_context: Relevant context from memory
            context: Additional context for the interaction

        Returns:
            The agent response
        """
        # Create agent context using the base method
        agent_context = self._create_agent_context(
            user_input=user_input,
            user_id=user_id,
            persona=persona,
            session_id=session_id,
            interaction_id=interaction_id,
            relevant_context=relevant_context,
            context=context,
        )

        # Get enhanced agent registry
        agent_registry = get_enhanced_agent_registry()

        # Select appropriate agent
        try:
            # For persona-specific agent selection, we could use:
            # agent_type = persona.preferred_agent_type
            # agent = agent_registry.get_agent(agent_type)

            # For context-based selection using enhanced registry:
            agent = select_agent_for_context(agent_context)

            logger.info(f"Selected agent type: {agent.__class__.__name__} for interaction {interaction_id}")
        except Exception as e:
            logger.error(f"Error selecting agent: {e}")
            # Fall back to SimpleTextAgent
            agent = agent_registry.get_agent("simple_text")
            logger.warning(f"Falling back to SimpleTextAgent for interaction {interaction_id}")

        # Execute the agent
        try:
            start_time = time.time()
            response = await agent.process(agent_context)
            process_time = int((time.time() - start_time) * 1000)  # Convert to ms

            # Add processing time to metadata
            if response.metadata is None:
                response.metadata = {}
            response.metadata["processing_time_ms"] = process_time

            logger.info(f"Agent {agent.__class__.__name__} processed interaction {interaction_id} in {process_time}ms")
            return response
        except Exception as e:
            logger.error(f"Agent processing failed: {e}", exc_info=True)
            # Create a fallback response
            fallback_msg = (
                f"I'm having trouble processing your request at the moment. "
                f"As {persona.name}, I'd like to help, but I need a moment to gather my thoughts."
            )
            return AgentResponse(
                text=fallback_msg,
                confidence=0.3,
                metadata={
                    "error": str(e),
                    "fallback": True,
                    "agent_type": agent.__class__.__name__,
                },
            )


# Global agent orchestrator instance
_agent_orchestrator = None


def get_agent_orchestrator() -> AgentOrchestrator:
    """
    Get the global agent orchestrator instance.

    This function provides a simple dependency injection mechanism
    for accessing the agent orchestrator throughout the application.

    Returns:
        The global AgentOrchestrator instance
    """
    global _agent_orchestrator

    if _agent_orchestrator is None:
        _agent_orchestrator = AgentOrchestrator()

    return _agent_orchestrator
