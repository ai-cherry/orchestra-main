"""
Service for interacting with Google Gemini LLM through Vertex AI.
"""
from typing import Dict, Any, List, Optional, Callable, Tuple
import json
import logging
import asyncio
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import lru_cache
from datetime import datetime

import backoff
from redis import Redis
from google.cloud import aiplatform
from google.cloud.aiplatform.gapic.schema import predict
from vertexai.preview.generative_models import (
    GenerativeModel,
    ChatSession,
    Part,
    Tool,
    FunctionDeclaration,
)
from google.api_core.exceptions import (
    GoogleAPIError,
    ResourceExhausted,
    ServiceUnavailable,
)

from app.config import settings
from app.services.admin_functions import (
    get_agent_status,
    start_agent,
    stop_agent,
    list_agents,
    prune_memory,
    promote_memory,
    get_memory_stats,
)

logger = logging.getLogger(__name__)

# Shared thread pool executor for all API calls
# This prevents thread pool exhaustion under load
_thread_pool = ThreadPoolExecutor(max_workers=10, thread_name_prefix="gemini-api-")

# Initialize Redis client if available
redis_client = (
    Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
    )
    if hasattr(settings, "REDIS_URL") and settings.REDIS_URL
    else None
)


@dataclass
class CircuitBreakerState:
    """
    Performance-optimized circuit breaker for Gemini API calls.
    Uses higher failure thresholds and shorter reset timeouts to maximize throughput.
    """

    failure_count: int = 0
    open_until: Optional[float] = None
    max_failures: int = 12  # Increased from 5 to allow more retries
    reset_timeout: float = 15.0  # Reduced from 30s to recover faster

    def record_failure(self) -> None:
        """Record a failure and potentially open the circuit, with fast path for common case."""
        self.failure_count += 1
        # Fast path optimization: Only calculate time and log when actually opening
        if self.failure_count >= self.max_failures:
            self.open_until = time.time() + self.reset_timeout
            logger.warning(
                f"Circuit breaker opened for {self.reset_timeout}s after {self.failure_count} failures"
            )

    def record_success(self) -> None:
        """Record a success using optimized approach."""
        # Only reset if we've had failures (avoid unnecessary writes)
        if self.failure_count > 0:
            self.failure_count = 0
            self.open_until = None

    def is_open(self) -> bool:
        """Optimized check if circuit is open (fastest path first)."""
        # Fast path for common case - not open
        if self.open_until is None:
            return False

        current_time = time.time()
        if current_time > self.open_until:
            # Reset after timeout - optimize by doing this in one step
            self.failure_count, self.open_until = 0, None
            return False
        return True


class GeminiAPIError(Exception):
    """Custom exception for Gemini API errors."""

    pass


