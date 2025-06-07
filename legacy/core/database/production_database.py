"""
Production Database Architecture for Cherry-AI.com
Advanced PostgreSQL schema with optimized performance and scalability
"""

import asyncio
import asyncpg
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
import uuid
import logging

# Database connection configuration
DATABASE_CONFIG = {
    'host': 'db.cherry-ai.com',
    'port': 5432,
    'database': 'cherry_ai_prod',
    'user': 'admin',
    'password': 'secure_password',
    'min_size': 10,
    'max_size': 20,
    'command_timeout': 60,
    'server_settings': {
        'jit': 'off',
        'application_name': 'cherry_ai_admin'
    }
}

class PersonaType(Enum):
    CHERRY = "cherry"
    SOPHIA = "sophia"
    KAREN = "karen"

class MemoryType(Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    WORKING = "working"

class PrivacyLevel(Enum):
    PUBLIC = 1
    SHARED = 2
    CONFIDENTIAL = 3
    RESTRICTED = 4
    PRIVATE = 5

@dataclass
class DatabaseSchema:
    """Complete database schema for Cherry-AI production system"""
    
    # Core system tables
    SYSTEM_HEALTH = """
    CREATE TABLE IF NOT EXISTS system_health (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMPTZ DEFAULT NOW(),
        cpu_usage_percent DECIMAL(5,2) NOT NULL,
        memory_usage_mb INTEGER NOT NULL,
        active_connections INTEGER NOT NULL,
        response_time_ms DECIMAL(8,2) NOT NULL,
        error_count INTEGER DEFAULT 0,
        status VARCHAR(20) DEFAULT 'healthy',
        metadata JSONB DEFAULT '{}'::jsonb,
        CONSTRAINT valid_cpu_usage CHECK (cpu_usage_percent >= 0 AND cpu_usage_percent <= 100),
        CONSTRAINT valid_memory CHECK (memory_usage_mb >= 0),
        CONSTRAINT valid_response_time CHECK (response_time_ms >= 0)
    );
    
    CREATE INDEX idx_system_health_timestamp ON system_health(timestamp DESC);
    CREATE INDEX idx_system_health_status ON system_health(status);
    """
    
    # Persona management tables
    PERSONAS = """
    CREATE TABLE IF NOT EXISTS personas (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR(50) NOT NULL UNIQUE,
        type persona_type NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        is_active BOOLEAN DEFAULT true,
        
        -- Personality configuration
        personality_config JSONB NOT NULL DEFAULT '{}'::jsonb,
        voice_config JSONB NOT NULL DEFAULT '{}'::jsonb,
        behavior_config JSONB NOT NULL DEFAULT '{}'::jsonb,
        
        -- Performance metrics
        interaction_count BIGINT DEFAULT 0,
        success_rate DECIMAL(5,2) DEFAULT 100.00,
        avg_response_time_ms DECIMAL(8,2) DEFAULT 0,
        personality_health DECIMAL(5,2) DEFAULT 100.00,
        memory_usage_mb INTEGER DEFAULT 0,
        
        -- Metadata
        accent_color VARCHAR(20) DEFAULT '#3b82f6',
        description TEXT,
        capabilities JSONB DEFAULT '[]'::jsonb,
        constraints JSONB DEFAULT '{}'::jsonb,
        
        CONSTRAINT valid_success_rate CHECK (success_rate >= 0 AND success_rate <= 100),
        CONSTRAINT valid_personality_health CHECK (personality_health >= 0 AND personality_health <= 100)
    );
    
    CREATE INDEX idx_personas_type ON personas(type);
    CREATE INDEX idx_personas_active ON personas(is_active);
    CREATE INDEX idx_personas_updated ON personas(updated_at DESC);
    """
    
    # Advanced memory system
    MEMORIES = """
    CREATE TABLE IF NOT EXISTS memories (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
        memory_type memory_type NOT NULL,
        privacy_level privacy_level NOT NULL DEFAULT 3,
        
        -- Content
        content TEXT NOT NULL,
        summary TEXT,
        keywords TEXT[],
        embedding VECTOR(1536), -- OpenAI embedding dimension
        
        -- Metadata
        created_at TIMESTAMPTZ DEFAULT NOW(),
        accessed_at TIMESTAMPTZ DEFAULT NOW(),
        access_count INTEGER DEFAULT 0,
        importance_score DECIMAL(3,2) DEFAULT 0.5,
        emotional_valence DECIMAL(3,2) DEFAULT 0.0, -- -1 to 1
        confidence_score DECIMAL(3,2) DEFAULT 1.0,
        
        -- Relationships
        related_memory_ids UUID[],
        source_interaction_id UUID,
        tags JSONB DEFAULT '[]'::jsonb,
        context JSONB DEFAULT '{}'::jsonb,
        
        -- Lifecycle
        expires_at TIMESTAMPTZ,
        is_archived BOOLEAN DEFAULT false,
        
        CONSTRAINT valid_importance CHECK (importance_score >= 0 AND importance_score <= 1),
        CONSTRAINT valid_emotional_valence CHECK (emotional_valence >= -1 AND emotional_valence <= 1),
        CONSTRAINT valid_confidence CHECK (confidence_score >= 0 AND confidence_score <= 1)
    );
    
    CREATE INDEX idx_memories_persona ON memories(persona_id);
    CREATE INDEX idx_memories_type ON memories(memory_type);
    CREATE INDEX idx_memories_privacy ON memories(privacy_level);
    CREATE INDEX idx_memories_created ON memories(created_at DESC);
    CREATE INDEX idx_memories_importance ON memories(importance_score DESC);
    CREATE INDEX idx_memories_keywords ON memories USING GIN(keywords);
    CREATE INDEX idx_memories_tags ON memories USING GIN(tags);
    CREATE INDEX idx_memories_embedding ON memories USING ivfflat(embedding vector_cosine_ops);
    """
    
    # Interaction tracking
    INTERACTIONS = """
    CREATE TABLE IF NOT EXISTS interactions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
        
        -- Interaction details
        user_input TEXT NOT NULL,
        persona_response TEXT NOT NULL,
        interaction_type VARCHAR(50) NOT NULL,
        privacy_level privacy_level NOT NULL DEFAULT 3,
        
        -- Performance metrics
        response_time_ms DECIMAL(8,2) NOT NULL,
        tokens_used INTEGER DEFAULT 0,
        cost_usd DECIMAL(10,4) DEFAULT 0,
        quality_score DECIMAL(3,2),
        
        -- Context
        conversation_id UUID,
        session_id UUID,
        context JSONB DEFAULT '{}'::jsonb,
        metadata JSONB DEFAULT '{}'::jsonb,
        
        -- Timestamps
        created_at TIMESTAMPTZ DEFAULT NOW(),
        
        CONSTRAINT valid_response_time CHECK (response_time_ms >= 0),
        CONSTRAINT valid_tokens CHECK (tokens_used >= 0),
        CONSTRAINT valid_cost CHECK (cost_usd >= 0),
        CONSTRAINT valid_quality CHECK (quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1))
    );
    
    CREATE INDEX idx_interactions_persona ON interactions(persona_id);
    CREATE INDEX idx_interactions_created ON interactions(created_at DESC);
    CREATE INDEX idx_interactions_conversation ON interactions(conversation_id);
    CREATE INDEX idx_interactions_session ON interactions(session_id);
    CREATE INDEX idx_interactions_type ON interactions(interaction_type);
    """
    
    # Workflow management
    WORKFLOWS = """
    CREATE TABLE IF NOT EXISTS workflows (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR(100) NOT NULL,
        description TEXT,
        
        -- Workflow definition
        nodes JSONB NOT NULL DEFAULT '[]'::jsonb,
        edges JSONB NOT NULL DEFAULT '[]'::jsonb,
        config JSONB NOT NULL DEFAULT '{}'::jsonb,
        
        -- Status
        status VARCHAR(20) DEFAULT 'draft',
        is_active BOOLEAN DEFAULT false,
        
        -- Execution metrics
        execution_count INTEGER DEFAULT 0,
        success_count INTEGER DEFAULT 0,
        avg_execution_time_ms DECIMAL(10,2) DEFAULT 0,
        last_executed_at TIMESTAMPTZ,
        
        -- Metadata
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        created_by VARCHAR(100),
        tags JSONB DEFAULT '[]'::jsonb,
        
        CONSTRAINT valid_execution_count CHECK (execution_count >= 0),
        CONSTRAINT valid_success_count CHECK (success_count >= 0 AND success_count <= execution_count)
    );
    
    CREATE INDEX idx_workflows_status ON workflows(status);
    CREATE INDEX idx_workflows_active ON workflows(is_active);
    CREATE INDEX idx_workflows_updated ON workflows(updated_at DESC);
    """
    
    # Generation tracking
    GENERATIONS = """
    CREATE TABLE IF NOT EXISTS generations (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        persona_id UUID REFERENCES personas(id) ON DELETE SET NULL,
        
        -- Generation details
        type VARCHAR(20) NOT NULL, -- image, video, audio, text
        prompt TEXT NOT NULL,
        model VARCHAR(50) NOT NULL,
        
        -- Configuration
        parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
        style VARCHAR(50),
        quality_setting INTEGER DEFAULT 80,
        
        -- Results
        output_url TEXT,
        output_content TEXT,
        status VARCHAR(20) DEFAULT 'pending',
        
        -- Performance
        generation_time_ms DECIMAL(10,2),
        cost_usd DECIMAL(10,4) DEFAULT 0,
        quality_score DECIMAL(3,2),
        
        -- Metadata
        created_at TIMESTAMPTZ DEFAULT NOW(),
        completed_at TIMESTAMPTZ,
        metadata JSONB DEFAULT '{}'::jsonb,
        
        CONSTRAINT valid_quality_setting CHECK (quality_setting >= 1 AND quality_setting <= 100),
        CONSTRAINT valid_generation_time CHECK (generation_time_ms IS NULL OR generation_time_ms >= 0),
        CONSTRAINT valid_cost CHECK (cost_usd >= 0),
        CONSTRAINT valid_quality_score CHECK (quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1))
    );
    
    CREATE INDEX idx_generations_persona ON generations(persona_id);
    CREATE INDEX idx_generations_type ON generations(type);
    CREATE INDEX idx_generations_status ON generations(status);
    CREATE INDEX idx_generations_created ON generations(created_at DESC);
    """
    
    # Search and analytics
    SEARCH_QUERIES = """
    CREATE TABLE IF NOT EXISTS search_queries (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        persona_id UUID REFERENCES personas(id) ON DELETE SET NULL,
        
        -- Query details
        query TEXT NOT NULL,
        search_mode VARCHAR(20) NOT NULL,
        privacy_level privacy_level NOT NULL DEFAULT 3,
        
        -- Results
        results_count INTEGER DEFAULT 0,
        response_time_ms DECIMAL(8,2) NOT NULL,
        success BOOLEAN DEFAULT true,
        
        -- Context
        context JSONB DEFAULT '{}'::jsonb,
        filters JSONB DEFAULT '{}'::jsonb,
        metadata JSONB DEFAULT '{}'::jsonb,
        
        -- Timestamps
        created_at TIMESTAMPTZ DEFAULT NOW(),
        
        CONSTRAINT valid_results_count CHECK (results_count >= 0),
        CONSTRAINT valid_response_time CHECK (response_time_ms >= 0)
    );
    
    CREATE INDEX idx_search_queries_persona ON search_queries(persona_id);
    CREATE INDEX idx_search_queries_mode ON search_queries(search_mode);
    CREATE INDEX idx_search_queries_created ON search_queries(created_at DESC);
    """

class DatabaseManager:
    """Production-grade database manager with connection pooling and optimization"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self) -> None:
        """Initialize database connection pool and schema"""
        try:
            # Create connection pool
            self.pool = await asyncpg.create_pool(**DATABASE_CONFIG)
            self.logger.info("Database connection pool created successfully")
            
            # Initialize schema
            await self._create_schema()
            await self._create_indexes()
            await self._setup_triggers()
            
            self.logger.info("Database schema initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise
    
    async def _create_schema(self) -> None:
        """Create database schema with all tables"""
        schema = DatabaseSchema()
        
        async with self.pool.acquire() as conn:
            # Create custom types
            await conn.execute("CREATE TYPE IF NOT EXISTS persona_type AS ENUM ('cherry', 'sophia', 'karen');")
            await conn.execute("CREATE TYPE IF NOT EXISTS memory_type AS ENUM ('episodic', 'semantic', 'procedural', 'working');")
            await conn.execute("CREATE TYPE IF NOT EXISTS privacy_level AS ENUM ('1', '2', '3', '4', '5');")
            
            # Create extension for vector operations
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # Create all tables
            await conn.execute(schema.SYSTEM_HEALTH)
            await conn.execute(schema.PERSONAS)
            await conn.execute(schema.MEMORIES)
            await conn.execute(schema.INTERACTIONS)
            await conn.execute(schema.WORKFLOWS)
            await conn.execute(schema.GENERATIONS)
            await conn.execute(schema.SEARCH_QUERIES)
    
    async def _create_indexes(self) -> None:
        """Create additional performance indexes"""
        async with self.pool.acquire() as conn:
            # Composite indexes for common queries
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_persona_type 
                ON memories(persona_id, memory_type);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_interactions_persona_created 
                ON interactions(persona_id, created_at DESC);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_system_health_timestamp_status 
                ON system_health(timestamp DESC, status);
            """)
    
    async def _setup_triggers(self) -> None:
        """Setup database triggers for automatic updates"""
        async with self.pool.acquire() as conn:
            # Auto-update timestamps
            await conn.execute("""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = NOW();
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            """)
            
            await conn.execute("""
                CREATE TRIGGER update_personas_updated_at 
                BEFORE UPDATE ON personas 
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            """)
            
            # Auto-update persona metrics
            await conn.execute("""
                CREATE OR REPLACE FUNCTION update_persona_metrics()
                RETURNS TRIGGER AS $$
                BEGIN
                    UPDATE personas SET 
                        interaction_count = interaction_count + 1,
                        avg_response_time_ms = (
                            SELECT AVG(response_time_ms) 
                            FROM interactions 
                            WHERE persona_id = NEW.persona_id
                        )
                    WHERE id = NEW.persona_id;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            """)
            
            await conn.execute("""
                CREATE TRIGGER update_persona_metrics_trigger
                AFTER INSERT ON interactions
                FOR EACH ROW EXECUTE FUNCTION update_persona_metrics();
            """)
    
    async def get_system_health(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get system health metrics for the last N hours"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM system_health 
                WHERE timestamp >= NOW() - INTERVAL '%s hours'
                ORDER BY timestamp DESC
            """, hours)
            
            return [dict(row) for row in rows]
    
    async def get_persona_metrics(self, persona_id: uuid.UUID) -> Dict[str, Any]:
        """Get comprehensive metrics for a specific persona"""
        async with self.pool.acquire() as conn:
            persona = await conn.fetchrow("""
                SELECT * FROM personas WHERE id = $1
            """, persona_id)
            
            if not persona:
                return {}
            
            # Get recent interactions
            interactions = await conn.fetch("""
                SELECT COUNT(*) as total, AVG(response_time_ms) as avg_response_time
                FROM interactions 
                WHERE persona_id = $1 AND created_at >= NOW() - INTERVAL '24 hours'
            """, persona_id)
            
            # Get memory usage
            memory_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_memories,
                    COUNT(*) FILTER (WHERE memory_type = 'episodic') as episodic_count,
                    COUNT(*) FILTER (WHERE memory_type = 'semantic') as semantic_count,
                    AVG(importance_score) as avg_importance
                FROM memories 
                WHERE persona_id = $1 AND NOT is_archived
            """, persona_id)
            
            return {
                'persona': dict(persona),
                'interactions': dict(interactions[0]) if interactions else {},
                'memory_stats': dict(memory_stats) if memory_stats else {}
            }
    
    async def store_memory(self, persona_id: uuid.UUID, content: str, 
                          memory_type: MemoryType, privacy_level: PrivacyLevel,
                          **kwargs) -> uuid.UUID:
        """Store a new memory with advanced indexing"""
        async with self.pool.acquire() as conn:
            memory_id = await conn.fetchval("""
                INSERT INTO memories (
                    persona_id, memory_type, privacy_level, content,
                    summary, keywords, importance_score, emotional_valence,
                    confidence_score, tags, context
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING id
            """, 
                persona_id, memory_type.value, privacy_level.value, content,
                kwargs.get('summary'), kwargs.get('keywords', []),
                kwargs.get('importance_score', 0.5), kwargs.get('emotional_valence', 0.0),
                kwargs.get('confidence_score', 1.0), json.dumps(kwargs.get('tags', [])),
                json.dumps(kwargs.get('context', {}))
            )
            
            return memory_id
    
    async def search_memories(self, persona_id: uuid.UUID, query: str,
                            memory_type: Optional[MemoryType] = None,
                            limit: int = 10) -> List[Dict[str, Any]]:
        """Advanced memory search with vector similarity"""
        async with self.pool.acquire() as conn:
            # Build dynamic query
            where_clauses = ["persona_id = $1", "NOT is_archived"]
            params = [persona_id]
            param_count = 1
            
            if memory_type:
                param_count += 1
                where_clauses.append(f"memory_type = ${param_count}")
                params.append(memory_type.value)
            
            # Text search with ranking
            param_count += 1
            where_clauses.append(f"(content ILIKE ${param_count} OR summary ILIKE ${param_count})")
            params.append(f"%{query}%")
            
            query_sql = f"""
                SELECT *, 
                       ts_rank(to_tsvector('english', content), plainto_tsquery('english', $2)) as rank
                FROM memories 
                WHERE {' AND '.join(where_clauses)}
                ORDER BY rank DESC, importance_score DESC, created_at DESC
                LIMIT {limit}
            """
            
            rows = await conn.fetch(query_sql, *params)
            return [dict(row) for row in rows]
    
    async def cleanup_old_data(self) -> None:
        """Cleanup old data based on retention policies"""
        async with self.pool.acquire() as conn:
            # Archive old system health data (keep 30 days)
            await conn.execute("""
                DELETE FROM system_health 
                WHERE timestamp < NOW() - INTERVAL '30 days'
            """)
            
            # Archive old interactions (keep 90 days)
            await conn.execute("""
                DELETE FROM interactions 
                WHERE created_at < NOW() - INTERVAL '90 days'
            """)
            
            # Archive low-importance memories (keep 1 year)
            await conn.execute("""
                UPDATE memories SET is_archived = true
                WHERE created_at < NOW() - INTERVAL '1 year'
                AND importance_score < 0.3
                AND NOT is_archived
            """)
    
    async def close(self) -> None:
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            self.logger.info("Database connection pool closed")

# Global database manager instance
db_manager = DatabaseManager()

async def initialize_database():
    """Initialize the production database"""
    await db_manager.initialize()

async def get_database():
    """Get database manager instance"""
    return db_manager

