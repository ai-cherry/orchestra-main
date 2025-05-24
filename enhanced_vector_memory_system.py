#!/usr/bin/env python3
"""
Enhanced Vector Memory System for Orchestra AI MVP
Provides high-performance vector search, contextual memory, and data aggregation.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import logging
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from google.cloud import firestore_v1
from google.cloud import storage
import redis.asyncio as redis
import uuid

logger = logging.getLogger(__name__)

@dataclass
class ContextualMemory:
    """Enhanced memory item with rich contextual metadata."""
    id: str
    user_id: str
    content: str
    embedding: List[float]
    source: str  # 'gong', 'salesforce', 'hubspot', 'slack', 'looker', 'manual'
    source_metadata: Dict[str, Any]
    timestamp: datetime
    context_tags: List[str] = field(default_factory=list)
    relevance_score: float = 0.0
    relationship_ids: List[str] = field(default_factory=list)
    expiry: Optional[datetime] = None

@dataclass
class ConversationContext:
    """Conversation context with memory aggregation."""
    conversation_id: str
    user_id: str
    active_memories: List[ContextualMemory]
    conversation_history: List[Dict[str, Any]]
    aggregated_context: str
    last_updated: datetime
    context_vector: Optional[List[float]] = None

class EnhancedVectorMemorySystem:
    """
    Production-ready vector memory system with advanced contextualization.
    
    Features:
    - Multi-source data aggregation (Gong, Salesforce, HubSpot, Slack, Looker)
    - Hybrid vector + metadata search
    - Real-time context aggregation
    - Conversation-aware memory retrieval
    - Memory relationship mapping
    """
    
    def __init__(
        self,
        project_id: str,
        embedding_model: str = "all-MiniLM-L6-v2",
        redis_url: str = "redis://localhost:6379",
        max_context_memories: int = 20,
        context_window_days: int = 30
    ):
        self.project_id = project_id
        self.max_context_memories = max_context_memories
        self.context_window_days = context_window_days
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Initialize clients
        self.firestore_client = firestore_v1.AsyncClient()
        self.redis_client = None
        self.gcs_client = storage.Client()
        
        # Collections
        self.memories_collection = "enhanced_memories"
        self.contexts_collection = "conversation_contexts"
        self.relationships_collection = "memory_relationships"
        
        # Cache for embeddings and contexts
        self._embedding_cache: Dict[str, List[float]] = {}
        self._context_cache: Dict[str, ConversationContext] = {}

    async def initialize(self) -> None:
        """Initialize the vector memory system."""
        self.redis_client = await redis.from_url("redis://localhost:6379")
        logger.info("Enhanced Vector Memory System initialized")

    async def close(self) -> None:
        """Close connections."""
        if self.redis_client:
            await self.redis_client.close()

    async def create_embedding(self, text: str) -> List[float]:
        """Create embedding with caching."""
        cache_key = f"emb:{hash(text)}"
        
        # Check cache first
        cached = await self.redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Generate embedding
        embedding = self.embedding_model.encode([text])[0].tolist()
        
        # Cache with 1 hour expiry
        await self.redis_client.setex(cache_key, 3600, json.dumps(embedding))
        
        return embedding

    async def add_memory(
        self,
        user_id: str,
        content: str,
        source: str,
        source_metadata: Dict[str, Any],
        context_tags: Optional[List[str]] = None
    ) -> str:
        """Add a new contextual memory."""
        memory_id = str(uuid.uuid4())
        
        # Create embedding
        embedding = await self.create_embedding(content)
        
        # Create memory object
        memory = ContextualMemory(
            id=memory_id,
            user_id=user_id,
            content=content,
            embedding=embedding,
            source=source,
            source_metadata=source_metadata,
            timestamp=datetime.utcnow(),
            context_tags=context_tags or []
        )
        
        # Store in Firestore
        doc_ref = self.firestore_client.collection(self.memories_collection).document(memory_id)
        await doc_ref.set({
            "id": memory.id,
            "user_id": memory.user_id,
            "content": memory.content,
            "embedding": memory.embedding,
            "source": memory.source,
            "source_metadata": memory.source_metadata,
            "timestamp": memory.timestamp,
            "context_tags": memory.context_tags
        })
        
        # Update context cache
        await self._update_user_context(user_id, memory)
        
        logger.info(f"Added memory {memory_id} from {source} for user {user_id}")
        return memory_id

    async def semantic_search(
        self,
        user_id: str,
        query: str,
        sources: Optional[List[str]] = None,
        context_tags: Optional[List[str]] = None,
        top_k: int = 10,
        min_similarity: float = 0.3
    ) -> List[ContextualMemory]:
        """Enhanced semantic search with source and tag filtering."""
        
        # Create query embedding
        query_embedding = await self.create_embedding(query)
        
        # Build Firestore query
        query_ref = self.firestore_client.collection(self.memories_collection).where("user_id", "==", user_id)
        
        # Apply source filtering
        if sources:
            query_ref = query_ref.where("source", "in", sources)
        
        # Get all candidate memories
        docs = await query_ref.get()
        
        memories_with_scores = []
        for doc in docs:
            data = doc.to_dict()
            
            # Apply tag filtering
            if context_tags:
                if not any(tag in data.get("context_tags", []) for tag in context_tags):
                    continue
            
            # Calculate similarity
            memory_embedding = data["embedding"]
            similarity = cosine_similarity([query_embedding], [memory_embedding])[0][0]
            
            if similarity >= min_similarity:
                memory = ContextualMemory(
                    id=data["id"],
                    user_id=data["user_id"],
                    content=data["content"],
                    embedding=data["embedding"],
                    source=data["source"],
                    source_metadata=data["source_metadata"],
                    timestamp=data["timestamp"],
                    context_tags=data.get("context_tags", []),
                    relevance_score=similarity
                )
                memories_with_scores.append((memory, similarity))
        
        # Sort by similarity and return top-k
        memories_with_scores.sort(key=lambda x: x[1], reverse=True)
        return [memory for memory, _ in memories_with_scores[:top_k]]

    async def get_conversation_context(
        self,
        user_id: str,
        conversation_id: str,
        query: Optional[str] = None
    ) -> ConversationContext:
        """Get rich conversation context with aggregated memories."""
        
        # Check cache first
        cache_key = f"{user_id}:{conversation_id}"
        if cache_key in self._context_cache:
            context = self._context_cache[cache_key]
            if (datetime.utcnow() - context.last_updated).seconds < 300:  # 5 min cache
                return context
        
        # Get recent memories for context
        cutoff_date = datetime.utcnow() - timedelta(days=self.context_window_days)
        
        memories_query = (
            self.firestore_client.collection(self.memories_collection)
            .where("user_id", "==", user_id)
            .where("timestamp", ">=", cutoff_date)
            .order_by("timestamp", direction=firestore_v1.Query.DESCENDING)
            .limit(self.max_context_memories)
        )
        
        docs = await memories_query.get()
        memories = []
        
        for doc in docs:
            data = doc.to_dict()
            memory = ContextualMemory(
                id=data["id"],
                user_id=data["user_id"],
                content=data["content"],
                embedding=data["embedding"],
                source=data["source"],
                source_metadata=data["source_metadata"],
                timestamp=data["timestamp"],
                context_tags=data.get("context_tags", [])
            )
            memories.append(memory)
        
        # If query provided, re-rank by relevance
        if query and memories:
            query_embedding = await self.create_embedding(query)
            for memory in memories:
                similarity = cosine_similarity([query_embedding], [memory.embedding])[0][0]
                memory.relevance_score = similarity
            
            memories.sort(key=lambda m: m.relevance_score, reverse=True)
        
        # Aggregate context
        aggregated_context = await self._aggregate_context(memories)
        
        # Create context object
        context = ConversationContext(
            conversation_id=conversation_id,
            user_id=user_id,
            active_memories=memories,
            conversation_history=[],  # Would be populated from conversation store
            aggregated_context=aggregated_context,
            last_updated=datetime.utcnow()
        )
        
        # Cache context
        self._context_cache[cache_key] = context
        
        return context

    async def _aggregate_context(self, memories: List[ContextualMemory]) -> str:
        """Aggregate multiple memories into coherent context."""
        if not memories:
            return ""
        
        # Group by source for structured aggregation
        by_source = {}
        for memory in memories:
            if memory.source not in by_source:
                by_source[memory.source] = []
            by_source[memory.source].append(memory)
        
        context_parts = []
        
        for source, source_memories in by_source.items():
            source_context = f"\n=== {source.upper()} DATA ===\n"
            for memory in source_memories[:5]:  # Limit per source
                source_context += f"- {memory.content[:200]}...\n"
            context_parts.append(source_context)
        
        return "\n".join(context_parts)

    async def _update_user_context(self, user_id: str, new_memory: ContextualMemory) -> None:
        """Update user's context with new memory."""
        # This would update conversation contexts that include this user
        # Implementation would depend on conversation management system
        pass

    async def add_memory_relationship(
        self,
        memory_id_1: str,
        memory_id_2: str,
        relationship_type: str,
        strength: float = 1.0
    ) -> None:
        """Add relationship between memories for enhanced context."""
        relationship_id = str(uuid.uuid4())
        
        relationship_doc = {
            "id": relationship_id,
            "memory_id_1": memory_id_1,
            "memory_id_2": memory_id_2,
            "relationship_type": relationship_type,
            "strength": strength,
            "created_at": datetime.utcnow()
        }
        
        await self.firestore_client.collection(self.relationships_collection).document(relationship_id).set(relationship_doc)

    async def get_related_memories(
        self,
        memory_id: str,
        max_depth: int = 2
    ) -> List[ContextualMemory]:
        """Get related memories through relationship graph."""
        related_ids = set()
        current_level = {memory_id}
        
        for depth in range(max_depth):
            next_level = set()
            
            for mid in current_level:
                # Find relationships
                relationships = await self.firestore_client.collection(self.relationships_collection).where("memory_id_1", "==", mid).get()
                for rel_doc in relationships:
                    rel_data = rel_doc.to_dict()
                    related_id = rel_data["memory_id_2"]
                    if related_id not in related_ids:
                        related_ids.add(related_id)
                        next_level.add(related_id)
                
                # Check reverse relationships
                relationships = await self.firestore_client.collection(self.relationships_collection).where("memory_id_2", "==", mid).get()
                for rel_doc in relationships:
                    rel_data = rel_doc.to_dict()
                    related_id = rel_data["memory_id_1"]
                    if related_id not in related_ids:
                        related_ids.add(related_id)
                        next_level.add(related_id)
            
            current_level = next_level
            if not current_level:
                break
        
        # Fetch related memories
        related_memories = []
        for related_id in related_ids:
            memory_doc = await self.firestore_client.collection(self.memories_collection).document(related_id).get()
            if memory_doc.exists:
                data = memory_doc.to_dict()
                memory = ContextualMemory(
                    id=data["id"],
                    user_id=data["user_id"],
                    content=data["content"],
                    embedding=data["embedding"],
                    source=data["source"],
                    source_metadata=data["source_metadata"],
                    timestamp=data["timestamp"],
                    context_tags=data.get("context_tags", [])
                )
                related_memories.append(memory)
        
        return related_memories

    async def cleanup_expired_memories(self) -> int:
        """Clean up expired memories."""
        now = datetime.utcnow()
        
        expired_query = self.firestore_client.collection(self.memories_collection).where("expiry", "<", now)
        docs = await expired_query.get()
        
        count = 0
        batch = self.firestore_client.batch()
        
        for doc in docs:
            batch.delete(doc.reference)
            count += 1
            
            if count % 500 == 0:  # Firestore batch limit
                await batch.commit()
                batch = self.firestore_client.batch()
        
        if count % 500 != 0:
            await batch.commit()
        
        logger.info(f"Cleaned up {count} expired memories")
        return count 