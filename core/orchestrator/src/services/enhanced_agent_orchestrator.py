"""
"""
    """
    """
        """Initialize the enhanced agent orchestrator."""
        """
        """
        session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
        interaction_id = f"interaction_{uuid.uuid4().hex}"
        context = context or {}

        try:


            pass
            # Get enhanced persona
            enhanced_persona = self._enhanced_persona_manager.get_enhanced_persona(persona_id)
            logger.info(f"Using persona {enhanced_persona.name} for interaction {interaction_id}")

            # Create base persona for agent context
            base_persona = PersonaConfig(
                name=enhanced_persona.name,
                background=enhanced_persona.background,
                interaction_style=enhanced_persona.interaction_style,
                traits=enhanced_persona.traits,
            )

            # Store user message in memory
            user_memory_item = MemoryItem(
                user_id=user_id,
                session_id=session_id,
                item_type="conversation",
                persona_active=enhanced_persona.name,
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
                persona=base_persona,
            )

            # Generate response
            agent_response = await self._execute_agent(
                user_input=user_input,
                user_id=user_id,
                persona=base_persona,
                enhanced_persona=enhanced_persona,
                session_id=session_id,
                interaction_id=interaction_id,
                relevant_context=relevant_context,
                context=context,
            )

            # Apply persona template to format the response
            formatted_response = enhanced_persona.format_response(agent_response.text)

            # Store agent response in memory
            response_memory_item = MemoryItem(
                user_id=user_id,
                session_id=session_id,
                item_type="conversation",
                persona_active=enhanced_persona.name,
                text_content=formatted_response,
                metadata={
                    "source": "system",
                    "interaction_id": interaction_id,
                    "confidence": agent_response.confidence,
                    "raw_response": agent_response.text,
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
                persona_name=enhanced_persona.name,
                user_memory_id=user_memory_id,
                response_memory_id=response_memory_id,
            )

            # Prepare and return response
            return {
                "message": formatted_response,
                "persona_id": persona_id or "default",
                "persona_name": enhanced_persona.name,
                "session_id": session_id,
                "interaction_id": interaction_id,
                "timestamp": datetime.utcnow(),
                "conversation_context": {
                    "relevant_items_count": len(relevant_context),
                    "confidence": agent_response.confidence,
                    "template_applied": enhanced_persona.prompt_template,
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
                persona_id=persona_id,
            )
            raise

    async def _execute_agent(
        self,
        user_input: str,
        user_id: str,
        persona: PersonaConfig,
        enhanced_persona,
        session_id: str,
        interaction_id: str,
        relevant_context: List[MemoryItem],
        context: Dict[str, Any],
    ) -> AgentResponse:
        """
        """
        timeout_seconds = getattr(settings, "AGENT_TIMEOUT_SECONDS", 30)
        use_preferred_agents = getattr(settings, "PREFERRED_AGENTS_ENABLED", True)

        # Get simplified agent registry
        agent_registry = get_simplified_agent_registry()
        agent = None
        agent_type = None

        # Select appropriate agent
        try:

            pass
            preferred_agent_type = enhanced_persona.preferred_agent_type if use_preferred_agents else None

            if preferred_agent_type:
                # Use preferred agent type if specified and enabled
                agent = agent_registry.get_agent(preferred_agent_type)
                agent_type = preferred_agent_type
                logger.info(f"Using preferred agent type '{preferred_agent_type}' for persona {persona.name}")
            else:
                # Otherwise, select based on capability
                agent = agent_registry.select_agent_for_context(agent_context)
                agent_type = agent.__class__.__name__

            logger.info(f"Selected agent type: {agent_type} for interaction {interaction_id}")
        except Exception:

            pass
            logger.error(f"Error selecting agent: {e}", exc_info=True)
            # Fall back to simple text agent
            agent_type = "simple_text"
            try:

                pass
                agent = agent_registry.get_agent(agent_type)
                logger.warning(f"Falling back to {agent_type} for interaction {interaction_id}")
            except Exception:

                pass
                logger.critical(
                    f"Critical failure - even fallback agent unavailable: {e2}",
                    exc_info=True,
                )
                # Emergency response when no agents are available
                return AgentResponse(
                    text="I apologize, but our service is experiencing difficulties at the moment. Please try again later.",
                    confidence=0.1,
                    metadata={"critical_error": True, "error": str(e2)},
                )

        # Execute the agent with timeout
        try:

            pass
            start_time = time.time()

            # Create a task with timeout
            try:

                pass
                response_task = asyncio.create_task(agent.process(agent_context))
                response = await asyncio.wait_for(response_task, timeout=timeout_seconds)
            except Exception:

                pass
                logger.warning(f"Agent processing timed out after {timeout_seconds}s for interaction {interaction_id}")
                # Generate a timeout response
                return AgentResponse(
                    text=f"I need a bit more time to think about this. As {persona.name}, I want to give you a thoughtful response.",
                    confidence=0.2,
                    metadata={
                        "timeout": True,
                        "agent_type": agent_type,
                        "timeout_seconds": timeout_seconds,
                    },
                )

            process_time = int((time.time() - start_time) * 1000)  # Convert to ms

            # Add processing time to metadata
            if response.metadata is None:
                response.metadata = {}
            response.metadata["processing_time_ms"] = process_time
            response.metadata["agent_type"] = agent_type

            # Check for empty or very short responses (possible agent failure)
            if not response.text or len(response.text) < 10:
                logger.warning(f"Agent returned suspiciously short response: '{response.text}'")

                # Append warning to metadata but don't override response
                response.metadata["warning"] = "suspiciously_short_response"
                if response.confidence > 0.5:  # Lower confidence for short responses
                    response.confidence = 0.5

            logger.info(f"Agent {agent_type} processed interaction {interaction_id} in {process_time}ms")
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
                metadata={"error": str(e), "fallback": True, "agent_type": agent_type},
            )

# Global enhanced agent orchestrator instance
_enhanced_agent_orchestrator = None

def get_enhanced_agent_orchestrator() -> EnhancedAgentOrchestrator:
    """
    """