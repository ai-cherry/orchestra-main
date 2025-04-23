"""
Prompt formatters for the AI Orchestration System.

This module provides specialized formatters for different prompt styles
based on persona traits and requirements.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Callable

from packages.shared.src.models.base_models import PersonaConfig, MemoryItem

# Configure logging
logger = logging.getLogger(__name__)


class PromptFormatter:
    """
    Base class for prompt formatters.

    Formatters transform the basic prompt structure into a specific style
    based on persona traits and requirements.
    """

    def format_system_prompt(self, system_prompt: str, persona: PersonaConfig) -> str:
        """
        Format the system prompt according to specific style.

        Args:
            system_prompt: The base system prompt
            persona: The persona configuration

        Returns:
            The formatted system prompt
        """
        return system_prompt


class TraitBasedFormatter(PromptFormatter):
    """
    Formatter that adjusts prompt based on persona traits.

    This formatter modifies the prompt to reflect persona traits like
    efficiency, assertiveness, etc.
    """

    def format_system_prompt(self, system_prompt: str, persona: PersonaConfig) -> str:
        """
        Format the system prompt according to persona traits.

        Args:
            system_prompt: The base system prompt
            persona: The persona configuration

        Returns:
            The formatted system prompt
        """
        if not persona.traits or len(persona.traits) == 0:
            return system_prompt

        # Start with the base prompt
        formatted_prompt = system_prompt

        # Apply trait-specific formatting

        # Efficiency trait affects prompt verbosity and structure
        if "efficiency" in persona.traits:
            efficiency_value = persona.traits["efficiency"]
            formatted_prompt = self._apply_efficiency_formatting(
                formatted_prompt, efficiency_value
            )

        # Assertiveness trait affects language strength and directness
        if "assertiveness" in persona.traits:
            assertiveness_value = persona.traits["assertiveness"]
            formatted_prompt = self._apply_assertiveness_formatting(
                formatted_prompt, assertiveness_value
            )

        # Creativity trait affects response style
        if "creativity" in persona.traits:
            creativity_value = persona.traits["creativity"]
            formatted_prompt = self._apply_creativity_formatting(
                formatted_prompt, creativity_value
            )

        return formatted_prompt

    def _apply_efficiency_formatting(self, prompt: str, efficiency_value: float) -> str:
        """
        Apply formatting based on efficiency trait.

        Args:
            prompt: The current prompt
            efficiency_value: The efficiency trait value (0.0-1.0)

        Returns:
            Modified prompt
        """
        if efficiency_value >= 0.7:
            # High efficiency: Add instructions for concise, direct communication
            prompt += "\n\nBe efficient in your communication. Keep responses concise and get straight to the point. Prioritize clarity and brevity over elaborate explanations."
        elif efficiency_value <= 0.3:
            # Low efficiency: Add instructions for detailed, thorough communication
            prompt += "\n\nTake your time to provide thorough, detailed explanations. Don't rush to a conclusion; explore multiple perspectives and provide context."

        return prompt

    def _apply_assertiveness_formatting(
        self, prompt: str, assertiveness_value: float
    ) -> str:
        """
        Apply formatting based on assertiveness trait.

        Args:
            prompt: The current prompt
            assertiveness_value: The assertiveness trait value (0.0-1.0)

        Returns:
            Modified prompt
        """
        if assertiveness_value >= 0.7:
            # High assertiveness: Add instructions for confident, direct language
            prompt += "\n\nUse confident, direct language. Make strong statements rather than hedging. Provide clear guidance and direction."
        elif assertiveness_value <= 0.3:
            # Low assertiveness: Add instructions for gentle, tentative language
            prompt += "\n\nUse gentle, non-confrontational language. Present ideas as suggestions rather than directives. Acknowledge other perspectives."

        return prompt

    def _apply_creativity_formatting(self, prompt: str, creativity_value: float) -> str:
        """
        Apply formatting based on creativity trait.

        Args:
            prompt: The current prompt
            creativity_value: The creativity trait value (0.0-1.0)

        Returns:
            Modified prompt
        """
        if creativity_value >= 0.7:
            # High creativity: Add instructions for innovative, original thinking
            prompt += "\n\nThink outside the box. Offer fresh perspectives and innovative ideas. Don't be constrained by conventional thinking."
        elif creativity_value <= 0.3:
            # Low creativity: Add instructions for practical, conventional thinking
            prompt += "\n\nFocus on practical, proven approaches. Stick to established methods and reliable solutions."

        return prompt


class ToneFormatter(PromptFormatter):
    """
    Formatter that adjusts the tone of the prompt.

    This formatter modifies linguistic patterns to achieve a specific tone
    like professional, casual, technical, etc.
    """

    # Tone style templates
    TONE_TEMPLATES = {
        "professional": "\n\nMaintain a professional tone. Use formal language, avoid colloquialisms, and structure your responses with clarity and precision.",
        "casual": "\n\nUse a casual, conversational tone. Feel free to use contractions and friendly language. Write as if you're having a relaxed conversation.",
        "technical": "\n\nAdopt a technical tone. Use precise terminology, structured explanations, and evidence-based reasoning.",
        "enthusiastic": "\n\nBe enthusiastic and energetic! Show excitement in your responses and use upbeat language.",
        "empathetic": "\n\nUse an empathetic tone. Show understanding and emotional intelligence. Acknowledge feelings and validate concerns.",
    }

    def format_system_prompt(self, system_prompt: str, persona: PersonaConfig) -> str:
        """
        Format the system prompt according to the desired tone.

        Args:
            system_prompt: The base system prompt
            persona: The persona configuration

        Returns:
            The formatted system prompt
        """
        # Start with the base prompt
        formatted_prompt = system_prompt

        # Determine the appropriate tone from persona metadata or name
        tone = self._determine_tone(persona)

        # Apply tone-specific template if available
        if tone in self.TONE_TEMPLATES:
            formatted_prompt += self.TONE_TEMPLATES[tone]

        return formatted_prompt

    def _determine_tone(self, persona: PersonaConfig) -> str:
        """
        Determine the appropriate tone based on the persona.

        Args:
            persona: The persona configuration

        Returns:
            The tone identifier
        """
        # Check metadata for explicit tone
        if persona.metadata and "tone" in persona.metadata:
            return persona.metadata["tone"]

        # Infer from persona name or description
        name_lower = persona.name.lower()
        desc_lower = persona.description.lower()

        if "professional" in desc_lower or "business" in desc_lower:
            return "professional"
        elif "casual" in desc_lower or "friendly" in desc_lower:
            return "casual"
        elif "technical" in desc_lower or "expert" in desc_lower:
            return "technical"
        elif (
            "cheerful" in desc_lower
            or "energetic" in desc_lower
            or "cherry" in name_lower
        ):
            return "enthusiastic"
        elif "empathetic" in desc_lower or "caring" in desc_lower:
            return "empathetic"

        # Default tone
        return "professional"


class MemoryContextFormatter(PromptFormatter):
    """
    Formatter that enriches prompts with memory context.

    This formatter analyzes conversation history to extract relevant
    context and incorporate it into the prompt.
    """

    def __init__(self, max_context_items: int = 3):
        """
        Initialize the memory context formatter.

        Args:
            max_context_items: Maximum number of context items to include
        """
        self.max_context_items = max_context_items

    def format_system_prompt(
        self,
        system_prompt: str,
        persona: PersonaConfig,
        history_items: Optional[List[MemoryItem]] = None,
    ) -> str:
        """
        Format the system prompt with memory context.

        Args:
            system_prompt: The base system prompt
            persona: The persona configuration
            history_items: Conversation history items

        Returns:
            The formatted system prompt with memory context
        """
        if not history_items or len(history_items) == 0:
            return system_prompt

        # Extract key topics and references from history
        memory_context = self._extract_memory_context(history_items)

        if memory_context:
            system_prompt += (
                f"\n\nRelevant context from previous conversations:\n{memory_context}"
            )

        return system_prompt

    def _extract_memory_context(self, history_items: List[MemoryItem]) -> str:
        """
        Extract relevant context from conversation history.

        Args:
            history_items: Conversation history items

        Returns:
            Formatted memory context
        """
        # Simple extraction for now - take the most recent exchanges
        context_elements = []

        # Extract key information from most recent items (limited by max_context_items)
        for item in history_items[: min(len(history_items), self.max_context_items)]:
            if item.text_content:
                # Extract the user's query/statement
                context_elements.append(f"- User mentioned: {item.text_content}")

            if item.metadata and "llm_response" in item.metadata:
                # Extract key points from the response
                response = item.metadata["llm_response"]
                # Use a simple heuristic to extract what appears to be important
                sentences = re.split(r"[.!?]", response)
                important_sentences = [
                    s
                    for s in sentences
                    if len(s.strip()) > 20
                    and any(
                        kw in s.lower()
                        for kw in [
                            "important",
                            "key",
                            "should",
                            "must",
                            "recommend",
                            "suggest",
                        ]
                    )
                ]

                if important_sentences:
                    context_elements.append(
                        f"- Important point discussed: {important_sentences[0].strip()}"
                    )

        return "\n".join(context_elements)


def get_formatter_for_persona(persona: PersonaConfig) -> PromptFormatter:
    """
    Get the appropriate formatter for the given persona.

    Args:
        persona: The persona configuration

    Returns:
        A suitable prompt formatter
    """
    # Create a list of formatters to apply in sequence
    formatters = []

    # Always add the trait-based formatter if traits are present
    if persona.traits and len(persona.traits) > 0:
        formatters.append(TraitBasedFormatter())

    # Add tone formatter based on persona type
    formatters.append(ToneFormatter())

    # If there's only one formatter, return it
    if len(formatters) == 1:
        return formatters[0]

    # Otherwise, create a composite formatter that applies all formatters in sequence
    return CompositeFormatter(formatters)


class CompositeFormatter(PromptFormatter):
    """
    Formatter that composes multiple formatters together.

    This formatter applies a sequence of formatters to the prompt.
    """

    def __init__(self, formatters: List[PromptFormatter]):
        """
        Initialize the composite formatter.

        Args:
            formatters: List of formatters to apply in sequence
        """
        self.formatters = formatters

    def format_system_prompt(self, system_prompt: str, persona: PersonaConfig) -> str:
        """
        Format the system prompt by applying all formatters in sequence.

        Args:
            system_prompt: The base system prompt
            persona: The persona configuration

        Returns:
            The formatted system prompt
        """
        formatted_prompt = system_prompt

        for formatter in self.formatters:
            formatted_prompt = formatter.format_system_prompt(formatted_prompt, persona)

        return formatted_prompt
