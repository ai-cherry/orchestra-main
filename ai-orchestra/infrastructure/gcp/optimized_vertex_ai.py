"""
Optimized Vertex AI service implementation for AI Orchestra.

This module provides an enhanced implementation of the Vertex AI service
with optimized request batching, semantic caching, and performance improvements.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union, Set, cast
import hashlib
import json

from google.cloud import aiplatform
from google.cloud.aiplatform.gapic.schema import predict
from vertexai.preview.generative_models import GenerativeModel, GenerationConfig

from ...core.interfaces.ai_service import AIService
from ...core.errors import (
    AIServiceError,
    ModelNotFoundError,
    ModelUnavailableError,
    InvalidInputError,
    AuthenticationError,
)
from ...core.config import get_settings
from ...utils.logging import log_event, log_start, log_end, log_error
from ..caching.tiered_cache import get_tiered_cache, cached, ModelCache, SemanticCache

logger = logging.getLogger(__name__)


class BatchProcessor:
    """
    Batch processor for Vertex AI requests.

    This class batches similar requests to improve throughput and
    reduce the number of API calls made to Vertex AI.
    """

    def __init__(
        self,
        max_batch_size: int = 10,
        max_wait_time: float = 0.05,  # 50ms
        min_batch_size: int = 2,
    ):
        """
        Initialize the batch processor.

        Args:
            max_batch_size: Maximum batch size
            max_wait_time: Maximum wait time in seconds
            min_batch_size: Minimum batch size to trigger processing
        """
        self.max_batch_size = max_batch_size
        self.max_wait_time = max_wait_time
        self.min_batch_size = min_batch_size
        self.batch_queue: List[Dict[str, Any]] = []
        self.lock = asyncio.Lock()
        self.processing = False
        self.timeout_task: Optional[asyncio.Task] = None

        # Statistics
        self.total_requests = 0
        self.total_batches = 0
        self.total_items_processed = 0
        self.batch_sizes: List[int] = []

    async def add_to_batch(
        self,
        item: Dict[str, Any],
        callback: asyncio.Future,
    ) -> None:
        """
        Add an item to the batch queue.

        Args:
            item: Item to add to the batch
            callback: Future to complete when the item is processed
        """
        async with self.lock:
            self.total_requests += 1
            self.batch_queue.append(
                {
                    "item": item,
                    "callback": callback,
                    "added_at": time.time(),
                }
            )

            # Start timeout task if not already running
            if self.timeout_task is None:
                self.timeout_task = asyncio.create_task(self._timeout_watcher())

            # Check if we should process the batch now
            if len(self.batch_queue) >= self.max_batch_size:
                asyncio.create_task(self._process_batch())

    async def _timeout_watcher(self) -> None:
        """Watch for batch timeout and trigger processing."""
        while True:
            # Sleep for a bit
            await asyncio.sleep(self.max_wait_time / 2)

            # Check if we should process the batch
            async with self.lock:
                if not self.batch_queue:
                    self.timeout_task = None
                    break

                # Check if the oldest item has been waiting too long
                oldest_timestamp = self.batch_queue[0]["added_at"]
                if time.time() - oldest_timestamp > self.max_wait_time and len(self.batch_queue) >= self.min_batch_size:
                    asyncio.create_task(self._process_batch())

    async def _process_batch(self) -> None:
        """Process the current batch."""
        async with self.lock:
            if self.processing or not self.batch_queue:
                return

            # Mark as processing and take the current batch
            self.processing = True
            current_batch = self.batch_queue
            self.batch_queue = []

            # Reset timeout task
            if self.timeout_task:
                self.timeout_task = None

        # Log batch processing
        batch_size = len(current_batch)
        self.batch_sizes.append(batch_size)
        self.total_batches += 1
        self.total_items_processed += batch_size

        log_event(
            logger,
            "batch_processing",
            "started",
            {
                "batch_size": batch_size,
                "total_batches": self.total_batches,
                "total_requests": self.total_requests,
            },
        )

        try:
            # Extract items
            items = [entry["item"] for entry in current_batch]

            # Process the batch
            results = await self._execute_batch(items)

            # Distribute results
            for entry, result in zip(current_batch, results):
                callback = entry["callback"]
                if not callback.done():
                    callback.set_result(result)

        except Exception as e:
            log_error(logger, "batch_processing", e, {"batch_size": batch_size})

            # Set exception for all callbacks
            for entry in current_batch:
                callback = entry["callback"]
                if not callback.done():
                    callback.set_exception(e)

        finally:
            # Mark as not processing
            async with self.lock:
                self.processing = False

                # Check if we should start a new batch
                if len(self.batch_queue) >= self.max_batch_size:
                    asyncio.create_task(self._process_batch())

    async def _execute_batch(self, items: List[Dict[str, Any]]) -> List[Any]:
        """
        Execute the batch of items.

        This method should be implemented by subclasses.

        Args:
            items: Batch of items to process

        Returns:
            List of results
        """
        raise NotImplementedError("Subclasses must implement _execute_batch")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get batch processing statistics.

        Returns:
            Dictionary with statistics
        """
        avg_batch_size = sum(self.batch_sizes) / len(self.batch_sizes) if self.batch_sizes else 0

        return {
            "total_requests": self.total_requests,
            "total_batches": self.total_batches,
            "total_items_processed": self.total_items_processed,
            "average_batch_size": avg_batch_size,
            "current_queue_size": len(self.batch_queue),
            "batch_size_distribution": self.batch_sizes[-10:] if self.batch_sizes else [],
        }


