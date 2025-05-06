"""
PromptBuilder for the AI Orchestration System.

This module provides the core PromptBuilder class for dynamically constructing
prompts based on persona traits, memory context, and specific requirements.
"""

import logging
import enum
from typing import Dict, List, Any, Optional, Tuple

from packages.shared.src.models.base_models import PersonaConfig, MemoryItem

# Configure logging
logger = logging.getLogger(__name__)


class PromptFormat(enum.Enum):
    """Enum defining the available prompt formats."""

    CHAT = "chat"  # Chat format with system/user/assistant messages
    INSTRUCTION = "instruction"  # Instruction format for instruction-tuned models
    RAW = "raw"  # Raw text format without specific structure


class PromptBuilder:
    """
    Builder for creating dynamic, persona-driven prompts.

    This class builds prompts tailored to specific personas, taking into
    account their traits, the conversation history, and the current input.
    """

    def __init__(self, max_history_tokens: int = 2000, max_prompt_tokens: int = 4000):
        """
        Initialize a new PromptBuilder.

        Args:
            max_history_tokens: Maximum number of tokens to use for history
            max_prompt_tokens: Maximum total tokens for the complete prompt
        """
        self.max_history_tokens = max_history_tokens
        self.max_prompt_tokens = max_prompt_tokens

        # Initialize trait processors for persona customization
        self._trait_processors = {
            "efficiency": self._process_efficiency_trait,
            "assertiveness": self._process_assertiveness_trait,
            "pragmatism": self._process_pragmatism_trait,
            "creativity": self._process_creativity_trait,
            "empathy": self._process_empathy_trait,
            "humor": self._process_humor_trait,
            "logic": self._process_logic_trait,
            "precision": self._process_precision_trait,
            "sass": self._process_sass_trait,
        }

        # Template components for different prompt elements
        self._system_prompt_templates = {
            "base": "You are {name}, {description}. {additional_instructions}",
            "traits": "\n\nYour personality traits include: {traits_description}",
            "memory_context": "\n\nRelevant context from previous conversations: {memory_context}",
            "general_instructions": "\n\nAlways stay in character and maintain a consistent voice.",
        }

    def build_prompt(
        self,
        persona: PersonaConfig,
        user_input: str,
        history_items: Optional[List[MemoryItem]] = None,
        format: PromptFormat = PromptFormat.CHAT,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Build a complete prompt for the given persona and context.

        Args:
            persona: The persona configuration to use
            user_input: The current user input
            history_items: Previous conversation history items (optional)
            format: The desired output format
            additional_context: Any additional context to include

        Returns:
            The constructed prompt in the specified format
        """
        # Process history if provided
        formatted_history = []
        if history_items:
            formatted_history = self._format_conversation_history(history_items)

        # Generate system prompt with persona traits applied
        system_prompt = self._build_system_prompt(persona, additional_context)

        # Return formatted prompt according to requested format
        if format == PromptFormat.CHAT:
            return self._format_as_chat(system_prompt, formatted_history, user_input)
        elif format == PromptFormat.INSTRUCTION:
            return self._format_as_instruction(
                system_prompt, formatted_history, user_input
            )
        else:  # RAW format
            return self._format_as_raw(system_prompt, formatted_history, user_input)

    def _build_system_prompt(
        self,
        persona: PersonaConfig,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Build the system prompt for the given persona.

        Args:
            persona: The persona configuration to use
            additional_context: Any additional context to include

        Returns:
            The constructed system prompt
        """
        # Start with the base template or the persona's custom template if provided
        if persona.prompt_template:
            system_prompt = persona.prompt_template
        else:
            # Build from base template
            additional_instructions = ""
            system_prompt = self._system_prompt_templates["base"].format(
                name=persona.name,
                description=persona.description,
                additional_instructions=additional_instructions,
            )

        # Add trait-specific modifications if traits are specified
        if persona.traits and len(persona.traits) > 0:
            traits_description = self._process_persona_traits(persona.traits)
            if traits_description:
                system_prompt += self._system_prompt_templates["traits"].format(
                    traits_description=traits_description
                )

        # Add any memory context from additional_context
        if additional_context and "memory_context" in additional_context:
            system_prompt += self._system_prompt_templates["memory_context"].format(
                memory_context=additional_context["memory_context"]
            )

        # Add general instructions
        system_prompt += self._system_prompt_templates["general_instructions"]

        return system_prompt

    def _process_persona_traits(self, traits: Dict[str, float]) -> str:
        """
        Process persona traits into a descriptive string.

        Args:
            traits: Dictionary mapping trait names to values (0.0-1.0)

        Returns:
            A string describing the traits
        """
        trait_descriptions = []

        for trait_name, trait_value in traits.items():
            # Get the processor for this trait if available
            processor = self._trait_processors.get(trait_name.lower())

            if processor:
                # Process this trait and add its description
                trait_desc = processor(trait_value)
                if trait_desc:
                    trait_descriptions.append(trait_desc)
            else:
                # For unknown traits, use a generic description
                if trait_value >= 0.7:
                    trait_descriptions.append(f"High {trait_name}")
                elif trait_value <= 0.3:
                    trait_descriptions.append(f"Low {trait_name}")

        return ", ".join(trait_descriptions)

    def _format_conversation_history(
        self, history_items: List[MemoryItem]
    ) -> List[Dict[str, str]]:
        """
        Format conversation history items into a structured format.

        Args:
            history_items: List of memory items representing conversation history

        Returns:
            Formatted history as a list of message dictionaries
        """
        formatted_history = []

        # Process in chronological order (oldest to newest)
        for item in history_items:  # The list is already in chronological order
            if item.text_content:
                formatted_history.append({"role": "user", "content": item.text_content})
            if item.metadata and "llm_response" in item.metadata:
                formatted_history.append(
                    {"role": "assistant", "content": item.metadata["llm_response"]}
                )

        return formatted_history

    def _format_as_chat(
        self,
        system_prompt: str,
        formatted_history: List[Dict[str, str]],
        user_input: str,
    ) -> List[Dict[str, str]]:
        """
        Format the prompt components as a chat completion format.

        Args:
            system_prompt: The system prompt
            formatted_history: Formatted conversation history
            user_input: The current user input

        Returns:
            A list of message dictionaries in chat format
        """
        messages = [{"role": "system", "content": system_prompt}]

        # Add history if available
        if formatted_history:
            messages.extend(formatted_history)

        # Add the current user input
        messages.append({"role": "user", "content": user_input})

        return messages

    def _format_as_instruction(
        self,
        system_prompt: str,
        formatted_history: List[Dict[str, str]],
        user_input: str,
    ) -> str:
        """
        Format the prompt components as an instruction completion format.

        Args:
            system_prompt: The system prompt
            formatted_history: Formatted conversation history
            user_input: The current user input

        Returns:
            A string in instruction format
        """
        prompt = system_prompt + "\n\n"

        # Add history if available
        if formatted_history:
            for message in formatted_history:
                if message["role"] == "user":
                    prompt += f"User: {message['content']}\n"
                else:
                    prompt += f"Assistant: {message['content']}\n"

        # Add the current user input and instruction marker
        prompt += f"User: {user_input}\n"
        prompt += "Assistant: "

        return prompt

    def _format_as_raw(
        self,
        system_prompt: str,
        formatted_history: List[Dict[str, str]],
        user_input: str,
    ) -> str:
        """
        Format the prompt components as raw text.

        Args:
            system_prompt: The system prompt
            formatted_history: Formatted conversation history
            user_input: The current user input

        Returns:
            A string in raw text format
        """
        prompt = system_prompt + "\n\n"

        # Add history if available
        if formatted_history:
            prompt += "Previous conversation:\n"
            for message in formatted_history:
                if message["role"] == "user":
                    prompt += f"Human: {message['content']}\n"
                else:
                    prompt += f"{message['content']}\n"

        # Add the current user input
        prompt += f"\nCurrent message: {user_input}\n\nYour response:"

        return prompt

    # Trait processor methods
    def _process_efficiency_trait(self, value: float) -> str:
        """Process efficiency trait."""
        if value >= 0.7:
            return "Be concise and direct, focusing on efficient communication"
        elif value <= 0.3:
            return "Take your time to explain things thoroughly"
        return ""

    def _process_assertiveness_trait(self, value: float) -> str:
        """Process assertiveness trait."""
        if value >= 0.7:
            return "Be assertive and confident in your responses"
        elif value <= 0.3:
            return "Be gentle and non-confrontational"
        return ""

    def _process_pragmatism_trait(self, value: float) -> str:
        """Process pragmatism trait."""
        if value >= 0.7:
            return "Focus on practical, actionable advice"
        elif value <= 0.3:
            return "Consider theoretical and philosophical perspectives"
        return ""

    def _process_creativity_trait(self, value: float) -> str:
        """Process creativity trait."""
        if value >= 0.7:
            return "Think outside the box and offer innovative ideas"
        elif value <= 0.3:
            return "Stick to conventional, proven approaches"
        return ""

    def _process_empathy_trait(self, value: float) -> str:
        """Process empathy trait."""
        if value >= 0.7:
            return "Show high emotional intelligence and empathize with the user"
        elif value <= 0.3:
            return "Focus on facts and logic rather than emotions"
        return ""

    def _process_humor_trait(self, value: float) -> str:
        """Process humor trait."""
        if value >= 0.7:
            return "Include witty remarks and playful language where appropriate"
        elif value <= 0.3:
            return "Maintain a serious, straightforward communication style"
        return ""

    def _process_logic_trait(self, value: float) -> str:
        """Process logic trait."""
        if value >= 0.7:
            return "Use structured, logical reasoning with clear arguments and evidence"
        elif value <= 0.3:
            return "Focus more on intuition and overall impressions rather than formal logic"
        return ""

    def _process_precision_trait(self, value: float) -> str:
        """Process precision trait."""
        if value >= 0.7:
            return "Be precise and detailed, using exact terminology and avoiding vague language"
        elif value <= 0.3:
            return "Focus on broader concepts rather than precise details"
        return ""

    def _process_sass_trait(self, value: float) -> str:
        """Process sass trait."""
        if value >= 0.7:
            return "Add witty, slightly sassy remarks that show personality and attitude (while remaining respectful)"
        elif value <= 0.3:
            return (
                "Maintain a straightforward, earnest communication style without sass"
            )
        return ""
