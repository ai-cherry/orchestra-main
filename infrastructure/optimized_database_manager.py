#!/usr/bin/env python3
"""
Optimized Database Manager for Multi-AI Collaboration Platform
Consolidates PostgreSQL, Redis, and Weaviate (eliminating Pinecone redundancy)
Includes comprehensive MCP knowledge population and synchronization

Author: Orchestra AI Team
Version: 2.0.0 (Optimized)
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import uuid
from dataclasses import dataclass
from contextlib import asynccontextmanager

# Database imports
import asyncpg
import redis.asyncio as redis
import weaviate
from weaviate.classes.config import Configure, Property, DataType

# Configuration and utilities
from pydantic import BaseModel
import openai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DatabaseMetrics:
    """Database performance metrics"""
    query_count: int = 0
    avg_query_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    active_connections: int = 0
    last_updated: datetime = datetime.now()

class OptimizedDatabaseConfig(BaseModel):
    """Unified database configuration"""
    # PostgreSQL Configuration
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_database: str = "multi_ai_collaboration"
    postgres_user: str = "ai_collab"
    postgres_password: str = ""
    postgres_pool_min: int = 5
    postgres_pool_max: int = 20
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    redis_max_connections: int = 20
    
    # Weaviate Configuration (Unified Vector Database)
    weaviate_url: str = "http://localhost:8080"
    weaviate_api_key: Optional[str] = None
    weaviate_timeout: int = 30
    
    # API Keys
    openai_api_key: Optional[str] = None
    
    # Performance Settings
    enable_metrics: bool = True
    enable_caching: bool = True
    cache_ttl: int = 3600  # 1 hour
    
    class Config:
        env_prefix = "DB_"

class MultiAIPostgreSQLManager:
    """Optimized PostgreSQL manager for multi-AI collaboration"""
    
    def __init__(self, config: OptimizedDatabaseConfig):
        self.config = config
        self.pool = None
        self.metrics = DatabaseMetrics()
    
    async def initialize(self):
        """Initialize PostgreSQL connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.postgres_host,
                port=self.config.postgres_port,
                database=self.config.postgres_database,
                user=self.config.postgres_user,
                password=self.config.postgres_password,
                min_size=self.config.postgres_pool_min,
                max_size=self.config.postgres_pool_max,
                command_timeout=30
            )
            
            # Create optimized schema for multi-AI collaboration
            await self._create_multi_ai_schema()
            logger.info("✅ PostgreSQL initialized with multi-AI schema")
            
        except Exception as e:
            logger.error(f"❌ PostgreSQL initialization failed: {e}")
            raise
    
    async def _create_multi_ai_schema(self):
        """Create optimized schema for multi-AI collaboration"""
        schema_sql = """
        -- Enable required extensions
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        CREATE EXTENSION IF NOT EXISTS "pg_trgm";
        
        -- AI Sessions table
        CREATE TABLE IF NOT EXISTS ai_sessions (
            session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            active_ais TEXT[] DEFAULT '{}',
            collaboration_type VARCHAR(100),
            project_context JSONB,
            status VARCHAR(50) DEFAULT 'active',
            performance_metrics JSONB DEFAULT '{}'::jsonb
        );
        
        -- AI Interactions table
        CREATE TABLE IF NOT EXISTS ai_interactions (
            interaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id UUID REFERENCES ai_sessions(session_id) ON DELETE CASCADE,
            from_ai VARCHAR(100) NOT NULL,
            to_ai VARCHAR(100),
            message_type VARCHAR(100) NOT NULL,
            content JSONB NOT NULL,
            routing_info JSONB DEFAULT '{}'::jsonb,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            processed BOOLEAN DEFAULT FALSE,
            processing_time_ms INTEGER,
            quality_score FLOAT
        );
        
        -- Collaboration State table
        CREATE TABLE IF NOT EXISTS collaboration_state (
            session_id UUID REFERENCES ai_sessions(session_id) ON DELETE CASCADE,
            state_key VARCHAR(255) NOT NULL,
            state_value JSONB NOT NULL,
            updated_by VARCHAR(100) NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            version INTEGER DEFAULT 1,
            PRIMARY KEY (session_id, state_key)
        );
        
        -- MCP Knowledge Cache table
        CREATE TABLE IF NOT EXISTS mcp_knowledge_cache (
            cache_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            domain VARCHAR(100) NOT NULL,
            knowledge_key VARCHAR(255) NOT NULL,
            content JSONB NOT NULL,
            embedding_stored BOOLEAN DEFAULT FALSE,
            usage_count INTEGER DEFAULT 0,
            last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            expires_at TIMESTAMP WITH TIME ZONE,
            UNIQUE(domain, knowledge_key)
        );
        
        -- Performance optimized indexes
        CREATE INDEX IF NOT EXISTS idx_ai_interactions_session_time 
        ON ai_interactions(session_id, timestamp DESC);
        
        CREATE INDEX IF NOT EXISTS idx_ai_interactions_routing 
        ON ai_interactions USING GIN (routing_info);
        
        CREATE INDEX IF NOT EXISTS idx_collaboration_state_updated 
        ON collaboration_state(updated_at DESC);
        
        CREATE INDEX IF NOT EXISTS idx_ai_sessions_active 
        ON ai_sessions(status) WHERE status = 'active';
        
        CREATE INDEX IF NOT EXISTS idx_mcp_knowledge_domain_key 
        ON mcp_knowledge_cache(domain, knowledge_key);
        
        CREATE INDEX IF NOT EXISTS idx_mcp_knowledge_usage 
        ON mcp_knowledge_cache(usage_count DESC, last_accessed DESC);
        
        -- Trigger for updating timestamps
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        DROP TRIGGER IF EXISTS update_ai_sessions_updated_at ON ai_sessions;
        CREATE TRIGGER update_ai_sessions_updated_at
        BEFORE UPDATE ON ai_sessions
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(schema_sql)
    
    async def create_ai_session(self, session_name: str, collaboration_type: str, 
                               active_ais: List[str]) -> str:
        """Create new AI collaboration session"""
        async with self.pool.acquire() as conn:
            session_id = await conn.fetchval("""
                INSERT INTO ai_sessions (session_name, collaboration_type, active_ais)
                VALUES ($1, $2, $3)
                RETURNING session_id
            """, session_name, collaboration_type, active_ais)
            
            logger.info(f"Created AI session: {session_id}")
            return str(session_id)
    
    async def log_ai_interaction(self, session_id: str, from_ai: str, to_ai: str,
                                message_type: str, content: dict, routing_info: dict = None):
        """Log AI interaction with performance metrics"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO ai_interactions 
                (session_id, from_ai, to_ai, message_type, content, routing_info)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, uuid.UUID(session_id), from_ai, to_ai, message_type, 
                json.dumps(content), json.dumps(routing_info or {}))
    
    async def get_collaboration_analytics(self, session_id: str) -> dict:
        """Get analytics for AI collaboration session"""
        async with self.pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_interactions,
                    COUNT(DISTINCT from_ai) as active_ais,
                    AVG(quality_score) as avg_quality,
                    AVG(processing_time_ms) as avg_processing_time
                FROM ai_interactions 
                WHERE session_id = $1
            """, uuid.UUID(session_id))
            
            return dict(stats) if stats else {}

class MultiAIRedisManager:
    """Optimized Redis manager for real-time collaboration"""
    
    def __init__(self, config: OptimizedDatabaseConfig):
        self.config = config
        self.redis = None
        self.pubsub = None
    
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                password=self.config.redis_password if self.config.redis_password else None,
                db=self.config.redis_db,
                max_connections=self.config.redis_max_connections,
                decode_responses=True
            )
            
            await self.redis.ping()
            self.pubsub = self.redis.pubsub()
            logger.info("✅ Redis initialized for multi-AI collaboration")
            
        except Exception as e:
            logger.error(f"❌ Redis initialization failed: {e}")
            raise
    
    async def register_ai_session(self, session_id: str, ai_name: str):
        """Register AI in active session"""
        async with self.redis.pipeline() as pipe:
            await pipe.sadd(f"session:{session_id}:ais", ai_name)
            await pipe.hset(f"ai:{ai_name}:status", "session", session_id)
            await pipe.hset(f"ai:{ai_name}:status", "last_seen", datetime.now().isoformat())
            await pipe.expire(f"ai:{ai_name}:status", 3600)
            await pipe.execute()
        
        logger.info(f"Registered {ai_name} in session {session_id}")
    
    async def route_message(self, session_id: str, message: dict):
        """Route message to appropriate AIs with priority queues"""
        target_ais = message.get('target_ais', [])
        priority = message.get('priority', 'normal')
        
        for ai in target_ais:
            queue_key = f"queue:{ai}:{priority}"
            await self.redis.lpush(queue_key, json.dumps(message))
            await self.redis.expire(queue_key, 3600)
        
        # Publish to session subscribers
        await self.redis.publish(f"session:{session_id}:messages", json.dumps(message))
    
    async def update_collaboration_state(self, session_id: str, key: str, value: dict):
        """Update shared collaboration state with versioning"""
        state_key = f"collab:{session_id}:state"
        version_key = f"collab:{session_id}:version:{key}"
        
        # Get current version
        current_version = await self.redis.get(version_key) or "0"
        new_version = str(int(current_version) + 1)
        
        async with self.redis.pipeline() as pipe:
            await pipe.hset(state_key, key, json.dumps(value))
            await pipe.set(version_key, new_version)
            await pipe.expire(state_key, 7200)  # 2 hours
            await pipe.expire(version_key, 7200)
            await pipe.execute()
        
        # Notify all AIs in session
        update_notification = {
            "type": "state_update",
            "key": key,
            "value": value,
            "version": new_version,
            "timestamp": datetime.now().isoformat()
        }
        await self.redis.publish(f"session:{session_id}:updates", json.dumps(update_notification))
    
    async def get_ai_queue_size(self, ai_name: str, priority: str = "normal") -> int:
        """Get queue size for specific AI"""
        queue_key = f"queue:{ai_name}:{priority}"
        return await self.redis.llen(queue_key)
    
    async def cache_mcp_knowledge(self, domain: str, key: str, data: dict, ttl: int = 3600):
        """Cache MCP knowledge with TTL"""
        cache_key = f"mcp:knowledge:{domain}:{key}"
        await self.redis.setex(cache_key, ttl, json.dumps(data))

class MultiAIWeaviateManager:
    """Optimized Weaviate manager (unified vector database)"""
    
    def __init__(self, config: OptimizedDatabaseConfig):
        self.config = config
        self.client = None
    
    async def initialize(self):
        """Initialize Weaviate client and schemas"""
        try:
            auth_config = None
            if self.config.weaviate_api_key:
                auth_config = weaviate.AuthApiKey(api_key=self.config.weaviate_api_key)
            
            self.client = weaviate.Client(
                url=self.config.weaviate_url,
                auth_client_secret=auth_config,
                timeout_config=(5, self.config.weaviate_timeout)
            )
            
            # Create optimized schemas for multi-AI collaboration
            await self._create_multi_ai_schemas()
            logger.info("✅ Weaviate initialized with multi-AI schemas")
            
        except Exception as e:
            logger.error(f"❌ Weaviate initialization failed: {e}")
            raise
    
    async def _create_multi_ai_schemas(self):
        """Create optimized Weaviate schemas"""
        # AI Knowledge schema
        ai_knowledge_schema = {
            "class": "AIKnowledge",
            "description": "Multi-AI collaboration knowledge base",
            "vectorizer": "text2vec-openai",
            "properties": [
                {"name": "content", "dataType": ["text"], "description": "Knowledge content"},
                {"name": "domain", "dataType": ["string"], "description": "Knowledge domain"},
                {"name": "ai_source", "dataType": ["string"], "description": "AI source"},
                {"name": "collaboration_context", "dataType": ["string"], "description": "Collaboration context"},
                {"name": "usage_frequency", "dataType": ["int"], "description": "Usage frequency"},
                {"name": "quality_score", "dataType": ["number"], "description": "Quality score"},
                {"name": "last_updated", "dataType": ["date"], "description": "Last update"},
                {"name": "tags", "dataType": ["string[]"], "description": "Knowledge tags"}
            ]
        }
        
        # AI Interaction Patterns schema
        ai_interaction_schema = {
            "class": "AIInteraction",
            "description": "AI collaboration interaction patterns",
            "vectorizer": "text2vec-openai",
            "properties": [
                {"name": "interaction_pattern", "dataType": ["text"], "description": "Interaction pattern"},
                {"name": "participants", "dataType": ["string[]"], "description": "AIs involved"},
                {"name": "outcome_quality", "dataType": ["number"], "description": "Outcome quality"},
                {"name": "context_type", "dataType": ["string"], "description": "Context type"},
                {"name": "success_metrics", "dataType": ["object"], "description": "Success metrics"},
                {"name": "timestamp", "dataType": ["date"], "description": "Interaction timestamp"}
            ]
        }
        
        # Create schemas if they don't exist
        existing_classes = [cls['class'] for cls in self.client.schema.get()['classes']]
        
        if "AIKnowledge" not in existing_classes:
            self.client.schema.create_class(ai_knowledge_schema)
        
        if "AIInteraction" not in existing_classes:
            self.client.schema.create_class(ai_interaction_schema)
    
    async def add_knowledge(self, content: str, domain: str, ai_source: str, 
                           metadata: dict = None) -> str:
        """Add knowledge to vector database"""
        knowledge_data = {
            "content": content,
            "domain": domain,
            "ai_source": ai_source,
            "collaboration_context": metadata.get("context", ""),
            "usage_frequency": 0,
            "quality_score": metadata.get("quality_score", 1.0),
            "tags": metadata.get("tags", [])
        }
        
        result = self.client.data_object.create(
            data_object=knowledge_data,
            class_name="AIKnowledge"
        )
        
        return result
    
    async def search_knowledge(self, query: str, domain: str = None, limit: int = 10) -> List[dict]:
        """Search knowledge with domain filtering"""
        query_builder = (
            self.client.query
            .get("AIKnowledge", ["content", "domain", "ai_source", "quality_score"])
            .with_near_text({"concepts": [query]})
            .with_limit(limit)
            .with_additional(["certainty", "distance"])
        )
        
        if domain:
            query_builder = query_builder.with_where({
                "path": ["domain"],
                "operator": "Equal",
                "valueString": domain
            })
        
        result = query_builder.do()
        return result.get("data", {}).get("Get", {}).get("AIKnowledge", [])
    
    async def learn_from_collaboration(self, interaction_data: dict):
        """Learn from successful AI collaborations"""
        interaction_obj = {
            "interaction_pattern": interaction_data.get("pattern", ""),
            "participants": interaction_data.get("participants", []),
            "outcome_quality": interaction_data.get("quality", 0.0),
            "context_type": interaction_data.get("context_type", ""),
            "success_metrics": interaction_data.get("metrics", {})
        }
        
        return self.client.data_object.create(
            data_object=interaction_obj,
            class_name="AIInteraction"
        )

class MCPKnowledgePopulator:
    """Advanced MCP knowledge population system"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.knowledge_domains = {
            "deployment": self._generate_deployment_knowledge,
            "architecture": self._generate_architecture_knowledge,
            "ui_development": self._generate_ui_knowledge,
            "debugging": self._generate_debugging_knowledge,
            "collaboration": self._generate_collaboration_knowledge
        }
    
    async def populate_all_domains(self):
        """Populate MCP with comprehensive knowledge"""
        total_items = 0
        
        for domain, generator in self.knowledge_domains.items():
            logger.info(f"Populating {domain} knowledge...")
            knowledge_items = await generator()
            
            for item in knowledge_items:
                # Store in Weaviate
                await self.db_manager.weaviate.add_knowledge(
                    content=item['content'],
                    domain=domain,
                    ai_source="mcp_populator",
                    metadata=item.get('metadata', {})
                )
                
                # Cache in Redis if high frequency
                if item.get('high_frequency'):
                    await self.db_manager.redis.cache_mcp_knowledge(
                        domain, item['key'], item
                    )
                
                # Store in PostgreSQL cache
                await self.db_manager.postgres.pool.execute("""
                    INSERT INTO mcp_knowledge_cache 
                    (domain, knowledge_key, content, usage_count)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (domain, knowledge_key) 
                    DO UPDATE SET content = $3, usage_count = usage_count + 1
                """, domain, item['key'], json.dumps(item), 0)
                
                total_items += 1
        
        logger.info(f"✅ Populated {total_items} knowledge items across all domains")
    
    async def _generate_deployment_knowledge(self) -> List[dict]:
        """Generate deployment-specific knowledge"""
        return [
            {
                "key": "docker_optimization",
                "content": "Multi-stage Docker builds with Python 3.10 slim base images. Use specific version tags, minimize layers, implement security best practices with non-root users. Configure for optimal AI workload performance.",
                "metadata": {"tags": ["docker", "optimization", "security"], "quality_score": 0.9},
                "high_frequency": True
            },
            {
                "key": "database_scaling",
                "content": "PostgreSQL scaling for AI workloads: shared_buffers=512MB, effective_cache_size=1536MB, work_mem=8MB for complex AI queries. Use connection pooling with 5-20 connections per service.",
                "metadata": {"tags": ["postgresql", "scaling", "performance"], "quality_score": 0.95},
                "high_frequency": True
            },
            {
                "key": "redis_collaboration",
                "content": "Redis configuration for multi-AI collaboration: maxmemory 1gb with allkeys-lru policy. Use pub/sub for real-time AI communication, priority queues for message routing.",
                "metadata": {"tags": ["redis", "collaboration", "real-time"], "quality_score": 0.9},
                "high_frequency": True
            }
        ]
    
    async def _generate_architecture_knowledge(self) -> List[dict]:
        """Generate architecture-specific knowledge"""
        return [
            {
                "key": "microservices_ai",
                "content": "AI-optimized microservices architecture: separate services for each AI agent type, shared databases with connection pooling, async communication patterns.",
                "metadata": {"tags": ["microservices", "ai", "architecture"], "quality_score": 0.85},
                "high_frequency": False
            },
            {
                "key": "vector_database_choice",
                "content": "Use Weaviate as unified vector database instead of multiple solutions. Eliminates Pinecone redundancy, provides hybrid search capabilities, better integration with PostgreSQL.",
                "metadata": {"tags": ["vector", "database", "optimization"], "quality_score": 0.9},
                "high_frequency": True
            }
        ]
    
    async def _generate_ui_knowledge(self) -> List[dict]:
        """Generate UI development knowledge"""
        return [
            {
                "key": "react_ai_patterns",
                "metadata": {"tags": ["react", "ai", "patterns"], "quality_score": 0.8},
                "high_frequency": False
            }
        ]
    
    async def _generate_debugging_knowledge(self) -> List[dict]:
        """Generate debugging knowledge"""
        return [
            {
                "key": "ai_debugging_tools",
                "content": "AI-specific debugging: log AI interactions with unique IDs, implement performance metrics collection, use distributed tracing for multi-AI workflows.",
                "metadata": {"tags": ["debugging", "ai", "monitoring"], "quality_score": 0.85},
                "high_frequency": False
            }
        ]
    
    async def _generate_collaboration_knowledge(self) -> List[dict]:
        """Generate AI collaboration knowledge"""
        return [
            {
                "key": "ai_routing_patterns",
                "content": "AI message routing: use Redis priority queues, implement circuit breakers for AI failures, maintain collaboration state in distributed cache.",
                "metadata": {"tags": ["collaboration", "routing", "reliability"], "quality_score": 0.9},
                "high_frequency": True
            }
        ]

