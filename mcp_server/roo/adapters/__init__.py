"""
Adapters for integrating Roo with different AI models.

This package contains adapters for integrating Roo with different AI models,
such as Copilot and Gemini, providing a consistent interface for memory access
and mode transitions.
"""

from .gemini_adapter import GeminiRooAdapter

__all__ = ["GeminiRooAdapter"]
