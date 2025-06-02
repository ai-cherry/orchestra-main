"""
Unit tests for persona configuration models.

Tests all Pydantic models for proper validation, serialization,
and business logic.
"""

from datetime import datetime, timedelta
from typing import Any, Dict
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from core.personas.models import (
    BehaviorRule,
    InteractionMode,
    KnowledgeDomain,
    MemoryConfiguration,
    PersonaConfiguration,
    PersonaMetrics,
    PersonaStatus,
    PersonaTemplate,
    PersonaTrait,
    ResponseStyle,
    ResponseStyleType,
    TraitCategory,
    VoiceConfiguration,
)

class TestPersonaTrait:
    """Test PersonaTrait model validation and behavior."""

    def test_valid_trait_creation(self):
        """Test creating a valid persona trait."""
        trait = PersonaTrait(
            name="analytical_thinking",
            category=TraitCategory.COGNITIVE,
            value=85,
            weight=2.0,
            description="Strong analytical capabilities",
        )
        assert trait.name == "analytical_thinking"
        assert trait.category == TraitCategory.COGNITIVE
        assert trait.value == 85
        assert trait.weight == 2.0
        assert isinstance(trait.id, UUID)

    def test_numeric_value_validation(self):
        """Test numeric value range validation."""
        # Valid numeric value
        trait = PersonaTrait(name="confidence", category=TraitCategory.PERSONALITY, value=75)
        assert trait.value == 75

        # Invalid numeric value (too high)
        with pytest.raises(ValidationError) as exc_info:
            PersonaTrait(name="confidence", category=TraitCategory.PERSONALITY, value=150)
        assert "Numeric trait values must be between 0 and 100" in str(exc_info.value)

    def test_string_and_bool_values(self):
        """Test traits with string and boolean values."""
        # String value
        trait_str = PersonaTrait(
            name="communication_style",
            category=TraitCategory.COMMUNICATION,
            value="direct",
        )
        assert trait_str.value == "direct"

        # Boolean value
        trait_bool = PersonaTrait(name="uses_humor", category=TraitCategory.BEHAVIORAL, value=True)
        assert trait_bool.value is True

    def test_weight_validation(self):
        """Test weight range validation."""
        # Valid weight
        trait = PersonaTrait(name="empathy", category=TraitCategory.PERSONALITY, value=80, weight=5.5)
        assert trait.weight == 5.5

        # Invalid weight (too high)
        with pytest.raises(ValidationError):
            PersonaTrait(name="empathy", category=TraitCategory.PERSONALITY, value=80, weight=15)

class TestResponseStyle:
    """Test ResponseStyle model validation and behavior."""

    def test_valid_response_style(self):
        """Test creating a valid response style."""
        style = ResponseStyle(
            type=ResponseStyleType.TECHNICAL,
            tone="professional",
            formality_level=8,
            verbosity=6,
            use_examples=True,
            formatting_preferences={"use_code_blocks": True},
        )
        assert style.type == ResponseStyleType.TECHNICAL
        assert style.formality_level == 8
        assert style.formatting_preferences["use_code_blocks"] is True

    def test_level_validations(self):
        """Test formality and verbosity level validations."""
        # Valid levels
        style = ResponseStyle(
            type=ResponseStyleType.CASUAL,
            tone="friendly",
            formality_level=3,
            verbosity=7,
        )
        assert style.formality_level == 3
        assert style.verbosity == 7

        # Invalid formality level
        with pytest.raises(ValidationError):
            ResponseStyle(
                type=ResponseStyleType.FORMAL,
                tone="professional",
                formality_level=15,
                verbosity=5,
            )

        # Invalid verbosity level
        with pytest.raises(ValidationError):
            ResponseStyle(
                type=ResponseStyleType.FORMAL,
                tone="professional",
                formality_level=5,
                verbosity=0,
            )

