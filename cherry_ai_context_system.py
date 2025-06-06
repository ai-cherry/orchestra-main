#!/usr/bin/env python3
"""
Cherry AI Context Management System
Manages workflow context, MCP integration, and vector store operations
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import hashlib
import pickle
from collections import defaultdict
import numpy as np
import pinecone
import weaviate
import redis
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ContextEntry:
    """Individual context entry with metadata"""
    id: str
    key: str
    value: Any
    context_type: str  # conversation, task, preference, memory
    persona: Optional[str] = None
    user_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    ttl: Optional[int] = None  # Time to live in seconds
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if context entry has expired"""
        if self.ttl is None:
            return False
        return (datetime.now() - self.timestamp).total_seconds() > self.ttl
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
            "context_type": self.context_type,
            "persona": self.persona,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "ttl": self.ttl,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat(),
            "metadata": self.metadata
        }


class VectorStoreManager:
    """Manages vector store operations for context retrieval"""
    
    def __init__(self, pinecone_api_key: str, weaviate_url: str):
        # Initialize Pinecone
        pinecone.init(api_key=pinecone_api_key)
        
        # Initialize indexes for each persona
        self.pinecone_indexes = {
            "cherry": pinecone.Index("cherry-personal"),
            "sophia": pinecone.Index("sophia-business"),
            "karen": pinecone.Index("karen-healthcare")
        }
        
        # Initialize Weaviate client
        self.weaviate_client = weaviate.Client(url=weaviate_url)
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text"""
        return self.embedding_model.encode(text)
        
    async def store_context_vector(self, context_entry: ContextEntry):
        """Store context entry in vector database"""
        # Generate embedding if not provided
        if context_entry.embedding is None:
            text_representation = f"{context_entry.key}: {str(context_entry.value)}"
            context_entry.embedding = self.generate_embedding(text_representation)
            
        # Store in Pinecone
        if context_entry.persona in self.pinecone_indexes:
            index = self.pinecone_indexes[context_entry.persona]
            
            # Prepare vector data
            vector_data = {
                "id": context_entry.id,
                "values": context_entry.embedding.tolist(),
                "metadata": {
                    "key": context_entry.key,
                    "context_type": context_entry.context_type,
                    "user_id": context_entry.user_id,
                    "timestamp": context_entry.timestamp.isoformat(),
                    **context_entry.metadata
                }
            }
            
            # Upsert to Pinecone
            index.upsert(vectors=[vector_data])
            
        # Store in Weaviate for knowledge graph
        if context_entry.context_type in ["preference", "memory"]:
            self._store_in_weaviate(context_entry)
            
    def _store_in_weaviate(self, context_entry: ContextEntry):
        """Store context in Weaviate knowledge graph"""
        class_name = f"{context_entry.persona.capitalize()}Knowledge"
        
        data_object = {
            "contextId": context_entry.id,
            "key": context_entry.key,
            "value": str(context_entry.value),
            "contextType": context_entry.context_type,
            "userId": context_entry.user_id,
            "timestamp": context_entry.timestamp.isoformat(),
            "metadata": json.dumps(context_entry.metadata)
        }
        
        try:
            self.weaviate_client.data_object.create(
                data_object=data_object,
                class_name=class_name
            )
        except Exception as e:
            logger.error(f"Error storing in Weaviate: {e}")
            
    async def retrieve_similar_contexts(
        self, 
        query: str, 
        persona: str, 
        top_k: int = 5,
        context_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve similar contexts from vector store"""
        # Generate query embedding
        query_embedding = self.generate_embedding(query)
        
        # Search in Pinecone
        if persona in self.pinecone_indexes:
            index = self.pinecone_indexes[persona]
            
            # Build filter
            filter_dict = {}
            if context_type:
                filter_dict["context_type"] = context_type
                
            # Query index
            results = index.query(
                vector=query_embedding.tolist(),
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict if filter_dict else None
            )
            
            return [
                {
                    "id": match["id"],
                    "score": match["score"],
                    "metadata": match["metadata"]
                }
                for match in results["matches"]
            ]
            
        return []
        
    async def get_knowledge_graph_connections(
        self, 
        context_id: str, 
        persona: str
    ) -> List[Dict[str, Any]]:
        """Get related contexts from knowledge graph"""
        class_name = f"{persona.capitalize()}Knowledge"
        
        try:
            # Query Weaviate for related objects
            result = self.weaviate_client.query.get(
                class_name,
                ["contextId", "key", "value", "contextType", "metadata"]
            ).with_where({
                "path": ["contextId"],
                "operator": "Equal",
                "valueString": context_id
            }).do()
            
            if result and "data" in result:
                return result["data"]["Get"][class_name]
                
        except Exception as e:
            logger.error(f"Error querying Weaviate: {e}")
            
        return []