class OptimizedDatabaseManager:
    """Unified database manager for multi-AI collaboration platform"""
    
    def __init__(self, config: OptimizedDatabaseConfig = None):
        self.config = config or OptimizedDatabaseConfig()
        self.postgres = MultiAIPostgreSQLManager(self.config)
        self.redis = MultiAIRedisManager(self.config)
        self.weaviate = MultiAIWeaviateManager(self.config)
        self.mcp_populator = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize all database systems"""
        if self.initialized:
            return
        
        logger.info("🚀 Initializing optimized multi-AI database systems...")
        
        # Initialize all database managers
        await self.postgres.initialize()
        await self.redis.initialize()
        await self.weaviate.initialize()
        
        # Initialize MCP populator
        self.mcp_populator = MCPKnowledgePopulator(self)
        
        self.initialized = True
        logger.info("✅ All database systems initialized successfully")
    
    async def populate_mcp_knowledge(self):
        """Populate MCP with comprehensive knowledge"""
        if not self.mcp_populator:
            raise RuntimeError("Database manager not initialized")
        
        await self.mcp_populator.populate_all_domains()
    
    async def health_check(self) -> dict:
        """Comprehensive health check for all systems"""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "services": {}
        }
        
        # PostgreSQL health
        try:
            async with self.postgres.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            health_status["services"]["postgresql"] = {"status": "healthy", "pool_size": self.postgres.pool.get_size()}
        except Exception as e:
            health_status["services"]["postgresql"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "degraded"
        
        # Redis health
        try:
            await self.redis.redis.ping()
            info = await self.redis.redis.info()
            health_status["services"]["redis"] = {
                "status": "healthy", 
                "connected_clients": info.get("connected_clients", 0)
            }
        except Exception as e:
            health_status["services"]["redis"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "degraded"
        
        # Weaviate health
        try:
            ready = self.weaviate.client.is_ready()
            health_status["services"]["weaviate"] = {"status": "healthy" if ready else "unhealthy"}
        except Exception as e:
            health_status["services"]["weaviate"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "degraded"
        
        return health_status
    
    async def cleanup(self):
        """Cleanup database connections"""
        if self.postgres.pool:
            await self.postgres.pool.close()
        if self.redis.redis:
            await self.redis.redis.close()
        
        logger.info("✅ Database connections cleaned up")

# Usage example and testing
async def main():
    """Example usage of optimized database manager"""
    config = OptimizedDatabaseConfig(
        postgres_password="your_secure_password",
        openai_api_key="your_openai_key"
    )
    
    db_manager = OptimizedDatabaseManager(config)
    
    try:
        # Initialize all systems
        await db_manager.initialize()
        
        # Populate MCP knowledge
        await db_manager.populate_mcp_knowledge()
        
        # Test AI session creation
        session_id = await db_manager.postgres.create_ai_session(
            session_name="Test Multi-AI Collaboration",
            collaboration_type="development",
            active_ais=["cursor_ai", "claude", "github_copilot"]
        )
        
        # Register AIs in session
        for ai in ["cursor_ai", "claude", "github_copilot"]:
            await db_manager.redis.register_ai_session(session_id, ai)
        
        # Test knowledge search
        knowledge = await db_manager.weaviate.search_knowledge(
            query="docker optimization for AI workloads",
            domain="deployment",
            limit=5
        )
        
        print(f"Found {len(knowledge)} knowledge items")
        
        # Health check
        health = await db_manager.health_check()
        print(f"System health: {health['status']}")
        
    finally:
        await db_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 