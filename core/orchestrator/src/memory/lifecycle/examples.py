"""
"""
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def importance_scorer_example():
    """Example of using the ImportanceScorer."""
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
    logger.info("Component scores:")
    logger.info(f"  Recency: {score.recency_score:.2f}")
    logger.info(f"  Usage: {score.usage_score:.2f}")
    logger.info(f"  Content: {score.content_score:.2f}")
    logger.info(f"  Metadata: {score.metadata_score:.2f}")
    logger.info(f"  Relationship: {score.relationship_score:.2f}")
    logger.info(f"  Semantic: {score.semantic_score:.2f}")

    return score

async def progressive_summarizer_example():
    """Example of using the ProgressiveSummarizer."""
    content = """
    """
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
    content = """
    """
    item_id = "doc123"

    # Paragraph chunking
    paragraph_chunks = await chunker.chunk_item(item_id, content, ChunkingStrategy.PARAGRAPH)

    # Sentence chunking
    sentence_chunks = await chunker.chunk_item(item_id, content, ChunkingStrategy.SENTENCE)

    # Fixed size chunking
    fixed_chunks = await chunker.chunk_item(item_id, content, ChunkingStrategy.FIXED_SIZE)

    # Print the results
    logger.info(f"\nParagraph chunking: {len(paragraph_chunks)} chunks")
    for i, chunk in enumerate(paragraph_chunks):
        logger.info(f"  Chunk {i+1}: {len(chunk.content)} chars, Heading: {chunk.metadata.heading}")

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
    content = """
    """
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
        summaries = await summarizer.create_progressive_summaries(chunk.content, chunk_id)
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
