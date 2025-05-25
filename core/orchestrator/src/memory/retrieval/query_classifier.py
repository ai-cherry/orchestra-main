"""
Query Classifier for AI Orchestra.

This module provides a query classifier that categorizes queries into different types
(factual, conceptual, conversational) to optimize retrieval strategies.
"""

import logging
import time
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)


class QueryType(str, Enum):
    """Types of queries for memory retrieval optimization."""

    FACTUAL = "factual"  # Prioritize exact matches
    CONCEPTUAL = "conceptual"  # Prioritize semantic matches
    CONVERSATIONAL = "conversational"  # Balance between exact and semantic
    UNKNOWN = "unknown"  # Default type


class QueryFeatures(BaseModel):
    """
    Features extracted from a query for classification.

    This class encapsulates various features that can be used to classify
    a query into different types.
    """

    # Query metadata
    query_length: int
    contains_question_mark: bool

    # Linguistic features
    factual_indicators: int = 0
    conceptual_indicators: int = 0
    conversational_indicators: int = 0

    # Word counts
    question_words: int = 0
    action_verbs: int = 0
    greeting_terms: int = 0

    # Additional features
    has_personal_pronouns: bool = False
    has_technical_terms: bool = False


class QueryClassificationResult(BaseModel):
    """
    Result of query classification.

    This class encapsulates the result of classifying a query,
    including the determined type and confidence scores.
    """

    query: str
    query_type: QueryType
    confidence: float
    scores: Dict[str, float]
    features: Optional[QueryFeatures] = None
    processing_time_ms: float = 0.0


