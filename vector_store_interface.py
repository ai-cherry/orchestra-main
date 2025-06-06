#!/usr/bin/env python3
"""
Vector Store Interface - Abstraction Layer
Enables seamless switching between Pinecone and Weaviate
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from dataclasses import dataclass
import json
import os
from datetime import datetime

@dataclass
class VectorDocument:
    """Standard vector document format"""
    id: str
    vector: List[float]
    metadata: Dict[str, Any]
    namespace: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'vector': self.vector,
            'metadata': self.metadata,
            'namespace': self.namespace
        }

@dataclass
class QueryResult:
    """Standard query result format"""
    id: str
    score: float
    metadata: Dict[str, Any]
    vector: Optional[List[float]] = None

class VectorStoreInterface(ABC):
    """Abstract interface for vector stores"""
    
    @abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """Initialize vector store with configuration"""
        pass
    
    @abstractmethod
    def upsert(self, documents: List[VectorDocument], namespace: Optional[str] = None) -> Dict[str, Any]:
        """Insert or update vectors"""
        pass
    
    @abstractmethod
    def query(self, 
              vector: List[float], 
              top_k: int = 10,
              namespace: Optional[str] = None,
              filter: Optional[Dict] = None) -> List[QueryResult]:
        """Query similar vectors"""
        pass
    
    @abstractmethod
    def delete(self, ids: List[str], namespace: Optional[str] = None) -> Dict[str, Any]:
        """Delete vectors by ID"""
        pass
    
    @abstractmethod
    def fetch(self, ids: List[str], namespace: Optional[str] = None) -> Dict[str, VectorDocument]:
        """Fetch vectors by ID"""
        pass
    
    @abstractmethod
    def describe_index_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        pass
    
    @abstractmethod
    def health_check(self) -> Tuple[bool, str]:
        """Check if vector store is healthy"""
        pass

class PineconeAdapter(VectorStoreInterface):
    """Pinecone implementation of vector store interface"""
    
    def __init__(self, config: Dict[str, Any]):
        try:
            import pinecone
            
            # Initialize Pinecone
            pinecone.init(
                api_key=config.get('api_key', os.getenv('PINECONE_API_KEY')),
                environment=config.get('environment', os.getenv('PINECONE_ENV', 'us-west1-gcp'))
            )
            
            self.index_name = config.get('index_name', 'vectors')
            self.index = pinecone.Index(self.index_name)
            self.config = config
            
        except ImportError:
            raise ImportError("Pinecone library not installed. Run: pip install pinecone-client")
    
    def upsert(self, documents: List[VectorDocument], namespace: Optional[str] = None) -> Dict[str, Any]:
        """Insert or update vectors in Pinecone"""
        try:
            # Convert documents to Pinecone format
            vectors = []
            for doc in documents:
                vector_data = {
                    'id': doc.id,
                    'values': doc.vector,
                    'metadata': doc.metadata
                }
                vectors.append(vector_data)
            
            # Upsert to Pinecone
            response = self.index.upsert(
                vectors=vectors,
                namespace=namespace or doc.namespace
            )
            
            return {
                'success': True,
                'upserted_count': response.get('upserted_count', len(documents)),
                'response': response
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def query(self, 
              vector: List[float], 
              top_k: int = 10,
              namespace: Optional[str] = None,
              filter: Optional[Dict] = None) -> List[QueryResult]:
        """Query similar vectors from Pinecone"""
        try:
            response = self.index.query(
                vector=vector,
                top_k=top_k,
                namespace=namespace,
                filter=filter,
                include_metadata=True,
                include_values=True
            )
            
            results = []
            for match in response.get('matches', []):
                result = QueryResult(
                    id=match['id'],
                    score=match['score'],
                    metadata=match.get('metadata', {}),
                    vector=match.get('values')
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Query error: {str(e)}")
            return []
    
    def delete(self, ids: List[str], namespace: Optional[str] = None) -> Dict[str, Any]:
        """Delete vectors from Pinecone"""
        try:
            response = self.index.delete(
                ids=ids,
                namespace=namespace
            )
            
            return {
                'success': True,
                'deleted_count': len(ids),
                'response': response
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def fetch(self, ids: List[str], namespace: Optional[str] = None) -> Dict[str, VectorDocument]:
        """Fetch vectors from Pinecone"""
        try:
            response = self.index.fetch(
                ids=ids,
                namespace=namespace
            )
            
            documents = {}
            for id, data in response.get('vectors', {}).items():
                doc = VectorDocument(
                    id=id,
                    vector=data.get('values', []),
                    metadata=data.get('metadata', {}),
                    namespace=namespace
                )
                documents[id] = doc
            
            return documents
            
        except Exception as e:
            print(f"Fetch error: {str(e)}")
            return {}
    
    def describe_index_stats(self) -> Dict[str, Any]:
        """Get Pinecone index statistics"""
        try:
            stats = self.index.describe_index_stats()
            return {
                'success': True,
                'stats': stats
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def health_check(self) -> Tuple[bool, str]:
        """Check Pinecone health"""
        try:
            stats = self.describe_index_stats()
            if stats.get('success'):
                return True, "Pinecone is healthy"
            else:
                return False, f"Pinecone error: {stats.get('error')}"
        except Exception as e:
            return False, f"Pinecone connection error: {str(e)}"

class WeaviateAdapter(VectorStoreInterface):
    """Weaviate implementation of vector store interface"""
    
    def __init__(self, config: Dict[str, Any]):
        try:
            import weaviate
            
            # Initialize Weaviate client
            self.client = weaviate.Client(
                url=config.get('url', 'http://localhost:8080'),
                auth_client_secret=config.get('auth_config')
            )
            
            self.class_name = config.get('class_name', 'Document')
            self.config = config
            
        except ImportError:
            raise ImportError("Weaviate library not installed. Run: pip install weaviate-client")
    
    def upsert(self, documents: List[VectorDocument], namespace: Optional[str] = None) -> Dict[str, Any]:
        """Insert or update vectors in Weaviate"""
        try:
            upserted_count = 0
            
            for doc in documents:
                # Prepare data object
                data_object = {
                    'id': doc.id,
                    **doc.metadata
                }
                
                # Add namespace to metadata if provided
                if namespace or doc.namespace:
                    data_object['namespace'] = namespace or doc.namespace
                
                # Create or update object
                self.client.data_object.create(
                    data_object=data_object,
                    class_name=self.class_name,
                    vector=doc.vector,
                    uuid=doc.id
                )
                
                upserted_count += 1
            
            return {
                'success': True,
                'upserted_count': upserted_count
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def query(self, 
              vector: List[float], 
              top_k: int = 10,
              namespace: Optional[str] = None,
              filter: Optional[Dict] = None) -> List[QueryResult]:
        """Query similar vectors from Weaviate"""
        try:
            # Build query
            query = self.client.query.get(
                self.class_name,
                ["id", "_additional {certainty}"]
            ).with_near_vector({
                "vector": vector
            }).with_limit(top_k)
            
            # Add namespace filter if provided
            if namespace:
                where_filter = {
                    "path": ["namespace"],
                    "operator": "Equal",
                    "valueString": namespace
                }
                query = query.with_where(where_filter)
            
            # Execute query
            result = query.do()
            
            results = []
            for item in result.get('data', {}).get('Get', {}).get(self.class_name, []):
                result_obj = QueryResult(
                    id=item.get('id'),
                    score=item.get('_additional', {}).get('certainty', 0),
                    metadata={k: v for k, v in item.items() if k not in ['id', '_additional']}
                )
                results.append(result_obj)
            
            return results
            
        except Exception as e:
            print(f"Query error: {str(e)}")
            return []
    
    def delete(self, ids: List[str], namespace: Optional[str] = None) -> Dict[str, Any]:
        """Delete vectors from Weaviate"""
        try:
            deleted_count = 0
            
            for id in ids:
                self.client.data_object.delete(
                    uuid=id,
                    class_name=self.class_name
                )
                deleted_count += 1
            
            return {
                'success': True,
                'deleted_count': deleted_count
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def fetch(self, ids: List[str], namespace: Optional[str] = None) -> Dict[str, VectorDocument]:
        """Fetch vectors from Weaviate"""
        try:
            documents = {}
            
            for id in ids:
                result = self.client.data_object.get_by_id(
                    uuid=id,
                    class_name=self.class_name,
                    with_vector=True
                )
                
                if result:
                    doc = VectorDocument(
                        id=id,
                        vector=result.get('vector', []),
                        metadata=result.get('properties', {}),
                        namespace=result.get('properties', {}).get('namespace')
                    )
                    documents[id] = doc
            
            return documents
            
        except Exception as e:
            print(f"Fetch error: {str(e)}")
            return {}
    
    def describe_index_stats(self) -> Dict[str, Any]:
        """Get Weaviate statistics"""
        try:
            # Get schema info
            schema = self.client.schema.get()
            
            # Count objects
            count_query = self.client.query.aggregate(self.class_name).with_meta_count().do()
            total_count = count_query.get('data', {}).get('Aggregate', {}).get(self.class_name, [{}])[0].get('meta', {}).get('count', 0)
            
            return {
                'success': True,
                'stats': {
                    'total_vectors': total_count,
                    'classes': len(schema.get('classes', [])),
                    'schema': schema
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def health_check(self) -> Tuple[bool, str]:
        """Check Weaviate health"""
        try:
            if self.client.is_ready():
                return True, "Weaviate is healthy"
            else:
                return False, "Weaviate is not ready"
        except Exception as e:
            return False, f"Weaviate connection error: {str(e)}"

class VectorStoreFactory:
    """Factory for creating vector store instances"""
    
    @staticmethod
    def create(store_type: str, config: Dict[str, Any]) -> VectorStoreInterface:
        """Create vector store instance based on type"""
        
        if store_type.lower() == 'pinecone':
            return PineconeAdapter(config)
        elif store_type.lower() == 'weaviate':
            return WeaviateAdapter(config)
        else:
            raise ValueError(f"Unknown vector store type: {store_type}")
    
    @staticmethod
    def create_from_env() -> VectorStoreInterface:
        """Create vector store from environment variables"""
        
        store_type = os.getenv('VECTOR_DB_PRIMARY', 'pinecone')
        
        if store_type.lower() == 'pinecone':
            config = {
                'api_key': os.getenv('PINECONE_API_KEY'),
                'environment': os.getenv('PINECONE_ENV', 'us-west1-gcp'),
                'index_name': os.getenv('PINECONE_INDEX', 'vectors')
            }
        else:
            config = {
                'url': os.getenv('WEAVIATE_URL', 'http://localhost:8080'),
                'class_name': os.getenv('WEAVIATE_CLASS', 'Document')
            }
        
        return VectorStoreFactory.create(store_type, config)


# Example usage and testing
if __name__ == "__main__":
    # Test vector store abstraction
    print("Vector Store Interface Test")
    print("="*50)
    
    # Create test document
    test_doc = VectorDocument(
        id="test_001",
        vector=[0.1] * 768,  # 768-dimensional vector
        metadata={
            "text": "This is a test document",
            "source": "test",
            "timestamp": datetime.now().isoformat()
        }
    )
    
    print(f"Created test document: {test_doc.id}")
    print(f"Vector dimension: {len(test_doc.vector)}")
    print(f"Metadata: {test_doc.metadata}")
    
    # Configuration ready for both stores
    print("\nVector store configurations ready:")
    print("- Pinecone: Set PINECONE_API_KEY and PINECONE_ENV")
    print("- Weaviate: Ensure service is running on localhost:8080")
    print("\nUse VectorStoreFactory.create_from_env() to instantiate")