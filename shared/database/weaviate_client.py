"""
Weaviate client adapter for vector database operations.

This module provides a mock implementation of the Weaviate client that can be
replaced with actual Weaviate integration when needed. It maintains the same
interface to ensure compatibility with unified_db_v2.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class WeaviateClient:
    """
    Mock Weaviate client for vector database operations.
    
    This implementation provides in-memory storage for development and testing.
    In production, this should be replaced with actual Weaviate client.
    """
    
    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None, **kwargs):
        """
        Initialize Weaviate client.
        
        Args:
            url: Weaviate instance URL
            api_key: API key for authentication
            **kwargs: Additional configuration options
        """
        self.url = url or "http://localhost:8080"
        self.api_key = api_key
        self.config = kwargs
        
        # Mock storage for development
        self._memories = {}
        self._conversations = {}
        self._documents = {}
        self._knowledge = {}
        
        logger.info(f"Initialized WeaviateClient (mock mode) for {self.url}")
    
    def health_check(self) -> bool:
        """
        Check if Weaviate is healthy and accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        # In mock mode, always return True
        # In production, this would check actual Weaviate health endpoint
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get Weaviate statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'objects': {
                'memories': len(self._memories),
                'conversations': len(self._conversations),
                'documents': len(self._documents),
                'knowledge': len(self._knowledge)
            },
            'status': 'healthy',
            'version': 'mock-1.0'
        }
    
    # Memory operations
    
    def store_memory(
        self,
        agent_id: str,
        content: str,
        memory_type: str = "general",
        context: Optional[str] = None,
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a memory in Weaviate.
        
        Args:
            agent_id: Agent ID
            content: Memory content
            memory_type: Type of memory
            context: Optional context
            importance: Importance score (0-1)
            metadata: Additional metadata
            
        Returns:
            Memory ID
        """
        memory_id = str(uuid.uuid4())
        self._memories[memory_id] = {
            'id': memory_id,
            'agent_id': agent_id,
            'content': content,
            'memory_type': memory_type,
            'context': context,
            'importance': importance,
            'metadata': metadata or {},
            'created_at': datetime.utcnow().isoformat(),
            'vector': self._mock_vectorize(content)  # Mock vector
        }
        logger.debug(f"Stored memory {memory_id} for agent {agent_id}")
        return memory_id
    
    def get_recent_memories(self, agent_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent memories for an agent.
        
        Args:
            agent_id: Agent ID
            limit: Maximum number of memories
            
        Returns:
            List of memories
        """
        agent_memories = [
            m for m in self._memories.values() 
            if m['agent_id'] == agent_id
        ]
        # Sort by creation time (newest first)
        agent_memories.sort(key=lambda x: x['created_at'], reverse=True)
        return agent_memories[:limit]
    
    def search_memories(
        self,
        agent_id: str,
        query: str,
        limit: int = 10,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search memories using semantic search.
        
        Args:
            agent_id: Agent ID
            query: Search query
            limit: Maximum results
            memory_type: Optional filter by type
            
        Returns:
            List of matching memories
        """
        # Mock semantic search - in production, use actual vector search
        agent_memories = [
            m for m in self._memories.values()
            if m['agent_id'] == agent_id
        ]
        
        if memory_type:
            agent_memories = [m for m in agent_memories if m['memory_type'] == memory_type]
        
        # Simple text matching for mock
        query_lower = query.lower()
        scored_memories = []
        for memory in agent_memories:
            score = self._calculate_relevance(query_lower, memory['content'].lower())
            if score > 0:
                scored_memories.append((score, memory))
        
        # Sort by score and return top results
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        return [m[1] for m in scored_memories[:limit]]
    
    # Conversation operations
    
    def store_conversation(
        self,
        session_id: str,
        agent_id: str,
        user_id: str,
        message: str,
        role: str = "user",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a conversation message.
        
        Args:
            session_id: Session ID
            agent_id: Agent ID
            user_id: User ID
            message: Message content
            role: Message role (user/assistant)
            metadata: Additional metadata
            
        Returns:
            Message ID
        """
        message_id = str(uuid.uuid4())
        self._conversations[message_id] = {
            'id': message_id,
            'session_id': session_id,
            'agent_id': agent_id,
            'user_id': user_id,
            'message': message,
            'role': role,
            'metadata': metadata or {},
            'created_at': datetime.utcnow().isoformat(),
            'vector': self._mock_vectorize(message)
        }
        logger.debug(f"Stored conversation message {message_id}")
        return message_id
    
    def get_conversation_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session ID
            limit: Maximum messages
            
        Returns:
            List of messages
        """
        messages = [
            m for m in self._conversations.values()
            if m['session_id'] == session_id
        ]
        # Sort by creation time
        messages.sort(key=lambda x: x['created_at'])
        return messages[-limit:] if len(messages) > limit else messages
    
    def search_conversations(
        self,
        query: str,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search conversations.
        
        Args:
            query: Search query
            agent_id: Optional filter by agent
            session_id: Optional filter by session
            limit: Maximum results
            
        Returns:
            List of matching messages
        """
        conversations = list(self._conversations.values())
        
        if agent_id:
            conversations = [c for c in conversations if c['agent_id'] == agent_id]
        if session_id:
            conversations = [c for c in conversations if c['session_id'] == session_id]
        
        # Mock search
        query_lower = query.lower()
        scored_conversations = []
        for conv in conversations:
            score = self._calculate_relevance(query_lower, conv['message'].lower())
            if score > 0:
                scored_conversations.append((score, conv))
        
        scored_conversations.sort(key=lambda x: x[0], reverse=True)
        return [c[1] for c in scored_conversations[:limit]]
    
    # Document operations
    
    def store_document(
        self,
        title: str,
        content: str,
        source: str,
        doc_type: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a document.
        
        Args:
            title: Document title
            content: Document content
            source: Document source
            doc_type: Document type
            metadata: Additional metadata
            
        Returns:
            Document ID
        """
        doc_id = str(uuid.uuid4())
        self._documents[doc_id] = {
            'id': doc_id,
            'title': title,
            'content': content,
            'source': source,
            'doc_type': doc_type,
            'metadata': metadata or {},
            'created_at': datetime.utcnow().isoformat(),
            'vector': self._mock_vectorize(content)
        }
        logger.debug(f"Stored document {doc_id}")
        return doc_id
    
    def search_documents(
        self,
        query: str,
        source: Optional[str] = None,
        doc_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search documents.
        
        Args:
            query: Search query
            source: Optional filter by source
            doc_type: Optional filter by type
            limit: Maximum results
            
        Returns:
            List of matching documents
        """
        documents = list(self._documents.values())
        
        if source:
            documents = [d for d in documents if d['source'] == source]
        if doc_type:
            documents = [d for d in documents if d['doc_type'] == doc_type]
        
        # Return all if empty query (for workflow documents)
        if not query:
            return documents[:limit]
        
        # Mock search
        query_lower = query.lower()
        scored_documents = []
        for doc in documents:
            score = self._calculate_relevance(query_lower, doc['content'].lower())
            if score > 0:
                scored_documents.append((score, doc))
        
        scored_documents.sort(key=lambda x: x[0], reverse=True)
        return [d[1] for d in scored_documents[:limit]]
    
    # Knowledge operations
    
    def store_knowledge(
        self,
        title: str,
        content: str,
        source: str,
        category: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store knowledge item.
        
        Args:
            title: Knowledge title
            content: Knowledge content
            source: Knowledge source
            category: Knowledge category
            tags: Optional tags
            metadata: Additional metadata
            
        Returns:
            Knowledge ID
        """
        knowledge_id = str(uuid.uuid4())
        self._knowledge[knowledge_id] = {
            'id': knowledge_id,
            'title': title,
            'content': content,
            'source': source,
            'category': category,
            'tags': tags or [],
            'metadata': metadata or {},
            'created_at': datetime.utcnow().isoformat(),
            'vector': self._mock_vectorize(content)
        }
        logger.debug(f"Stored knowledge {knowledge_id}")
        return knowledge_id
    
    def search_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge base.
        
        Args:
            query: Search query
            category: Optional filter by category
            tags: Optional filter by tags
            limit: Maximum results
            
        Returns:
            List of matching knowledge items
        """
        knowledge_items = list(self._knowledge.values())
        
        if category:
            knowledge_items = [k for k in knowledge_items if k['category'] == category]
        if tags:
            knowledge_items = [
                k for k in knowledge_items 
                if any(tag in k['tags'] for tag in tags)
            ]
        
        # Mock search
        query_lower = query.lower()
        scored_knowledge = []
        for item in knowledge_items:
            score = self._calculate_relevance(
                query_lower, 
                f"{item['title']} {item['content']}".lower()
            )
            if score > 0:
                scored_knowledge.append((score, item))
        
        scored_knowledge.sort(key=lambda x: x[0], reverse=True)
        return [k[1] for k in scored_knowledge[:limit]]
    
    # Helper methods
    
    def _mock_vectorize(self, text: str) -> List[float]:
        """
        Create a mock vector representation.
        
        In production, this would use actual embedding model.
        """
        # Simple mock: use hash to generate consistent "vectors"
        hash_val = hash(text)
        return [(hash_val >> i) & 0xFF for i in range(0, 32, 8)]
    
    def _calculate_relevance(self, query: str, content: str) -> float:
        """
        Calculate simple relevance score for mock search.
        
        In production, this would use vector similarity.
        """
        # Count matching words
        query_words = set(query.split())
        content_words = set(content.split())
        
        if not query_words:
            return 0.0
        
        matches = len(query_words.intersection(content_words))
        return matches / len(query_words)