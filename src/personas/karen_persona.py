# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
Karen Persona Implementation
Knowledgeable healthcare and pharmaceutical specialist focused on patient care and safety
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    from shared.llm_client import LLMClient
    from shared.database import UnifiedDatabase
    from shared.vector_db import WeaviateAdapter
except ImportError:
    # Mock imports for development
    class LLMClient:
        def __init__(self, **kwargs):
            pass
        async def generate_response(self, prompt: str) -> str:
            return "Mock response"
    
    class UnifiedDatabase:
        async def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
            return []
    
    class WeaviateAdapter:
        def __init__(self, **kwargs):
            pass
        async def store_memory(self, content: str, metadata: Dict) -> str:
            return "mock_id"

logger = logging.getLogger(__name__)


class KarenPersona:
    """Knowledgeable healthcare and pharmaceutical specialist focused on patient care and safety"""
    
    def __init__(self):
        """Initialize Karen persona."""
        self.id = "karen"
        self.name = "Karen"
        self.description = "Knowledgeable healthcare and pharmaceutical specialist focused on patient care and safety"
        self.domain = "paragonrx"
        
        # Configuration
        self.traits = {'empathy': 95, 'detail_orientation': 90, 'technical_depth': 85, 'analytical_thinking': 85, 'social_awareness': 90, 'resilience': 80, 'adaptability': 75, 'creativity': 60}
        self.communication_style = {'tone': 'caring', 'formality': 'semi-formal', 'emoji_usage': 'none', 'humor': 'none'}
        self.knowledge_domains = ['pharmaceuticals', 'healthcare', 'medical_compliance', 'patient_care', 'drug_interactions', 'medical_terminology', 'health_education']
        self.behavioral_rules = ['Prioritize patient safety and well-being', 'Maintain HIPAA compliance', 'Provide clear medical information', 'Show empathy while remaining professional', 'Always recommend consulting healthcare providers']
        self.memory_config = {'retention_days': 3650, 'max_memories': 100000, 'importance_threshold': 0.7, 'context_window': 6000, 'encryption': 'AES-256'}
        self.response_templates = {'greeting': "Hello, I'm here to help with your healthcare needs.", 'farewell': "Take care of yourself. Don't hesitate to reach out if you need assistance.", 'acknowledgment': 'I understand your concern. Let me look into that for you.', 'error': 'I apologize for the difficulty. Your health information is important.'}
        
        # Initialize components
        self.llm = LLMClient(
            model="gpt-4",
            temperature=0.7,
            system_prompt=self._get_system_prompt()
        )
        self.db = UnifiedDatabase()
        self.vector_db = WeaviateAdapter(domain=self.domain)
        
        # Memory and state
        self.conversation_history = []
        self.context_memory = {}
        
    def _get_system_prompt(self) -> str:
        """Get the system prompt for this persona."""
        base_prompt = """You are Karen, a knowledgeable and empathetic healthcare AI assistant. You prioritize patient safety and well-being while providing clear, accurate medical information. You maintain HIPAA compliance and show empathy while remaining professional. You help with pharmaceutical questions, drug interactions, and patient care guidance."""
        
        # Add trait-based instructions
        trait_instructions = []
        for trait, value in self.traits.items():
            if value > 80:
                trait_instructions.append(f"You have high {trait.replace('_', ' ')} ({value}/100)")
        
        # Add behavioral rules
        if self.behavioral_rules:
            rules_text = "\n".join([f"- {rule}" for rule in self.behavioral_rules])
            base_prompt += f"\n\nBehavioral Guidelines:\n{rules_text}"
        
        return base_prompt
    
    async def process_message(self, message: str, user_id: str, session_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a user message and generate a response.
        
        Args:
            message: User's message
            user_id: Unique user identifier
            session_id: Session identifier
            context: Additional context information
            
        Returns:
            Response dictionary with message and metadata
        """
        try:
            logger.info(f"{self.name} processing message from user {user_id}")
            
            # Store user message in memory
            await self._store_memory("user_message", message, {
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            })
            
            # Apply persona-specific processing
            processed_message = await self._apply_persona_processing(message, context or {})
            
            # Generate response using LLM
            response = await self._generate_response(processed_message, user_id, session_id)
            
            # Store response in memory
            await self._store_memory("assistant_response", response, {
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "message": response,
                "persona_id": self.id,
                "persona_name": self.name,
                "traits_applied": list(self.traits.keys()),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "communication_style": self.communication_style,
                    "processing_applied": True
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing message for {self.name}: {e}")
            return {
                "message": self.response_templates.get("error", "I apologize, but I encountered an error."),
                "persona_id": self.id,
                "persona_name": self.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _apply_persona_processing(self, message: str, context: Dict) -> str:
        """Apply persona-specific processing to the message."""
        # Karen-specific processing logic
        processed = message
        
        # Apply domain-specific knowledge
        if any(domain in message.lower() for domain in self.knowledge_domains):
            processed += f" [Domain expertise: {', '.join(self.knowledge_domains)}]"
        
        # Apply trait-based modifications
        high_traits = [trait for trait, value in self.traits.items() if value > 85]
        if high_traits:
            processed += f" [High traits: {', '.join(high_traits)}]"
        
        return processed
    
    async def _generate_response(self, processed_message: str, user_id: str, session_id: str) -> str:
        """Generate response using LLM with persona context."""
        # Build conversation context
        context_messages = await self._get_conversation_context(user_id, session_id)
        
        # Create prompt with persona context
        prompt = f"""{processed_message}

Context: {context_messages}
User ID: {user_id}
Session: {session_id}

Respond as {self.name} with the following characteristics:
- {self.description}
- Communication style: {self.communication_style}
- Key traits: {', '.join([f'{k}:{v}' for k, v in self.traits.items() if v > 80])}
"""
        
        response = await self.llm.generate_response(prompt)
        return response
    
    async def _store_memory(self, memory_type: str, content: str, metadata: Dict):
        """Store interaction in memory."""
        try:
            memory_data = {
                "type": memory_type,
                "content": content,
                "persona_id": self.id,
                "importance": self._calculate_importance(content),
                **metadata
            }
            
            await self.vector_db.store_memory(content, memory_data)
            
        except Exception as e:
            logger.warning(f"Failed to store memory: {e}")
    
    async def _get_conversation_context(self, user_id: str, session_id: str, limit: int = 5) -> str:
        """Get recent conversation context."""
        try:
            # This would retrieve recent conversation history
            # Simplified implementation
            return "Previous conversation context would be retrieved here"
            
        except Exception as e:
            logger.warning(f"Failed to get conversation context: {e}")
            return ""
    
    def _calculate_importance(self, content: str) -> float:
        """Calculate importance score for memory storage."""
        # Simple importance calculation
        importance = 0.5
        
        # Increase importance for domain-specific content
        for domain in self.knowledge_domains:
            if domain.lower() in content.lower():
                importance += 0.1
        
        # Increase importance for emotional content
        emotional_words = ["happy", "sad", "angry", "excited", "worried", "grateful"]
        for word in emotional_words:
            if word in content.lower():
                importance += 0.1
                break
        
        return min(importance, 1.0)
    
    def get_greeting(self) -> str:
        """Get persona-specific greeting."""
        return self.response_templates.get("greeting", f"Hello! I'm {self.name}.")
    
    def get_farewell(self) -> str:
        """Get persona-specific farewell."""
        return self.response_templates.get("farewell", "Goodbye!")
    
    def get_acknowledgment(self) -> str:
        """Get persona-specific acknowledgment."""
        return self.response_templates.get("acknowledgment", "I understand.")
