"""
PostgreSQL storage adapter implementation.

This module provides a PostgreSQL adapter for storing metadata and
structured data in the data ingestion system.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

import asyncpg
from asyncpg.pool import Pool

from ..interfaces.storage import StorageInterface, StorageResult, StorageType

logger = logging.getLogger(__name__)

class PostgresAdapter(StorageInterface):
    """
    PostgreSQL storage adapter for metadata and structured data.
    
    This adapter handles all PostgreSQL operations including connection
    pooling, query optimization, and transaction management.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize PostgreSQL adapter.
        
        Args:
            config: Configuration with connection details
                - host: PostgreSQL host
                - port: PostgreSQL port
                - database: Database name
                - user: Username
                - password: Password
                - pool_size: Connection pool size (default: 10)
                - pool_max_size: Max pool size (default: 20)
        """
        super().__init__(config)
        self.storage_type = StorageType.POSTGRES
        self._pool: Optional[Pool] = None
        self._schema = config.get("schema", "data_ingestion")
        
    async def connect(self) -> bool:
        """Establish connection pool to PostgreSQL."""
        try:
            # Create connection pool
            self._pool = await asyncpg.create_pool(
                host=self.config["host"],
                port=self.config.get("port", 5432),
                database=self.config["database"],
                user=self.config["user"],
                password=self.config["password"],
                min_size=self.config.get("pool_size", 10),
                max_size=self.config.get("pool_max_size", 20),
                command_timeout=60,
                server_settings={
                    'search_path': f'{self._schema},public'
                }
            )
            
            # Test connection
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            
            self._connected = True
            logger.info("PostgreSQL connection established")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            self._connected = False
            return False
    
    async def disconnect(self) -> bool:
        """Close connection pool."""
        try:
            if self._pool:
                await self._pool.close()
                self._pool = None
            
            self._connected = False
            logger.info("PostgreSQL connection closed")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting from PostgreSQL: {e}")
            return False
    
    async def store(
        self, 
        data: Any, 
        key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StorageResult:
        """
        Store data in PostgreSQL.
        
        This method stores data in the appropriate table based on the
        data type and metadata provided.
        """
        if not self._connected or not self._pool:
            return StorageResult(
                success=False,
                error="Not connected to PostgreSQL"
            )
        
        try:
            # Generate key if not provided
            if not key:
                key = str(uuid.uuid4())
            
            # Determine table and operation based on metadata
            table = metadata.get("table", "parsed_content")
            operation = metadata.get("operation", "insert")
            
            async with self._pool.acquire() as conn:
                async with conn.transaction():
                    if operation == "insert":
                        result = await self._insert_data(
                            conn, table, key, data, metadata
                        )
                    elif operation == "update":
                        result = await self._update_data(
                            conn, table, key, data, metadata
                        )
                    else:
                        return StorageResult(
                            success=False,
                            error=f"Unsupported operation: {operation}"
                        )
            
            return result
            
        except Exception as e:
            logger.error(f"Error storing data in PostgreSQL: {e}")
            return StorageResult(
                success=False,
                error=str(e)
            )
    
    async def retrieve(
        self, 
        key: str,
        include_metadata: bool = False
    ) -> Optional[Any]:
        """Retrieve data from PostgreSQL by key."""
        if not self._connected or not self._pool:
            return None
        
        try:
            async with self._pool.acquire() as conn:
                # Try to find in parsed_content first
                query = f"""
                    SELECT id, content, metadata, created_at
                    FROM {self._schema}.parsed_content
                    WHERE id = $1
                """
                
                row = await conn.fetchrow(query, uuid.UUID(key))
                
                if row:
                    if include_metadata:
                        return {
                            "id": str(row["id"]),
                            "content": row["content"],
                            "metadata": row["metadata"],
                            "created_at": row["created_at"]
                        }
                    else:
                        return row["content"]
                
                # Try file_imports table
                query = f"""
                    SELECT id, filename, source_type, metadata, created_at
                    FROM {self._schema}.file_imports
                    WHERE id = $1
                """
                
                row = await conn.fetchrow(query, uuid.UUID(key))
                
                if row:
                    if include_metadata:
                        return dict(row)
                    else:
                        return {
                            "filename": row["filename"],
                            "source_type": row["source_type"]
                        }
                
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving data from PostgreSQL: {e}")
            return None
    
    async def delete(self, key: str) -> StorageResult:
        """Delete data from PostgreSQL."""
        if not self._connected or not self._pool:
            return StorageResult(
                success=False,
                error="Not connected to PostgreSQL"
            )
        
        try:
            async with self._pool.acquire() as conn:
                async with conn.transaction():
                    # Delete from parsed_content (cascade will handle related)
                    query = f"""
                        DELETE FROM {self._schema}.parsed_content
                        WHERE id = $1
                    """
                    
                    result = await conn.execute(query, uuid.UUID(key))
                    
                    if result == "DELETE 0":
                        # Try file_imports
                        query = f"""
                            DELETE FROM {self._schema}.file_imports
                            WHERE id = $1
                        """
                        result = await conn.execute(query, uuid.UUID(key))
                    
                    deleted = result != "DELETE 0"
            
            return StorageResult(
                success=deleted,
                key=key,
                error=None if deleted else "Key not found"
            )
            
        except Exception as e:
            logger.error(f"Error deleting from PostgreSQL: {e}")
            return StorageResult(
                success=False,
                key=key,
                error=str(e)
            )
    
    async def list(
        self, 
        prefix: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[str]:
        """List keys from PostgreSQL tables."""
        if not self._connected or not self._pool:
            return []
        
        try:
            async with self._pool.acquire() as conn:
                # List from parsed_content
                query = f"""
                    SELECT id::text
                    FROM {self._schema}.parsed_content
                """
                
                params = []
                if prefix:
                    query += " WHERE content_type = $1"
                    params.append(prefix)
                
                query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
                params.extend([limit, offset])
                
                rows = await conn.fetch(query, *params)
                
                return [row["id"] for row in rows]
                
        except Exception as e:
            logger.error(f"Error listing keys from PostgreSQL: {e}")
            return []
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in PostgreSQL."""
        if not self._connected or not self._pool:
            return False
        
        try:
            async with self._pool.acquire() as conn:
                query = f"""
                    SELECT EXISTS(
                        SELECT 1 FROM {self._schema}.parsed_content WHERE id = $1
                        UNION
                        SELECT 1 FROM {self._schema}.file_imports WHERE id = $1
                    )
                """
                
                return await conn.fetchval(query, uuid.UUID(key))
                
        except Exception:
            return False
    
    # PostgreSQL-specific methods
    
    async def _insert_data(
        self,
        conn: asyncpg.Connection,
        table: str,
        key: str,
        data: Any,
        metadata: Dict[str, Any]
    ) -> StorageResult:
        """Insert data into specified table."""
        try:
            if table == "parsed_content":
                query = f"""
                    INSERT INTO {self._schema}.parsed_content
                    (id, file_import_id, content_type, source_id, content, metadata, vector_id, tokens_count)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (file_import_id, content_hash) DO NOTHING
                    RETURNING id
                """
                
                result = await conn.fetchval(
                    query,
                    uuid.UUID(key),
                    uuid.UUID(metadata["file_import_id"]) if metadata.get("file_import_id") else None,
                    metadata.get("content_type", "unknown"),
                    metadata.get("source_id"),
                    str(data),
                    json.dumps(metadata.get("metadata", {})),
                    metadata.get("vector_id"),
                    metadata.get("tokens_count")
                )
                
                return StorageResult(
                    success=result is not None,
                    key=str(result) if result else key,
                    metadata={"inserted": result is not None}
                )
                
            elif table == "file_imports":
                query = f"""
                    INSERT INTO {self._schema}.file_imports
                    (id, filename, source_type, file_size, mime_type, s3_key, metadata, created_by)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING id
                """
                
                result = await conn.fetchval(
                    query,
                    uuid.UUID(key),
                    data.get("filename"),
                    data.get("source_type"),
                    data.get("file_size"),
                    data.get("mime_type"),
                    data.get("s3_key"),
                    json.dumps(metadata or {}),
                    uuid.UUID(data.get("created_by")) if data.get("created_by") else None
                )
                
                return StorageResult(
                    success=True,
                    key=str(result)
                )
            
            else:
                return StorageResult(
                    success=False,
                    error=f"Unsupported table: {table}"
                )
                
        except Exception as e:
            return StorageResult(
                success=False,
                error=str(e)
            )
    
    async def _update_data(
        self,
        conn: asyncpg.Connection,
        table: str,
        key: str,
        data: Any,
        metadata: Dict[str, Any]
    ) -> StorageResult:
        """Update data in specified table."""
        try:
            if table == "file_imports":
                updates = []
                params = [uuid.UUID(key)]
                param_count = 1
                
                if "processing_status" in data:
                    param_count += 1
                    updates.append(f"processing_status = ${param_count}")
                    params.append(data["processing_status"])
                
                if "error_message" in data:
                    param_count += 1
                    updates.append(f"error_message = ${param_count}")
                    params.append(data["error_message"])
                
                if "processing_started_at" in data:
                    param_count += 1
                    updates.append(f"processing_started_at = ${param_count}")
                    params.append(data["processing_started_at"])
                
                if "processing_completed_at" in data:
                    param_count += 1
                    updates.append(f"processing_completed_at = ${param_count}")
                    params.append(data["processing_completed_at"])
                
                if "metadata" in data:
                    param_count += 1
                    updates.append(f"metadata = ${param_count}")
                    params.append(json.dumps(data["metadata"]))
                
                if not updates:
                    return StorageResult(
                        success=False,
                        error="No fields to update"
                    )
                
                query = f"""
                    UPDATE {self._schema}.file_imports
                    SET {', '.join(updates)}, updated_at = NOW()
                    WHERE id = $1
                """
                
                result = await conn.execute(query, *params)
                
                return StorageResult(
                    success=result != "UPDATE 0",
                    key=key
                )
            
            else:
                return StorageResult(
                    success=False,
                    error=f"Update not supported for table: {table}"
                )
                
        except Exception as e:
            return StorageResult(
                success=False,
                error=str(e)
            )
    
    async def execute_query(
        self,
        query: str,
        params: Optional[List[Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a custom query and return results."""
        if not self._connected or not self._pool:
            return []
        
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, *(params or []))
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return []