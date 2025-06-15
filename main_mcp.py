#!/usr/bin/env python3
"""
Orchestra AI - Memory Management MCP Server
Port: 8003

Handles memory management, context persistence, and data caching for the Orchestra AI platform.
Integrates with PostgreSQL, Redis, and Weaviate for comprehensive memory solutions.
"""

import sys
import os
# Correctly add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

import asyncpg
import redis.asyncio as redis
import weaviate
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import structlog
import uvicorn

# Configure structured logging
logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger(__name__)

# Configuration
CONFIG = {
    "port": 8003,
    "host": "0.0.0.0",
    "postgres_host": os.getenv("POSTGRES_HOST", "45.77.87.106"),
    "postgres_port": int(os.getenv("POSTGRES_PORT", "5432")),
    "postgres_db": os.getenv("POSTGRES_DB", "orchestra_ai"),
    "postgres_user": os.getenv("POSTGRES_USER", "postgres"),
    "postgres_password": os.getenv("POSTGRES_PASSWORD", "password"),
    "redis_host": os.getenv("REDIS_HOST", "45.77.87.106"),
    "redis_port": int(os.getenv("REDIS_PORT", "6379")),
    "weaviate_host": os.getenv("WEAVIATE_HOST", "45.77.87.106"),
    "weaviate_port": int(os.getenv("WEAVIATE_PORT", "8080")),
    "environment": os.getenv("ENVIRONMENT", "development")
}

# Data Models
@dataclass
class MemoryEntry:
    id: str
    type: str  # 'conversation', 'context', 'user_preference', 'system_state'
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime] = None
    accessed_count: int = 0
    last_accessed: Optional[datetime] = None

