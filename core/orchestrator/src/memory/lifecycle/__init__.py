"""
Memory Lifecycle Management for AI Orchestra.

This module provides functionality for managing the lifecycle of memory items,
including importance scoring, progressive summarization, and chunking.
"""

from core.orchestrator.src.memory.lifecycle.importance_scorer import (
    ImportanceFactors,
    ImportanceScore,
    ImportanceScorer,
    ImportanceScoringConfig,
)
from core.orchestrator.src.memory.lifecycle.memory_chunker import (
    Chunk,
    ChunkerConfig,
    ChunkingStrategy,
    ChunkMetadata,
    MemoryChunker,
)
from core.orchestrator.src.memory.lifecycle.progressive_summarizer import (
    ProgressiveSummarizer,
    ProgressiveSummarizerConfig,
    SummaryLevel,
    SummaryResult,
)

__all__ = [
    # Importance Scorer
    "ImportanceScorer",
    "ImportanceScore",
    "ImportanceFactors",
    "ImportanceScoringConfig",
    # Progressive Summarizer
    "ProgressiveSummarizer",
    "SummaryLevel",
    "SummaryResult",
    "ProgressiveSummarizerConfig",
    # Memory Chunker
    "MemoryChunker",
    "Chunk",
    "ChunkMetadata",
    "ChunkingStrategy",
    "ChunkerConfig",
]
