#!/usr/bin/env python3
"""
Enterprise Database Layer Manager
Comprehensive multi-database architecture for Cherry AI Orchestrator

Supports:
- Pinecone: Ultra-fast vector search
- Weaviate: Metadata-rich hybrid queries  
- Redis: High-speed caching and session management
- PostgreSQL: Structured data and metadata

Author: Cherry AI Team
Version: 1.0.0
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import hashlib

# Vector Database Imports
try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    print("Warning: Pinecone not available. Install with: pip install pinecone")

try:
    import weaviate
    from weaviate.classes.config import Configure
    WEAVIATE_AVAILABLE = True
except ImportError:
    WEAVIATE_AVAILABLE = False
    print("Warning: Weaviate not available. Install with: pip install weaviate-client")

# Traditional Database Imports
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Warning: Redis not available. Install with: pip install redis")

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    import psycopg2.pool
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False
    print("Warning: PostgreSQL not available. Install with: pip install psycopg2-binary")

# Embedding and NLP
try:
    import openai
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("Warning: Embeddings not available. Install with: pip install openai sentence-transformers")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Configuration management for all database connections"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), 'database_config.json')
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load database configuration from file or environment"""
        default_config = {
            "pinecone": {
                "api_key": os.getenv("PINECONE_API_KEY", ""),
                "environment": os.getenv("PINECONE_ENVIRONMENT", "us-east-1-aws"),
                "indexes": {
                    "cherry": "cherry-personal-index",
                    "sophia": "sophia-business-index", 
                    "karen": "karen-healthcare-index"
                },
                "dimension": 1536,
                "metric": "cosine"
            },
            "weaviate": {
                "url": os.getenv("WEAVIATE_URL", "http://45.77.87.106:8080"),
                "api_key": os.getenv("WEAVIATE_API_KEY", ""),
                "classes": {
                    "cherry": "CherryPersonal",
                    "sophia": "SophiaBusiness",
                    "karen": "KarenHealthcare"
                }
            },
            "redis": {
                "host": os.getenv("REDIS_HOST", "45.77.87.106"),
                "port": int(os.getenv("REDIS_PORT", "6379")),
                "password": os.getenv("REDIS_PASSWORD", ""),
                "db": 0,
                "decode_responses": True
            },
            "postgresql": {
                "host": os.getenv("POSTGRES_HOST", "45.77.87.106"),
                "port": int(os.getenv("POSTGRES_PORT", "5432")),
                "database": os.getenv("POSTGRES_DB", "orchestra"),
                "user": os.getenv("POSTGRES_USER", "orchestra"),
                "password": os.getenv("POSTGRES_PASSWORD", "OrchAI_DB_2024!"),
                "pool_size": 10,
                "max_overflow": 20
            },
            "embeddings": {
                "provider": "openai",  # or "sentence_transformers"
                "model": "text-embedding-ada-002",
                "dimension": 1536,
                "batch_size": 100
            }
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    file_config = json.load(f)
                    # Merge with defaults
                    for key, value in file_config.items():
                        if key in default_config and isinstance(value, dict):
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
            except Exception as e:
                logger.warning(f"Error loading config file: {e}")
        
        return default_config
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

class EmbeddingManager:
    """Manages text embeddings for vector databases"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider = config.get("provider", "openai")
        self.model = config.get("model", "text-embedding-ada-002")
        self.dimension = config.get("dimension", 1536)
        self.batch_size = config.get("batch_size", 100)
        
        if self.provider == "openai":
            openai.api_key = os.getenv("OPENAI_API_KEY")
        elif self.provider == "sentence_transformers":
            self.model_instance = SentenceTransformer(self.model)
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        return await self.embed_texts([text])[0]
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if self.provider == "openai":
            return await self._embed_openai(texts)
        elif self.provider == "sentence_transformers":
            return await self._embed_sentence_transformers(texts)
        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")
    
    async def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API"""
        embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            try:
                response = await openai.Embedding.acreate(
                    model=self.model,
                    input=batch
                )
                batch_embeddings = [item['embedding'] for item in response['data']]
                embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"OpenAI embedding error: {e}")
                # Fallback to zero vectors
                embeddings.extend([[0.0] * self.dimension] * len(batch))
        
        return embeddings
    
    async def _embed_sentence_transformers(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using sentence-transformers"""
        try:
            embeddings = self.model_instance.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Sentence transformers embedding error: {e}")
            return [[0.0] * self.dimension] * len(texts)

class PineconeManager:
    """Manages Pinecone vector database operations"""
    
    def __init__(self, config: Dict[str, Any]):
        if not PINECONE_AVAILABLE:
            raise ImportError("Pinecone not available")
        
        self.config = config
        self.api_key = config["api_key"]
        self.environment = config["environment"]
        self.indexes = config["indexes"]
        self.dimension = config["dimension"]
        self.metric = config["metric"]
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=self.api_key)
        self.index_connections = {}
    
    async def initialize_indexes(self):
        """Create and configure Pinecone indexes for each persona"""
        for persona, index_name in self.indexes.items():
            try:
                # Check if index exists
                existing_indexes = self.pc.list_indexes()
                if index_name not in [idx.name for idx in existing_indexes]:
                    # Create index
                    self.pc.create_index(
                        name=index_name,
                        dimension=self.dimension,
                        metric=self.metric,
                        spec=ServerlessSpec(
                            cloud='aws',
                            region=self.environment
                        )
                    )
                    logger.info(f"Created Pinecone index: {index_name}")
                
                # Connect to index
                self.index_connections[persona] = self.pc.Index(index_name)
                logger.info(f"Connected to Pinecone index: {index_name}")
                
            except Exception as e:
                logger.error(f"Error initializing Pinecone index {index_name}: {e}")
    
    async def upsert_vectors(self, persona: str, vectors: List[Dict[str, Any]]):
        """Insert or update vectors in Pinecone"""
        if persona not in self.index_connections:
            raise ValueError(f"No index connection for persona: {persona}")
        
        try:
            index = self.index_connections[persona]
            index.upsert(vectors=vectors)
            logger.info(f"Upserted {len(vectors)} vectors to {persona} index")
        except Exception as e:
            logger.error(f"Error upserting vectors to {persona}: {e}")
    
    async def query_vectors(self, persona: str, query_vector: List[float], 
                          top_k: int = 10, filter_dict: Optional[Dict] = None) -> Dict[str, Any]:
        """Query vectors from Pinecone"""
        if persona not in self.index_connections:
            raise ValueError(f"No index connection for persona: {persona}")
        
        try:
            index = self.index_connections[persona]
            results = index.query(
                vector=query_vector,
                top_k=top_k,
                filter=filter_dict,
                include_metadata=True
            )
            return results
        except Exception as e:
            logger.error(f"Error querying vectors from {persona}: {e}")
            return {"matches": []}

class WeaviateManager:
    """Manages Weaviate vector database operations"""
    
    def __init__(self, config: Dict[str, Any]):
        if not WEAVIATE_AVAILABLE:
            raise ImportError("Weaviate not available")
        
        self.config = config
        self.url = config["url"]
        self.api_key = config.get("api_key", "")
        self.classes = config["classes"]
        
        # Initialize Weaviate client
        auth_config = None
        if self.api_key:
            auth_config = weaviate.AuthApiKey(api_key=self.api_key)
        
        self.client = weaviate.Client(
            url=self.url,
            auth_client_secret=auth_config
        )
    
    async def initialize_schema(self):
        """Create Weaviate schema for each persona"""
        for persona, class_name in self.classes.items():
            try:
                # Check if class exists
                if not self.client.schema.exists(class_name):
                    # Define schema
                    schema = {
                        "class": class_name,
                        "description": f"Data for {persona} persona",
                        "vectorizer": "text2vec-openai",
                        "moduleConfig": {
                            "text2vec-openai": {
                                "model": "ada",
                                "modelVersion": "002",
                                "type": "text"
                            }
                        },
                        "properties": [
                            {
                                "name": "content",
                                "dataType": ["text"],
                                "description": "Main content text"
                            },
                            {
                                "name": "source",
                                "dataType": ["string"],
                                "description": "Source of the content"
                            },
                            {
                                "name": "timestamp",
                                "dataType": ["date"],
                                "description": "Creation timestamp"
                            },
                            {
                                "name": "metadata",
                                "dataType": ["object"],
                                "description": "Additional metadata"
                            },
                            {
                                "name": "persona",
                                "dataType": ["string"],
                                "description": "Associated persona"
                            },
                            {
                                "name": "file_type",
                                "dataType": ["string"],
                                "description": "Original file type"
                            },
                            {
                                "name": "chunk_index",
                                "dataType": ["int"],
                                "description": "Chunk index for large documents"
                            }
                        ]
                    }
                    
                    self.client.schema.create_class(schema)
                    logger.info(f"Created Weaviate class: {class_name}")
                else:
                    logger.info(f"Weaviate class already exists: {class_name}")
                    
            except Exception as e:
                logger.error(f"Error initializing Weaviate schema for {class_name}: {e}")
    
    async def add_objects(self, persona: str, objects: List[Dict[str, Any]]):
        """Add objects to Weaviate"""
        class_name = self.classes.get(persona)
        if not class_name:
            raise ValueError(f"No class defined for persona: {persona}")
        
        try:
            with self.client.batch as batch:
                for obj in objects:
                    batch.add_data_object(
                        data_object=obj,
                        class_name=class_name
                    )
            logger.info(f"Added {len(objects)} objects to {class_name}")
        except Exception as e:
            logger.error(f"Error adding objects to {class_name}: {e}")
    
    async def query_objects(self, persona: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Query objects from Weaviate"""
        class_name = self.classes.get(persona)
        if not class_name:
            raise ValueError(f"No class defined for persona: {persona}")
        
        try:
            result = (
                self.client.query
                .get(class_name, ["content", "source", "timestamp", "metadata"])
                .with_near_text({"concepts": [query]})
                .with_limit(limit)
                .do()
            )
            
            return result.get("data", {}).get("Get", {}).get(class_name, [])
        except Exception as e:
            logger.error(f"Error querying {class_name}: {e}")
            return []

class RedisManager:
    """Manages Redis caching and session operations"""
    
    def __init__(self, config: Dict[str, Any]):
        if not REDIS_AVAILABLE:
            raise ImportError("Redis not available")
        
        self.config = config
        self.client = redis.Redis(**config)
        
        # Test connection
        try:
            self.client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Redis connection error: {e}")
    
    async def cache_embedding(self, text: str, embedding: List[float], ttl: int = 3600):
        """Cache text embedding with TTL"""
        key = f"embedding:{hashlib.md5(text.encode()).hexdigest()}"
        try:
            self.client.setex(key, ttl, json.dumps(embedding))
        except Exception as e:
            logger.error(f"Error caching embedding: {e}")
    
    async def get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """Retrieve cached embedding"""
        key = f"embedding:{hashlib.md5(text.encode()).hexdigest()}"
        try:
            cached = self.client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Error retrieving cached embedding: {e}")
        return None
    
    async def cache_query_result(self, query: str, persona: str, result: Dict[str, Any], ttl: int = 300):
        """Cache query results"""
        key = f"query:{persona}:{hashlib.md5(query.encode()).hexdigest()}"
        try:
            self.client.setex(key, ttl, json.dumps(result))
        except Exception as e:
            logger.error(f"Error caching query result: {e}")
    
    async def get_cached_query_result(self, query: str, persona: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached query result"""
        key = f"query:{persona}:{hashlib.md5(query.encode()).hexdigest()}"
        try:
            cached = self.client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Error retrieving cached query result: {e}")
        return None
    
    async def store_user_session(self, session_id: str, data: Dict[str, Any], ttl: int = 86400):
        """Store user session data"""
        key = f"session:{session_id}"
        try:
            self.client.setex(key, ttl, json.dumps(data))
        except Exception as e:
            logger.error(f"Error storing session: {e}")
    
    async def get_user_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user session data"""
        key = f"session:{session_id}"
        try:
            cached = self.client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Error retrieving session: {e}")
        return None

class PostgreSQLManager:
    """Manages PostgreSQL operations for structured data"""
    
    def __init__(self, config: Dict[str, Any]):
        if not POSTGRESQL_AVAILABLE:
            raise ImportError("PostgreSQL not available")
        
        self.config = config
        self.pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize PostgreSQL connection pool"""
        try:
            self.pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=self.config.get("pool_size", 10),
                host=self.config["host"],
                port=self.config["port"],
                database=self.config["database"],
                user=self.config["user"],
                password=self.config["password"]
            )
            logger.info("PostgreSQL connection pool initialized")
        except Exception as e:
            logger.error(f"PostgreSQL pool initialization error: {e}")
    
    async def initialize_schema(self):
        """Create database schema for enterprise data"""
        schema_sql = """
        -- Enable vector extension if available
        CREATE EXTENSION IF NOT EXISTS vector;
        
        -- Personas table
        CREATE TABLE IF NOT EXISTS personas (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Entities table for fuzzy matching
        CREATE TABLE IF NOT EXISTS entities (
            id SERIAL PRIMARY KEY,
            canonical_name VARCHAR(255) NOT NULL,
            entity_type VARCHAR(50) NOT NULL,
            persona_id INTEGER REFERENCES personas(id),
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Entity aliases for fuzzy matching
        CREATE TABLE IF NOT EXISTS entity_aliases (
            id SERIAL PRIMARY KEY,
            entity_id INTEGER REFERENCES entities(id),
            alias_name VARCHAR(255) NOT NULL,
            confidence_score FLOAT DEFAULT 1.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- User preferences and learning
        CREATE TABLE IF NOT EXISTS user_preferences (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(100) NOT NULL,
            persona VARCHAR(50) NOT NULL,
            preference_type VARCHAR(50) NOT NULL,
            preference_data JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Query learning and disambiguation
        CREATE TABLE IF NOT EXISTS query_learning (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(100) NOT NULL,
            original_query TEXT NOT NULL,
            clarified_query TEXT,
            selected_entity_id INTEGER REFERENCES entities(id),
            persona VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- File ingestion tracking
        CREATE TABLE IF NOT EXISTS file_ingestion (
            id SERIAL PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            file_hash VARCHAR(64) UNIQUE NOT NULL,
            file_size BIGINT,
            file_type VARCHAR(50),
            persona VARCHAR(50) NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            chunks_created INTEGER DEFAULT 0,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        );
        
        -- API integration logs
        CREATE TABLE IF NOT EXISTS api_integration_logs (
            id SERIAL PRIMARY KEY,
            api_name VARCHAR(50) NOT NULL,
            operation VARCHAR(50) NOT NULL,
            status VARCHAR(20) NOT NULL,
            records_processed INTEGER DEFAULT 0,
            error_message TEXT,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_entities_type_persona ON entities(entity_type, persona_id);
        CREATE INDEX IF NOT EXISTS idx_entity_aliases_name ON entity_aliases(alias_name);
        CREATE INDEX IF NOT EXISTS idx_user_preferences_user_persona ON user_preferences(user_id, persona);
        CREATE INDEX IF NOT EXISTS idx_query_learning_user_persona ON query_learning(user_id, persona);
        CREATE INDEX IF NOT EXISTS idx_file_ingestion_status ON file_ingestion(status);
        CREATE INDEX IF NOT EXISTS idx_api_logs_name_status ON api_integration_logs(api_name, status);
        
        -- Insert default personas
        INSERT INTO personas (name, description) VALUES 
            ('cherry', 'Personal life management and ranch operations')
            ON CONFLICT (name) DO NOTHING;
        INSERT INTO personas (name, description) VALUES 
            ('sophia', 'PayReady business intelligence and operations')
            ON CONFLICT (name) DO NOTHING;
        INSERT INTO personas (name, description) VALUES 
            ('karen', 'ParagonRX healthcare operations management')
            ON CONFLICT (name) DO NOTHING;
        """
        
        conn = None
        try:
            conn = self.pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute(schema_sql)
                conn.commit()
            logger.info("PostgreSQL schema initialized")
        except Exception as e:
            logger.error(f"Error initializing PostgreSQL schema: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                self.pool.putconn(conn)
    
    async def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results"""
        conn = None
        try:
            conn = self.pool.getconn()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return []
        finally:
            if conn:
                self.pool.putconn(conn)
    
    async def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows"""
        conn = None
        try:
            conn = self.pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Error executing update: {e}")
            if conn:
                conn.rollback()
            return 0
        finally:
            if conn:
                self.pool.putconn(conn)

class EnterpriseDatabaseManager:
    """Main database manager coordinating all database systems"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = DatabaseConfig(config_path)
        self.embedding_manager = None
        self.pinecone_manager = None
        self.weaviate_manager = None
        self.redis_manager = None
        self.postgresql_manager = None
        
        self._initialize_managers()
    
    def _initialize_managers(self):
        """Initialize all database managers"""
        try:
            # Initialize embedding manager
            if EMBEDDINGS_AVAILABLE:
                self.embedding_manager = EmbeddingManager(self.config.config["embeddings"])
            
            # Initialize Pinecone
            if PINECONE_AVAILABLE and self.config.config["pinecone"]["api_key"]:
                self.pinecone_manager = PineconeManager(self.config.config["pinecone"])
            
            # Initialize Weaviate
            if WEAVIATE_AVAILABLE:
                self.weaviate_manager = WeaviateManager(self.config.config["weaviate"])
            
            # Initialize Redis
            if REDIS_AVAILABLE:
                self.redis_manager = RedisManager(self.config.config["redis"])
            
            # Initialize PostgreSQL
            if POSTGRESQL_AVAILABLE:
                self.postgresql_manager = PostgreSQLManager(self.config.config["postgresql"])
            
            logger.info("Database managers initialized")
            
        except Exception as e:
            logger.error(f"Error initializing database managers: {e}")
    
    async def initialize_all(self):
        """Initialize all database schemas and connections"""
        try:
            # Initialize PostgreSQL schema first
            if self.postgresql_manager:
                await self.postgresql_manager.initialize_schema()
            
            # Initialize Pinecone indexes
            if self.pinecone_manager:
                await self.pinecone_manager.initialize_indexes()
            
            # Initialize Weaviate schema
            if self.weaviate_manager:
                await self.weaviate_manager.initialize_schema()
            
            logger.info("All database systems initialized")
            
        except Exception as e:
            logger.error(f"Error initializing database systems: {e}")
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all database connections"""
        health = {}
        
        # Check Pinecone
        try:
            if self.pinecone_manager:
                # Try to list indexes
                self.pinecone_manager.pc.list_indexes()
                health["pinecone"] = True
            else:
                health["pinecone"] = False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            health["pinecone"] = False
        
        # Check Weaviate
        try:
            if self.weaviate_manager:
                self.weaviate_manager.client.schema.get()
                health["weaviate"] = True
            else:
                health["weaviate"] = False
        except:
            health["weaviate"] = False
        
        # Check Redis
        try:
            if self.redis_manager:
                self.redis_manager.client.ping()
                health["redis"] = True
            else:
                health["redis"] = False
        except:
            health["redis"] = False
        
        # Check PostgreSQL
        try:
            if self.postgresql_manager:
                await self.postgresql_manager.execute_query("SELECT 1")
                health["postgresql"] = True
            else:
                health["postgresql"] = False
        except:
            health["postgresql"] = False
        
        return health

# Example usage and testing
async def main():
    """Test the database manager"""
    db_manager = EnterpriseDatabaseManager()
    
    # Initialize all systems
    await db_manager.initialize_all()
    
    # Health check
    health = await db_manager.health_check()
    print("Database Health Check:")
    for system, status in health.items():
        print(f"  {system}: {'✅' if status else '❌'}")

if __name__ == "__main__":
    asyncio.run(main())

