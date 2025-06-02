"""
PostgreSQL Storage Implementation

High-performance PostgreSQL storage for L3 tier with connection pooling,
prepared statements, and optimized indexing.
"""

import asyncio
import json
import pickle
import lz4.frame
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import asyncpg
from asyncpg.pool import Pool

from ...interfaces import IMemoryStorage, MemoryItem, MemoryTier
from ...config import PostgreSQLConfig
from ...exceptions import (
    MemoryStorageError,
    MemoryConnectionError,
    MemorySerializationError,
    MemoryNotFoundError,
    MemoryTimeoutError
)

logger = logging.getLogger(__name__)

class PostgreSQLStorage(IMemoryStorage):
    """
    PostgreSQL storage implementation optimized for performance.
    
    Features:
    - Connection pooling with asyncpg
    - Prepared statements for common queries
    - Optimized indexes for fast lookups
    - JSONB for metadata storage
    - Binary data compression
    - Batch operations support
    - Automatic vacuum and analyze
    """
    
    def __init__(
        self,
        tier: MemoryTier,
        config: PostgreSQLConfig,
        table_name: str = "memory_items",
        compression_enabled: bool = True,
        compression_threshold: int = 1024
    ):
        self.tier = tier
        self.config = config
        self.table_name = table_name
        self.compression_enabled = compression_enabled
        self.compression_threshold = compression_threshold
        
        self._pool: Optional[Pool] = None
        self._prepared_statements: Dict[str, str] = {}
        
        logger.info(
            f"Initialized PostgreSQLStorage for tier {tier.value} "
            f"with table {table_name}"
        )
    
    async def initialize(self) -> None:
        """Initialize PostgreSQL connection pool and schema."""
        try:
            # Create connection pool
            self._pool = await asyncpg.create_pool(
                self.config.connection_string,
                min_size=self.config.pool_size_min,
                max_size=self.config.pool_size_max,
                max_queries=self.config.max_queries,
                max_inactive_connection_lifetime=300,
                command_timeout=self.config.command_timeout,
                statement_cache_size=self.config.statement_cache_size,
                server_settings={
                    'jit': 'on',
                    'work_mem': '256MB',
                    'maintenance_work_mem': '1GB',
                    'effective_cache_size': '4GB',
                    'random_page_cost': '1.1',  # SSD optimization
                }
            )
            
            # Create schema
            await self._create_schema()
            
            # Prepare common statements
            await self._prepare_statements()
            
            # Optimize indexes
            await self._optimize_indexes()
            
            logger.info(f"PostgreSQL storage initialized for tier {self.tier.value}")
            
        except Exception as e:
            raise MemoryConnectionError(
                backend="postgresql",
                host=self.config.host,
                port=self.config.port,
                reason=str(e),
                cause=e
            )
    
    async def _create_schema(self) -> None:
        """Create the memory items table if it doesn't exist."""
        async with self._pool.acquire() as conn:
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    key TEXT PRIMARY KEY,
                    value BYTEA NOT NULL,
                    metadata JSONB NOT NULL DEFAULT '{{}}',
                    tier TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    access_count INTEGER NOT NULL DEFAULT 0,
                    size_bytes INTEGER NOT NULL,
                    ttl_seconds INTEGER,
                    expires_at TIMESTAMPTZ,
                    checksum TEXT NOT NULL,
                    compressed BOOLEAN NOT NULL DEFAULT FALSE
                );
                
                -- Create indexes
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_tier 
                ON {self.table_name} (tier);
                
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_accessed_at 
                ON {self.table_name} (accessed_at DESC);
                
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_expires_at 
                ON {self.table_name} (expires_at) 
                WHERE expires_at IS NOT NULL;
                
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_metadata 
                ON {self.table_name} USING GIN (metadata);
                
                -- Create function for automatic expiry calculation
                CREATE OR REPLACE FUNCTION calculate_expires_at()
                RETURNS TRIGGER AS $$
                BEGIN
                    IF NEW.ttl_seconds IS NOT NULL THEN
                        NEW.expires_at = NOW() + (NEW.ttl_seconds || ' seconds')::INTERVAL;
                    END IF;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
                
                -- Create trigger
                DROP TRIGGER IF EXISTS {self.table_name}_calculate_expiry ON {self.table_name};
                CREATE TRIGGER {self.table_name}_calculate_expiry
                BEFORE INSERT OR UPDATE ON {self.table_name}
                FOR EACH ROW
                EXECUTE FUNCTION calculate_expires_at();
            """)
    
    async def _prepare_statements(self) -> None:
        """Prepare common SQL statements for performance."""
        async with self._pool.acquire() as conn:
            # Get statement
            self._prepared_statements['get'] = await conn.prepare(f"""
                SELECT value, metadata, tier, created_at, accessed_at, 
                       access_count, size_bytes, ttl_seconds, checksum, compressed
                FROM {self.table_name}
                WHERE key = $1 AND (expires_at IS NULL OR expires_at > NOW())
            """)
            
            # Update access statement
            self._prepared_statements['update_access'] = await conn.prepare(f"""
                UPDATE {self.table_name}
                SET accessed_at = NOW(), access_count = access_count + 1
                WHERE key = $1
            """)
            
            # Set statement
            self._prepared_statements['set'] = await conn.prepare(f"""
                INSERT INTO {self.table_name} 
                (key, value, metadata, tier, created_at, accessed_at, 
                 access_count, size_bytes, ttl_seconds, checksum, compressed)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (key) DO UPDATE
                SET value = $2, metadata = $3, tier = $4, 
                    accessed_at = $6, access_count = {self.table_name}.access_count + 1,
                    size_bytes = $8, ttl_seconds = $9, checksum = $10, compressed = $11
            """)
            
            # Delete statement
            self._prepared_statements['delete'] = await conn.prepare(f"""
                DELETE FROM {self.table_name} WHERE key = $1
            """)
            
            # Exists statement
            self._prepared_statements['exists'] = await conn.prepare(f"""
                SELECT 1 FROM {self.table_name} 
                WHERE key = $1 AND (expires_at IS NULL OR expires_at > NOW())
                LIMIT 1
            """)
    
    async def _optimize_indexes(self) -> None:
        """Create optimized indexes based on access patterns."""
        async with self._pool.acquire() as conn:
            # Covering index for hot data
            await conn.execute(f"""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_{self.table_name}_hot_covering
                ON {self.table_name} (key, tier)
                INCLUDE (value, metadata, accessed_at)
                WHERE tier = '{self.tier.value}' AND access_count > 10
            """)
            
            # Partial index for recent data
            await conn.execute(f"""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_{self.table_name}_recent
                ON {self.table_name} (accessed_at DESC)
                WHERE accessed_at > NOW() - INTERVAL '7 days'
            """)
            
            # Update statistics
            await conn.execute(f"ANALYZE {self.table_name}")
    
    async def get(self, key: str) -> Optional[MemoryItem]:
        """Retrieve an item from PostgreSQL."""
        try:
            async with self._pool.acquire() as conn:
                # Use prepared statement
                stmt = self._prepared_statements.get('get')
                if stmt:
                    row = await stmt.fetchrow(key)
                else:
                    row = await conn.fetchrow(f"""
                        SELECT value, metadata, tier, created_at, accessed_at, 
                               access_count, size_bytes, ttl_seconds, checksum, compressed
                        FROM {self.table_name}
                        WHERE key = $1 AND (expires_at IS NULL OR expires_at > NOW())
                    """, key)
                
                if not row:
                    return None
                
                # Update access info
                update_stmt = self._prepared_statements.get('update_access')
                if update_stmt:
                    await update_stmt.execute(key)
                else:
                    await conn.execute(f"""
                        UPDATE {self.table_name}
                        SET accessed_at = NOW(), access_count = access_count + 1
                        WHERE key = $1
                    """, key)
                
                # Deserialize value
                value = self._deserialize_value(row['value'], row['compressed'])
                
                # Create MemoryItem
                return MemoryItem(
                    key=key,
                    value=value,
                    metadata=dict(row['metadata']),
                    tier=MemoryTier(row['tier']),
                    created_at=row['created_at'],
                    accessed_at=row['accessed_at'],
                    access_count=row['access_count'] + 1,
                    size_bytes=row['size_bytes'],
                    ttl_seconds=row['ttl_seconds'],
                    checksum=row['checksum']
                )
                
        except asyncio.TimeoutError:
            raise MemoryTimeoutError(
                operation="get",
                timeout_seconds=self.config.command_timeout,
                key=key
            )
        except Exception as e:
            logger.error(f"Failed to get item {key}: {str(e)}")
            raise MemoryStorageError(
                operation="get",
                storage_backend="postgresql",
                reason=str(e),
                key=key,
                cause=e
            )
    
    async def set(self, item: MemoryItem) -> bool:
        """Store an item in PostgreSQL."""
        try:
            # Serialize value
            serialized, compressed = self._serialize_value(item.value)
            
            async with self._pool.acquire() as conn:
                stmt = self._prepared_statements.get('set')
                if stmt:
                    await stmt.execute(
                        item.key,
                        serialized,
                        json.dumps(item.metadata),
                        item.tier.value,
                        item.created_at,
                        item.accessed_at,
                        item.access_count,
                        len(serialized),
                        item.ttl_seconds,
                        item.checksum,
                        compressed
                    )
                else:
                    await conn.execute(f"""
                        INSERT INTO {self.table_name} 
                        (key, value, metadata, tier, created_at, accessed_at, 
                         access_count, size_bytes, ttl_seconds, checksum, compressed)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                        ON CONFLICT (key) DO UPDATE
                        SET value = $2, metadata = $3, tier = $4, 
                            accessed_at = $6, access_count = {self.table_name}.access_count + 1,
                            size_bytes = $8, ttl_seconds = $9, checksum = $10, compressed = $11
                    """, item.key, serialized, json.dumps(item.metadata), item.tier.value,
                        item.created_at, item.accessed_at, item.access_count,
                        len(serialized), item.ttl_seconds, item.checksum, compressed)
                
                return True
                
        except asyncio.TimeoutError:
            raise MemoryTimeoutError(
                operation="set",
                timeout_seconds=self.config.command_timeout,
                key=item.key
            )
        except Exception as e:
            logger.error(f"Failed to set item {item.key}: {str(e)}")
            raise MemoryStorageError(
                operation="set",
                storage_backend="postgresql",
                reason=str(e),
                key=item.key,
                cause=e
            )
    
    async def delete(self, key: str) -> bool:
        """Delete an item from PostgreSQL."""
        try:
            async with self._pool.acquire() as conn:
                stmt = self._prepared_statements.get('delete')
                if stmt:
                    result = await stmt.execute(key)
                else:
                    result = await conn.execute(f"""
                        DELETE FROM {self.table_name} WHERE key = $1
                    """, key)
                
                # Check if row was deleted
                return result.split()[-1] != '0'
                
        except Exception as e:
            logger.error(f"Failed to delete item {key}: {str(e)}")
            raise MemoryStorageError(
                operation="delete",
                storage_backend="postgresql",
                reason=str(e),
                key=key,
                cause=e
            )
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in PostgreSQL."""
        try:
            async with self._pool.acquire() as conn:
                stmt = self._prepared_statements.get('exists')
                if stmt:
                    row = await stmt.fetchrow(key)
                else:
                    row = await conn.fetchrow(f"""
                        SELECT 1 FROM {self.table_name} 
                        WHERE key = $1 AND (expires_at IS NULL OR expires_at > NOW())
                        LIMIT 1
                    """, key)
                
                return row is not None
                
        except Exception as e:
            logger.error(f"Failed to check existence of {key}: {str(e)}")
            return False
    
    async def get_batch(self, keys: List[str]) -> Dict[str, Optional[MemoryItem]]:
        """Get multiple items in a single query."""
        if not keys:
            return {}
        
        try:
            async with self._pool.acquire() as conn:
                # Batch get
                rows = await conn.fetch(f"""
                    SELECT key, value, metadata, tier, created_at, accessed_at, 
                           access_count, size_bytes, ttl_seconds, checksum, compressed
                    FROM {self.table_name}
                    WHERE key = ANY($1) AND (expires_at IS NULL OR expires_at > NOW())
                """, keys)
                
                # Batch update access
                await conn.execute(f"""
                    UPDATE {self.table_name}
                    SET accessed_at = NOW(), access_count = access_count + 1
                    WHERE key = ANY($1)
                """, keys)
                
                # Build results
                results = {key: None for key in keys}
                
                for row in rows:
                    value = self._deserialize_value(row['value'], row['compressed'])
                    results[row['key']] = MemoryItem(
                        key=row['key'],
                        value=value,
                        metadata=dict(row['metadata']),
                        tier=MemoryTier(row['tier']),
                        created_at=row['created_at'],
                        accessed_at=row['accessed_at'],
                        access_count=row['access_count'] + 1,
                        size_bytes=row['size_bytes'],
                        ttl_seconds=row['ttl_seconds'],
                        checksum=row['checksum']
                    )
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to get batch: {str(e)}")
            raise MemoryStorageError(
                operation="get_batch",
                storage_backend="postgresql",
                reason=str(e),
                cause=e
            )
    
    async def set_batch(self, items: List[MemoryItem]) -> Dict[str, bool]:
        """Set multiple items in a single transaction."""
        if not items:
            return {}
        
        results = {item.key: False for item in items}
        
        try:
            async with self._pool.acquire() as conn:
                async with conn.transaction():
                    # Prepare batch data
                    values = []
                    for item in items:
                        serialized, compressed = self._serialize_value(item.value)
                        values.append((
                            item.key,
                            serialized,
                            json.dumps(item.metadata),
                            item.tier.value,
                            item.created_at,
                            item.accessed_at,
                            item.access_count,
                            len(serialized),
                            item.ttl_seconds,
                            item.checksum,
                            compressed
                        ))
                    
                    # Batch insert/update
                    await conn.executemany(f"""
                        INSERT INTO {self.table_name} 
                        (key, value, metadata, tier, created_at, accessed_at, 
                         access_count, size_bytes, ttl_seconds, checksum, compressed)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                        ON CONFLICT (key) DO UPDATE
                        SET value = EXCLUDED.value, metadata = EXCLUDED.metadata, 
                            tier = EXCLUDED.tier, accessed_at = EXCLUDED.accessed_at,
                            access_count = {self.table_name}.access_count + 1,
                            size_bytes = EXCLUDED.size_bytes, ttl_seconds = EXCLUDED.ttl_seconds,
                            checksum = EXCLUDED.checksum, compressed = EXCLUDED.compressed
                    """, values)
                    
                    # Mark all as successful
                    for item in items:
                        results[item.key] = True
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to set batch: {str(e)}")
            # Return partial results
            return results
    
    async def search(
        self,
        pattern: Optional[str] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[MemoryItem]:
        """Search for items using pattern matching and metadata filters."""
        try:
            async with self._pool.acquire() as conn:
                # Build query
                query = f"""
                    SELECT key, value, metadata, tier, created_at, accessed_at, 
                           access_count, size_bytes, ttl_seconds, checksum, compressed
                    FROM {self.table_name}
                    WHERE (expires_at IS NULL OR expires_at > NOW())
                """
                params = []
                param_count = 0
                
                # Add pattern filter
                if pattern:
                    param_count += 1
                    query += f" AND key LIKE ${param_count}"
                    params.append(pattern.replace('*', '%'))
                
                # Add metadata filters
                if metadata_filter:
                    for key, value in metadata_filter.items():
                        param_count += 1
                        query += f" AND metadata->>${param_count - 1} = ${param_count}"
                        params.extend([key, json.dumps(value)])
                
                # Add order and limit
                query += f" ORDER BY accessed_at DESC LIMIT ${param_count + 1}"
                params.append(limit)
                
                # Execute query
                rows = await conn.fetch(query, *params)
                
                # Build results
                results = []
                for row in rows:
                    value = self._deserialize_value(row['value'], row['compressed'])
                    results.append(MemoryItem(
                        key=row['key'],
                        value=value,
                        metadata=dict(row['metadata']),
                        tier=MemoryTier(row['tier']),
                        created_at=row['created_at'],
                        accessed_at=row['accessed_at'],
                        access_count=row['access_count'],
                        size_bytes=row['size_bytes'],
                        ttl_seconds=row['ttl_seconds'],
                        checksum=row['checksum']
                    ))
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to search: {str(e)}")
            raise MemoryStorageError(
                operation="search",
                storage_backend="postgresql",
                reason=str(e),
                cause=e
            )
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        try:
            async with self._pool.acquire() as conn:
                # Get basic stats
                stats = await conn.fetchrow(f"""
                    SELECT 
                        COUNT(*) as total_items,
                        SUM(size_bytes) as total_size,
                        AVG(access_count) as avg_access_count,
                        MAX(accessed_at) as last_access
                    FROM {self.table_name}
                    WHERE tier = $1
                """, self.tier.value)
                
                # Get tier distribution
                tier_dist = await conn.fetch(f"""
                    SELECT tier, COUNT(*) as count
                    FROM {self.table_name}
                    GROUP BY tier
                """)
                
                return {
                    "tier": self.tier.value,
                    "total_items": stats['total_items'] or 0,
                    "total_size_bytes": stats['total_size'] or 0,
                    "avg_access_count": float(stats['avg_access_count'] or 0),
                    "last_access": stats['last_access'],
                    "tier_distribution": {
                        row['tier']: row['count'] for row in tier_dist
                    },
                    "pool_size": self._pool.get_size() if self._pool else 0,
                    "pool_free": self._pool.get_idle_size() if self._pool else 0,
                }
                
        except Exception as e:
            logger.error(f"Failed to get stats: {str(e)}")
            return {}
    
    async def cleanup_expired(self) -> int:
        """Remove expired items."""
        try:
            async with self._pool.acquire() as conn:
                result = await conn.execute(f"""
                    DELETE FROM {self.table_name}
                    WHERE expires_at IS NOT NULL AND expires_at <= NOW()
                """)
                
                # Extract count from result
                count = int(result.split()[-1])
                
                if count > 0:
                    # Run vacuum to reclaim space
                    await conn.execute(f"VACUUM ANALYZE {self.table_name}")
                    logger.info(f"Cleaned up {count} expired items from {self.tier.value}")
                
                return count
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired items: {str(e)}")
            return 0
    
    async def close(self) -> None:
        """Close PostgreSQL connections."""
        if self._pool:
            await self._pool.close()
            logger.info(f"PostgreSQL storage closed for tier {self.tier.value}")
    
    # Private helper methods
    
    def _serialize_value(self, value: Any) -> Tuple[bytes, bool]:
        """Serialize and optionally compress value."""
        try:
            # Serialize with pickle
            serialized = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
            compressed = False
            
            # Compress if enabled and above threshold
            if self.compression_enabled and len(serialized) > self.compression_threshold:
                serialized = lz4.frame.compress(serialized)
                compressed = True
            
            return serialized, compressed
            
        except Exception as e:
            raise MemorySerializationError(
                operation="serialize",
                key="",
                value_type=type(value).__name__,
                reason=str(e),
                cause=e
            )
    
    def _deserialize_value(self, data: bytes, compressed: bool) -> Any:
        """Deserialize and optionally decompress value."""
        try:
            # Decompress if needed
            if compressed:
                data = lz4.frame.decompress(data)
            
            # Deserialize with pickle
            return pickle.loads(data)
            
        except Exception as e:
            raise MemorySerializationError(
                operation="deserialize",
                key="",
                value_type="unknown",
                reason=str(e),
                cause=e
            )