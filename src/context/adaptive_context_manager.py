"""
Adaptive Context Management System for Orchestra AI

This module implements a dynamic context management system that intelligently prioritizes
information based on relevance and recency, with hierarchical context layers and decay mechanisms.
"""

from typing import Dict, List, Optional, Any, Tuple, Set
import uuid
from datetime import datetime
import math
from enum import Enum
import json
import numpy as np
from dataclasses import dataclass, field

class ContextLayerType(str, Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    BACKGROUND = "background"

class ContextItemType(str, Enum):
    FACT = "fact"
    INSTRUCTION = "instruction"
    PREFERENCE = "preference"
    HISTORY = "history"
    METADATA = "metadata"

@dataclass
class ContextItem:
    """Represents a single piece of information in the context system."""
    
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context item to dictionary representation."""
        return {
            "id": self.id,
            "content": self.content,
            "item_type": self.item_type,
            "source": self.source,
            "layer": self.layer,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
            "relevance_score": self.relevance_score,
            "embedding": self.embedding,
            "metadata": self.metadata,
            "tags": list(self.tags)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextItem':
        """Create context item from dictionary representation."""
        tags = set(data.get("tags", []))
        item = cls(
            content=data["content"],
            item_type=data["item_type"],
            source=data["source"],
            layer=data["layer"],
            id=data["id"],
            created_at=data["created_at"],
            last_accessed=data["last_accessed"],
            access_count=data["access_count"],
            relevance_score=data["relevance_score"],
            embedding=data.get("embedding"),
            metadata=data.get("metadata", {}),
            tags=tags
        )
        return item
    
    def access(self) -> None:
        """Record an access to this context item."""
        self.last_accessed = datetime.now().isoformat()
        self.access_count += 1

class AdaptiveContextManager:
    """Manages a dynamic, hierarchical context system with relevance decay."""
    
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
    
    def get_item(self, item_id: str) -> Optional[ContextItem]:
        """Get a context item by ID and record the access."""
        item = self.items.get(item_id)
        if item:
            item.access()
        return item
    
    def get_layer_items(self, layer: ContextLayerType) -> List[ContextItem]:
        """Get all items in a specific context layer."""
        return [item for item in self.items.values() if item.layer == layer]
    
    def get_items_by_type(self, item_type: ContextItemType) -> List[ContextItem]:
        """Get all items of a specific type."""
        return [item for item in self.items.values() if item.item_type == item_type]
    
    def get_items_by_tags(self, tags: Set[str], require_all: bool = False) -> List[ContextItem]:
        """Get items that match the specified tags."""
        if require_all:
            return [
                item for item in self.items.values()
                if tags.issubset(item.tags)
            ]
        else:
            return [
                item for item in self.items.values()
                if tags.intersection(item.tags)
            ]
    
    def search_by_content(self, query: str, limit: int = 10) -> List[ContextItem]:
        """Simple text search for context items."""
        # This is a basic implementation; in practice, you'd use a more sophisticated
        # search algorithm or vector similarity for embeddings
        query = query.lower()
        results = []
        
        for item in self.items.values():
            if query in item.content.lower():
                results.append(item)
                item.access()  # Record that this item was accessed
        
        # Sort by relevance score and limit results
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:limit]
    
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
    
    def _update_layers(self) -> None:
        """Move items between layers based on relevance scores."""
        # Check for items to demote from primary to secondary
        for item in self.get_layer_items(ContextLayerType.PRIMARY):
            if item.relevance_score < 0.5:
                item.layer = ContextLayerType.SECONDARY
        
        # Check for items to demote from secondary to background
        for item in self.get_layer_items(ContextLayerType.SECONDARY):
            if item.relevance_score < 0.3:
                item.layer = ContextLayerType.BACKGROUND
        
        # Check for items to resurrect from background to secondary
        for item in self.get_layer_items(ContextLayerType.BACKGROUND):
            if item.relevance_score > self.resurrection_threshold:
                item.layer = ContextLayerType.SECONDARY
        
        # Balance the layers to ensure we don't exceed maximum items
        self._balance_layers()
    
    def _balance_layers(self) -> None:
        """Ensure layers don't exceed their maximum item counts."""
        # Balance primary layer
        primary_items = self.get_layer_items(ContextLayerType.PRIMARY)
        if len(primary_items) > self.max_primary_items:
            # Sort by relevance score (ascending) to find least relevant items
            primary_items.sort(key=lambda x: x.relevance_score)
            # Demote excess items to secondary
            for item in primary_items[:len(primary_items) - self.max_primary_items]:
                item.layer = ContextLayerType.SECONDARY
        
        # Balance secondary layer
        secondary_items = self.get_layer_items(ContextLayerType.SECONDARY)
        if len(secondary_items) > self.max_secondary_items:
            # Sort by relevance score (ascending) to find least relevant items
            secondary_items.sort(key=lambda x: x.relevance_score)
            # Demote excess items to background
            for item in secondary_items[:len(secondary_items) - self.max_secondary_items]:
                item.layer = ContextLayerType.BACKGROUND
    
    def get_context_summary(self, max_items: int = None) -> Dict[str, Any]:
        """Get a summary of the current context state."""
        primary_items = self.get_layer_items(ContextLayerType.PRIMARY)
        secondary_items = self.get_layer_items(ContextLayerType.SECONDARY)
        background_items = self.get_layer_items(ContextLayerType.BACKGROUND)
        
        # Sort items by relevance score
        primary_items.sort(key=lambda x: x.relevance_score, reverse=True)
        secondary_items.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Limit items if requested
        if max_items:
            primary_items = primary_items[:max_items]
            secondary_items = secondary_items[:max_items]
            background_items = background_items[:max_items]
        
        return {
            "primary_count": len(primary_items),
            "secondary_count": len(secondary_items),
            "background_count": len(background_items),
            "primary_items": [item.to_dict() for item in primary_items],
            "secondary_items": [item.to_dict() for item in secondary_items],
            "background_items": [item.to_dict() for item in background_items],
            "last_decay_update": self.last_decay_update.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the entire context manager state to a dictionary."""
        return {
            "items": {item_id: item.to_dict() for item_id, item in self.items.items()},
            "decay_rate": self.decay_rate,
            "resurrection_threshold": self.resurrection_threshold,
            "embedding_dimension": self.embedding_dimension,
            "max_primary_items": self.max_primary_items,
            "max_secondary_items": self.max_secondary_items,
            "last_decay_update": self.last_decay_update.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AdaptiveContextManager':
        """Create a context manager from a dictionary representation."""
        manager = cls(
            decay_rate=data["decay_rate"],
            resurrection_threshold=data["resurrection_threshold"],
            embedding_dimension=data["embedding_dimension"],
            max_primary_items=data["max_primary_items"],
            max_secondary_items=data["max_secondary_items"]
        )
        
        manager.last_decay_update = datetime.fromisoformat(data["last_decay_update"])
        
        # Restore all items
        for item_id, item_data in data["items"].items():
            manager.items[item_id] = ContextItem.from_dict(item_data)
        
        return manager
    
    def save_to_file(self, filepath: str) -> None:
        """Save the context manager state to a JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'AdaptiveContextManager':
        """Load a context manager from a JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
