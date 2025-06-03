"""
"""
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
    """Base database error."""
    """Database connection error."""
    """Query execution error."""
    """Vector search result."""
    """Hybrid search result combining relational and vector data."""
    """
    """
        weaviate_url: str = "http://localhost:8080",
        weaviate_api_key: Optional[str] = None,
        pool_size: int = 10,
        max_overflow: int = 20
    ):
        """Initialize unified database interface."""
        """Initialize database connections."""
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
            
        except Exception:

            
            pass
            logger.error(f"Database initialization failed: {e}")
            raise ConnectionError(f"Failed to initialize databases: {e}")
    
    async def close(self) -> None:
        """Close database connections."""
        logger.info("Database connections closed")
    
    @asynccontextmanager
    async def get_postgres_connection(self):
        """Get PostgreSQL connection from pool."""
            raise ConnectionError("PostgreSQL pool not initialized")
        
        connection = None
        try:

            pass
            connection = await self._postgres_pool.acquire()
            yield connection
        finally:
            if connection:
                await self._postgres_pool.release(connection)
    
    def get_weaviate_client(self) -> weaviate.Client:
        """Get Weaviate client."""
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
        """Insert record into PostgreSQL table."""
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
            "postgres": False,
            "weaviate": False,
            "overall": False
        }
        
        # Check PostgreSQL
        try:

            pass
            async with self.get_postgres_connection() as conn:
                await conn.fetchval("SELECT 1")
            health_status["postgres"] = True
            self._postgres_healthy = True
        except Exception:

            pass
            logger.warning(f"PostgreSQL health check failed: {e}")
            self._postgres_healthy = False
        
        # Check Weaviate
        try:

            pass
            client = self.get_weaviate_client()
            health_status["weaviate"] = client.is_ready()
            self._weaviate_healthy = health_status["weaviate"]
        except Exception:

            pass
            logger.warning(f"Weaviate health check failed: {e}")
            self._weaviate_healthy = False
        
        health_status["overall"] = health_status["postgres"] and health_status["weaviate"]
        return health_status
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics."""
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
    """Close the global database instance."""