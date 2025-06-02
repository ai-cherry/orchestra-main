#!/usr/bin/env python3
"""
Unified memory management using only PostgreSQL and Weaviate.
Replaces all Redis, MongoDB, Firestore, and other storage systems.
PostgreSQL handles all structured data, Weaviate handles all vector operations.
"""

import json
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from enum import Enum
import asyncpg
from asyncpg.pool import Pool
import weaviate
from weaviate.exceptions import WeaviateException
import numpy as np
import logging

logger = logging.getLogger(__name__)

class MemoryType(str, Enum):
    """Types of memory storage."""
    SHORT_TERM = "short_term"  # PostgreSQL with TTL
    LONG_TERM = "long_term"    # PostgreSQL persistent
    SEMANTIC = "semantic"      # Weaviate vector storage

class UnifiedMemoryManager:
    """
    Unified memory manager using PostgreSQL for all data and Weaviate for vectors.
    Provides a complete replacement for Redis, MongoDB, and Firestore.
    """
    
    def __init__(
        self,
        postgres_dsn: str,
        weaviate_url: str,
        weaviate_api_key: Optional[str] = None,
        pool_size: int = 20,
        default_ttl: int = 3600,
    ):
        """
        Initialize unified memory manager.
        
        Args:
            postgres_dsn: PostgreSQL connection string
            weaviate_url: Weaviate server URL
            weaviate_api_key: Optional Weaviate API key
            pool_size: PostgreSQL connection pool size
            default_ttl: Default TTL for short-term memories
        """
        self.postgres_dsn = postgres_dsn
        self.weaviate_url = weaviate_url
        self.weaviate_api_key = weaviate_api_key
        self.pool_size = pool_size
        self.default_ttl = default_ttl
        
        self.pg_pool: Optional[Pool] = None
        self.weaviate_client: Optional[weaviate.Client] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def initialize(self):
        """Initialize PostgreSQL and Weaviate connections."""
        # Initialize PostgreSQL
        self.pg_pool = await asyncpg.create_pool(
            self.postgres_dsn,
            min_size=5,
            max_size=self.pool_size,
            command_timeout=60,
            server_settings={
                'jit': 'on',
                'max_parallel_workers_per_gather': '4',
            }
        )
        
        # Create PostgreSQL tables
        await self._create_postgresql_schema()
        
        # Initialize Weaviate
        auth_config = None
        if self.weaviate_api_key:
            auth_config = weaviate.AuthApiKey(api_key=self.weaviate_api_key)
            
        self.weaviate_client = weaviate.Client(
            url=self.weaviate_url,
            auth_client_secret=auth_config
        )
        
        # Create Weaviate schema
        self._create_weaviate_schema()
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_memories())
        
        logger.info("Unified memory manager initialized")
        
    async def close(self):
        """Close all connections."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
                
        if self.pg_pool:
            await self.pg_pool.close()
            
    async def _create_postgresql_schema(self):
        """Create PostgreSQL schema for memory storage."""
        async with self.pg_pool.acquire() as conn:
            # Create memories table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    memory_type TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    user_id TEXT,
                    conversation_id TEXT,
                    content TEXT NOT NULL,
                    metadata JSONB DEFAULT '{}',
                    embedding_id UUID,  -- Reference to Weaviate
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP WITH TIME ZONE,
                    access_count INTEGER DEFAULT 1,
                    importance FLOAT DEFAULT 0.5,
                    is_active BOOLEAN DEFAULT true
                )
            """)
            
            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_agent_id 
                ON memories (agent_id) WHERE is_active = true;
                
                CREATE INDEX IF NOT EXISTS idx_memories_user_id 
                ON memories (user_id) WHERE is_active = true;
                
                CREATE INDEX IF NOT EXISTS idx_memories_conversation_id 
                ON memories (conversation_id) WHERE is_active = true;
                
                CREATE INDEX IF NOT EXISTS idx_memories_expires_at 
                ON memories (expires_at) WHERE is_active = true AND expires_at IS NOT NULL;
                
                CREATE INDEX IF NOT EXISTS idx_memories_metadata 
                ON memories USING GIN (metadata);
                
                CREATE INDEX IF NOT EXISTS idx_memories_importance 
                ON memories (importance DESC) WHERE is_active = true;
            """)
            
            # Create update trigger
            await conn.execute("""
                CREATE OR REPLACE FUNCTION update_memories_updated_at()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
                
                DROP TRIGGER IF EXISTS update_memories_updated_at ON memories;
                
                CREATE TRIGGER update_memories_updated_at 
                BEFORE UPDATE ON memories
                FOR EACH ROW EXECUTE FUNCTION update_memories_updated_at();
            """)
            
    def _create_weaviate_schema(self):
        """Create Weaviate schema for vector storage."""
        try:
            # Check if schema exists
            existing = self.weaviate_client.schema.get()
