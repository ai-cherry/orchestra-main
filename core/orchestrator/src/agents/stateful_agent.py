"""
"""
    """
    """
        """
        """
        """
        """
        """
        """
        """
        """
        """
        """
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.updated_at = datetime.utcnow()

class StatefulAgent(Agent):
    """
    """
        """
        """
        self._state_ttl = config.get("state_ttl", 3600) if config else 3600  # 1 hour default

    def get_state(self, context: AgentContext) -> AgentState:
        """
        """
        """
        """
        """
        """
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

    async def recall(self, context: AgentContext, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        """
                    "id": memory.id,
                    "text": memory.text_content,
                    "metadata": memory.metadata,
                    "timestamp": (memory.timestamp.isoformat() if memory.timestamp else None),
                }
            )

        return results

    async def recall_conversation(self, context: AgentContext, limit: int = 10) -> List[Dict[str, Any]]:
        """
        """
                    "id": memory.id,
                    "text": memory.text_content,
                    "role": ("user" if memory.metadata.get("source") == "user" else "assistant"),
                    "timestamp": (memory.timestamp.isoformat() if memory.timestamp else None),
                }
            )

        # Sort by timestamp (oldest first)
        results.sort(key=lambda x: x.get("timestamp", ""))

        return results

    async def process_with_state(self, context: AgentContext) -> Tuple[AgentResponse, AgentState]:
        """
        """
        """
        """
        """
        """

class ConversationalAgent(StatefulAgent):
    """
    """
        """
        """
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
