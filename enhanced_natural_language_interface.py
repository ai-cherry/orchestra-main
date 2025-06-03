#!/usr/bin/env python3
"""
"""
    """Different conversation modes for context-aware responses."""
    CASUAL = "casual"
    ANALYTICAL = "analytical"
    TECHNICAL = "technical"
    STRATEGIC = "strategic"
    CREATIVE = "creative"

@dataclass
class ConversationMessage:
    """Individual conversation message with metadata."""
    """Complete conversation session with context."""
    """Classifies user intents from natural language input."""
        "search_memory": [
            r"what.*about",
            r"tell me.*about",
            r"find.*information",
            r"search.*for",
            r"look.*up",
            r"remember.*when",
            r"recall.*about",
        ],
        "analyze_data": [
            r"analyze.*",
            r"what.*trends",
            r"compare.*",
            r"summary.*of",
            r"insights.*about",
            r"performance.*of",
        ],
        "ask_question": [r"how.*", r"why.*", r"what.*is", r"explain.*", r"help.*with"],
        "schedule_action": [
            r"schedule.*",
            r"remind.*me",
            r"set.*up",
            r"create.*meeting",
        ],
        "data_sync": [r"sync.*data", r"update.*from", r"pull.*latest", r"refresh.*"],
    }

    def classify_intent(self, text: str) -> Optional[str]:
        """Classify the intent of user input."""
        return "general_query"

