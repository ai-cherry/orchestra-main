"""
Tests for the ParallelMemoryRetriever class.

This module contains tests for the ParallelMemoryRetriever class to ensure
it correctly performs parallel retrieval across multiple memory layers.
"""

import asyncio
import pytest
from typing import Dict, List, Any, Optional
from unittest.mock import MagicMock, patch

from core.orchestrator.src.memory.interface import MemoryInterface
from core.orchestrator.src.memory.retrieval import ParallelMemoryRetriever, SearchResult


class MockMemoryStore(MemoryInterface):
    """Mock memory store for testing."""
    
    def __init__(self, name: str, delay: float = 0.0, items: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Initialize mock memory store.
        
        Args:
            name: Name of the store
            delay: Artificial delay in seconds to simulate processing time
            items: Initial items to populate the store with
        """
        self.name = name
        self.delay = delay
        self.items = items or {}
        self.search_called = False
    
    async def store(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Store an item."""
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        self.items[key] = value
        return True
    
    async def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve an item."""
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        return self.items.get(key)
    
    async def delete(self, key: str) -> bool:
        """Delete an item."""
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        if key in self.items:
            del self.items[key]
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        """Check if an item exists."""
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        return key in self.items
    
    async def search(
        self, 
        field: str, 
        value: Any, 
        operator: str = "==",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for items."""
        self.search_called = True
        if self.delay > 0:
            await asyncio.sleep(self.delay)
            
        results = []
        for item_key, item in self.items.items():
            if len(results) >= limit:
                break
                
            # Simple contains check for text fields
            if field in item and isinstance(item[field], str) and isinstance(value, str):
                if operator == "contains" and value.lower() in item[field].lower():
                    results.append(item)
                elif operator == "==" and value.lower() == item[field].lower():
                    results.append(item)
            
            # Special case for semantic search
            elif field == "semantic" and "content" in item:
                # In a real implementation, this would use vector similarity
                # For testing, we'll just do a simple text match
                if isinstance(value, str) and isinstance(item["content"], str):
                    if value.lower() in item["content"].lower():
                        results.append(item)
        
        return results


@pytest.fixture
def memory_layers():
    """Fixture providing mock memory layers for testing."""
    return {
        "short_term": MockMemoryStore("short_term", delay=0.1, items={
            "item1": {"id": "item1", "content": "AI Orchestra short-term memory"},
            "item2": {"id": "item2", "content": "Testing parallel retrieval"}
        }),
        "mid_term": MockMemoryStore("mid_term", delay=0.2, items={
            "item3": {"id": "item3", "content": "AI Orchestra mid-term memory"},
            "item4": {"id": "item4", "content": "Memory system architecture"}
        }),
        "long_term": MockMemoryStore("long_term", delay=0.3, items={
            "item5": {"id": "item5", "content": "AI Orchestra long-term memory"},
            "item6": {"id": "item6", "content": "Layered memory implementation"}
        }),
        "semantic": MockMemoryStore("semantic", delay=0.4, items={
            "item7": {"id": "item7", "content": "Vector-based semantic search"},
            "item8": {"id": "item8", "content": "Embedding models for memory"}
        })
    }


@pytest.mark.asyncio
async def test_parallel_retrieval(memory_layers):
    """Test that retrieval happens in parallel across layers."""
    # Create retriever
    retriever = ParallelMemoryRetriever(layers=memory_layers)
    
    # Start timer
    start_time = asyncio.get_event_loop().time()
    
    # Perform search
    results = await retriever.search(
        field="content",
        value="memory",
        operator="contains",
        limit=10
    )
    
    # End timer
    end_time = asyncio.get_event_loop().time()
    elapsed_time = end_time - start_time
    
    # Verify results
    assert len(results) > 0
    
    # Check that all layers were searched
    for layer_name, layer in memory_layers.items():
        assert layer.search_called, f"Layer {layer_name} was not searched"
    
    # Check that search was parallel (elapsed time should be close to the slowest layer)
    # Add a small buffer for processing overhead
    assert elapsed_time < 0.5, f"Search took {elapsed_time:.2f}s, expected < 0.5s for parallel execution"


@pytest.mark.asyncio
async def test_layer_weights(memory_layers):
    """Test that layer weights are applied correctly."""
    # Create retriever with custom weights
    retriever = ParallelMemoryRetriever(
        layers=memory_layers,
        layer_weights={
            "short_term": 2.0,
            "mid_term": 1.0,
            "long_term": 0.5,
            "semantic": 1.5
        }
    )
    
    # Perform search
    results = await retriever.search(
        field="content",
        value="AI Orchestra",
        operator="contains",
        limit=10
    )
    
    # Verify results are sorted by score (which includes layer weights)
    assert len(results) > 0
    
    # Check that scores reflect layer weights
    for result in results:
        if result.source_layer == "short_term":
            assert result.score > 1.5, "Short-term results should have higher scores"
        elif result.source_layer == "semantic":
            assert result.score > 1.0, "Semantic results should have higher scores"


@pytest.mark.asyncio
async def test_timeout_handling(memory_layers):
    """Test that timeouts are handled correctly."""
    # Create a very slow layer that will timeout
    slow_layer = MockMemoryStore("slow", delay=2.0)
    memory_layers["slow"] = slow_layer
    
    # Create retriever with short timeout
    retriever = ParallelMemoryRetriever(
        layers=memory_layers,
        timeout=0.5
    )
    
    # Perform search
    results = await retriever.search(
        field="content",
        value="memory",
        operator="contains",
        limit=10
    )
    
    # Verify we got results from other layers despite the timeout
    assert len(results) > 0
    
    # Check that all layers except the slow one were searched
    for layer_name, layer in memory_layers.items():
        if layer_name != "slow":
            assert layer.search_called, f"Layer {layer_name} was not searched"


@pytest.mark.asyncio
async def test_semantic_search(memory_layers):
    """Test semantic search functionality."""
    # Create retriever
    retriever = ParallelMemoryRetriever(layers=memory_layers)
    
    # Perform semantic search
    results = await retriever.semantic_search(
        query="vector embeddings",
        limit=5
    )
    
    # Verify results
    assert len(results) > 0
    
    # Check that semantic layer was prioritized
    semantic_results = [r for r in results if r.source_layer == "semantic"]
    assert len(semantic_results) > 0, "Expected results from semantic layer"
    
    # Check that semantic results have higher scores
    if len(results) > 1:
        semantic_scores = [r.score for r in results if r.source_layer == "semantic"]
        other_scores = [r.score for r in results if r.source_layer != "semantic"]
        
        if semantic_scores and other_scores:
            assert max(semantic_scores) >= max(other_scores), "Semantic results should have higher scores"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])