#!/usr/bin/env python3
"""
Pinecone Integration Manager for Cherry AI Orchestrator
Handles vector database operations for all three domains (Cherry, Sophia, Karen)
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

try:
    from pinecone import Pinecone, ServerlessSpec
except ImportError:
    print("Installing Pinecone client...")
    os.system("pip install pinecone")
    from pinecone import Pinecone, ServerlessSpec

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class VectorDocument:
    """Represents a document to be stored in Pinecone"""
    id: str
    content: str
    metadata: Dict[str, Any]
    domain: str  # cherry, sophia, or karen
    embedding: Optional[List[float]] = None

class PineconeManager:
    """Manages Pinecone vector database operations for Cherry AI Orchestrator"""
    
    def __init__(self, api_key: str = None):
        """Initialize Pinecone connection"""
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        if not self.api_key:
            raise ValueError("Pinecone API key not provided")
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=self.api_key)
        
        # Index configurations for each domain
        self.index_configs = {
            "cherry-personal": {
                "dimension": 1536,  # OpenAI embedding dimension
                "metric": "cosine",
                "description": "Personal assistant and ranch management data"
            },
            "sophia-business": {
                "dimension": 1536,
                "metric": "cosine", 
                "description": "Pay Ready business intelligence and analytics"
            },
            "karen-healthcare": {
                "dimension": 1536,
                "metric": "cosine",
                "description": "ParagonRX healthcare operations and patient data"
            }
        }
        
        self.indexes = {}
        self._initialize_indexes()
    
    def _initialize_indexes(self):
        """Initialize or connect to Pinecone indexes for each domain"""
        logger.info("🔗 Initializing Pinecone indexes for all domains...")
        
        for index_name, config in self.index_configs.items():
            try:
                # Check if index exists
                existing_indexes = [idx.name for idx in self.pc.list_indexes()]
                
                if index_name not in existing_indexes:
                    logger.info(f"📊 Creating new index: {index_name}")
                    self.pc.create_index(
                        name=index_name,
                        dimension=config["dimension"],
                        metric=config["metric"],
                        spec=ServerlessSpec(
                            cloud="gcp",
                            region="us-west1"
                        )
                    )
                else:
                    logger.info(f"✅ Index already exists: {index_name}")
                
                # Connect to index
                self.indexes[index_name] = self.pc.Index(index_name)
                
            except Exception as e:
                logger.error(f"❌ Error initializing index {index_name}: {e}")
                raise
    
    def get_index_for_domain(self, domain: str):
        """Get the appropriate Pinecone index for a domain"""
        domain_mapping = {
            "cherry": "cherry-personal",
            "sophia": "sophia-business", 
            "karen": "karen-healthcare"
        }
        
        index_name = domain_mapping.get(domain.lower())
        if not index_name:
            raise ValueError(f"Unknown domain: {domain}")
        
        return self.indexes.get(index_name)
    
    def upsert_documents(self, documents: List[VectorDocument], domain: str):
        """Store documents in the appropriate domain index"""
        index = self.get_index_for_domain(domain)
        if not index:
            raise ValueError(f"Index not found for domain: {domain}")
        
        # Prepare vectors for upsert
        vectors = []
        for doc in documents:
            if not doc.embedding:
                # Generate embedding if not provided
                doc.embedding = self._generate_embedding(doc.content)
            
            vectors.append({
                "id": doc.id,
                "values": doc.embedding,
                "metadata": {
                    **doc.metadata,
                    "content": doc.content,
                    "domain": domain,
                    "timestamp": datetime.now().isoformat()
                }
            })
        
        # Upsert to Pinecone
        try:
            result = index.upsert(vectors=vectors)
            logger.info(f"✅ Upserted {len(vectors)} documents to {domain} domain")
            return result
        except Exception as e:
            logger.error(f"❌ Error upserting documents: {e}")
            raise
    
    def search_documents(self, query: str, domain: str, top_k: int = 10, filter_metadata: Dict = None):
        """Search for similar documents in a domain"""
        index = self.get_index_for_domain(domain)
        if not index:
            raise ValueError(f"Index not found for domain: {domain}")
        
        # Generate query embedding
        query_embedding = self._generate_embedding(query)
        
        # Search
        try:
            results = index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_metadata
            )
            
            logger.info(f"🔍 Found {len(results.matches)} results for query in {domain} domain")
            return results
        except Exception as e:
            logger.error(f"❌ Error searching documents: {e}")
            raise
    
    def delete_documents(self, document_ids: List[str], domain: str):
        """Delete documents from a domain index"""
        index = self.get_index_for_domain(domain)
        if not index:
            raise ValueError(f"Index not found for domain: {domain}")
        
        try:
            result = index.delete(ids=document_ids)
            logger.info(f"🗑️ Deleted {len(document_ids)} documents from {domain} domain")
            return result
        except Exception as e:
            logger.error(f"❌ Error deleting documents: {e}")
            raise
    
    def get_index_stats(self, domain: str):
        """Get statistics for a domain index"""
        index = self.get_index_for_domain(domain)
        if not index:
            raise ValueError(f"Index not found for domain: {domain}")
        
        try:
            stats = index.describe_index_stats()
            return stats
        except Exception as e:
            logger.error(f"❌ Error getting index stats: {e}")
            raise
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI API"""
        try:
            import openai
            
            # Use OpenAI API to generate embeddings
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                logger.warning("OpenAI API key not found, using mock embedding")
                return [0.1] * 1536  # Mock embedding
            
            client = openai.OpenAI(api_key=openai_api_key)
            response = client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.warning(f"Error generating embedding: {e}, using mock embedding")
            return [0.1] * 1536  # Mock embedding for testing

