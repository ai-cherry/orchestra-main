# Unified Knowledge Graph

## Overview

The Unified Knowledge Graph is a centralized knowledge management system that integrates information from all data sources and user interactions. It enables more sophisticated reasoning, institutional memory, and knowledge verification across the Orchestra AI platform.

## Key Components

### 1. Knowledge Nodes

Nodes represent entities, concepts, facts, events, and other information units in the knowledge graph:

- **Entity Nodes**: Represent real-world objects, people, organizations, etc.
- **Concept Nodes**: Represent abstract ideas or categories
- **Fact Nodes**: Represent verified pieces of information
- **Event Nodes**: Represent occurrences with temporal properties
- **User/Persona Nodes**: Represent users and AI personas in the system
- **Document Nodes**: Represent source documents and their metadata

### 2. Knowledge Relations

Relations connect nodes to each other with specific relationship types:

- **IS_A**: Taxonomic relationships (e.g., "Paris is a city")
- **HAS_A**: Possession or component relationships
- **PART_OF**: Membership or inclusion relationships
- **RELATED_TO**: General associative relationships
- **CREATED_BY**: Attribution relationships
- **MENTIONED_IN**: Reference relationships
- **PARTICIPATED_IN**: Involvement relationships
- **KNOWS**: Knowledge or acquaintance relationships
- **CUSTOM**: User-defined relationship types

### 3. Knowledge Extractors

Specialized components that populate the knowledge graph from various sources:

- **TextKnowledgeExtractor**: Extracts knowledge from text content
- **ConversationKnowledgeExtractor**: Extracts knowledge from conversation history
- **DocumentKnowledgeExtractor**: Extracts knowledge from documents

### 4. Knowledge Verification

A system to ensure the accuracy and reliability of information in the graph:

- **Confidence Scores**: Measure of certainty about information
- **Source Tracking**: Record of where information originated
- **Verification Status**: Whether information has been verified

## Implementation Details

The system is implemented in `src/knowledge/unified_knowledge_graph.py` with the following key classes:

### KnowledgeNode

Represents a node in the knowledge graph:

```python
@dataclass
class KnowledgeNode:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    node_type: NodeType = NodeType.ENTITY
    properties: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    confidence: float = 1.0
    source: str = "system"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    verified: bool = False
```

### KnowledgeRelation

Represents a relation between nodes in the knowledge graph:

```python
@dataclass
class KnowledgeRelation:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    target_id: str = ""
    relation_type: RelationType = RelationType.RELATED_TO
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    source: str = "system"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    verified: bool = False
```

### UnifiedKnowledgeGraph

Manages the centralized knowledge graph:

```python
class UnifiedKnowledgeGraph:
    def __init__(self, storage_dir: str = "./knowledge_graph"):
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.relations: Dict[str, KnowledgeRelation] = {}
        self.graph = nx.DiGraph()
        self.storage_dir = storage_dir
        self.verifier = KnowledgeVerifier()
        self.extractors: Dict[str, KnowledgeExtractor] = {
            "text": TextKnowledgeExtractor(),
            "conversation": ConversationKnowledgeExtractor(),
            "document": DocumentKnowledgeExtractor()
        }
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
```

## Key Functions

### Adding Nodes and Relations