class ContextualResponseGenerator:
    """Generates context-aware responses using multiple AI models."""
        self.gemini = generative_models.GenerativeModel("gemini-1.5-pro")
        self.portkey = portkey.Client(api_key=portkey_api_key, config={"virtual_key": "vertex-agent-special"})

        # Model routing based on query type
        self.model_routing = {
            "analytical": "gemini-pro",
            "technical": "claude-3-sonnet",
            "creative": "gpt-4",
            "strategic": "gemini-pro",
            "casual": "gpt-3.5-turbo",
        }

    async def generate_response(
        self,
        query: str,
        context: ConversationContext,
        mode: ConversationMode = ConversationMode.CASUAL,
        intent: Optional[str] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate a contextual response with metadata."""
        model = self.model_routing.get(mode.value, "gemini-pro")

        try:


            pass
            # Try primary model
            response = await self._generate_with_model(enhanced_prompt, model)

            # Extract metadata from response
            metadata = await self._extract_response_metadata(response, context)

            return response, metadata

        except Exception:


            pass
            logger.warning(f"Primary model failed, falling back to Gemini: {e}")

            # Fallback to Gemini
            try:

                pass
                response = self.gemini.generate_content(enhanced_prompt).text
                metadata = {
                    "model": "gemini-fallback",
                    "timestamp": datetime.utcnow().isoformat(),
                }
                return response, metadata
            except Exception:

                pass
                logger.error(f"All models failed: {fallback_error}")
                return (
                    "I'm having trouble processing your request right now. Please try again.",
                    {},
                )

    async def _build_enhanced_prompt(
        self,
        query: str,
        context: ConversationContext,
        mode: ConversationMode,
        intent: Optional[str],
    ) -> str:
        """Build an enhanced prompt with rich context."""
            "You are an advanced AI assistant with access to comprehensive business data and context.",
            f"Current conversation mode: {mode.value}",
            f"User query intent: {intent or 'general'}",
            "",
            "RELEVANT CONTEXT FROM MEMORY:",
            context.aggregated_context,
            "",
            "RECENT CONVERSATION HISTORY:",
        ]

        # Add recent conversation messages
        for msg in context.conversation_history[-5:]:  # Last 5 messages
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:200]  # Truncate long messages
            prompt_parts.append(f"{role.upper()}: {content}")

        prompt_parts.extend(
            [
                "",
                "DATA SOURCE SUMMARY:",
            ]
        )

        # Add data source summary
        source_summary = self._generate_source_summary(context.active_memories)
        prompt_parts.append(source_summary)

        prompt_parts.extend(
            [
                "",
                f"USER QUERY: {query}",
                "",
                "Please provide a comprehensive, contextual response that:",
                "1. Directly addresses the user's query",
                "2. Incorporates relevant information from the available context",
                "3. Maintains conversation continuity",
                "4. Suggests follow-up actions when appropriate",
                f"5. Matches the {mode.value} conversation style",
            ]
        )

        return "\n".join(prompt_parts)

    def _generate_source_summary(self, memories: List[ContextualMemory]) -> str:
        """Generate a summary of available data sources."""
            return "No specific data sources available."

        summary_parts = []
        for source, count in source_counts.items():
            summary_parts.append(f"- {source.upper()}: {count} relevant items")

        return "\n".join(summary_parts)

    async def _generate_with_model(self, prompt: str, model: str) -> str:
        """Generate response using specified model via Portkey."""
                        "role": "system",
                        "content": "You are an expert AI assistant with access to comprehensive business data.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
            )
            return response.choices[0].message.content

        except Exception:


            pass
            logger.error(f"Portkey generation failed with model {model}: {e}")
            raise

    async def _extract_response_metadata(self, response: str, context: ConversationContext) -> Dict[str, Any]:
        """Extract metadata from the generated response."""
            "timestamp": datetime.utcnow().isoformat(),
            "context_memories_used": len(context.active_memories),
            "sources_referenced": list(set(m.source for m in context.active_memories)),
            "response_length": len(response),
            "conversation_length": len(context.conversation_history),
        }

        # Analyze response for action items
        action_indicators = [
            "should",
            "recommend",
            "suggest",
            "next step",
            "follow up",
            "schedule",
            "contact",
        ]

        response_lower = response.lower()
        suggested_actions = [action for action in action_indicators if action in response_lower]

        if suggested_actions:
            metadata["suggested_actions"] = suggested_actions

        return metadata

class EnhancedNaturalLanguageInterface:
    """
    """
        """Start a new conversation session or resume existing one."""
            conversation_id = f"conv_{user_id}_{int(datetime.utcnow().timestamp())}"

        # Get conversation context from memory system
        context = await self.memory_system.get_conversation_context(
            user_id=user_id, conversation_id=conversation_id, query=initial_query
        )

        # Create conversation session
        session = ConversationSession(
            id=conversation_id,
            user_id=user_id,
            title=None,
            mode=mode,
            messages=[],
            context=context,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Store in active sessions
        self.active_sessions[conversation_id] = session

        # Process initial query if provided
        if initial_query:
            await self.process_message(conversation_id, initial_query)

        return session

    async def process_message(
        self, conversation_id: str, message: str, user_id: Optional[str] = None
    ) -> ConversationMessage:
        """Process a user message and generate a response."""
            raise ValueError(f"No active session found for conversation {conversation_id}")

        # Classify intent
        intent = self.intent_classifier.classify_intent(message)

        # Create user message
        user_message = ConversationMessage(
            id=f"msg_{len(session.messages) + 1}",
            user_id=session.user_id,
            conversation_id=conversation_id,
            content=message,
            role="user",
            timestamp=datetime.utcnow(),
            intent=intent,
        )

        session.messages.append(user_message)

        # Handle specific intents
        if intent == "data_sync":
            return await self._handle_data_sync(session, message)
        elif intent == "search_memory":
            return await self._handle_memory_search(session, message)
        elif intent == "analyze_data":
            return await self._handle_data_analysis(session, message)
        else:
            return await self._handle_general_query(session, message)

    async def _handle_data_sync(self, session: ConversationSession, message: str) -> ConversationMessage:
        """Handle data synchronization requests."""
        for source in ["gong", "salesforce", "hubspot", "slack", "looker"]:
            if source in message.lower():
                sources_mentioned.append(source)

        if not sources_mentioned:
            sources_mentioned = ["all"]

        # Trigger data sync
        if "all" in sources_mentioned:
            sync_results = await self.data_orchestrator.sync_all_sources()
        else:
            sync_results = {}
            for source in sources_mentioned:
                if source in self.data_orchestrator.integrations:
                    count = await self.data_orchestrator.integrations[source].sync_data()
                    sync_results[source] = count

        # Generate response
        response_content = "Data synchronization completed:\n"
        for source, count in sync_results.items():
            if count >= 0:
                response_content += f"- {source.upper()}: {count} items synchronized\n"
            else:
                response_content += f"- {source.upper()}: Synchronization failed\n"

        response_message = ConversationMessage(
            id=f"msg_{len(session.messages) + 1}",
            user_id=session.user_id,
            conversation_id=session.id,
            content=response_content,
            role="assistant",
            timestamp=datetime.utcnow(),
            metadata={"sync_results": sync_results},
        )

        session.messages.append(response_message)
        session.updated_at = datetime.utcnow()

        return response_message

    async def _handle_memory_search(self, session: ConversationSession, message: str) -> ConversationMessage:
        """Handle memory search requests."""
        if "gong" in message.lower():
            sources = ["gong"]
        elif "salesforce" in message.lower():
            sources = ["salesforce"]
        elif "hubspot" in message.lower():
            sources = ["hubspot"]
        elif "slack" in message.lower():
            sources = ["slack"]
        elif "looker" in message.lower():
            sources = ["looker"]

        # Search memory
        memories = await self.memory_system.semantic_search(
            user_id=session.user_id, query=message, sources=sources, top_k=10
        )

        # Generate response
        if memories:
            response_content = f"Found {len(memories)} relevant items:\n\n"
            for i, memory in enumerate(memories[:5], 1):
                response_content += f"{i}. From {memory.source.upper()}: {memory.content[:200]}...\n"
                response_content += f"   Relevance: {memory.relevance_score:.2f}\n\n"
        else:
            response_content = "No relevant information found in memory. Try rephrasing your query or check if data has been synchronized recently."

        response_message = ConversationMessage(
            id=f"msg_{len(session.messages) + 1}",
            user_id=session.user_id,
            conversation_id=session.id,
            content=response_content,
            role="assistant",
            timestamp=datetime.utcnow(),
            metadata={"memories_found": len(memories)},
        )

        session.messages.append(response_message)
        session.updated_at = datetime.utcnow()

        return response_message

    async def _handle_data_analysis(self, session: ConversationSession, message: str) -> ConversationMessage:
        """Handle data analysis requests."""
            intent="analyze_data",
        )

        response_message = ConversationMessage(
            id=f"msg_{len(session.messages) + 1}",
            user_id=session.user_id,
            conversation_id=session.id,
            content=response_content,
            role="assistant",
            timestamp=datetime.utcnow(),
            metadata=metadata,
        )

        session.messages.append(response_message)
        session.updated_at = datetime.utcnow()

        return response_message

    async def _handle_general_query(self, session: ConversationSession, message: str) -> ConversationMessage:
        """Handle general queries with full context."""
            id=f"msg_{len(session.messages) + 1}",
            user_id=session.user_id,
            conversation_id=session.id,
            content=response_content,
            role="assistant",
            timestamp=datetime.utcnow(),
            metadata=metadata,
        )

        session.messages.append(response_message)
        session.updated_at = datetime.utcnow()

        return response_message

    async def get_conversation_history(
        self, conversation_id: str, limit: Optional[int] = None
    ) -> List[ConversationMessage]:
        """Get conversation history."""
        """End and clean up a conversation session."""
                conversation_summary = f"Conversation Summary: {len(session.messages)} messages exchanged"

                await self.memory_system.add_memory(
                    user_id=session.user_id,
                    content=conversation_summary,
                    source="conversation",
                    source_metadata={
                        "conversation_id": conversation_id,
                        "message_count": len(session.messages),
                        "duration": (session.updated_at - session.created_at).total_seconds(),
                        "mode": session.mode.value,
                    },
                    context_tags=["conversation", "summary"],
                )

            # Remove from active sessions
            del self.active_sessions[conversation_id]

    def get_active_conversations(self, user_id: str) -> List[ConversationSession]:
        """Get all active conversations for a user."""