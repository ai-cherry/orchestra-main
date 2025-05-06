"""
Tests for the PromptBuilder module.

This module contains tests for the PromptBuilder and related components.
"""

import pytest
from typing import Dict, List, Any, Optional

from packages.shared.src.models.base_models import MemoryItem
from packages.shared.src.models.base_models import PersonaConfig
from packages.shared.src.prompt_builder import (
    PromptBuilder, PromptFormat,
    TraitsProcessor, PromptTemplate,
    get_formatter_for_persona
)

# Test data
test_personas = {
    "cherry": PersonaConfig(
        name="Cherry",
        description="Creative Muse, playful, witty",
        prompt_template="You are Cherry, a creative and witty AI with a touch of dark humor. Respond playfully and inspire Patrick.",
        traits={"creativity": 0.9, "humor": 0.8, "empathy": 0.7}
    ),
    "sophia": PersonaConfig(
        name="Sophia",
        description="Analytical Powerhouse, strategic, sassy",
        prompt_template="You are Sophia, a strategic and precise AI with a touch of sass. Provide clear, data-backed responses.",
        traits={"logic": 0.9, "precision": 0.8, "sass": 0.7}
    ),
    "gordon_gekko": PersonaConfig(
        name="Gordon Gekko",
        description="Ruthless Efficiency Expert, blunt, results-obsessed",
        prompt_template="You are Gordon Gekko, a no-nonsense AI focused on results. Be blunt, skip pleasantries, and push Patrick to win with tough love.",
        traits={
            "efficiency": 0.9,
            "assertiveness": 0.8,
            "pragmatism": 0.7
        }
    ),
    "custom": PersonaConfig(
        name="CustomBot",
        description="A highly configurable assistant",
        prompt_template=None,
        traits={
            "creativity": 0.8,
            "empathy": 0.9,
            "efficiency": 0.3,
            "humor": 0.7
        }
    )
}


@pytest.fixture
def prompt_builder():
    """Create a PromptBuilder instance for testing."""
    return PromptBuilder()


class TestPromptBuilder:
    """Tests for the PromptBuilder class."""

    def test_build_prompt_basic(self, prompt_builder):
        """Test basic prompt building without history."""
        user_input = "Hello, how are you?"
        persona = test_personas["cherry"]
        
        # Build a chat prompt
        chat_prompt = prompt_builder.build_prompt(
            persona=persona,
            user_input=user_input,
            format=PromptFormat.CHAT
        )
        
        # Verify the structure
        assert isinstance(chat_prompt, list)
        assert len(chat_prompt) == 2  # system + user message
        assert chat_prompt[0]["role"] == "system"
        assert chat_prompt[1]["role"] == "user"
        assert chat_prompt[1]["content"] == user_input
        
        # Test that persona template is included
        assert "creative and witty AI" in chat_prompt[0]["content"]

    def test_build_prompt_with_traits(self, prompt_builder):
        """Test prompt building with persona traits."""
        user_input = "Give me some business advice."
        persona = test_personas["gordon_gekko"]
        
        # Build a chat prompt
        chat_prompt = prompt_builder.build_prompt(
            persona=persona,
            user_input=user_input,
            format=PromptFormat.CHAT
        )
        
        # Verify trait info is included
        system_content = chat_prompt[0]["content"]
        assert "Gordon Gekko" in system_content
        assert "no-nonsense" in system_content
        
        # Check for trait descriptions
        assert "efficiency" in system_content.lower() or "concise" in system_content.lower()
        assert "assertive" in system_content.lower() or "confident" in system_content.lower()

    def test_build_prompt_instruction_format(self, prompt_builder):
        """Test building a prompt in instruction format."""
        user_input = "What's the weather like?"
        persona = test_personas["sophia"]
        
        # Build an instruction format prompt
        instruction_prompt = prompt_builder.build_prompt(
            persona=persona,
            user_input=user_input,
            format=PromptFormat.INSTRUCTION
        )
        
        # Verify the structure
        assert isinstance(instruction_prompt, str)
        assert "Sophia" in instruction_prompt
        assert f"User: {user_input}" in instruction_prompt
        assert instruction_prompt.endswith("Assistant: ")

    def test_build_prompt_with_history(self, prompt_builder):
        """Test building a prompt with conversation history."""
        user_input = "What do you think of that?"
        persona = test_personas["cherry"]
        
        # Create some history items
        history_items = [
            MemoryItem(
                id="1",
                user_id="test_user",
                session_id="test_session",
                timestamp="2023-01-01T12:00:00Z",
                item_type="conversation",
                persona_active="cherry",
                text_content="Hello there!",
                metadata={"llm_response": "Hi! How can I help you today?"}
            ),
            MemoryItem(
                id="2",
                user_id="test_user",
                session_id="test_session",
                timestamp="2023-01-01T12:01:00Z",
                item_type="conversation",
                persona_active="cherry",
                text_content="Tell me about AI.",
                metadata={"llm_response": "AI is a fascinating field of computer science!"}
            )
        ]
        
        # Build a chat prompt with history
        chat_prompt = prompt_builder.build_prompt(
            persona=persona,
            user_input=user_input,
            history_items=history_items,
            format=PromptFormat.CHAT
        )
        
        # Verify the history is included
        assert len(chat_prompt) == 6  # system + 2 history exchanges + current user message
        assert chat_prompt[1]["role"] == "user"
        assert chat_prompt[1]["content"] == "Hello there!"
        assert chat_prompt[2]["role"] == "assistant"
        assert "AI is a fascinating field" in chat_prompt[4]["content"]
        assert chat_prompt[5]["content"] == user_input


