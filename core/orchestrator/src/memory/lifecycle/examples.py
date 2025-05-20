"""
Examples for Memory Lifecycle Components.

This module provides examples of how to use the memory lifecycle components
for importance scoring, progressive summarization, and chunking.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional

from core.orchestrator.src.memory.lifecycle import (
    ImportanceScorer,
    ImportanceScoringConfig,
    ImportanceFactors,
    ProgressiveSummarizer,
    SummaryLevel,
    MemoryChunker,
    ChunkingStrategy,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def importance_scorer_example():
    """Example of using the ImportanceScorer."""
    # Create an importance scorer with custom configuration
    scorer = ImportanceScorer(
        config=ImportanceScoringConfig(
            recency_weight=0.3,
            usage_weight=0.2,
            content_weight=0.2,
            metadata_weight=0.1,
            relationship_weight=0.1,
            semantic_weight=0.1,
        )
    )

    # Create a sample memory item
    from datetime import datetime, timedelta

    item = {
        "id": "mem123",
        "content": "This is an important memory about AI Orchestra architecture.",
        "created_at": datetime.utcnow() - timedelta(days=2),
        "last_accessed_at": datetime.utcnow() - timedelta(hours=3),
        "access_count": 5,
        "reference_count": 2,
        "entities": ["AI Orchestra", "architecture"],
        "metadata": {"important": True},
    }

    # Score the item
    score = scorer.score_item(item)

    # Print the results
    logger.info(f"Item ID: {score.item_id}")
    logger.info(f"Overall score: {score.score:.2f}")
    logger.info(f"Component scores:")
    logger.info(f"  Recency: {score.recency_score:.2f}")
    logger.info(f"  Usage: {score.usage_score:.2f}")
    logger.info(f"  Content: {score.content_score:.2f}")
    logger.info(f"  Metadata: {score.metadata_score:.2f}")
    logger.info(f"  Relationship: {score.relationship_score:.2f}")
    logger.info(f"  Semantic: {score.semantic_score:.2f}")

    return score


async def progressive_summarizer_example():
    """Example of using the ProgressiveSummarizer."""
    # Create a progressive summarizer
    summarizer = ProgressiveSummarizer()

    # Sample content to summarize
    content = """
    # AI Orchestra Memory System
    
    The AI Orchestra memory system is designed to provide a unified interface for managing
    different types of memory storage (short-term, mid-term, semantic) across various backends
    (Redis, Firestore, Vertex AI Vector Search, etc.).
    
    ## Key Components
    
    1. **Layered Memory**: Manages multiple memory layers with different characteristics
    2. **Memory Store**: Abstract interface for memory storage backends
    3. **Memory Query**: Encapsulates parameters for memory retrieval
    
    ## Memory Types
    
    - **Short-term memory**: Fast, ephemeral storage using Redis
    - **Mid-term memory**: Structured storage using Firestore
    - **Long-term memory**: Persistent storage using Firestore
    - **Semantic memory**: Vector-based storage using Vertex AI Vector Search
    
    ## Recent Enhancements
    
    The memory system has been enhanced with several new capabilities:
    
    1. **Parallel Retrieval**: Execute searches across multiple memory layers concurrently
    2. **Hybrid Search**: Combine keyword-based and semantic search for better results
    3. **Query Classification**: Dynamically adjust retrieval strategies based on query type
    4. **Importance Scoring**: Evaluate the importance of memory items for retention decisions
    5. **Progressive Summarization**: Create multi-level summaries for efficient storage
    6. **Memory Chunking**: Split large documents into semantic chunks for better retrieval
    
    These enhancements significantly improve the performance, scalability, and intelligence
    of the memory system while maintaining its clean architectural design.
    """

    # Create summaries at different levels
    item_id = "doc123"
    summaries = await summarizer.create_progressive_summaries(content, item_id)

    # Print the results
    for level, result in summaries.items():
        logger.info(f"\nSummary Level: {level}")
        logger.info(f"Length: {len(result.summary_text)} chars")
        logger.info(f"Compression ratio: {result.compression_ratio:.2f}x")
        logger.info(f"Summary: {result.summary_text[:100]}...")

    return summaries


async def memory_chunker_example():
    """Example of using the MemoryChunker."""
    # Create a memory chunker
    chunker = MemoryChunker()

    # Sample content to chunk
    content = """
    # AI Orchestra Memory System
    
    The AI Orchestra memory system is designed to provide a unified interface for managing
    different types of memory storage (short-term, mid-term, semantic) across various backends
    (Redis, Firestore, Vertex AI Vector Search, etc.).
    
    ## Key Components
    
    1. **Layered Memory**: Manages multiple memory layers with different characteristics
    2. **Memory Store**: Abstract interface for memory storage backends
    3. **Memory Query**: Encapsulates parameters for memory retrieval
    
    ## Memory Types
    
    - **Short-term memory**: Fast, ephemeral storage using Redis
    - **Mid-term memory**: Structured storage using Firestore
    - **Long-term memory**: Persistent storage using Firestore
    - **Semantic memory**: Vector-based storage using Vertex AI Vector Search
    
    ## Recent Enhancements
    
    The memory system has been enhanced with several new capabilities:
    
    1. **Parallel Retrieval**: Execute searches across multiple memory layers concurrently
    2. **Hybrid Search**: Combine keyword-based and semantic search for better results
    3. **Query Classification**: Dynamically adjust retrieval strategies based on query type
    4. **Importance Scoring**: Evaluate the importance of memory items for retention decisions
    5. **Progressive Summarization**: Create multi-level summaries for efficient storage
    6. **Memory Chunking**: Split large documents into semantic chunks for better retrieval
    
    These enhancements significantly improve the performance, scalability, and intelligence
    of the memory system while maintaining its clean architectural design.
    """

    # Chunk the content using different strategies
    item_id = "doc123"

    # Paragraph chunking
    paragraph_chunks = await chunker.chunk_item(
        item_id, content, ChunkingStrategy.PARAGRAPH
    )

    # Sentence chunking
    sentence_chunks = await chunker.chunk_item(
        item_id, content, ChunkingStrategy.SENTENCE
    )

    # Fixed size chunking
    fixed_chunks = await chunker.chunk_item(
        item_id, content, ChunkingStrategy.FIXED_SIZE
    )

    # Print the results
    logger.info(f"\nParagraph chunking: {len(paragraph_chunks)} chunks")
    for i, chunk in enumerate(paragraph_chunks):
        logger.info(
            f"  Chunk {i+1}: {len(chunk.content)} chars, Heading: {chunk.metadata.heading}"
        )

    logger.info(f"\nSentence chunking: {len(sentence_chunks)} chunks")
    for i, chunk in enumerate(sentence_chunks[:3]):  # Show first 3 chunks
        logger.info(f"  Chunk {i+1}: {len(chunk.content)} chars")

    logger.info(f"\nFixed size chunking: {len(fixed_chunks)} chunks")
    for i, chunk in enumerate(fixed_chunks[:3]):  # Show first 3 chunks
        logger.info(f"  Chunk {i+1}: {len(chunk.content)} chars")

    return {
        "paragraph": paragraph_chunks,
        "sentence": sentence_chunks,
        "fixed": fixed_chunks,
    }


async def integrated_example():
    """Example of using all memory lifecycle components together."""
    # Create components
    scorer = ImportanceScorer()
    summarizer = ProgressiveSummarizer()
    chunker = MemoryChunker()

    # Sample content
    content = """
    # AI Orchestra Memory System Architecture
    
    The AI Orchestra memory system provides a unified interface for managing different types
    of memory across various storage backends. This document outlines the key architectural
    components and recent enhancements.
    
    ## System Components
    
    The memory system consists of several key components:
    
    1. **Layered Memory Manager**: Coordinates access to different memory layers
    2. **Memory Stores**: Implementations for different storage backends
    3. **Query Engine**: Processes and optimizes memory queries
    4. **Memory Lifecycle**: Manages the lifecycle of memory items
    
    ## Recent Enhancements
    
    Several enhancements have been made to improve performance and functionality:
    
    - Parallel retrieval for faster search across memory layers
    - Hybrid search combining keyword and semantic approaches
    - Query classification for optimized retrieval strategies
    - Importance scoring for intelligent memory management
    - Progressive summarization for efficient storage
    - Memory chunking for better handling of large documents
    
    These improvements significantly enhance the system's capabilities while
    maintaining its clean architectural design.
    """

    # Process the content
    item_id = "doc456"

    # Step 1: Chunk the content
    logger.info("Step 1: Chunking content")
    chunks = await chunker.chunk_item(item_id, content, ChunkingStrategy.PARAGRAPH)
    logger.info(f"Created {len(chunks)} chunks")

    # Step 2: Create summaries for each chunk
    logger.info("\nStep 2: Creating summaries")
    all_summaries = []
    for i, chunk in enumerate(chunks):
        chunk_id = f"{item_id}_chunk_{i}"
        summaries = await summarizer.create_progressive_summaries(
            chunk.content, chunk_id
        )
        all_summaries.append(summaries)
        logger.info(f"Created summaries for chunk {i+1}")

    # Step 3: Score the importance of each chunk
    logger.info("\nStep 3: Scoring importance")
    scores = []
    for i, chunk in enumerate(chunks):
        # Create a memory item from the chunk
        item = {
            "id": chunk.metadata.chunk_id,
            "content": chunk.content,
            "created_at": datetime.utcnow(),
            "access_count": 0,
            "reference_count": 0,
            "entities": [],
            "metadata": chunk.metadata.custom_metadata,
        }

        # Score the item
        score = scorer.score_item(item)
        scores.append(score)
        logger.info(f"Chunk {i+1} importance score: {score.score:.2f}")

    # Step 4: Determine storage strategy based on importance
    logger.info("\nStep 4: Determining storage strategy")
    storage_decisions = []
    for i, score in enumerate(scores):
        if score.score > 0.7:
            # High importance: store full content
            decision = "full_content"
        elif score.score > 0.4:
            # Medium importance: store condensed summary
            decision = "condensed"
        else:
            # Low importance: store key points only
            decision = "key_points"

        storage_decisions.append(decision)
        logger.info(f"Chunk {i+1} storage decision: {decision}")

    return {
        "chunks": chunks,
        "summaries": all_summaries,
        "scores": scores,
        "decisions": storage_decisions,
    }


# Import datetime here to avoid circular import
from datetime import datetime


# Run examples if module is executed directly
if __name__ == "__main__":

    async def run_examples():
        logger.info("Running importance scorer example...")
        await importance_scorer_example()

        logger.info("\nRunning progressive summarizer example...")
        await progressive_summarizer_example()

        logger.info("\nRunning memory chunker example...")
        await memory_chunker_example()

        logger.info("\nRunning integrated example...")
        await integrated_example()

    # Run the examples
    asyncio.run(run_examples())
