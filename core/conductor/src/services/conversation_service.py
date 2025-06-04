"""
"""
    """
    """
    """
    """
        """Initialize the conversation service."""
        logger.info("ConversationService initialized")

    async def start_conversation(self, user_id: str, persona_name: Optional[str] = None) -> str:
        """
        """
            item_type="conversation_event",
            content={
                "event_type": "conversation_started",
                "persona_name": persona_name,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        try:


            pass
            # Directly await the async method
            await self._memory_manager.add_memory_item(conversation_start)
        except Exception:

            pass
            logger.error(f"Failed to store conversation start: {e}")

        # Track active conversation
        self._active_conversations[user_id] = ConversationState(
            user_id=user_id,
            session_id=session_id,
            persona_active=persona_name,
            start_time=datetime.utcnow(),
            turn_count=0,
        )

        # Publish event using async method
        try:

            pass
            await self._event_bus.publish_async(
                "conversation_started",
                {
                    "user_id": user_id,
                    "session_id": session_id,
                    "persona_name": persona_name,
                },
            )
        except Exception:

            pass
            logger.warning(f"Failed to publish conversation_started event: {e}")
            # Non-critical, continue execution

        return session_id

    async def end_conversation(self, user_id: str, session_id: Optional[str] = None) -> bool:
        """
        """
            logger.warning(f"No active conversation found for user: {user_id}")
            return False

        # Check if specific session_id matches
        if session_id and conversation.session_id != session_id:
            logger.warning(f"Session ID mismatch for user {user_id}")
            return False

        # Store conversation end in memory
        conversation_end = MemoryItem(
            user_id=user_id,
            item_type="conversation_event",
            content={
                "event_type": "conversation_ended",
                "persona_name": conversation.persona_active,
                "session_id": conversation.session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "duration_seconds": (datetime.utcnow() - conversation.start_time).total_seconds(),
                "turn_count": conversation.turn_count,
                "success_status": True,  # Added field to indicate normal conversation end
            },
        )

        try:


            pass
            # Directly await the async method
            await self._memory_manager.add_memory_item(conversation_end)
        except Exception:

            pass
            logger.error(
                f"Failed to store conversation end for user {user_id}, session {conversation.session_id}: {str(e)}",
                exc_info=True,
            )

        # Remove from active conversations
        del self._active_conversations[user_id]

        # Publish event using async method
        try:

            pass
            await self._event_bus.publish_async(
                "conversation_ended",
                {
                    "user_id": user_id,
                    "session_id": conversation.session_id,
                    "persona_name": conversation.persona_active,
                    "turn_count": conversation.turn_count,
                },
            )
        except Exception:

            pass
            logger.warning(f"Failed to publish conversation_ended event: {e}")
            # Non-critical, continue execution

        return True

    def get_active_conversation(self, user_id: str) -> Optional[ConversationState]:
        """
        """
        """
        """
            item_type="conversation_message",
            content={
                "message": content,
                "is_user": is_user,
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": session_id,
            },
        )

        # Add metadata if provided
        if metadata:
            message_item.content["metadata"] = metadata

        # Add persona context if available
        if conversation and conversation.persona_active:
            message_item.content["persona_name"] = conversation.persona_active

        # Store in memory using async method
        try:

            pass
            # Directly await the async method
            message_id = await self._memory_manager.add_memory_item(message_item)
        except Exception:

            pass
            logger.error(f"Failed to store conversation message: {e}")
            message_id = str(uuid.uuid4())  # Generate a fallback ID

        # Update turn count if this is an active conversation
        if conversation:
            if is_user:
                conversation.turn_count += 1
            conversation.last_activity = datetime.utcnow()

        # Publish event using async method
        try:

            pass
            await self._event_bus.publish_async(
                "conversation_message_added",
                {
                    "user_id": user_id,
                    "message_id": message_id,
                    "is_user": is_user,
                    "session_id": session_id,
                },
            )
        except Exception:

            pass
            logger.warning(f"Failed to publish conversation_message_added event: {e}")
            # Non-critical, continue execution

        return message_id

    async def get_conversation_history(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 20,
        persona_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        """
            filters = {"persona_name": persona_name}

        try:


            pass
            # Directly await the async method
            raw_items = await self._memory_manager.get_conversation_history(
                user_id=user_id,
                session_id=session_id,
                limit=limit,
                filters=filters,
            )
        except Exception:

            pass
            logger.error(f"Failed to retrieve conversation history: {e}")
            raw_items = []  # Return empty list on error

        # Format the items in a conversation-friendly structure
        formatted_messages = []
        for item in raw_items:
            if item.item_type != "conversation_message":
                continue  # Skip non-message items

            message = {
                "id": item.id,
                "role": "user" if item.content.get("is_user") else "assistant",
                "content": item.content.get("message", ""),
                "timestamp": item.content.get("timestamp"),
            }

            # Add metadata if available
            if "metadata" in item.content:
                message["metadata"] = item.content["metadata"]

            formatted_messages.append(message)

        return formatted_messages

    async def add_memory_item_async(self, item: MemoryItem) -> str:
        """
        """
    """
    """