```python
def add_node(
    self,
    name: str,
    node_type: NodeType,
    properties: Dict[str, Any] = None,
    embedding: List[float] = None,
    confidence: float = 1.0,
    source: str = "system",
    verify: bool = True
) -> str:
    """Add a new node to the knowledge graph."""
    node = KnowledgeNode(
        name=name,
        node_type=node_type,
        properties=properties or {},
        embedding=embedding,
        confidence=confidence,
        source=source,
        verified=False
    )
    
    # Verify node if requested
    if verify:
        verified, confidence = self.verifier.verify_node(node)
        node.verified = verified
        node.confidence = confidence
        
        # Skip adding node if verification fails
        if not verified:
            return ""
    
    # Add node to storage
    self.nodes[node.id] = node
    
    # Add node to graph
    self.graph.add_node(
        node.id,
        name=node.name,
        node_type=node.node_type,
        properties=node.properties,
        confidence=node.confidence
    )
    
    return node.id

def add_relation(
    self,
    source_id: str,
    target_id: str,
    relation_type: RelationType,
    properties: Dict[str, Any] = None,
    confidence: float = 1.0,
    source: str = "system",
    verify: bool = True
) -> str:
    """Add a new relation to the knowledge graph."""
    # Check if source and target nodes exist
    if source_id not in self.nodes or target_id not in self.nodes:
        return ""
    
    relation = KnowledgeRelation(
        source_id=source_id,
        target_id=target_id,
        relation_type=relation_type,
        properties=properties or {},
        confidence=confidence,
        source=source,
        verified=False
    )
    
    # Verify relation if requested
    if verify:
        verified, confidence = self.verifier.verify_relation(relation)
        relation.verified = verified
        relation.confidence = confidence
        
        # Skip adding relation if verification fails
        if not verified:
            return ""
    
    # Add relation to storage
    self.relations[relation.id] = relation
    
    # Add edge to graph
    self.graph.add_edge(
        source_id,
        target_id,
        id=relation.id,
        relation_type=relation.relation_type,
        properties=relation.properties,
        confidence=relation.confidence
    )
    
    return relation.id
```

### Knowledge Extraction

```python
def extract_from_text(self, text: str) -> Tuple[List[str], List[str]]:
    """Extract knowledge from text and add to the graph."""
    extractor = self.extractors["text"]
    nodes, relations = extractor.extract(text)
    
    # Add extracted nodes and relations to the graph
    node_ids = []
    for node in nodes:
        node_id = self.add_node(
            name=node.name,
            node_type=node.node_type,
            properties=node.properties,
            confidence=node.confidence,
            source=node.source,
            verify=True
        )
        if node_id:
            node_ids.append(node_id)
    
    relation_ids = []
    for relation in relations:
        relation_id = self.add_relation(
            source_id=relation.source_id,
            target_id=relation.target_id,
            relation_type=relation.relation_type,
            properties=relation.properties,
            confidence=relation.confidence,
            source=relation.source,
            verify=True
        )
        if relation_id:
            relation_ids.append(relation_id)
    
    return node_ids, relation_ids
```

### Graph Querying

```python
def find_path(self, start_node_id: str, end_node_id: str, max_depth: int = 3) -> List[List[str]]:
    """Find paths between two nodes in the graph."""
    if start_node_id not in self.nodes or end_node_id not in self.nodes:
        return []
    
    try:
        # Find all simple paths up to max_depth
        paths = list(nx.all_simple_paths(
            self.graph, 
            source=start_node_id, 
            target=end_node_id, 
            cutoff=max_depth
        ))
        return paths
    except nx.NetworkXNoPath:
        return []

def get_subgraph(self, node_ids: List[str], include_neighbors: bool = False) -> 'UnifiedKnowledgeGraph':
    """Extract a subgraph containing the specified nodes."""
    if not node_ids:
        return None
    
    # Create a new graph instance
    subgraph = UnifiedKnowledgeGraph(storage_dir=self.storage_dir)
    
    # Add specified nodes
    nodes_to_include = set(node_ids)
    
    # Add neighbors if requested
    if include_neighbors:
        for node_id in node_ids:
            if node_id in self.nodes:
                neighbors = list(self.graph.neighbors(node_id))
                nodes_to_include.update(neighbors)
    
    # Copy nodes and their properties
    for node_id in nodes_to_include:
        if node_id in self.nodes:
            node = self.nodes[node_id]
            subgraph.nodes[node_id] = KnowledgeNode(
                id=node.id,
                name=node.name,
                node_type=node.node_type,
                properties=node.properties.copy(),
                embedding=node.embedding.copy() if node.embedding else None,
                confidence=node.confidence,
                source=node.source,
                created_at=node.created_at,
                updated_at=node.updated_at,
                verified=node.verified
            )
            
            # Add node to NetworkX graph
            subgraph.graph.add_node(
                node_id,
                name=node.name,
                node_type=node.node_type,
                properties=node.properties,
                confidence=node.confidence
            )
    
    # Copy relations between included nodes
    for relation_id, relation in self.relations.items():
        if relation.source_id in nodes_to_include and relation.target_id in nodes_to_include:
            subgraph.relations[relation_id] = KnowledgeRelation(
                id=relation.id,
                source_id=relation.source_id,
                target_id=relation.target_id,
                relation_type=relation.relation_type,
                properties=relation.properties.copy(),
                confidence=relation.confidence,
                source=relation.source,
                created_at=relation.created_at,
                updated_at=relation.updated_at,
                verified=relation.verified
            )
            
            # Add edge to NetworkX graph
            subgraph.graph.add_edge(
                relation.source_id,
                relation.target_id,
                id=relation.id,
                relation_type=relation.relation_type,
                properties=relation.properties,
                confidence=relation.confidence
            )
    
    return subgraph
```

