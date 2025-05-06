"""
PostgreSQL adapter for the Memory Storage Port.

This module implements the MemoryStoragePort interface using PostgreSQL,
following the hexagonal architecture pattern to isolate infrastructure concerns.
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import asyncpg
import numpy as np
from asyncpg.pool import Pool

from packages.shared.src.models.base_models import MemoryItem, AgentData
from packages.shared.src.memory.ports import MemoryStoragePort
from packages.shared.src.memory.exceptions import (
    MemoryConnectionError,
    MemoryItemNotFound,
    MemoryQueryError,
    MemoryWriteError,
    MemoryValidationError,
)
from packages.shared.src.memory.memory_types import MemoryHealth
from packages.shared.src.storage.config import StorageConfig

# Configure logging
logger = logging.getLogger(__name__)

# Table names
MEMORY_ITEMS_TABLE = "memory_items"
AGENT_DATA_TABLE = "agent_data"


class PostgresStorageAdapter(MemoryStoragePort):
    """
    PostgreSQL implementation of the MemoryStoragePort.

    This adapter handles all PostgreSQL-specific details while conforming
    to the port interface, providing a clean separation between domain logic
    and infrastructure concerns.
    """

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: Optional[str] = None,
        schema: str = "public",
        min_connections: int = 5,
        max_connections: int = 10,
        config: Optional[StorageConfig] = None,
    ):
        """
        Initialize the PostgreSQL adapter.

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
            schema: Database schema
            min_connections: Minimum number of connections in the pool
            max_connections: Maximum number of connections in the pool
            config: Storage configuration
        """
        self._host = host
        self._port = port
        self._database = database
        self._user = user
        self._password = password
        self._schema = schema
        self._min_connections = min_connections
        self._max_connections = max_connections
        self._config = config or StorageConfig(
            namespace=schema,
            environment="development",
        )

        # Will be initialized in initialize()
        self._pool: Optional[Pool] = None
        self._initialized = False
        self._error_count = 0
        self._last_error = None

        logger.debug(
            f"PostgresStorageAdapter initialized with host: {host}, database: {database}")

    async def initialize(self) -> None:
        """
        Initialize the PostgreSQL connection pool and ensure tables exist.

        Raises:
            MemoryConnectionError: If connection to PostgreSQL fails
        """
        if self._initialized:
            return

        try:
            # Create connection pool
            self._pool = await asyncpg.create_pool(
                host=self._host,
                port=self._port,
                database=self._database,
                user=self._user,
                password=self._password,
                min_size=self._min_connections,
                max_size=self._max_connections,
            )

            # Ensure the schema exists
            async with self._pool.acquire() as conn:
                await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {self._schema}")

            # Ensure tables exist
            await self._ensure_tables_exist()

            self._initialized = True
            logger.info(
                f"PostgresStorageAdapter successfully connected to {self._host}:{self._port}/{self._database}")

        except Exception as e:
            error_msg = f"Failed to connect to PostgreSQL: {e}"
            logger.error(error_msg)
            raise MemoryConnectionError(error_msg)

    async def _ensure_tables_exist(self) -> None:
        """
        Ensure the required tables exist in the database.

        Raises:
            MemoryConnectionError: If table creation fails
        """
        try:
            async with self._pool.acquire() as conn:
                # Create memory items table if it doesn't exist
                await conn.execute(f'''
                    CREATE TABLE IF NOT EXISTS {self._schema}.{MEMORY_ITEMS_TABLE} (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        session_id TEXT,
                        item_type TEXT NOT NULL,
                        text_content TEXT,
                        persona_active TEXT,
                        timestamp TIMESTAMPTZ DEFAULT NOW(),
                        metadata JSONB DEFAULT '{{}}'::jsonb,
                        embedding FLOAT[] DEFAULT NULL,
                        ttl TIMESTAMPTZ DEFAULT NULL
                    )
                ''')

                # Create indexes for efficient queries
                await conn.execute(f'''
                    CREATE INDEX IF NOT EXISTS idx_{MEMORY_ITEMS_TABLE}_user_id 
                    ON {self._schema}.{MEMORY_ITEMS_TABLE} (user_id)
                ''')

                await conn.execute(f'''
                    CREATE INDEX IF NOT EXISTS idx_{MEMORY_ITEMS_TABLE}_session_id 
                    ON {self._schema}.{MEMORY_ITEMS_TABLE} (session_id)
                ''')

                await conn.execute(f'''
                    CREATE INDEX IF NOT EXISTS idx_{MEMORY_ITEMS_TABLE}_timestamp 
                    ON {self._schema}.{MEMORY_ITEMS_TABLE} (timestamp DESC)
                ''')

                # Create agent data table if it doesn't exist
                await conn.execute(f'''
                    CREATE TABLE IF NOT EXISTS {self._schema}.{AGENT_DATA_TABLE} (
                        id TEXT PRIMARY KEY,
                        agent_id TEXT NOT NULL,
                        data_type TEXT NOT NULL,
                        content TEXT,
                        timestamp TIMESTAMPTZ DEFAULT NOW(),
                        metadata JSONB DEFAULT '{{}}'::jsonb
                    )
                ''')

                # Create index for agent queries
                await conn.execute(f'''
                    CREATE INDEX IF NOT EXISTS idx_{AGENT_DATA_TABLE}_agent_id 
                    ON {self._schema}.{AGENT_DATA_TABLE} (agent_id)
                ''')

                logger.debug(
                    "PostgreSQL tables and indexes created or verified")

        except Exception as e:
            error_msg = f"Failed to create tables in PostgreSQL: {e}"
            logger.error(error_msg)
            raise MemoryConnectionError(error_msg)

    async def close(self) -> None:
        """Close the PostgreSQL connection pool."""
        if self._pool:
            await self._pool.close()
            self._initialized = False
            logger.info("PostgresStorageAdapter connection pool closed")

    def _check_initialized(self) -> None:
        """
        Check if the adapter is initialized.

        Raises:
            MemoryConnectionError: If the adapter is not initialized
        """
        if not self._initialized or not self._pool:
            raise MemoryConnectionError(
                "PostgresStorageAdapter is not initialized")

    async def save_item(self, item: MemoryItem) -> str:
        """
        Save a memory item to PostgreSQL.

        Args:
            item: Memory item to save

        Returns:
            ID of the saved item

        Raises:
            MemoryWriteError: If the save operation fails
            MemoryValidationError: If the item validation fails
        """
        self._check_initialized()

        # Validate item
        if not item.id:
            raise MemoryValidationError("Memory item must have an ID")

        if not item.user_id:
            raise MemoryValidationError("Memory item must have a user ID")

        try:
            # Convert MemoryItem to dict and extract values for PostgreSQL
            # Note: This keeps infrastructure concerns in the adapter
            metadata = json.dumps(item.metadata or {})
            embedding = item.embedding

            # Calculate TTL if configured
            ttl = None
            if hasattr(self._config, "item_ttl_days") and self._config.item_ttl_days > 0:
                ttl = datetime.now() + timedelta(days=self._config.item_ttl_days)

            async with self._pool.acquire() as conn:
                await conn.execute(f'''
                    INSERT INTO {self._schema}.{MEMORY_ITEMS_TABLE}
                    (id, user_id, session_id, item_type, text_content, persona_active, timestamp, metadata, embedding, ttl)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (id)
                    DO UPDATE SET
                        user_id = $2,
                        session_id = $3,
                        item_type = $4,
                        text_content = $5,
                        persona_active = $6,
                        timestamp = $7,
                        metadata = $8,
                        embedding = $9,
                        ttl = $10
                ''',
                                   item.id,
                                   item.user_id,
                                   item.session_id,
                                   item.item_type,
                                   item.text_content,
                                   item.persona_active,
                                   item.timestamp or datetime.now(),
                                   metadata,
                                   embedding,
                                   ttl
                                   )

            logger.debug(f"Saved memory item {item.id} to PostgreSQL")
            return item.id

        except Exception as e:
            error_msg = f"Failed to save memory item to PostgreSQL: {e}"
            logger.error(error_msg)
            self._track_error(e)
            raise MemoryWriteError(error_msg)

    async def retrieve_item(self, item_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory item from PostgreSQL.

        Args:
            item_id: ID of the item to retrieve

        Returns:
            The memory item, or None if not found

        Raises:
            MemoryQueryError: If the retrieval operation fails
        """
        self._check_initialized()

        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(f'''
                    SELECT id, user_id, session_id, item_type, text_content, persona_active, 
                           timestamp, metadata, embedding
                    FROM {self._schema}.{MEMORY_ITEMS_TABLE}
                    WHERE id = $1
                ''', item_id)

                if not row:
                    return None

                # Convert PostgreSQL row to MemoryItem
                # Note: This keeps infrastructure concerns in the adapter
                metadata = json.loads(
                    row['metadata']) if row['metadata'] else {}

                # Convert embedding from database format to list if present
                embedding = list(
                    row['embedding']) if row['embedding'] else None

                return MemoryItem(
                    id=row['id'],
                    user_id=row['user_id'],
                    session_id=row['session_id'],
                    item_type=row['item_type'],
                    text_content=row['text_content'],
                    persona_active=row['persona_active'],
                    timestamp=row['timestamp'],
                    metadata=metadata,
                    embedding=embedding
                )

        except Exception as e:
            error_msg = f"Failed to retrieve memory item from PostgreSQL: {e}"
            logger.error(error_msg)
            self._track_error(e)
            raise MemoryQueryError(error_msg)

    async def query_items(
        self,
        user_id: str,
        filters: Dict[str, Any],
        limit: int,
    ) -> List[MemoryItem]:
        """
        Query memory items from PostgreSQL.

        Args:
            user_id: User ID to filter by
            filters: Additional filters to apply
            limit: Maximum number of items to return

        Returns:
            List of memory items matching the query

        Raises:
            MemoryQueryError: If the query operation fails
        """
        self._check_initialized()

        try:
            # Build the SQL query with parameters
            query = f'''
                SELECT id, user_id, session_id, item_type, text_content, persona_active, 
                       timestamp, metadata, embedding
                FROM {self._schema}.{MEMORY_ITEMS_TABLE}
                WHERE user_id = $1
            '''

            params = [user_id]
            param_index = 2

            # Add additional filters
            where_clauses = []

            for key, value in filters.items():
                if key == 'session_id' and value:
                    where_clauses.append(f"session_id = ${param_index}")
                    params.append(value)
                    param_index += 1
                elif key == 'item_type' and value:
                    where_clauses.append(f"item_type = ${param_index}")
                    params.append(value)
                    param_index += 1
                elif key == 'persona_active' and value:
                    where_clauses.append(f"persona_active = ${param_index}")
                    params.append(value)
                    param_index += 1
                elif key == 'timestamp' and isinstance(value, dict):
                    if 'start' in value:
                        where_clauses.append(f"timestamp >= ${param_index}")
                        params.append(value['start'])
                        param_index += 1
                    if 'end' in value:
                        where_clauses.append(f"timestamp <= ${param_index}")
                        params.append(value['end'])
                        param_index += 1
                # Add more filter types as needed

            # Add all WHERE clauses
            if where_clauses:
                query += " AND " + " AND ".join(where_clauses)

            # Add ordering and limit
            query += f" ORDER BY timestamp DESC LIMIT ${param_index}"
            params.append(limit)

            # Execute query
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, *params)

            # Convert rows to MemoryItems
            result = []
            for row in rows:
                try:
                    metadata = json.loads(
                        row['metadata']) if row['metadata'] else {}
                    embedding = list(
                        row['embedding']) if row['embedding'] else None

                    memory_item = MemoryItem(
                        id=row['id'],
                        user_id=row['user_id'],
                        session_id=row['session_id'],
                        item_type=row['item_type'],
                        text_content=row['text_content'],
                        persona_active=row['persona_active'],
                        timestamp=row['timestamp'],
                        metadata=metadata,
                        embedding=embedding
                    )
                    result.append(memory_item)
                except Exception as e:
                    logger.warning(
                        f"Error parsing row for id {row['id'] if 'id' in row else 'unknown'}: {e}")
                    continue

            logger.debug(
                f"Retrieved {len(result)} memory items for user {user_id}")
            return result

        except Exception as e:
            error_msg = f"Failed to query memory items from PostgreSQL: {e}"
            logger.error(error_msg)
            self._track_error(e)
            raise MemoryQueryError(error_msg)

    async def save_agent_data(self, data: AgentData) -> str:
        """
        Save agent data to PostgreSQL.

        Args:
            data: Agent data to save

        Returns:
            ID of the saved data

        Raises:
            MemoryWriteError: If the save operation fails
            MemoryValidationError: If the data validation fails
        """
        self._check_initialized()

        # Validate data
        if not data.id:
            raise MemoryValidationError("Agent data must have an ID")

        if not data.agent_id:
            raise MemoryValidationError("Agent data must have an agent ID")

        try:
            # Convert AgentData to parameters for PostgreSQL
            metadata = json.dumps(data.metadata or {})

            async with self._pool.acquire() as conn:
                await conn.execute(f'''
                    INSERT INTO {self._schema}.{AGENT_DATA_TABLE}
                    (id, agent_id, data_type, content, timestamp, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (id)
                    DO UPDATE SET
                        agent_id = $2,
                        data_type = $3,
                        content = $4,
                        timestamp = $5,
                        metadata = $6
                ''',
                                   data.id,
                                   data.agent_id,
                                   data.data_type,
                                   data.content,
                                   data.timestamp or datetime.now(),
                                   metadata
                                   )

            logger.debug(
                f"Saved agent data {data.id} for agent {data.agent_id} to PostgreSQL")
            return data.id

        except Exception as e:
            error_msg = f"Failed to save agent data to PostgreSQL: {e}"
            logger.error(error_msg)
            self._track_error(e)
            raise MemoryWriteError(error_msg)

    async def delete_items(self, filter_criteria: Dict[str, Any]) -> int:
        """
        Delete items matching the given criteria.

        Args:
            filter_criteria: Criteria for items to delete

        Returns:
            Number of items deleted

        Raises:
            MemoryWriteError: If the delete operation fails
        """
        self._check_initialized()

        try:
            # Build the SQL query with parameters
            query = f"DELETE FROM {self._schema}.{MEMORY_ITEMS_TABLE} WHERE "

            where_clauses = []
            params = []
            param_index = 1

            for key, value in filter_criteria.items():
                where_clauses.append(f"{key} = ${param_index}")
                params.append(value)
                param_index += 1

            if not where_clauses:
                raise MemoryValidationError(
                    "At least one filter criterion is required for deletion")

            query += " AND ".join(where_clauses)

            # Execute deletion and get count
            async with self._pool.acquire() as conn:
                result = await conn.execute(query, *params)

                # Parse the deletion count from the result
                count = int(result.split(" ")[1]) if result else 0

            logger.debug(f"Deleted {count} memory items from PostgreSQL")
            return count

        except Exception as e:
            error_msg = f"Failed to delete memory items from PostgreSQL: {e}"
            logger.error(error_msg)
            self._track_error(e)
            raise MemoryWriteError(error_msg)

    async def check_health(self) -> MemoryHealth:
        """
        Check the health of the PostgreSQL connection.

        Returns:
            Health status information
        """
        health = {
            "status": "healthy" if self._initialized else "not_initialized",
            "postgres": self._initialized,
            "error_count": self._error_count,
            "details": {
                "adapter": "PostgresStorageAdapter",
                "host": self._host,
                "database": self._database,
                "schema": self._schema,
            }
        }

        if self._last_error:
            health["last_error"] = str(self._last_error)

        # Try a simple query to verify connection
        if self._initialized and self._pool:
            try:
                async with self._pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                health["details"]["connection_verified"] = True
            except Exception as e:
                health["status"] = "error"
                health["details"]["connection_error"] = str(e)
                health["details"]["connection_verified"] = False

        return health

    def _track_error(self, error: Exception) -> None:
        """
        Track an error for health monitoring.

        Args:
            error: The error to track
        """
        self._error_count += 1
        self._last_error = error
