"""
Tests for the ImportanceScorer class.

This module contains tests for the ImportanceScorer class to ensure
it correctly evaluates the importance of memory items.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from core.orchestrator.src.memory.lifecycle import (
    ImportanceScorer,
    ImportanceScoringConfig,
    ImportanceFactors
)


@pytest.fixture
def sample_memory_item() -> Dict[str, Any]:
    """Fixture providing a sample memory item for testing."""
    return {
        "id": "test_item_1",
        "content": "This is a test memory item about AI Orchestra architecture.",
        "created_at": datetime.utcnow() - timedelta(days=2),
        "last_accessed_at": datetime.utcnow() - timedelta(hours=3),
        "access_count": 5,
        "reference_count": 2,
        "entities": ["AI Orchestra", "architecture"],
        "metadata": {
            "important": True
        }
    }


@pytest.fixture
def importance_scorer() -> ImportanceScorer:
    """Fixture providing an ImportanceScorer instance for testing."""
    config = ImportanceScoringConfig(
        recency_weight=0.3,
        usage_weight=0.2,
        content_weight=0.2,
        metadata_weight=0.1,
        relationship_weight=0.1,
        semantic_weight=0.1
    )
    return ImportanceScorer(config=config)


def test_score_item(importance_scorer, sample_memory_item):
    """Test that score_item correctly evaluates a memory item."""
    # Score the item
    score = importance_scorer.score_item(sample_memory_item)
    
    # Check that the score is within the expected range
    assert 0.0 <= score.score <= 1.0
    
    # Check that the item ID is correct
    assert score.item_id == sample_memory_item["id"]
    
    # Check that all component scores are within the expected range
    assert 0.0 <= score.recency_score <= 1.0
    assert 0.0 <= score.usage_score <= 1.0
    assert 0.0 <= score.content_score <= 1.0
    assert 0.0 <= score.metadata_score <= 1.0
    assert 0.0 <= score.relationship_score <= 1.0
    assert 0.0 <= score.semantic_score <= 1.0


def test_recency_score(importance_scorer):
    """Test that recency scoring works correctly."""
    # Create items with different creation times
    recent_item = {
        "id": "recent",
        "content": "Recent item",
        "created_at": datetime.utcnow() - timedelta(hours=1)
    }
    
    old_item = {
        "id": "old",
        "content": "Old item",
        "created_at": datetime.utcnow() - timedelta(days=30)
    }
    
    # Score the items
    recent_score = importance_scorer.score_item(recent_item)
    old_score = importance_scorer.score_item(old_item)
    
    # Recent items should have higher recency scores
    assert recent_score.recency_score > old_score.recency_score


def test_usage_score(importance_scorer):
    """Test that usage scoring works correctly."""
    # Create items with different usage patterns
    high_usage_item = {
        "id": "high_usage",
        "content": "High usage item",
        "created_at": datetime.utcnow(),
        "access_count": 20,
        "reference_count": 10
    }
    
    low_usage_item = {
        "id": "low_usage",
        "content": "Low usage item",
        "created_at": datetime.utcnow(),
        "access_count": 1,
        "reference_count": 0
    }
    
    # Score the items
    high_usage_score = importance_scorer.score_item(high_usage_item)
    low_usage_score = importance_scorer.score_item(low_usage_item)
    
    # High usage items should have higher usage scores
    assert high_usage_score.usage_score > low_usage_score.usage_score


def test_content_score(importance_scorer):
    """Test that content scoring works correctly."""
    # Create items with different content
    rich_content_item = {
        "id": "rich_content",
        "content": "This is a detailed item with lots of information about AI Orchestra architecture and its components.",
        "created_at": datetime.utcnow(),
        "entities": ["AI Orchestra", "architecture", "components", "memory", "agents"]
    }
    
    sparse_content_item = {
        "id": "sparse_content",
        "content": "Short item.",
        "created_at": datetime.utcnow(),
        "entities": []
    }
    
    # Score the items
    rich_content_score = importance_scorer.score_item(rich_content_item)
    sparse_content_score = importance_scorer.score_item(sparse_content_item)
    
    # Rich content items should have higher content scores
    assert rich_content_score.content_score > sparse_content_score.content_score


def test_metadata_score(importance_scorer):
    """Test that metadata scoring works correctly."""
    # Create items with different metadata
    important_item = {
        "id": "important",
        "content": "Important item",
        "created_at": datetime.utcnow(),
        "metadata": {
            "important": True
        }
    }
    
    regular_item = {
        "id": "regular",
        "content": "Regular item",
        "created_at": datetime.utcnow(),
        "metadata": {}
    }
    
    explicit_importance_item = {
        "id": "explicit_importance",
        "content": "Item with explicit importance",
        "created_at": datetime.utcnow(),
        "metadata": {
            "importance": 0.8
        }
    }
    
    # Score the items
    important_score = importance_scorer.score_item(important_item)
    regular_score = importance_scorer.score_item(regular_item)
    explicit_importance_score = importance_scorer.score_item(explicit_importance_item)
    
    # Important items should have higher metadata scores
    assert important_score.metadata_score > regular_score.metadata_score
    assert explicit_importance_score.metadata_score > regular_score.metadata_score
    assert important_score.metadata_score == 1.0  # Should be maximum score


def test_extract_factors(importance_scorer, sample_memory_item):
    """Test that _extract_factors correctly extracts importance factors."""
    # Extract factors
    factors = importance_scorer._extract_factors(sample_memory_item)
    
    # Check that factors are correctly extracted
    assert isinstance(factors, ImportanceFactors)
    assert factors.created_at == sample_memory_item["created_at"]
    assert factors.last_accessed_at == sample_memory_item["last_accessed_at"]
    assert factors.access_count == sample_memory_item["access_count"]
    assert factors.reference_count == sample_memory_item["reference_count"]
    assert factors.content_length > 0
    assert factors.has_entities == True
    assert factors.entity_count == len(sample_memory_item["entities"])
    assert factors.is_user_marked_important == sample_memory_item["metadata"]["important"]


def test_weights_sum_to_one():
    """Test that the weights in the config sum to 1.0."""
    # Create config with custom weights
    config = ImportanceScoringConfig(
        recency_weight=0.2,
        usage_weight=0.2,
        content_weight=0.2,
        metadata_weight=0.2,
        relationship_weight=0.1,
        semantic_weight=0.1
    )
    
    # Check that weights sum to 1.0
    weights_sum = (
        config.recency_weight +
        config.usage_weight +
        config.content_weight +
        config.metadata_weight +
        config.relationship_weight +
        config.semantic_weight
    )
    
    assert abs(weights_sum - 1.0) < 0.001


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])