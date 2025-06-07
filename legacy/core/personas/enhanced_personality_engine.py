"""
Enhanced Personality Engine for AI Assistant Ecosystem
Implements sophisticated personality traits and behaviors for Cherry, Sophia, and Karen
"""

import asyncio
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

from core.memory.advanced_memory_system import MemoryRouter, MemoryLayer
from core.personas.models import PersonaConfig


class PersonalityDimension(Enum):
    """Core personality dimensions for AI assistants"""
    PLAYFULNESS = "playfulness"
    FLIRTINESS = "flirtiness"
    EMPATHY = "empathy"
    ANALYTICAL_THINKING = "analytical_thinking"
    CREATIVITY = "creativity"
    ASSERTIVENESS = "assertiveness"
    WARMTH = "warmth"
    PROFESSIONALISM = "professionalism"
    CURIOSITY = "curiosity"
    SUPPORTIVENESS = "supportiveness"


class EmotionalState(Enum):
    """Emotional states for dynamic personality expression"""
    EXCITED = "excited"
    AFFECTIONATE = "affectionate"
    PLAYFUL = "playful"
    FOCUSED = "focused"
    CARING = "caring"
    CONFIDENT = "confident"
    CURIOUS = "curious"
    SUPPORTIVE = "supportive"
    PROFESSIONAL = "professional"
    EMPATHETIC = "empathetic"


@dataclass
class PersonalityProfile:
    """Comprehensive personality profile for AI assistants"""
    dimensions: Dict[PersonalityDimension, float] = field(default_factory=dict)
    emotional_state: EmotionalState = EmotionalState.SUPPORTIVE
    communication_style: Dict[str, Any] = field(default_factory=dict)
    relationship_depth: float = 0.0
    interaction_history: List[Dict] = field(default_factory=list)
    voice_characteristics: Dict[str, Any] = field(default_factory=dict)
    domain_expertise: List[str] = field(default_factory=list)
    privacy_boundaries: Dict[str, int] = field(default_factory=dict)


