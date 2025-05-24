"""
PGVector service for vector search in AI Orchestra.

This module provides a service for storing and retrieving vectors in pgvector.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import asyncpg
from ai_orchestra.core.config import settings

logger = logging.getLogger("ai_orchestra.infrastructure.vector.pgvector_service")


@dataclass
class DocumentChunk:
    """Document chunk with metadata and embedding."""

    chunk_id: str
    document_id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


class PGVectorService:
    """
    Service for vector operations using pgvector.

    This service provides methods for storing, retrieving, and searching
    vectors in a PostgreSQL database with the pgvector extension.
    """

    def __init__(self, connection_pool: Optional[asyncpg.Pool] = None):
        """
        Initialize the PGVector service.

        Args:
            connection_pool: Optional existing connection pool
        """
        self.pool = connection_pool
        self.initialized = False

    async def initialize(self):
        """Initialize the vector service if not already initialized."""
        if self.initialized:
            return

        # Create connection pool if not provided
        if not self.pool:
            dsn = settings.vector.pg_dsn
            self.pool = await asyncpg.create_pool(
                dsn,
                min_size=settings.vector.min_connections,
                max_size=settings.vector.max_connections,
            )

        # Ensure pgvector extension is loaded
        await self._setup_database()
        self.initialized = True

    async def _setup_database(self):
        """Set up the database with required tables and extensions."""
        async with self.pool.acquire() as conn:
            # Create extension if it doesn't exist
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

            # Create documents table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    source TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB
                )
            """
            )

            # Create chunks table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT REFERENCES documents(id) ON DELETE CASCADE,
                    content TEXT NOT NULL,
                    embedding vector(768),
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    seq_num INTEGER
                )
            """
            )

            # Create index on document_id
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id
                ON document_chunks(document_id)
            """
            )

            # Create vector index for similarity search
            try:
                await conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
                    ON document_chunks
                    USING hnsw (embedding vector_cosine_ops)
                    WITH (ef_construction = 128, m = 16)
                """
                )
            except Exception as e:
                logger.warning(f"Could not create HNSW index, falling back to IVFFlat: {e}")
                # Fall back to IVFFlat index which is more widely supported
                await conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
                    ON document_chunks
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100)
                """
                )

    async def store_document(
        self,
        document_id: str,
        title: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Store document metadata.

        Args:
            document_id: The document ID
            title: The document title
            source: The document source
            metadata: Optional metadata

        Returns:
            True if successful
        """
        await self.initialize()
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    """
                    INSERT INTO documents (id, title, source, metadata)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (id) DO UPDATE
                    SET title = $2, source = $3, metadata = $4
                    """,
                    document_id,
                    title,
                    source,
                    metadata or {},
                )
                return True
            except Exception as e:
                logger.error(f"Error storing document: {e}")
                return False

    async def store_chunks(self, chunks: List[DocumentChunk]) -> bool:
        """
        Store document chunks with embeddings.

        Args:
            chunks: List of document chunks to store

        Returns:
            True if successful
        """
        if not chunks:
            return True

        await self.initialize()
        async with self.pool.acquire() as conn:
            try:
                # Use a transaction for atomic operation
                async with conn.transaction():
                    for i, chunk in enumerate(chunks):
                        await conn.execute(
                            """
                            INSERT INTO document_chunks
                            (id, document_id, content, embedding, metadata, seq_num)
                            VALUES ($1, $2, $3, $4, $5, $6)
                            ON CONFLICT (id) DO UPDATE
                            SET content = $3, embedding = $4, metadata = $5, seq_num = $6
                            """,
                            chunk.chunk_id,
                            chunk.document_id,
                            chunk.content,
                            chunk.embedding,
                            chunk.metadata or {},
                            i,
                        )
                return True
            except Exception as e:
                logger.error(f"Error storing chunks: {e}")
                return False

    async def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 5,
        score_threshold: float = 0.7,
        document_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks based on embedding.

        Args:
            query_embedding: The query embedding vector
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score (0-1)
            document_id: Optional document ID to filter results

        Returns:
            List of chunks with similarity scores
        """
        await self.initialize()
        async with self.pool.acquire() as conn:
            try:
                query = """
                    SELECT
                        c.id,
                        c.document_id,
                        c.content,
                        c.metadata,
                        d.title as document_title,
                        d.source as document_source,
                        1 - (c.embedding <=> $1) as similarity
                    FROM
                        document_chunks c
                    JOIN
                        documents d ON c.document_id = d.id
                    WHERE
                        1 - (c.embedding <=> $1) > $2
                """

                params = [query_embedding, score_threshold]

                # Add document filter if specified
                if document_id:
                    query += " AND c.document_id = $3"
                    params.append(document_id)

                # Add limit and order
                query += " ORDER BY similarity DESC LIMIT $%d" % (len(params) + 1)
                params.append(limit)

                rows = await conn.fetch(query, *params)

                return [
                    {
                        "id": row["id"],
                        "document_id": row["document_id"],
                        "content": row["content"],
                        "metadata": row["metadata"],
                        "document_title": row["document_title"],
                        "document_source": row["document_source"],
                        "similarity": row["similarity"],
                    }
                    for row in rows
                ]
            except Exception as e:
                logger.error(f"Error searching similar chunks: {e}")
                return []

    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and all its chunks.

        Args:
            document_id: The document ID

        Returns:
            True if successful
        """
        await self.initialize()
        async with self.pool.acquire() as conn:
            try:
                # Use a transaction for atomic operation
                async with conn.transaction():
                    # Delete document (cascade will delete chunks)
                    await conn.execute("DELETE FROM documents WHERE id = $1", document_id)
                return True
            except Exception as e:
                logger.error(f"Error deleting document: {e}")
                return False

    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document metadata.

        Args:
            document_id: The document ID

        Returns:
            Document metadata or None if not found
        """
        await self.initialize()
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(
                    """
                    SELECT id, title, source, metadata, created_at
                    FROM documents
                    WHERE id = $1
                    """,
                    document_id,
                )

                if not row:
                    return None

                return {
                    "id": row["id"],
                    "title": row["title"],
                    "source": row["source"],
                    "metadata": row["metadata"],
                    "created_at": row["created_at"].isoformat(),
                }
            except Exception as e:
                logger.error(f"Error getting document: {e}")
                return None

    async def list_documents(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List all documents.

        Args:
            limit: Maximum number of documents to return
            offset: Pagination offset

        Returns:
            List of document metadata
        """
        await self.initialize()
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(
                    """
                    SELECT id, title, source, metadata, created_at
                    FROM documents
                    ORDER BY created_at DESC
                    LIMIT $1 OFFSET $2
                    """,
                    limit,
                    offset,
                )

                return [
                    {
                        "id": row["id"],
                        "title": row["title"],
                        "source": row["source"],
                        "metadata": row["metadata"],
                        "created_at": row["created_at"].isoformat(),
                    }
                    for row in rows
                ]
            except Exception as e:
                logger.error(f"Error listing documents: {e}")
                return []

    async def count_documents(self) -> int:
        """
        Count the total number of documents.

        Returns:
            Total number of documents
        """
        await self.initialize()
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow("SELECT COUNT(*) FROM documents")
                return row[0]
            except Exception as e:
                logger.error(f"Error counting documents: {e}")
                return 0

    async def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Get all chunks for a document.

        Args:
            document_id: The ID of the document

        Returns:
            List of document chunks
        """
        await self.initialize()
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(
                    """
                    SELECT id, document_id, content, metadata, created_at, seq_num
                    FROM document_chunks
                    WHERE document_id = $1
                    ORDER BY seq_num ASC NULLS LAST, created_at ASC
                    """,
                    document_id,
                )

                return [
                    {
                        "id": row["id"],
                        "document_id": row["document_id"],
                        "content": row["content"],
                        "metadata": row["metadata"],
                        "created_at": row["created_at"].isoformat(),
                    }
                    for row in rows
                ]
            except Exception as e:
                logger.error(f"Error getting document chunks: {e}")
                return []

    async def get_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific chunk.

        Args:
            chunk_id: The chunk ID

        Returns:
            Chunk data or None if not found
        """
        await self.initialize()
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(
                    """
                    SELECT
                        c.id,
                        c.document_id,
                        c.content,
                        c.metadata,
                        c.seq_num,
                        d.title as document_title,
                        d.source as document_source
                    FROM
                        document_chunks c
                    JOIN
                        documents d ON c.document_id = d.id
                    WHERE
                        c.id = $1
                    """,
                    chunk_id,
                )

                if not row:
                    return None

                return {
                    "id": row["id"],
                    "document_id": row["document_id"],
                    "content": row["content"],
                    "metadata": row["metadata"],
                    "sequence_number": row["seq_num"],
                    "document_title": row["document_title"],
                    "document_source": row["document_source"],
                }
            except Exception as e:
                logger.error(f"Error getting chunk: {e}")
                return None

    async def close(self):
        """Close database connections."""
        if self.pool:
            await self.pool.close()

    async def __aenter__(self):
        """Context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()
