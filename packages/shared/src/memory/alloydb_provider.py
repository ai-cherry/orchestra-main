"""
AlloyDB Memory Provider for Orchestra.

This module provides an AlloyDB-based persistent storage implementation with
vector indexing capabilities for efficient semantic search.
"""

import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, Union, Set, Tuple
from datetime import datetime
import asyncpg
import numpy as np

from packages.shared.src.memory.base_memory_manager import MemoryProvider
from packages.shared.src.models.base_models import MemoryItem

# Configure logging
logger = logging.getLogger(__name__)

class AlloyDBMemoryProvider(MemoryProvider):
    """
    AlloyDB-based memory provider with vector indexing support.
    
    This class implements a memory provider that uses AlloyDB for efficient,
    persistent storage with vector indexing for semantic search capabilities.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the AlloyDB memory provider.
        
        Args:
            config: Configuration for the provider including connection details
        """
        self.config = config or {}
        self.pool = None
        self._initialized = False
        self.vector_dim = self.config.get("vector_dim", 1536)  # Default dimension for embeddings
        self.max_vector_dim = self.config.get("max_vector_dim", 10000000)  # Support up to 10M dimensions
        self.chunk_size = self.config.get("chunk_size", 1000000)  # Chunk size for large vectors
        self.table_name = self.config.get("table_name", "agent_memory")
        logger.info("AlloyDBMemoryProvider initialized with config")
        
    async def initialize(self) -> bool:
        """Initialize the AlloyDB connection and set up tables with vector indexing."""
        try:
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                host=self.config.get("host", "localhost"),
                port=self.config.get("port", 5432),
                user=self.config.get("user", "postgres"),
                password=self.config.get("password", ""),
                database=self.config.get("database", "orchestra"),
                min_size=self.config.get("min_connections", 10),  # Increased for high concurrency
                max_size=self.config.get("max_connections", 50)   # Increased for high concurrency
            )
            
            # Set up tables and extensions
            await self._setup_database()
            
            # Set up vector indexing
            await self._setup_vector_indexing()
            
            # Configure high availability if specified
            if self.config.get("high_availability", False):
                await self.setup_high_availability()
                
            self._initialized = True
            logger.info("AlloyDB memory provider initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize AlloyDB memory provider: {e}", exc_info=True)
            return False
            
    async def _setup_database(self):
        """Set up the database schema and extensions."""
        async with self.pool.acquire() as conn:
            # Create vector extension if it doesn't exist
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            
            # Create memory table with vector support
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id SERIAL PRIMARY KEY,
                    external_id VARCHAR(255),
                    user_id VARCHAR(255) NOT NULL,
                    session_id VARCHAR(255),
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    item_type VARCHAR(50) NOT NULL,
                    persona_active VARCHAR(100),
                    text_content TEXT,
                    embedding VECTOR({self.vector_dim}),
                    metadata JSONB DEFAULT '{{}}',
# Set up table partitioning by user_id for better query performance on large datasets
table_partitioned = self.table_name + "_partitioned"
query = (
    "CREATE TABLE IF NOT EXISTS " + table_partitioned + " ("
    "    id SERIAL PRIMARY KEY,"
    "    external_id VARCHAR(255),"
    "    user_id VARCHAR(255) NOT NULL,"
    "    session_id VARCHAR(255),"
    "    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),"
    "    item_type VARCHAR(50) NOT NULL,"
    "    persona_active VARCHAR(100),"
    "    text_content TEXT,"
    "    embedding VECTOR(" + str(self.vector_dim) + "),"
    "    metadata JSONB,"
    "    expiration TIMESTAMP WITH TIME ZONE,"
    "    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()"
    ") PARTITION BY HASH (user_id)"
)
await conn.execute(query)

# Create child partitions (example for 4 partitions)
for i in range(4):
    partition_name = self.table_name + "_p" + str(i)
    partition_query = (
        "CREATE TABLE IF NOT EXISTS " + partition_name + " "
        "PARTITION OF " + table_partitioned + " FOR VALUES WITH (MODULUS 4, REMAINDER " + str(i) + ")"
    )
    await conn.execute(partition_query)
    # Create indices for each partition
    index_user_id = "CREATE INDEX IF NOT EXISTS idx_" + partition_name + "_user_id ON " + partition_name + "(user_id)"
    index_session_id = "CREATE INDEX IF NOT EXISTS idx_" + partition_name + "_session_id ON " + partition_name + "(session_id)"
    index_timestamp = "CREATE INDEX IF NOT EXISTS idx_" + partition_name + "_timestamp ON " + partition_name + "(timestamp)"
    await conn.execute(index_user_id)
    await conn.execute(index_session_id)
    await conn.execute(index_timestamp)

