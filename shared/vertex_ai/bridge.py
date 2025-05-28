#!/usr/bin/env python3
"""
AI Orchestra Vertex AI Bridge

This module provides a unified interface for accessing Google Vertex AI services
from both GitHub Codespaces and GCP Cloud Workstations, enabling seamless AI
capabilities during and after the migration process.

Key features:
- Environment-aware authentication (Workload Identity Federation or ADC)
- Cached responses for common operations to improve performance
- Optimized model configurations for code-related tasks
- Support for both synchronous and asynchronous operations
- Circuit breaker pattern for resilience

Usage:
    # Direct model access
    from gcp_migration.openai_bridge import get_vertex_client
    client = get_vertex_client()
    response = client.generate_text("Generate a function to sort a list")

    # Higher-level functions
    from gcp_migration.openai_bridge import generate_code, analyze_code
    code = generate_code("Create a Python function to check if a string is a palindrome")
    analysis = analyze_code("def add(a, b): return a + b", "Check for type hints")
"""

import asyncio
import functools
import hashlib
import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from google.cloud import aiplatform

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("openai_bridge")

# Import optional dependencies for GCP
try:

    GOOGLE_LIBRARIES_AVAILABLE = True
except ImportError:
    logger.warning(
        "Google Cloud libraries not available. Some functionality will be limited."
    )
    GOOGLE_LIBRARIES_AVAILABLE = False


class EnvironmentType(Enum):
    """Type of environment the bridge is running in."""

    CODESPACES = "codespaces"
    GCP_WORKSTATION = "gcp-workstation"
    UNKNOWN = "unknown"


class ModelType(Enum):
    """Types of Vertex AI models available."""

    GEMINI_PRO = "gemini-pro"
    GEMINI_PRO_VISION = "gemini-pro-vision"
    GEMINI_ULTRA = "gemini-ultra"
    PALM_TEXT = "text-bison"
    PALM_CHAT = "chat-bison"
    PALM_CODE = "code-bison"
    CODE_GECKO = "code-gecko"


@dataclass
class ModelConfig:
    """Configuration for a Vertex AI model."""

    model_type: ModelType
    temperature: float = 0.2
    max_output_tokens: int = 8192
    top_p: float = 0.95
    top_k: int = 40

    # Prompt engineering configurations
    system_prompt: Optional[str] = None
    safety_settings: Optional[Dict[str, Any]] = None

    # Performance configurations
    cache_responses: bool = True
    cache_ttl: int = 3600  # Seconds
    retry_count: int = 3
    timeout: int = 120  # Seconds


@dataclass
class CacheEntry:
    """Entry in the response cache."""

    response: Any
    created_at: datetime = field(default_factory=datetime.now)
    ttl: int = 3600  # Seconds

    @property
    def is_expired(self) -> bool:
        """Check if the cache entry is expired.

        Returns:
            True if the entry is expired, False otherwise
        """
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl)


