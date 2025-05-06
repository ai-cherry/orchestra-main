"""
LLM client interface definition.

This module defines the abstract base class that all LLM clients must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union


class LLMClient(ABC):
    """
    Abstract base class for LLM clients.

    This interface defines the contract that all LLM provider
    implementations must follow.
    """

    @abstractmethod
    async def generate_response(
        self, model: str, messages: List[Dict[str, str]], **kwargs
    ) -> str:
        """
        Generate a response from the LLM based on the provided messages.

        Args:
            model: The model identifier to use for generation
            messages: A list of message dictionaries in the ChatML format
                     (each with 'role' and 'content' keys)
            **kwargs: Additional model-specific parameters (e.g., temperature, max_tokens)

        Returns:
            The generated text response from the LLM

        Raises:
            Exception: If there's an error communicating with the LLM provider
        """
        pass

    def __str__(self) -> str:
        """Return a string representation of the client."""
        return f"{self.__class__.__name__}"
