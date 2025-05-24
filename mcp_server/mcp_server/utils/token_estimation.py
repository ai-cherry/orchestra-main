#!/usr/bin/env python3
"""
token_estimation.py - Accurate Token Estimation for LLMs

This module provides accurate token estimation for different LLM models using
the tiktoken library. It includes caching and fallback mechanisms for efficient
token counting in production environments.
"""

import json
import re
import logging
import functools
from typing import Dict, Any, Optional, List, Union, Callable, TypeVar
import hashlib

# Import tiktoken with fallback
try:
    import tiktoken

    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False

# Import from relative paths
from ..models.memory import MemoryEntry

# Set up logging
from .structured_logging import get_logger

logger = get_logger(__name__)

# Type variable for generic functions
T = TypeVar("T")

# Mapping of model names to tiktoken encoding names
MODEL_TO_ENCODING = {
    # OpenAI models
    "gpt-3.5-turbo": "cl100k_base",
    "gpt-4": "cl100k_base",
    "gpt-4-turbo": "cl100k_base",
    "gpt-4o": "cl100k_base",
    "text-embedding-ada-002": "cl100k_base",
    # Anthropic models (using cl100k_base as approximation)
    "claude-instant-1": "cl100k_base",
    "claude-2": "cl100k_base",
    "claude-3-opus": "cl100k_base",
    "claude-3-sonnet": "cl100k_base",
    "claude-3-haiku": "cl100k_base",
    # Google models (using cl100k_base as approximation)
    "gemini-pro": "cl100k_base",
    "gemini-ultra": "cl100k_base",
    "text-embedding-gecko": "cl100k_base",
}

# Cache for encoders to avoid repeated initialization
_ENCODER_CACHE: Dict[str, Any] = {}

# Cache for token counts to avoid repeated computation
_TOKEN_COUNT_CACHE: Dict[str, int] = {}
_MAX_CACHE_SIZE = 10000


def get_encoding(model_name: str) -> Any:
    """Get the tokenizer encoding for a specific model.

    Args:
        model_name: The name of the model

    Returns:
        The tokenizer encoding for the model

    Raises:
        ValueError: If tiktoken is not available or the model is not supported
    """
    if not HAS_TIKTOKEN:
        raise ValueError("tiktoken is not installed. Install with 'pip install tiktoken'")

    # Check cache first
    if model_name in _ENCODER_CACHE:
        return _ENCODER_CACHE[model_name]

    # Get encoding name for the model
    encoding_name = MODEL_TO_ENCODING.get(model_name)

    try:
        if encoding_name:
            # Get encoding by name
            encoding = tiktoken.get_encoding(encoding_name)
        else:
            # Try to get encoding directly for the model
            try:
                encoding = tiktoken.encoding_for_model(model_name)
            except KeyError:
                # Fall back to cl100k_base for unknown models
                logger.warning(f"Unknown model: {model_name}, falling back to cl100k_base encoding")
                encoding = tiktoken.get_encoding("cl100k_base")

        # Cache the encoding
        _ENCODER_CACHE[model_name] = encoding
        return encoding

    except Exception as e:
        logger.error(f"Error getting encoding for model {model_name}: {e}")
        raise ValueError(f"Failed to get encoding for model {model_name}: {e}")


def _compute_hash(content: Any) -> str:
    """Compute a hash of the content for caching.

    Args:
        content: The content to hash

    Returns:
        A hash string of the content
    """
    if isinstance(content, str):
        content_str = content
    else:
        try:
            content_str = json.dumps(content, sort_keys=True)
        except (TypeError, ValueError):
            content_str = str(content)

    return hashlib.md5(content_str.encode("utf-8")).hexdigest()


