"""
"""
    """
    """
        """
        """
        """
        """
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
        """
            logger.warning("Memory manager not available, cannot search memory")
            return []

        # Search memory
        results = await self.memory_manager.search(query, limit=limit)

        # Extract items
        return [result.item for result in results]

    async def recall_conversation(self, limit: int = 10) -> List[ConversationMemoryItem]:
        """
        """
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
    """
        """
        """
            "redis_config": {
                "host": "localhost",
                "port": 6379,
                "ttl": 3600,  # 1 hour
            },
            "firestore_config": {
                "project_id": "cherry-ai-project",
                "collection": "memory",
            },
            "openai_config": {
                "project_id": "cherry-ai-project",
                "location": "us-west4",
                "index_name": "orchestra-memory-index",
            },
        }

        # Initialize memory manager (lazily)
        self._memory_manager: Optional[LayeredMemoryManager] = None

    async def initialize_async(self) -> None:
        """Initialize the registry and memory manager."""
            redis_config=self.memory_config.get("redis_config"),
            firestore_config=self.memory_config.get("firestore_config"),
            openai_config=self.memory_config.get("openai_config"),
        )
        await self._memory_manager.initialize()

    def create_context(self, text: str, conversation_id: Optional[str] = None, **kwargs) -> MemoryEnhancedAgentContext:
        """
        """
        """
        """
    """Example of using the memory-aware agent registry."""
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