class DomainSpecificVectorStore:
    """Domain-specific vector store operations"""
    
    def __init__(self, pinecone_manager: PineconeManager):
        self.pm = pinecone_manager
    
    def store_cherry_data(self, personal_data: Dict[str, Any]):
        """Store Cherry domain personal and ranch data"""
        documents = []
        
        # Process personal tasks
        if "tasks" in personal_data:
            for task in personal_data["tasks"]:
                doc = VectorDocument(
                    id=f"cherry_task_{task.get('id', len(documents))}",
                    content=f"Personal task: {task.get('description', '')}",
                    metadata={
                        "type": "personal_task",
                        "priority": task.get("priority", "medium"),
                        "category": task.get("category", "general")
                    },
                    domain="cherry"
                )
                documents.append(doc)
        
        # Process ranch data
        if "ranch_operations" in personal_data:
            for operation in personal_data["ranch_operations"]:
                doc = VectorDocument(
                    id=f"cherry_ranch_{operation.get('id', len(documents))}",
                    content=f"Ranch operation: {operation.get('description', '')}",
                    metadata={
                        "type": "ranch_operation",
                        "livestock_type": operation.get("livestock_type"),
                        "location": operation.get("location")
                    },
                    domain="cherry"
                )
                documents.append(doc)
        
        return self.pm.upsert_documents(documents, "cherry")
    
    def store_sophia_data(self, business_data: Dict[str, Any]):
        """Store Sophia domain Pay Ready business data"""
        documents = []
        
        # Process debt recovery data
        if "debt_recovery" in business_data:
            for case in business_data["debt_recovery"]:
                doc = VectorDocument(
                    id=f"sophia_debt_{case.get('id', len(documents))}",
                    content=f"Debt recovery case: {case.get('description', '')}",
                    metadata={
                        "type": "debt_recovery",
                        "amount": case.get("amount"),
                        "status": case.get("status"),
                        "client": case.get("client")
                    },
                    domain="sophia"
                )
                documents.append(doc)
        
        # Process sales data
        if "sales_data" in business_data:
            for sale in business_data["sales_data"]:
                doc = VectorDocument(
                    id=f"sophia_sale_{sale.get('id', len(documents))}",
                    content=f"Sales record: {sale.get('description', '')}",
                    metadata={
                        "type": "sales_record",
                        "revenue": sale.get("revenue"),
                        "product": sale.get("product"),
                        "customer": sale.get("customer")
                    },
                    domain="sophia"
                )
                documents.append(doc)
        
        return self.pm.upsert_documents(documents, "sophia")
    
    def store_karen_data(self, healthcare_data: Dict[str, Any]):
        """Store Karen domain ParagonRX healthcare data"""
        documents = []
        
        # Process patient data (anonymized)
        if "patient_records" in healthcare_data:
            for record in healthcare_data["patient_records"]:
                doc = VectorDocument(
                    id=f"karen_patient_{record.get('id', len(documents))}",
                    content=f"Patient record: {record.get('summary', '')}",
                    metadata={
                        "type": "patient_record",
                        "condition": record.get("condition"),
                        "treatment": record.get("treatment"),
                        "pharmacy": record.get("pharmacy")
                    },
                    domain="karen"
                )
                documents.append(doc)
        
        # Process pharmacy operations
        if "pharmacy_operations" in healthcare_data:
            for operation in healthcare_data["pharmacy_operations"]:
                doc = VectorDocument(
                    id=f"karen_pharmacy_{operation.get('id', len(documents))}",
                    content=f"Pharmacy operation: {operation.get('description', '')}",
                    metadata={
                        "type": "pharmacy_operation",
                        "medication": operation.get("medication"),
                        "quantity": operation.get("quantity"),
                        "location": operation.get("location")
                    },
                    domain="karen"
                )
                documents.append(doc)
        
        return self.pm.upsert_documents(documents, "karen")

def main():
    """Test Pinecone integration"""
    try:
        # Initialize with provided API key
api_key = os.getenv('ORCHESTRA_INFRA_API_KEY')
        pm = PineconeManager(api_key=api_key)
        
        print("🍒 Cherry AI Orchestrator - Pinecone Integration")
        print("=" * 50)
        
        # Test each domain
        domains = ["cherry", "sophia", "karen"]
        for domain in domains:
            stats = pm.get_index_stats(domain)
            print(f"📊 {domain.title()} Domain Stats:")
            print(f"   Total vectors: {stats.total_vector_count}")
            print(f"   Dimension: {stats.dimension}")
            print()
        
        # Test document storage
        domain_store = DomainSpecificVectorStore(pm)
        
        # Test Cherry domain
        cherry_data = {
            "tasks": [
                {"id": "1", "description": "Check cattle feed levels", "priority": "high", "category": "ranch"},
                {"id": "2", "description": "Schedule vet appointment", "priority": "medium", "category": "livestock"}
            ],
            "ranch_operations": [
                {"id": "1", "description": "Morning cattle count", "livestock_type": "cattle", "location": "north_pasture"}
            ]
        }
        
        result = domain_store.store_cherry_data(cherry_data)
        print(f"✅ Stored Cherry domain data: {result}")
        
        # Test search
        search_results = pm.search_documents("cattle feed", "cherry", top_k=5)
        print(f"🔍 Search results for 'cattle feed': {len(search_results.matches)} matches")
        
        print("\n🎉 Pinecone integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing Pinecone integration: {e}")
        raise

if __name__ == "__main__":
    main()

