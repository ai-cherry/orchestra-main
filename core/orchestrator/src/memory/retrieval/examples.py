e in """
Integration Examples for Memory Retrieval Components.

This module provides examples of how to use the new memory retrieval components
with the existing memory system.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional

from core.orchestrator.src.memory.interface import MemoryInterface
from core.orchestrator.src.memory.layered_memory import LayeredMemory
from core.orchestrator.src.memory.retrieval import (
    ParallelMemoryRetriever,
    HybridSearchEngine,
    HybridSearchConfig,
    QueryClassifier,
)

# Configure logging
logger = logging.getLogger(__name__)


async def parallel_retrieval_example(layered_memory: LayeredMemory) -> None:
    """
    Example of using the ParallelMemoryRetriever with LayeredMemory.

    Args:
        layered_memory: An initialized LayeredMemory instance
    """
    # Create a parallel retriever using the layers from LayeredMemory
    retriever = ParallelMemoryRetriever(
        layers=layered_memory.layers,
        # Customize layer weights if needed
        layer_weights={
            "short_term": 1.2,  # Prioritize recent information
            "mid_term": 1.0,
            "long_term": 0.8,
            "semantic": 1.5,  # Prioritize semantic matches
        },
        timeout=3.0,  # Set timeout for layer queries
    )

    # Perform a search across all layers in parallel
    query = "AI Orchestra architecture"
    results = await retriever.search(
        field="content", value=query, operator="contains", limit=10
    )

    # Process results
    logger.info(f"Found {len(results)} results for query: '{query}'")
    for i, result in enumerate(results):
        logger.info(
            f"Result {i+1}: Score={result.score:.2f}, "
            f"Source={result.source_layer}, "
            f"Time={result.retrieval_time_ms:.2f}ms"
        )

    # Perform a semantic search
    semantic_results = await retriever.semantic_search(query=query, limit=10)

    logger.info(f"Found {len(semantic_results)} semantic results for query: '{query}'")


async def hybrid_search_example(layered_memory: LayeredMemory) -> None:
    """
    Example of using the HybridSearchEngine with LayeredMemory.

    Args:
        layered_memory: An initialized LayeredMemory instance
    """
    # Create a hybrid search engine
    search_engine = HybridSearchEngine(
        layers=layered_memory.layers,
        config=HybridSearchConfig(
            # Customize weights for different search types
            keyword_weight=1.0,
            semantic_weight=1.2,
            # Fusion method: "weighted_sum" or "reciprocal_rank_fusion"
            fusion_method="weighted_sum",
        ),
    )

    # Perform hybrid search
    query = "How does the memory system work in AI Orchestra?"
    results = await search_engine.search(query=query, limit=10)

    # Process results
    logger.info(f"Found {len(results)} hybrid results for query: '{query}'")
    for i, result in enumerate(results):
        search_type = result.item.get("search_type", "unknown")
        logger.info(
            f"Result {i+1}: Score={result.score:.2f}, "
            f"Type={search_type}, Source={result.source_layer}"
        )


async def query_classification_example() -> None:
    """Example of using the QueryClassifier."""
    # Create a query classifier
    classifier = QueryClassifier(
        # Enable Vertex AI for production use
        use_vertex_ai=False,
        # Configure confidence threshold
        confidence_threshold=0.6,
    )

    # Example queries to classify
    queries = [
        "What is AI Orchestra?",
        "Why does the memory system use multiple layers?",
        "Can you help me understand how agents communicate?",
        "Show me the code for the LayeredMemory class",
        "Compare Redis and Firestore for memory storage",
    ]

    # Classify each query
    for query in queries:
        result = await classifier.classify(query)
        logger.info(
            f"Query: '{query}'\n"
            f"Type: {result.query_type} (Confidence: {result.confidence:.2f})\n"
            f"Scores: {', '.join(f'{k}={v:.2f}' for k, v in result.scores.items())}\n"
        )


async def enhanced_layered_memory_example() -> None:
    """
    Example of enhancing LayeredMemory with the new retrieval components.

    This example shows how to extend the existing LayeredMemory class
    with the new retrieval capabilities.
    """
    # This is a simplified example - in a real implementation,
    # you would use actual memory stores

    # Create mock memory stores
    mock_layers: Dict[str, MemoryInterface] = {
        "short_term": MockMemoryStore("short_term"),
        "mid_term": MockMemoryStore("mid_term"),
        "long_term": MockMemoryStore("long_term"),
        "semantic": MockMemoryStore("semantic"),
    }

    # Create layered memory
    layered_memory = LayeredMemory(layers=mock_layers, auto_promote=True)

    # Create retrieval components
    retriever = ParallelMemoryRetriever(layers=mock_layers)
    search_engine = HybridSearchEngine(layers=mock_layers)
    classifier = QueryClassifier()

    # Example query
    query = "How do agents communicate in AI Orchestra?"

    # Classify the query
    classification = await classifier.classify(query)
    query_type = classification.query_type

    logger.info(f"Query classified as: {query_type}")

    # Use appropriate search strategy based on query type
    if query_type == "factual":
        # For factual queries, prioritize exact matches
        results = await retriever.search(
            field="content", value=query, operator="contains", limit=5
        )
    elif query_type == "conceptual":
        # For conceptual queries, prioritize semantic matches
        results = await retriever.semantic_search(query=query, limit=5)
    else:
        # For other queries, use hybrid search
        results = await search_engine.search(
            query=query, limit=5, query_type=query_type
        )

    logger.info(f"Found {len(results)} results using strategy for {query_type} query")


# Simple mock memory store for examples
class MockMemoryStore(MemoryInterface):
    """Mock memory store for examples."""

    def __init__(self, name: str):
        """Initialize mock memory store."""
        self.name = name
        self.items: Dict[str, Dict[str, Any]] = {}

    async def store(
        self, key: str, value: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        """Store an item."""
        self.items[key] = value
        return True

    async def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve an item."""
        return self.items.get(key)

    async def delete(self, key: str) -> bool:
        """Delete an item."""
        if key in self.items:
            del self.items[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if an item exists."""
        return key in self.items

    async def search(
        self, field: str, value: Any, operator: str = "==", limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for items."""
        # Mock implementation - in a real store, this would perform actual search
        results = []
        for item_key, item in self.items.items():
            if len(results) >= limit:
                break

            # Simple contains check for text fields
            if (
                field in item
                and isinstance(item[field], str)
                and isinstance(value, str)
            ):
                if operator == "contains" and value.lower() in item[field].lower():
                    results.append(item)
                elif operator == "==" and value.lower() == item[field].lower():
                    results.append(item)

        return results


# Run examples if module is executed directly
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run examples
    async def run_examples():
        # Create mock layered memory for examples
        mock_layers = {
            "short_term": MockMemoryStore("short_term"),
            "mid_term": MockMemoryStore("mid_term"),
            "long_term": MockMemoryStore("long_term"),
            "semantic": MockMemoryStore("semantic"),
        }
        layered_memory = LayeredMemory(layers=mock_layers)

        # Run examples
        logger.info("Running parallel retrieval example...")
        await parallel_retrieval_example(layered_memory)

        logger.info("\nRunning hybrid search example...")
        await hybrid_search_example(layered_memory)

        logger.info("\nRunning query classification example...")
        await query_classification_example()

        logger.info("\nRunning enhanced layered memory example...")
        await enhanced_layered_memory_example()

    # Run the examples
    asyncio.run(run_examples())