class ContextVersionManager:
    """Manages context versioning and rollback"""
    
    def __init__(self, max_versions: int = 10):
        self.max_versions = max_versions
        self.version_store: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.current_versions: Dict[str, int] = {}
        
    def create_version(self, context_key: str, context_data: Dict[str, Any]):
        """Create a new version of context"""
        version = {
            "version_id": hashlib.sha256(
                f"{context_key}_{datetime.now().isoformat()}".encode()
            ).hexdigest()[:16],
            "timestamp": datetime.now(),
            "data": context_data.copy(),
            "checksum": self._calculate_checksum(context_data)
        }
        
        # Add to version store
        self.version_store[context_key].append(version)
        
        # Prune old versions
        if len(self.version_store[context_key]) > self.max_versions:
            self.version_store[context_key] = self.version_store[context_key][-self.max_versions:]
            
        # Update current version
        self.current_versions[context_key] = len(self.version_store[context_key]) - 1
        
        return version["version_id"]
        
    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate checksum for data integrity"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()
        
    def get_version(self, context_key: str, version_index: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get specific version of context"""
        if context_key not in self.version_store:
            return None
            
        versions = self.version_store[context_key]
        if not versions:
            return None
            
        if version_index is None:
            version_index = self.current_versions.get(context_key, -1)
            
        if 0 <= version_index < len(versions):
            return versions[version_index]["data"]
            
        return None
        
    def rollback(self, context_key: str, version_index: int) -> bool:
        """Rollback to specific version"""
        if context_key in self.version_store:
            versions = self.version_store[context_key]
            if 0 <= version_index < len(versions):
                self.current_versions[context_key] = version_index
                return True
        return False
        
    def get_version_history(self, context_key: str) -> List[Dict[str, Any]]:
        """Get version history for context"""
        if context_key not in self.version_store:
            return []
            
        return [
            {
                "version_id": v["version_id"],
                "timestamp": v["timestamp"].isoformat(),
                "is_current": i == self.current_versions.get(context_key, -1)
            }
            for i, v in enumerate(self.version_store[context_key])
        ]


class WorkflowContextManager:
    """Manages context for workflow execution"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.workflow_contexts: Dict[str, Dict[str, Any]] = {}
        self.checkpoint_prefix = "checkpoint:"
        self.context_prefix = "context:"
        
    async def create_workflow_context(self, workflow_id: str, initial_context: Dict[str, Any]) -> str:
        """Create new workflow context"""
        context = {
            "workflow_id": workflow_id,
            "created_at": datetime.now().isoformat(),
            "status": "initialized",
            "data": initial_context,
            "checkpoints": [],
            "current_step": None
        }
        
        # Store in memory
        self.workflow_contexts[workflow_id] = context
        
        # Persist to Redis
        await self._persist_context(workflow_id, context)
        
        return workflow_id
        
    async def update_workflow_context(
        self, 
        workflow_id: str, 
        updates: Dict[str, Any],
        create_checkpoint: bool = False
    ):
        """Update workflow context"""
        if workflow_id not in self.workflow_contexts:
            # Try to load from Redis
            context = await self._load_context(workflow_id)
            if not context:
                raise ValueError(f"Workflow {workflow_id} not found")
            self.workflow_contexts[workflow_id] = context
            
        # Update context data
        context = self.workflow_contexts[workflow_id]
        context["data"].update(updates)
        context["updated_at"] = datetime.now().isoformat()
        
        # Create checkpoint if requested
        if create_checkpoint:
            checkpoint = {
                "id": f"checkpoint_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "data": context["data"].copy()
            }
            context["checkpoints"].append(checkpoint)
            
        # Persist updated context
        await self._persist_context(workflow_id, context)
        
    async def _persist_context(self, workflow_id: str, context: Dict[str, Any]):
        """Persist workflow context to Redis"""
        key = f"{self.context_prefix}{workflow_id}"
        await self.redis_client.set(key, json.dumps(context), ex=86400)  # 24 hours TTL
        
    async def _load_context(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Load workflow context from Redis"""
        key = f"{self.context_prefix}{workflow_id}"
        context_data = await self.redis_client.get(key)
        if context_data:
            return json.loads(context_data)
        return None
        
    async def get_workflow_context(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow context"""
        if workflow_id in self.workflow_contexts:
            return self.workflow_contexts[workflow_id]
            
        # Try loading from Redis
        context = await self._load_context(workflow_id)
        if context:
            self.workflow_contexts[workflow_id] = context
            return context
            
        return None
        
    async def create_checkpoint(self, workflow_id: str, checkpoint_name: str) -> str:
        """Create a named checkpoint"""
        context = await self.get_workflow_context(workflow_id)
        if not context:
            raise ValueError(f"Workflow {workflow_id} not found")
            
        checkpoint_id = f"checkpoint_{datetime.now().timestamp()}"
        checkpoint = {
            "id": checkpoint_id,
            "name": checkpoint_name,
            "timestamp": datetime.now().isoformat(),
            "data": context["data"].copy()
        }
        
        context["checkpoints"].append(checkpoint)
        await self._persist_context(workflow_id, context)
        
        return checkpoint_id
        
    async def restore_checkpoint(self, workflow_id: str, checkpoint_id: str) -> bool:
        """Restore from a specific checkpoint"""
        context = await self.get_workflow_context(workflow_id)
        if not context:
            return False
            
        # Find the checkpoint
        for checkpoint in context["checkpoints"]:
            if checkpoint["id"] == checkpoint_id:
                context["data"] = checkpoint["data"].copy()
                context["restored_from"] = checkpoint_id
                context["restored_at"] = datetime.now().isoformat()
                await self._persist_context(workflow_id, context)
                return True
                
        return False
