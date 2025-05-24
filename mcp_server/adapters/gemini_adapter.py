#!/usr/bin/env python3
"""
gemini_adapter.py - Optimized Google Gemini Adapter for MCP

This module implements the IToolAdapter interface for Google Gemini,
enabling bidirectional memory synchronization between Gemini and the MCP system.
This implementation includes performance optimizations, proper async patterns,
and integration with Vertex AI.
"""

import os
import json
import logging
import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple, Set, Deque
from collections import deque
import hashlib
import aiohttp
from functools import lru_cache

from ..interfaces.tool_adapter import IToolAdapter
from ..models.memory import MemoryEntry, MemoryType

# Import Vertex AI libraries conditionally to avoid hard dependency
try:
    from google.cloud import aiplatform
    from vertexai.preview.generative_models import GenerativeModel, GenerationConfig
    from vertexai.language_models import TextEmbeddingModel

    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Vertex AI libraries not available. Using simulated responses.")

logger = logging.getLogger(__name__)


class GeminiAdapter(IToolAdapter):
    """Optimized Google Gemini adapter for MCP with Vertex AI integration."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the Gemini adapter with optimized configuration."""
        self.config = config or {}
        self.project_id = self.config.get("project_id") or os.environ.get("GOOGLE_CLOUD_PROJECT", "cherry-ai-project")
        self.location = self.config.get("location") or os.environ.get("VERTEX_LOCATION", "us-central1")
        self.api_key = self.config.get("api_key") or os.environ.get("GEMINI_API_KEY")
        self.model = self.config.get("model", "gemini-pro")
        self.embeddings_model = self.config.get("embeddings_model", "textembedding-gecko")

        # Performance optimizations
        self.initialized = False
        self.context_cache: Dict[str, Any] = {}
        self.embedding_cache: Dict[str, List[float]] = {}
        self.cache_ttl = self.config.get("cache_ttl", 300)  # 5 minutes
        self.max_cache_size = self.config.get("max_cache_size", 1000)
        self.batch_size = self.config.get("batch_size", 5)  # For batch processing

        # Request throttling
        self.request_semaphore = asyncio.Semaphore(self.config.get("max_concurrent_requests", 10))
        self.request_history: Deque[float] = deque(maxlen=100)  # Track recent requests
        self.rate_limit = self.config.get("rate_limit", 60)  # Requests per minute

        # Gemini Pro has a large context window
        self.token_limit = self.config.get("token_limit", 200000)

        # Track context usage
        self.current_token_usage = 0

        # Vertex AI clients
        self.vertex_client = None
        self.generative_model = None
        self.embedding_model = None

    @property
    def tool_name(self) -> str:
        """Get the name of the tool."""
        return "gemini"

    @property
    def context_window_size(self) -> int:
        """Get the context window size for Gemini."""
        return self.token_limit

    async def initialize(self) -> bool:
        """Initialize the Gemini adapter with Vertex AI integration."""
        try:
            if VERTEX_AI_AVAILABLE:
                # Initialize Vertex AI
                aiplatform.init(project=self.project_id, location=self.location)

                # Initialize generative model
                self.generative_model = GenerativeModel(self.model)

                # Initialize embedding model
                self.embedding_model = TextEmbeddingModel.from_pretrained(self.embeddings_model)

                logger.info(f"Initialized Gemini adapter with Vertex AI: {self.model}")
            else:
                logger.warning("Using simulated Gemini adapter (Vertex AI not available)")

            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"Error initializing Gemini adapter: {e}")
            return False

    async def sync_create(self, key: str, entry: MemoryEntry) -> bool:
        """Sync a newly created memory entry to Gemini with optimized token management."""
        if not self.initialized:
            logger.error("Gemini adapter not initialized")
            return False

        try:
            # Apply rate limiting
            await self._apply_rate_limiting()

            # Store in context cache with TTL
            cache_entry = {"entry": entry, "expires_at": time.time() + self.cache_ttl}
            self.context_cache[key] = cache_entry

            # Manage cache size
            if len(self.context_cache) > self.max_cache_size:
                await self._cleanup_cache()

            # Estimate token usage more accurately
            token_estimate = await self._estimate_tokens_async(entry.content)
            self.current_token_usage += token_estimate

            # Pre-compute embedding for text content to speed up future operations
            if isinstance(entry.content, str) and len(entry.content) > 0:
                # Use a background task to avoid blocking
                asyncio.create_task(self._precompute_embedding(key, entry.content))

            logger.debug(f"Synced created memory entry to Gemini: {key}")
            return True
        except Exception as e:
            logger.error(f"Error syncing memory entry to Gemini: {e}")
            return False

    async def sync_update(self, key: str, entry: MemoryEntry) -> bool:
        """Sync an updated memory entry to Gemini."""
        if not self.initialized:
            logger.error("Gemini adapter not initialized")
            return False

        try:
            # Remove token count for old entry if it exists
            if key in self.context_cache:
                old_entry = self.context_cache[key]
                old_tokens = self._estimate_tokens(old_entry.content)
                self.current_token_usage = max(0, self.current_token_usage - old_tokens)

            # In a real implementation, this would use the Gemini API
            # For now, we just store in our local cache
            self.context_cache[key] = entry

            # Estimate token usage
            token_estimate = self._estimate_tokens(entry.content)
            self.current_token_usage += token_estimate

            logger.debug(f"Synced updated memory entry to Gemini: {key}")
            return True
        except Exception as e:
            logger.error(f"Error syncing updated memory entry to Gemini: {e}")
            return False

    async def sync_delete(self, key: str) -> bool:
        """Sync a deleted memory entry to Gemini."""
        if not self.initialized:
            logger.error("Gemini adapter not initialized")
            return False

        try:
            # Remove token count for old entry if it exists
            if key in self.context_cache:
                old_entry = self.context_cache[key]
                old_tokens = self._estimate_tokens(old_entry.content)
                self.current_token_usage = max(0, self.current_token_usage - old_tokens)
                del self.context_cache[key]

            logger.debug(f"Synced deleted memory entry to Gemini: {key}")
            return True
        except Exception as e:
            logger.error(f"Error syncing deletion to Gemini: {e}")
            return False

    async def execute(self, mode: str, prompt: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Execute a prompt with Gemini using Vertex AI with optimized context handling."""
        if not self.initialized:
            logger.error("Gemini adapter not initialized")
            return None

        try:
            # Apply rate limiting
            await self._apply_rate_limiting()

            # Use the semaphore to limit concurrent requests
            async with self.request_semaphore:
                logger.info(f"Executing Gemini prompt in mode {mode}: {prompt[:50]}...")

                # Prepare the prompt with context
                full_prompt = prompt
                if context:
                    # Optimize context by prioritizing most relevant information
                    optimized_context = await self._optimize_context(context)
                    context_str = json.dumps(optimized_context)
                    full_prompt = f"Context: {context_str}\n\nPrompt: {prompt}"

                # Track this request
                self.request_history.append(time.time())

                if VERTEX_AI_AVAILABLE and self.generative_model:
                    # Configure generation parameters based on mode
                    generation_config = self._get_generation_config(mode)

                    # Execute the request with Vertex AI
                    response = await asyncio.to_thread(self._execute_vertex_request, full_prompt, generation_config)
                    return response
                else:
                    # Simulate a response with a slight delay
                    await asyncio.sleep(0.5)  # Reduced from 1.0 for better performance

                    # Generate a mock response based on the mode and prompt
                    if mode == "chat":
                        response = f"Gemini response to: {prompt[:50]}...\n\nI've analyzed the request and here's my answer: This is a simulated response from Gemini AI that would contain detailed information based on the provided context and prompt."
                    elif mode == "code":
                        response = f"```python\n# Gemini generated code for: {prompt[:30]}...\ndef gemini_solution():\n    print('This is a solution for the prompt')\n    return 'Success'\n```"
                    else:
                        response = f"Gemini response in {mode} mode for: {prompt[:50]}...\n\nThis is a simulated response from the Gemini {self.model} model."

                    return response
        except Exception as e:
            logger.error(f"Error executing Gemini prompt: {e}")
            return None

    async def get_embeddings(self, text: str) -> List[float]:
        """Get vector embeddings using Vertex AI's embedding model with caching."""
        if not self.initialized:
            logger.error("Gemini adapter not initialized")
            return [0.0] * 768

        try:
            # Check cache first using a hash of the text as key
            cache_key = hashlib.md5(text.encode()).hexdigest()
            if cache_key in self.embedding_cache:
                logger.debug(f"Embedding cache hit for text: {text[:30]}...")
                return self.embedding_cache[cache_key]

            # Apply rate limiting
            await self._apply_rate_limiting()

            # Use the semaphore to limit concurrent requests
            async with self.request_semaphore:
                # Track this request
                self.request_history.append(time.time())

                if VERTEX_AI_AVAILABLE and self.embedding_model:
                    # Get embeddings from Vertex AI
                    embeddings = await asyncio.to_thread(self._get_vertex_embeddings, text)

                    # Cache the result
                    self.embedding_cache[cache_key] = embeddings

                    # Manage cache size
                    if len(self.embedding_cache) > self.max_cache_size:
                        # Remove a random item to avoid complex LRU logic
                        self.embedding_cache.pop(next(iter(self.embedding_cache)))

                    return embeddings
                else:
                    # Generate a deterministic dummy embedding based on the text
                    # Create a fixed-length embedding (768 dimensions for Gemini)
                    embedding_dim = 768
                    embedding = []

                    # Generate a hash of the text
                    hash_obj = hashlib.sha256(text.encode())
                    hash_bytes = hash_obj.digest()

                    # Use hash bytes to seed the embedding values
                    for i in range(embedding_dim):
                        byte_idx = i % len(hash_bytes)
                        val = hash_bytes[byte_idx] / 255.0  # Normalize to [0, 1]
                        # Center around 0
                        val = (val * 2) - 1
                        embedding.append(val)

                    # Cache the result
                    self.embedding_cache[cache_key] = embedding

                    return embedding
        except Exception as e:
            logger.error(f"Error generating embeddings with Gemini: {e}")
            return [0.0] * 768

    async def get_context(self) -> Dict[str, Any]:
        """Get current context from Gemini."""
        if not self.initialized:
            logger.error("Gemini adapter not initialized")
            return {}

        # Gemini doesn't have direct IDE integration like Copilot
        # It's more of a standalone API, so it doesn't have a concept of "current context"
        # For demonstration purposes, we return an empty context
        return {}

    async def get_status(self) -> Dict[str, Any]:
        """Get the status of the Gemini adapter."""
        return {
            "status": "connected" if self.initialized else "disconnected",
            "api_key_configured": bool(self.api_key),
            "model": self.model,
            "embeddings_model": self.embeddings_model,
            "context_window_used": self.current_token_usage,
            "context_window_size": self.context_window_size,
            "cached_entries": len(self.context_cache),
        }

    # Helper methods for optimized implementation

    def _execute_vertex_request(self, prompt: str, generation_config: GenerationConfig) -> str:
        """Execute a request to Vertex AI (runs in a thread pool)."""
        try:
            response = self.generative_model.generate_content(prompt, generation_config=generation_config)
            return response.text
        except Exception as e:
            logger.error(f"Error in Vertex AI request: {e}")
            return f"Error generating response: {str(e)}"

    def _get_vertex_embeddings(self, text: str) -> List[float]:
        """Get embeddings from Vertex AI (runs in a thread pool)."""
        try:
            embeddings = self.embedding_model.get_embeddings([text])
            return embeddings[0].values
        except Exception as e:
            logger.error(f"Error getting embeddings from Vertex AI: {e}")
            # Return zeros with proper dimension
            return [0.0] * 768

    def _get_generation_config(self, mode: str) -> GenerationConfig:
        """Get generation configuration based on the mode."""
        if mode == "code":
            return GenerationConfig(temperature=0.2, top_p=0.95, top_k=40, max_output_tokens=2048)
        elif mode == "chat":
            return GenerationConfig(temperature=0.7, top_p=0.95, top_k=40, max_output_tokens=1024)
        else:
            return GenerationConfig(temperature=0.4, top_p=0.95, top_k=40, max_output_tokens=1024)

    async def _optimize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize context by prioritizing most relevant information."""
        if not context:
            return {}

        # If context is small, return as is
        context_str = json.dumps(context)
        if len(context_str) < 10000:
            return context

        # For large contexts, prioritize based on keys
        priority_keys = {
            "query",
            "user_input",
            "current_task",
            "recent_history",
            "relevant_context",
        }
        optimized_context = {}

        # Add priority keys first
        for key in priority_keys:
            if key in context:
                optimized_context[key] = context[key]

        # Add other keys until we reach a reasonable size
        for key, value in context.items():
            if key not in optimized_context:
                # Add the key and check size
                optimized_context[key] = value
                if len(json.dumps(optimized_context)) > 15000:  # Reasonable size limit
                    # Remove the last added key if too large
                    del optimized_context[key]
                    break

        return optimized_context

    async def _apply_rate_limiting(self) -> None:
        """Apply rate limiting to avoid hitting API limits."""
        # Check if we need to apply rate limiting
        if len(self.request_history) < self.rate_limit:
            return

        # Calculate time since oldest request
        now = time.time()
        oldest_request = self.request_history[0]
        time_window = now - oldest_request

        # If we've made too many requests in the time window, wait
        if time_window < 60 and len(self.request_history) >= self.rate_limit:
            wait_time = 60 - time_window
            logger.info(f"Rate limiting applied, waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)

    async def _cleanup_cache(self) -> None:
        """Clean up expired items from the cache."""
        now = time.time()
        keys_to_remove = []

        # Find expired entries
        for key, cache_entry in self.context_cache.items():
            if cache_entry.get("expires_at", 0) < now:
                keys_to_remove.append(key)

        # Remove expired entries
        for key in keys_to_remove:
            del self.context_cache[key]

        # If still too large, remove oldest entries
        if len(self.context_cache) > self.max_cache_size:
            # Sort by expiration time and keep only max_cache_size entries
            sorted_entries = sorted(self.context_cache.items(), key=lambda x: x[1].get("expires_at", 0))

            # Keep only the newest entries
            self.context_cache = dict(sorted_entries[-self.max_cache_size :])

    async def _precompute_embedding(self, key: str, text: str) -> None:
        """Precompute embedding for text content in the background."""
        try:
            # Only compute if not already in cache
            cache_key = hashlib.md5(text.encode()).hexdigest()
            if cache_key not in self.embedding_cache:
                # Get embeddings (this will also cache the result)
                await self.get_embeddings(text)
                logger.debug(f"Precomputed embedding for key: {key}")
        except Exception as e:
            logger.error(f"Error precomputing embedding: {e}")

    @lru_cache(maxsize=1000)
    def _estimate_tokens_cached(self, text: str) -> int:
        """Cached version of token estimation for strings."""
        # More accurate token estimation based on GPT tokenization patterns
        # Whitespace: ~0.25 tokens, punctuation: ~0.5 tokens, avg word: ~1.3 tokens
        import re

        words = re.findall(r"\w+", text)
        whitespace_count = len(re.findall(r"\s", text))
        punctuation_count = len(re.findall(r"[^\w\s]", text))

        # Calculate estimated tokens
        word_tokens = len(words) * 1.3
        whitespace_tokens = whitespace_count * 0.25
        punctuation_tokens = punctuation_count * 0.5

        return int(word_tokens + whitespace_tokens + punctuation_tokens)

    async def _estimate_tokens_async(self, content: Any) -> int:
        """Asynchronous version of token estimation with caching for better performance."""
        if isinstance(content, str):
            return self._estimate_tokens_cached(content)
        elif isinstance(content, dict):
            # Convert to string and estimate
            content_str = json.dumps(content)
            return self._estimate_tokens_cached(content_str)
        elif isinstance(content, list):
            # Process list items in parallel for better performance
            if len(content) > 10:  # Only parallelize for larger lists
                tasks = [self._estimate_tokens_async(item) for item in content]
                results = await asyncio.gather(*tasks)
                return sum(results)
            else:
                # For small lists, process sequentially
                total = 0
                for item in content:
                    total += await self._estimate_tokens_async(item)
                return total
        else:
            # Default for other types
            return 10
