"""
Traits processor for the AI Orchestration System.

This module provides logic for processing persona traits and translating
them into specific prompt modifications.
"""

import logging
from typing import Dict, List, Any, Optional, Callable, Tuple

# Configure logging
logger = logging.getLogger(__name__)


class TraitsProcessor:
    """
    Processor for persona traits.

    This class processes persona traits and translates them into specific
    prompt modifications and behavior directives.
    """

    def __init__(self):
        """Initialize the traits processor."""
        # Register trait processors
        self._processors: Dict[str, Callable[[float], Tuple[str, Dict[str, Any]]]] = {
            "efficiency": self._process_efficiency,
            "assertiveness": self._process_assertiveness,
            "pragmatism": self._process_pragmatism,
            "creativity": self._process_creativity,
            "empathy": self._process_empathy,
            "humor": self._process_humor,
            "formality": self._process_formality,
            "detail_orientation": self._process_detail_orientation,
            "logic": self._process_logic,
            "precision": self._process_precision,
            "sass": self._process_sass,
        }

    def process_traits(
        self, traits: Dict[str, float]
    ) -> Tuple[List[str], Dict[str, Any]]:
        """
        Process a set of persona traits.

        Args:
            traits: Dictionary mapping trait names to values (0.0-1.0)

        Returns:
            A tuple containing:
            - List of directive strings to add to the prompt
            - Dictionary of parameters to influence prompt construction
        """
        directives = []
        parameters = {}

        for trait_name, trait_value in traits.items():
            trait_processor = self._processors.get(trait_name.lower())

            if trait_processor:
                # Process this trait
                directive, trait_params = trait_processor(trait_value)
                if directive:
                    directives.append(directive)
                # Merge parameters
                parameters.update(trait_params)
            else:
                # Handle unknown traits with a generic approach
                directive = self._process_generic_trait(trait_name, trait_value)
                if directive:
                    directives.append(directive)

        return directives, parameters

    def _process_generic_trait(self, trait_name: str, value: float) -> str:
        """Process an unknown trait generically."""
        if value >= 0.7:
            return f"You have high {trait_name}. This means you tend to {self._get_high_trait_behavior(trait_name)}."
        elif value <= 0.3:
            return f"You have low {trait_name}. This means you tend to {self._get_low_trait_behavior(trait_name)}."
        return ""

    def _get_high_trait_behavior(self, trait_name: str) -> str:
        """Get a generic behavior description for a high trait value."""
        # Some basic generic descriptions
        generic_behaviors = {
            "confidence": "speak with authority and certainty",
            "patience": "take time to explain things thoroughly",
            "thoroughness": "cover topics comprehensively",
            "enthusiasm": "show excitement and energy",
            "curiosity": "ask questions and explore topics deeply",
            "precision": "be exact and accurate in your statements",
        }

        return generic_behaviors.get(
            trait_name, f"emphasize {trait_name} in your responses"
        )

    def _get_low_trait_behavior(self, trait_name: str) -> str:
        """Get a generic behavior description for a low trait value."""
        # Some basic generic descriptions
        generic_behaviors = {
            "confidence": "be more tentative and consider multiple viewpoints",
            "patience": "get to the point quickly",
            "thoroughness": "focus on the main points without too much detail",
            "enthusiasm": "maintain a calm and measured tone",
            "curiosity": "focus on providing answers rather than exploring tangents",
            "precision": "speak in more general terms",
        }

        return generic_behaviors.get(
            trait_name, f"downplay {trait_name} in your responses"
        )

    # Trait-specific processors
    # Each returns a tuple of (directive, parameters)

    def _process_efficiency(self, value: float) -> Tuple[str, Dict[str, Any]]:
        """Process efficiency trait."""
        params = {"response_length": "auto"}

        if value >= 0.7:
            params["response_length"] = "concise"
            return (
                "You prioritize efficiency in communication. Keep responses concise and direct, "
                "focusing only on the most important information. Avoid unnecessary elaboration "
                "and get straight to the point.",
                params,
            )
        elif value <= 0.3:
            params["response_length"] = "detailed"
            return (
                "You value thoroughness over efficiency. Take time to explain concepts in detail, "
                "providing background information and exploring various aspects of the topic.",
                params,
            )

        return "", params

    def _process_assertiveness(self, value: float) -> Tuple[str, Dict[str, Any]]:
        """Process assertiveness trait."""
        params = {"language_strength": "moderate"}

        if value >= 0.7:
            params["language_strength"] = "strong"
            return (
                "You are highly assertive in your communication. Make confident, direct statements "
                "without hedging. Use authoritative language and provide clear guidance rather than "
                "tentative suggestions.",
                params,
            )
        elif value <= 0.3:
            params["language_strength"] = "gentle"
            return (
                "You have a gentle, non-assertive communication style. Present ideas as suggestions "
                "rather than directives. Use softening language like 'perhaps', 'might consider', "
                "and acknowledge alternative perspectives.",
                params,
            )

        return "", params

    def _process_pragmatism(self, value: float) -> Tuple[str, Dict[str, Any]]:
        """Process pragmatism trait."""
        params = {"focus": "balanced"}

        if value >= 0.7:
            params["focus"] = "practical"
            return (
                "You are highly pragmatic. Focus on practical, actionable advice and real-world "
                "applications. Prioritize solutions that can be implemented immediately and "
                "deliver tangible results.",
                params,
            )
        elif value <= 0.3:
            params["focus"] = "theoretical"
            return (
                "You tend to consider theoretical and philosophical perspectives. Explore conceptual "
                "frameworks and underlying principles rather than only focusing on immediate "
                "practical applications.",
                params,
            )

        return "", params

    def _process_creativity(self, value: float) -> Tuple[str, Dict[str, Any]]:
        """Process creativity trait."""
        params = {"approach": "standard"}

        if value >= 0.7:
            params["approach"] = "creative"
            return (
                "You think creatively and outside the box. Offer innovative ideas and unconventional "
                "approaches. Make unexpected connections between concepts and suggest novel solutions "
                "to problems.",
                params,
            )
        elif value <= 0.3:
            params["approach"] = "conventional"
            return (
                "You favor conventional, proven approaches. Stick to established methods and reliable "
                "solutions with a track record of success. Avoid speculative or experimental ideas "
                "unless specifically requested.",
                params,
            )

        return "", params

    def _process_empathy(self, value: float) -> Tuple[str, Dict[str, Any]]:
        """Process empathy trait."""
        params = {"tone": "neutral"}

        if value >= 0.7:
            params["tone"] = "empathetic"
            return (
                "You have high emotional intelligence and empathy. Acknowledge feelings, validate "
                "concerns, and show understanding of emotional aspects. Pay attention to the user's "
                "emotional state and respond with compassion.",
                params,
            )
        elif value <= 0.3:
            params["tone"] = "logical"
            return (
                "You focus primarily on facts and logic rather than emotions. Maintain an objective, "
                "analytical approach to questions and problems. Provide rational analysis without "
                "emphasizing emotional aspects.",
                params,
            )

        return "", params

    def _process_humor(self, value: float) -> Tuple[str, Dict[str, Any]]:
        """Process humor trait."""
        params = {"humor_level": "moderate"}

        if value >= 0.7:
            params["humor_level"] = "high"
            return (
                "You have a good sense of humor and enjoy adding light-hearted elements to your "
                "responses. Include appropriate humor, wordplay, or a playful tone when it doesn't "
                "detract from the information being conveyed.",
                params,
            )
        elif value <= 0.3:
            params["humor_level"] = "low"
            return (
                "You maintain a serious, straightforward communication style. Focus on delivering "
                "information clearly without attempts at humor or playfulness. Maintain a professional "
                "tone throughout your responses.",
                params,
            )

        return "", params

    def _process_formality(self, value: float) -> Tuple[str, Dict[str, Any]]:
        """Process formality trait."""
        params = {"formality": "balanced"}

        if value >= 0.7:
            params["formality"] = "formal"
            return (
                "You communicate with a high degree of formality. Use proper language, avoid "
                "contractions and slang, and maintain a professional, structured approach to your "
                "responses.",
                params,
            )
        elif value <= 0.3:
            params["formality"] = "casual"
            return (
                "You communicate in a casual, conversational manner. Use contractions, colloquial "
                "expressions, and a relaxed tone as if speaking to a friend rather than in a formal "
                "context.",
                params,
            )

        return "", params

    def _process_detail_orientation(self, value: float) -> Tuple[str, Dict[str, Any]]:
        """Process detail orientation trait."""
        params = {"detail_level": "moderate"}

        if value >= 0.7:
            params["detail_level"] = "high"
            return (
                "You pay close attention to details. Provide specific information, precise data, "
                "and thorough explanations that cover all relevant aspects of a topic. Break complex "
                "topics into their component parts.",
                params,
            )
        elif value <= 0.3:
            params["detail_level"] = "low"
            return (
                "You focus on the big picture rather than details. Provide high-level overviews "
                "and general principles without getting lost in specific details unless they're "
                "essential to understanding.",
                params,
            )

        return "", params

    def _process_logic(self, value: float) -> Tuple[str, Dict[str, Any]]:
        """Process logic trait."""
        params = {"reasoning_style": "balanced"}

        if value >= 0.7:
            params["reasoning_style"] = "logical"
            return (
                "You have a highly logical approach to reasoning. Use structured arguments, clear "
                "premises and conclusions, and identify logical relationships between concepts. "
                "Present information in a systematic, organized manner with clear reasoning chains.",
                params,
            )
        elif value <= 0.3:
            params["reasoning_style"] = "intuitive"
            return (
                "You rely more on intuition than formal logic. Draw on patterns, associations, and "
                "holistic understanding rather than step-by-step deductive reasoning. Present insights "
                "without necessarily explaining every logical step.",
                params,
            )

        return "", params

    def _process_precision(self, value: float) -> Tuple[str, Dict[str, Any]]:
        """Process precision trait."""
        params = {"precision_level": "moderate"}

        if value >= 0.7:
            params["precision_level"] = "high"
            return (
                "You value precision and accuracy in communication. Use exact terminology, provide "
                "specific numbers rather than approximations when available, and make careful "
                "distinctions between similar concepts. Avoid vague language or generalizations.",
                params,
            )
        elif value <= 0.3:
            params["precision_level"] = "low"
            return (
                "You favor broader, more general statements over precise details. Use approximations "
                "and generalizations to convey the essence of ideas without getting caught up in "
                "technical precision. Focus on overall meaning rather than exact specifics.",
                params,
            )

        return "", params

    def _process_sass(self, value: float) -> Tuple[str, Dict[str, Any]]:
        """Process sass trait."""
        params = {"sass_level": "moderate"}

        if value >= 0.7:
            params["sass_level"] = "high"
            return (
                "You have a sassy, slightly irreverent communication style. Include witty remarks, "
                "clever observations, and the occasional playful challenge. Don't be afraid to "
                "show personality and a touch of attitude while maintaining respect.",
                params,
            )
        elif value <= 0.3:
            params["sass_level"] = "low"
            return (
                "You maintain a straightforward, earnest communication style without sass or "
                "irreverence. Present information in a direct, sincere manner without adding "
                "witty remarks or attitude.",
                params,
            )

        return "", params


# Global instance for easy access
traits_processor = TraitsProcessor()


def get_traits_processor() -> TraitsProcessor:
    """
    Get the global traits processor instance.

    Returns:
        The traits processor
    """
    return traits_processor


def process_persona_traits(
    traits: Dict[str, float],
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Process a set of persona traits.

    Args:
        traits: Dictionary mapping trait names to values (0.0-1.0)

    Returns:
        A tuple containing:
        - List of directive strings to add to the prompt
        - Dictionary of parameters to influence prompt construction
    """
    return traits_processor.process_traits(traits)
