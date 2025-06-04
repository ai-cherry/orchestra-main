# Memory Retrieval System

This module provides advanced retrieval capabilities for the AI cherry_ai memory system, enabling more efficient and effective memory access across different storage layers.

## Overview

The memory retrieval system enhances the existing layered memory architecture with:

1. **Parallel Retrieval**: Execute searches across multiple memory layers concurrently
2. **Hybrid Search**: Combine keyword-based and semantic search for better results
3. **Query Classification**: Dynamically adjust retrieval strategies based on query type

These components work together to provide significant performance improvements and more relevant search results.

## Components

### ParallelMemoryRetriever

The `ParallelMemoryRetriever` executes searches across multiple memory layers in parallel using asyncio, significantly reducing retrieval latency compared to sequential searching.

Key features:

- Concurrent layer querying with configurable timeouts
- Layer-specific weighting for result scoring
- Graceful handling of layer failures

```python
from core.conductor.src.memory.retrieval import ParallelMemoryRetriever

# Create retriever with existing memory layers
retriever = ParallelMemoryRetriever(
    layers=layered_memory.layers,
    layer_weights={
        "short_term": 1.2,  # Prioritize recent information
        "mid_term": 1.0,
        "long_term": 0.8,
        "semantic": 1.5     # Prioritize semantic matches
    },
    timeout=3.0  # Set timeout for layer queries
)

# Perform search across all layers in parallel
results = await retriever.search(
    field="content",
    value="AI cherry_ai architecture",
    operator="contains",
    limit=10
)

# Perform semantic search
semantic_results = await retriever.semantic_search(
    query="AI cherry_ai architecture",
    limit=10
)
```

### HybridSearchEngine

The `HybridSearchEngine` combines keyword-based and semantic search approaches for more comprehensive results. It uses fusion algorithms to merge results from different search methods.

Key features:

- Multiple fusion algorithms (weighted sum, reciprocal rank fusion)
- Query type-specific weighting
- Configurable search parameters

```python
from core.conductor.src.memory.retrieval import HybridSearchEngine, HybridSearchConfig

# Create hybrid search engine
search_engine = HybridSearchEngine(
    layers=layered_memory.layers,
    config=HybridSearchConfig(
        # Customize weights for different search types
        keyword_weight=1.0,
        semantic_weight=1.2,
        # Fusion method: "weighted_sum" or "reciprocal_rank_fusion"
        fusion_method="weighted_sum"
    )
)

# Perform hybrid search
results = await search_engine.search(
    query="How does the memory system work in AI cherry_ai?",
    limit=10
)
```

### QueryClassifier

The `QueryClassifier` categorizes queries into different types (factual, conceptual, conversational) to optimize retrieval strategies. It supports both rule-based classification and Vertex AI-based classification.

Key features:

- Multiple classification methods (rule-based, Vertex AI)
- Feature extraction for query analysis
- Confidence scoring for classification results

```python
from core.conductor.src.memory.retrieval import QueryClassifier, QueryType

# Create query classifier
classifier = QueryClassifier(
    # Enable Vertex AI for production use
    use_vertex_ai=True,
    vertex_ai_config={
        "project": "cherry-ai-project",
        "location": "us-central1"
    },
    confidence_threshold=0.6
)

# Classify a query
result = await classifier.classify("What is AI cherry_ai?")
query_type = result.query_type  # e.g., QueryType.FACTUAL

# Use classification to select retrieval strategy
if query_type == QueryType.FACTUAL:
    # Use keyword search for factual queries
    results = await retriever.search(field="content", value=query, operator="contains")
elif query_type == QueryType.CONCEPTUAL:
    # Use semantic search for conceptual queries
    results = await retriever.semantic_search(query=query)
else:
    # Use hybrid search for other queries
    results = await search_engine.search(query=query)
```

## Integration with Existing Memory System

These components are designed to work seamlessly with the existing layered memory system. They can be used individually or together to enhance memory retrieval capabilities.

### Basic Integration

```python
from core.conductor.src.memory.layered_memory import LayeredMemory
from core.conductor.src.memory.retrieval import ParallelMemoryRetriever

# Use with existing LayeredMemory
layered_memory = LayeredMemory(layers=memory_layers)

# Create retriever using the same layers
retriever = ParallelMemoryRetriever(layers=layered_memory.layers)

# Use retriever for more efficient searches
results = await retriever.search(field="content", value="query", operator="contains")
```

### Advanced Integration

For more advanced integration, you can extend the `LayeredMemory` class to use these new components internally:

```python
class EnhancedLayeredMemory(LayeredMemory):
    """Enhanced layered memory with advanced retrieval capabilities."""

    def __init__(self, layers, auto_promote=True, auto_demote=False):
        """Initialize enhanced layered memory."""
        super().__init__(layers, auto_promote, auto_demote)

        # Initialize retrieval components
        self.retriever = ParallelMemoryRetriever(layers=layers)
        self.search_engine = HybridSearchEngine(layers=layers)
        self.classifier = QueryClassifier()

    async def enhanced_search(self, query, limit=10):
        """Perform enhanced search using query classification."""
        # Classify the query
        classification = await self.classifier.classify(query)
        query_type = classification.query_type

        # Use appropriate search strategy based on query type
        if query_type == "factual":
            return await self.retriever.search(
                field="content", value=query, operator="contains", limit=limit
            )
        elif query_type == "conceptual":
            return await self.retriever.semantic_search(query=query, limit=limit)
        else:
            return await self.search_engine.search(query=query, limit=limit)
```

## Performance Considerations

- **Timeouts**: Configure appropriate timeouts for each layer to prevent slow layers from blocking results
- **Layer Weights**: Adjust layer weights based on your specific use case and data distribution
- **Fusion Methods**: Experiment with different fusion methods to find the best approach for your data

## Future Enhancements

- **Caching**: Add caching for frequently accessed queries and embeddings
- **Advanced Ranking**: Implement more sophisticated ranking algorithms
- **Personalization**: Add user-specific ranking and filtering

## Examples

See the `examples.py` file for complete usage examples.

## Testing

Run the tests to verify the functionality:

```bash
pytest tests/core/conductor/memory/retrieval/
```
