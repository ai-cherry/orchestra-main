"""
"""
    """
    """
        """
        """

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
        """
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
        """
                formatted_history.append({"role": "assistant", "content": item.text_content})
            else:
                formatted_history.append({"role": "user", "content": item.text_content})

        return formatted_history