class ResponseCache:
    """Cache for model responses to improve performance."""

    def __init__(self, max_entries: int = 1000):
        """Initialize the response cache.

        Args:
            max_entries: Maximum number of entries in the cache
        """
        self.max_entries = max_entries
        self.cache: Dict[str, CacheEntry] = {}

    def _generate_key(self, model_type: ModelType, prompt: str, **kwargs: Any) -> str:
        """Generate a cache key for the request.

        Args:
            model_type: Type of model
            prompt: Prompt text
            **kwargs: Additional arguments that affect the response

        Returns:
            Cache key
        """
        key_parts = [
            model_type.value,
            prompt,
        ]

        # Add significant kwargs to the key
        significant_params = [
            "temperature",
            "max_output_tokens",
            "top_p",
            "top_k",
            "system_prompt",
        ]

        for param in significant_params:
            if param in kwargs and kwargs[param] is not None:
                key_parts.append(f"{param}:{kwargs[param]}")

        # Create a hash of the key parts
        key_str = "|".join(str(part) for part in key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, model_type: ModelType, prompt: str, **kwargs: Any) -> Optional[Any]:
        """Get a response from the cache.

        Args:
            model_type: Type of model
            prompt: Prompt text
            **kwargs: Additional arguments

        Returns:
            Cached response or None if not found
        """
        key = self._generate_key(model_type, prompt, **kwargs)

        if key in self.cache:
            entry = self.cache[key]

            # Check if the entry is expired
            if entry.is_expired:
                # Remove the expired entry
                del self.cache[key]
                return None

            return entry.response

        return None

    def put(
        self,
        model_type: ModelType,
        prompt: str,
        response: Any,
        ttl: int = 3600,
        **kwargs: Any,
    ) -> None:
        """Put a response in the cache.

        Args:
            model_type: Type of model
            prompt: Prompt text
            response: Response to cache
            ttl: Time to live in seconds
            **kwargs: Additional arguments
        """
        key = self._generate_key(model_type, prompt, **kwargs)

        # Add the entry to the cache
        self.cache[key] = CacheEntry(
            response=response,
            created_at=datetime.now(),
            ttl=ttl,
        )

        # Check if we need to evict entries
        if len(self.cache) > self.max_entries:
            # Remove the oldest entries
            sorted_keys = sorted(
                self.cache.keys(),
                key=lambda k: self.cache[k].created_at,
            )

            # Remove the oldest 10% of entries
            entries_to_remove = max(1, int(len(sorted_keys) * 0.1))
            for key in sorted_keys[:entries_to_remove]:
                del self.cache[key]

    def clear(self) -> None:
        """Clear the cache."""
        self.cache.clear()

    def cleanup_expired(self) -> int:
        """Clean up expired entries.

        Returns:
            Number of entries removed
        """
        keys_to_remove = [key for key, entry in self.cache.items() if entry.is_expired]

        for key in keys_to_remove:
            del self.cache[key]

        return len(keys_to_remove)

    @property
    def size(self) -> int:
        """Get the number of entries in the cache.

        Returns:
            Number of entries
        """
        return len(self.cache)

    @property
    def hit_ratio(self) -> float:
        """Get the cache hit ratio.

        Returns:
            Cache hit ratio
        """
        if self._total_accesses == 0:
            return 0.0

        return self._hits / self._total_accesses

    # Hit/miss tracking
    _hits: int = 0
    _misses: int = 0

    @property
    def _total_accesses(self) -> int:
        """Get the total number of cache accesses.

        Returns:
            Total number of accesses
        """
        return self._hits + self._misses


