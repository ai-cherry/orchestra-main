"""
Vector Store Management

Handles vector database operations for semantic search and embeddings storage.
Supports both Weaviate and FAISS for flexible deployment options.
"""

import os
import json
import uuid
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
import structlog

logger = structlog.get_logger(__name__)

class VectorStore(ABC):
    """Abstract base class for vector store implementations"""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the vector store"""
        pass
    
    @abstractmethod
    async def create_collection(self, collection_name: str, embedding_dim: int, metadata_schema: Dict[str, Any]) -> bool:
        """Create a new collection/index"""
        pass
    
    @abstractmethod
    async def add_vectors(self, collection_name: str, vectors: List[List[float]], 
                         metadata: List[Dict[str, Any]], ids: List[str]) -> bool:
        """Add vectors to a collection"""
        pass
    
    @abstractmethod
    async def search_vectors(self, collection_name: str, query_vector: List[float], 
                           top_k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        pass
    
    @abstractmethod
    async def delete_vectors(self, collection_name: str, ids: List[str]) -> bool:
        """Delete vectors by ID"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check vector store health"""
        pass

class WeaviateStore(VectorStore):
    """Weaviate vector store implementation"""
    
    def __init__(self):
        self.client = None
        self.url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
        self.api_key = os.getenv("WEAVIATE_API_KEY")
        
    async def initialize(self) -> bool:
        """Initialize Weaviate client"""
        try:
            import weaviate
            
            auth_config = None
            if self.api_key:
                auth_config = weaviate.AuthApiKey(api_key=self.api_key)
            
            self.client = weaviate.Client(
                url=self.url,
                auth_client_secret=auth_config,
                timeout_config=(5, 15)
            )
            
            # Test connection
            schema = self.client.schema.get()
            logger.info("Weaviate initialized successfully", classes=len(schema.get('classes', [])))
            return True
            
        except Exception as e:
            logger.error("Failed to initialize Weaviate", error=str(e))
            return False
    
    async def create_collection(self, collection_name: str, embedding_dim: int, metadata_schema: Dict[str, Any]) -> bool:
        """Create a Weaviate class"""
        try:
            # Define class properties based on metadata schema
            properties = []
            for field_name, field_type in metadata_schema.items():
                if field_type == "string":
                    properties.append({
                        "name": field_name,
                        "dataType": ["text"]
                    })
                elif field_type == "number":
                    properties.append({
                        "name": field_name,
                        "dataType": ["number"]
                    })
                elif field_type == "boolean":
                    properties.append({
                        "name": field_name,
                        "dataType": ["boolean"]
                    })
            
            # Standard properties for all collections
            properties.extend([
                {"name": "content", "dataType": ["text"]},
                {"name": "file_id", "dataType": ["text"]},
                {"name": "chunk_index", "dataType": ["int"]},
                {"name": "timestamp", "dataType": ["date"]}
            ])
            
            class_obj = {
                "class": collection_name,
                "description": f"Vector collection for {collection_name}",
                "properties": properties,
                "vectorizer": "none",  # We provide our own vectors
                "vectorIndexConfig": {
                    "distance": "cosine"
                }
            }
            
            self.client.schema.create_class(class_obj)
            logger.info(f"Created Weaviate class: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create Weaviate class {collection_name}", error=str(e))
            return False
    
    async def add_vectors(self, collection_name: str, vectors: List[List[float]], 
                         metadata: List[Dict[str, Any]], ids: List[str]) -> bool:
        """Add vectors to Weaviate"""
        try:
            with self.client.batch as batch:
                batch.batch_size = 100
                
                for i, (vector, meta, doc_id) in enumerate(zip(vectors, metadata, ids)):
                    data_object = meta.copy()
                    data_object["id"] = doc_id
                    
                    batch.add_data_object(
                        data_object=data_object,
                        class_name=collection_name,
                        uuid=doc_id,
                        vector=vector
                    )
            
            logger.info(f"Added {len(vectors)} vectors to {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add vectors to {collection_name}", error=str(e))
            return False
    
    async def search_vectors(self, collection_name: str, query_vector: List[float], 
                           top_k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search Weaviate for similar vectors"""
        try:
            query = self.client.query.get(collection_name, ["*"]).with_near_vector({
                "vector": query_vector,
                "certainty": 0.7
            }).with_limit(top_k)
            
            # Apply filters if provided
            if filters:
                where_filter = {"operator": "And", "operands": []}
                for key, value in filters.items():
                    where_filter["operands"].append({
                        "path": [key],
                        "operator": "Equal",
                        "valueText": str(value)
                    })
                query = query.with_where(where_filter)
            
            result = query.do()
            
            # Extract results
            results = []
            if "data" in result and "Get" in result["data"]:
                for item in result["data"]["Get"][collection_name]:
                    results.append({
                        "id": item.get("id", ""),
                        "score": item.get("_additional", {}).get("certainty", 0.0),
                        "metadata": item
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search vectors in {collection_name}", error=str(e))
            return []
    
    async def delete_vectors(self, collection_name: str, ids: List[str]) -> bool:
        """Delete vectors from Weaviate"""
        try:
            for doc_id in ids:
                self.client.data_object.delete(uuid=doc_id, class_name=collection_name)
            
            logger.info(f"Deleted {len(ids)} vectors from {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete vectors from {collection_name}", error=str(e))
            return False
    
    async def health_check(self) -> bool:
        """Check Weaviate health"""
        try:
            return self.client.is_ready()
        except Exception:
            return False

class FAISSStore(VectorStore):
    """FAISS vector store implementation for local development"""
    
    def __init__(self):
        self.indexes = {}
        self.metadata_store = {}
        self.storage_path = os.getenv("FAISS_STORAGE_PATH", "./data/faiss")
        os.makedirs(self.storage_path, exist_ok=True)
        
    async def initialize(self) -> bool:
        """Initialize FAISS store"""
        try:
            import faiss
            logger.info("FAISS store initialized successfully")
            return True
        except ImportError:
            logger.error("FAISS library not available")
            return False
    
    async def create_collection(self, collection_name: str, embedding_dim: int, metadata_schema: Dict[str, Any]) -> bool:
        """Create a FAISS index"""
        try:
            import faiss
            
            # Create index
            index = faiss.IndexFlatIP(embedding_dim)  # Inner product for cosine similarity
            self.indexes[collection_name] = {
                "index": index,
                "dimension": embedding_dim,
                "metadata_schema": metadata_schema
            }
            
            # Initialize metadata store
            self.metadata_store[collection_name] = {}
            
            logger.info(f"Created FAISS index: {collection_name} (dim: {embedding_dim})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create FAISS index {collection_name}", error=str(e))
            return False
    
    async def add_vectors(self, collection_name: str, vectors: List[List[float]], 
                         metadata: List[Dict[str, Any]], ids: List[str]) -> bool:
        """Add vectors to FAISS index"""
        try:
            if collection_name not in self.indexes:
                return False
            
            index_info = self.indexes[collection_name]
            index = index_info["index"]
            
            # Convert to numpy array and normalize for cosine similarity
            vectors_np = np.array(vectors, dtype=np.float32)
            faiss.normalize_L2(vectors_np)
            
            # Add vectors to index
            start_id = index.ntotal
            index.add(vectors_np)
            
            # Store metadata
            for i, (doc_id, meta) in enumerate(zip(ids, metadata)):
                internal_id = start_id + i
                self.metadata_store[collection_name][internal_id] = {
                    "id": doc_id,
                    "metadata": meta
                }
            
            logger.info(f"Added {len(vectors)} vectors to FAISS index {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add vectors to FAISS index {collection_name}", error=str(e))
            return False
    
    async def search_vectors(self, collection_name: str, query_vector: List[float], 
                           top_k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search FAISS index for similar vectors"""
        try:
            if collection_name not in self.indexes:
                return []
            
            index_info = self.indexes[collection_name]
            index = index_info["index"]
            
            # Normalize query vector
            query_np = np.array([query_vector], dtype=np.float32)
            faiss.normalize_L2(query_np)
            
            # Search
            scores, indices = index.search(query_np, top_k)
            
            # Build results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:  # No more results
                    break
                
                if idx in self.metadata_store[collection_name]:
                    item = self.metadata_store[collection_name][idx]
                    
                    # Apply filters if provided
                    if filters:
                        skip = False
                        for key, value in filters.items():
                            if key in item["metadata"] and item["metadata"][key] != value:
                                skip = True
                                break
                        if skip:
                            continue
                    
                    results.append({
                        "id": item["id"],
                        "score": float(score),
                        "metadata": item["metadata"]
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to search FAISS index {collection_name}", error=str(e))
            return []
    
    async def delete_vectors(self, collection_name: str, ids: List[str]) -> bool:
        """Delete vectors from FAISS index (not directly supported, would need rebuild)"""
        try:
            # FAISS doesn't support deletion, so we mark as deleted in metadata
            if collection_name not in self.metadata_store:
                return False
            
            deleted_count = 0
            for internal_id, item in self.metadata_store[collection_name].items():
                if item["id"] in ids:
                    item["deleted"] = True
                    deleted_count += 1
            
            logger.info(f"Marked {deleted_count} vectors as deleted in {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete vectors from FAISS index {collection_name}", error=str(e))
            return False
    
    async def health_check(self) -> bool:
        """Check FAISS store health"""
        return True

# Factory function to create vector store based on configuration
def create_vector_store() -> VectorStore:
    """Create vector store instance based on configuration"""
    store_type = os.getenv("VECTOR_STORE_TYPE", "faiss").lower()
    
    if store_type == "weaviate":
        return WeaviateStore()
    elif store_type == "faiss":
        return FAISSStore()
    else:
        logger.warning(f"Unknown vector store type: {store_type}, defaulting to FAISS")
        return FAISSStore()

# Global vector store instance
vector_store = create_vector_store() 