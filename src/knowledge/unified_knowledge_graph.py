"""
Unified Knowledge Graph for Orchestra AI

This module implements a centralized knowledge graph that integrates information from all data sources
and user interactions, enabling more sophisticated reasoning and institutional memory.
"""

from typing import Dict, List, Optional, Any, Tuple, Set, Union
import uuid
from datetime import datetime
import json
import os
from enum import Enum
from dataclasses import dataclass, field
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

class NodeType(str, Enum):
    ENTITY = "entity"
    CONCEPT = "concept"
    FACT = "fact"
    EVENT = "event"
    USER = "user"
    PERSONA = "persona"
    DOCUMENT = "document"
    CONVERSATION = "conversation"
    CUSTOM = "custom"

class RelationType(str, Enum):
    IS_A = "is_a"
    HAS_A = "has_a"
    PART_OF = "part_of"
    RELATED_TO = "related_to"
    CREATED_BY = "created_by"
    MENTIONED_IN = "mentioned_in"
    PARTICIPATED_IN = "participated_in"
    KNOWS = "knows"
    CUSTOM = "custom"

@dataclass
class KnowledgeNode:
    """Represents a node in the knowledge graph."""
    
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "node_type": self.node_type,
            "properties": self.properties,
            "embedding": self.embedding,
            "confidence": self.confidence,
            "source": self.source,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "verified": self.verified
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeNode':
        """Create node from dictionary representation."""
        node = cls(
            id=data["id"],
            name=data["name"],
            node_type=data["node_type"],
            properties=data["properties"],
            embedding=data.get("embedding"),
            confidence=data["confidence"],
            source=data["source"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            verified=data["verified"]
        )
        return node

@dataclass
class KnowledgeRelation:
    """Represents a relation between nodes in the knowledge graph."""
    
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert relation to dictionary representation."""
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type,
            "properties": self.properties,
            "confidence": self.confidence,
            "source": self.source,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "verified": self.verified
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeRelation':
        """Create relation from dictionary representation."""
        relation = cls(
            id=data["id"],
            source_id=data["source_id"],
            target_id=data["target_id"],
            relation_type=data["relation_type"],
            properties=data["properties"],
            confidence=data["confidence"],
            source=data["source"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            verified=data["verified"]
        )
        return relation

class KnowledgeExtractor:
    """Base class for extractors that populate the knowledge graph from various sources."""
    
    def extract(self, source_data: Any) -> Tuple[List[KnowledgeNode], List[KnowledgeRelation]]:
        """Extract knowledge from source data."""
        raise NotImplementedError("Subclasses must implement extract method")

class TextKnowledgeExtractor(KnowledgeExtractor):
    """Extracts knowledge from text content."""
    
    def extract(self, text: str) -> Tuple[List[KnowledgeNode], List[KnowledgeRelation]]:
        """Extract knowledge from text."""
        # This is a placeholder implementation
        # In a real system, this would use NLP techniques to extract entities and relations
        
        nodes = []
        relations = []
        
        # Example: Extract simple entities (very basic implementation)
        words = text.split()
        for word in words:
            if len(word) > 5 and word[0].isupper():
                # Create a simple entity node for capitalized words
                node = KnowledgeNode(
                    name=word,
                    node_type=NodeType.ENTITY,
                    properties={"extracted_from": "text"},
                    confidence=0.5,
                    source="text_extractor",
                    verified=False
                )
                nodes.append(node)
        
        # In a real implementation, we would also extract relations between entities
        
        return nodes, relations

class ConversationKnowledgeExtractor(KnowledgeExtractor):
    """Extracts knowledge from conversation history."""
    
    def extract(self, conversation: Dict[str, Any]) -> Tuple[List[KnowledgeNode], List[KnowledgeRelation]]:
        """Extract knowledge from conversation."""
        # This is a placeholder implementation
        
        nodes = []
        relations = []
        
        # Create a conversation node
        conversation_node = KnowledgeNode(
            name=f"Conversation {conversation.get('id', 'unknown')}",
            node_type=NodeType.CONVERSATION,
            properties={
                "timestamp": conversation.get("timestamp", datetime.now().isoformat()),
                "topic": conversation.get("topic", "unknown")
            },
            confidence=1.0,
            source="conversation_extractor",
            verified=True
        )
        nodes.append(conversation_node)
        
        # Create nodes for participants
        for participant in conversation.get("participants", []):
            participant_node = KnowledgeNode(
                name=participant.get("name", "Unknown User"),
                node_type=NodeType.USER if participant.get("type") == "user" else NodeType.PERSONA,
                properties={
                    "user_id": participant.get("id", "unknown"),
                    "type": participant.get("type", "unknown")
                },
                confidence=1.0,
                source="conversation_extractor",
                verified=True
            )
            nodes.append(participant_node)
            
            # Create relation between participant and conversation
            relation = KnowledgeRelation(
                source_id=participant_node.id,
                target_id=conversation_node.id,
                relation_type=RelationType.PARTICIPATED_IN,
                confidence=1.0,
                source="conversation_extractor",
                verified=True
            )
            relations.append(relation)
        
        # In a real implementation, we would also extract entities and facts from messages
        
        return nodes, relations

class DocumentKnowledgeExtractor(KnowledgeExtractor):
    """Extracts knowledge from documents."""
    
    def extract(self, document: Dict[str, Any]) -> Tuple[List[KnowledgeNode], List[KnowledgeRelation]]:
        """Extract knowledge from document."""
        # This is a placeholder implementation
        
        nodes = []
        relations = []
        
        # Create a document node
        document_node = KnowledgeNode(
            name=document.get("title", "Untitled Document"),
            node_type=NodeType.DOCUMENT,
            properties={
                "document_id": document.get("id", "unknown"),
                "author": document.get("author", "unknown"),
                "created_at": document.get("created_at", datetime.now().isoformat()),
                "type": document.get("type", "unknown")
            },
            confidence=1.0,
            source="document_extractor",
            verified=True
        )
        nodes.append(document_node)
        
        # Extract knowledge from document content
        if "content" in document and isinstance(document["content"], str):
            text_extractor = TextKnowledgeExtractor()
            content_nodes, content_relations = text_extractor.extract(document["content"])
            
            nodes.extend(content_nodes)
            relations.extend(content_relations)
            
            # Create relations between extracted entities and the document
            for node in content_nodes:
                relation = KnowledgeRelation(
                    source_id=node.id,
                    target_id=document_node.id,
                    relation_type=RelationType.MENTIONED_IN,
                    confidence=node.confidence,
                    source="document_extractor",
                    verified=False
                )
                relations.append(relation)
        
        return nodes, relations

class KnowledgeVerifier:
    """Verifies knowledge before adding it to the graph."""
    
    def verify_node(self, node: KnowledgeNode) -> Tuple[bool, float]:
        """Verify a node and return verification status and confidence."""
        # This is a placeholder implementation
        # In a real system, this would use various verification techniques
        
        # For now, just trust system-generated nodes
        if node.source == "system":
            return True, 1.0
        
        # For other sources, use a simple confidence threshold
        return node.confidence > 0.7, node.confidence
    
    def verify_relation(self, relation: KnowledgeRelation) -> Tuple[bool, float]:
        """Verify a relation and return verification status and confidence."""
        # This is a placeholder implementation
        
        # For now, just trust system-generated relations
        if relation.source == "system":
            return True, 1.0
        
        # For other sources, use a simple confidence threshold
        return relation.confidence > 0.7, relation.confidence

class UnifiedKnowledgeGraph:
    """Manages a centralized knowledge graph that integrates information from all sources."""
    
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
    
    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def get_relation(self, relation_id: str) -> Optional[KnowledgeRelation]:
        """Get a relation by ID."""
        return self.relations.get(relation_id)
    
    def get_nodes_by_type(self, node_type: NodeType) -> List[KnowledgeNode]:
        """Get all nodes of a specific type."""
        return [node for node in self.nodes.values() if node.node_type == node_type]
    
    def get_relations_by_type(self, relation_type: RelationType) -> List[KnowledgeRelation]:
        """Get all relations of a specific type."""
        return [rel for rel in self.relations.values() if rel.relation_type == relation_type]
    
    def get_node_relations(self, node_id: str) -> List[KnowledgeRelation]:
        """Get all relations involving a specific node."""
        return [
            rel for rel in self.relations.values()
            if rel.source_id == node_id or rel.target_id == node_id
        ]
    
    def search_nodes(self, query: str, limit: int = 10) -> List[KnowledgeNode]:
        """Search for nodes by name or properties."""
        query = query.lower()
        results = []
        
        for node in self.nodes.values():
            # Check name
            if query in node.name.lower():
                results.append(node)
                continue
            
            # Check properties
            for key, value in node.properties.items():
                if isinstance(value, str) and query in value.lower():
                    results.append(node)
                    break
        
        # Sort by confidence and limit results
        results.sort(key=lambda x: x.confidence, reverse=True)
        return results[:limit]
    
    def search_by_embedding(self, query_embedding: List[float], limit: int = 10) -> List[Tuple[KnowledgeNode, float]]:
        """Search for nodes using vector similarity."""
        if not query_embedding:
            return []
        
        results = []
        query_embedding_np = np.array(query_embedding)
        
        for node in self.nodes.values():
            if node.embedding:
                # Calculate cosine similarity
                node_embedding_np = np.array(node.embedding)
                similarity = np.dot(query_embedding_np, node_embedding_np) / (
                    np.linalg.norm(query_embedding_np) * np.linalg.norm(node_embedding_np)
                )
                results.append((node, similarity))
        
        # Sort by similarity and limit results
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def extract_knowledge(self, data: Any, extractor_type: str) -> Tuple[List[str], List[str]]:
        """Extract knowledge from data using the specified extractor."""
        if extractor_type not in self.extractors:
            return [], []
        
        extractor = self.extractors[extractor_type]
        nodes, relations = extractor.extract(data)
        
        # Add extracted nodes and relations to the graph
        node_ids = []
        for node in nodes:
            node_id = self.add_node(
                name=node.name,
                node_type=node.node_type,
                properties=node.properties,
                embedding=node.embedding,
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
    
    def get_subgraph(self, node_ids: List[str], depth: int = 1) -> nx.DiGraph:
        """Get a subgraph centered on the specified nodes with given depth."""
        if not node_ids:
            return nx.DiGraph()
        
        # Start with the specified nodes
        nodes_to_include = set(node_ids)
        
        # Expand to neighbors up to the specified depth
        current_nodes = set(node_ids)
        for _ in range(depth):
            next_nodes = set()
            for node_id in current_nodes:
                # Add successors (outgoing edges)
                next_nodes.update(self.graph.successors(node_id))
                # Add predecessors (incoming edges)
                next_nodes.update(self.graph.predecessors(node_id))
            
            # Add new nodes to the set of nodes to include
            nodes_to_include.update(next_nodes)
            # Update current nodes for next iteration
            current_nodes = next_nodes
        
        # Create subgraph
        return self.graph.subgraph(nodes_to_include).copy()
    
    def visualize_subgraph(self, subgraph: nx.DiGraph, output_file: str = None) -> None:
        """Visualize a subgraph."""
        plt.figure(figsize=(12, 8))
        
        # Create position layout
        pos = nx.spring_layout(subgraph)
        
        # Draw nodes
        node_colors = []
        for node in subgraph.nodes():
            node_type = subgraph.nodes[node].get("node_type", NodeType.ENTITY)
            if node_type == NodeType.ENTITY:
                node_colors.append("skyblue")
            elif node_type == NodeType.CONCEPT:
                node_colors.append("lightgreen")
            elif node_type == NodeType.FACT:
                node_colors.append("yellow")
            elif node_type == NodeType.USER:
                node_colors.append("orange")
            elif node_type == NodeType.PERSONA:
                node_colors.append("purple")
            else:
                node_colors.append("gray")
        
        nx.draw_networkx_nodes(subgraph, pos, node_color=node_colors, alpha=0.8)
        
        # Draw edges
        edge_colors = []
        for _, _, edge_data in subgraph.edges(data=True):
            relation_type = edge_data.get("relation_type", RelationType.RELATED_TO)
            if relation_type == RelationType.IS_A:
                edge_colors.append("blue")
            elif relation_type == RelationType.HAS_A:
                edge_colors.append("green")
            elif relation_type == RelationType.PART_OF:
                edge_colors.append("red")
            else:
                edge_colors.append("gray")
        
        nx.draw_networkx_edges(subgraph, pos, edge_color=edge_colors, alpha=0.5)
        
        # Draw labels
        labels = {node: subgraph.nodes[node].get("name", node) for node in subgraph.nodes()}
        nx.draw_networkx_labels(subgraph, pos, labels=labels, font_size=8)
        
        plt.title("Knowledge Graph Visualization")
        plt.axis("off")
        
        if output_file:
            plt.savefig(output_file, format="png", dpi=300, bbox_inches="tight")
        else:
            plt.show()
    
    def find_path(self, source_id: str, target_id: str) -> List[Tuple[str, str, RelationType]]:
        """Find a path between two nodes."""
        if source_id not in self.nodes or target_id not in self.nodes:
            return []
        
        try:
            # Find shortest path
            path_nodes = nx.shortest_path(self.graph, source=source_id, target=target_id)
            
            # Convert to list of (node, node, relation) tuples
            path = []
            for i in range(len(path_nodes) - 1):
                source = path_nodes[i]
                target = path_nodes[i + 1]
                edge_data = self.graph.get_edge_data(source, target)
                relation_type = edge_data.get("relation_type", RelationType.RELATED_TO)
                path.append((source, target, relation_type))
            
            return path
        except nx.NetworkXNoPath:
            return []
    
    def save(self) -> str:
        """Save the knowledge graph to disk."""
        # Save nodes
        nodes_data = {node_id: node.to_dict() for node_id, node in self.nodes.items()}
        nodes_file = os.path.join(self.storage_dir, "nodes.json")
        with open(nodes_file, 'w') as f:
            json.dump(nodes_data, f, indent=2)
        
        # Save relations
        relations_data = {rel_id: rel.to_dict() for rel_id, rel in self.relations.items()}
        relations_file = os.path.join(self.storage_dir, "relations.json")
        with open(relations_file, 'w') as f:
            json.dump(relations_data, f, indent=2)
        
        return self.storage_dir
    
    def load(self) -> bool:
        """Load the knowledge graph from disk."""
        try:
            # Load nodes
            nodes_file = os.path.join(self.storage_dir, "nodes.json")
            if os.path.exists(nodes_file):
                with open(nodes_file, 'r') as f:
                    nodes_data = json.load(f)
                
                self.nodes = {node_id: KnowledgeNode.from_dict(node_data) for node_id, node_data in nodes_data.items()}
            
            # Load relations
            relations_file = os.path.join(self.storage_dir, "relations.json")
            if os.path.exists(relations_file):
                with open(relations_file, 'r') as f:
                    relations_data = json.load(f)
                
                self.relations = {rel_id: KnowledgeRelation.from_dict(rel_data) for rel_id, rel_data in relations_data.items()}
            
            # Rebuild graph
            self.graph = nx.DiGraph()
            
            # Add nodes to graph
            for node_id, node in self.nodes.items():
                self.graph.add_node(
                    node_id,
                    name=node.name,
                    node_type=node.node_type,
                    properties=node.properties,
                    confidence=node.confidence
                )
            
            # Add edges to graph
            for rel_id, rel in self.relations.items():
                self.graph.add_edge(
                    rel.source_id,
                    rel.target_id,
                    id=rel_id,
                    relation_type=rel.relation_type,
                    properties=rel.properties,
                    confidence=rel.confidence
                )
            
            return True
        except Exception as e:
            print(f"Error loading knowledge graph: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph."""
        node_types = {}
        for node in self.nodes.values():
            if node.node_type not in node_types:
                node_types[node.node_type] = 0
            node_types[node.node_type] += 1
        
        relation_types = {}
        for rel in self.relations.values():
            if rel.relation_type not in relation_types:
                relation_types[rel.relation_type] = 0
            relation_types[rel.relation_type] += 1
        
        return {
            "total_nodes": len(self.nodes),
            "total_relations": len(self.relations),
            "node_types": node_types,
            "relation_types": relation_types,
            "verified_nodes": sum(1 for node in self.nodes.values() if node.verified),
            "verified_relations": sum(1 for rel in self.relations.values() if rel.verified),
            "average_node_confidence": sum(node.confidence for node in self.nodes.values()) / len(self.nodes) if self.nodes else 0,
            "average_relation_confidence": sum(rel.confidence for rel in self.relations.values()) / len(self.relations) if self.relations else 0
        }