class MemoryRequest(BaseModel):
    memory_type: str = Field(..., description="Type of memory: conversation, context, user_preference, system_state")
    content: Dict[str, Any] = Field(..., description="Memory content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    ttl_seconds: Optional[int] = Field(None, description="Time to live in seconds")
    user_id: Optional[str] = Field(None, description="User ID for scoped memory")
    session_id: Optional[str] = Field(None, description="Session ID for scoped memory")

class MemoryQuery(BaseModel):
    memory_type: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata_filter: Optional[Dict[str, Any]] = None
    limit: int = Field(default=50, le=1000)
    offset: int = Field(default=0, ge=0)

class MemoryResponse(BaseModel):
    id: str
    type: str
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: str
    accessed_count: int
    last_accessed: Optional[str] = None

# Database Connections
class DatabaseManager:
    def __init__(self):
        self.postgres_pool: Optional[asyncpg.Pool] = None
        self.redis_client: Optional[redis.Redis] = None
        self.weaviate_client: Optional[weaviate.Client] = None
        
    async def initialize(self):
        """Initialize all database connections."""
        try:
            # PostgreSQL Connection Pool
            if CONFIG["environment"] != "development":
                self.postgres_pool = await asyncpg.create_pool(
                    host=CONFIG["postgres_host"],
                    port=CONFIG["postgres_port"],
                    database=CONFIG["postgres_db"],
                    user=CONFIG["postgres_user"],
                    password=CONFIG["postgres_password"],
                    min_size=5,
                    max_size=20
                )
                logger.info("PostgreSQL connection pool initialized")
            else:
                logger.info("Development mode: PostgreSQL disabled")
            
            # Redis Connection
            if CONFIG["environment"] != "development":
                self.redis_client = redis.Redis(
                    host=CONFIG["redis_host"],
                    port=CONFIG["redis_port"],
                    decode_responses=True,
                    retry_on_timeout=True,
                    socket_keepalive=True,
                    socket_keepalive_options={}
                )
                await self.redis_client.ping()
                logger.info("Redis connection established")
            else:
                logger.info("Development mode: Redis disabled")
            
            # Weaviate Connection
            if CONFIG["environment"] != "development":
                self.weaviate_client = weaviate.Client(
                    url=f"http://{CONFIG['weaviate_host']}:{CONFIG['weaviate_port']}"
                )
                logger.info("Weaviate connection established")
            else:
                logger.info("Development mode: Weaviate disabled")
                
            await self._create_tables()
            
        except Exception as e:
            logger.error("Failed to initialize databases", error=str(e))
            raise
    
    async def _create_tables(self):
        """Create necessary database tables."""
        if not self.postgres_pool:
            return
            
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS memory_entries (
            id VARCHAR(255) PRIMARY KEY,
            type VARCHAR(100) NOT NULL,
            content JSONB NOT NULL,
            metadata JSONB DEFAULT '{}',
            user_id VARCHAR(255),
            session_id VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            expires_at TIMESTAMP WITH TIME ZONE,
            accessed_count INTEGER DEFAULT 0,
            last_accessed TIMESTAMP WITH TIME ZONE,
            INDEX(type),
            INDEX(user_id),
            INDEX(session_id),
            INDEX(created_at),
            INDEX(expires_at)
        );
        """
        
        async with self.postgres_pool.acquire() as conn:
            await conn.execute(create_table_sql)
            logger.info("Memory tables created/verified")
    
    async def close(self):
        """Close all database connections."""
        if self.postgres_pool:
            await self.postgres_pool.close()
        if self.redis_client:
            await self.redis_client.close()
        logger.info("Database connections closed")

# Memory Management Service
class MemoryManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.local_cache: Dict[str, MemoryEntry] = {}  # Local fallback cache
        
    async def store_memory(self, memory_req: MemoryRequest) -> str:
        """Store a memory entry."""
        memory_id = f"{memory_req.memory_type}_{datetime.now().isoformat()}_{hash(str(memory_req.content))}"
        expires_at = None
        if memory_req.ttl_seconds:
            expires_at = datetime.now() + timedelta(seconds=memory_req.ttl_seconds)
        
        memory_entry = MemoryEntry(
            id=memory_id,
            type=memory_req.memory_type,
            content=memory_req.content,
            metadata={
                **memory_req.metadata,
                "user_id": memory_req.user_id,
                "session_id": memory_req.session_id
            },
            created_at=datetime.now(),
            expires_at=expires_at
        )
        
        # Store in PostgreSQL (primary)
        if self.db.postgres_pool:
            try:
                async with self.db.postgres_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO memory_entries 
                        (id, type, content, metadata, user_id, session_id, created_at, expires_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """, memory_entry.id, memory_entry.type, json.dumps(memory_entry.content),
                    json.dumps(memory_entry.metadata), memory_req.user_id, memory_req.session_id,
                    memory_entry.created_at, memory_entry.expires_at)
                    
                logger.info("Memory stored in PostgreSQL", memory_id=memory_id)
            except Exception as e:
                logger.error("Failed to store in PostgreSQL", error=str(e))
        
        # Store in Redis (cache)
        if self.db.redis_client:
            try:
                redis_key = f"memory:{memory_id}"
                redis_data = json.dumps(asdict(memory_entry), default=str)
                if memory_req.ttl_seconds:
                    await self.db.redis_client.setex(redis_key, memory_req.ttl_seconds, redis_data)
                else:
                    await self.db.redis_client.set(redis_key, redis_data)
                    
                logger.info("Memory cached in Redis", memory_id=memory_id)
            except Exception as e:
                logger.error("Failed to cache in Redis", error=str(e))
        
        # Store in local cache (fallback)
        self.local_cache[memory_id] = memory_entry
        logger.info("Memory stored locally", memory_id=memory_id)
        
        return memory_id
    
    async def retrieve_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by ID."""
        # Try Redis first (fastest)
        if self.db.redis_client:
            try:
                redis_key = f"memory:{memory_id}"
                redis_data = await self.db.redis_client.get(redis_key)
                if redis_data:
                    data = json.loads(redis_data)
                    memory_entry = MemoryEntry(**data)
                    await self._update_access_stats(memory_id)
                    logger.info("Memory retrieved from Redis", memory_id=memory_id)
                    return memory_entry
            except Exception as e:
                logger.error("Failed to retrieve from Redis", error=str(e))
        
        # Try PostgreSQL (primary)
        if self.db.postgres_pool:
            try:
                async with self.db.postgres_pool.acquire() as conn:
                    row = await conn.fetchrow("""
                        SELECT id, type, content, metadata, created_at, expires_at, accessed_count, last_accessed
                        FROM memory_entries WHERE id = $1 AND (expires_at IS NULL OR expires_at > NOW())
                    """, memory_id)
                    
                    if row:
                        memory_entry = MemoryEntry(
                            id=row['id'],
                            type=row['type'],
                            content=json.loads(row['content']),
                            metadata=json.loads(row['metadata']),
                            created_at=row['created_at'],
                            expires_at=row['expires_at'],
                            accessed_count=row['accessed_count'],
                            last_accessed=row['last_accessed']
                        )
                        await self._update_access_stats(memory_id)
                        logger.info("Memory retrieved from PostgreSQL", memory_id=memory_id)
                        return memory_entry
            except Exception as e:
                logger.error("Failed to retrieve from PostgreSQL", error=str(e))
        
        # Try local cache (fallback)
        if memory_id in self.local_cache:
            memory_entry = self.local_cache[memory_id]
            if not memory_entry.expires_at or memory_entry.expires_at > datetime.now():
                memory_entry.accessed_count += 1
                memory_entry.last_accessed = datetime.now()
                logger.info("Memory retrieved from local cache", memory_id=memory_id)
                return memory_entry
            else:
                del self.local_cache[memory_id]  # Remove expired
        
        logger.warning("Memory not found", memory_id=memory_id)
        return None
    
    async def query_memories(self, query: MemoryQuery) -> List[MemoryEntry]:
        """Query memories based on criteria."""
        memories = []
        
        # Query PostgreSQL (primary)
        if self.db.postgres_pool:
            try:
                sql = """
                    SELECT id, type, content, metadata, created_at, expires_at, accessed_count, last_accessed
                    FROM memory_entries 
                    WHERE (expires_at IS NULL OR expires_at > NOW())
                """
                params = []
                param_count = 0
                
                if query.memory_type:
                    param_count += 1
                    sql += f" AND type = ${param_count}"
                    params.append(query.memory_type)
                
                if query.user_id:
                    param_count += 1
                    sql += f" AND user_id = ${param_count}"
                    params.append(query.user_id)
                
                if query.session_id:
                    param_count += 1
                    sql += f" AND session_id = ${param_count}"
                    params.append(query.session_id)
                
                sql += f" ORDER BY created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
                params.extend([query.limit, query.offset])
                
                async with self.db.postgres_pool.acquire() as conn:
                    rows = await conn.fetch(sql, *params)
                    
                    for row in rows:
                        memory_entry = MemoryEntry(
                            id=row['id'],
                            type=row['type'],
                            content=json.loads(row['content']),
                            metadata=json.loads(row['metadata']),
                            created_at=row['created_at'],
                            expires_at=row['expires_at'],
                            accessed_count=row['accessed_count'],
                            last_accessed=row['last_accessed']
                        )
                        memories.append(memory_entry)
                
                logger.info("Memories queried from PostgreSQL", count=len(memories))
                return memories
                
            except Exception as e:
                logger.error("Failed to query PostgreSQL", error=str(e))
        
        # Fallback to local cache
        for memory_id, memory_entry in self.local_cache.items():
            if memory_entry.expires_at and memory_entry.expires_at <= datetime.now():
                continue  # Skip expired
            
            if query.memory_type and memory_entry.type != query.memory_type:
                continue
            
            if query.user_id and memory_entry.metadata.get("user_id") != query.user_id:
                continue
            
            if query.session_id and memory_entry.metadata.get("session_id") != query.session_id:
                continue
            
            memories.append(memory_entry)
        
        # Sort and paginate
        memories.sort(key=lambda x: x.created_at, reverse=True)
        start_idx = query.offset
        end_idx = start_idx + query.limit
        
        logger.info("Memories queried from local cache", count=len(memories[start_idx:end_idx]))
        return memories[start_idx:end_idx]
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory entry."""
        deleted = False
        
        # Delete from PostgreSQL
        if self.db.postgres_pool:
            try:
                async with self.db.postgres_pool.acquire() as conn:
                    result = await conn.execute("DELETE FROM memory_entries WHERE id = $1", memory_id)
                    if result == "DELETE 1":
                        deleted = True
                        logger.info("Memory deleted from PostgreSQL", memory_id=memory_id)
            except Exception as e:
                logger.error("Failed to delete from PostgreSQL", error=str(e))
        
        # Delete from Redis
        if self.db.redis_client:
            try:
                redis_key = f"memory:{memory_id}"
                await self.db.redis_client.delete(redis_key)
                logger.info("Memory deleted from Redis", memory_id=memory_id)
            except Exception as e:
                logger.error("Failed to delete from Redis", error=str(e))
        
        # Delete from local cache
        if memory_id in self.local_cache:
            del self.local_cache[memory_id]
            deleted = True
            logger.info("Memory deleted from local cache", memory_id=memory_id)
        
        return deleted
    
    async def _update_access_stats(self, memory_id: str):
        """Update access statistics for a memory entry."""
        if self.db.postgres_pool:
            try:
                async with self.db.postgres_pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE memory_entries 
                        SET accessed_count = accessed_count + 1, last_accessed = NOW()
                        WHERE id = $1
                    """, memory_id)
            except Exception as e:
                logger.error("Failed to update access stats", error=str(e))
    
    async def cleanup_expired(self):
        """Clean up expired memory entries."""
        # Clean PostgreSQL
        if self.db.postgres_pool:
            try:
                async with self.db.postgres_pool.acquire() as conn:
                    result = await conn.execute("""
                        DELETE FROM memory_entries 
                        WHERE expires_at IS NOT NULL AND expires_at <= NOW()
                    """)
                    logger.info("Expired memories cleaned from PostgreSQL", result=result)
            except Exception as e:
                logger.error("Failed to clean PostgreSQL", error=str(e))
        
        # Clean local cache
        expired_keys = []
        for memory_id, memory_entry in self.local_cache.items():
            if memory_entry.expires_at and memory_entry.expires_at <= datetime.now():
                expired_keys.append(memory_id)
        
        for key in expired_keys:
            del self.local_cache[key]
        
        if expired_keys:
            logger.info("Expired memories cleaned from local cache", count=len(expired_keys))

# Global instances
db_manager = DatabaseManager()
memory_manager = MemoryManager(db_manager)

# FastAPI Application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Memory Management MCP Server", port=CONFIG["port"])
    await db_manager.initialize()
    
    # Schedule cleanup task
    async def cleanup_task():
        while True:
            await asyncio.sleep(3600)  # Run every hour
            await memory_manager.cleanup_expired()
    
    cleanup_task_handle = asyncio.create_task(cleanup_task())
    
    yield
    
    # Shutdown
    cleanup_task_handle.cancel()
    await db_manager.close()
    logger.info("Memory Management MCP Server stopped")

app = FastAPI(
    title="Orchestra AI - Memory Management MCP Server",
    description="Memory management, context persistence, and data caching",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    status = {
        "status": "healthy",
        "service": "memory-management",
        "port": CONFIG["port"],
        "environment": CONFIG["environment"],
        "timestamp": datetime.now().isoformat(),
        "connections": {
            "postgres": bool(db_manager.postgres_pool),
            "redis": bool(db_manager.redis_client),
            "weaviate": bool(db_manager.weaviate_client)
        }
    }
    return status

@app.post("/memory", response_model=Dict[str, str])
async def store_memory_endpoint(memory_req: MemoryRequest):
    """Store a new memory entry."""
    try:
        memory_id = await memory_manager.store_memory(memory_req)
        return {"memory_id": memory_id, "status": "stored"}
    except Exception as e:
        logger.error("Failed to store memory", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/{memory_id}", response_model=MemoryResponse)
async def get_memory_endpoint(memory_id: str):
    """Retrieve a memory entry by ID."""
    try:
        memory_entry = await memory_manager.retrieve_memory(memory_id)
        if not memory_entry:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        return MemoryResponse(
            id=memory_entry.id,
            type=memory_entry.type,
            content=memory_entry.content,
            metadata=memory_entry.metadata,
            created_at=memory_entry.created_at.isoformat(),
            accessed_count=memory_entry.accessed_count,
            last_accessed=memory_entry.last_accessed.isoformat() if memory_entry.last_accessed else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve memory", memory_id=memory_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory/query", response_model=List[MemoryResponse])
async def query_memories_endpoint(query: MemoryQuery):
    """Query memories based on criteria."""
    try:
        memories = await memory_manager.query_memories(query)
        return [
            MemoryResponse(
                id=memory.id,
                type=memory.type,
                content=memory.content,
                metadata=memory.metadata,
                created_at=memory.created_at.isoformat(),
                accessed_count=memory.accessed_count,
                last_accessed=memory.last_accessed.isoformat() if memory.last_accessed else None
            )
            for memory in memories
        ]
    except Exception as e:
        logger.error("Failed to query memories", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/memory/{memory_id}")
async def delete_memory_endpoint(memory_id: str):
    """Delete a memory entry."""
    try:
        deleted = await memory_manager.delete_memory(memory_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        return {"memory_id": memory_id, "status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete memory", memory_id=memory_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory/cleanup")
async def cleanup_expired_endpoint(background_tasks: BackgroundTasks):
    """Manually trigger cleanup of expired memories."""
    background_tasks.add_task(memory_manager.cleanup_expired)
    return {"status": "cleanup_scheduled"}

@app.get("/metrics")
async def get_metrics():
    """Get memory management metrics."""
    return {
        "local_cache_size": len(memory_manager.local_cache),
        "environment": CONFIG["environment"],
        "connections": {
            "postgres": bool(db_manager.postgres_pool),
            "redis": bool(db_manager.redis_client),
            "weaviate": bool(db_manager.weaviate_client)
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Orchestra AI - Memory Management MCP Server",
        "version": "1.0.0",
        "port": CONFIG["port"],
        "environment": CONFIG["environment"],
        "endpoints": {
            "health": "/health",
            "store_memory": "POST /memory",
            "get_memory": "GET /memory/{memory_id}",
            "query_memories": "POST /memory/query",
            "delete_memory": "DELETE /memory/{memory_id}",
            "cleanup": "POST /memory/cleanup",
            "metrics": "/metrics"
        }
    }

# Main entry point
if __name__ == "__main__":
    logger.info("Starting Memory Management MCP Server", 
                port=CONFIG["port"], 
                environment=CONFIG["environment"])
    
    uvicorn.run(
        "memory_management_server:app",
        host=CONFIG["host"],
        port=CONFIG["port"],
        log_level="info",
        reload=CONFIG["environment"] == "development"
    ) 