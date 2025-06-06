#!/usr/bin/env python3
"""
Vector Router - Intelligent routing between Pinecone and Weaviate
Routes operations based on use case and performance requirements
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
import json
import os
from datetime import datetime
import time
from dataclasses import dataclass
from vector_store_interface import (
    VectorStoreInterface, 
    VectorStoreFactory,
    VectorDocument,
    QueryResult
)

class VectorOperation(Enum):
    """Types of vector operations"""
    # Pinecone-optimized operations
    SIMPLE_SIMILARITY = "simple_similarity"
    HIGH_VOLUME_SEARCH = "high_volume_search"
    AGENT_MEMORY = "agent_memory"
    EMBEDDING_STORAGE = "embedding_storage"
    
    # Weaviate-optimized operations
    HYBRID_SEARCH = "hybrid_search"
    SEMANTIC_QA = "semantic_qa"
    GRAPH_TRAVERSAL = "graph_traversal"
    COMPLEX_FILTERING = "complex_filtering"
    CONTEXTUAL_SEARCH = "contextual_search"

@dataclass
class RoutingMetrics:
    """Metrics for routing decisions"""
    operation: VectorOperation
    latency_ms: float
    success: bool
    store_used: str
    timestamp: datetime

class VectorRouter:
    """Intelligent router for vector operations"""
    
    def __init__(self, pinecone_config: Dict = None, weaviate_config: Dict = None):
        """Initialize router with both vector stores"""
        
        # Initialize Pinecone
        self.pinecone_config = pinecone_config or {
            'api_key': os.getenv('PINECONE_API_KEY'),
            'environment': os.getenv('PINECONE_ENV', 'us-west1-gcp'),
            'index_name': os.getenv('PINECONE_INDEX', 'vectors')
        }
        
        # Initialize Weaviate
        self.weaviate_config = weaviate_config or {
            'url': os.getenv('WEAVIATE_URL', 'http://localhost:8080'),
            'class_name': os.getenv('WEAVIATE_CLASS', 'Document')
        }
        
        # Lazy initialization
        self._pinecone_store = None
        self._weaviate_store = None
        
        # Routing configuration
        self.routing_rules = {
            # Pinecone for high-performance, simple operations
            VectorOperation.SIMPLE_SIMILARITY: 'pinecone',
            VectorOperation.HIGH_VOLUME_SEARCH: 'pinecone',
            VectorOperation.AGENT_MEMORY: 'pinecone',
            VectorOperation.EMBEDDING_STORAGE: 'pinecone',
            
            # Weaviate for complex AI operations
            VectorOperation.HYBRID_SEARCH: 'weaviate',
            VectorOperation.SEMANTIC_QA: 'weaviate',
            VectorOperation.GRAPH_TRAVERSAL: 'weaviate',
            VectorOperation.COMPLEX_FILTERING: 'weaviate',
            VectorOperation.CONTEXTUAL_SEARCH: 'weaviate'
        }
        
        # Performance metrics
        self.metrics: List[RoutingMetrics] = []
        
        # Circuit breaker configuration
        self.circuit_breaker = {
            'pinecone': {'failures': 0, 'threshold': 5, 'is_open': False},
            'weaviate': {'failures': 0, 'threshold': 5, 'is_open': False}
        }
    
    @property
    def pinecone_store(self) -> VectorStoreInterface:
        """Get Pinecone store (lazy initialization)"""
        if self._pinecone_store is None:
            try:
                self._pinecone_store = VectorStoreFactory.create('pinecone', self.pinecone_config)
                print("Pinecone store initialized successfully")
            except Exception as e:
                print(f"Failed to initialize Pinecone: {str(e)}")
                raise
        return self._pinecone_store
    
    @property
    def weaviate_store(self) -> VectorStoreInterface:
        """Get Weaviate store (lazy initialization)"""
        if self._weaviate_store is None:
            try:
                self._weaviate_store = VectorStoreFactory.create('weaviate', self.weaviate_config)
                print("Weaviate store initialized successfully")
            except Exception as e:
                print(f"Failed to initialize Weaviate: {str(e)}")
                raise
        return self._weaviate_store
    
    def get_store_for_operation(self, operation: VectorOperation) -> Tuple[VectorStoreInterface, str]:
        """Get the appropriate store for an operation"""
        
        # Check routing rules
        preferred_store = self.routing_rules.get(operation, 'pinecone')
        
        # Check circuit breaker
        if self.circuit_breaker[preferred_store]['is_open']:
            # Fallback to other store
            fallback_store = 'weaviate' if preferred_store == 'pinecone' else 'pinecone'
            print(f"Circuit breaker open for {preferred_store}, falling back to {fallback_store}")
            preferred_store = fallback_store
        
        # Return appropriate store
        if preferred_store == 'pinecone':
            return self.pinecone_store, 'pinecone'
        else:
            return self.weaviate_store, 'weaviate'
    
    def upsert(self, 
               documents: List[VectorDocument], 
               operation: VectorOperation,
               namespace: Optional[str] = None) -> Dict[str, Any]:
        """Route upsert operation to appropriate store"""
        
        start_time = time.time()
        store, store_name = self.get_store_for_operation(operation)
        
        try:
            result = store.upsert(documents, namespace)
            
            # Record metrics
            latency = (time.time() - start_time) * 1000
            self._record_metric(operation, latency, True, store_name)
            
            # Reset circuit breaker on success
            self.circuit_breaker[store_name]['failures'] = 0
            
            return {
                **result,
                'store_used': store_name,
                'latency_ms': latency
            }
            
        except Exception as e:
            # Record failure
            latency = (time.time() - start_time) * 1000
            self._record_metric(operation, latency, False, store_name)
            
            # Update circuit breaker
            self._handle_failure(store_name)
            
            return {
                'success': False,
                'error': str(e),
                'store_used': store_name,
                'latency_ms': latency
            }
    
    def query(self,
              vector: List[float],
              operation: VectorOperation,
              top_k: int = 10,
              namespace: Optional[str] = None,
              filter: Optional[Dict] = None) -> List[QueryResult]:
        """Route query operation to appropriate store"""
        
        start_time = time.time()
        store, store_name = self.get_store_for_operation(operation)
        
        try:
            results = store.query(vector, top_k, namespace, filter)
            
            # Record metrics
            latency = (time.time() - start_time) * 1000
            self._record_metric(operation, latency, True, store_name)
            
            # Reset circuit breaker on success
            self.circuit_breaker[store_name]['failures'] = 0
            
            # Add metadata about which store was used
            for result in results:
                if not hasattr(result, 'metadata'):
                    result.metadata = {}
                result.metadata['_vector_store'] = store_name
                result.metadata['_latency_ms'] = latency
            
            return results
            
        except Exception as e:
            # Record failure
            latency = (time.time() - start_time) * 1000
            self._record_metric(operation, latency, False, store_name)
            
            # Update circuit breaker
            self._handle_failure(store_name)
            
            print(f"Query failed on {store_name}: {str(e)}")
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of both vector stores"""
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'stores': {},
            'routing_rules': self.routing_rules,
            'circuit_breakers': self.circuit_breaker
        }
        
        # Check Pinecone
        try:
            pinecone_healthy, pinecone_msg = self.pinecone_store.health_check()
            health_status['stores']['pinecone'] = {
                'healthy': pinecone_healthy,
                'message': pinecone_msg,
                'stats': self.pinecone_store.describe_index_stats()
            }
        except Exception as e:
            health_status['stores']['pinecone'] = {
                'healthy': False,
                'message': f"Health check failed: {str(e)}"
            }
        
        # Check Weaviate
        try:
            weaviate_healthy, weaviate_msg = self.weaviate_store.health_check()
            health_status['stores']['weaviate'] = {
                'healthy': weaviate_healthy,
                'message': weaviate_msg,
                'stats': self.weaviate_store.describe_index_stats()
            }
        except Exception as e:
            health_status['stores']['weaviate'] = {
                'healthy': False,
                'message': f"Health check failed: {str(e)}"
            }
        
        return health_status
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for routing decisions"""
        
        if not self.metrics:
            return {'message': 'No metrics available yet'}
        
        # Aggregate metrics by operation and store
        metrics_summary = {}
        
        for metric in self.metrics:
            key = f"{metric.operation.value}_{metric.store_used}"
            
            if key not in metrics_summary:
                metrics_summary[key] = {
                    'operation': metric.operation.value,
                    'store': metric.store_used,
                    'count': 0,
                    'success_count': 0,
                    'total_latency': 0,
                    'min_latency': float('inf'),
                    'max_latency': 0
                }
            
            summary = metrics_summary[key]
            summary['count'] += 1
            if metric.success:
                summary['success_count'] += 1
            summary['total_latency'] += metric.latency_ms
            summary['min_latency'] = min(summary['min_latency'], metric.latency_ms)
            summary['max_latency'] = max(summary['max_latency'], metric.latency_ms)
        
        # Calculate averages and success rates
        for summary in metrics_summary.values():
            summary['avg_latency'] = summary['total_latency'] / summary['count']
            summary['success_rate'] = summary['success_count'] / summary['count']
            del summary['total_latency']  # Remove intermediate value
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_operations': len(self.metrics),
            'metrics_by_operation': list(metrics_summary.values()),
            'last_10_operations': [
                {
                    'operation': m.operation.value,
                    'store': m.store_used,
                    'latency_ms': m.latency_ms,
                    'success': m.success,
                    'timestamp': m.timestamp.isoformat()
                }
                for m in self.metrics[-10:]
            ]
        }
    
    def _record_metric(self, operation: VectorOperation, latency_ms: float, 
                      success: bool, store_used: str):
        """Record performance metric"""
        metric = RoutingMetrics(
            operation=operation,
            latency_ms=latency_ms,
            success=success,
            store_used=store_used,
            timestamp=datetime.now()
        )
        self.metrics.append(metric)
        
        # Keep only last 1000 metrics
        if len(self.metrics) > 1000:
            self.metrics = self.metrics[-1000:]
    
    def _handle_failure(self, store_name: str):
        """Handle store failure for circuit breaker"""
        breaker = self.circuit_breaker[store_name]
        breaker['failures'] += 1
        
        if breaker['failures'] >= breaker['threshold']:
            breaker['is_open'] = True
            print(f"Circuit breaker opened for {store_name} after {breaker['failures']} failures")
            
            # Schedule circuit breaker reset after 60 seconds
            import threading
            threading.Timer(60.0, self._reset_circuit_breaker, args=[store_name]).start()
    
    def _reset_circuit_breaker(self, store_name: str):
        """Reset circuit breaker after timeout"""
        self.circuit_breaker[store_name]['is_open'] = False
        self.circuit_breaker[store_name]['failures'] = 0
        print(f"Circuit breaker reset for {store_name}")


# Example usage and testing
if __name__ == "__main__":
    print("Vector Router Test")
    print("="*50)
    
    # Initialize router
    router = VectorRouter()
    
    # Check health
    print("\nChecking vector store health...")
    health = router.health_check()
    print(json.dumps(health, indent=2))
    
    # Example routing decision
    print("\nRouting examples:")
    for operation in VectorOperation:
        store_name = router.routing_rules.get(operation, 'unknown')
        print(f"  {operation.value} -> {store_name}")
    
    print("\nRouter initialized and ready for operations")
    print("Use router.upsert() and router.query() with appropriate VectorOperation")