class TestKnowledgeDomain:
    """Test KnowledgeDomain model validation and behavior."""

    def test_valid_knowledge_domain(self):
        """Test creating a valid knowledge domain."""
        domain = KnowledgeDomain(
            name="Software Development",
            expertise_level=9,
            topics=["Python", "TypeScript", "API Design"],
            related_tools=["Git", "Docker"],
            context_keywords=["code", "programming"],
            priority=8,
        )
        assert domain.name == "Software Development"
        assert domain.expertise_level == 9
        assert len(domain.topics) == 3
        assert "Python" in domain.topics

    def test_list_validation(self):
        """Test list field validation."""
        # Empty topics list should fail
        with pytest.raises(ValidationError):
            KnowledgeDomain(
                name="Empty Domain",
                expertise_level=5,
                topics=[],  # Empty list not allowed
            )

        # Whitespace-only items should be filtered
        domain = KnowledgeDomain(
            name="Test Domain",
            expertise_level=5,
            topics=["Valid", "  ", "Also Valid"],
            related_tools=["Tool1", "", "Tool2"],
        )
        assert len(domain.topics) == 2
        assert "Valid" in domain.topics
        assert "Also Valid" in domain.topics
        assert len(domain.related_tools) == 2

class TestBehaviorRule:
    """Test BehaviorRule model validation and behavior."""

    def test_valid_behavior_rule(self):
        """Test creating a valid behavior rule."""
        rule = BehaviorRule(
            name="Simplify for Beginners",
            condition="user_expertise_level < 3",
            action="use_simple_language",
            priority=9,
            is_mandatory=True,
            exceptions=["technical_mode_enabled"],
        )
        assert rule.name == "Simplify for Beginners"
        assert rule.is_mandatory is True
        assert len(rule.exceptions) == 1

    def test_priority_validation(self):
        """Test priority range validation."""
        # Valid priority
        rule = BehaviorRule(
            name="Test Rule",
            condition="always",
            action="test_action",
            priority=10,
        )
        assert rule.priority == 10

        # Invalid priority
        with pytest.raises(ValidationError):
            BehaviorRule(
                name="Test Rule",
                condition="always",
                action="test_action",
                priority=11,
            )

class TestMemoryConfiguration:
    """Test MemoryConfiguration model validation and behavior."""

    def test_valid_memory_config(self):
        """Test creating a valid memory configuration."""
        config = MemoryConfiguration(
            retention_period_hours=48,
            max_context_tokens=8000,
            summarization_threshold=3000,
            priority_topics=["user_preferences", "key_decisions"],
            use_semantic_compression=True,
        )
        assert config.retention_period_hours == 48
        assert config.max_context_tokens == 8000
        assert len(config.priority_topics) == 2

    def test_token_limits(self):
        """Test token limit validations."""
        # Valid token limits
        config = MemoryConfiguration(max_context_tokens=16000)
        assert config.max_context_tokens == 16000

        # Invalid max tokens (too low)
        with pytest.raises(ValidationError):
            MemoryConfiguration(max_context_tokens=50)

        # Invalid max tokens (too high)
        with pytest.raises(ValidationError):
            MemoryConfiguration(max_context_tokens=64000)

class TestVoiceConfiguration:
    """Test VoiceConfiguration model validation and behavior."""

    def test_valid_voice_config(self):
        """Test creating a valid voice configuration."""
        config = VoiceConfiguration(
            provider="elevenlabs",
            voice_id="test_voice_123",
            language="en-US",
            gender="female",
            speaking_rate=1.2,
            pitch=0.9,
            volume=0.8,
        )
        assert config.provider == "elevenlabs"
        assert config.speaking_rate == 1.2
        assert config.volume == 0.8

    def test_rate_and_pitch_validation(self):
        """Test speaking rate and pitch validations."""
        # Valid rates
        config = VoiceConfiguration(speaking_rate=0.5, pitch=2.0)
        assert config.speaking_rate == 0.5
        assert config.pitch == 2.0

        # Invalid speaking rate
        with pytest.raises(ValidationError):
            VoiceConfiguration(speaking_rate=3.0)

        # Invalid volume
        with pytest.raises(ValidationError):
            VoiceConfiguration(volume=1.5)

class TestPersonaTemplate:
    """Test PersonaTemplate model validation and behavior."""

    def test_valid_template(self):
        """Test creating a valid persona template."""
        trait = PersonaTrait(name="helpful", category=TraitCategory.PERSONALITY, value=90)
        style = ResponseStyle(
            type=ResponseStyleType.EDUCATIONAL,
            tone="friendly",
            formality_level=5,
            verbosity=7,
        )

        template = PersonaTemplate(
            name="Teacher Assistant",
            description="Template for educational personas",
            category="education",
            base_traits=[trait],
            base_response_style=style,
            customizable_fields=["subject_expertise", "grade_level"],
            tags=["education", "teaching"],
        )
        assert template.name == "Teacher Assistant"
        assert len(template.base_traits) == 1
        assert template.base_response_style.type == ResponseStyleType.EDUCATIONAL

    def test_timestamp_defaults(self):
        """Test that timestamps are set automatically."""
        template = PersonaTemplate(
            name="Test Template",
            description="Test",
            category="test",
        )
        assert isinstance(template.created_at, datetime)
        assert isinstance(template.updated_at, datetime)
        assert template.created_at <= template.updated_at