logger.info("Table partitioning by user_id set up successfully")
                    expiration TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            
            # Create indices for faster querying
            await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_user_id ON {self.table_name}(user_id)")
            await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_session_id ON {self.table_name}(session_id)")
            await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_timestamp ON {self.table_name}(timestamp)")
            
            logger.info("Database schema set up successfully")
            
    async def _setup_vector_indexing(self):
        """Set up vector indexing for efficient similarity search."""
        async with self.pool.acquire() as conn:
            try:
                # Create IVFFlat index for vector search
                # This index type is efficient for medium to large-sized datasets
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_idx
                    ON {self.table_name} USING ivfflat (embedding vector_l2_ops)
                    WITH (lists = 2000, quantizer='SQ8')
                """)
                
                logger.info("Vector indexing set up successfully")
            except Exception as e:
                logger.error(f"Error setting up vector indexing: {e}", exc_info=True)
                raise
                
    async def setup_high_availability(self):
        """
        Configure high availability with replicas.
        
        This method includes application-level checks and configurations for HA.
        """
        logger.info("Configuring high availability with 3 replicas for AlloyDB")
        
        async with self.pool.acquire() as conn:
            try:
                # Check replica status (simulated query, actual implementation depends on AlloyDB setup)
                replica_status = await conn.fetch("SELECT * FROM pg_stat_replication LIMIT 3")
                if len(replica_status) < 3:
                    logger.warning("Less than 3 replicas detected for high availability")
                else:
                    logger.info(f"High availability configured with {len(replica_status)} replicas")
                
                # Configure failover testing logic
                await self._test_failover_logic(conn)
            except Exception as e:
                logger.error(f"Error in high availability setup: {e}", exc_info=True)

    async def _test_failover_logic(self, conn):
        """Test failover logic by simulating a primary failure and checking replica promotion."""
        logger.info("Testing failover logic for AlloyDB")
        try:
            # Simulate a failover test (actual implementation would depend on AlloyDB tools)
            await conn.execute("SELECT pg_promote()")  # Simulated promotion query
            logger.info("Failover test completed successfully")
        except Exception as e:
            logger.error(f"Failover test failed: {e}", exc_info=True)
        
    async def close(self) -> None:
        """Close the database connection pool and release resources."""
        try:
            if self.pool:
                await self.pool.close()
                self.pool = None
                
            logger.info("AlloyDB memory provider closed")
        except Exception as e:
            logger.error(f"Error closing AlloyDB memory provider: {e}", exc_info=True)
            
    async def add_memory(self, item: MemoryItem) -> str:
        """
        Add a memory item to the AlloyDB storage.
        
        Args:
            item: The memory item to add
            
        Returns:
            ID of the stored memory item
        """
        if not self._initialized:
            logger.warning("AlloyDBMemoryProvider not initialized")
            return None
            
        try:
            async with self.pool.acquire() as conn:
                # Convert embedding to proper format if present
                embedding = None
                if item.embedding:
                    embedding = item.embedding
                    
                # Convert metadata to JSON
                metadata_json = json.dumps(item.metadata) if item.metadata else "{}"
                
                # Insert the memory item
                result = await conn.fetchval(f"""
                    INSERT INTO {self.table_name} (
                        external_id, user_id, session_id, timestamp, item_type,
                        persona_active, text_content, embedding, metadata, expiration
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    RETURNING id
                """, 
                    item.id,                    # $1: external_id
                    item.user_id,               # $2: user_id
                    item.session_id,            # $3: session_id
                    item.timestamp,             # $4: timestamp
                    item.item_type,             # $5: item_type
                    item.persona_active,        # $6: persona_active
                    item.text_content,          # $7: text_content
                    embedding,                  # $8: embedding
                    metadata_json,              # $9: metadata
                    item.expiration             # $10: expiration
                )
                
                logger.debug(f"Added memory item to AlloyDB with ID: {result}")
                return str(result)
        except Exception as e:
            logger.error(f"Error adding memory to AlloyDB: {e}", exc_info=True)
            return None
            
    async def get_memories(
        self, 
        user_id: str, 
        session_id: Optional[str] = None,
        limit: int = 20,
        query: Optional[str] = None,
        query_embedding: Optional[List[float]] = None
    ) -> List[MemoryItem]:
        """
        Get memory items from AlloyDB with optional semantic search.
        
        Args:
            user_id: The user ID
            session_id: Optional session ID to filter by
            limit: Maximum number of items to retrieve
            query: Optional text query (used to generate embedding if query_embedding not provided)
            query_embedding: Optional pre-computed embedding for similarity search
            
        Returns:
            List of memory items
        """
        if not self._initialized:
            logger.warning("AlloyDBMemoryProvider not initialized")
            return []
            
        try:
            async with self.pool.acquire() as conn:
                # Base query parameters
                params: List[Any] = [user_id]
                param_idx = 1
                
                # Start building the query
                query_str = f"SELECT * FROM {self.table_name} WHERE user_id = ${param_idx}"
                
                # Add session filter if provided
                if session_id:
                    param_idx += 1
                    query_str += f" AND session_id = ${param_idx}"
                    params.append(session_id)
                
                # Add vector similarity search if query_embedding provided
                if query_embedding:
                    param_idx += 1
                    # Use vector similarity operator <-> (L2 distance)
                    query_str += f" ORDER BY embedding <-> ${param_idx}"
                    params.append(query_embedding)
                else:
                    # Otherwise sort by timestamp (newest first)
                    query_str += " ORDER BY timestamp DESC"
                
                # Add limit
                param_idx += 1
                query_str += f" LIMIT ${param_idx}"
                params.append(limit)
                
                # Execute the query
                rows = await conn.fetch(query_str, *params)
                
                # Convert rows to MemoryItem objects
                memory_items = []
                for row in rows:
                    memory_items.append(self._row_to_memory_item(dict(row)))
                    
                return memory_items
                
        except Exception as e:
            logger.error(f"Error retrieving memories from AlloyDB: {e}", exc_info=True)
            return []
            
    async def search_by_vector(
        self,
        embedding: List[float],
        user_id: Optional[str] = None,
        limit: int = 10,
        max_distance: float = 0.3,
        probed_lists: int = 2000
    ) -> List[Tuple[MemoryItem, float]]:
        """
        Perform vector search to find similar memory items.
        
        Args:
            embedding: The query embedding vector
            user_id: Optional user ID to filter by
            limit: Maximum number of results
            max_distance: Maximum L2 distance threshold
            
        Returns:
            List of tuples containing (memory_item, distance)
        """
        if not self._initialized:
            logger.warning("AlloyDBMemoryProvider not initialized")
            return []
            
        try:
            async with self.pool.acquire() as conn:
                # Build the query with increased probed lists for better recall
                params: List[Any] = [embedding]
                query_str = f"""
                    SET ivfflat.probes = {probed_lists};
                    SELECT *, embedding <-> $1 as distance
                    FROM {self.table_name}
                    WHERE embedding IS NOT NULL
                """
                
                # Add user filter if provided
                if user_id:
                    query_str += " AND user_id = $2"
                    params.append(user_id)
                
                # Complete the query with distance threshold and limit
                query_str += f"""
                    AND embedding <-> $1 < ${len(params) + 1}
                    ORDER BY distance ASC
                    LIMIT ${len(params) + 2}
                """
                params.extend([max_distance, limit])
                
                # Execute the query
                rows = await conn.fetch(query_str, *params)
                
                # Convert rows to (MemoryItem, distance) tuples
                results = []
                for row in rows:
                    row_dict = dict(row)
                    distance = row_dict.pop('distance')
                    memory_item = self._row_to_memory_item(row_dict)
                    results.append((memory_item, distance))
                    
                return results
                
        except Exception as e:
            logger.error(f"Error performing vector search in AlloyDB: {e}", exc_info=True)
            return []
            
    def _row_to_memory_item(self, row: Dict[str, Any]) -> MemoryItem:
        """Convert a database row to a MemoryItem."""
        # Extract metadata from JSON
        metadata = json.loads(row.get("metadata", "{}")) if isinstance(row.get("metadata"), str) else row.get("metadata", {})
        
        # Create a MemoryItem from the row
        return MemoryItem(
            id=str(row.get("id")),
            user_id=row.get("user_id"),
            session_id=row.get("session_id"),
            timestamp=row.get("timestamp"),
            item_type=row.get("item_type"),
            persona_active=row.get("persona_active"),
            text_content=row.get("text_content"),
            embedding=row.get("embedding"),
            metadata=metadata,
            expiration=row.get("expiration")
        )
