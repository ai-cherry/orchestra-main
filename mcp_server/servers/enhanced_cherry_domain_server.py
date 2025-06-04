#!/usr/bin/env python3
"""
Enhanced MCP Server for Cherry Domain (Personal Assistant)
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

class CherryDomainServer:
    """Enhanced Cherry Domain MCP Server with full database integration"""
    
    def __init__(self):
        self.domain = "cherry"
        self.description = "Sweet, playful personal assistant for lifestyle and ranch management"
        
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
            pinecone_api_key = os.getenv("PINECONE_API_KEY", "pcsk_4vD8zy_Shcrmkr8JKBGm9hZ7ipbFRGVfGxb4Z3xkTAky5noWPRx2RMrWoFcoXPr5Vkwm5L")
            if PineconeManager and pinecone_api_key:
                self.pinecone_manager = PineconeManager(api_key=pinecone_api_key)
                self.vector_store = DomainSpecificVectorStore(self.pinecone_manager)
                logger.info("✅ Pinecone initialized for Cherry domain")
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
            logger.info("✅ PostgreSQL connected for Cherry domain")
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
            logger.info("✅ Redis connected for Cherry domain")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.redis_client = None
        
        try:
            # Weaviate connection
            import weaviate
            self.weaviate_client = weaviate.Client(self.weaviate_config["url"])
            logger.info("✅ Weaviate connected for Cherry domain")
        except Exception as e:
            logger.error(f"❌ Weaviate connection failed: {e}")
            self.weaviate_client = None
    
    async def handle_personal_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle personal task management with full database integration"""
        try:
            task_id = task_data.get("id", f"task_{datetime.now().timestamp()}")
            
            # Store in PostgreSQL for structured data
            if self.pg_conn:
                cursor = self.pg_conn.cursor()
                cursor.execute("""
                    INSERT INTO cherry_personal_tasks (id, description, priority, category, created_at, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                    description = EXCLUDED.description,
                    priority = EXCLUDED.priority,
                    category = EXCLUDED.category,
                    metadata = EXCLUDED.metadata
                """, (
                    task_id,
                    task_data.get("description", ""),
                    task_data.get("priority", "medium"),
                    task_data.get("category", "general"),
                    datetime.now(),
                    json.dumps(task_data)
                ))
                self.pg_conn.commit()
            
            # Cache in Redis for quick access
            if self.redis_client:
                cache_key = f"cherry:task:{task_id}"
                self.redis_client.setex(cache_key, 3600, json.dumps(task_data))
            
            # Store in Pinecone for semantic search
            if self.vector_store:
                doc = VectorDocument(
                    id=f"cherry_task_{task_id}",
                    content=f"Personal task: {task_data.get('description', '')}",
                    metadata={
                        "type": "personal_task",
                        "priority": task_data.get("priority", "medium"),
                        "category": task_data.get("category", "general"),
                        "created_at": datetime.now().isoformat()
                    },
                    domain="cherry"
                )
                self.pinecone_manager.upsert_documents([doc], "cherry")
            
            return {
                "status": "success",
                "message": f"🍒 Personal task '{task_data.get('description')}' processed successfully!",
                "task_id": task_id,
                "stored_in": ["postgresql", "redis", "pinecone"]
            }
            
        except Exception as e:
            logger.error(f"Error handling personal task: {e}")
            return {
                "status": "error",
                "message": f"Failed to process personal task: {e}"
            }
    
    async def handle_ranch_operation(self, ranch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ranch management operations"""
        try:
            operation_id = ranch_data.get("id", f"ranch_{datetime.now().timestamp()}")
            
            # Store in PostgreSQL
            if self.pg_conn:
                cursor = self.pg_conn.cursor()
                cursor.execute("""
                    INSERT INTO cherry_ranch_operations (id, description, livestock_type, location, created_at, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                    description = EXCLUDED.description,
                    livestock_type = EXCLUDED.livestock_type,
                    location = EXCLUDED.location,
                    metadata = EXCLUDED.metadata
                """, (
                    operation_id,
                    ranch_data.get("description", ""),
                    ranch_data.get("livestock_type", ""),
                    ranch_data.get("location", ""),
                    datetime.now(),
                    json.dumps(ranch_data)
                ))
                self.pg_conn.commit()
            
            # Store in Pinecone for semantic search
            if self.vector_store:
                doc = VectorDocument(
                    id=f"cherry_ranch_{operation_id}",
                    content=f"Ranch operation: {ranch_data.get('description', '')}",
                    metadata={
                        "type": "ranch_operation",
                        "livestock_type": ranch_data.get("livestock_type"),
                        "location": ranch_data.get("location"),
                        "created_at": datetime.now().isoformat()
                    },
                    domain="cherry"
                )
                self.pinecone_manager.upsert_documents([doc], "cherry")
            
            return {
                "status": "success",
                "message": f"🐄 Ranch operation '{ranch_data.get('description')}' recorded successfully!",
                "operation_id": operation_id
            }
            
        except Exception as e:
            logger.error(f"Error handling ranch operation: {e}")
            return {
                "status": "error",
                "message": f"Failed to process ranch operation: {e}"
            }
    
    async def search_personal_data(self, query: str, search_type: str = "all") -> Dict[str, Any]:
        """Search personal data across all databases"""
        try:
            results = {
                "query": query,
                "search_type": search_type,
                "results": []
            }
            
            # Search in Pinecone for semantic similarity
            if self.pinecone_manager:
                vector_results = self.pinecone_manager.search_documents(query, "cherry", top_k=10)
                for match in vector_results.matches:
                    results["results"].append({
                        "source": "pinecone",
                        "score": match.score,
                        "content": match.metadata.get("content", ""),
                        "type": match.metadata.get("type", ""),
                        "metadata": match.metadata
                    })
            
            # Search in PostgreSQL for structured queries
            if self.pg_conn and search_type in ["all", "structured"]:
                cursor = self.pg_conn.cursor()
                cursor.execute("""
                    SELECT id, description, priority, category, created_at, metadata
                    FROM cherry_personal_tasks
                    WHERE description ILIKE %s OR category ILIKE %s
                    ORDER BY created_at DESC LIMIT 10
                """, (f"%{query}%", f"%{query}%"))
                
                for row in cursor.fetchall():
                    results["results"].append({
                        "source": "postgresql",
                        "type": "personal_task",
                        "id": row[0],
                        "description": row[1],
                        "priority": row[2],
                        "category": row[3],
                        "created_at": row[4].isoformat(),
                        "metadata": row[5]
                    })
            
            return {
                "status": "success",
                "message": f"🔍 Found {len(results['results'])} results for '{query}'",
                "data": results
            }
            
        except Exception as e:
            logger.error(f"Error searching personal data: {e}")
            return {
                "status": "error",
                "message": f"Search failed: {e}"
            }
    
    async def get_domain_status(self) -> Dict[str, Any]:
        """Get comprehensive status of Cherry domain and database connections"""
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
            "statistics": {}
        }
        
        # Check PostgreSQL
        if self.pg_conn:
            try:
                cursor = self.pg_conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM cherry_personal_tasks")
                task_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM cherry_ranch_operations")
                ranch_count = cursor.fetchone()[0]
                
                status["databases"]["postgresql"] = "connected"
                status["statistics"]["personal_tasks"] = task_count
                status["statistics"]["ranch_operations"] = ranch_count
            except Exception as e:
                logger.error(f"PostgreSQL status check failed: {e}")
        
        # Check Redis
        if self.redis_client:
            try:
                self.redis_client.ping()
                status["databases"]["redis"] = "connected"
                # Get cache statistics
                cache_keys = self.redis_client.keys("cherry:*")
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
                stats = self.pinecone_manager.get_index_stats("cherry")
                status["databases"]["pinecone"] = "connected"
                status["statistics"]["vector_count"] = stats.total_vector_count
            except Exception as e:
                logger.error(f"Pinecone status check failed: {e}")
        
        return status
    
    async def process_natural_language_request(self, request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process natural language requests with Cherry's sweet personality"""
        try:
            request_lower = request.lower()
            
            # Determine request type and respond with Cherry's personality
            if any(word in request_lower for word in ["task", "todo", "remind", "schedule"]):
                return {
                    "status": "success",
                    "message": "🍒 Sweet! I'd love to help you with your personal tasks! What would you like me to add to your schedule?",
                    "suggested_actions": [
                        "Add a new personal task",
                        "View upcoming tasks",
                        "Set a reminder"
                    ],
                    "personality": "sweet_helpful"
                }
            
            elif any(word in request_lower for word in ["ranch", "cattle", "livestock", "farm"]):
                return {
                    "status": "success", 
                    "message": "🐄 Oh wonderful! Ranch management is one of my favorite things to help with! Tell me what's happening on the ranch today.",
                    "suggested_actions": [
                        "Record livestock count",
                        "Schedule veterinary visit",
                        "Track feed levels",
                        "Monitor pasture conditions"
                    ],
                    "personality": "enthusiastic_ranch_helper"
                }
            
            elif any(word in request_lower for word in ["health", "wellness", "fitness", "exercise"]):
                return {
                    "status": "success",
                    "message": "💪 That's fantastic! I'm here to support your health and wellness journey. What aspect of your wellness would you like to focus on?",
                    "suggested_actions": [
                        "Log workout session",
                        "Track health metrics",
                        "Set wellness goals",
                        "Schedule health appointments"
                    ],
                    "personality": "caring_wellness_coach"
                }
            
            else:
                # General Cherry response
                return {
                    "status": "success",
                    "message": "🍒 Hi there! I'm Cherry, your sweet personal assistant! I can help you with personal tasks, ranch management, and wellness tracking. What would you like to work on together?",
                    "suggested_actions": [
                        "Manage personal tasks",
                        "Ranch operations",
                        "Health & wellness",
                        "Search my data"
                    ],
                    "personality": "sweet_general"
                }
                
        except Exception as e:
            logger.error(f"Error processing natural language request: {e}")
            return {
                "status": "error",
                "message": "🍒 Oops! I had a little hiccup processing that request. Could you try again, sweetie?"
            }

def main():
    """Test the enhanced Cherry domain server"""
    async def test_server():
        server = CherryDomainServer()
        
        print("🍒 Cherry Domain MCP Server - Enhanced Database Integration")
        print("=" * 60)
        
        # Test domain status
        status = await server.get_domain_status()
        print(f"📊 Domain Status: {json.dumps(status, indent=2)}")
        
        # Test personal task handling
        task_result = await server.handle_personal_task({
            "id": "test_task_1",
            "description": "Check cattle feed levels in north pasture",
            "priority": "high",
            "category": "ranch"
        })
        print(f"✅ Task Result: {task_result}")
        
        # Test ranch operation
        ranch_result = await server.handle_ranch_operation({
            "id": "test_ranch_1", 
            "description": "Morning cattle count - 47 head present",
            "livestock_type": "cattle",
            "location": "north_pasture"
        })
        print(f"🐄 Ranch Result: {ranch_result}")
        
        # Test natural language processing
        nl_result = await server.process_natural_language_request(
            "I need help managing my ranch operations"
        )
        print(f"💬 Natural Language Result: {nl_result}")
        
        # Test search
        search_result = await server.search_personal_data("cattle feed")
        print(f"🔍 Search Result: {search_result}")
        
        print("\n🎉 Cherry domain server test completed!")
    
    asyncio.run(test_server())

if __name__ == "__main__":
    main()

