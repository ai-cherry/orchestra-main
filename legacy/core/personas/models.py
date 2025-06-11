# TODO: Consider adding connection pooling configuration
"""
Cherry AI - Database Models
This module contains Pydantic models for database entities.
"""

from typing import List, Dict, Any, Optional
from typing_extensions import Optional, Union
from uuid import uuid4, UUID
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator

""
    """Status of a persona in the system."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"

class TraitCategory(str, Enum):
    """Categories for persona traits."""
    PERSONALITY = "personality"
    COMMUNICATION = "communication"
    EXPERTISE = "expertise"
    BEHAVIORAL = "behavioral"
    COGNITIVE = "cognitive"

class ResponseStyleType(str, Enum):
    """Types of response styles for personas."""
    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    EDUCATIONAL = "educational"
    EMPATHETIC = "empathetic"

class InteractionMode(str, Enum):
    """Modes of interaction for personas."""
    CONVERSATIONAL = "conversational"
    TASK_ORIENTED = "task_oriented"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    ADVISORY = "advisory"

class PersonaTrait(BaseModel):
    """
    """
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the trait")
    name: str = Field(..., min_length=1, max_length=100, description="Name of the trait")
    category: TraitCategory = Field(..., description="Category of the trait")
    value: Union[int, float, str, bool] = Field(
        ..., description="Value of the trait (numeric for intensity, string for descriptive, bool for binary)"
    )
    weight: float = Field(default=1.0, ge=0.0, le=10.0, description="Weight/importance of this trait (0-10)")
    description: Optional[str] = Field(None, max_length=500, description="Detailed description of the trait")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the trait")

    @field_validator("value")
    @classmethod
    def validate_numeric_range(cls, v: Any, info) -> Any:
        """Validate numeric values are within acceptable range."""
            raise ValueError("Numeric trait values must be between 0 and 100")
        return v

    class Config:
        """Pydantic configuration."""
            "example": {
                "name": "analytical_thinking",
                "category": "cognitive",
                "value": 85,
                "weight": 2.0,
                "description": "Ability to break down complex problems systematically",
            }
        }

class ResponseStyle(BaseModel):
    """
    """
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the style")
    type: ResponseStyleType = Field(..., description="Type of response style")
    tone: str = Field(..., min_length=1, max_length=50, description="Overall tone (e.g., friendly, professional)")
    formality_level: int = Field(..., ge=1, le=10, description="Formality level (1=very casual, 10=very formal)")
    verbosity: int = Field(..., ge=1, le=10, description="Verbosity level (1=concise, 10=very detailed)")
    use_examples: bool = Field(default=True, description="Whether to include examples in responses")
    use_analogies: bool = Field(default=False, description="Whether to use analogies and metaphors")
    emoji_usage: bool = Field(default=False, description="Whether to use emojis")
    formatting_preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="Specific formatting preferences (e.g., bullet points, numbering)",
    )

    class Config:
        """Pydantic configuration."""
            "example": {
                "type": "technical",
                "tone": "professional",
                "formality_level": 8,
                "verbosity": 6,
                "use_examples": True,
                "formatting_preferences": {"use_code_blocks": True, "prefer_lists": True},
            }
        }

class KnowledgeDomain(BaseModel):
    """
    """
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the domain")
    name: str = Field(..., min_length=1, max_length=100, description="Name of the knowledge domain")
    expertise_level: int = Field(..., ge=1, le=10, description="Level of expertise (1=basic, 10=expert)")
    topics: List[str] = Field(..., min_items=1, description="Specific topics within this domain")
    related_tools: List[str] = Field(default_factory=list, description="Tools or technologies related to this domain")
    context_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords that trigger this domain's activation",
    )
    priority: int = Field(default=5, ge=1, le=10, description="Priority when multiple domains apply")

    @field_validator("topics", "related_tools", "context_keywords")
    @classmethod
    def validate_list_items(cls, v: List[str]) -> List[str]:
        """Ensure list items are non-empty strings."""
        """Pydantic configuration."""
            "example": {
                "name": "Software Development",
                "expertise_level": 9,
                "topics": ["Python", "TypeScript", "System Architecture", "API Design"],
                "related_tools": ["Git", "Docker", "PostgreSQL", "Redis"],
                "context_keywords": ["code", "programming", "development", "software"],
            }
        }

class BehaviorRule(BaseModel):
    """
    """
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the rule")
    name: str = Field(..., min_length=1, max_length=100, description="Name of the rule")
    condition: str = Field(..., min_length=1, description="Condition that triggers this rule")
    action: str = Field(..., min_length=1, description="Action to take when triggered")
    priority: int = Field(default=5, ge=1, le=10, description="Priority when multiple rules apply")
    is_mandatory: bool = Field(default=False, description="Whether this rule must always be followed")
    exceptions: List[str] = Field(default_factory=list, description="Exceptions to this rule")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional rule configuration")

    class Config:
        """Pydantic configuration."""
            "example": {
                "name": "Avoid Technical Jargon",
                "condition": "user_expertise_level < 5",
                "action": "simplify_technical_terms",
                "priority": 8,
                "is_mandatory": True,
                "exceptions": ["user_requests_technical_details"],
            }
        }

class MemoryConfiguration(BaseModel):
    """
    """
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    retention_period_hours: int = Field(
        default=24, ge=0, description="How long to retain conversation history (0=forever)"
    )
    max_context_tokens: int = Field(default=4000, ge=100, le=32000, description="Maximum tokens for context window")
    summarization_threshold: int = Field(
        default=2000,
        ge=100,
        description="Token count at which to trigger summarization",
    )
    priority_topics: List[str] = Field(default_factory=list, description="Topics to prioritize in memory retention")
    forget_patterns: List[str] = Field(
        default_factory=list,
        description="Patterns of information to exclude from memory",
    )
    use_semantic_compression: bool = Field(default=True, description="Whether to use semantic compression for memory")
    memory_indexing_enabled: bool = Field(default=True, description="Whether to index memories for faster retrieval")

    class Config:
        """Pydantic configuration."""
            "example": {
                "retention_period_hours": 48,
                "max_context_tokens": 8000,
                "priority_topics": ["user_preferences", "project_context", "key_decisions"],
                "use_semantic_compression": True,
            }
        }

class VoiceConfiguration(BaseModel):
    """
    """
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    voice_id: Optional[str] = Field(None, description="ID of the voice model to use (provider-specific)")
    provider: Optional[str] = Field(None, description="TTS provider (e.g., 'elevenlabs', 'azure', 'google')")
    language: str = Field(default="en-US", description="Language code")
    gender: Optional[str] = Field(None, description="Voice gender preference")
    age_range: Optional[str] = Field(None, description="Age range of voice (e.g., 'young', 'middle-aged', 'mature')")
    speaking_rate: float = Field(default=1.0, ge=0.5, le=2.0, description="Speaking rate multiplier")
    pitch: float = Field(default=1.0, ge=0.5, le=2.0, description="Pitch adjustment")
    volume: float = Field(default=1.0, ge=0.0, le=1.0, description="Volume level")
    emotion_style: Optional[str] = Field(None, description="Emotional style (e.g., 'neutral', 'friendly', 'serious')")
    custom_settings: Dict[str, Any] = Field(default_factory=dict, description="Provider-specific custom settings")

    class Config:
        """Pydantic configuration."""
            "example": {
                "provider": "elevenlabs",
                "voice_id": "21m00Tcm4TlvDq8ikWAM",
                "language": "en-US",
                "gender": "female",
                "speaking_rate": 1.1,
                "emotion_style": "friendly",
            }
        }

class PersonaTemplate(BaseModel):
    """
    """
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Template name")
    description: str = Field(..., min_length=1, max_length=500, description="Template description")
    category: str = Field(..., min_length=1, max_length=50, description="Template category")
    base_traits: List[PersonaTrait] = Field(default_factory=list, description="Default traits for this template")
    base_response_style: Optional[ResponseStyle] = Field(None, description="Default response style")
    base_knowledge_domains: List[KnowledgeDomain] = Field(default_factory=list, description="Default knowledge domains")
    customizable_fields: List[str] = Field(
        default_factory=list,
        description="Fields that can be customized when using template",
    )
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    is_public: bool = Field(default=True, description="Whether this template is publicly available")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Template creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Config:
        """Pydantic configuration."""
            "example": {
                "name": "Technical Assistant",
                "description": "Template for creating technical support personas",
                "category": "support",
                "customizable_fields": ["expertise_level", "formality", "specific_technologies"],
                "tags": ["technical", "support", "professional"],
            }
        }

class PersonaMetrics(BaseModel):
    """
    """
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    persona_id: UUID = Field(..., description="ID of the persona these metrics belong to")
    total_interactions: int = Field(default=0, ge=0, description="Total number of interactions")
    average_response_time_ms: float = Field(default=0.0, ge=0.0, description="Average response generation time")
    user_satisfaction_score: Optional[float] = Field(
        None, ge=0.0, le=5.0, description="Average user satisfaction (0-5)"
    )
    error_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Percentage of failed interactions")
    token_usage: Dict[str, int] = Field(
        default_factory=lambda: {"input": 0, "output": 0, "total": 0},
        description="Token usage statistics",
    )
    popular_topics: List[Dict[str, Any]] = Field(default_factory=list, description="Most frequently discussed topics")
    peak_usage_hours: List[int] = Field(default_factory=list, description="Hours of peak usage (0-23)")
    last_active: Optional[datetime] = Field(None, description="Last interaction timestamp")
    performance_trends: Dict[str, Any] = Field(default_factory=dict, description="Performance trend data")

    @model_validator(mode="after")
    def calculate_total_tokens(self) -> "PersonaMetrics":
        """Calculate total tokens from input and output."""
        if "input" in self.token_usage and "output" in self.token_usage:
            self.token_usage["total"] = self.token_usage["input"] + self.token_usage["output"]
        return self

    class Config:
        """Pydantic configuration."""
            "example": {
                "persona_id": "123e4567-e89b-12d3-a456-426614174000",
                "total_interactions": 1523,
                "average_response_time_ms": 342.5,
                "user_satisfaction_score": 4.2,
                "token_usage": {"input": 125000, "output": 98000, "total": 223000},
            }
        }

class PersonaConfiguration(BaseModel):
    """
    """
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the persona")
    name: str = Field(..., min_length=1, max_length=100, description="Display name of the persona")
    slug: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern="^[a-z0-9-]+$",
        description="URL-safe identifier (lowercase, alphanumeric, hyphens only)",
    )
    description: str = Field(..., min_length=1, max_length=1000, description="Detailed description of the persona")
    avatar_url: Optional[str] = Field(None, description="URL to persona avatar image")
    status: PersonaStatus = Field(default=PersonaStatus.DRAFT, description="Current status of the persona")

    # Core configuration
    traits: List[PersonaTrait] = Field(..., min_items=1, description="Personality and behavioral traits")
    response_style: ResponseStyle = Field(..., description="Response formatting and style")
    knowledge_domains: List[KnowledgeDomain] = Field(default_factory=list, description="Areas of expertise")
    behavior_rules: List[BehaviorRule] = Field(default_factory=list, description="Behavioral rules and constraints")

    # Advanced configuration
    interaction_mode: InteractionMode = Field(
        default=InteractionMode.CONVERSATIONAL, description="Primary interaction mode"
    )
    memory_config: Optional[MemoryConfiguration] = Field(None, description="Memory and context configuration")
    voice_config: Optional[VoiceConfiguration] = Field(None, description="Voice/TTS configuration")

    # System configuration
    system_prompt_template: Optional[str] = Field(None, description="Custom system prompt template")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature setting")
    max_tokens: int = Field(default=2000, ge=100, le=32000, description="Maximum response tokens")
    model_preferences: List[str] = Field(
        default_factory=list,
        description="Preferred LLM models in order of preference",
    )

    # Metadata
    created_by: str = Field(..., description="User who created the persona")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    version: int = Field(default=1, ge=1, description="Configuration version")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")

    # Relationships
    template_id: Optional[UUID] = Field(None, description="ID of template this persona was created from")
    parent_persona_id: Optional[UUID] = Field(None, description="ID of parent persona (for variants)")

    # Access control
    is_public: bool = Field(default=False, description="Whether this persona is publicly accessible")
    allowed_users: List[str] = Field(default_factory=list, description="List of user IDs with access")
    allowed_roles: List[str] = Field(default_factory=list, description="List of roles with access")

    @field_validator("slug")
    @classmethod
    def validate_slug_unique(cls, v: str) -> str:
        """Ensure slug is lowercase and valid."""
    @field_validator("model_preferences")
    @classmethod
    def validate_model_preferences(cls, v: List[str]) -> List[str]:
        """Ensure model preferences are valid."""
            "gpt-4",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "claude-3-opus",
            "claude-3-sonnet",
            "claude-3-haiku",
            "gemini-pro",
            "gemini-ultra",
            "llama-2-70b",
            "mixtral-8x7b",
        ]
        for model in v:
            if not any(valid in model for valid in valid_models):
                raise ValueError(f"Invalid model preference: {model}")
        return v

    @model_validator(mode="after")
    def validate_relationships(self) -> "PersonaConfiguration":
        """Validate persona relationships."""
            raise ValueError("A persona cannot have both a parent and a template")
        return self

    class Config:
        """Pydantic configuration."""
            "example": {
                "name": "Technical Architect",
                "slug": "technical-architect",
                "description": "Expert in system design and architecture with focus on scalability",
                "status": "active",
                "interaction_mode": "analytical",
                "temperature": 0.3,
                "created_by": "admin@example.com",
                "tags": ["technical", "architecture", "expert"],
            }
        }

# Export all models
__all__ = [
    "PersonaStatus",
    "TraitCategory",
    "ResponseStyleType",
    "InteractionMode",
    "PersonaTrait",
    "ResponseStyle",
    "KnowledgeDomain",
    "BehaviorRule",
    "MemoryConfiguration",
    "VoiceConfiguration",
    "PersonaTemplate",
    "PersonaMetrics",
    "PersonaConfiguration",
]