class EmbeddingBatchProcessor(BatchProcessor):
    """Batch processor for embedding requests."""

    def __init__(
        self,
        project_id: str,
        location: str,
        model_id: str,
        max_batch_size: int = 10,
        max_wait_time: float = 0.05,
    ):
        """
        Initialize the embedding batch processor.

        Args:
            project_id: GCP project ID
            location: GCP location
            model_id: Model ID to use
            max_batch_size: Maximum batch size
            max_wait_time: Maximum wait time in seconds
        """
        super().__init__(
            max_batch_size=max_batch_size,
            max_wait_time=max_wait_time,
            min_batch_size=2,
        )
        self.project_id = project_id
        self.location = location
        self.model_id = model_id
        self._endpoint = None

    async def _get_endpoint(self):
        """Get or create the endpoint."""
        if self._endpoint is None:
            self._endpoint = aiplatform.Endpoint(
                f"projects/{self.project_id}/locations/{self.location}/publishers/google/models/{self.model_id}"
            )
        return self._endpoint

    async def _execute_batch(self, items: List[Dict[str, Any]]) -> List[List[float]]:
        """
        Execute a batch of embedding requests.

        Args:
            items: Batch of items to process

        Returns:
            List of embedding vectors
        """
        # Get all texts
        texts = [item["text"] for item in items]

        # Prepare the instances
        instances = [{"content": text} for text in texts]

        # Get the endpoint
        endpoint = await self._get_endpoint()

        # Make the prediction
        response = await asyncio.to_thread(
            endpoint.predict,
            instances=instances,
        )

        # Extract embeddings from response
        embeddings = []
        for prediction in response.predictions:
            if "embeddings" in prediction:
                embedding = prediction["embeddings"]["values"]
                embeddings.append(embedding)
            else:
                embeddings.append([])

        return embeddings