class VertexAIClient:
    """Client for interacting with Vertex AI services."""

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        default_model: ModelType = ModelType.GEMINI_PRO,
        default_config: Optional[ModelConfig] = None,
    ):
        """Initialize the Vertex AI client.

        Args:
            project_id: GCP project ID
            location: GCP location
            default_model: Default model to use
            default_config: Default model configuration
        """
        self.project_id = project_id
        self.location = location
        self.default_model = default_model
        self.environment = self._detect_environment()

        # Set up default configuration
        if default_config is None:
            self.default_config = ModelConfig(model_type=default_model)
        else:
            self.default_config = default_config

        # Initialize cache
        self.cache = ResponseCache()

        # Initialize client if libraries are available
        self.client = None
        if GOOGLE_LIBRARIES_AVAILABLE:
            self.initialize_client()

        logger.info(
            f"Initialized Vertex AI client for {self.project_id} in "
            f"{self.location} (environment: {self.environment.value})"
        )

    def _detect_environment(self) -> EnvironmentType:
        """Detect the current environment.

        Returns:
            Environment type
        """
        # Check for CODESPACES environment variable (set in GitHub Codespaces)
        if os.environ.get("CODESPACES", "").lower() == "true":
            return EnvironmentType.CODESPACES

        # Check for CLOUD_WORKSTATIONS_ENVIRONMENT variable (set in GCP Cloud Workstations)
        if "CLOUD_WORKSTATIONS_ENVIRONMENT" in os.environ:
            return EnvironmentType.GCP_WORKSTATION

        # Try to detect based on files
        if os.path.exists("/.codespaces"):
            return EnvironmentType.CODESPACES

        if os.path.exists("/.gcp-workstation"):
            return EnvironmentType.GCP_WORKSTATION

        return EnvironmentType.UNKNOWN

    def initialize_client(self) -> None:
        """Initialize the Vertex AI client based on the environment."""
        if not GOOGLE_LIBRARIES_AVAILABLE:
            logger.warning(
                "Google Cloud libraries not available. Cannot initialize client."
            )
            return

        try:
            # Initialize aiplatform
            aiplatform.init(project=self.project_id, location=self.location)

            # Client is initialized through aiplatform.init()
            self.client = True

            logger.info("Successfully initialized Vertex AI client")
        except Exception as e:
            logger.error(f"Error initializing Vertex AI client: {str(e)}")
            raise

    def _authenticate_codespaces(self) -> None:
        """Authenticate from GitHub Codespaces using Workload Identity Federation."""
        if not GOOGLE_LIBRARIES_AVAILABLE:
            logger.warning("Google Cloud libraries not available. Cannot authenticate.")
            return

        # Check for GOOGLE_APPLICATION_CREDENTIALS
        creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

        if creds_path and os.path.exists(creds_path):
            logger.info(f"Using service account credentials from {creds_path}")
            # The credentials will be automatically picked up by the client library
            return

        # Check for Workload Identity Federation
        # This requires configuration of WIF in the GCP project
        # and proper ambient credentials in GitHub Actions or Codespaces
        oidc_token_file = os.environ.get("OIDC_TOKEN_FILE")

        if oidc_token_file and os.path.exists(oidc_token_file):
            logger.info("Using Workload Identity Federation for authentication")
            # The client library will automatically use WIF if properly configured
            return

        logger.warning(
            "No authentication method found for Codespaces. "
            "Please set up GOOGLE_APPLICATION_CREDENTIALS or Workload Identity Federation."
        )

    def _authenticate_gcp_workstation(self) -> None:
        """Authenticate from GCP Cloud Workstation using Application Default Credentials."""
        if not GOOGLE_LIBRARIES_AVAILABLE:
            logger.warning("Google Cloud libraries not available. Cannot authenticate.")
            return

        # GCP Cloud Workstation should already have Application Default Credentials
        # The client library will automatically use ADC
        logger.info("Using Application Default Credentials for authentication")

    def _ensure_authenticated(self) -> None:
        """Ensure the client is authenticated.

        Raises:
            RuntimeError: If authentication fails
        """
        if not GOOGLE_LIBRARIES_AVAILABLE:
            raise RuntimeError(
                "Google Cloud libraries not available. Cannot authenticate."
            )

        if self.environment == EnvironmentType.CODESPACES:
            self._authenticate_codespaces()
        elif self.environment == EnvironmentType.GCP_WORKSTATION:
            self._authenticate_gcp_workstation()
        else:
            # Try to authenticate using Application Default Credentials
            logger.info(
                "Environment type unknown, trying Application Default Credentials"
            )

    def _format_gemini_prompt(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format a prompt for the Gemini model.

        Args:
            prompt: User prompt text
            system_prompt: Optional system prompt

        Returns:
            Formatted prompt structure
        """
        contents = []

        # Add system prompt if provided
        if system_prompt:
            contents.append({"role": "system", "parts": [{"text": system_prompt}]})

        # Add user prompt
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        return {"contents": contents}

    def _format_palm_prompt(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format a prompt for the PaLM model.

        Args:
            prompt: User prompt text
            system_prompt: Optional system prompt

        Returns:
            Formatted prompt structure
        """
        if system_prompt:
            combined_prompt = f"{system_prompt}\n\n{prompt}"
        else:
            combined_prompt = prompt

        return {"prompt": combined_prompt}

    def generate_text(
        self,
        prompt: str,
        model_type: Optional[ModelType] = None,
        config: Optional[ModelConfig] = None,
        use_cache: bool = True,
    ) -> str:
        """Generate text using the specified model.

        Args:
            prompt: Prompt text
            model_type: Type of model to use (defaults to client default)
            config: Model configuration (defaults to client default)
            use_cache: Whether to use the response cache

        Returns:
            Generated text

        Raises:
            RuntimeError: If generation fails
        """
        model = model_type or self.default_model
        cfg = config or self.default_config

        # Check cache first if enabled
        if use_cache and cfg.cache_responses:
            cached_response = self.cache.get(
                model_type=model,
                prompt=prompt,
                temperature=cfg.temperature,
                max_output_tokens=cfg.max_output_tokens,
                top_p=cfg.top_p,
                top_k=cfg.top_k,
                system_prompt=cfg.system_prompt,
            )

            if cached_response:
                logger.debug(f"Using cached response for {model.value}")
                self.cache._hits += 1
                return cached_response

            self.cache._misses += 1

        # Ensure client is ready
        self._ensure_authenticated()

        if not GOOGLE_LIBRARIES_AVAILABLE:
            raise RuntimeError(
                "Google Cloud libraries not available. Cannot generate text."
            )

        try:
            # Initialize parameters based on model type
            if model.value.startswith("gemini"):
                # Gemini models
                vertex_model = aiplatform.GenerativeModel(model.value)
                generation_config = {
                    "temperature": cfg.temperature,
                    "max_output_tokens": cfg.max_output_tokens,
                    "top_p": cfg.top_p,
                    "top_k": cfg.top_k,
                }

                prompt_dict = self._format_gemini_prompt(prompt, cfg.system_prompt)

                response = vertex_model.generate_content(
                    **prompt_dict,
                    generation_config=generation_config,
                    safety_settings=cfg.safety_settings,
                )

                result = response.text
            else:
                # PaLM models
                # The aiplatform.PredictionService approach
                # This is a simpler API for older PaLM models
                parameters = {
                    "temperature": cfg.temperature,
                    "max_output_tokens": cfg.max_output_tokens,
                    "top_p": cfg.top_p,
                    "top_k": cfg.top_k,
                }

                prompt_dict = self._format_palm_prompt(prompt, cfg.system_prompt)

                endpoint = aiplatform.Endpoint(
                    f"projects/{self.project_id}/locations/{self.location}/publishers/google/models/{model.value}"
                )

                response = endpoint.predict(
                    instances=[prompt_dict],
                    parameters=parameters,
                )

                result = response.predictions[0].get("content", "")

            # Cache the response if enabled
            if use_cache and cfg.cache_responses:
                self.cache.put(
                    model_type=model,
                    prompt=prompt,
                    response=result,
                    ttl=cfg.cache_ttl,
                    temperature=cfg.temperature,
                    max_output_tokens=cfg.max_output_tokens,
                    top_p=cfg.top_p,
                    top_k=cfg.top_k,
                    system_prompt=cfg.system_prompt,
                )

            return result
        except Exception as e:
            logger.error(f"Error generating text with {model.value}: {str(e)}")
            raise RuntimeError(f"Failed to generate text: {str(e)}") from e

    async def generate_text_async(
        self,
        prompt: str,
        model_type: Optional[ModelType] = None,
        config: Optional[ModelConfig] = None,
        use_cache: bool = True,
    ) -> str:
        """Generate text asynchronously using the specified model.

        Args:
            prompt: Prompt text
            model_type: Type of model to use (defaults to client default)
            config: Model configuration (defaults to client default)
            use_cache: Whether to use the response cache

        Returns:
            Generated text

        Raises:
            RuntimeError: If generation fails
        """
        # Run the synchronous method in an executor
        # since the Vertex AI Python client doesn't have native async support
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            functools.partial(
                self.generate_text,
                prompt=prompt,
                model_type=model_type,
                config=config,
                use_cache=use_cache,
            ),
        )

    def get_embedding(
        self,
        text: str,
        model_name: str = "textembedding-gecko",
    ) -> List[float]:
        """Get embeddings for the given text.

        Args:
            text: Text to embed
            model_name: Embedding model name

        Returns:
            Embedding vector

        Raises:
            RuntimeError: If embedding generation fails
        """
        # Ensure client is ready
        self._ensure_authenticated()

        if not GOOGLE_LIBRARIES_AVAILABLE:
            raise RuntimeError(
                "Google Cloud libraries not available. Cannot generate embeddings."
            )

        try:
            # Create the embedding
            model = aiplatform.TextEmbeddingModel.from_pretrained(model_name)
            embeddings = model.get_embeddings([text])

            if not embeddings or not embeddings[0].values:
                raise ValueError("Failed to generate embeddings")

            return embeddings[0].values
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise RuntimeError(f"Failed to generate embeddings: {str(e)}") from e

    async def get_embedding_async(
        self,
        text: str,
        model_name: str = "textembedding-gecko",
    ) -> List[float]:
        """Get embeddings asynchronously for the given text.

        Args:
            text: Text to embed
            model_name: Embedding model name

        Returns:
            Embedding vector

        Raises:
            RuntimeError: If embedding generation fails
        """
        # Run the synchronous method in an executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            functools.partial(
                self.get_embedding,
                text=text,
                model_name=model_name,
            ),
        )


