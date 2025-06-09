# Adaptive Context Management System

## Overview

The Adaptive Context Management System implements a dynamic context management system that intelligently prioritizes information based on relevance and recency. It organizes context into hierarchical layers and implements decay mechanisms to ensure the most relevant information is readily available.

## Key Components

### 1. Hierarchical Context Structure

The system organizes context information into three distinct layers:

- **Primary**: The most relevant and recent information that is immediately accessible
- **Secondary**: Information that is still relevant but not as immediately important
- **Background**: Historical information that may become relevant again in the future

### 2. Context Items

Each piece of information is stored as a context item with metadata about its source, type, and relevance:

- **Content**: The actual information being stored
- **Item Type**: Classification of the information (fact, instruction, preference, history, metadata)
- **Layer**: The hierarchical layer where the item is currently stored
- **Relevance Score**: A dynamic score that determines the item's importance
- **Embedding**: Optional vector representation for semantic search

### 3. Relevance Decay

The system implements a decay mechanism where information gradually becomes less relevant over time unless it is accessed:

- **Time-based Decay**: Relevance decreases as time passes since last access
- **Access Boosting**: Relevance increases when information is accessed
- **Layer Movement**: Items move between layers based on their relevance scores

### 4. Context Resurrection

When previously backgrounded information becomes relevant again, it can be "resurrected" to a higher context layer:

- **Resurrection Threshold**: When relevance exceeds this threshold, items move to a higher layer
- **Access Tracking**: The system tracks when and how often items are accessed

## Implementation Details

The system is implemented in `src/context/adaptive_context_manager.py` with the following key classes:

### ContextItem

Represents a single piece of information in the context system:

```python
@dataclass
class ContextItem:
    content: str
    item_type: ContextItemType
    source: str
    layer: ContextLayerType = ContextLayerType.PRIMARY
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_accessed: str = field(default_factory=lambda: datetime.now().isoformat())
    access_count: int = 0
    relevance_score: float = 1.0
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
```

### AdaptiveContextManager

Manages the dynamic, hierarchical context system with relevance decay:

```python
class AdaptiveContextManager:
    def __init__(
        self,
        decay_rate: float = 0.05,
        resurrection_threshold: float = 0.7,
        embedding_dimension: int = 768,
        max_primary_items: int = 20,
        max_secondary_items: int = 50
    ):
        self.items: Dict[str, ContextItem] = {}
        self.decay_rate = decay_rate
        self.resurrection_threshold = resurrection_threshold
        self.embedding_dimension = embedding_dimension
        self.max_primary_items = max_primary_items
        self.max_secondary_items = max_secondary_items
        self.last_decay_update = datetime.now()
```

## Key Functions

### Adding Context Items

```python
def add_item(
    self,
    content: str,
    item_type: ContextItemType,
    source: str,
    layer: ContextLayerType = ContextLayerType.PRIMARY,
    metadata: Dict[str, Any] = None,
    tags: Set[str] = None,
    embedding: List[float] = None
) -> str:
    """Add a new context item."""
    item = ContextItem(
        content=content,
        item_type=item_type,
        source=source,
        layer=layer,
        metadata=metadata or {},
        tags=tags or set(),
        embedding=embedding
    )
    
    self.items[item.id] = item
    
    # Ensure we don't exceed maximum items per layer
    self._balance_layers()
    
    return item.id
```

### Updating Relevance Scores

```python
def update_relevance_scores(self) -> None:
    """Update relevance scores based on recency and access patterns."""
    now = datetime.now()
    time_since_last_update = (now - self.last_decay_update).total_seconds() / 3600  # hours
    
    for item in self.items.values():
        # Calculate time factor (decay based on time since last access)
        last_accessed = datetime.fromisoformat(item.last_accessed)
        hours_since_access = (now - last_accessed).total_seconds() / 3600
        time_factor = math.exp(-self.decay_rate * hours_since_access)
        
        # Calculate access factor (boost based on access count)
        access_factor = min(1.0, 0.5 + (item.access_count / 10))
        
        # Update relevance score
        item.relevance_score = time_factor * access_factor
    
    self.last_decay_update = now
    
    # After updating scores, check if any items need to change layers
    self._update_layers()
```

### Searching Context

```python
def search_by_embedding(self, query_embedding: List[float], limit: int = 10) -> List[ContextItem]:
    """Search for context items using vector similarity."""
    if not query_embedding:
        return []
    
    results = []
    query_embedding_np = np.array(query_embedding)
    
    for item in self.items.values():
        if item.embedding:
            # Calculate cosine similarity
            item_embedding_np = np.array(item.embedding)
            similarity = np.dot(query_embedding_np, item_embedding_np) / (
                np.linalg.norm(query_embedding_np) * np.linalg.norm(item_embedding_np)
            )
            results.append((item, similarity))
            item.access()  # Record that this item was accessed
    
    # Sort by similarity and limit results
    results.sort(key=lambda x: x[1], reverse=True)
    return [item for item, _ in results[:limit]]
```

## Usage Examples

### Creating and Managing Context

```python
from context.adaptive_context_manager import AdaptiveContextManager, ContextItemType, ContextLayerType

# Initialize the context manager
context_manager = AdaptiveContextManager(
    decay_rate=0.05,
    resurrection_threshold=0.7,
    max_primary_items=20
)

# Add items to the context
fact_id = context_manager.add_item(
    content="The capital of France is Paris",
    item_type=ContextItemType.FACT,
    source="knowledge_base",
    tags={"geography", "europe", "capitals"}
)

preference_id = context_manager.add_item(
    content="User prefers concise responses",
    item_type=ContextItemType.PREFERENCE,
    source="user_profile"
)

# Retrieve items
fact = context_manager.get_item(fact_id)
preferences = context_manager.get_items_by_type(ContextItemType.PREFERENCE)

# Search for items
geography_items = context_manager.get_items_by_tags({"geography"})
paris_items = context_manager.search_by_content("Paris")

# Update relevance scores (typically called periodically)
context_manager.update_relevance_scores()
```

### Persisting Context

```python
# Save context to disk
context_manager.save_to_file("/path/to/context.json")

# Load context from disk
loaded_context = AdaptiveContextManager.load_from_file("/path/to/context.json")
```

## Benefits

1. **More Efficient Context Usage**: Prioritizes the most relevant information
2. **Better Handling of Long Conversations**: Maintains important context while allowing less relevant information to fade
3. **Improved Response Relevance**: Ensures AI responses focus on the most important information
4. **Dynamic Adaptation**: Automatically adjusts to changing conversation focus
5. **Semantic Search**: Enables finding related information based on meaning, not just keywords

## Integration with Other Systems

The Adaptive Context Management System integrates with:

1. **Persona Collaboration Framework**: Provides shared context for collaborating personas
2. **Unified Knowledge Graph**: Supplies relevant context from the knowledge graph
3. **Adaptive Learning System**: Uses feedback to improve context prioritization

This system is a core component of Orchestra AI's ability to maintain coherent, relevant conversations over extended interactions.
