#!/usr/bin/env python3
"""
Enhanced Natural Language Interface for Orchestra AI MVP
Provides intelligent conversational AI with deep context, memory, and multi-modal capabilities.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import portkey
from enhanced_vector_memory_system import ContextualMemory, ConversationContext, EnhancedVectorMemorySystem
from weaviate.preview import generative_models

from data_source_integrations import DataAggregationOrchestrator

logger = logging.getLogger(__name__)

class ConversationMode(Enum):
    """Different conversation modes for context-aware responses."""

    CASUAL = "casual"
    ANALYTICAL = "analytical"
    TECHNICAL = "technical"
    STRATEGIC = "strategic"
    CREATIVE = "creative"

@dataclass
class ConversationMessage:
    """Individual conversation message with metadata."""

    id: str
    user_id: str
    conversation_id: str
    content: str
    role: str  # 'user', 'assistant', 'system'
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    intent: Optional[str] = None
    entities: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class ConversationSession:
    """Complete conversation session with context."""

    id: str
    user_id: str
    title: Optional[str]
    mode: ConversationMode
    messages: List[ConversationMessage]
    context: ConversationContext
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

class IntentClassifier:
    """Classifies user intents from natural language input."""

    INTENT_PATTERNS = {
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
        text_lower = text.lower()

        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return intent

        return "general_query"

class ContextualResponseGenerator:
    """Generates context-aware responses using multiple AI models."""

    def __init__(self, project_id: str, portkey_api_key: str):
        self.project_id = project_id

        # Initialize AI models
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

        # Build enhanced prompt with context
        enhanced_prompt = await self._build_enhanced_prompt(query, context, mode, intent)

        # Select appropriate model
        model = self.model_routing.get(mode.value, "gemini-pro")

        try:
            # Try primary model
            response = await self._generate_with_model(enhanced_prompt, model)

            # Extract metadata from response
            metadata = await self._extract_response_metadata(response, context)

            return response, metadata

        except Exception as e:
            logger.warning(f"Primary model failed, falling back to Gemini: {e}")

            # Fallback to Gemini
            try:
                response = self.gemini.generate_content(enhanced_prompt).text
                metadata = {
                    "model": "gemini-fallback",
                    "timestamp": datetime.utcnow().isoformat(),
                }
                return response, metadata
            except Exception as fallback_error:
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

        prompt_parts = [
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
        source_counts = {}
        for memory in memories:
            source = memory.source
            source_counts[source] = source_counts.get(source, 0) + 1

        if not source_counts:
            return "No specific data sources available."

        summary_parts = []
        for source, count in source_counts.items():
            summary_parts.append(f"- {source.upper()}: {count} relevant items")

        return "\n".join(summary_parts)

    async def _generate_with_model(self, prompt: str, model: str) -> str:
        """Generate response using specified model via Portkey."""

        try:
            response = self.portkey.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert AI assistant with access to comprehensive business data.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
            )
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Portkey generation failed with model {model}: {e}")
            raise

    async def _extract_response_metadata(self, response: str, context: ConversationContext) -> Dict[str, Any]:
        """Extract metadata from the generated response."""

        metadata = {
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
    Advanced natural language interface for Orchestra AI.

    Features:
    - Context-aware conversations
    - Multi-modal AI model routing
    - Intent classification
    - Memory-powered responses
    - Real-time data integration
    """

    def __init__(
        self,
        memory_system: EnhancedVectorMemorySystem,
        data_orchestrator: DataAggregationOrchestrator,
        project_id: str,
        portkey_api_key: str,
    ):
        self.memory_system = memory_system
        self.data_orchestrator = data_orchestrator
        self.project_id = project_id

        # Initialize components
        self.intent_classifier = IntentClassifier()
        self.response_generator = ContextualResponseGenerator(project_id, portkey_api_key)

        # Active conversations
        self.active_sessions: Dict[str, ConversationSession] = {}

    async def start_conversation(
        self,
        user_id: str,
        initial_query: Optional[str] = None,
        mode: ConversationMode = ConversationMode.CASUAL,
        conversation_id: Optional[str] = None,
    ) -> ConversationSession:
        """Start a new conversation session or resume existing one."""

        if not conversation_id:
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

        session = self.active_sessions.get(conversation_id)
        if not session:
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

        # Extract data sources from message
        sources_mentioned = []
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

        # Extract search parameters from message
        sources = None
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

        # Update context with analytical focus
        context = await self.memory_system.get_conversation_context(
            user_id=session.user_id, conversation_id=session.id, query=message
        )

        # Generate analytical response
        response_content, metadata = await self.response_generator.generate_response(
            query=message,
            context=context,
            mode=ConversationMode.ANALYTICAL,
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

        # Update conversation context
        context = await self.memory_system.get_conversation_context(
            user_id=session.user_id, conversation_id=session.id, query=message
        )

        # Update session context
        session.context = context

        # Generate contextual response
        response_content, metadata = await self.response_generator.generate_response(
            query=message,
            context=context,
            mode=session.mode,
            intent=session.messages[-1].intent if session.messages else None,
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

    async def get_conversation_history(
        self, conversation_id: str, limit: Optional[int] = None
    ) -> List[ConversationMessage]:
        """Get conversation history."""

        session = self.active_sessions.get(conversation_id)
        if not session:
            return []

        messages = session.messages
        if limit:
            messages = messages[-limit:]

        return messages

    async def end_conversation(self, conversation_id: str) -> None:
        """End and clean up a conversation session."""

        if conversation_id in self.active_sessions:
            session = self.active_sessions[conversation_id]

            # Save conversation summary to memory
            if session.messages:
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
        return [session for session in self.active_sessions.values() if session.user_id == user_id]
