"""
Unified Database Interface for Orchestra AI
Provides a single interface for PostgreSQL (relational) and Weaviate (vector) operations.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union, AsyncGenerator, Tuple
from uuid import UUID, uuid4

import asyncpg
import weaviate
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class DatabaseType(str, Enum):
    """Database type for operations."""
    RELATIONAL = "relational"    # PostgreSQL
    VECTOR = "vector"           # Weaviate
    HYBRID = "hybrid"          # Both databases

class OperationType(str, Enum):
    """Operation types for metrics."""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    VECTOR_SEARCH = "vector_search"
    HYBRID_SEARCH = "hybrid_search"

@dataclass
class DatabaseMetrics:
    """Database performance metrics."""
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    total_latency: float = 0.0
    operation_counts: Dict[OperationType, int] = None
    connection_pool_stats: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.operation_counts is None:
            self.operation_counts = {op: 0 for op in OperationType}
        if self.connection_pool_stats is None:
            self.connection_pool_stats = {}

class DatabaseError(Exception):
    """Base database error."""
    pass

class ConnectionError(DatabaseError):
    """Database connection error."""
    pass

class QueryError(DatabaseError):
    """Query execution error."""
    pass

class VectorSearchResult(BaseModel):
    """Vector search result."""
    id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    score: float = 0.0
    vector: Optional[List[float]] = None

class HybridSearchResult(BaseModel):
    """Hybrid search result combining relational and vector data."""
    id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    vector_score: float = 0.0
    relational_data: Dict[str, Any] = Field(default_factory=dict)

class UnifiedDatabase:
    """
    Unified database interface providing PostgreSQL and Weaviate operations.
    """
    
    def __init__(
        self,
        postgres_url: str,
        weaviate_url: str = "http://localhost:8080",
        weaviate_api_key: Optional[str] = None,
        pool_size: int = 10,
        max_overflow: int = 20
    ):
        """Initialize unified database interface."""
        self.postgres_url = postgres_url
        self.weaviate_url = weaviate_url
        self.weaviate_api_key = weaviate_api_key
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        
        # Connection pools
        self._postgres_pool: Optional[asyncpg.Pool] = None
        self._weaviate_client: Optional[weaviate.Client] = None
        
        # Metrics
        self.metrics = DatabaseMetrics()
        
        # Health status
        self._postgres_healthy = False
        self._weaviate_healthy = False
        
        # Initialize flag
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize database connections."""
        if self._initialized:
            return
        
        try:
            # Initialize PostgreSQL pool
            self._postgres_pool = await asyncpg.create_pool(
                self.postgres_url,
                min_size=1,
                max_size=self.pool_size,
                command_timeout=30
            )
            self._postgres_healthy = True
            logger.info("PostgreSQL connection pool initialized")
            
            # Initialize Weaviate client (v3 syntax)
            if self.weaviate_api_key:
                auth_config = weaviate.AuthApiKey(api_key=self.weaviate_api_key)
                self._weaviate_client = weaviate.Client(
                    url=self.weaviate_url,
                    auth_client_secret=auth_config
                )
            else:
                self._weaviate_client = weaviate.Client(url=self.weaviate_url)
            
            # Test Weaviate connection
            if self._weaviate_client.is_ready():
                self._weaviate_healthy = True
                logger.info("Weaviate client initialized")
            else:
                logger.warning("Weaviate client not ready")
            
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise ConnectionError(f"Failed to initialize databases: {e}")
    
    async def close(self) -> None:
        """Close database connections."""
        if self._postgres_pool:
            await self._postgres_pool.close()
            self._postgres_pool = None
            self._postgres_healthy = False
        
        if self._weaviate_client:
            self._weaviate_client = None
            self._weaviate_healthy = False
        
        self._initialized = False
        logger.info("Database connections closed")
    
    @asynccontextmanager
    async def get_postgres_connection(self):
        """Get PostgreSQL connection from pool."""
        if not self._postgres_pool:
            raise ConnectionError("PostgreSQL pool not initialized")
        
        connection = None
        try:
            connection = await self._postgres_pool.acquire()
            yield connection
        finally:
            if connection:
                await self._postgres_pool.release(connection)
    
    def get_weaviate_client(self) -> weaviate.Client:
        """Get Weaviate client."""
        if not self._weaviate_client:
            raise ConnectionError("Weaviate client not initialized")
        return self._weaviate_client
    
    async def _execute_with_metrics(
        self,
        operation_type: OperationType,
        operation_func,
        *args,
        **kwargs
    ) -> Any:
        """Execute operation with metrics tracking."""
        start_time = time.time()
        try:
            result = await operation_func(*args, **kwargs)
            
            # Update success metrics
            self.metrics.successful_operations += 1
            self.metrics.operation_counts[operation_type] += 1
            
            return result
            
        except Exception as e:
            self.metrics.failed_operations += 1
            logger.error(f"Database operation failed: {e}")
            raise
            
        finally:
            # Update timing metrics
            latency = time.time() - start_time
            self.metrics.total_latency += latency
            self.metrics.total_operations += 1
    
    # PostgreSQL Operations
    async def execute_query(
        self,
        query: str,
        params: Optional[List] = None,
        fetch: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """Execute PostgreSQL query."""
        async def _execute():
            async with self.get_postgres_connection() as conn:
                if fetch:
                    if params:
                        result = await conn.fetch(query, *params)
                    else:
                        result = await conn.fetch(query)
                    return [dict(row) for row in result]
                else:
                    if params:
                        await conn.execute(query, *params)
                    else:
                        await conn.execute(query)
                    return None
        
        operation_type = OperationType.SELECT if fetch else OperationType.INSERT
        return await self._execute_with_metrics(operation_type, _execute)
    
    async def insert_record(
        self,
        table: str,
        data: Dict[str, Any],
        returning: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Insert record into PostgreSQL table."""
        async def _insert():
            columns = list(data.keys())
            placeholders = [f"${i+1}" for i in range(len(columns))]
            values = list(data.values())
            
            query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            if returning:
                query += f" RETURNING {returning}"
            
            async with self.get_postgres_connection() as conn:
                if returning:
                    result = await conn.fetchrow(query, *values)
                    return dict(result) if result else None
                else:
                    await conn.execute(query, *values)
                    return None
        
        return await self._execute_with_metrics(OperationType.INSERT, _insert)
    
    # Simplified Weaviate operations for v3
    async def vector_search(
        self,
        class_name: str,
        query_text: Optional[str] = None,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """Perform vector search in Weaviate (v3 syntax)."""
        async def _search():
            client = self.get_weaviate_client()
            
            # Build query using v3 syntax
            query_builder = client.query.get(class_name, ["content"])
            
            if query_text:
                query_builder = query_builder.with_near_text({"concepts": [query_text]})
            
            if filters:
                query_builder = query_builder.with_where(filters)
            
            query_builder = query_builder.with_limit(limit)
            
            # Execute search
            response = query_builder.do()
            
            # Convert to results
            results = []
            if 'data' in response and 'Get' in response['data'] and class_name in response['data']['Get']:
                for obj in response['data']['Get'][class_name]:
                    result = VectorSearchResult(
                        id=obj.get('_id', str(uuid4())),
                        content=obj.get('content', ''),
                        metadata=obj,
                        score=obj.get('_additional', {}).get('distance', 0.0)
                    )
                    results.append(result)
            
            return results
        
        return await self._execute_with_metrics(OperationType.VECTOR_SEARCH, _search)
    
    async def insert_vector(
        self,
        class_name: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        object_id: Optional[str] = None
    ) -> str:
        """Insert vector into Weaviate class (v3 syntax)."""
        async def _insert():
            client = self.get_weaviate_client()
            
            # Prepare properties
            properties = {"content": content}
            if metadata:
                properties.update(metadata)
            
            # Insert object using v3 syntax
            result = client.data_object.create(
                data_object=properties,
                class_name=class_name,
                uuid=object_id
            )
            
            return str(result)
        
        return await self._execute_with_metrics(OperationType.INSERT, _insert)
    
    # Health and Monitoring
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all database connections."""
        health_status = {
            "postgres": False,
            "weaviate": False,
            "overall": False
        }
        
        # Check PostgreSQL
        try:
            async with self.get_postgres_connection() as conn:
                await conn.fetchval("SELECT 1")
            health_status["postgres"] = True
            self._postgres_healthy = True
        except Exception as e:
            logger.warning(f"PostgreSQL health check failed: {e}")
            self._postgres_healthy = False
        
        # Check Weaviate
        try:
            client = self.get_weaviate_client()
            health_status["weaviate"] = client.is_ready()
            self._weaviate_healthy = health_status["weaviate"]
        except Exception as e:
            logger.warning(f"Weaviate health check failed: {e}")
            self._weaviate_healthy = False
        
        health_status["overall"] = health_status["postgres"] and health_status["weaviate"]
        return health_status
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics."""
        avg_latency = (
            self.metrics.total_latency / self.metrics.total_operations
            if self.metrics.total_operations > 0 else 0
        )
        
        success_rate = (
            self.metrics.successful_operations / self.metrics.total_operations
            if self.metrics.total_operations > 0 else 0
        )
        
        return {
            "total_operations": self.metrics.total_operations,
            "successful_operations": self.metrics.successful_operations,
            "failed_operations": self.metrics.failed_operations,
            "success_rate": success_rate,
            "average_latency": avg_latency,
            "operation_counts": dict(self.metrics.operation_counts),
            "postgres_healthy": self._postgres_healthy,
            "weaviate_healthy": self._weaviate_healthy,
            "pool_stats": self._get_pool_stats()
        }
    
    def _get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        if not self._postgres_pool:
            return {}
        
        return {
            "size": self._postgres_pool.get_size(),
            "idle_size": self._postgres_pool.get_idle_size(),
            "min_size": self._postgres_pool.get_min_size(),
            "max_size": self._postgres_pool.get_max_size()
        }

# Global database instance
_database_instance: Optional[UnifiedDatabase] = None

def get_database(
    postgres_url: Optional[str] = None,
    weaviate_url: Optional[str] = None,
    weaviate_api_key: Optional[str] = None
) -> UnifiedDatabase:
    """Get or create the global database instance."""
    global _database_instance
    
    if _database_instance is None:
        if not postgres_url:
            raise ValueError("postgres_url is required for first initialization")
        
        _database_instance = UnifiedDatabase(
            postgres_url=postgres_url,
            weaviate_url=weaviate_url or "http://localhost:8080",
            weaviate_api_key=weaviate_api_key
        )
    
    return _database_instance

async def initialize_database(
    postgres_url: str,
    weaviate_url: str = "http://localhost:8080",
    weaviate_api_key: Optional[str] = None
) -> UnifiedDatabase:
    """Initialize and return the global database instance."""
    db = get_database(postgres_url, weaviate_url, weaviate_api_key)
    await db.initialize()
    return db

async def close_database():
    """Close the global database instance."""
    global _database_instance
    if _database_instance:
        await _database_instance.close()
        _database_instance = None
