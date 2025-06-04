# Memory Lifecycle Management

This module provides components for managing the lifecycle of memory items in the AI cherry_ai memory system, including importance scoring, progressive summarization, and chunking.

## Overview

The memory lifecycle management system enhances the existing memory architecture with:

1. **Importance Scoring**: Evaluate the importance of memory items for retention decisions
2. **Progressive Summarization**: Create multi-level summaries for efficient storage
3. **Memory Chunking**: Split large documents into semantic chunks for better retrieval

These components work together to provide more intelligent memory management, optimizing storage while preserving important information.

## Components

### ImportanceScorer

The `ImportanceScorer` evaluates the importance of memory items based on various factors, including recency, usage, content, metadata, relationships, and semantic richness.

Key features:

- Multi-factor importance scoring
- Configurable weights for different factors
- Detailed component scores for transparency

```python
from core.conductor.src.memory.lifecycle import ImportanceScorer, ImportanceScoringConfig

# Create scorer with custom configuration
scorer = ImportanceScorer(
    config=ImportanceScoringConfig(
        recency_weight=0.3,
        usage_weight=0.2,
        content_weight=0.2,
        metadata_weight=0.1,
        relationship_weight=0.1,
        semantic_weight=0.1
    )
)

# Score a memory item
item = {
    "id": "mem123",
    "content": "Important memory about AI cherry_ai",
    "created_at": datetime.utcnow() - timedelta(days=2),
    "access_count": 5,
    "metadata": {"important": True}
}

score = scorer.score_item(item)
print(f"Overall importance score: {score.score:.2f}")
```

### ProgressiveSummarizer

The `ProgressiveSummarizer` creates multi-level summaries of memory items, from condensed highlights to single-sentence headlines, optimizing storage while preserving context.

Key features:

- Multiple summary levels (full, condensed, key points, headline)
- AI-powered summarization using Vertex AI
- Entity and keyword preservation

```python
from core.conductor.src.memory.lifecycle import ProgressiveSummarizer, SummaryLevel

# Create summarizer
summarizer = ProgressiveSummarizer()

# Create summaries at different levels
content = "Long document content..."
item_id = "doc123"
summaries = await summarizer.create_progressive_summaries(content, item_id)

# Access summaries at different levels
full_content = summaries[SummaryLevel.FULL].summary_text
condensed = summaries[SummaryLevel.CONDENSED].summary_text
key_points = summaries[SummaryLevel.KEY_POINTS].summary_text
headline = summaries[SummaryLevel.HEADLINE].summary_text
```

### MemoryChunker

The `MemoryChunker` splits large documents into semantic chunks for more efficient storage and retrieval, using various chunking strategies.

Key features:

- Multiple chunking strategies (paragraph, sentence, fixed size, semantic, hybrid)
- Semantic chunking using Vertex AI
- Heading extraction and summary generation

```python
from core.conductor.src.memory.lifecycle import MemoryChunker, ChunkingStrategy

# Create chunker
chunker = MemoryChunker()

# Chunk a document using different strategies
content = "Long document content..."
item_id = "doc123"

# Paragraph chunking
paragraph_chunks = await chunker.chunk_item(
    item_id, content, ChunkingStrategy.PARAGRAPH
)

# Semantic chunking
semantic_chunks = await chunker.chunk_item(
    item_id, content, ChunkingStrategy.SEMANTIC
)

# Process chunks
for chunk in paragraph_chunks:
    print(f"Chunk ID: {chunk.metadata.chunk_id}")
    print(f"Content: {chunk.content[:50]}...")
    print(f"Heading: {chunk.metadata.heading}")
```

## Integration with Memory System

These components can be integrated with the existing memory system to provide more intelligent memory management:

```python
# Example: Intelligent memory storage based on importance
async def store_with_intelligence(content, item_id):
    # Create components
    chunker = MemoryChunker()
    summarizer = ProgressiveSummarizer()
    scorer = ImportanceScorer()

    # Step 1: Chunk the content
    chunks = await chunker.chunk_item(item_id, content)

    # Step 2: Score each chunk
    for chunk in chunks:
        # Create a memory item from the chunk
        item = {
            "id": chunk.metadata.chunk_id,
            "content": chunk.content,
            "created_at": datetime.utcnow()
        }

        # Score the item
        score = scorer.score_item(item)

        # Step 3: Create appropriate summary based on importance
        if score.score > 0.7:
            # High importance: store full content
            memory_content = chunk.content
        elif score.score > 0.4:
            # Medium importance: store condensed summary
            summaries = await summarizer.create_progressive_summaries(chunk.content, chunk.metadata.chunk_id)
            memory_content = summaries[SummaryLevel.CONDENSED].summary_text
        else:
            # Low importance: store key points only
            summaries = await summarizer.create_progressive_summaries(chunk.content, chunk.metadata.chunk_id)
            memory_content = summaries[SummaryLevel.KEY_POINTS].summary_text

        # Step 4: Store in memory system
        # memory_manager.store(chunk.metadata.chunk_id, memory_content)
```

## Performance Considerations

- **Vertex AI Integration**: The summarizer and chunker can use Vertex AI for AI-powered processing, which may add latency but improves quality
- **Batch Processing**: For large documents, consider processing chunks in batches
- **Caching**: Consider caching importance scores and summaries for frequently accessed items

## Future Enhancements

- **Adaptive Importance Thresholds**: Dynamically adjust importance thresholds based on storage usage
- **Personalized Importance Scoring**: Incorporate user-specific factors in importance scoring
- **Cross-Document Relationships**: Consider relationships between documents in importance scoring

## Examples

See the `examples.py` file for complete usage examples.

## Testing

Run the tests to verify the functionality:

```bash
pytest tests/core/conductor/memory/lifecycle/
```
