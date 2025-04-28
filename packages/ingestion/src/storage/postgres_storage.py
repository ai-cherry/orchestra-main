"""
PostgreSQL Vector Storage for File Ingestion System.

This module provides PostgreSQL integration for storing and retrieving
vector embeddings using the pgvector extension.
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple

import asyncpg
import numpy as np

from packages.ingestion.src.models.ingestion_models import TextChunk
from packages.ingestion.src.config.settings import get_settings

# Configure logging
logger = logging.getLogger(__name__)


class PostgresStorageError(Exception):
    """Exception for PostgreSQL storage-related errors."""
    pass


class PostgresStorage:
    """
    PostgreSQL storage implementation for vector embeddings.
    
    This class provides methods for storing and retrieving
    vector embeddings in PostgreSQL with pgvector extension.
    """
    
    def __init__(self, dsn: Optional[str] = None):
        """
        Initialize the PostgreSQL storage.
        
        Args:
            dsn: Optional DSN connection string. If not provided,
                will be read from settings or environment.
        """
        settings = get_settings()
        postgres_settings = settings.postgres
        
        # Use provided DSN or construct from settings
        self.dsn = dsn or postgres_settings.dsn
        if not self.dsn and postgres_settings.host:
            user_pass = f"{postgres_settings.user}:{postgres_settings.password}@" if postgres_settings.user else ""
            port = f":{postgres_settings.port}" if postgres_settings.port else ""
            self.dsn = f"postgres://{user_pass}{postgres_settings.host}{port}/{postgres_settings.database}"
            
        self.table_name = postgres_settings.embedding_table
        self.embedding_dimension = postgres_settings.embedding_dimension
        self._pool = None
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize the PostgreSQL connection pool and ensure the required table exists."""
        if self._initialized:
            return
            
        try:
            if not self.dsn:
                raise PostgresStorageError("No DSN or connection details provided for PostgreSQL")
                
            # Create connection pool
            self._pool = await asyncpg.create_pool(self.dsn)
            
            # Check if pgvector extension is installed
            async with self._pool.acquire() as conn:
                has_vector = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")
                if not has_vector:
                    logger.warning("pgvector extension not installed in PostgreSQL")
                    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                
                # Create embeddings table if it doesn't exist
                await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id SERIAL PRIMARY KEY,
                    file_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    chunk_number INTEGER NOT NULL,
                    text_content TEXT NOT NULL,
                    embedding vector({self.embedding_dimension}) NOT NULL,
                    metadata JSONB NOT NULL DEFAULT '{{}}',
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    
                    CONSTRAINT unique_file_chunk UNIQUE (file_id, chunk_number)
                )
                """)
                
                # Create indexes if they don't exist
                # Check if indexes exist
                metadata_index = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM pg_indexes WHERE indexname = 'idx_embeddings_metadata')"
                )
                if not metadata_index:
                    await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_embeddings_metadata 
                    ON {self.table_name} USING GIN (metadata)
                    """)
                
                user_index = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM pg_indexes WHERE indexname = 'idx_embeddings_user')"
                )
                if not user_index:
                    await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_embeddings_user 
                    ON {self.table_name} (user_id)
                    """)
                
                # Create vector index if it doesn't exist
                # This is a more complex check since the index type is specialized
                vector_index = await conn.fetchval(f"""
                SELECT EXISTS(
                    SELECT 1 FROM pg_indexes 
                    WHERE indexname = 'idx_embeddings_embedding'
                    AND tablename = '{self.table_name.lower()}'
                )
                """)
                if not vector_index:
                    # Create vector index with 100 lists (can be tuned based on data size)
                    await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_embeddings_embedding 
                    ON {self.table_name} USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100)
                    """)
            
            self._initialized = True
            logger.info("PostgreSQL storage initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL storage: {e}")
            raise PostgresStorageError(f"Failed to initialize PostgreSQL storage: {e}")
    
    async def close(self) -> None:
        """Close the PostgreSQL connection pool."""
        if self._pool:
            await self._pool.close()
            
        self._pool = None
        self._initialized = False
        logger.debug("PostgreSQL connection pool closed")
    
    def _check_initialized(self) -> None:
        """Check if the client is initialized and raise error if not."""
        if not self._initialized or not self._pool:
            raise PostgresStorageError("PostgreSQL storage not initialized")
    
    async def store_embedding(self, chunk: TextChunk) -> int:
        """
        Store a text chunk with embedding in PostgreSQL.
        
        Args:
            chunk: The text chunk with embedding to store
            
        Returns:
            The ID of the stored embedding
            
        Raises:
            PostgresStorageError: If storage fails
        """
        self._check_initialized()
        
        if not chunk.embedding:
            raise PostgresStorageError("No embedding provided in the chunk")
            
        try:
            metadata = chunk.metadata or {}
            
            # Insert embedding
            async with self._pool.acquire() as conn:
                embedding_id = await conn.fetchval(f"""
                INSERT INTO {self.table_name} 
                (file_id, task_id, user_id, chunk_number, text_content, embedding, metadata, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (file_id, chunk_number)
                DO UPDATE SET 
                    text_content = EXCLUDED.text_content,
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata
                RETURNING id
                """,
                chunk.file_id, chunk.task_id, chunk.user_id, chunk.chunk_number,
                chunk.text_content, chunk.embedding, metadata, chunk.created_at)
                
            logger.debug(f"Stored embedding for chunk {chunk.file_id}/{chunk.chunk_number} with ID {embedding_id}")
            return embedding_id
        except Exception as e:
            logger.error(f"Failed to store embedding in PostgreSQL: {e}")
            raise PostgresStorageError(f"Failed to store embedding: {e}")
    
    async def store_embeddings(self, chunks: List[TextChunk]) -> List[int]:
        """
        Store multiple text chunks with embeddings in PostgreSQL.
        
        Args:
            chunks: List of text chunks with embeddings to store
            
        Returns:
            List of stored embedding IDs
            
        Raises:
            PostgresStorageError: If storage fails
        """
        self._check_initialized()
        
        # Validate all chunks have embeddings
        for i, chunk in enumerate(chunks):
            if not chunk.embedding:
                raise PostgresStorageError(f"No embedding provided in chunk {i}")
                
        try:
            embedding_ids = []
            
            # Use a transaction for batch insertion
            async with self._pool.acquire() as conn:
                async with conn.transaction():
                    for chunk in chunks:
                        metadata = chunk.metadata or {}
                        
                        embedding_id = await conn.fetchval(f"""
                        INSERT INTO {self.table_name} 
                        (file_id, task_id, user_id, chunk_number, text_content, embedding, metadata, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        ON CONFLICT (file_id, chunk_number)
                        DO UPDATE SET 
                            text_content = EXCLUDED.text_content,
                            embedding = EXCLUDED.embedding,
                            metadata = EXCLUDED.metadata
                        RETURNING id
                        """,
                        chunk.file_id, chunk.task_id, chunk.user_id, chunk.chunk_number,
                        chunk.text_content, chunk.embedding, metadata, chunk.created_at)
                        
                        embedding_ids.append(embedding_id)
                        
            logger.debug(f"Stored {len(chunks)} embeddings in PostgreSQL")
            return embedding_ids
        except Exception as e:
            logger.error(f"Failed to store embeddings in PostgreSQL: {e}")
            raise PostgresStorageError(f"Failed to store embeddings: {e}")
    
    async def search_similar(
        self,
        query_embedding: List[float],
        user_id: str,
        limit: int = 10,
        task_id: Optional[str] = None,
        file_id: Optional[str] = None,
        metadata_filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings in PostgreSQL.
        
        Args:
            query_embedding: The query embedding to search for
            user_id: The user ID to filter by
            limit: Maximum number of results to return
            task_id: Optional task ID to filter by
            file_id: Optional file ID to filter by
            metadata_filters: Optional metadata filters to apply
            
        Returns:
            List of matching chunks with similarity scores
            
        Raises:
            PostgresStorageError: If search fails
        """
        self._check_initialized()
        
        try:
            # Start building the query
            query = f"""
            SELECT id, file_id, task_id, user_id, chunk_number, text_content, 
                   metadata, 1 - (embedding <=> $1) AS similarity
            FROM {self.table_name}
            WHERE user_id = $2
            """
            
            params = [query_embedding, user_id]
            param_index = 3
            
            # Add task_id filter if provided
            if task_id:
                query += f" AND task_id = ${param_index}"
                params.append(task_id)
                param_index += 1
                
            # Add file_id filter if provided
            if file_id:
                query += f" AND file_id = ${param_index}"
                params.append(file_id)
                param_index += 1
                
            # Add metadata filters if provided
            if metadata_filters:
                for key, value in metadata_filters.items():
                    query += f" AND metadata->>'${key}' = ${param_index}"
                    params.append(value)
                    param_index += 1
                    
            # Order by similarity and apply limit
            query += " ORDER BY similarity DESC LIMIT $" + str(param_index)
            params.append(limit)
            
            # Execute the query
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                
            # Process results
            results = []
            for row in rows:
                # Convert to dict and add similarity score
                result = dict(row)
                results.append(result)
                
            logger.debug(f"Found {len(results)} similar chunks for query")
            return results
        except Exception as e:
            logger.error(f"Failed to search for similar embeddings: {e}")
            raise PostgresStorageError(f"Failed to search similar embeddings: {e}")
    
    async def get_chunks_for_file(self, file_id: str) -> List[Dict[str, Any]]:
        """
        Get all chunks for a specific file.
        
        Args:
            file_id: The ID of the file
            
        Returns:
            List of chunks
            
        Raises:
            PostgresStorageError: If retrieval fails
        """
        self._check_initialized()
        
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(f"""
                SELECT id, file_id, task_id, user_id, chunk_number, text_content, metadata
                FROM {self.table_name}
                WHERE file_id = $1
                ORDER BY chunk_number
                """, file_id)
                
            # Convert rows to dictionaries
            chunks = [dict(row) for row in rows]
            
            logger.debug(f"Got {len(chunks)} chunks for file {file_id}")
            return chunks
        except Exception as e:
            logger.error(f"Failed to get chunks for file {file_id}: {e}")
            raise PostgresStorageError(f"Failed to get chunks for file: {e}")
    
    async def delete_chunks_for_task(self, task_id: str) -> int:
        """
        Delete all chunks for a specific task.
        
        Args:
            task_id: The ID of the task
            
        Returns:
            Number of chunks deleted
            
        Raises:
            PostgresStorageError: If deletion fails
        """
        self._check_initialized()
        
        try:
            async with self._pool.acquire() as conn:
                count = await conn.fetchval(f"""
                DELETE FROM {self.table_name}
                WHERE task_id = $1
                RETURNING COUNT(*)
                """, task_id)
                
            logger.info(f"Deleted {count} chunks for task {task_id}")
            return count
        except Exception as e:
            logger.error(f"Failed to delete chunks for task {task_id}: {e}")
            raise PostgresStorageError(f"Failed to delete chunks for task: {e}")
