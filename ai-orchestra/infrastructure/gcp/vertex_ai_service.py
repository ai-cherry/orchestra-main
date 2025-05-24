"""
Vertex AI implementation of the AI service interface.

This module provides a Vertex AI-based implementation of the AI service.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional

from ai_orchestra.core.config import settings
from ai_orchestra.core.errors import (
    AIServiceError,
    InvalidInputError,
    ModelNotFoundError,
    ModelUnavailableError,
)
from ai_orchestra.utils.logging import log_end, log_error, log_event, log_start
from google.cloud import aiplatform
from vertexai.preview.generative_models import GenerationConfig, GenerativeModel

logger = logging.getLogger("ai_orchestra.infrastructure.gcp.vertex_ai_service")


class VertexAIService:
    """Vertex AI implementation of the AI service interface."""

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
    ):
        """
        Initialize the Vertex AI service.

        Args:
            project_id: GCP project ID
            location: GCP location
        """
        self.project_id = project_id or settings.gcp.project_id
        self.location = location or settings.gcp.region

        # Initialize Vertex AI
        aiplatform.init(project=self.project_id, location=self.location)

        # Model mapping
        self.model_mapping = {
            "gemini-pro": "gemini-pro",
            "gemini-pro-vision": "gemini-pro-vision",
            "text-embedding": "textembedding-gecko@latest",
            "text-bison": "text-bison@latest",
        }

        log_event(
            logger,
            "vertex_ai_service",
            "initialized",
            {
                "project_id": self.project_id,
                "location": self.location,
            },
        )

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
        log_start(
            logger,
            "generate_text",
            {
                "model_id": model_id,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )

        try:
            # Map model ID to Vertex AI model
            vertex_model_id = self.model_mapping.get(model_id)
            if not vertex_model_id:
                raise ModelNotFoundError(model_id)

            # For Gemini models
            if vertex_model_id.startswith("gemini-"):
                return await self._generate_text_gemini(
                    prompt=prompt,
                    model_id=vertex_model_id,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    stop_sequences=stop_sequences,
                )

            # For other models
            return await self._generate_text_vertex(
                prompt=prompt,
                model_id=vertex_model_id,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop_sequences=stop_sequences,
            )

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
        start_time = log_start(
            logger,
            "generate_text",
            {
                "model_id": model_id,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        try:
            # Create generation config
            generation_config = GenerationConfig(
                temperature=temperature,
                top_p=top_p,
                max_output_tokens=max_tokens,
                stop_sequences=stop_sequences,
            )

            # Initialize the model
            model = GenerativeModel(model_id)

            # Generate content
            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config=generation_config,
            )

            # Extract text from response
            generated_text = response.text

            log_end(
                logger,
                "generate_text",
                start_time,
                {
                    "model_id": model_id,
                    "output_length": len(generated_text),
                },
            )

            return generated_text

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
        start_time = log_start(
            logger,
            "generate_text",
            {
                "model_id": model_id,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )
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

            generated_text = predictions[0].get("content", "")

            log_end(
                logger,
                "generate_text",
                start_time,
                {
                    "model_id": model_id,
                    "output_length": len(generated_text),
                },
            )

            return generated_text

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

            # Get the model endpoint
            endpoint = aiplatform.Endpoint(
                f"projects/{self.project_id}/locations/{self.location}/publishers/google/models/{vertex_model_id}"
            )

            # Prepare the request
            instances = [{"content": text} for text in texts]

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

            log_end(
                logger,
                "generate_embeddings",
                start_time,
                {
                    "model_id": model_id,
                    "embedding_count": len(embeddings),
                },
            )

            return embeddings

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
        time.time()
        embeddings = await self.generate_embeddings(
            texts=[text],
            model_id=model_id,
        )

        # Return the first embedding or empty list as fallback
        if embeddings and len(embeddings) > 0:
            return embeddings[0]
        else:
            return []

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
                temperature=0.3,  # Lower temperature for more factual responses
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
            The summarized text

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
                temperature=0.3,  # Lower temperature for more factual responses
                max_tokens=max_length // 4 if max_length else None,  # Rough estimate of tokens from characters
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
                code="TEXT_SUMMARIZATION_ERROR",
                message=f"Failed to summarize text with model '{model_id}'",
                cause=e,
            )

    async def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get a list of available models.

        Returns:
            List of model information dictionaries

        Raises:
            AIServiceError: If there was an error getting available models
        """
        start_time = log_start(logger, "get_available_models", {})

        try:
            # Return information about available models
            models = [
                {
                    "id": model_id,
                    "name": model_id,
                    "provider": "vertex_ai",
                    "capabilities": self._get_model_capabilities(model_id),
                }
                for model_id in self.model_mapping.keys()
            ]

            log_end(
                logger,
                "get_available_models",
                start_time,
                {
                    "model_count": len(models),
                },
            )

            return models

        except Exception as e:
            log_error(logger, "get_available_models", e, {})
            raise AIServiceError(
                code="MODEL_LIST_ERROR",
                message="Failed to get available models",
                cause=e,
            )

    def _get_model_capabilities(self, model_id: str) -> List[str]:
        """
        Get the capabilities of a model.

        Args:
            model_id: The model identifier

        Returns:
            List of capability strings
        """
        # Define capabilities for each model
        capabilities_map = {
            "gemini-pro": [
                "text_generation",
                "classification",
                "question_answering",
                "summarization",
            ],
            "gemini-pro-vision": ["text_generation", "image_understanding"],
            "text-embedding": ["embeddings"],
            "text-bison": [
                "text_generation",
                "classification",
                "question_answering",
                "summarization",
            ],
        }

        return capabilities_map.get(model_id, [])

    async def batch_get_embeddings(
        self, texts: List[str], model_id: str = "text-embedding-preview-0409"
    ) -> List[List[float]]:
        """Get embeddings for a list of texts in batches."""
        start_time = time.time()
        embeddings = await self.generate_embeddings(texts, model_id)
        log_end(logger, "batch_get_embeddings", start_time, {"embedding_count": len(embeddings)})
        return embeddings