## Usage Examples

### Building a Knowledge Graph

```python
from knowledge.unified_knowledge_graph import (
    UnifiedKnowledgeGraph, 
    NodeType, 
    RelationType
)

# Initialize the knowledge graph
kg = UnifiedKnowledgeGraph(storage_dir="./data/knowledge_graph")

# Add nodes
paris_id = kg.add_node(
    name="Paris",
    node_type=NodeType.ENTITY,
    properties={"population": 2161000, "country": "France"}
)

france_id = kg.add_node(
    name="France",
    node_type=NodeType.ENTITY,
    properties={"continent": "Europe", "capital": "Paris"}
)

city_id = kg.add_node(
    name="City",
    node_type=NodeType.CONCEPT
)

# Add relations
kg.add_relation(
    source_id=paris_id,
    target_id=france_id,
    relation_type=RelationType.PART_OF
)

kg.add_relation(
    source_id=paris_id,
    target_id=city_id,
    relation_type=RelationType.IS_A
)
```

### Extracting Knowledge from Text

```python
# Extract knowledge from text
text = """
Paris is the capital of France. It is known for the Eiffel Tower, 
which was completed in 1889. The city hosts many museums including the Louvre.
"""

node_ids, relation_ids = kg.extract_from_text(text)

# Get the extracted nodes
for node_id in node_ids:
    node = kg.get_node(node_id)
    print(f"Extracted: {node.name} ({node.node_type})")
```

### Querying the Knowledge Graph

```python
# Find all entities related to Paris
paris_relations = kg.get_node_relations(paris_id)
for relation in paris_relations:
    source = kg.get_node(relation.source_id)
    target = kg.get_node(relation.target_id)
    print(f"{source.name} {relation.relation_type} {target.name}")

# Search for nodes by name
museums = kg.search_nodes("museum")
for museum in museums:
    print(f"Found: {museum.name}")

# Find paths between nodes
paths = kg.find_path(paris_id, city_id)
for path in paths:
    path_names = [kg.get_node(node_id).name for node_id in path]
    print(" -> ".join(path_names))
```

### Visualizing the Knowledge Graph

```python
# Visualize a subgraph
kg.visualize_subgraph(
    node_ids=[paris_id, france_id, city_id],
    include_neighbors=True,
    output_file="paris_subgraph.png"
)
```

## Benefits

1. **Creates Institutional Memory**: Maintains knowledge across conversations and interactions
2. **Improves Response Accuracy**: Provides verified information for AI responses
3. **Enables Sophisticated Reasoning**: Supports inference across connected knowledge
4. **Reduces Redundancy**: Centralizes knowledge from multiple sources
5. **Supports Verification**: Tracks confidence and verification status of information

## Integration with Other Systems

The Unified Knowledge Graph integrates with:

1. **Persona Collaboration Framework**: Provides knowledge for persona responses
2. **Adaptive Context Management**: Supplies relevant knowledge based on context
3. **File Ingestion System**: Receives knowledge extracted from documents
4. **Search Engine**: Enhances search with semantic knowledge

This system forms the backbone of Orchestra AI's knowledge management capabilities, enabling more intelligent and informed interactions.
