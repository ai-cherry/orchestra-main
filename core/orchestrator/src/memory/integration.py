"""
Memory Integration for AI Orchestra.

This module demonstrates how to integrate the layered memory system with the agent registry.
"""

import logging
from typing import Any, Dict, List, Optional

from core.orchestrator.src.agents.memory.models import (
    ConversationMemoryItem,
    MemoryItem,
    MemoryType,
)
from core.orchestrator.src.agents.unified_agent_registry import (
    AgentContext,
    AgentRegistry,
)
from core.orchestrator.src.memory.layered_memory import LayeredMemoryManager

logger = logging.getLogger(__name__)


class MemoryEnhancedAgentContext(AgentContext):
    """
    Enhanced agent context with memory access.

    This class extends the standard AgentContext with methods to access
    the memory system, allowing agents to store and retrieve information
    across different memory types.
    """

    def __init__(
        self,
        text: str,
        memory_manager: Optional[LayeredMemoryManager] = None,
        conversation_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize memory-enhanced agent context.

        Args:
            text: The input text for the agent
            memory_manager: The memory manager instance
            conversation_id: Optional conversation ID for context
            **kwargs: Additional context parameters
        """
        super().__init__(text=text, **kwargs)
        self.memory_manager = memory_manager
        self.conversation_id = conversation_id
        self.memory_items: List[MemoryItem] = []

    async def remember(self, content: Any, memory_type: MemoryType = MemoryType.MID_TERM, **kwargs) -> str:
        """
        Store information in memory.

        Args:
            content: The content to store
            memory_type: The type of memory to use
            **kwargs: Additional metadata for the memory item

        Returns:
            The ID of the stored memory item
        """
        if not self.memory_manager:
            logger.warning("Memory manager not available, cannot store memory")
            return ""

        # Create appropriate memory item
        if self.conversation_id:
            item = ConversationMemoryItem(
                content=content,
                memory_type=memory_type,
                conversation_id=self.conversation_id,
                role=kwargs.get("role", "assistant"),
                metadata=kwargs,
            )
        else:
            item = MemoryItem(
                content=content,
                memory_type=memory_type,
                metadata=kwargs,
            )

        # Store in memory
        item_id = await self.memory_manager.store(item)

        # Track memory items created in this context
        self.memory_items.append(item)

        return item_id

    async def recall(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """
        Search memory for relevant information.

        Args:
            query: The search query
            limit: Maximum number of results to return

        Returns:
            List of memory items matching the query
        """
        if not self.memory_manager:
            logger.warning("Memory manager not available, cannot search memory")
            return []

        # Search memory
        results = await self.memory_manager.search(query, limit=limit)

        # Extract items
        return [result.item for result in results]

    async def recall_conversation(self, limit: int = 10) -> List[ConversationMemoryItem]:
        """
        Retrieve recent conversation history.

        Args:
            limit: Maximum number of messages to retrieve

        Returns:
            List of conversation memory items
        """
        if not self.memory_manager or not self.conversation_id:
            logger.warning("Memory manager or conversation ID not available")
            return []

        # Search for conversation history
        results = await self.memory_manager.search(
            f"conversation_id:{self.conversation_id}",
            memory_types=[MemoryType.SHORT_TERM, MemoryType.MID_TERM],
            limit=limit,
        )

        # Extract and filter items
        conversation_items = []
        for result in results:
            if isinstance(result.item, ConversationMemoryItem):
                conversation_items.append(result.item)

        # Sort by creation time
        conversation_items.sort(key=lambda x: x.created_at)

        return conversation_items


class MemoryAwareAgentRegistry(AgentRegistry):
    """
    Agent registry with integrated memory system.

    This class extends the standard AgentRegistry with memory capabilities,
    allowing agents to access and manipulate the memory system.
    """

    def __init__(self, memory_config: Optional[Dict[str, Any]] = None):
        """
        Initialize memory-aware agent registry.

        Args:
            memory_config: Configuration for the memory system
        """
        super().__init__()

        # Default memory configuration
        self.memory_config = memory_config or {
            "redis_config": {
                "host": "localhost",
                "port": 6379,
                "ttl": 3600,  # 1 hour
            },
            "firestore_config": {
                "project_id": "cherry-ai-project",
                "collection": "memory",
            },
            "vertex_ai_config": {
                "project_id": "cherry-ai-project",
                "location": "us-west4",
                "index_name": "orchestra-memory-index",
            },
        }

        # Initialize memory manager (lazily)
        self._memory_manager: Optional[LayeredMemoryManager] = None

    async def initialize_async(self) -> None:
        """Initialize the registry and memory manager."""
        # Initialize registry
        await super().initialize_async()

        # Initialize memory manager
        self._memory_manager = LayeredMemoryManager(
            redis_config=self.memory_config.get("redis_config"),
            firestore_config=self.memory_config.get("firestore_config"),
            vertex_ai_config=self.memory_config.get("vertex_ai_config"),
        )
        await self._memory_manager.initialize()

    def create_context(self, text: str, conversation_id: Optional[str] = None, **kwargs) -> MemoryEnhancedAgentContext:
        """
        Create a memory-enhanced agent context.

        Args:
            text: The input text for the agent
            conversation_id: Optional conversation ID for context
            **kwargs: Additional context parameters

        Returns:
            A memory-enhanced agent context
        """
        return MemoryEnhancedAgentContext(
            text=text,
            memory_manager=self._memory_manager,
            conversation_id=conversation_id,
            **kwargs,
        )

    async def select_agent_for_context(self, context: AgentContext) -> Any:
        """
        Select the most appropriate agent for a context.

        This override enhances the context with memory capabilities
        before passing it to the selected agent.

        Args:
            context: The context to select an agent for

        Returns:
            The selected agent
        """
        # Convert to memory-enhanced context if needed
        if not isinstance(context, MemoryEnhancedAgentContext) and self._memory_manager:
            enhanced_context = MemoryEnhancedAgentContext(
                text=context.text,
                memory_manager=self._memory_manager,
                metadata=context.metadata,
            )
            context = enhanced_context

        # Select agent using standard logic
        return await super().select_agent_for_context(context)


# Example usage
async def example_usage():
    """Example of using the memory-aware agent registry."""
    # Create memory-aware registry
    registry = MemoryAwareAgentRegistry()
    await registry.initialize_async()

    # Create context with conversation ID
    context = registry.create_context(
        text="Hello, I'm looking for information about AI Orchestra.",
        conversation_id="user123",
    )

    # Store user message in memory
    await context.remember(
        content="Hello, I'm looking for information about AI Orchestra.",
        memory_type=MemoryType.SHORT_TERM,
        role="user",
    )

    # Select agent for context
    agent = await registry.select_agent_for_context(context)

    # Process with selected agent
    response = await agent.process(context)

    # Store agent response in memory
    await context.remember(
        content=response.text,
        memory_type=MemoryType.SHORT_TERM,
        role="assistant",
    )

    # Retrieve conversation history
    conversation = await context.recall_conversation()
    print(f"Conversation history: {len(conversation)} messages")

    return response