def _manage_cache_size() -> None:
    """Manage the token count cache size."""
    if len(_TOKEN_COUNT_CACHE) >= _MAX_CACHE_SIZE:
        # Remove oldest entries (simple approach: remove half the cache)
        keys_to_remove = list(_TOKEN_COUNT_CACHE.keys())[: _MAX_CACHE_SIZE // 2]
        for key in keys_to_remove:
            del _TOKEN_COUNT_CACHE[key]
        logger.debug(f"Token count cache cleared to {len(_TOKEN_COUNT_CACHE)} entries")


def count_tokens(text: str, model_name: str = "gpt-4") -> int:
    """Count the number of tokens in a text string.

    Args:
        text: The text to count tokens for
        model_name: The name of the model to use for tokenization

    Returns:
        The number of tokens in the text
    """
    # Check cache first
    cache_key = f"{model_name}:{_compute_hash(text)}"
    if cache_key in _TOKEN_COUNT_CACHE:
        return _TOKEN_COUNT_CACHE[cache_key]

    # Use tiktoken if available
    if HAS_TIKTOKEN:
        try:
            encoding = get_encoding(model_name)
            token_count = len(encoding.encode(text))

            # Cache the result
            _TOKEN_COUNT_CACHE[cache_key] = token_count
            _manage_cache_size()

            return token_count
        except Exception as e:
            logger.warning(f"Error counting tokens with tiktoken: {e}")
            # Fall back to heuristic method

    # Fallback heuristic method
    # 1. Count words (approx 0.75 tokens per word)
    # 2. Count special characters (approx 1 token per special char)
    # 3. Count whitespace (approx 0.25 tokens per whitespace)
    word_pattern = re.compile(r"\b\w+\b")
    special_char_pattern = re.compile(r"[^\w\s]")
    whitespace_pattern = re.compile(r"\s+")

    word_count = len(word_pattern.findall(text))
    special_char_count = len(special_char_pattern.findall(text))
    whitespace_count = len(whitespace_pattern.findall(text))

    # Calculate token estimate
    token_estimate = int(word_count * 0.75 + special_char_count + whitespace_count * 0.25 + 4)

    # Cache the result
    _TOKEN_COUNT_CACHE[cache_key] = token_estimate
    _manage_cache_size()

    return token_estimate


def count_tokens_recursive(content: Any, model_name: str = "gpt-4") -> int:
    """Count tokens recursively for nested data structures.

    Args:
        content: The content to count tokens for (can be string, dict, list, etc.)
        model_name: The name of the model to use for tokenization

    Returns:
        The total number of tokens
    """
    # Check cache first
    cache_key = f"{model_name}:{_compute_hash(content)}"
    if cache_key in _TOKEN_COUNT_CACHE:
        return _TOKEN_COUNT_CACHE[cache_key]

    # Process based on content type
    if isinstance(content, str):
        token_count = count_tokens(content, model_name)
    elif isinstance(content, dict):
        # For dictionaries, count tokens for each key and value
        token_count = 0
        for key, value in content.items():
            token_count += count_tokens(str(key), model_name)
            token_count += count_tokens_recursive(value, model_name)
        # Add tokens for braces and commas
        token_count += 2 + max(0, len(content) - 1)
    elif isinstance(content, list):
        # For lists, count tokens for each item
        token_count = sum(count_tokens_recursive(item, model_name) for item in content)
        # Add tokens for brackets and commas
        token_count += 2 + max(0, len(content) - 1)
    else:
        # For other types, convert to string
        token_count = count_tokens(str(content), model_name)

    # Cache the result
    _TOKEN_COUNT_CACHE[cache_key] = token_count
    _manage_cache_size()

    return token_count


def estimate_memory_entry_tokens(entry: MemoryEntry, model_name: str = "gpt-4") -> int:
    """Estimate the number of tokens in a memory entry.

    Args:
        entry: The memory entry to estimate tokens for
        model_name: The name of the model to use for tokenization

    Returns:
        The estimated number of tokens
    """
    # Check if content hash is available and in cache
    if entry.metadata.content_hash:
        cache_key = f"{model_name}:{entry.metadata.content_hash}"
        if cache_key in _TOKEN_COUNT_CACHE:
            return _TOKEN_COUNT_CACHE[cache_key]

    # Count tokens for the content
    token_count = count_tokens_recursive(entry.content, model_name)

    # Add tokens for metadata (simplified estimate)
    metadata_str = json.dumps(entry.metadata.to_dict())
    token_count += count_tokens(metadata_str, model_name)

    # Cache the result if content hash is available
    if entry.metadata.content_hash:
        cache_key = f"{model_name}:{entry.metadata.content_hash}"
        _TOKEN_COUNT_CACHE[cache_key] = token_count
        _manage_cache_size()

    return token_count


def with_token_counting(
    model_name: str = "gpt-4",
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to count tokens for function inputs and outputs.

    Args:
        model_name: The name of the model to use for tokenization

    Returns:
        A decorator function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Count tokens for inputs
            args_tokens = count_tokens_recursive(args, model_name)
            kwargs_tokens = count_tokens_recursive(kwargs, model_name)

            # Call the function
            result = func(*args, **kwargs)

            # Count tokens for output
            result_tokens = count_tokens_recursive(result, model_name)

            # Log token counts
            logger.debug(
                f"Token counts for {func.__name__}: args={args_tokens}, "
                f"kwargs={kwargs_tokens}, result={result_tokens}, "
                f"total={args_tokens + kwargs_tokens + result_tokens}",
                extra={
                    "token_count": {
                        "args": args_tokens,
                        "kwargs": kwargs_tokens,
                        "result": result_tokens,
                        "total": args_tokens + kwargs_tokens + result_tokens,
                    }
                },
            )

            return result

        return wrapper

    return decorator


class TokenEstimator:
    """Accurate token estimation for different LLM models."""

    def __init__(self, model_name: str = "gpt-4"):
        """Initialize the token estimator.

        Args:
            model_name: The name of the model to use for tokenization
        """
        self.model_name = model_name

    def estimate_tokens(self, content: Any) -> int:
        """Estimate the number of tokens in content.

        Args:
            content: The content to estimate tokens for

        Returns:
            The estimated number of tokens
        """
        return count_tokens_recursive(content, self.model_name)

    def estimate_memory_entry(self, entry: MemoryEntry) -> int:
        """Estimate the number of tokens in a memory entry.

        Args:
            entry: The memory entry to estimate tokens for

        Returns:
            The estimated number of tokens
        """
        return estimate_memory_entry_tokens(entry, self.model_name)

    def clear_cache(self) -> None:
        """Clear the token count cache."""
        _TOKEN_COUNT_CACHE.clear()
        logger.debug("Token count cache cleared")
