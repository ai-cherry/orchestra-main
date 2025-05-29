"""
Importance Scorer for AI Orchestra Memory System.

This module provides functionality to evaluate the importance of memory items
for intelligent promotion, demotion, and retention decisions.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)


class ImportanceFactors(BaseModel):
    """
    Factors that contribute to a memory item's importance score.

    This class encapsulates the various factors that are used to calculate
    the importance of a memory item for retention and promotion decisions.
    """

    # Recency factors
    created_at: datetime
    last_accessed_at: Optional[datetime] = None

    # Usage factors
    access_count: int = 0
    reference_count: int = 0

    # Content factors
    content_length: int = 0
    has_entities: bool = False
    entity_count: int = 0

    # Metadata factors
    is_user_marked_important: bool = False
    explicit_importance: Optional[float] = None

    # Relationship factors
    connected_item_count: int = 0

    # Semantic factors
    semantic_richness: float = 0.0  # Higher values indicate more information density


class ImportanceScore(BaseModel):
    """
    Result of importance scoring for a memory item.

    This class encapsulates the importance score and its components
    for a memory item.
    """

    # Item identifier
    item_id: str

    # Overall score (0.0 to 1.0)
    score: float

    # Component scores
    recency_score: float
    usage_score: float
    content_score: float
    metadata_score: float
    relationship_score: float
    semantic_score: float

    # Factors used for scoring
    factors: ImportanceFactors

    # Timestamp
    scored_at: datetime = Field(default_factory=datetime.utcnow)


class ImportanceScoringConfig(BaseModel):
    """
    Configuration for importance scoring.

    This class encapsulates the configuration parameters for the
    importance scoring algorithm.
    """

    # Component weights (must sum to 1.0)
    recency_weight: float = 0.3
    usage_weight: float = 0.2
    content_weight: float = 0.15
    metadata_weight: float = 0.15
    relationship_weight: float = 0.1
    semantic_weight: float = 0.1

    # Recency decay parameters
    recency_half_life_days: float = 7.0  # Half-life in days

    # Usage thresholds
    high_access_threshold: int = 10
    high_reference_threshold: int = 5

    # Content thresholds
    min_content_length: int = 10
    significant_content_length: int = 100

    # Relationship thresholds
    significant_connection_count: int = 3


class ImportanceScorer:
    """
    Evaluates the importance of memory items.

    This class provides functionality to score memory items based on various
    factors to determine their importance for retention and promotion decisions.
    """

    def __init__(self, config: Optional[ImportanceScoringConfig] = None):
        """
        Initialize importance scorer.

        Args:
            config: Optional configuration for importance scoring
        """
        self.config = config or ImportanceScoringConfig()

        # Validate weights sum to 1.0
        weights_sum = (
            self.config.recency_weight
            + self.config.usage_weight
            + self.config.content_weight
            + self.config.metadata_weight
            + self.config.relationship_weight
            + self.config.semantic_weight
        )

        if abs(weights_sum - 1.0) > 0.001:
            logger.warning(
                f"Importance scoring weights sum to {weights_sum}, not 1.0. " "Scores may not be properly normalized."
            )

        logger.info("ImportanceScorer initialized")

    def score_item(self, item: Dict[str, Any], factors: Optional[ImportanceFactors] = None) -> ImportanceScore:
        """
        Score a memory item based on its importance factors.

        Args:
            item: The memory item to score
            factors: Optional pre-extracted importance factors

        Returns:
            Importance score for the item
        """
        # Extract item ID
        item_id = item.get("id", item.get("memory_key", str(id(item))))

        # Extract or use provided factors
        if factors is None:
            factors = self._extract_factors(item)

        # Calculate component scores
        recency_score = self._calculate_recency_score(factors)
        usage_score = self._calculate_usage_score(factors)
        content_score = self._calculate_content_score(factors)
        metadata_score = self._calculate_metadata_score(factors)
        relationship_score = self._calculate_relationship_score(factors)
        semantic_score = self._calculate_semantic_score(factors)

        # Calculate overall score (weighted sum)
        overall_score = (
            recency_score * self.config.recency_weight
            + usage_score * self.config.usage_weight
            + content_score * self.config.content_weight
            + metadata_score * self.config.metadata_weight
            + relationship_score * self.config.relationship_weight
            + semantic_score * self.config.semantic_weight
        )

        # Ensure score is in [0, 1] range
        overall_score = max(0.0, min(1.0, overall_score))

        # Create and return score object
        return ImportanceScore(
            item_id=item_id,
            score=overall_score,
            recency_score=recency_score,
            usage_score=usage_score,
            content_score=content_score,
            metadata_score=metadata_score,
            relationship_score=relationship_score,
            semantic_score=semantic_score,
            factors=factors,
        )

    def _extract_factors(self, item: Dict[str, Any]) -> ImportanceFactors:
        """
        Extract importance factors from a memory item.

        Args:
            item: The memory item to extract factors from

        Returns:
            Extracted importance factors
        """
        # Extract creation time
        created_at = item.get("created_at")
        if isinstance(created_at, (int, float)):
            created_at = datetime.fromtimestamp(created_at)
        elif not isinstance(created_at, datetime):
            created_at = datetime.utcnow()

        # Extract last accessed time
        last_accessed_at = item.get("last_accessed_at")
        if isinstance(last_accessed_at, (int, float)):
            last_accessed_at = datetime.fromtimestamp(last_accessed_at)
        elif not isinstance(last_accessed_at, datetime):
            last_accessed_at = None

        # Extract content
        content = item.get("content", item.get("text_content", ""))
        if not isinstance(content, str):
            content = str(content)

        # Extract metadata
        metadata = item.get("metadata", {})

        # Extract entities
        entities = item.get("entities", [])
        if not isinstance(entities, list):
            entities = []

        # Extract relationships
        relationships = item.get("relationships", [])
        if not isinstance(relationships, list):
            relationships = []

        # Create and return factors
        return ImportanceFactors(
            created_at=created_at,
            last_accessed_at=last_accessed_at,
            access_count=item.get("access_count", 0),
            reference_count=item.get("reference_count", 0),
            content_length=len(content),
            has_entities=len(entities) > 0,
            entity_count=len(entities),
            is_user_marked_important=metadata.get("important", False),
            explicit_importance=metadata.get("importance"),
            connected_item_count=len(relationships),
            semantic_richness=item.get("semantic_richness", 0.0),
        )

    def _calculate_recency_score(self, factors: ImportanceFactors) -> float:
        """
        Calculate recency score based on creation and access times.

        Args:
            factors: Importance factors

        Returns:
            Recency score (0.0 to 1.0)
        """
        # Use last accessed time if available, otherwise creation time
        reference_time = factors.last_accessed_at or factors.created_at

        # Calculate age in days
        age_days = (datetime.utcnow() - reference_time).total_seconds() / (24 * 3600)

        # Apply exponential decay based on half-life
        half_life_days = self.config.recency_half_life_days
        decay_factor = 0.5 ** (age_days / half_life_days)

        return decay_factor

    def _calculate_usage_score(self, factors: ImportanceFactors) -> float:
        """
        Calculate usage score based on access and reference counts.

        Args:
            factors: Importance factors

        Returns:
            Usage score (0.0 to 1.0)
        """
        # Normalize access count
        access_score = min(1.0, factors.access_count / self.config.high_access_threshold)

        # Normalize reference count
        reference_score = min(1.0, factors.reference_count / self.config.high_reference_threshold)

        # Combine scores (higher weight on references)
        return 0.4 * access_score + 0.6 * reference_score

    def _calculate_content_score(self, factors: ImportanceFactors) -> float:
        """
        Calculate content score based on content length and entities.

        Args:
            factors: Importance factors

        Returns:
            Content score (0.0 to 1.0)
        """
        # Score based on content length
        if factors.content_length < self.config.min_content_length:
            length_score = 0.0
        else:
            length_score = min(1.0, factors.content_length / self.config.significant_content_length)

        # Score based on entities
        entity_score = min(1.0, factors.entity_count / 5.0)

        # Combine scores
        return 0.7 * length_score + 0.3 * entity_score

    def _calculate_metadata_score(self, factors: ImportanceFactors) -> float:
        """
        Calculate metadata score based on user importance marking.

        Args:
            factors: Importance factors

        Returns:
            Metadata score (0.0 to 1.0)
        """
        # If explicitly marked important, high score
        if factors.is_user_marked_important:
            return 1.0

        # If explicit importance provided, use it
        if factors.explicit_importance is not None:
            return max(0.0, min(1.0, factors.explicit_importance))

        # Default score
        return 0.0

    def _calculate_relationship_score(self, factors: ImportanceFactors) -> float:
        """
        Calculate relationship score based on connected items.

        Args:
            factors: Importance factors

        Returns:
            Relationship score (0.0 to 1.0)
        """
        # Normalize connection count
        return min(1.0, factors.connected_item_count / self.config.significant_connection_count)

    def _calculate_semantic_score(self, factors: ImportanceFactors) -> float:
        """
        Calculate semantic score based on semantic richness.

        Args:
            factors: Importance factors

        Returns:
            Semantic score (0.0 to 1.0)
        """
        # Normalize semantic richness (assumed to be in [0, 1] range)
        return max(0.0, min(1.0, factors.semantic_richness))