class OptimizedVertexAIService:
    """
    Optimized Vertex AI implementation with enhanced performance.

    This class provides an optimized implementation of the Vertex AI service
    with request batching, caching, and other performance enhancements.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        enable_batching: bool = True,
        enable_caching: bool = True,
        semantic_cache_threshold: float = 0.85,
    ):
        """
        Initialize the optimized Vertex AI service.

        Args:
            project_id: GCP project ID
            location: GCP location
            enable_batching: Whether to enable request batching
            enable_caching: Whether to enable caching
            semantic_cache_threshold: Threshold for semantic cache hits
        """
        settings = get_settings()
        self.project_id = project_id or settings.gcp.project_id
        self.location = location or settings.gcp.region
        self.enable_batching = enable_batching
        self.enable_caching = enable_caching
        self.semantic_cache_threshold = semantic_cache_threshold

        # Initialize Vertex AI
        aiplatform.init(project=self.project_id, location=self.location)

        # Model mapping
        self.model_mapping = {
            "gemini-pro": "gemini-pro",
            "gemini-pro-vision": "gemini-pro-vision",
            "text-embedding": "textembedding-gecko@latest",
            "text-bison": "text-bison@latest",
        }

        # Batch processors for different operations
        self.embedding_batch_processors: Dict[str, EmbeddingBatchProcessor] = {}

        # Caches for different operations
        self.response_cache = get_tiered_cache()
        self.semantic_cache = SemanticCache(
            prefix="semantic:vertex:",
            similarity_threshold=semantic_cache_threshold,
        )

        # Generative model instances - lazily initialized
        self._generative_models: Dict[str, GenerativeModel] = {}

        log_event(
            logger,
            "vertex_ai_service",
            "initialized",
            {
                "project_id": self.project_id,
                "location": self.location,
                "enable_batching": enable_batching,
                "enable_caching": enable_caching,
            },
        )

    def _get_embedding_batch_processor(self, model_id: str) -> EmbeddingBatchProcessor:
        """
        Get or create an embedding batch processor for a model.

        Args:
            model_id: The model identifier

        Returns:
            An embedding batch processor
        """
        vertex_model_id = self.model_mapping.get(model_id, model_id)

        if vertex_model_id not in self.embedding_batch_processors:
            self.embedding_batch_processors[vertex_model_id] = EmbeddingBatchProcessor(
                project_id=self.project_id,
                location=self.location,
                model_id=vertex_model_id,
                max_batch_size=10,  # Adjust based on testing
                max_wait_time=0.05,  # 50ms max latency impact
            )

        return self.embedding_batch_processors[vertex_model_id]

    def _get_generative_model(self, model_id: str) -> GenerativeModel:
        """
        Get or create a generative model instance.

        Args:
            model_id: The model identifier

        Returns:
            A generative model instance
        """
        if model_id not in self._generative_models:
            self._generative_models[model_id] = GenerativeModel(model_id)

        return self._generative_models[model_id]

    async def get_batch_stats(self) -> Dict[str, Any]:
        """
        Get batch processing statistics.

        Returns:
            Dictionary with statistics
        """
        stats = {}

        for model_id, processor in self.embedding_batch_processors.items():
            stats[f"embedding_batch_{model_id}"] = processor.get_stats()

        return stats

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with statistics
        """
        stats = {
            "response_cache": await self.response_cache.get_stats(),
        }

        return stats

    @cached(ttl_seconds=300, namespace="vertex:text")
    async def generate_text(
        self,
        prompt: str,
        model_id: str = "gemini-pro",
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

        Raises:
            ModelNotFoundError: If the model is not found
            ModelUnavailableError: If the model is unavailable
            InvalidInputError: If the input is invalid
            AIServiceError: For other errors
        """
        start_time = log_start(
            logger,
            "generate_text",
            {
                "model_id": model_id,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )

        # Try semantic cache if caching is enabled
        if self.enable_caching:
            semantic_query = f"{prompt}|{model_id}|{temperature}|{top_p}|{max_tokens}"
            cached_result = await self.semantic_cache.get(semantic_query)

            if cached_result:
                log_end(
                    logger,
                    "generate_text",
                    start_time,
                    {
                        "model_id": model_id,
                        "cache": "semantic_hit",
                    },
                )
                return cached_result.get("text", "")

        try:
            # Map model ID to Vertex AI model
            vertex_model_id = self.model_mapping.get(model_id)
            if not vertex_model_id:
                raise ModelNotFoundError(model_id)

            # For Gemini models
            if vertex_model_id.startswith("gemini-"):
                result = await self._generate_text_gemini(
                    prompt=prompt,
                    model_id=vertex_model_id,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    stop_sequences=stop_sequences,
                )
            # For other models
            else:
                result = await self._generate_text_vertex(
                    prompt=prompt,
                    model_id=vertex_model_id,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    stop_sequences=stop_sequences,
                )

            # Store in semantic cache if caching is enabled
            if self.enable_caching:
                await self.semantic_cache.set(semantic_query, {"text": result, "model_id": model_id})

            log_end(
                logger,
                "generate_text",
                start_time,
                {
                    "model_id": model_id,
                    "output_length": len(result),
                    "cache": "miss",
                },
            )

            return result

        except ModelNotFoundError:
            # Re-raise model not found errors
            raise
        except ModelUnavailableError:
            # Re-raise model unavailable errors
            raise
        except InvalidInputError:
            # Re-raise invalid input errors
            raise
        except Exception as e:
            log_error(logger, "generate_text", e, {"model_id": model_id})
            raise AIServiceError(
                code="TEXT_GENERATION_ERROR",
                message=f"Failed to generate text with model '{model_id}'",
                cause=e,
            )

    async def _generate_text_gemini(
        self,
        prompt: str,
        model_id: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 1.0,
        stop_sequences: Optional[List[str]] = None,
    ) -> str:
        """
        Generate text using Gemini models.

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
        try:
            # Create generation config
            generation_config = GenerationConfig(
                temperature=temperature,
                top_p=top_p,
                max_output_tokens=max_tokens,
                stop_sequences=stop_sequences,
            )

            # Get or initialize the model
            model = self._get_generative_model(model_id)

            # Generate content
            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config=generation_config,
            )

            # Extract text from response
            return response.text

        except Exception as e:
            log_error(logger, "generate_text_gemini", e, {"model_id": model_id})
            raise

    async def _generate_text_vertex(
        self,
        prompt: str,
        model_id: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 1.0,
        stop_sequences: Optional[List[str]] = None,
    ) -> str:
        """
        Generate text using other Vertex AI models.

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
        try:
            # Get the model endpoint
            endpoint = aiplatform.Endpoint(
                f"projects/{self.project_id}/locations/{self.location}/publishers/google/models/{model_id}"
            )

            # Prepare the request
            instances = [{"prompt": prompt}]
            parameters = {
                "temperature": temperature,
                "maxOutputTokens": max_tokens or 1024,
                "topP": top_p,
            }

            if stop_sequences:
                parameters["stopSequences"] = stop_sequences

            # Make the prediction
            response = await asyncio.to_thread(
                endpoint.predict,
                instances=instances,
                parameters=parameters,
            )

            # Extract text from response
            predictions = response.predictions
            if not predictions:
                return ""

            return predictions[0].get("content", "")

        except Exception as e:
            log_error(logger, "generate_text_vertex", e, {"model_id": model_id})
            raise

    async def generate_embeddings(
        self,
        texts: List[str],
        model_id: str = "text-embedding",
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of input texts
            model_id: The model identifier

        Returns:
            List of embedding vectors

        Raises:
            ModelNotFoundError: If the model is not found
            ModelUnavailableError: If the model is unavailable
            InvalidInputError: If the input is invalid
            AIServiceError: For other errors
        """
        if not texts:
            return []

        start_time = log_start(
            logger,
            "generate_embeddings",
            {
                "model_id": model_id,
                "text_count": len(texts),
            },
        )

        try:
            # Map model ID to Vertex AI model
            vertex_model_id = self.model_mapping.get(model_id)
            if not vertex_model_id:
                raise ModelNotFoundError(model_id)

            # Process requests in parallel for better performance
            results = await asyncio.gather(*[self._generate_single_embedding(text, vertex_model_id) for text in texts])

            log_end(
                logger,
                "generate_embeddings",
                start_time,
                {
                    "model_id": model_id,
                    "embedding_count": len(results),
                },
            )

            return results

        except ModelNotFoundError:
            # Re-raise model not found errors
            raise
        except Exception as e:
            log_error(logger, "generate_embeddings", e, {"model_id": model_id})
            raise AIServiceError(
                code="EMBEDDING_GENERATION_ERROR",
                message=f"Failed to generate embeddings with model '{model_id}'",
                cause=e,
            )

    async def _generate_single_embedding(
        self,
        text: str,
        model_id: str,
    ) -> List[float]:
        """
        Generate embedding for a single text.

        This method uses batching if enabled, or direct API calls otherwise.

        Args:
            text: Input text
            model_id: The model identifier

        Returns:
            Embedding vector
        """
        # Try cache first if enabled
        if self.enable_caching:
            cache_key = f"embedding:{model_id}:{hashlib.md5(text.encode()).hexdigest()}"
            cached_result = await self.response_cache.get(cache_key)

            if cached_result:
                return cached_result

        # Use batching if enabled
        if self.enable_batching:
            # Get the batch processor
            processor = self._get_embedding_batch_processor(model_id)

            # Create a future for the result
            future = asyncio.Future()

            # Add to batch
            await processor.add_to_batch(
                {"text": text, "model_id": model_id},
                future,
            )

            # Wait for result
            embedding = await future

        else:
            # Get the endpoint
            endpoint = aiplatform.Endpoint(
                f"projects/{self.project_id}/locations/{self.location}/publishers/google/models/{model_id}"
            )

            # Prepare the request
            instances = [{"content": text}]

            # Make the prediction
            response = await asyncio.to_thread(
                endpoint.predict,
                instances=instances,
            )

            # Extract embedding from response
            if not response.predictions:
                embedding = []
            elif "embeddings" in response.predictions[0]:
                embedding = response.predictions[0]["embeddings"]["values"]
            else:
                embedding = []

        # Store in cache if enabled
        if self.enable_caching and embedding:
            await self.response_cache.set(
                cache_key,
                embedding,
                l1_ttl_seconds=300,  # 5 minutes in L1
                l2_ttl_seconds=3600,  # 1 hour in L2
            )

        return embedding

    async def get_embedding(
        self,
        text: str,
        model_id: str = "text-embedding",
    ) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text
            model_id: The model identifier

        Returns:
            Embedding vector

        Raises:
            ModelNotFoundError: If the model is not found
            ModelUnavailableError: If the model is unavailable
            InvalidInputError: If the input is invalid
            AIServiceError: For other errors
        """
        embeddings = await self.generate_embeddings(
            texts=[text],
            model_id=model_id,
        )

        # Return the first embedding or empty list as fallback
        if embeddings and len(embeddings) > 0:
            return embeddings[0]
        else:
            return []

    @cached(ttl_seconds=300, namespace="vertex:classify")
    async def classify_text(
        self,
        text: str,
        categories: List[str],
        model_id: str = "gemini-pro",
    ) -> Dict[str, float]:
        """
        Classify text into categories.

        Args:
            text: The input text
            categories: List of possible categories
            model_id: The model identifier

        Returns:
            Dictionary mapping categories to confidence scores

        Raises:
            ModelNotFoundError: If the model is not found
            ModelUnavailableError: If the model is unavailable
            InvalidInputError: If the input is invalid
            AIServiceError: For other errors
        """
        start_time = log_start(
            logger,
            "classify_text",
            {
                "model_id": model_id,
                "category_count": len(categories),
            },
        )

        try:
            # For classification, we'll use a prompt-based approach with Gemini
            categories_str = ", ".join(categories)
            prompt = f"""
            Classify the following text into one of these categories: {categories_str}
            
            Text: {text}
            
            Respond with a JSON object where the keys are the categories and the values are confidence scores between 0 and 1.
            The confidence scores should sum to 1.
            """

            # Generate text
            response_text = await self.generate_text(
                prompt=prompt,
                model_id=model_id,
                temperature=0.1,  # Low temperature for more deterministic results
            )

            # Parse the JSON response
            try:
                # Extract JSON from the response
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1

                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    classification = json.loads(json_str)
                else:
                    # Fallback: create a uniform distribution
                    classification = {category: 1.0 / len(categories) for category in categories}

                # Ensure all categories are present
                for category in categories:
                    if category not in classification:
                        classification[category] = 0.0

                # Normalize scores to sum to 1
                total = sum(classification.values())
                if total > 0:
                    classification = {k: v / total for k, v in classification.items()}

                log_end(
                    logger,
                    "classify_text",
                    start_time,
                    {
                        "model_id": model_id,
                        "categories": list(classification.keys()),
                    },
                )

                return classification

            except json.JSONDecodeError:
                # Fallback: create a uniform distribution
                classification = {category: 1.0 / len(categories) for category in categories}

                log_end(
                    logger,
                    "classify_text",
                    start_time,
                    {
                        "model_id": model_id,
                        "categories": list(classification.keys()),
                        "fallback": True,
                    },
                )

                return classification

        except Exception as e:
            log_error(logger, "classify_text", e, {"model_id": model_id})
            raise AIServiceError(
                code="TEXT_CLASSIFICATION_ERROR",
                message=f"Failed to classify text with model '{model_id}'",
                cause=e,
            )

    @cached(ttl_seconds=300, namespace="vertex:qa")
    async def answer_question(
        self,
        question: str,
        context: str,
        model_id: str = "gemini-pro",
    ) -> str:
        """
        Answer a question based on context.

        Args:
            question: The question to answer
            context: The context to use for answering
            model_id: The model identifier

        Returns:
            The answer to the question

        Raises:
            ModelNotFoundError: If the model is not found
            ModelUnavailableError: If the model is unavailable
            InvalidInputError: If the input is invalid
            AIServiceError: For other errors
        """
        start_time = log_start(
            logger,
            "answer_question",
            {
                "model_id": model_id,
                "question_length": len(question),
                "context_length": len(context),
            },
        )

        try:
            # Create a prompt for question answering
            prompt = f"""
            Context: {context}
            
            Question: {question}
            
            Answer the question based only on the provided context. If the answer cannot be determined from the context, say "I don't know."
            """

            # Generate text
            answer = await self.generate_text(
                prompt=prompt,
                model_id=model_id,
                temperature=0.2,  # Low temperature for more deterministic results
            )

            log_end(
                logger,
                "answer_question",
                start_time,
                {
                    "model_id": model_id,
                    "answer_length": len(answer),
                },
            )

            return answer

        except Exception as e:
            log_error(logger, "answer_question", e, {"model_id": model_id})
            raise AIServiceError(
                code="QUESTION_ANSWERING_ERROR",
                message=f"Failed to answer question with model '{model_id}'",
                cause=e,
            )

    @cached(ttl_seconds=300, namespace="vertex:summarize")
    async def summarize_text(
        self,
        text: str,
        max_length: Optional[int] = None,
        model_id: str = "gemini-pro",
    ) -> str:
        """
        Summarize text.

        Args:
            text: The text to summarize
            max_length: Maximum length of the summary
            model_id: The model identifier

        Returns:
            The summary

        Raises:
            ModelNotFoundError: If the model is not found
            ModelUnavailableError: If the model is unavailable
            InvalidInputError: If the input is invalid
            AIServiceError: For other errors
        """
        start_time = log_start(
            logger,
            "summarize_text",
            {
                "model_id": model_id,
                "text_length": len(text),
                "max_length": max_length,
            },
        )

        try:
            # Create a prompt for summarization
            prompt = f"""
            Summarize the following text:
            
            {text}
            """

            if max_length:
                prompt += f"\n\nKeep the summary under {max_length} characters."

            # Generate text
            summary = await self.generate_text(
                prompt=prompt,
                model_id=model_id,
                temperature=0.3,  # Moderate temperature for balance
                max_tokens=max_length // 4 if max_length else None,  # Approximate token limit
            )

            log_end(
                logger,
                "summarize_text",
                start_time,
                {
                    "model_id": model_id,
                    "summary_length": len(summary),
                },
            )

            return summary

        except Exception as e:
            log_error(logger, "summarize_text", e, {"model_id": model_id})
            raise AIServiceError(
                code="SUMMARIZATION_ERROR",
                message=f"Failed to summarize text with model '{model_id}'",
                cause=e,
            )

    async def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get available models.

        Returns:
            List of available models with capabilities
        """
        try:
            models = [
                {
                    "id": "gemini-pro",
                    "display_name": "Gemini Pro",
                    "capabilities": self._get_model_capabilities("gemini-pro"),
                    "provider": "Google Vertex AI",
                },
                {
                    "id": "gemini-pro-vision",
                    "display_name": "Gemini Pro Vision",
                    "capabilities": self._get_model_capabilities("gemini-pro-vision"),
                    "provider": "Google Vertex AI",
                },
                {
                    "id": "text-embedding",
                    "display_name": "Text Embedding",
                    "capabilities": self._get_model_capabilities("text-embedding"),
                    "provider": "Google Vertex AI",
                },
                {
                    "id": "text-bison",
                    "display_name": "Text Bison",
                    "capabilities": self._get_model_capabilities("text-bison"),
                    "provider": "Google Vertex AI",
                },
            ]

            return models

        except Exception as e:
            log_error(logger, "get_available_models", e, {})
            return []

    def _get_model_capabilities(self, model_id: str) -> List[str]:
        """
        Get model capabilities.

        Args:
            model_id: The model identifier

        Returns:
            List of capabilities
        """
        if model_id == "gemini-pro":
            return [
                "text-generation",
                "classification",
                "question-answering",
                "summarization",
            ]
        elif model_id == "gemini-pro-vision":
            return ["multimodal-generation"]
        elif model_id == "text-embedding":
            return ["embeddings"]
        elif model_id == "text-bison":
            return ["text-generation", "classification", "summarization"]
        else:
            return []