class TestPersonaMetrics:
    """Test PersonaMetrics model validation and behavior."""

    def test_valid_metrics(self):
        """Test creating valid persona metrics."""
        persona_id = uuid4()
        metrics = PersonaMetrics(
            persona_id=persona_id,
            total_interactions=1500,
            average_response_time_ms=250.5,
            user_satisfaction_score=4.3,
            error_rate=0.02,
            token_usage={"input": 50000, "output": 40000},
        )
        assert metrics.persona_id == persona_id
        assert metrics.total_interactions == 1500
        assert metrics.token_usage["total"] == 90000  # Auto-calculated

    def test_token_calculation(self):
        """Test automatic total token calculation."""
        metrics = PersonaMetrics(
            persona_id=uuid4(),
            token_usage={"input": 1000, "output": 2000},
        )
        assert metrics.token_usage["total"] == 3000

    def test_satisfaction_score_validation(self):
        """Test user satisfaction score validation."""
        # Valid score
        metrics = PersonaMetrics(
            persona_id=uuid4(),
            user_satisfaction_score=4.5,
        )
        assert metrics.user_satisfaction_score == 4.5

        # Invalid score (too high)
        with pytest.raises(ValidationError):
            PersonaMetrics(
                persona_id=uuid4(),
                user_satisfaction_score=6.0,
            )

class TestPersonaConfiguration:
    """Test PersonaConfiguration model validation and behavior."""

    def test_valid_persona_configuration(self):
        """Test creating a valid persona configuration."""
        trait = PersonaTrait(name="analytical", category=TraitCategory.COGNITIVE, value=85)
        style = ResponseStyle(
            type=ResponseStyleType.TECHNICAL,
            tone="professional",
            formality_level=8,
            verbosity=6,
        )
        domain = KnowledgeDomain(
            name="AI/ML",
            expertise_level=9,
            topics=["Machine Learning", "Neural Networks"],
        )

        config = PersonaConfiguration(
            name="AI Expert",
            slug="ai-expert",
            description="Expert in artificial intelligence and machine learning",
            traits=[trait],
            response_style=style,
            knowledge_domains=[domain],
            created_by="admin@example.com",
            temperature=0.3,
        )
        assert config.name == "AI Expert"
        assert config.slug == "ai-expert"
        assert config.status == PersonaStatus.DRAFT
        assert len(config.traits) == 1
        assert config.temperature == 0.3

    def test_slug_validation(self):
        """Test slug format validation."""
        # Valid slug
        config = PersonaConfiguration(
            name="Test Persona",
            slug="test-persona-123",
            description="Test",
            traits=[PersonaTrait(name="test", category=TraitCategory.PERSONALITY, value=50)],
            response_style=ResponseStyle(
                type=ResponseStyleType.CASUAL,
                tone="friendly",
                formality_level=3,
                verbosity=5,
            ),
            created_by="test@example.com",
        )
        assert config.slug == "test-persona-123"

        # Invalid slug (uppercase)
        with pytest.raises(ValidationError):
            PersonaConfiguration(
                name="Test",
                slug="Test-Persona",  # Should be lowercase
                description="Test",
                traits=[PersonaTrait(name="test", category=TraitCategory.PERSONALITY, value=50)],
                response_style=ResponseStyle(
                    type=ResponseStyleType.CASUAL,
                    tone="friendly",
                    formality_level=3,
                    verbosity=5,
                ),
                created_by="test@example.com",
            )

    def test_model_preferences_validation(self):
        """Test model preferences validation."""
        # Valid model preferences
        config = PersonaConfiguration(
            name="Test",
            slug="test",
            description="Test",
            traits=[PersonaTrait(name="test", category=TraitCategory.PERSONALITY, value=50)],
            response_style=ResponseStyle(
                type=ResponseStyleType.CASUAL,
                tone="friendly",
                formality_level=3,
                verbosity=5,
            ),
            created_by="test@example.com",
            model_preferences=["gpt-4-turbo", "claude-3-opus"],
        )
        assert len(config.model_preferences) == 2

        # Invalid model preference
        with pytest.raises(ValidationError) as exc_info:
            PersonaConfiguration(
                name="Test",
                slug="test",
                description="Test",
                traits=[PersonaTrait(name="test", category=TraitCategory.PERSONALITY, value=50)],
                response_style=ResponseStyle(
                    type=ResponseStyleType.CASUAL,
                    tone="friendly",
                    formality_level=3,
                    verbosity=5,
                ),
                created_by="test@example.com",
                model_preferences=["invalid-model-xyz"],
            )
        assert "Invalid model preference" in str(exc_info.value)

    def test_relationship_validation(self):
        """Test that personas can't have both parent and template."""
        parent_id = uuid4()
        template_id = uuid4()

        # Should fail with both parent and template
        with pytest.raises(ValidationError) as exc_info:
            PersonaConfiguration(
                name="Test",
                slug="test",
                description="Test",
                traits=[PersonaTrait(name="test", category=TraitCategory.PERSONALITY, value=50)],
                response_style=ResponseStyle(
                    type=ResponseStyleType.CASUAL,
                    tone="friendly",
                    formality_level=3,
                    verbosity=5,
                ),
                created_by="test@example.com",
                parent_persona_id=parent_id,
                template_id=template_id,
            )
        assert "cannot have both a parent and a template" in str(exc_info.value)

    def test_serialization(self):
        """Test model serialization to dict/JSON."""
        config = PersonaConfiguration(
            name="Serialization Test",
            slug="serialization-test",
            description="Test serialization",
            traits=[PersonaTrait(name="test", category=TraitCategory.PERSONALITY, value=75)],
            response_style=ResponseStyle(
                type=ResponseStyleType.FORMAL,
                tone="professional",
                formality_level=8,
                verbosity=5,
            ),
            created_by="test@example.com",
        )

        # Test dict serialization
        config_dict = config.model_dump()
        assert isinstance(config_dict, dict)
        assert config_dict["name"] == "Serialization Test"
        assert isinstance(config_dict["id"], str)  # UUID serialized to string

        # Test JSON serialization
        config_json = config.model_dump_json()
        assert isinstance(config_json, str)
        assert "Serialization Test" in config_json

