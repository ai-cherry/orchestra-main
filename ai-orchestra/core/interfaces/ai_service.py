"""
AI service interface for AI Orchestra.

This module defines the protocol for AI model interactions.
"""

from typing import Protocol, Any, Optional, Dict, List, Union


class AIService(Protocol):
    """AI service provider interface."""

    async def generate_text(
        self,
        prompt: str,
        model_id: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 1.0,
        stop_sequences: Optional[List[str]] = None,
    ) -> str:
        """
        Generate text from a prompt.

        Args:
            prompt: The input prompt
            model_id: The model identifier
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            top_p: Nucleus sampling parameter (0.0-1.0)
            stop_sequences: Optional list of sequences to stop generation

        Returns:
            The generated text
        """
        ...

    async def generate_embeddings(
        self,
        texts: List[str],
        model_id: str,
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of input texts
            model_id: The model identifier

        Returns:
            List of embedding vectors
        """
        ...

    async def classify_text(
        self,
        text: str,
        categories: List[str],
        model_id: str,
    ) -> Dict[str, float]:
        """
        Classify text into categories.

        Args:
            text: The input text
            categories: List of possible categories
            model_id: The model identifier

        Returns:
            Dictionary mapping categories to confidence scores
        """
        ...

    async def answer_question(
        self,
        question: str,
        context: str,
        model_id: str,
    ) -> str:
        """
        Answer a question based on context.

        Args:
            question: The question to answer
            context: The context to use for answering
            model_id: The model identifier

        Returns:
            The answer to the question
        """
        ...

    async def summarize_text(
        self,
        text: str,
        max_length: Optional[int] = None,
        model_id: str = "default",
    ) -> str:
        """
        Summarize text.

        Args:
            text: The text to summarize
            max_length: Maximum length of the summary
            model_id: The model identifier

        Returns:
            The summarized text
        """
        ...

    async def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get a list of available models.

        Returns:
            List of model information dictionaries
        """
        ...