class GeminiService:
    """
    Service for interacting with Google Gemini through Vertex AI.
    Includes caching, retry logic, and circuit breaking for improved resilience.
    """

    def __init__(self, project_id: str, location: str, model_id: str):
        """
        Initialize the Gemini service.

        Args:
            project_id: GCP project ID
            location: Vertex AI location (e.g., 'us-central1')
            model_id: Gemini model ID (e.g., 'gemini-2.5-pro-preview-05-06')
        """
        self.project_id = project_id
        self.location = location
        self.model_id = model_id

        # Initialize Vertex AI
        aiplatform.init(project=project_id, location=location)

        # Initialize Gemini model
        self.model = GenerativeModel(model_id)

        # Define available functions that Gemini can call
        self.tools = self._define_tools()

        # Circuit breaker for API calls
        self.circuit_breaker = CircuitBreakerState()

        # Enable caching if Redis is available
        self.enable_caching = redis_client is not None and settings.GEMINI_CACHE_ENABLED

        logger.info(
            f"GeminiService initialized with model {model_id}, "
            f"caching {'enabled' if self.enable_caching else 'disabled'}"
        )

    def _define_tools(self) -> List[Tool]:
        """
        Define tools (functions) that Gemini can call.

        Returns:
            List[Tool]: List of tools available for Gemini
        """
        functions = [
            FunctionDeclaration(
                name="get_agent_status",
                description="Get the current status of an agent",
                parameters={
                    "type": "object",
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "description": "ID of the agent to check",
                        }
                    },
                    "required": ["agent_id"],
                },
            ),
            FunctionDeclaration(
                name="start_agent",
                description="Start an agent",
                parameters={
                    "type": "object",
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "description": "ID of the agent to start",
                        }
                    },
                    "required": ["agent_id"],
                },
            ),
            FunctionDeclaration(
                name="stop_agent",
                description="Stop a running agent",
                parameters={
                    "type": "object",
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "description": "ID of the agent to stop",
                        }
                    },
                    "required": ["agent_id"],
                },
            ),
            FunctionDeclaration(
                name="list_agents",
                description="List all available agents",
                parameters={
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "Filter agents by status (running, stopped, all)",
                            "enum": ["running", "stopped", "all"],
                        }
                    },
                    "required": [],
                },
            ),
            FunctionDeclaration(
                name="prune_memory",
                description="Prune memory for an agent",
                parameters={
                    "type": "object",
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "description": "ID of the agent to prune memory for",
                        },
                        "older_than_days": {
                            "type": "integer",
                            "description": "Prune memories older than this many days",
                        },
                    },
                    "required": ["agent_id", "older_than_days"],
                },
            ),
            FunctionDeclaration(
                name="promote_memory",
                description="Promote a memory to a higher tier",
                parameters={
                    "type": "object",
                    "properties": {
                        "memory_id": {
                            "type": "string",
                            "description": "ID of the memory to promote",
                        },
                        "tier": {
                            "type": "string",
                            "description": "Target tier to promote to",
                            "enum": ["working", "long_term", "core"],
                        },
                    },
                    "required": ["memory_id", "tier"],
                },
            ),
            FunctionDeclaration(
                name="get_memory_stats",
                description="Get memory statistics for an agent",
                parameters={
                    "type": "object",
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "description": "ID of the agent to get memory stats for",
                        }
                    },
                    "required": ["agent_id"],
                },
            ),
        ]

        return [Tool(function_declarations=functions)]

    def _get_function_map(self) -> Dict[str, Callable]:
        """
        Create a mapping of function names to their implementations.

        Returns:
            Dict[str, Callable]: Mapping of function names to implementations
        """
        return {
            "get_agent_status": get_agent_status,
            "start_agent": start_agent,
            "stop_agent": stop_agent,
            "list_agents": list_agents,
            "prune_memory": prune_memory,
            "promote_memory": promote_memory,
            "get_memory_stats": get_memory_stats,
        }

    def _generate_cache_key(self, prefix: str, content: str, **kwargs) -> str:
        """
        Generate a cache key for Redis.

        Args:
            prefix: Prefix for the cache key
            content: Primary content
            **kwargs: Additional parameters that affect the response

        Returns:
            str: Cache key
        """
        # Create a string with all parameters that affect the result
        key_content = f"{content}:{json.dumps(kwargs, sort_keys=True)}"

        # Create a hash of the content
        key_hash = hashlib.md5(key_content.encode()).hexdigest()
        return f"gemini:{prefix}:{self.model_id}:{key_hash}"

    async def _call_with_backoff_and_circuit_breaker(
        self, func: Callable, *args, **kwargs
    ) -> Any:
        """
        Call a function with backoff retry and circuit breaker pattern.

        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Any: Function result

        Raises:
            GeminiAPIError: If the circuit is open or max retries are exceeded
        """
        # Check if circuit breaker is open
        if self.circuit_breaker.is_open():
            raise GeminiAPIError(
                "Circuit breaker is open due to multiple failures. " "Try again later."
            )

        @backoff.on_exception(
            backoff.expo,
            (GoogleAPIError, ResourceExhausted, ServiceUnavailable),
            max_tries=3,
            on_backoff=lambda details: logger.warning(
                f"Retrying Gemini API call after {details['wait']:.2f}s delay"
            ),
        )
        async def call_with_retry():
            start_time = time.time()
            try:
                # Use the shared thread pool for all API calls
                result = await asyncio.get_event_loop().run_in_executor(
                    _thread_pool, lambda: func(*args, **kwargs)
                )

                # Record success for circuit breaker
                self.circuit_breaker.record_success()

                # Log performance metrics
                elapsed = time.time() - start_time
                logger.info(f"Gemini API call completed in {elapsed:.2f}s")

                return result
            except Exception as e:
                # Record failure for circuit breaker
                self.circuit_breaker.record_failure()

                # Log error details
                elapsed = time.time() - start_time
                logger.error(
                    f"Gemini API call failed after {elapsed:.2f}s: {str(e)}",
                    exc_info=True,
                )
                raise

        return await call_with_retry()

    @backoff.on_exception(
        backoff.expo,
        (GoogleAPIError, ResourceExhausted, ServiceUnavailable),
        max_tries=3,
    )
    async def process_command(self, command: str) -> Dict[str, Any]:
        """
        Process a natural language command using Gemini.
        Includes retry logic and circuit breaking.

        Args:
            command: The natural language command to process

        Returns:
            Dict[str, Any]: The response from Gemini, including any function calls

        Raises:
            GeminiAPIError: If the request fails after retries or circuit breaker is open
        """
        start_time = time.time()
        logger.info(f"Processing command: {command}")

        try:
            # Check if circuit breaker is open
            if self.circuit_breaker.is_open():
                raise GeminiAPIError("Circuit breaker is open due to multiple failures")

            # Create a new chat session
            chat = self.model.start_chat(tools=self.tools)

            # Send the command to Gemini
            function_map = self._get_function_map()
            function_calls = []

            # Use the shared thread pool
            response = await self._call_with_backoff_and_circuit_breaker(
                lambda: chat.send_message(command, tools=self.tools)
            )

            # Handle function calling
            for function_call in response.candidates[0].content.parts[0].function_calls:
                function_name = function_call.name
                arguments = json.loads(function_call.args)

                logger.info(f"Function call: {function_name} with args: {arguments}")

                # Execute the function
                if function_name in function_map:
                    function_result = await function_map[function_name](**arguments)

                    # Add the function call to the list
                    function_calls.append(
                        {
                            "name": function_name,
                            "arguments": arguments,
                            "result": function_result,
                        }
                    )

                    # Send the function result back to Gemini
                    await self._call_with_backoff_and_circuit_breaker(
                        lambda: chat.send_message(
                            Part.from_function_response(
                                name=function_name, response=function_result
                            )
                        )
                    )
                else:
                    logger.warning(
                        f"Unknown function called by Gemini: {function_name}"
                    )

            # Get the final response
            result = {"response": response.text, "function_calls": function_calls}

            # Record success for circuit breaker
            self.circuit_breaker.record_success()

            # Log performance metrics
            elapsed = time.time() - start_time
            logger.info(f"Command processing completed in {elapsed:.2f}s")

            return result

        except Exception as e:
            # Record failure for circuit breaker
            self.circuit_breaker.record_failure()

            # Log error with details
            elapsed = time.time() - start_time
            logger.error(
                f"Command processing failed after {elapsed:.2f}s: {str(e)}",
                exc_info=True,
            )

            raise GeminiAPIError(f"Error processing command: {str(e)}")
        return result

    async def analyze_content(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
        analysis_type: str = "general",
    ) -> Dict[str, Any]:
        """
        Analyze content using Gemini with caching and retry logic.

        Args:
            content: The content to analyze
            context: Additional context for the analysis
            analysis_type: Type of analysis to perform

        Returns:
            Dict[str, Any]: Analysis results

        Raises:
            GeminiAPIError: If the request fails after retries
        """
        start_time = time.time()
        logger.info(
            f"Analyzing content with type: {analysis_type}, size: {len(content)} chars"
        )

        # Check cache if enabled
        if self.enable_caching and redis_client:
            cache_key = self._generate_cache_key(
                "analysis", content, context=context, analysis_type=analysis_type
            )

            # Try to get from cache
            cached_result = redis_client.get(cache_key)
            if cached_result:
                try:
                    logger.info(f"Cache hit for analysis request: {cache_key[:20]}...")
                    return json.loads(cached_result)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in cache: {cache_key[:20]}...")
                    # Continue with the analysis if cache is corrupted

        try:
            # Create the prompt based on the analysis type
            prompts = {
                "general": "Analyze the following content and provide key insights:",
                "logs": "Analyze the following logs and identify any errors, warnings, or anomalies:",
                "metrics": "Analyze the following metrics and identify trends, anomalies, or areas for optimization:",
                "memory": "Analyze the following memory data and provide insights on memory usage patterns and optimization opportunities:",
            }

            # Choose the appropriate prompt or use the general one
            prompt = prompts.get(analysis_type, prompts["general"])

            # Add context if provided
            if context:
                context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
                prompt += f"\n\nContext:\n{context_str}"

            # Add the content - truncate if too large to avoid token limits
            if len(content) > 30000:  # Approximate token limit protection
                content = content[:30000] + "...[CONTENT TRUNCATED]"
                logger.warning("Content truncated due to size limitations")

            prompt += f"\n\nContent:\n{content}"

            # Add specific instructions based on analysis type
            if analysis_type == "logs":
                prompt += "\n\nPlease structure your analysis with the following sections: Summary, Critical Issues, Warnings, Performance Insights, and Recommendations."
            elif analysis_type == "metrics":
                prompt += "\n\nPlease structure your analysis with the following sections: Summary, Key Metrics, Trends, Anomalies, and Recommendations."
            elif analysis_type == "memory":
                prompt += "\n\nPlease structure your analysis with the following sections: Summary, Memory Usage Patterns, Inefficiencies, and Optimization Recommendations."
            else:
                prompt += "\n\nPlease structure your analysis with the following sections: Summary, Key Insights, and Recommendations."

            prompt += "\n\nFormat your response as a structured JSON object with these sections."

            # Send the prompt to Gemini with backoff/retry
            response = await self._call_with_backoff_and_circuit_breaker(
                lambda: self.model.generate_content(prompt)
            )

            # Try to parse the response as JSON
            try:
                # First, try to extract just the JSON part if there's additional text
                if "```json" in response.text and "```" in response.text:
                    json_str = response.text.split("```json")[1].split("```")[0].strip()
                    analysis = json.loads(json_str)
                else:
                    analysis = json.loads(response.text)
            except json.JSONDecodeError:
                # If parsing fails, return the raw text in a structured format
                analysis = {
                    "summary": "Analysis completed but not in JSON format",
                    "raw_analysis": response.text,
                }

            # Store in cache if enabled
            if self.enable_caching and redis_client:
                try:
                    redis_client.setex(
                        cache_key, settings.REDIS_TTL, json.dumps(analysis)
                    )
                    logger.info(f"Analysis result cached with key: {cache_key[:20]}...")
                except Exception as e:
                    logger.warning(f"Failed to cache analysis result: {str(e)}")

            # Log performance metrics
            elapsed = time.time() - start_time
            logger.info(f"Content analysis completed in {elapsed:.2f}s")

            return analysis

        except Exception as e:
            # Record failure for circuit breaker
            self.circuit_breaker.record_failure()

            # Log error with details
            elapsed = time.time() - start_time
            logger.error(
                f"Content analysis failed after {elapsed:.2f}s: {str(e)}", exc_info=True
            )

            raise GeminiAPIError(f"Error analyzing content: {str(e)}")
        return analysis

    # Cache capabilities for improved performance
    @lru_cache(maxsize=1)
    async def get_capabilities(self) -> Dict[str, Any]:
        """
        Get available Gemini capabilities and functions.
        Results are cached to improve performance.

        Returns:
            Dict[str, Any]: Gemini capabilities info
        """
        functions = []
        for tool in self.tools:
            for func in tool.function_declarations:
                functions.append(
                    {
                        "name": func.name,
                        "description": func.description,
                        "parameters": func.parameters,
                    }
                )

        # Add status information
        result = {
            "model": self.model_id,
            "location": self.location,
            "project_id": self.project_id,
            "available_functions": functions,
            "caching_enabled": self.enable_caching,
            "circuit_breaker_state": "open"
            if self.circuit_breaker.is_open()
            else "closed",
            "circuit_breaker_failures": self.circuit_breaker.failure_count,
        }

        return result


@lru_cache()
def get_gemini_service() -> GeminiService:
    """
    Factory function for GeminiService instances.
    Used as a FastAPI dependency.

    Returns:
        GeminiService: The Gemini service instance
    """
    return GeminiService(
        project_id=settings.PROJECT_ID,
        location=settings.GEMINI_LOCATION,
        model_id=settings.GEMINI_MODEL_ID,
    )
