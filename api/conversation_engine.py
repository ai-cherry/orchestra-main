#!/usr/bin/env python3
"""
Cherry AI Conversation Engine
Implements sophisticated relationship development and learning framework
"""

import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import hashlib
from pathlib import Path

import asyncpg
from pydantic import BaseModel

# Add parent directory to path for config import
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

try:
    from config.cherry_ai_config import get_config, CherryAIConfig
    HAS_CONFIG = True
except ImportError:
    logging.warning("Could not import cherry_ai_config, using fallback configuration")
    HAS_CONFIG = False

logger = logging.getLogger(__name__)

class ConversationMode(str, Enum):
    """Conversation interaction modes"""
    CASUAL = "casual"
    FOCUSED = "focused"
    COACHING = "coaching"
    ANALYTICAL = "analytical"
    SUPPORTIVE = "supportive"

class LearningType(str, Enum):
    """Types of learning patterns"""
    COMMUNICATION_STYLE = "communication_style"
    PREFERENCES = "preferences"
    GOALS = "goals"
    PATTERNS = "patterns"
    EMOTIONAL_RESPONSE = "emotional_response"
    DECISION_MAKING = "decision_making"

@dataclass
class ConversationContext:
    """Context for ongoing conversations"""
    user_id: int
    persona_type: str
    session_id: str
    mode: ConversationMode
    topic_focus: Optional[str] = None
    relationship_stage: str = "developing"  # developing, established, mature
    interaction_count: int = 0
    last_interaction: Optional[datetime] = None
    emotional_tone: str = "neutral"
    context_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LearningPattern:
    """Individual learning pattern"""
    pattern_type: LearningType
    pattern_data: Dict[str, Any]
    confidence_score: float
    observation_count: int
    last_updated: datetime
    effectiveness_score: float = 0.5

class PersonaPersonality:
    """Base personality framework for AI personas"""
    
    def __init__(self, persona_type: str, base_traits: Dict[str, float], config: Optional['CherryAIConfig'] = None):
        self.persona_type = persona_type
        self.base_traits = base_traits
        self.learned_adjustments: Dict[str, float] = {}
        self.communication_patterns: Dict[str, Any] = {}
        
        # Load adaptation limits from config if available
        if config and HAS_CONFIG:
            ai_config = config.ai
            persona_config = config.get_persona_config(persona_type)
            learning_config = persona_config.learning_config
            
            self.adaptation_limits = {
                'max_trait_adjustment': learning_config.get('max_trait_adjustment', ai_config.max_trait_adjustment),
                'learning_rate': learning_config.get('adaptation_rate', ai_config.learning_rate),
                'confidence_threshold': learning_config.get('confidence_threshold', ai_config.confidence_threshold)
            }
        else:
            # Fallback defaults
            self.adaptation_limits = {
                'max_trait_adjustment': 0.2,  # Maximum 20% adjustment from base
                'learning_rate': 0.05,  # Gradual 5% learning rate
                'confidence_threshold': 0.7  # Minimum confidence for adaptation
            }
    
    def get_effective_trait(self, trait_name: str) -> float:
        """Get effective trait value with learned adjustments"""
        base_value = self.base_traits.get(trait_name, 0.5)
        adjustment = self.learned_adjustments.get(trait_name, 0.0)
        
        # Apply adaptation limits
        max_adj = self.adaptation_limits['max_trait_adjustment']
        adjustment = max(-max_adj, min(max_adj, adjustment))
        
        return max(0.0, min(1.0, base_value + adjustment))
    
    def adapt_trait(self, trait_name: str, feedback_score: float, confidence: float):
        """Gradually adapt personality trait based on feedback"""
        if confidence < self.adaptation_limits['confidence_threshold']:
            return
        
        current_adjustment = self.learned_adjustments.get(trait_name, 0.0)
        learning_rate = self.adaptation_limits['learning_rate']
        
        # Calculate adjustment based on feedback
        target_adjustment = (feedback_score - 0.5) * 0.4  # Scale feedback to adjustment range
        new_adjustment = current_adjustment + (target_adjustment - current_adjustment) * learning_rate
        
        # Apply limits
        max_adj = self.adaptation_limits['max_trait_adjustment']
        new_adjustment = max(-max_adj, min(max_adj, new_adjustment))
        
        self.learned_adjustments[trait_name] = new_adjustment