class TestEnumValues:
    """Test all enum values are accessible and valid."""

    def test_persona_status_enum(self):
        """Test PersonaStatus enum values."""
        assert PersonaStatus.ACTIVE == "active"
        assert PersonaStatus.INACTIVE == "inactive"
        assert PersonaStatus.DRAFT == "draft"
        assert PersonaStatus.ARCHIVED == "archived"

    def test_trait_category_enum(self):
        """Test TraitCategory enum values."""
        assert TraitCategory.PERSONALITY == "personality"
        assert TraitCategory.COMMUNICATION == "communication"
        assert TraitCategory.EXPERTISE == "expertise"
        assert TraitCategory.BEHAVIORAL == "behavioral"
        assert TraitCategory.COGNITIVE == "cognitive"

    def test_response_style_type_enum(self):
        """Test ResponseStyleType enum values."""
        assert ResponseStyleType.FORMAL == "formal"
        assert ResponseStyleType.CASUAL == "casual"
        assert ResponseStyleType.TECHNICAL == "technical"
        assert ResponseStyleType.CREATIVE == "creative"
        assert ResponseStyleType.EDUCATIONAL == "educational"
        assert ResponseStyleType.EMPATHETIC == "empathetic"

    def test_interaction_mode_enum(self):
        """Test InteractionMode enum values."""
        assert InteractionMode.CONVERSATIONAL == "conversational"
        assert InteractionMode.TASK_ORIENTED == "task_oriented"
        assert InteractionMode.ANALYTICAL == "analytical"
        assert InteractionMode.CREATIVE == "creative"
        assert InteractionMode.ADVISORY == "advisory"

