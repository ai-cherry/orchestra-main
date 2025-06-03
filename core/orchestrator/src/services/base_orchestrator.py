"""
"""
    """
    """
        """Initialize common orchestrator components."""
        self._event_bus.subscribe("persona_selected", self._on_persona_selected)

        logger.info(f"{self.__class__.__name__} initialized")

    def initialize(self) -> None:
        """Initialize the orchestrator resources."""
        """Close the orchestrator and release resources."""
        self._event_bus.unsubscribe("persona_selected", self._on_persona_selected)

        # Subclasses can override to add specific cleanup

    def _on_persona_selected(self, event_data: Dict[str, Any]) -> None:
        """
        """
        persona_name = event_data.get("name", "unknown")
        user_id = event_data.get("user_id", "unknown")

        logger.info(f"Persona selected for user {user_id}: {persona_name}")

    @abstractmethod
    async def process_interaction(
        self,
        user_input: str,
        user_id: str,
        session_id: Optional[str] = None,
        persona_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        """
        """
        """
        if hasattr(self._memory_service, "add_memory_item_async"):
            return await self._memory_service.add_memory_item_async(item)

        # Fall back to synchronous add in executor
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._memory_service.add_memory_item, item)

    async def _retrieve_context(
        self, user_id: str, session_id: str, current_input: str, persona: PersonaConfig
    ) -> List[MemoryItem]:
        """
        """
        history_limit = getattr(settings, "CONVERSATION_HISTORY_LIMIT", 10)

        # Use async version if available to avoid blocking
        if hasattr(self._memory_service, "get_conversation_history_async"):
            conversation_history = await self._memory_service.get_conversation_history_async(
                user_id=user_id, session_id=session_id, limit=history_limit
            )
        else:
            # Fall back to synchronous version in a thread pool
            loop = asyncio.get_running_loop()
            conversation_history = await loop.run_in_executor(
                None,
                lambda: self._memory_service.get_conversation_history(
                    user_id=user_id, session_id=session_id, limit=history_limit
                ),
            )

        # In a real implementation, we would:
        # 1. Generate an embedding for the current input
        # 2. Perform semantic search
        # 3. Merge and deduplicate results

        # For now, we'll just return the conversation history
        return conversation_history

    def _create_agent_context(
        self,
        user_input: str,
        user_id: str,
        persona: PersonaConfig,
        session_id: str,
        interaction_id: str,
        relevant_context: List[MemoryItem],
        context: Dict[str, Any],
        max_context_items: int = 20,
    ) -> AgentContext:
        """
        """
        """
        """
            "interaction_complete",
            {
                "user_id": user_id,
                "session_id": session_id,
                "interaction_id": interaction_id,
                "persona_name": persona_name,
                "user_memory_id": user_memory_id,
                "response_memory_id": response_memory_id,
            },
        )

    def _publish_interaction_error(
        self,
        user_id: str,
        session_id: str,
        interaction_id: str,
        error: str,
        persona_id: Optional[str] = None,
    ) -> None:
        """
        """
            "user_id": user_id,
            "session_id": session_id,
            "interaction_id": interaction_id,
            "error": error,
        }

        if persona_id:
            event_data["persona_id"] = persona_id

        self._event_bus.publish("interaction_error", event_data)