class RelationshipMemory:
    """Manages relationship memory and learning patterns"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.learning_patterns: Dict[str, List[LearningPattern]] = {}
    
    async def initialize_schema(self):
        """Initialize relationship memory database schema"""
        schema_sql = """
        -- Conversation history with comprehensive context
        CREATE TABLE IF NOT EXISTS shared.conversations (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES shared.users(id) ON DELETE CASCADE,
            persona_type VARCHAR(50) NOT NULL,
            session_id UUID DEFAULT gen_random_uuid(),
            message_type VARCHAR(20) CHECK (message_type IN ('user', 'assistant')),
            content TEXT NOT NULL,
            context_data JSONB DEFAULT '{}',
            mood_score FLOAT DEFAULT 0.5,
            learning_indicators JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            response_time_ms INTEGER,
            effectiveness_score FLOAT
        );
        
        -- Relationship development tracking
        CREATE TABLE IF NOT EXISTS shared.relationship_development (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES shared.users(id) ON DELETE CASCADE,
            persona_type VARCHAR(50) NOT NULL,
            relationship_stage VARCHAR(50) DEFAULT 'developing',
            interaction_count INTEGER DEFAULT 0,
            trust_score FLOAT DEFAULT 0.5,
            familiarity_score FLOAT DEFAULT 0.5,
            communication_effectiveness FLOAT DEFAULT 0.5,
            last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            development_milestones JSONB DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, persona_type)
        );
        
        -- Learning patterns and adaptations
        CREATE TABLE IF NOT EXISTS shared.learning_patterns (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES shared.users(id) ON DELETE CASCADE,
            persona_type VARCHAR(50) NOT NULL,
            pattern_type VARCHAR(50) NOT NULL,
            pattern_data JSONB NOT NULL,
            confidence_score FLOAT DEFAULT 0.5,
            observation_count INTEGER DEFAULT 1,
            effectiveness_score FLOAT DEFAULT 0.5,
            last_observed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Personality adaptations tracking
        CREATE TABLE IF NOT EXISTS shared.personality_adaptations (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES shared.users(id) ON DELETE CASCADE,
            persona_type VARCHAR(50) NOT NULL,
            trait_name VARCHAR(100) NOT NULL,
            base_value FLOAT NOT NULL,
            learned_adjustment FLOAT DEFAULT 0.0,
            adaptation_confidence FLOAT DEFAULT 0.5,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, persona_type, trait_name)
        );
        
        -- Performance indexes
        CREATE INDEX IF NOT EXISTS idx_conversations_user_persona 
            ON shared.conversations(user_id, persona_type, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_conversations_session 
            ON shared.conversations(session_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_relationship_user_persona 
            ON shared.relationship_development(user_id, persona_type);
        CREATE INDEX IF NOT EXISTS idx_learning_patterns_user_persona 
            ON shared.learning_patterns(user_id, persona_type, pattern_type);
        CREATE INDEX IF NOT EXISTS idx_personality_adaptations_user_persona 
            ON shared.personality_adaptations(user_id, persona_type);
        """
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(schema_sql)
            logger.info("Relationship memory schema initialized")
    
    async def get_relationship_context(self, user_id: int, persona_type: str) -> Dict[str, Any]:
        """Get comprehensive relationship context for user-persona pair"""
        cache_key = f"{user_id}_{persona_type}"
        
        if cache_key in self.memory_cache:
            return self.memory_cache[cache_key]
        
        async with self.db_pool.acquire() as conn:
            # Get relationship development status
            relationship = await conn.fetchrow("""
                SELECT * FROM shared.relationship_development 
                WHERE user_id = $1 AND persona_type = $2
            """, user_id, persona_type)
            
            # Get recent conversations for context
            recent_conversations = await conn.fetch("""
                SELECT content, context_data, mood_score, created_at
                FROM shared.conversations 
                WHERE user_id = $1 AND persona_type = $2
                ORDER BY created_at DESC LIMIT 10
            """, user_id, persona_type)
            
            # Get learning patterns
            learning_patterns = await conn.fetch("""
                SELECT pattern_type, pattern_data, confidence_score, effectiveness_score
                FROM shared.learning_patterns 
                WHERE user_id = $1 AND persona_type = $2
                AND confidence_score > 0.6
            """, user_id, persona_type)
            
            # Get personality adaptations
            adaptations = await conn.fetch("""
                SELECT trait_name, base_value, learned_adjustment, adaptation_confidence
                FROM shared.personality_adaptations 
                WHERE user_id = $1 AND persona_type = $2
            """, user_id, persona_type)
        
        context = {
            'relationship': dict(relationship) if relationship else None,
            'recent_conversations': [dict(conv) for conv in recent_conversations],
            'learning_patterns': [dict(pattern) for pattern in learning_patterns],
            'personality_adaptations': [dict(adapt) for adapt in adaptations],
            'interaction_summary': await self._generate_interaction_summary(user_id, persona_type)
        }
        
        # Cache for performance
        self.memory_cache[cache_key] = context
        return context
    
    async def _generate_interaction_summary(self, user_id: int, persona_type: str) -> Dict[str, Any]:
        """Generate summary of interaction patterns"""
        async with self.db_pool.acquire() as conn:
            # Get interaction statistics
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_interactions,
                    AVG(mood_score) as avg_mood,
                    AVG(effectiveness_score) as avg_effectiveness,
                    MAX(created_at) as last_interaction,
                    MIN(created_at) as first_interaction
                FROM shared.conversations 
                WHERE user_id = $1 AND persona_type = $2 AND message_type = 'user'
            """, user_id, persona_type)
            
            return dict(stats) if stats else {}
    
    async def record_conversation(self, user_id: int, persona_type: str, 
                                message_type: str, content: str, context_data: Dict[str, Any],
                                session_id: str, mood_score: float = 0.5, 
                                learning_indicators: Dict[str, Any] = None,
                                response_time_ms: int = None) -> int:
        """Record conversation with learning context"""
        async with self.db_pool.acquire() as conn:
            conversation_id = await conn.fetchval("""
                INSERT INTO shared.conversations 
                (user_id, persona_type, session_id, message_type, content, 
                 context_data, mood_score, learning_indicators, response_time_ms)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id
            """, user_id, persona_type, session_id, message_type, content,
                json.dumps(context_data), mood_score, 
                json.dumps(learning_indicators or {}), response_time_ms)
            
            # Clear cache for this user-persona pair
            cache_key = f"{user_id}_{persona_type}"
            self.memory_cache.pop(cache_key, None)
            
            return conversation_id
    
    async def update_relationship_development(self, user_id: int, persona_type: str,
                                            interaction_feedback: Dict[str, float]):
        """Update relationship development metrics"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO shared.relationship_development 
                (user_id, persona_type, interaction_count, trust_score, 
                 familiarity_score, communication_effectiveness, last_interaction)
                VALUES ($1, $2, 1, $3, $4, $5, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id, persona_type) DO UPDATE SET
                    interaction_count = relationship_development.interaction_count + 1,
                    trust_score = LEAST(1.0, relationship_development.trust_score + ($3 - 0.5) * 0.05),
                    familiarity_score = LEAST(1.0, relationship_development.familiarity_score + 0.02),
                    communication_effectiveness = ($5 + relationship_development.communication_effectiveness) / 2,
                    last_interaction = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
            """, user_id, persona_type, 
                interaction_feedback.get('trust', 0.5),
                interaction_feedback.get('familiarity', 0.5),
                interaction_feedback.get('effectiveness', 0.5))

