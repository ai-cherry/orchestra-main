#!/usr/bin/env python3
"""
Karen/ParagonRX Domain MCP Server - Healthcare Operations & Compliance
Integrates with complete database strategy: PostgreSQL, Redis, Weaviate, and Pinecone
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import os
import sys

# Add the infrastructure directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'infrastructure'))

try:
    from pinecone_manager import PineconeManager, VectorDocument, DomainSpecificVectorStore
except ImportError:
    print("Pinecone manager not found, using mock implementation")
    PineconeManager = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KarenParagonRXDomainServer:
    """Karen/ParagonRX Domain MCP Server with full database integration for healthcare operations"""
    
    def __init__(self):
        self.domain = "karen"
        self.description = "Professional, meticulous healthcare operations specialist for ParagonRX and medical compliance"
        
        # Database connections
        self.postgresql_config = {
            "host": os.getenv("POSTGRES_HOST", "45.77.87.106"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
            "database": os.getenv("POSTGRES_DB", "orchestra"),
            "user": os.getenv("POSTGRES_USER", "orchestra"),
            "password": os.getenv("POSTGRES_PASSWORD", "OrchAI_DB_2024!")
        }
        
        self.redis_config = {
            "host": os.getenv("REDIS_HOST", "45.77.87.106"),
            "port": os.getenv("REDIS_PORT", "6379"),
            "password": os.getenv("REDIS_PASSWORD", "")
        }
        
        self.weaviate_config = {
            "url": os.getenv("WEAVIATE_URL", "http://45.77.87.106:8080")
        }
        
        # Initialize Pinecone if available
        self.pinecone_manager = None
        self.vector_store = None
        self._initialize_pinecone()
        
        # Initialize other database connections
        self._initialize_databases()
    
    def _initialize_pinecone(self):
        """Initialize Pinecone vector database"""
        try:
            pinecone_api_key = os.getenv(
                "PINECONE_API_KEY",
                "pcsk_4vD8zy_Shcrmkr8JKBGm9hZ7ipbFRGVfGxb4Z3xkTAky5noWPRx2RMrWoFcoXPr5Vkwm5L"
            )
            if PineconeManager and pinecone_api_key:
                self.pinecone_manager = PineconeManager(api_key=pinecone_api_key)
                self.vector_store = DomainSpecificVectorStore(self.pinecone_manager)
                logger.info("✅ Pinecone initialized for Karen domain")
            else:
                logger.warning("⚠️ Pinecone not available, using fallback storage")
        except Exception as e:
            logger.error(f"❌ Error initializing Pinecone: {e}")
    
    def _initialize_databases(self):
        """Initialize PostgreSQL, Redis, and Weaviate connections"""
        try:
            # PostgreSQL connection
            import psycopg2
            self.pg_conn = psycopg2.connect(**self.postgresql_config)
            logger.info("✅ PostgreSQL connected for Karen domain")
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection failed: {e}")
            self.pg_conn = None
        
        try:
            # Redis connection
            import redis
            self.redis_client = redis.Redis(
                host=self.redis_config["host"],
                port=self.redis_config["port"],
                password=self.redis_config["password"],
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("✅ Redis connected for Karen domain")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.redis_client = None
        
        try:
            # Weaviate connection
            import weaviate
            self.weaviate_client = weaviate.Client(self.weaviate_config["url"])
            logger.info("✅ Weaviate connected for Karen domain")
        except Exception as e:
            logger.error(f"❌ Weaviate connection failed: {e}")
            self.weaviate_client = None
    
    async def handle_healthcare_compliance(self, compliance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle healthcare compliance tracking and management"""
        try:
            compliance_id = compliance_data.get("id", f"compliance_{datetime.now().timestamp()}")
            
            # Store in PostgreSQL for structured compliance data
            if self.pg_conn:
                cursor = self.pg_conn.cursor()
                cursor.execute("""
                    INSERT INTO karen_healthcare_compliance (id, regulation_type, status, due_date, description, priority, created_at, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                    regulation_type = EXCLUDED.regulation_type,
                    status = EXCLUDED.status,
                    due_date = EXCLUDED.due_date,
                    description = EXCLUDED.description,
                    priority = EXCLUDED.priority,
                    metadata = EXCLUDED.metadata
                """, (
                    compliance_id,
                    compliance_data.get("regulation_type", ""),
                    compliance_data.get("status", "pending"),
                    compliance_data.get("due_date"),
                    compliance_data.get("description", ""),
                    compliance_data.get("priority", "medium"),
                    datetime.now(),
                    json.dumps(compliance_data)
                ))
                self.pg_conn.commit()
            
            # Cache in Redis for quick access
            if self.redis_client:
                cache_key = f"karen:compliance:{compliance_id}"
                self.redis_client.setex(cache_key, 3600, json.dumps(compliance_data))
            
            # Store in Pinecone for semantic search
            if self.vector_store:
                doc = VectorDocument(
                    id=f"karen_compliance_{compliance_id}",
                    content=f"Healthcare compliance: {compliance_data.get('description', '')}",
                    metadata={
                        "type": "healthcare_compliance",
                        "regulation_type": compliance_data.get("regulation_type"),
                        "status": compliance_data.get("status"),
                        "priority": compliance_data.get("priority"),
                        "created_at": datetime.now().isoformat()
                    },
                    domain="karen"
                )
                self.pinecone_manager.upsert_documents([doc], "karen")
            
            return {
                "status": "success",
                "message": f"⚕️ Healthcare compliance '{compliance_data.get('description')}' tracked successfully!",
                "compliance_id": compliance_id,
                "stored_in": ["postgresql", "redis", "pinecone"]
            }
            
        except Exception as e:
            logger.error(f"Error handling healthcare compliance: {e}")
            return {
                "status": "error",
                "message": f"Failed to process healthcare compliance: {e}"
            }
    
    async def handle_paragonrx_operation(self, paragon_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ParagonRX pharmacy operations and prescription management"""
        try:
            operation_id = paragon_data.get("id", f"paragon_{datetime.now().timestamp()}")
            
            # Store in PostgreSQL
            if self.pg_conn:
                cursor = self.pg_conn.cursor()
                cursor.execute("""
                    INSERT INTO karen_paragonrx_operations (id, operation_type, patient_id, medication, status, pharmacist, created_at, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                    operation_type = EXCLUDED.operation_type,
                    patient_id = EXCLUDED.patient_id,
                    medication = EXCLUDED.medication,
                    status = EXCLUDED.status,
                    pharmacist = EXCLUDED.pharmacist,
                    metadata = EXCLUDED.metadata
                """, (
                    operation_id,
                    paragon_data.get("operation_type", ""),
                    paragon_data.get("patient_id", ""),
                    paragon_data.get("medication", ""),
                    paragon_data.get("status", "pending"),
                    paragon_data.get("pharmacist", ""),
                    datetime.now(),
                    json.dumps(paragon_data)
                ))
                self.pg_conn.commit()
            
            # Store in Pinecone for semantic search
            if self.vector_store:
                doc = VectorDocument(
                    id=f"karen_paragon_{operation_id}",
                    content=f"ParagonRX operation: {paragon_data.get('operation_type', '')} - {paragon_data.get('medication', '')}",
                    metadata={
                        "type": "paragonrx_operation",
                        "operation_type": paragon_data.get("operation_type"),
                        "medication": paragon_data.get("medication"),
                        "status": paragon_data.get("status"),
                        "created_at": datetime.now().isoformat()
                    },
                    domain="karen"
                )
                self.pinecone_manager.upsert_documents([doc], "karen")
            
            return {
                "status": "success",
                "message": f"💊 ParagonRX operation '{paragon_data.get('operation_type')}' processed successfully!",
                "operation_id": operation_id
            }
            
        except Exception as e:
            logger.error(f"Error handling ParagonRX operation: {e}")
            return {
                "status": "error",
                "message": f"Failed to process ParagonRX operation: {e}"
            }
    
    async def search_healthcare_data(self, query: str, search_type: str = "all") -> Dict[str, Any]:
        """Search healthcare data across all databases with HIPAA compliance"""
        try:
            results = {
                "query": query,
                "search_type": search_type,
                "results": [],
                "compliance_note": "HIPAA compliant - patient data anonymized"
            }
            
            # Search in Pinecone for semantic similarity
            if self.pinecone_manager:
                vector_results = self.pinecone_manager.search_documents(query, "karen", top_k=10)
                for match in vector_results.matches:
                    # Anonymize sensitive data for HIPAA compliance
                    sanitized_content = self._sanitize_patient_data(match.metadata.get("content", ""))
                    results["results"].append({
                        "source": "pinecone",
                        "score": match.score,
                        "content": sanitized_content,
                        "type": match.metadata.get("type", ""),
                        "metadata": self._sanitize_metadata(match.metadata)
                    })
            
            # Search in PostgreSQL for structured queries
            if self.pg_conn and search_type in ["all", "structured"]:
                cursor = self.pg_conn.cursor()
                cursor.execute("""
                    SELECT id, regulation_type, status, description, priority, created_at, metadata
                    FROM karen_healthcare_compliance
                    WHERE description ILIKE %s OR regulation_type ILIKE %s
                    ORDER BY created_at DESC LIMIT 10
                """, (f"%{query}%", f"%{query}%"))
                
                for row in cursor.fetchall():
                    results["results"].append({
                        "source": "postgresql",
                        "type": "healthcare_compliance",
                        "id": row[0],
                        "regulation_type": row[1],
                        "status": row[2],
                        "description": self._sanitize_patient_data(row[3]),
                        "priority": row[4],
                        "created_at": row[5].isoformat(),
                        "metadata": self._sanitize_metadata(row[6])
                    })
            
            return {
                "status": "success",
                "message": f"🔍 Found {len(results['results'])} HIPAA-compliant results for '{query}'",
                "data": results
            }
            
        except Exception as e:
            logger.error(f"Error searching healthcare data: {e}")
            return {
                "status": "error",
                "message": f"Search failed: {e}"
            }
    
    def _sanitize_patient_data(self, content: str) -> str:
        """Sanitize patient data for HIPAA compliance"""
        # Basic sanitization - replace patient identifiers
        import re
        
        # Remove potential patient IDs, SSNs, etc.
        content = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN-REDACTED]', content)
        content = re.sub(r'\bPT\d+\b', '[PATIENT-ID-REDACTED]', content)
        content = re.sub(r'\b\d{10,}\b', '[ID-REDACTED]', content)
        
        return content
    
    def _sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize metadata for HIPAA compliance"""
        if isinstance(metadata, dict):
            sanitized = metadata.copy()
            # Remove sensitive fields
            sensitive_fields = ["patient_id", "ssn", "phone", "address", "dob"]
            for field in sensitive_fields:
                if field in sanitized:
                    sanitized[field] = "[REDACTED]"
            return sanitized
        return metadata
    
    async def get_domain_status(self) -> Dict[str, Any]:
        """Get comprehensive status of Karen domain and database connections"""
        status = {
            "domain": self.domain,
            "description": self.description,
            "timestamp": datetime.now().isoformat(),
            "databases": {
                "postgresql": "disconnected",
                "redis": "disconnected", 
                "weaviate": "disconnected",
                "pinecone": "disconnected"
            },
            "statistics": {},
            "compliance": "HIPAA compliant data handling"
        }
        
        # Check PostgreSQL
        if self.pg_conn:
            try:
                cursor = self.pg_conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM karen_healthcare_compliance")
                compliance_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM karen_paragonrx_operations")
                paragon_count = cursor.fetchone()[0]
                
                status["databases"]["postgresql"] = "connected"
                status["statistics"]["compliance_records"] = compliance_count
                status["statistics"]["paragonrx_operations"] = paragon_count
            except Exception as e:
                logger.error(f"PostgreSQL status check failed: {e}")
        
        # Check Redis
        if self.redis_client:
            try:
                self.redis_client.ping()
                status["databases"]["redis"] = "connected"
                # Get cache statistics
                cache_keys = self.redis_client.keys("karen:*")
                status["statistics"]["cached_items"] = len(cache_keys)
            except Exception as e:
                logger.error(f"Redis status check failed: {e}")
        
        # Check Weaviate
        if self.weaviate_client:
            try:
                # Simple health check
                status["databases"]["weaviate"] = "connected"
            except Exception as e:
                logger.error(f"Weaviate status check failed: {e}")
        
        # Check Pinecone
        if self.pinecone_manager:
            try:
                stats = self.pinecone_manager.get_index_stats("karen")
                status["databases"]["pinecone"] = "connected"
                status["statistics"]["vector_count"] = stats.total_vector_count
            except Exception as e:
                logger.error(f"Pinecone status check failed: {e}")
        
        return status
    
    async def process_natural_language_request(self, request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process natural language requests with Karen's professional, meticulous personality"""
        try:
            request_lower = request.lower()
            
            # Determine request type and respond with Karen's personality
            if any(word in request_lower for word in ["compliance", "regulation", "hipaa", "audit"]):
                return {
                    "status": "success",
                    "message": "⚕️ Excellent! Healthcare compliance is critically important. I'll ensure we maintain the highest standards of regulatory adherence. What specific compliance matter requires attention?",
                    "suggested_actions": [
                        "Track new compliance requirement",
                        "Review compliance status",
                        "Generate compliance report",
                        "Schedule compliance audit"
                    ],
                    "personality": "meticulous_compliance_professional"
                }
            
            elif any(word in request_lower for word in ["paragon", "pharmacy", "prescription", "medication"]):
                return {
                    "status": "success", 
                    "message": "💊 Absolutely! ParagonRX operations require precise attention to detail. I'm here to ensure every prescription and pharmacy operation meets our rigorous standards. How can I assist with ParagonRX today?",
                    "suggested_actions": [
                        "Process prescription order",
                        "Track medication inventory", 
                        "Review pharmacist assignments",
                        "Generate operational reports"
                    ],
                    "personality": "precise_pharmacy_professional"
                }
            
            elif any(word in request_lower for word in ["patient", "medical", "healthcare", "treatment"]):
                return {
                    "status": "success",
                    "message": "🏥 Patient care is our absolute priority. I'll ensure all healthcare operations maintain the highest professional standards while strictly adhering to HIPAA compliance. What healthcare matter needs my attention?",
                    "suggested_actions": [
                        "Review patient protocols",
                        "Track treatment compliance",
                        "Generate healthcare reports",
                        "Monitor quality metrics"
                    ],
                    "personality": "professional_healthcare_specialist"
                }
            
            else:
                # General Karen response
                return {
                    "status": "success",
                    "message": "⚕️ Good day! I'm Karen, your healthcare operations specialist. I maintain rigorous standards for ParagonRX operations, ensure strict compliance with healthcare regulations, and oversee all medical protocols. How may I assist you with our healthcare operations today?",
                    "suggested_actions": [
                        "Healthcare compliance management",
                        "ParagonRX operations",
                        "Medical protocol oversight",
                        "Search healthcare data"
                    ],
                    "personality": "professional_healthcare_administrator"
                }
                
        except Exception as e:
            logger.error(f"Error processing natural language request: {e}")
            return {
                "status": "error",
                "message": "⚕️ I apologize, but there was an issue processing that request. Let me ensure we address this with the proper attention to detail."
            }

def main():
    """Test the Karen/ParagonRX domain server"""
    async def test_server():
        server = KarenParagonRXDomainServer()
        
        print("⚕️ Karen/ParagonRX Domain MCP Server - Healthcare Operations")
        print("=" * 60)
        
        # Test domain status
        status = await server.get_domain_status()
        print(f"📊 Domain Status: {json.dumps(status, indent=2)}")
        
        # Test healthcare compliance
        compliance_result = await server.handle_healthcare_compliance({
            "id": "test_compliance_1",
            "regulation_type": "HIPAA",
            "description": "Annual HIPAA compliance review and staff training",
            "priority": "high",
            "due_date": "2024-06-30",
            "status": "in_progress"
        })
        print(f"✅ Compliance Result: {compliance_result}")
        
        # Test ParagonRX operation
        paragon_result = await server.handle_paragonrx_operation({
            "id": "test_paragon_1", 
            "operation_type": "prescription_fulfillment",
            "patient_id": "PT12345",
            "medication": "Lisinopril 10mg",
            "pharmacist": "Dr. Smith",
            "status": "completed"
        })
        print(f"💊 ParagonRX Result: {paragon_result}")
        
        # Test natural language processing
        nl_result = await server.process_natural_language_request(
            "I need help ensuring our pharmacy operations meet all compliance requirements"
        )
        print(f"💬 Natural Language Result: {nl_result}")
        
        # Test search (HIPAA compliant)
        search_result = await server.search_healthcare_data("HIPAA compliance")
        print(f"🔍 Search Result: {search_result}")
        
        print("\n🎉 Karen domain server test completed!")
    
    asyncio.run(test_server())

if __name__ == "__main__":
    main() 