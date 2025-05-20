"""
Strategy implementations for applying different interaction styles to agent responses.
"""

from abc import ABC, abstractmethod


class InteractionStylingStrategy(ABC):
    """
    Abstract base class for interaction styling strategies.
    """

    @abstractmethod
    def apply_style(self, text: str) -> str:
        """
        Apply a specific interaction style to the given text.

        Args:
            text: The input text to style.

        Returns:
            The styled text.
        """
        pass


class FormalStyling(InteractionStylingStrategy):
    """Applies a formal interaction style."""

    def apply_style(self, text: str) -> str:
        return text.replace("I can ", "I am able to ").replace("can't", "cannot")


class CasualStyling(InteractionStylingStrategy):
    """Applies a casual interaction style."""

    def apply_style(self, text: str) -> str:
        return text.replace("I am", "I'm").replace("will not", "won't")


class FriendlyStyling(InteractionStylingStrategy):
    """Applies a friendly interaction style."""

    def apply_style(self, text: str) -> str:
        return f"{text} I hope that helps!"


class TechnicalStyling(InteractionStylingStrategy):
    """Applies a technical interaction style."""

    def apply_style(self, text: str) -> str:
        return f"Technically speaking, {text}"


class ConciseStyling(InteractionStylingStrategy):
    """Applies a concise interaction style."""

    def apply_style(self, text: str) -> str:
        # Simplistic implementation - would be more sophisticated in real system
        return text.split(". ")[0] + "."


class ElaborateStyling(InteractionStylingStrategy):
    """Applies an elaborate interaction style."""

    def apply_style(self, text: str) -> str:
        return f"{text} There are, of course, multiple facets to consider here."


class EmpatheticStyling(InteractionStylingStrategy):
    """Applies an empathetic interaction style."""

    def apply_style(self, text: str) -> str:
        return f"I understand your interest in this. {text}"


class WittyStyling(InteractionStylingStrategy):
    """Applies a witty interaction style."""

    def apply_style(self, text: str) -> str:
        return f"{text} Who would have thought, right?"


class ProfessionalStyling(InteractionStylingStrategy):
    """Applies a professional interaction style."""

    def apply_style(self, text: str) -> str:
        return f"From a professional standpoint, {text}"


# Mapping of style names to strategy instances
STYLE_STRATEGIES = {
    "formal": FormalStyling(),
    "casual": CasualStyling(),
    "friendly": FriendlyStyling(),
    "technical": TechnicalStyling(),
    "concise": ConciseStyling(),
    "elaborate": ElaborateStyling(),
    "empathetic": EmpatheticStyling(),
    "witty": WittyStyling(),
    "professional": ProfessionalStyling(),
}


def get_styling_strategy(style_name: str) -> InteractionStylingStrategy:
    """
    Get the appropriate styling strategy for a given style name.

    Args:
        style_name: The name of the interaction style.

    Returns:
        An instance of the corresponding InteractionStylingStrategy.
        Defaults to FormalStyling if the style name is not found.
    """
    return STYLE_STRATEGIES.get(style_name.lower(), FormalStyling())