class QueryClassifier:
    """
    Query classifier for AI Orchestra.

    This class provides functionality to classify queries into different types
    to optimize retrieval strategies.
    """

    def __init__(
        self,
        use_vertex_ai: bool = False,
        vertex_ai_config: Optional[Dict[str, Any]] = None,
        confidence_threshold: float = 0.6,
    ):
        """
        Initialize query classifier.

        Args:
            use_vertex_ai: Whether to use Vertex AI for classification
            vertex_ai_config: Configuration for Vertex AI
            confidence_threshold: Minimum confidence threshold for classification
        """
        self.use_vertex_ai = use_vertex_ai
        self.vertex_ai_config = vertex_ai_config or {}
        self.confidence_threshold = confidence_threshold
        self.vertex_ai_client = None

        # Initialize Vertex AI client if enabled
        if self.use_vertex_ai:
            self._init_vertex_ai()

        # Define indicator terms for rule-based classification
        self.factual_indicators = [
            "what is",
            "who is",
            "when did",
            "where is",
            "how many",
            "define",
            "explain",
            "list",
            "tell me about",
            "find",
            "show me",
            "give me",
            "name",
            "identify",
            "locate",
        ]

        self.conceptual_indicators = [
            "why",
            "how does",
            "what if",
            "compare",
            "contrast",
            "analyze",
            "evaluate",
            "similar to",
            "difference between",
            "relationship",
            "concept",
            "theory",
            "principle",
            "explain why",
            "reason for",
            "cause of",
            "effect of",
            "impact of",
            "significance of",
        ]

        self.conversational_indicators = [
            "can you",
            "could you",
            "would you",
            "i want",
            "i need",
            "help me",
            "please",
            "thanks",
            "thank you",
            "hi",
            "hello",
            "good morning",
            "good afternoon",
            "how are you",
            "nice to meet you",
        ]

        logger.info(f"QueryClassifier initialized (Vertex AI: {use_vertex_ai})")

    def _init_vertex_ai(self) -> None:
        """
        Initialize Vertex AI client for query classification.

        This method sets up the Vertex AI client for text classification.
        """
        try:
            from google.cloud import aiplatform

            # Extract configuration
            project = self.vertex_ai_config.get("project", "cherry-ai-project")
            location = self.vertex_ai_config.get("location", "us-central1")

            # Initialize Vertex AI
            aiplatform.init(project=project, location=location)

            # Set up endpoint for text classification
            endpoint_name = self.vertex_ai_config.get("endpoint_name")
            if endpoint_name:
                self.vertex_ai_client = aiplatform.Endpoint(endpoint_name)
                logger.info(f"Vertex AI endpoint initialized: {endpoint_name}")
            else:
                # Use foundation model for classification
                self.vertex_ai_client = aiplatform.TextEmbeddingModel.from_pretrained(
                    "textembedding-gecko@latest"
                )
                logger.info(
                    "Vertex AI foundation model initialized for query classification"
                )

        except ImportError:
            logger.warning(
                "google-cloud-aiplatform package not installed. Falling back to rule-based classification."
            )
            self.use_vertex_ai = False
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            self.use_vertex_ai = False

    async def classify(self, query: str) -> QueryClassificationResult:
        """
        Classify a query into a specific type.

        Args:
            query: The query to classify

        Returns:
            Classification result with query type and confidence
        """
        start_time = time.time()

        if not query:
            # Empty query, return unknown
            return QueryClassificationResult(
                query=query,
                query_type=QueryType.UNKNOWN,
                confidence=1.0,
                scores={t.value: 0.0 for t in QueryType},
                processing_time_ms=0.0,
            )

        # Use Vertex AI if enabled and available
        if self.use_vertex_ai and self.vertex_ai_client:
            try:
                result = await self._classify_with_vertex_ai(query)
                result.processing_time_ms = (time.time() - start_time) * 1000
                return result
            except Exception as e:
                logger.error(f"Vertex AI classification failed: {e}")
                # Fall back to rule-based classification

        # Use rule-based classification
        result = self._classify_with_rules(query)
        result.processing_time_ms = (time.time() - start_time) * 1000
        return result

    async def _classify_with_vertex_ai(self, query: str) -> QueryClassificationResult:
        """
        Classify a query using Vertex AI.

        Args:
            query: The query to classify

        Returns:
            Classification result with query type and confidence
        """
        try:
            # Extract features for additional context
            features = self._extract_features(query)

            # Prepare prompt for classification
            prompt = f"""
            Classify the following query into one of these types:
            - FACTUAL: Seeking specific information or facts (e.g., "What is X?", "Who invented Y?")
            - CONCEPTUAL: Seeking understanding of concepts, theories, or relationships (e.g., "Why does X happen?", "How does Y work?")
            - CONVERSATIONAL: General conversation, greetings, or requests (e.g., "Can you help me?", "Hello")

            Query: "{query}"

            Classification:
            """

            # Call Vertex AI endpoint
            if hasattr(self.vertex_ai_client, "predict"):
                # Using custom endpoint
                response = await self.vertex_ai_client.predict_async(
                    instances=[{"prompt": prompt}]
                )

                # Parse response based on expected format
                # Note: This would need to be adjusted based on the actual model output format
                prediction = response[0]
                scores = {
                    QueryType.FACTUAL.value: prediction.get("scores", {}).get(
                        "FACTUAL", 0.0
                    ),
                    QueryType.CONCEPTUAL.value: prediction.get("scores", {}).get(
                        "CONCEPTUAL", 0.0
                    ),
                    QueryType.CONVERSATIONAL.value: prediction.get("scores", {}).get(
                        "CONVERSATIONAL", 0.0
                    ),
                    QueryType.UNKNOWN.value: 0.0,
                }

                # Determine the type with highest score
                query_type = max(scores.items(), key=lambda x: x[1])[0]
                confidence = scores[query_type]

            else:
                # Using foundation model for text classification
                # This is a simplified approach using embeddings similarity
                # In a real implementation, you would use a proper classification model

                # For now, fall back to rule-based classification
                return self._classify_with_rules(query)

            return QueryClassificationResult(
                query=query,
                query_type=QueryType(query_type),
                confidence=confidence,
                scores=scores,
                features=features,
            )

        except Exception as e:
            logger.error(f"Error in Vertex AI classification: {e}")
            # Fall back to rule-based classification
            return self._classify_with_rules(query)

    def _classify_with_rules(self, query: str) -> QueryClassificationResult:
        """
        Classify a query using rule-based approach.

        Args:
            query: The query to classify

        Returns:
            Classification result with query type and confidence
        """
        # Extract features
        features = self._extract_features(query)

        # Calculate scores for each type
        scores = {
            QueryType.FACTUAL.value: features.factual_indicators * 0.2
            + features.question_words * 0.1,
            QueryType.CONCEPTUAL.value: features.conceptual_indicators * 0.2
            + (features.has_technical_terms * 0.2),
            QueryType.CONVERSATIONAL.value: features.conversational_indicators * 0.2
            + features.greeting_terms * 0.2
            + (features.has_personal_pronouns * 0.1),
            QueryType.UNKNOWN.value: 0.1,
        }

        # Normalize scores
        total = sum(scores.values())
        if total > 0:
            for key in scores:
                scores[key] /= total

        # Determine the type with highest score
        query_type = max(scores.items(), key=lambda x: x[1])[0]
        confidence = scores[query_type]

        # If confidence is below threshold, use UNKNOWN
        if confidence < self.confidence_threshold:
            query_type = QueryType.UNKNOWN.value
            confidence = scores[QueryType.UNKNOWN.value]

        return QueryClassificationResult(
            query=query,
            query_type=QueryType(query_type),
            confidence=confidence,
            scores=scores,
            features=features,
        )

    def _extract_features(self, query: str) -> QueryFeatures:
        """
        Extract features from a query for classification.

        Args:
            query: The query to extract features from

        Returns:
            Extracted features
        """
        query_lower = query.lower()

        # Basic features
        features = QueryFeatures(
            query_length=len(query), contains_question_mark="?" in query
        )

        # Count indicator terms
        features.factual_indicators = sum(
            1 for indicator in self.factual_indicators if indicator in query_lower
        )
        features.conceptual_indicators = sum(
            1 for indicator in self.conceptual_indicators if indicator in query_lower
        )
        features.conversational_indicators = sum(
            1
            for indicator in self.conversational_indicators
            if indicator in query_lower
        )

        # Count question words
        question_words = ["what", "who", "when", "where", "why", "how"]
        features.question_words = sum(
            1 for word in question_words if word in query_lower.split()
        )

        # Count greeting terms
        greeting_terms = [
            "hi",
            "hello",
            "hey",
            "good morning",
            "good afternoon",
            "good evening",
        ]
        features.greeting_terms = sum(
            1 for term in greeting_terms if term in query_lower
        )

        # Check for personal pronouns
        personal_pronouns = [
            "i",
            "me",
            "my",
            "mine",
            "you",
            "your",
            "yours",
            "we",
            "us",
            "our",
        ]
        features.has_personal_pronouns = any(
            pronoun in query_lower.split() for pronoun in personal_pronouns
        )

        # Simple check for technical terms (could be enhanced with a domain-specific vocabulary)
        technical_indicators = [
            "algorithm",
            "system",
            "database",
            "function",
            "api",
            "interface",
            "protocol",
            "architecture",
        ]
        features.has_technical_terms = any(
            term in query_lower for term in technical_indicators
        )

        return features