class TestComplexScenarios:
    """Test complex scenarios and edge cases."""

    def test_full_persona_with_all_features(self):
        """Test creating a fully-featured persona configuration."""
        # Create all components
        traits = [
            PersonaTrait(
                name="analytical",
                category=TraitCategory.COGNITIVE,
                value=90,
                weight=2.5,
            ),
            PersonaTrait(
                name="empathetic",
                category=TraitCategory.PERSONALITY,
                value=75,
                weight=1.8,
            ),
            PersonaTrait(
                name="uses_examples",
                category=TraitCategory.COMMUNICATION,
                value=True,
                weight=1.0,
            ),
        ]

        style = ResponseStyle(
            type=ResponseStyleType.EDUCATIONAL,
            tone="encouraging",
            formality_level=6,
            verbosity=7,
            use_examples=True,
            use_analogies=True,
            formatting_preferences={
                "use_bullet_points": True,
                "include_summaries": True,
            },
        )

        domains = [
            KnowledgeDomain(
                name="Machine Learning",
                expertise_level=9,
                topics=["Deep Learning", "NLP", "Computer Vision"],
                related_tools=["PyTorch", "TensorFlow", "Scikit-learn"],
                context_keywords=["ML", "AI", "neural", "model"],
                priority=9,
            ),
            KnowledgeDomain(
                name="Software Engineering",
                expertise_level=8,
                topics=["Architecture", "Design Patterns", "Testing"],
                related_tools=["Git", "Docker", "Kubernetes"],
                context_keywords=["code", "software", "development"],
                priority=7,
            ),
        ]

        rules = [
            BehaviorRule(
                name="Explain Complex Concepts",
                condition="topic_complexity > 7",
                action="break_down_into_steps",
                priority=8,
                is_mandatory=True,
            ),
            BehaviorRule(
                name="Encourage Learning",
                condition="user_shows_confusion",
                action="provide_encouragement",
                priority=6,
            ),
        ]

        memory_config = MemoryConfiguration(
            retention_period_hours=72,
            max_context_tokens=12000,
            summarization_threshold=4000,
            priority_topics=["learning_goals", "misconceptions", "progress"],
            use_semantic_compression=True,
        )

        voice_config = VoiceConfiguration(
            provider="elevenlabs",
            voice_id="teacher_voice_001",
            language="en-US",
            gender="female",
            age_range="middle-aged",
            speaking_rate=0.95,
            emotion_style="encouraging",
        )

        # Create the full persona
        persona = PersonaConfiguration(
            name="AI Teaching Assistant",
            slug="ai-teaching-assistant",
            description="An expert AI educator specializing in machine learning and software engineering",
            avatar_url="https://example.com/avatars/teacher.png",
            status=PersonaStatus.ACTIVE,
            traits=traits,
            response_style=style,
            knowledge_domains=domains,
            behavior_rules=rules,
            interaction_mode=InteractionMode.EDUCATIONAL,
            memory_config=memory_config,
            voice_config=voice_config,
            system_prompt_template="You are an expert AI educator...",
            temperature=0.7,
            max_tokens=3000,
            model_preferences=["gpt-4-turbo", "claude-3-opus"],
            created_by="admin@university.edu",
            tags=["education", "AI", "expert", "teacher"],
            is_public=True,
            allowed_roles=["student", "teacher"],
        )

        # Verify all components
        assert persona.name == "AI Teaching Assistant"
        assert len(persona.traits) == 3
        assert len(persona.knowledge_domains) == 2
        assert len(persona.behavior_rules) == 2
        assert persona.memory_config.retention_period_hours == 72
        assert persona.voice_config.provider == "elevenlabs"
        assert persona.status == PersonaStatus.ACTIVE
        assert persona.is_public is True

        # Test serialization of complex object
        serialized = persona.model_dump()
        assert isinstance(serialized, dict)
        assert len(serialized["traits"]) == 3
        assert serialized["memory_config"]["max_context_tokens"] == 12000

    def test_minimal_persona_configuration(self):
        """Test creating a persona with only required fields."""
        minimal_persona = PersonaConfiguration(
            name="Minimal Bot",
            slug="minimal-bot",
            description="A minimal persona configuration",
            traits=[PersonaTrait(name="simple", category=TraitCategory.PERSONALITY, value=50)],
            response_style=ResponseStyle(
                type=ResponseStyleType.CASUAL,
                tone="neutral",
                formality_level=5,
                verbosity=5,
            ),
            created_by="user@example.com",
        )

        assert minimal_persona.name == "Minimal Bot"
        assert minimal_persona.status == PersonaStatus.DRAFT  # Default
        assert minimal_persona.interaction_mode == InteractionMode.CONVERSATIONAL  # Default
        assert minimal_persona.temperature == 0.7  # Default
        assert minimal_persona.max_tokens == 2000  # Default
        assert len(minimal_persona.knowledge_domains) == 0
        assert len(minimal_persona.behavior_rules) == 0
        assert minimal_persona.memory_config is None
        assert minimal_persona.voice_config is None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
