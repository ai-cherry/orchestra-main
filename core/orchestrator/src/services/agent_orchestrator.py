"""
"""
    """
    """
        """Initialize the agent orchestrator."""
        """
        """
        session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
        interaction_id = f"interaction_{uuid.uuid4().hex}"
        context = context or {}

        try:


            pass
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
        except Exception:

            pass
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
        """
            logger.info(f"Selected agent type: {agent.__class__.__name__} for interaction {interaction_id}")
        except Exception:

            pass
            logger.error(f"Error selecting agent: {e}")
            # Fall back to SimpleTextAgent
            agent = agent_registry.get_agent("simple_text")
            logger.warning(f"Falling back to SimpleTextAgent for interaction {interaction_id}")

        # Execute the agent
        try:

            pass
            start_time = time.time()
            response = await agent.process(agent_context)
            process_time = int((time.time() - start_time) * 1000)  # Convert to ms

            # Add processing time to metadata
            if response.metadata is None:
                response.metadata = {}
            response.metadata["processing_time_ms"] = process_time

            logger.info(f"Agent {agent.__class__.__name__} processed interaction {interaction_id} in {process_time}ms")
            return response
        except Exception:

            pass
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
    """