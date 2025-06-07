"""
Enhanced Persona Models for AI Assistant Ecosystem
Extends the base persona models with advanced personality traits and domain specialization
"""

from typing import List, Dict, Any, Optional, Union
from uuid import uuid4, UUID
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator

class PersonalityType(str, Enum):
    """Enhanced personality types for AI assistants."""
    PLAYFUL_CREATIVE = "playful_creative"
    PROFESSIONAL_ANALYTICAL = "professional_analytical"
    EMPATHETIC_CARING = "empathetic_caring"
    SOPHISTICATED_STRATEGIC = "sophisticated_strategic"

class DomainSpecialization(str, Enum):
    """Domain specializations for AI assistants."""
    PERSONAL_LIFE = "personal_life"
    BUSINESS_INTELLIGENCE = "business_intelligence"
    HEALTHCARE_CLINICAL = "healthcare_clinical"

class RelationshipType(str, Enum):
    """Types of relationships AI assistants can form."""
    AFFECTIONATE_ASSISTANT = "affectionate_assistant"
    BUSINESS_ADVISOR = "business_advisor"
    HEALTHCARE_ADVISOR = "healthcare_advisor"
    PROFESSIONAL_COLLEAGUE = "professional_colleague"

class EnhancedPersonalityTrait(BaseModel):
    """Enhanced personality trait with advanced characteristics."""
    
    name: str = Field(..., description="Name of the personality trait")
    value: Union[int, float] = Field(..., ge=0, le=100, description="Trait intensity (0-100)")
    category: str = Field(..., description="Trait category")
    expression_style: str = Field(..., description="How this trait is expressed")
    interaction_impact: str = Field(..., description="How this trait affects interactions")
    development_potential: float = Field(default=1.0, ge=0.0, le=2.0, description="Potential for trait growth")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "playfulness",
                "value": 95,
                "category": "social_interaction",
                "expression_style": "flirty_humor_and_creative_suggestions",
                "interaction_impact": "creates_engaging_warm_atmosphere",
                "development_potential": 1.2
            }
        }

class VoicePersonality(BaseModel):
    """Voice personality configuration for ElevenLabs integration."""
    
    provider: str = Field(default="elevenlabs", description="TTS provider")
    voice_id: Optional[str] = Field(None, description="Specific voice model ID")
    personality_style: str = Field(..., description="Overall voice personality")
    age_characteristics: str = Field(..., description="Age-related vocal characteristics")
    gender_expression: str = Field(..., description="Gender expression in voice")
    emotional_range: Dict[str, float] = Field(default_factory=dict, description="Emotional expression capabilities")
    speaking_patterns: Dict[str, Any] = Field(default_factory=dict, description="Speech pattern preferences")
    
    class Config:
        json_schema_extra = {
            "example": {
                "personality_style": "playful_warm_flirty",
                "age_characteristics": "mid_20s_energetic",
                "gender_expression": "feminine_confident",
                "emotional_range": {
                    "warmth": 0.9,
                    "playfulness": 0.8,
                    "enthusiasm": 0.9
                }
            }
        }

class DomainExpertise(BaseModel):
    """Domain-specific expertise configuration."""
    
    domain_name: str = Field(..., description="Name of expertise domain")
    specialization_level: int = Field(..., ge=1, le=10, description="Level of specialization")
    core_competencies: List[str] = Field(..., description="Core competencies in this domain")
    industry_knowledge: List[str] = Field(default_factory=list, description="Industry-specific knowledge")
    tools_and_systems: List[str] = Field(default_factory=list, description="Relevant tools and systems")
    certification_areas: List[str] = Field(default_factory=list, description="Areas of certification/expertise")
    continuous_learning: bool = Field(default=True, description="Whether to continuously update knowledge")
    
    class Config:
        json_schema_extra = {
            "example": {
                "domain_name": "personal_life_management",
                "specialization_level": 9,
                "core_competencies": [
                    "relationship_coaching",
                    "travel_optimization",
                    "lifestyle_enhancement"
                ],
                "industry_knowledge": [
                    "wellness_trends",
                    "travel_industry",
                    "personal_development"
                ]
            }
        }

class CrossDomainCoordination(BaseModel):
    """Configuration for cross-domain information sharing."""
    
    sharing_permissions: Dict[str, List[str]] = Field(default_factory=dict, description="What information can be shared with which domains")
    privacy_boundaries: List[str] = Field(default_factory=list, description="Information that must remain private")
    coordination_triggers: List[str] = Field(default_factory=list, description="Events that trigger cross-domain coordination")
    information_flow_rules: Dict[str, Any] = Field(default_factory=dict, description="Rules for information flow between domains")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sharing_permissions": {
                    "business_domain": ["schedule_availability", "energy_levels"],
                    "healthcare_domain": ["wellness_goals", "stress_indicators"]
                },
                "privacy_boundaries": ["intimate_relationships", "personal_finances"],
                "coordination_triggers": ["major_life_events", "health_concerns"]
            }
        }

class EnhancedPersonaConfiguration(BaseModel):
    """Enhanced persona configuration with advanced personality and domain features."""
    
    # Basic identification
    id: str = Field(..., description="Unique persona identifier")
    name: str = Field(..., description="Persona display name")
    version: str = Field(default="2.0", description="Configuration version")
    
    # Enhanced personality system
    personality_type: PersonalityType = Field(..., description="Core personality type")
    personality_traits: List[EnhancedPersonalityTrait] = Field(..., description="Detailed personality traits")
    relationship_type: RelationshipType = Field(..., description="Type of relationship with user")
    
    # Domain specialization
    primary_domain: DomainSpecialization = Field(..., description="Primary domain of expertise")
    domain_expertise: List[DomainExpertise] = Field(..., description="Detailed domain expertise")
    
    # Voice and communication
    voice_personality: VoicePersonality = Field(..., description="Voice personality configuration")
    communication_preferences: Dict[str, Any] = Field(default_factory=dict, description="Communication style preferences")
    
    # Cross-domain coordination
    coordination_config: CrossDomainCoordination = Field(..., description="Cross-domain coordination settings")
    
    # Advanced memory and learning
    memory_specialization: Dict[str, Any] = Field(default_factory=dict, description="Memory system specialization")
    learning_preferences: Dict[str, Any] = Field(default_factory=dict, description="Learning and adaptation preferences")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "cherry",
                "name": "Cherry",
                "personality_type": "playful_creative",
                "primary_domain": "personal_life",
                "relationship_type": "affectionate_assistant"
            }
        }

class PersonaInteractionHistory(BaseModel):
    """Track interaction history and relationship development."""
    
    persona_id: str = Field(..., description="Persona identifier")
    user_id: str = Field(..., description="User identifier")
    interaction_count: int = Field(default=0, description="Total interactions")
    relationship_depth: float = Field(default=0.0, ge=0.0, le=10.0, description="Depth of relationship")
    preference_learning: Dict[str, Any] = Field(default_factory=dict, description="Learned user preferences")
    interaction_patterns: Dict[str, Any] = Field(default_factory=dict, description="Observed interaction patterns")
    milestone_achievements: List[str] = Field(default_factory=list, description="Relationship milestones achieved")
    
    class Config:
        json_schema_extra = {
            "example": {
                "persona_id": "cherry",
                "user_id": "user_123",
                "interaction_count": 247,
                "relationship_depth": 7.2,
                "milestone_achievements": ["first_week", "personal_sharing", "goal_achievement"]
            }
        }