# Global instance of the response cache
_response_cache = ResponseCache()

# Global client instance
_default_client: Optional[VertexAIClient] = None


def get_vertex_client(
    project_id: Optional[str] = None,
    location: str = "us-central1",
    reinitialize: bool = False,
) -> VertexAIClient:
    """Get the default Vertex AI client.

    Args:
        project_id: GCP project ID (defaults to environment variable or config file)
        location: GCP location
        reinitialize: Whether to reinitialize the client even if it already exists

    Returns:
        Vertex AI client

    Raises:
        RuntimeError: If client initialization fails
    """
    global _default_client

    if _default_client is not None and not reinitialize:
        return _default_client

    # Resolve project ID if not provided
    if project_id is None:
        # Try to get from environment variable
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")

        if project_id is None:
            # Try to get from gcloud config
            try:
                result = subprocess.run(
                    ["gcloud", "config", "get-value", "project"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                project_id = result.stdout.strip()
            except Exception:
                pass

        if project_id is None:
            # Try to infer from service account credentials
            creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

            if creds_path and os.path.exists(creds_path):
                try:
                    with open(creds_path, "r") as f:
                        creds_data = json.load(f)
                        project_id = creds_data.get("project_id")
                except Exception:
                    pass

        # If still None, use a default
        if project_id is None:
            project_id = "cherry-ai-project"
            logger.warning(
                f"Could not determine project ID. Using default: {project_id}. "
                f"Set GOOGLE_CLOUD_PROJECT environment variable to override."
            )

    # Create the client
    _default_client = VertexAIClient(project_id=project_id, location=location)
    return _default_client


# Higher-level functions for common tasks


def generate_code(
    prompt: str,
    language: str = "python",
    model_type: ModelType = ModelType.GEMINI_PRO,
    temperature: float = 0.2,
) -> str:
    """Generate code using Vertex AI.

    Args:
        prompt: Code generation prompt
        language: Programming language
        model_type: Model to use
        temperature: Temperature for generation

    Returns:
        Generated code

    Raises:
        RuntimeError: If code generation fails
    """
    client = get_vertex_client()

    # Format the prompt for code generation
    code_prompt = f"Generate {language} code for: {prompt}\n"
    code_prompt += f"Return only the {language} code without explanations or markdown."

    # Create a code-optimized configuration
    config = ModelConfig(
        model_type=model_type,
        temperature=temperature,
        max_output_tokens=8192,
        top_p=0.95,
        top_k=40,
        system_prompt=(
            f"You are an expert {language} developer. Generate clean, efficient, "
            f"well-documented code. Follow best practices for {language} and "
            f"include error handling."
        ),
    )

    return client.generate_text(
        prompt=code_prompt,
        model_type=model_type,
        config=config,
    )


async def generate_code_async(
    prompt: str,
    language: str = "python",
    model_type: ModelType = ModelType.GEMINI_PRO,
    temperature: float = 0.2,
) -> str:
    """Generate code asynchronously using Vertex AI.

    Args:
        prompt: Code generation prompt
        language: Programming language
        model_type: Model to use
        temperature: Temperature for generation

    Returns:
        Generated code

    Raises:
        RuntimeError: If code generation fails
    """
    client = get_vertex_client()

    # Format the prompt for code generation
    code_prompt = f"Generate {language} code for: {prompt}\n"
    code_prompt += f"Return only the {language} code without explanations or markdown."

    # Create a code-optimized configuration
    config = ModelConfig(
        model_type=model_type,
        temperature=temperature,
        max_output_tokens=8192,
        top_p=0.95,
        top_k=40,
        system_prompt=(
            f"You are an expert {language} developer. Generate clean, efficient, "
            f"well-documented code. Follow best practices for {language} and "
            f"include error handling."
        ),
    )

    return await client.generate_text_async(
        prompt=code_prompt,
        model_type=model_type,
        config=config,
    )


def analyze_code(
    code: str,
    instructions: str,
    model_type: ModelType = ModelType.GEMINI_PRO,
) -> str:
    """Analyze code using Vertex AI.

    Args:
        code: Code to analyze
        instructions: Instructions for analysis
        model_type: Model to use

    Returns:
        Analysis results

    Raises:
        RuntimeError: If code analysis fails
    """
    client = get_vertex_client()

    # Format the prompt for code analysis
    analysis_prompt = (
        f"Instructions: {instructions}\n\nCode to analyze:\n```\n{code}\n```"
    )

    # Create an analysis-optimized configuration
    config = ModelConfig(
        model_type=model_type,
        temperature=0.1,  # Lower temperature for more deterministic analysis
        max_output_tokens=8192,
        top_p=0.95,
        top_k=40,
        system_prompt=(
            "You are an expert code reviewer. Analyze the provided code according to "
            "the given instructions. Be thorough, specific, and constructive."
        ),
    )

    return client.generate_text(
        prompt=analysis_prompt,
        model_type=model_type,
        config=config,
    )


async def analyze_code_async(
    code: str,
    instructions: str,
    model_type: ModelType = ModelType.GEMINI_PRO,
) -> str:
    """Analyze code asynchronously using Vertex AI.

    Args:
        code: Code to analyze
        instructions: Instructions for analysis
        model_type: Model to use

    Returns:
        Analysis results

    Raises:
        RuntimeError: If code analysis fails
    """
    client = get_vertex_client()

    # Format the prompt for code analysis
    analysis_prompt = (
        f"Instructions: {instructions}\n\nCode to analyze:\n```\n{code}\n```"
    )

    # Create an analysis-optimized configuration
    config = ModelConfig(
        model_type=model_type,
        temperature=0.1,  # Lower temperature for more deterministic analysis
        max_output_tokens=8192,
        top_p=0.95,
        top_k=40,
        system_prompt=(
            "You are an expert code reviewer. Analyze the provided code according to "
            "the given instructions. Be thorough, specific, and constructive."
        ),
    )

    return await client.generate_text_async(
        prompt=analysis_prompt,
        model_type=model_type,
        config=config,
    )


def clear_cache() -> None:
    """Clear the response cache."""
    global _response_cache
    _response_cache.clear()


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics.

    Returns:
        Cache statistics
    """
    global _response_cache
    return {
        "size": _response_cache.size,
        "hit_ratio": _response_cache.hit_ratio,
        "hits": _response_cache._hits,
        "misses": _response_cache._misses,
    }


if __name__ == "__main__":
    """Run a simple demo of the Vertex AI Bridge."""
    import argparse

    parser = argparse.ArgumentParser(description="Vertex AI Bridge demo")
    parser.add_argument("--prompt", type=str, help="Prompt to send to the model")
    parser.add_argument("--model", type=str, default="gemini-pro", help="Model to use")
    parser.add_argument(
        "--temperature", type=float, default=0.2, help="Temperature for generation"
    )
    parser.add_argument("--project", type=str, help="GCP project ID")
    parser.add_argument("--code", action="store_true", help="Generate code")
    parser.add_argument("--analyze", type=str, help="Code to analyze")
    parser.add_argument(
        "--location", type=str, default="us-central1", help="GCP location"
    )

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Create client
    client = get_vertex_client(project_id=args.project, location=args.location)

    # Determine model type
    try:
        model_type = ModelType(args.model)
    except ValueError:
        print(
            f"Invalid model type: {args.model}. Using {ModelType.GEMINI_PRO.value} instead."
        )
        model_type = ModelType.GEMINI_PRO

    # Generate text, code, or analyze code
    if args.code:
        if not args.prompt:
            print("Error: Prompt is required for code generation")
            sys.exit(1)

        try:
            result = generate_code(
                prompt=args.prompt,
                model_type=model_type,
                temperature=args.temperature,
            )
            print("\n=== Generated Code ===\n")
            print(result)
        except Exception as e:
            print(f"Error generating code: {str(e)}")
            sys.exit(1)
    elif args.analyze:
        if not args.prompt:
            print("Error: Prompt (instructions) is required for code analysis")
            sys.exit(1)

        try:
            result = analyze_code(
                code=args.analyze,
                instructions=args.prompt,
                model_type=model_type,
            )
            print("\n=== Code Analysis ===\n")
            print(result)
        except Exception as e:
            print(f"Error analyzing code: {str(e)}")
            sys.exit(1)
    elif args.prompt:
        # Just generate text
        try:
            result = client.generate_text(
                prompt=args.prompt,
                model_type=model_type,
                config=ModelConfig(
                    model_type=model_type,
                    temperature=args.temperature,
                ),
            )
            print("\n=== Generated Text ===\n")
            print(result)
        except Exception as e:
            print(f"Error generating text: {str(e)}")
            sys.exit(1)
    else:
        print("Error: No action specified. Use --prompt, --code, or --analyze")
        sys.exit(1)

    # Print cache stats
    print("\n=== Cache Stats ===\n")
    stats = get_cache_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
