"""
Stateful Agent Implementation for AI Orchestration System.

This module provides an agent implementation that maintains state between
interactions, using Pydantic models for structured state management.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from core.orchestrator.src.agents.agent_base import Agent, AgentContext, AgentResponse
from core.orchestrator.src.agents.memory.layered_memory import get_memory_manager

# Configure logging
logger = logging.getLogger(__name__)


class AgentState(BaseModel):
    """
    Structured state for agents using Pydantic.

    This class provides a structured way to store and manage agent state,
    including conversation context, memory references, and tool results.
    """

    conversation_id: str
    user_id: str
    current_step: int = 0
    memory_keys: List[str] = Field(default_factory=list)
    context_variables: Dict[str, Any] = Field(default_factory=dict)
    last_tool_results: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def update(self, **kwargs) -> None:
        """
        Update state with new values.

        Args:
            **kwargs: Values to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        # Update timestamp
        self.updated_at = datetime.utcnow()

    def increment_step(self) -> int:
        """
        Increment the current step counter.

        Returns:
            The new step count
        """
        self.current_step += 1
        self.updated_at = datetime.utcnow()
        return self.current_step

    def add_memory_key(self, key: str) -> None:
        """
        Add a memory key to the state.

        Args:
            key: The memory key to add
        """
        if key not in self.memory_keys:
            self.memory_keys.append(key)
            self.updated_at = datetime.utcnow()

    def add_context_variable(self, key: str, value: Any) -> None:
        """
        Add a context variable to the state.

        Args:
            key: The variable name
            value: The variable value
        """
        self.context_variables[key] = value
        self.updated_at = datetime.utcnow()

    def add_tool_result(self, tool_name: str, result: Any) -> None:
        """
        Add a tool result to the state.

        Args:
            tool_name: The name of the tool
            result: The result of the tool execution
        """
        self.last_tool_results[tool_name] = {
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.updated_at = datetime.utcnow()


class StatefulAgent(Agent):
    """
    Agent that maintains state between interactions.

    This class extends the base Agent class with state management capabilities,
    allowing agents to maintain context and memory between interactions.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a stateful agent.

        Args:
            config: Optional configuration for the agent
        """
        super().__init__(config)
        self.states: Dict[str, AgentState] = {}
        self._state_ttl = (
            config.get("state_ttl", 3600) if config else 3600
        )  # 1 hour default

    def get_state(self, context: AgentContext) -> AgentState:
        """
        Get or create state for this conversation.

        Args:
            context: The context for this interaction

        Returns:
            The agent state for this conversation
        """
        conversation_id = context.session_id or str(uuid.uuid4())

        if conversation_id not in self.states:
            self.states[conversation_id] = AgentState(
                conversation_id=conversation_id, user_id=context.user_id
            )

        return self.states[conversation_id]

    async def update_state(self, context: AgentContext, **updates) -> None:
        """
        Update the agent state with new values.

        Args:
            context: The context for this interaction
            **updates: Values to update
        """
        state = self.get_state(context)
        state.update(**updates)

    async def remember(
        self,
        context: AgentContext,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Remember something in the agent's memory.

        This method stores a memory item and adds its key to the agent's state.

        Args:
            context: The context for this interaction
            text: The text to remember
            metadata: Optional metadata for the memory

        Returns:
            The ID of the stored memory
        """
        state = self.get_state(context)

        # Prepare metadata
        full_metadata = {
            "user_id": context.user_id,
            "conversation_id": state.conversation_id,
            "step": state.current_step,
            **(metadata or {}),
        }

        # Store in memory
        memory_manager = await get_memory_manager()
        memory_id = await memory_manager.remember_conversation(
            text=text,
            user_id=context.user_id,
            conversation_id=state.conversation_id,
            metadata=full_metadata,
        )

        # Add to state
        state.add_memory_key(memory_id)

        return memory_id

    async def recall(
        self, context: AgentContext, query: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Recall relevant memories.

        This method retrieves memories relevant to the given query.

        Args:
            context: The context for this interaction
            query: The query to search for
            limit: Maximum number of memories to return

        Returns:
            A list of relevant memories
        """
        # Get memory manager
        memory_manager = await get_memory_manager()

        # Recall relevant memories
        memories = await memory_manager.recall_relevant(query, limit=limit)

        # Convert to simplified format
        results = []
        for memory in memories:
            results.append(
                {
                    "id": memory.id,
                    "text": memory.text_content,
                    "metadata": memory.metadata,
                    "timestamp": (
                        memory.timestamp.isoformat() if memory.timestamp else None
                    ),
                }
            )

        return results

    async def recall_conversation(
        self, context: AgentContext, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Recall conversation history.

        This method retrieves the conversation history for the current session.

        Args:
            context: The context for this interaction
            limit: Maximum number of messages to return

        Returns:
            A list of conversation messages
        """
        state = self.get_state(context)

        # Get memory manager
        memory_manager = await get_memory_manager()

        # Get conversation history
        memories = await memory_manager.get_conversation_history(
            conversation_id=state.conversation_id, limit=limit
        )

        # Convert to simplified format
        results = []
        for memory in memories:
            results.append(
                {
                    "id": memory.id,
                    "text": memory.text_content,
                    "role": (
                        "user"
                        if memory.metadata.get("source") == "user"
                        else "assistant"
                    ),
                    "timestamp": (
                        memory.timestamp.isoformat() if memory.timestamp else None
                    ),
                }
            )

        # Sort by timestamp (oldest first)
        results.sort(key=lambda x: x.get("timestamp", ""))

        return results

    async def process_with_state(
        self, context: AgentContext
    ) -> Tuple[AgentResponse, AgentState]:
        """
        Process user input with state management.

        This method should be implemented by subclasses to provide the actual
        processing logic with access to the agent's state.

        Args:
            context: The context for this interaction

        Returns:
            A tuple of (response, state)
        """
        # Get state
        state = self.get_state(context)

        # Increment step counter
        state.increment_step()

        # Default implementation just calls the regular process method
        response = await self.process(context)

        return response, state

    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Process user input and generate a response.

        This method overrides the base Agent.process method to add state
        management. Subclasses should override process_with_state instead.

        Args:
            context: The context for this interaction

        Returns:
            The agent's response
        """
        # Process with state
        response, state = await self.process_with_state(context)

        # Clean up old states
        self._cleanup_old_states()

        return response

    def _cleanup_old_states(self) -> None:
        """
        Clean up old states based on TTL.

        This method removes states that have not been updated recently,
        to prevent memory leaks.
        """
        now = datetime.utcnow()
        expired_keys = []

        for key, state in self.states.items():
            # Calculate age in seconds
            age = (now - state.updated_at).total_seconds()

            # Mark for removal if expired
            if age > self._state_ttl:
                expired_keys.append(key)

        # Remove expired states
        for key in expired_keys:
            del self.states[key]

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired states")


class ConversationalAgent(StatefulAgent):
    """
    Agent specialized in maintaining conversational context.

    This class extends StatefulAgent with additional capabilities for
    managing conversational context, including message history tracking
    and context-aware responses.
    """

    async def process_with_state(
        self, context: AgentContext
    ) -> Tuple[AgentResponse, AgentState]:
        """
        Process user input with conversational context.

        This method demonstrates how to use the state to maintain
        conversational context.

        Args:
            context: The context for this interaction

        Returns:
            A tuple of (response, state)
        """
        # Get state
        state = self.get_state(context)

        # Increment step counter
        state.increment_step()

        # Remember user message
        await self.remember(
            context=context,
            text=context.user_input,
            metadata={"source": "user", "step": state.current_step},
        )

        # Get conversation history
        history = await self.recall_conversation(context, limit=10)

        # Add conversation history to context metadata
        if context.metadata is None:
            context.metadata = {}
        context.metadata["conversation_history"] = history

        # Generate response (subclasses should override this)
        response_text = f"I'm a conversational agent. You said: {context.user_input}"
        response = AgentResponse(
            text=response_text,
            confidence=0.8,
            metadata={"state": state.dict(), "step": state.current_step},
        )

        # Remember agent response
        await self.remember(
            context=context,
            text=response.text,
            metadata={"source": "agent", "step": state.current_step},
        )

        return response, state
