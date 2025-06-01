"""
Weaviate client for Orchestra AI.

Provides vector storage, semantic search, and knowledge management
operations for the Orchestra system.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from uuid import UUID

import weaviate
from weaviate.client import Client
from weaviate.auth import AuthApiKey
from weaviate.classes.query import Filter
from weaviate.util import generate_uuid5

logger = logging.getLogger(__name__)


class WeaviateClient:
    """Weaviate client for vector operations and semantic search."""
    
    # Collection names
    AGENT_MEMORY = "AgentMemory"
    KNOWLEDGE = "Knowledge"
    CONVERSATION = "Conversation"
    DOCUMENT = "Document"
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        grpc_port: Optional[int] = None,
        api_key: Optional[str] = None,
        use_grpc: bool = False
    ):
        """Initialize Weaviate client."""
        self.host = host or os.getenv("WEAVIATE_HOST", "localhost")
        self.port = port or int(os.getenv("WEAVIATE_PORT", "8080"))
        self.grpc_port = grpc_port or int(os.getenv("WEAVIATE_GRPC_PORT", "50051"))
        self.api_key = api_key or os.getenv("WEAVIATE_API_KEY", "")
        self.use_grpc = use_grpc
        
        self.client = self._create_client()
        self._ensure_schema()
    
    def _create_client(self) -> Client:
        """Create Weaviate client."""
        try:
            if self.api_key:
                auth_config = AuthApiKey(api_key=self.api_key)
                return weaviate.Client(
                    url=f"http://{self.host}:{self.port}",
                    auth_client_secret=auth_config,
                    additional_headers={
                        "X-Weaviate-Grpc-Host": f"{self.host}:{self.grpc_port}"
                    } if self.use_grpc else None
                )
            else:
                return weaviate.Client(
                    url=f"http://{self.host}:{self.port}",
                    additional_headers={
                        "X-Weaviate-Grpc-Host": f"{self.host}:{self.grpc_port}"
                    } if self.use_grpc else None
                )
        except Exception as e:
            logger.error(f"Failed to create Weaviate client: {e}")
            raise
    
    def _ensure_schema(self) -> None:
        """Ensure required collections exist."""
        collections = [
            {
                "class": self.AGENT_MEMORY,
                "description": "Agent memory and context storage",
                "properties": [
                    {"name": "agent_id", "dataType": ["text"], "description": "ID of the agent"},
                    {"name": "content", "dataType": ["text"], "description": "Memory content"},
                    {"name": "context", "dataType": ["text"], "description": "Additional context"},
                    {"name": "memory_type", "dataType": ["text"], "description": "Type of memory"},
                    {"name": "importance", "dataType": ["number"], "description": "Importance score"},
                    {"name": "timestamp", "dataType": ["date"], "description": "Creation timestamp"},
                    {"name": "metadata", "dataType": ["object"], "description": "Additional metadata"}
                ],
                "vectorizer": "text2vec-openai"
            },
            {
                "class": self.KNOWLEDGE,
                "description": "Knowledge base storage",
                "properties": [
                    {"name": "title", "dataType": ["text"], "description": "Knowledge title"},
                    {"name": "content", "dataType": ["text"], "description": "Knowledge content"},
                    {"name": "source", "dataType": ["text"], "description": "Source of knowledge"},
                    {"name": "category", "dataType": ["text"], "description": "Knowledge category"},
                    {"name": "tags", "dataType": ["text[]"], "description": "Tags for categorization"},
                    {"name": "created_at", "dataType": ["date"], "description": "Creation timestamp"},
                    {"name": "metadata", "dataType": ["object"], "description": "Additional metadata"}
                ],
                "vectorizer": "text2vec-openai"
            },
            {
                "class": self.CONVERSATION,
                "description": "Conversation history storage",
                "properties": [
                    {"name": "session_id", "dataType": ["text"], "description": "Session identifier"},
                    {"name": "agent_id", "dataType": ["text"], "description": "Agent identifier"},
                    {"name": "user_id", "dataType": ["text"], "description": "User identifier"},
                    {"name": "message", "dataType": ["text"], "description": "Message content"},
                    {"name": "role", "dataType": ["text"], "description": "Message role (user/assistant)"},
                    {"name": "timestamp", "dataType": ["date"], "description": "Message timestamp"},
                    {"name": "metadata", "dataType": ["object"], "description": "Additional metadata"}
                ],
                "vectorizer": "text2vec-openai"
            },
            {
                "class": self.DOCUMENT,
                "description": "Document storage for RAG",
                "properties": [
                    {"name": "title", "dataType": ["text"], "description": "Document title"},
                    {"name": "content", "dataType": ["text"], "description": "Document content"},
                    {"name": "source", "dataType": ["text"], "description": "Document source"},
                    {"name": "doc_type", "dataType": ["text"], "description": "Document type"},
                    {"name": "chunk_index", "dataType": ["int"], "description": "Chunk index if split"},
                    {"name": "created_at", "dataType": ["date"], "description": "Creation timestamp"},
                    {"name": "metadata", "dataType": ["object"], "description": "Additional metadata"}
                ],
                "vectorizer": "text2vec-openai"
            }
        ]
        
        for collection in collections:
            if not self.client.schema.exists(collection["class"]):
                self.client.schema.create_class(collection)
                logger.info(f"Created Weaviate collection: {collection['class']}")
    
    # Agent Memory operations
    def store_memory(
        self,
        agent_id: str,
        content: str,
        memory_type: str = "general",
        context: Optional[str] = None,
        importance: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store agent memory."""
        data = {
            "agent_id": agent_id,
            "content": content,
            "memory_type": memory_type,
            "context": context or "",
            "importance": importance,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        result = self.client.data_object.create(
            data_object=data,
            class_name=self.AGENT_MEMORY,
            uuid=generate_uuid5(f"{agent_id}:{content}:{datetime.utcnow().isoformat()}")
        )
        
        return result
    
    def search_memories(
        self,
        agent_id: str,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
        min_certainty: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search agent memories using semantic search."""
        where_filter = {"path": ["agent_id"], "operator": "Equal", "valueText": agent_id}
        
        if memory_type:
            where_filter = {
                "operator": "And",
                "operands": [
                    where_filter,
                    {"path": ["memory_type"], "operator": "Equal", "valueText": memory_type}
                ]
            }
        
        result = (
            self.client.query
            .get(self.AGENT_MEMORY, ["agent_id", "content", "context", "memory_type", "importance", "timestamp", "metadata"])
            .with_near_text({"concepts": [query], "certainty": min_certainty})
            .with_where(where_filter)
            .with_limit(limit)
            .with_additional(["id", "certainty"])
            .do()
        )
        
        return result.get("data", {}).get("Get", {}).get(self.AGENT_MEMORY, [])
    
    def get_recent_memories(
        self,
        agent_id: str,
        limit: int = 20,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent memories for an agent."""
        where_filter = {"path": ["agent_id"], "operator": "Equal", "valueText": agent_id}
        
        if memory_type:
            where_filter = {
                "operator": "And",
                "operands": [
                    where_filter,
                    {"path": ["memory_type"], "operator": "Equal", "valueText": memory_type}
                ]
            }
        
        result = (
            self.client.query
            .get(self.AGENT_MEMORY, ["agent_id", "content", "context", "memory_type", "importance", "timestamp", "metadata"])
            .with_where(where_filter)
            .with_limit(limit)
            .with_additional(["id"])
            .do()
        )
        
        memories = result.get("data", {}).get("Get", {}).get(self.AGENT_MEMORY, [])
        # Sort by timestamp
        return sorted(memories, key=lambda x: x.get("timestamp", ""), reverse=True)
    
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
        """Store knowledge in the knowledge base."""
        data = {
            "title": title,
            "content": content,
            "source": source,
            "category": category,
            "tags": tags or [],
            "created_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        result = self.client.data_object.create(
            data_object=data,
            class_name=self.KNOWLEDGE,
            uuid=generate_uuid5(f"{title}:{source}:{datetime.utcnow().isoformat()}")
        )
        
        return result
    
    def search_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
        min_certainty: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search knowledge base."""
        where_filter = None
        
        if category:
            where_filter = {"path": ["category"], "operator": "Equal", "valueText": category}
        
        if tags:
            tag_filters = [{"path": ["tags"], "operator": "ContainsAny", "valueTextArray": tags}]
            if where_filter:
                where_filter = {
                    "operator": "And",
                    "operands": [where_filter] + tag_filters
                }
            else:
                where_filter = tag_filters[0]
        
        query_builder = (
            self.client.query
            .get(self.KNOWLEDGE, ["title", "content", "source", "category", "tags", "created_at", "metadata"])
            .with_near_text({"concepts": [query], "certainty": min_certainty})
            .with_limit(limit)
            .with_additional(["id", "certainty"])
        )
        
        if where_filter:
            query_builder = query_builder.with_where(where_filter)
        
        result = query_builder.do()
        
        return result.get("data", {}).get("Get", {}).get(self.KNOWLEDGE, [])
    
    # Conversation operations
    def store_conversation(
        self,
        session_id: str,
        agent_id: str,
        user_id: str,
        message: str,
        role: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store conversation message."""
        data = {
            "session_id": session_id,
            "agent_id": agent_id,
            "user_id": user_id,
            "message": message,
            "role": role,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        result = self.client.data_object.create(
            data_object=data,
            class_name=self.CONVERSATION
        )
        
        return result
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        result = (
            self.client.query
            .get(self.CONVERSATION, ["session_id", "agent_id", "user_id", "message", "role", "timestamp", "metadata"])
            .with_where({"path": ["session_id"], "operator": "Equal", "valueText": session_id})
            .with_limit(limit)
            .with_additional(["id"])
            .do()
        )
        
        messages = result.get("data", {}).get("Get", {}).get(self.CONVERSATION, [])
        # Sort by timestamp
        return sorted(messages, key=lambda x: x.get("timestamp", ""))
    
    def search_conversations(
        self,
        query: str,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 20,
        min_certainty: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search conversations."""
        where_filter = None
        
        if agent_id:
            where_filter = {"path": ["agent_id"], "operator": "Equal", "valueText": agent_id}
        
        if user_id:
            user_filter = {"path": ["user_id"], "operator": "Equal", "valueText": user_id}
            if where_filter:
                where_filter = {
                    "operator": "And",
                    "operands": [where_filter, user_filter]
                }
            else:
                where_filter = user_filter
        
        query_builder = (
            self.client.query
            .get(self.CONVERSATION, ["session_id", "agent_id", "user_id", "message", "role", "timestamp", "metadata"])
            .with_near_text({"concepts": [query], "certainty": min_certainty})
            .with_limit(limit)
            .with_additional(["id", "certainty"])
        )
        
        if where_filter:
            query_builder = query_builder.with_where(where_filter)
        
        result = query_builder.do()
        
        return result.get("data", {}).get("Get", {}).get(self.CONVERSATION, [])
    
    # Document operations
    def store_document(
        self,
        title: str,
        content: str,
        source: str,
        doc_type: str,
        chunk_index: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store document for RAG."""
        data = {
            "title": title,
            "content": content,
            "source": source,
            "doc_type": doc_type,
            "chunk_index": chunk_index,
            "created_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        result = self.client.data_object.create(
            data_object=data,
            class_name=self.DOCUMENT
        )
        
        return result
    
    def search_documents(
        self,
        query: str,
        doc_type: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 10,
        min_certainty: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search documents."""
        where_filter = None
        
        if doc_type:
            where_filter = {"path": ["doc_type"], "operator": "Equal", "valueText": doc_type}
        
        if source:
            source_filter = {"path": ["source"], "operator": "Equal", "valueText": source}
            if where_filter:
                where_filter = {
                    "operator": "And",
                    "operands": [where_filter, source_filter]
                }
            else:
                where_filter = source_filter
        
        query_builder = (
            self.client.query
            .get(self.DOCUMENT, ["title", "content", "source", "doc_type", "chunk_index", "created_at", "metadata"])
            .with_near_text({"concepts": [query], "certainty": min_certainty})
            .with_limit(limit)
            .with_additional(["id", "certainty"])
        )
        
        if where_filter:
            query_builder = query_builder.with_where(where_filter)
        
        result = query_builder.do()
        
        return result.get("data", {}).get("Get", {}).get(self.DOCUMENT, [])
    
    # Utility methods
    def delete_object(self, class_name: str, object_id: str) -> bool:
        """Delete an object by ID."""
        try:
            self.client.data_object.delete(
                uuid=object_id,
                class_name=class_name
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete object: {e}")
            return False
    
    def batch_create(self, class_name: str, objects: List[Dict[str, Any]]) -> List[str]:
        """Batch create objects."""
        with self.client.batch as batch:
            batch.batch_size = 100
            ids = []
            
            for obj in objects:
                id = batch.add_data_object(
                    data_object=obj,
                    class_name=class_name
                )
                ids.append(id)
        
        return ids
    
    def health_check(self) -> bool:
        """Check Weaviate connection health."""
        try:
            return self.client.is_ready()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Weaviate statistics."""
        stats = {}
        for class_name in [self.AGENT_MEMORY, self.KNOWLEDGE, self.CONVERSATION, self.DOCUMENT]:
            try:
                result = (
                    self.client.query
                    .aggregate(class_name)
                    .with_meta_count()
                    .do()
                )
                count = result.get("data", {}).get("Aggregate", {}).get(class_name, [{}])[0].get("meta", {}).get("count", 0)
                stats[class_name] = count
            except Exception as e:
                logger.error(f"Failed to get stats for {class_name}: {e}")
                stats[class_name] = 0
        
        return stats 