class TestTraitsProcessor:
    """Tests for the TraitsProcessor."""
    
    def test_process_traits(self):
        """Test processing persona traits."""
        traits_processor = TraitsProcessor()
        
        # Test with Gordon Gekko's traits
        traits = test_personas["gordon_gekko"].traits
        directives, parameters = traits_processor.process_traits(traits)
        
        # Verify we got some directives
        assert len(directives) > 0
        
        # Check that efficiency parameter is set to "concise"
        assert "response_length" in parameters
        assert parameters["response_length"] == "concise"
        
        # Check that we have assertiveness directive
        assert any("assertive" in directive.lower() for directive in directives)

    def test_process_custom_traits(self):
        """Test processing custom traits."""
        traits_processor = TraitsProcessor()
        
        # Test with custom traits
        traits = {
            "creativity": 0.8,
            "empathy": 0.9,
            "detail_orientation": 0.2
        }
        
        directives, parameters = traits_processor.process_traits(traits)
        
        # Verify creativity and empathy directives are included
        assert any("creative" in directive.lower() for directive in directives)
        assert any("empathy" in directive.lower() for directive in directives)
        assert any("detail" in directive.lower() for directive in directives)
        
        # Check that tone parameter is set to "empathetic" due to high empathy
        assert "tone" in parameters
        assert parameters["tone"] == "empathetic"


class TestFormatters:
    """Tests for prompt formatters."""
    
    def test_formatter_selection(self):
        """Test getting the appropriate formatter for a persona."""
        # Test with trait-heavy persona
        gekko_formatter = get_formatter_for_persona(test_personas["gordon_gekko"])
        assert gekko_formatter is not None
        
        # Test with minimal trait persona
        cherry_formatter = get_formatter_for_persona(test_personas["cherry"])
        assert cherry_formatter is not None
    
    def test_trait_based_formatting(self):
        """Test trait-based formatting."""
        from packages.shared.src.prompt_builder.formatters import TraitBasedFormatter
        
        formatter = TraitBasedFormatter()
        base_prompt = "You are an AI assistant."
        
        # Test with efficiency trait
        persona = PersonaConfig(
            name="Test",
            description="Test",
            prompt_template=None,
            traits={"efficiency": 0.9}
        )
        
        formatted = formatter.format_system_prompt(base_prompt, persona)
        assert "efficient" in formatted.lower() or "concise" in formatted.lower()
    
    def test_tone_formatting(self):
        """Test tone-based formatting."""
        from packages.shared.src.prompt_builder.formatters import ToneFormatter
        
        formatter = ToneFormatter()
        base_prompt = "You are an AI assistant."
        
        # Test with Cherry persona (should detect enthusiastic tone)
        formatted = formatter.format_system_prompt(base_prompt, test_personas["cherry"])
        assert "enthusiastic" in formatted.lower() or "upbeat" in formatted.lower()
        
        # Test with metadata-specified tone
        persona = PersonaConfig(
            name="Test",
            description="Test",
            prompt_template=None,
            traits={},
            metadata={"tone": "professional"}
        )
        
        formatted = formatter.format_system_prompt(base_prompt, persona)
        assert "professional" in formatted.lower()


class TestTemplates:
    """Tests for prompt templates."""
    
    def test_template_rendering(self):
        """Test rendering a template with context."""
        from packages.shared.src.prompt_builder.templates import PromptTemplate
        
        template = PromptTemplate(
            "test",
            "You are {name}, a {description}. Your focus is on {focus}."
        )
        
        context = {
            "name": "TestBot",
            "description": "helpful assistant",
            "focus": "accuracy"
        }
        
        rendered = template.render(context)
        assert "You are TestBot, a helpful assistant" in rendered
        assert "Your focus is on accuracy" in rendered
    
    def test_template_for_persona(self):
        """Test getting a template for a persona."""
        from packages.shared.src.prompt_builder.templates import get_template_for_persona
        
        # Test with known persona
        cherry_template = get_template_for_persona(test_personas["cherry"])
        assert cherry_template is not None
        assert cherry_template.template_id == "cherry" or cherry_template.template_id == "cheerful"
        
        # Test with trait-based matching
        high_efficiency_persona = PersonaConfig(
            name="EfficiencyBot",
            description="Efficient assistant",
            prompt_template=None,
            traits={"efficiency": 0.9}
        )
        
        efficiency_template = get_template_for_persona(high_efficiency_persona)
        assert efficiency_template is not None