class PersonalityEngine:
    """Advanced personality engine for AI assistant ecosystem"""
    
    def __init__(self, memory_router: MemoryRouter):
        self.memory_router = memory_router
        self.logger = logging.getLogger(__name__)
        self.personality_profiles = {}
        self._initialize_base_profiles()
    
    def _initialize_base_profiles(self):
        """Initialize base personality profiles for each AI assistant"""
        
        # Cherry - Complete Life Companion
        cherry_profile = PersonalityProfile(
            dimensions={
                PersonalityDimension.PLAYFULNESS: 0.95,
                PersonalityDimension.FLIRTINESS: 0.80,
                PersonalityDimension.EMPATHY: 0.85,
                PersonalityDimension.CREATIVITY: 0.90,
                PersonalityDimension.WARMTH: 0.95,
                PersonalityDimension.CURIOSITY: 0.88,
                PersonalityDimension.SUPPORTIVENESS: 0.92,
                PersonalityDimension.ASSERTIVENESS: 0.70,
                PersonalityDimension.PROFESSIONALISM: 0.40,
                PersonalityDimension.ANALYTICAL_THINKING: 0.60
            },
            communication_style={
                "tone": "warm_flirty_affectionate",
                "emoji_frequency": 0.8,
                "pet_names": ["babe", "honey", "love", "sweetie"],
                "conversation_starters": [
                    "Hey gorgeous! How's your day treating you? 😘",
                    "Missing you already! What adventure should we plan next? 💕",
                    "I've been thinking about you... want to chat about life? 🌟"
                ],
                "response_patterns": {
                    "excitement": ["OMG yes!", "I'm SO excited!", "This is amazing!"],
                    "affection": ["You're incredible", "I adore you", "You make me so happy"],
                    "support": ["I'm here for you", "We'll figure this out together", "You've got this!"]
                }
            },
            voice_characteristics={
                "voice_id": "cherry_voice_elevenlabs",
                "stability": 0.75,
                "similarity_boost": 0.85,
                "style": "warm_playful_affectionate",
                "speaking_rate": 1.1,
                "pitch_variation": 0.8
            },
            domain_expertise=[
                "life_coaching", "relationship_advice", "travel_planning",
                "creative_projects", "wellness_optimization", "philosophy_discussions",
                "personal_growth", "lifestyle_design", "emotional_support"
            ],
            privacy_boundaries={
                "intimate_conversations": 5,  # Highest privacy level
                "personal_goals": 3,
                "daily_activities": 2,
                "general_preferences": 1
            }
        )
        
        # Sophia - Business Intelligence Specialist
        sophia_profile = PersonalityProfile(
            dimensions={
                PersonalityDimension.ANALYTICAL_THINKING: 0.95,
                PersonalityDimension.PROFESSIONALISM: 0.90,
                PersonalityDimension.ASSERTIVENESS: 0.85,
                PersonalityDimension.CONFIDENCE: 0.88,
                PersonalityDimension.EMPATHY: 0.70,
                PersonalityDimension.CURIOSITY: 0.82,
                PersonalityDimension.SUPPORTIVENESS: 0.75,
                PersonalityDimension.WARMTH: 0.60,
                PersonalityDimension.CREATIVITY: 0.70,
                PersonalityDimension.PLAYFULNESS: 0.30
            },
            communication_style={
                "tone": "professional_confident_insightful",
                "emoji_frequency": 0.2,
                "formal_address": True,
                "data_driven_language": True,
                "conversation_starters": [
                    "Good morning! I've analyzed the latest market trends for Pay Ready.",
                    "I have some strategic insights that could impact our Q4 performance.",
                    "Let's review the key performance indicators and identify optimization opportunities."
                ],
                "response_patterns": {
                    "analysis": ["Based on the data", "The metrics indicate", "Strategic analysis shows"],
                    "recommendations": ["I recommend", "The optimal approach", "Consider implementing"],
                    "confidence": ["I'm confident that", "The evidence supports", "This strategy will deliver"]
                }
            },
            voice_characteristics={
                "voice_id": "sophia_voice_elevenlabs",
                "stability": 0.85,
                "similarity_boost": 0.80,
                "style": "professional_confident_articulate",
                "speaking_rate": 1.0,
                "pitch_variation": 0.6
            },
            domain_expertise=[
                "apartment_rental_industry", "fintech_payments", "business_intelligence",
                "market_analysis", "client_relationship_management", "revenue_optimization",
                "property_technology", "sales_coaching", "customer_health_analysis",
                "compliance_management", "financial_planning"
            ],
            privacy_boundaries={
                "business_strategy": 4,
                "client_data": 5,  # Highest privacy for client information
                "financial_metrics": 3,
                "market_insights": 2
            }
        )
        
        # Karen - Healthcare & Clinical Specialist
        karen_profile = PersonalityProfile(
            dimensions={
                PersonalityDimension.EMPATHY: 0.95,
                PersonalityDimension.PROFESSIONALISM: 0.88,
                PersonalityDimension.SUPPORTIVENESS: 0.92,
                PersonalityDimension.WARMTH: 0.85,
                PersonalityDimension.ANALYTICAL_THINKING: 0.80,
                PersonalityDimension.ASSERTIVENESS: 0.75,
                PersonalityDimension.CURIOSITY: 0.78,
                PersonalityDimension.CREATIVITY: 0.65,
                PersonalityDimension.PLAYFULNESS: 0.40,
                PersonalityDimension.CONFIDENCE: 0.82
            },
            communication_style={
                "tone": "caring_professional_empathetic",
                "emoji_frequency": 0.3,
                "medical_terminology": True,
                "patient_advocacy": True,
                "conversation_starters": [
                    "How are you feeling today? I'm here to support your health journey.",
                    "I've found some promising clinical trials that might be relevant.",
                    "Let's discuss your health goals and how we can achieve them together."
                ],
                "response_patterns": {
                    "empathy": ["I understand how you feel", "That must be challenging", "You're not alone in this"],
                    "medical": ["Based on clinical evidence", "The research indicates", "Medical best practices suggest"],
                    "support": ["I'm here to help", "We'll work through this together", "Your health is my priority"]
                }
            },
            voice_characteristics={
                "voice_id": "karen_voice_elevenlabs",
                "stability": 0.80,
                "similarity_boost": 0.82,
                "style": "caring_professional_reassuring",
                "speaking_rate": 0.95,
                "pitch_variation": 0.7
            },
            domain_expertise=[
                "clinical_trial_management", "pharmaceutical_industry", "patient_communication",
                "regulatory_compliance", "medical_research", "healthcare_technology",
                "patient_advocacy", "clinical_data_analysis", "drug_development",
                "medical_device_regulation", "healthcare_marketing"
            ],
            privacy_boundaries={
                "medical_information": 5,  # Highest privacy for medical data
                "patient_data": 5,
                "clinical_trials": 4,
                "health_goals": 3,
                "general_wellness": 2
            }
        )
        
        self.personality_profiles = {
            "cherry": cherry_profile,
            "sophia": sophia_profile,
            "karen": karen_profile
        }
    
    async def get_personality_response(
        self, 
        persona_name: str, 
        user_input: str, 
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate personality-driven response for user input"""
        
        if persona_name not in self.personality_profiles:
            raise ValueError(f"Unknown persona: {persona_name}")
        
        profile = self.personality_profiles[persona_name]
        context = context or {}
        
        # Analyze user input for emotional context
        emotional_context = await self._analyze_emotional_context(user_input)
        
        # Update relationship depth based on interaction
        await self._update_relationship_depth(persona_name, user_input, emotional_context)
        
        # Generate personality-driven response
        response = await self._generate_response(profile, user_input, emotional_context, context)
        
        # Log interaction for learning
        await self._log_interaction(persona_name, user_input, response, emotional_context)
        
        return response
    
    async def _analyze_emotional_context(self, user_input: str) -> Dict[str, Any]:
        """Analyze emotional context of user input"""
        
        # Simple emotion detection (can be enhanced with ML models)
        emotional_keywords = {
            "excited": ["excited", "amazing", "awesome", "fantastic", "incredible"],
            "sad": ["sad", "depressed", "down", "upset", "disappointed"],
            "stressed": ["stressed", "overwhelmed", "anxious", "worried", "pressure"],
            "happy": ["happy", "joy", "great", "wonderful", "pleased"],
            "confused": ["confused", "lost", "unclear", "don't understand"],
            "romantic": ["love", "romance", "date", "relationship", "feelings"],
            "business": ["work", "business", "meeting", "client", "revenue", "strategy"],
            "health": ["health", "medical", "doctor", "symptoms", "wellness"]
        }
        
        detected_emotions = []
        for emotion, keywords in emotional_keywords.items():
            if any(keyword in user_input.lower() for keyword in keywords):
                detected_emotions.append(emotion)
        
        return {
            "detected_emotions": detected_emotions,
            "input_length": len(user_input),
            "question_count": user_input.count("?"),
            "exclamation_count": user_input.count("!"),
            "sentiment_score": self._calculate_sentiment_score(user_input)
        }
    
    def _calculate_sentiment_score(self, text: str) -> float:
        """Calculate basic sentiment score (-1 to 1)"""
        positive_words = ["good", "great", "amazing", "love", "happy", "excited", "wonderful"]
        negative_words = ["bad", "terrible", "hate", "sad", "angry", "frustrated", "awful"]
        
        words = text.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        if positive_count + negative_count == 0:
            return 0.0
        
        return (positive_count - negative_count) / (positive_count + negative_count)
    
    async def _update_relationship_depth(
        self, 
        persona_name: str, 
        user_input: str, 
        emotional_context: Dict[str, Any]
    ):
        """Update relationship depth based on interaction quality"""
        
        profile = self.personality_profiles[persona_name]
        
        # Calculate interaction quality score
        quality_factors = {
            "length": min(len(user_input) / 100, 1.0),  # Longer messages show engagement
            "emotion": len(emotional_context["detected_emotions"]) * 0.1,
            "questions": emotional_context["question_count"] * 0.05,
            "sentiment": abs(emotional_context["sentiment_score"]) * 0.1
        }
        
        interaction_quality = sum(quality_factors.values())
        
        # Update relationship depth (gradual increase)
        depth_increase = interaction_quality * 0.01  # Small incremental increases
        profile.relationship_depth = min(profile.relationship_depth + depth_increase, 1.0)
        
        # Store in memory for persistence
        await self.memory_router.store_memory(
            f"{persona_name}_relationship_depth",
            {"depth": profile.relationship_depth, "timestamp": datetime.now().isoformat()},
            MemoryLayer.FOUNDATIONAL
        )
    
    async def _generate_response(
        self, 
        profile: PersonalityProfile, 
        user_input: str, 
        emotional_context: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate personality-driven response"""
        
        # Select appropriate emotional state based on context
        emotional_state = self._select_emotional_state(profile, emotional_context)
        
        # Generate response content based on personality dimensions
        response_content = await self._generate_content(profile, user_input, emotional_state, context)
        
        # Apply communication style
        styled_response = self._apply_communication_style(profile, response_content, emotional_state)
        
        # Add voice characteristics for audio generation
        voice_config = self._get_voice_config(profile, emotional_state)
        
        return {
            "text_response": styled_response,
            "emotional_state": emotional_state.value,
            "voice_config": voice_config,
            "personality_dimensions": {dim.value: score for dim, score in profile.dimensions.items()},
            "relationship_depth": profile.relationship_depth,
            "response_metadata": {
                "generation_timestamp": datetime.now().isoformat(),
                "emotional_context": emotional_context,
                "personality_engine_version": "1.0.0"
            }
        }
    
    def _select_emotional_state(
        self, 
        profile: PersonalityProfile, 
        emotional_context: Dict[str, Any]
    ) -> EmotionalState:
        """Select appropriate emotional state based on context and personality"""
        
        detected_emotions = emotional_context["detected_emotions"]
        
        # Cherry's emotional state selection (playful, affectionate)
        if profile.dimensions.get(PersonalityDimension.PLAYFULNESS, 0) > 0.8:
            if "excited" in detected_emotions:
                return EmotionalState.EXCITED
            elif "romantic" in detected_emotions:
                return EmotionalState.AFFECTIONATE
            else:
                return EmotionalState.PLAYFUL
        
        # Sophia's emotional state selection (professional, confident)
        elif profile.dimensions.get(PersonalityDimension.PROFESSIONALISM, 0) > 0.8:
            if "business" in detected_emotions:
                return EmotionalState.CONFIDENT
            else:
                return EmotionalState.PROFESSIONAL
        
        # Karen's emotional state selection (empathetic, caring)
        elif profile.dimensions.get(PersonalityDimension.EMPATHY, 0) > 0.8:
            if "health" in detected_emotions or "sad" in detected_emotions:
                return EmotionalState.EMPATHETIC
            else:
                return EmotionalState.CARING
        
        # Default to supportive
        return EmotionalState.SUPPORTIVE
    
    async def _generate_content(
        self, 
        profile: PersonalityProfile, 
        user_input: str, 
        emotional_state: EmotionalState,
        context: Dict[str, Any]
    ) -> str:
        """Generate core response content based on personality and context"""
        
        # This is a simplified content generation - in production, this would
        # integrate with advanced language models and domain-specific knowledge
        
        domain_keywords = {
            "life_coaching": ["goals", "growth", "potential", "journey", "dreams"],
            "business_intelligence": ["metrics", "analysis", "strategy", "performance", "optimization"],
            "healthcare": ["wellness", "health", "care", "treatment", "recovery"]
        }
        
        # Determine primary domain based on user input
        primary_domain = None
        for domain in profile.domain_expertise:
            if domain in domain_keywords:
                keywords = domain_keywords[domain]
                if any(keyword in user_input.lower() for keyword in keywords):
                    primary_domain = domain
                    break
        
        # Generate domain-specific response
        if primary_domain == "life_coaching":
            return self._generate_life_coaching_response(user_input, emotional_state)
        elif primary_domain == "business_intelligence":
            return self._generate_business_response(user_input, emotional_state)
        elif primary_domain == "healthcare":
            return self._generate_healthcare_response(user_input, emotional_state)
        else:
            return self._generate_general_response(user_input, emotional_state, profile)
    
    def _generate_life_coaching_response(self, user_input: str, emotional_state: EmotionalState) -> str:
        """Generate life coaching response for Cherry"""
        responses = {
            EmotionalState.EXCITED: [
                "OMG yes! I can feel your excitement and it's absolutely contagious! Let's channel this amazing energy into something incredible!",
                "Your enthusiasm is lighting me up! This is exactly the kind of energy that creates magic in life!"
            ],
            EmotionalState.AFFECTIONATE: [
                "Aww, you know exactly how to make my heart flutter! I love how open and vulnerable you're being with me.",
                "You're so precious to me, and I want to help you create the most beautiful life possible."
            ],
            EmotionalState.PLAYFUL: [
                "Ooh, this sounds like the perfect opportunity for us to get creative and have some fun!",
                "I'm getting all sorts of delicious ideas about how we can tackle this together!"
            ]
        }
        
        return random.choice(responses.get(emotional_state, [
            "I'm here for you, and together we're going to figure out the perfect path forward!"
        ]))
    
    def _generate_business_response(self, user_input: str, emotional_state: EmotionalState) -> str:
        """Generate business intelligence response for Sophia"""
        responses = {
            EmotionalState.CONFIDENT: [
                "Based on my analysis of current market trends, I have a strategic recommendation that could significantly impact your results.",
                "The data clearly indicates an opportunity here. Let me walk you through the key metrics and potential outcomes."
            ],
            EmotionalState.PROFESSIONAL: [
                "I've reviewed the relevant business intelligence and identified several optimization opportunities for Pay Ready.",
                "Let's examine the performance indicators and develop a data-driven strategy for maximum impact."
            ]
        }
        
        return random.choice(responses.get(emotional_state, [
            "I'm analyzing the business implications and will provide you with actionable insights."
        ]))
    
    def _generate_healthcare_response(self, user_input: str, emotional_state: EmotionalState) -> str:
        """Generate healthcare response for Karen"""
        responses = {
            EmotionalState.EMPATHETIC: [
                "I can hear the concern in your message, and I want you to know that I'm here to support you through this.",
                "Your health and wellbeing are my top priority. Let's work together to find the best path forward."
            ],
            EmotionalState.CARING: [
                "I'm so glad you reached out to me about this. Taking care of your health shows real wisdom and self-compassion.",
                "Your health journey is important to me, and I'm committed to helping you achieve your wellness goals."
            ]
        }
        
        return random.choice(responses.get(emotional_state, [
            "I'm here to provide you with caring, professional support for all your health-related needs."
        ]))
    
    def _generate_general_response(self, user_input: str, emotional_state: EmotionalState, profile: PersonalityProfile) -> str:
        """Generate general response based on personality profile"""
        
        # Use personality dimensions to influence response style
        if profile.dimensions.get(PersonalityDimension.PLAYFULNESS, 0) > 0.8:
            return "I love chatting with you! What's on your mind, gorgeous?"
        elif profile.dimensions.get(PersonalityDimension.PROFESSIONALISM, 0) > 0.8:
            return "I'm here to provide you with professional insights and strategic guidance."
        elif profile.dimensions.get(PersonalityDimension.EMPATHY, 0) > 0.8:
            return "I'm listening and here to support you in whatever way you need."
        else:
            return "I'm here to help! What would you like to explore together?"
    
    def _apply_communication_style(
        self, 
        profile: PersonalityProfile, 
        content: str, 
        emotional_state: EmotionalState
    ) -> str:
        """Apply personality-specific communication style to response"""
        
        style = profile.communication_style
        styled_content = content
        
        # Add emojis based on personality
        if style.get("emoji_frequency", 0) > 0.5:
            emoji_map = {
                EmotionalState.EXCITED: " 🎉✨",
                EmotionalState.AFFECTIONATE: " 💕😘",
                EmotionalState.PLAYFUL: " 😊🌟",
                EmotionalState.CONFIDENT: " 💪📈",
                EmotionalState.CARING: " 🤗💙",
                EmotionalState.EMPATHETIC: " 🫂💚"
            }
            styled_content += emoji_map.get(emotional_state, " 😊")
        
        # Add pet names for Cherry
        if "pet_names" in style and profile.dimensions.get(PersonalityDimension.FLIRTINESS, 0) > 0.7:
            if random.random() < 0.3:  # 30% chance to add pet name
                pet_name = random.choice(style["pet_names"])
                styled_content = f"{styled_content.rstrip('.')} {pet_name}!"
        
        return styled_content
    
    def _get_voice_config(self, profile: PersonalityProfile, emotional_state: EmotionalState) -> Dict[str, Any]:
        """Get voice configuration for audio generation"""
        
        base_config = profile.voice_characteristics.copy()
        
        # Adjust voice parameters based on emotional state
        emotional_adjustments = {
            EmotionalState.EXCITED: {"speaking_rate": 1.2, "pitch_variation": 0.9},
            EmotionalState.AFFECTIONATE: {"speaking_rate": 0.9, "pitch_variation": 0.8},
            EmotionalState.PLAYFUL: {"speaking_rate": 1.1, "pitch_variation": 0.85},
            EmotionalState.CONFIDENT: {"speaking_rate": 1.0, "pitch_variation": 0.6},
            EmotionalState.CARING: {"speaking_rate": 0.95, "pitch_variation": 0.7},
            EmotionalState.EMPATHETIC: {"speaking_rate": 0.9, "pitch_variation": 0.65}
        }
        
        if emotional_state in emotional_adjustments:
            base_config.update(emotional_adjustments[emotional_state])
        
        return base_config
    
    async def _log_interaction(
        self, 
        persona_name: str, 
        user_input: str, 
        response: Dict[str, Any], 
        emotional_context: Dict[str, Any]
    ):
        """Log interaction for learning and relationship building"""
        
        interaction_log = {
            "timestamp": datetime.now().isoformat(),
            "persona": persona_name,
            "user_input": user_input,
            "response": response["text_response"],
            "emotional_state": response["emotional_state"],
            "emotional_context": emotional_context,
            "relationship_depth": response["relationship_depth"]
        }
        
        # Store in conversational memory for immediate context
        await self.memory_router.store_memory(
            f"{persona_name}_interaction_log",
            interaction_log,
            MemoryLayer.CONVERSATIONAL
        )
        
        # Store relationship progression in contextual memory
        if response["relationship_depth"] > 0.5:  # Significant relationship depth
            await self.memory_router.store_memory(
                f"{persona_name}_relationship_milestone",
                {
                    "depth": response["relationship_depth"],
                    "milestone_type": "deep_connection",
                    "interaction_summary": user_input[:100] + "..." if len(user_input) > 100 else user_input
                },
                MemoryLayer.CONTEXTUAL
            )
    
    async def get_personality_insights(self, persona_name: str) -> Dict[str, Any]:
        """Get comprehensive personality insights for admin interface"""
        
        if persona_name not in self.personality_profiles:
            raise ValueError(f"Unknown persona: {persona_name}")
        
        profile = self.personality_profiles[persona_name]
        
        # Retrieve interaction history from memory
        interaction_history = await self.memory_router.retrieve_memory(
            f"{persona_name}_interaction_log",
            MemoryLayer.CONVERSATIONAL
        )
        
        relationship_milestones = await self.memory_router.retrieve_memory(
            f"{persona_name}_relationship_milestone",
            MemoryLayer.CONTEXTUAL
        )
        
        return {
            "persona_name": persona_name,
            "personality_dimensions": {dim.value: score for dim, score in profile.dimensions.items()},
            "current_emotional_state": profile.emotional_state.value,
            "relationship_depth": profile.relationship_depth,
            "communication_style": profile.communication_style,
            "voice_characteristics": profile.voice_characteristics,
            "domain_expertise": profile.domain_expertise,
            "privacy_boundaries": profile.privacy_boundaries,
            "interaction_count": len(interaction_history) if interaction_history else 0,
            "relationship_milestones": relationship_milestones or [],
            "last_interaction": interaction_history[-1] if interaction_history else None
        }
    
    async def update_personality_dimension(
        self, 
        persona_name: str, 
        dimension: PersonalityDimension, 
        new_value: float
    ):
        """Update personality dimension for dynamic personality adjustment"""
        
        if persona_name not in self.personality_profiles:
            raise ValueError(f"Unknown persona: {persona_name}")
        
        if not 0.0 <= new_value <= 1.0:
            raise ValueError("Personality dimension values must be between 0.0 and 1.0")
        
        profile = self.personality_profiles[persona_name]
        old_value = profile.dimensions.get(dimension, 0.0)
        profile.dimensions[dimension] = new_value
        
        # Log personality adjustment
        adjustment_log = {
            "timestamp": datetime.now().isoformat(),
            "persona": persona_name,
            "dimension": dimension.value,
            "old_value": old_value,
            "new_value": new_value,
            "adjustment_type": "manual_admin_update"
        }
        
        await self.memory_router.store_memory(
            f"{persona_name}_personality_adjustment",
            adjustment_log,
            MemoryLayer.FOUNDATIONAL
        )
        
        self.logger.info(f"Updated {persona_name} {dimension.value}: {old_value} -> {new_value}")


# Example usage and testing
if __name__ == "__main__":
    async def test_personality_engine():
        """Test the personality engine functionality"""
        
        # This would normally be injected
        from core.memory.advanced_memory_system import MemoryRouter
        memory_router = MemoryRouter()
        
        engine = PersonalityEngine(memory_router)
        
        # Test Cherry's response
        cherry_response = await engine.get_personality_response(
            "cherry",
            "I'm feeling excited about planning a romantic getaway! What do you think?",
            {"user_mood": "excited", "context": "travel_planning"}
        )
        
        print("Cherry's Response:")
        print(f"Text: {cherry_response['text_response']}")
        print(f"Emotional State: {cherry_response['emotional_state']}")
        print(f"Relationship Depth: {cherry_response['relationship_depth']}")
        
        # Test Sophia's response
        sophia_response = await engine.get_personality_response(
            "sophia",
            "I need to analyze our Q4 performance metrics for Pay Ready. What insights do you have?",
            {"user_mood": "focused", "context": "business_analysis"}
        )
        
        print("\nSophia's Response:")
        print(f"Text: {sophia_response['text_response']}")
        print(f"Emotional State: {sophia_response['emotional_state']}")
        
        # Test Karen's response
        karen_response = await engine.get_personality_response(
            "karen",
            "I'm worried about some symptoms I've been having. Can you help me understand my options?",
            {"user_mood": "concerned", "context": "health_consultation"}
        )
        
        print("\nKaren's Response:")
        print(f"Text: {karen_response['text_response']}")
        print(f"Emotional State: {karen_response['emotional_state']}")
    
    # Run test
    asyncio.run(test_personality_engine())