class ConversationEngine:
    """Main conversation engine with learning and adaptation"""
    
    def __init__(self, db_pool: asyncpg.Pool, config: Optional['CherryAIConfig'] = None):
        self.db_pool = db_pool
        self.memory = RelationshipMemory(db_pool)
        self.personalities: Dict[str, PersonaPersonality] = {}
        self.active_sessions: Dict[str, ConversationContext] = {}
        self.config = config or (get_config() if HAS_CONFIG else None)
        
        # Initialize persona personalities with config
        self._initialize_personalities()
    
    async def initialize(self):
        """Initialize conversation engine"""
        await self.memory.initialize_schema()
        logger.info("Conversation engine initialized")
    
    def _initialize_personalities(self):
        """Initialize base personality configurations from config"""
        if self.config and HAS_CONFIG:
            # Load personalities from configuration
            self.personalities = {}
            for persona_type, persona_config in self.config.personas.items():
                self.personalities[persona_type] = PersonaPersonality(
                    persona_type, 
                    persona_config.personality_traits, 
                    self.config
                )
                logger.info(f"Initialized {persona_type} personality from config")
        else:
            # Fallback to hardcoded personalities
            self.personalities = {
                'cherry': PersonaPersonality('cherry', {
                    'playful': 0.9, 'flirty': 0.8, 'creative': 0.9, 
                    'smart': 0.95, 'empathetic': 0.9, 'supportive': 0.95,
                    'energetic': 0.8, 'optimistic': 0.9, 'warm': 0.95
                }),
                'sophia': PersonaPersonality('sophia', {
                    'strategic': 0.95, 'professional': 0.9, 'intelligent': 0.95, 
                    'confident': 0.9, 'analytical': 0.9, 'decisive': 0.85,
                    'focused': 0.9, 'competent': 0.95, 'results_oriented': 0.9
                }),
                'karen': PersonaPersonality('karen', {
                    'knowledgeable': 0.95, 'trustworthy': 0.95, 'patient_centered': 0.9,
                    'detail_oriented': 0.95, 'authoritative': 0.8, 'careful': 0.9,
                    'systematic': 0.9, 'reliable': 0.95, 'thorough': 0.9
                })
            }
            logger.info("Initialized personalities from fallback configuration")
    
    async def generate_response(self, user_id: int, persona_type: str, 
                              user_message: str, session_id: str = None,
                              mode: ConversationMode = ConversationMode.CASUAL) -> Dict[str, Any]:
        """Generate sophisticated AI response with learning integration"""
        start_time = datetime.now()
        
        if not session_id:
            session_id = hashlib.sha256(f"{user_id}_{persona_type}_{datetime.now()}".encode()).hexdigest()[:16]
        
        # Get relationship context
        context = await self.memory.get_relationship_context(user_id, persona_type)
        personality = self.personalities[persona_type]
        
        # Analyze user message for learning indicators
        message_analysis = await self._analyze_user_message(user_message, context)
        
        # Generate personalized response
        response_content = await self._generate_personalized_response(
            persona_type, user_message, context, personality, message_analysis, mode
        )
        
        # Calculate response timing
        response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Record conversation
        await self.memory.record_conversation(
            user_id, persona_type, 'user', user_message, 
            message_analysis, session_id, message_analysis.get('mood_score', 0.5)
        )
        
        await self.memory.record_conversation(
            user_id, persona_type, 'assistant', response_content, 
            {'response_mode': mode.value, 'personality_state': personality.learned_adjustments},
            session_id, response_time_ms=response_time_ms
        )
        
        # Update relationship development
        await self.memory.update_relationship_development(
            user_id, persona_type, {
                'trust': 0.6,  # Positive interaction
                'effectiveness': 0.7,  # Good response quality
                'familiarity': 0.6
            }
        )
        
        return {
            'response': response_content,
            'persona_type': persona_type,
            'session_id': session_id,
            'mode': mode.value,
            'response_time_ms': response_time_ms,
            'relationship_context': {
                'stage': context.get('relationship', {}).get('relationship_stage', 'developing'),
                'interaction_count': context.get('interaction_summary', {}).get('total_interactions', 0),
                'trust_score': context.get('relationship', {}).get('trust_score', 0.5)
            },
            'learning_applied': len(context.get('personality_adaptations', []))
        }
    
    async def _analyze_user_message(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user message for learning indicators"""
        analysis = {
            'mood_score': 0.5,
            'topics': [],
            'intent': 'general',
            'complexity': 'medium',
            'emotional_indicators': [],
            'preference_signals': []
        }
        
        # Simple sentiment analysis (would be replaced with actual NLP)
        positive_words = ['great', 'good', 'love', 'excellent', 'wonderful', 'amazing', 'perfect']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'horrible', 'disappointed', 'frustrated']
        
        message_lower = message.lower()
        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)
        
        # Adjust mood score based on sentiment
        if positive_count > negative_count:
            analysis['mood_score'] = 0.7 + (positive_count * 0.1)
        elif negative_count > positive_count:
            analysis['mood_score'] = 0.3 - (negative_count * 0.1)
        
        analysis['mood_score'] = max(0.0, min(1.0, analysis['mood_score']))
        
        # Detect intent patterns
        if any(word in message_lower for word in ['help', 'assist', 'support']):
            analysis['intent'] = 'help_seeking'
        elif any(word in message_lower for word in ['plan', 'schedule', 'organize']):
            analysis['intent'] = 'planning'
        elif any(word in message_lower for word in ['advice', 'suggest', 'recommend']):
            analysis['intent'] = 'advice_seeking'
        
        return analysis
    
    async def _generate_personalized_response(self, persona_type: str, user_message: str,
                                           context: Dict[str, Any], personality: PersonaPersonality,
                                           message_analysis: Dict[str, Any], 
                                           mode: ConversationMode) -> str:
        """Generate response with personality and learning integration"""
        
        # This is a sophisticated response generation framework
        # In production, this would integrate with LLM APIs (OpenAI, Anthropic, etc.)
        
        base_responses = {
            'cherry': {
                'greeting': [
                    "Hey there! 🌸 What's on your mind today?",
                    "Hi sweetie! I'm so excited to chat with you! ✨",
                    "Hello beautiful! How can I brighten your day? 😊"
                ],
                'help_seeking': [
                    "Of course I'm here to help! You know I've got your back 💕",
                    "Absolutely! Let's figure this out together, gorgeous! 🌟",
                    "I'm totally here for you! What do you need support with? 🤗"
                ],
                'planning': [
                    "Ooh, I love planning! Let's make something amazing happen! ✨",
                    "Planning is so my thing! What are we organizing, honey? 📋",
                    "Yes! I'm excited to help you get this sorted out perfectly! 🎯"
                ]
            },
            'sophia': {
                'greeting': [
                    "Good to see you. What strategic challenges are we tackling today?",
                    "Hello. I'm ready to dive into whatever business matters you're facing.",
                    "Welcome back. Let's focus on driving results for your objectives."
                ],
                'help_seeking': [
                    "I'm here to provide the strategic guidance you need. What's the situation?",
                    "Absolutely. Let's analyze this systematically and develop an action plan.",
                    "I'll help you navigate this effectively. Tell me more about the challenge."
                ],
                'planning': [
                    "Excellent. Strategic planning is where we create competitive advantage.",
                    "Perfect timing. Let's structure this for maximum impact and efficiency.",
                    "I appreciate systematic planning. What are our key objectives and constraints?"
                ]
            },
            'karen': {
                'greeting': [
                    "Hello. I'm here to help with any healthcare or regulatory questions you have.",
                    "Good day. How can I assist with your healthcare operations today?",
                    "Welcome. I'm ready to provide guidance on clinical or compliance matters."
                ],
                'help_seeking': [
                    "Certainly. Let me provide you with comprehensive guidance on this matter.",
                    "I'm here to help ensure we address this properly and thoroughly.",
                    "Of course. Let's work through this systematically to ensure compliance."
                ],
                'planning': [
                    "Excellent. Proper planning is essential for regulatory compliance and patient safety.",
                    "Good approach. Let's structure this to meet all regulatory requirements.",
                    "I appreciate thorough planning. What protocols do we need to establish?"
                ]
            }
        }
        
        # Get appropriate response category
        intent = message_analysis.get('intent', 'greeting')
        if intent not in base_responses[persona_type]:
            intent = 'greeting'
        
        # Select base response (would use more sophisticated selection in production)
        import random
        base_response = random.choice(base_responses[persona_type][intent])
        
        # Apply personality adaptations
        relationship_stage = context.get('relationship', {}).get('relationship_stage', 'developing')
        interaction_count = context.get('interaction_summary', {}).get('total_interactions', 0)
        
        # Adapt response based on relationship development
        if relationship_stage == 'established' and interaction_count > 20:
            # More personalized, familiar tone
            if persona_type == 'cherry':
                base_response = base_response.replace("Hey there", "Hey babe").replace("Hi sweetie", "Hi gorgeous")
            elif persona_type == 'sophia':
                base_response = base_response.replace("Good to see you", "Good to see you again")
        
        return base_response
    
    async def get_conversation_history(self, user_id: int, persona_type: str, 
                                     limit: int = 20) -> List[Dict[str, Any]]:
        """Get conversation history with relationship context"""
        async with self.db_pool.acquire() as conn:
            conversations = await conn.fetch("""
                SELECT message_type, content, context_data, mood_score, 
                       created_at, effectiveness_score
                FROM shared.conversations 
                WHERE user_id = $1 AND persona_type = $2
                ORDER BY created_at DESC LIMIT $3
            """, user_id, persona_type, limit)
            
            return [dict(conv) for conv in reversed(conversations)]
    
    async def get_relationship_insights(self, user_id: int, persona_type: str) -> Dict[str, Any]:
        """Get comprehensive relationship development insights"""
        context = await self.memory.get_relationship_context(user_id, persona_type)
        
        return {
            'relationship_stage': context.get('relationship', {}).get('relationship_stage', 'developing'),
            'trust_score': context.get('relationship', {}).get('trust_score', 0.5),
            'familiarity_score': context.get('relationship', {}).get('familiarity_score', 0.5),
            'interaction_count': context.get('interaction_summary', {}).get('total_interactions', 0),
            'communication_effectiveness': context.get('relationship', {}).get('communication_effectiveness', 0.5),
            'learning_patterns_active': len(context.get('learning_patterns', [])),
            'personality_adaptations': len(context.get('personality_adaptations', [])),
            'recent_mood_trend': context.get('interaction_summary', {}).get('avg_mood', 0.5)
        } 