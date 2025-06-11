# TODO: Consider adding connection pooling configuration
"""
"""
    """Base database error"""
    """Database connection error"""
    """Database query error"""
    """Database transaction error"""
    """Standardized query result"""
    """Vector search result with scores"""
    """Abstract database interface"""
        """Establish database connection"""
        """Close database connection"""
        """Check database health"""
        """Execute a query"""
    """PostgreSQL database interface with async support"""
        """Establish PostgreSQL connection pool"""
            logger.info("PostgreSQL connection pool established")
            
        except Exception:

            
            pass
            self._connection_retries += 1
            if self._connection_retries <= self._max_retries:
                logger.warning(f"PostgreSQL connection failed (attempt {self._connection_retries}): {e}")
                await asyncio.sleep(2 ** self._connection_retries)
                await self.connect()
            else:
                raise ConnectionError(f"Failed to connect to PostgreSQL after {self._max_retries} attempts: {e}")
    
    async def disconnect(self) -> None:
        """Close PostgreSQL connection pool"""
            logger.info("PostgreSQL connection pool closed")
    
    async def health_check(self) -> bool:
        """Check PostgreSQL health"""
            logger.error(f"PostgreSQL health check failed: {e}")
            return False
    
    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Execute PostgreSQL query"""
            raise ConnectionError("PostgreSQL pool not initialized")
        
        start_time = time.time()
        
        try:

        
            pass
            async with self.pool.acquire() as conn:
                if params:
                    # Convert named parameters to positional if needed
                    if isinstance(params, dict):
                        result = await conn.fetch(query, *params.values())
                    else:
                        result = await conn.fetch(query, params)
                else:
                    result = await conn.fetch(query)
                
                # Convert asyncpg.Record to dict
                rows = [dict(row) for row in result]
                
                return QueryResult(
                    rows=rows,
                    count=len(rows),
                    execution_time=time.time() - start_time,
                    metadata={"query": query, "params": params}
                )
                
        except Exception:

                
            pass
            execution_time = time.time() - start_time
            logger.error(f"PostgreSQL query failed in {execution_time:.3f}s: {e}")
            raise QueryError(f"PostgreSQL query failed: {e}", retryable=True, original_error=e)
    
    async def execute_many(self, query: str, params_list: List[Dict[str, Any]]) -> int:
        """Execute query with multiple parameter sets"""
            raise ConnectionError("PostgreSQL pool not initialized")
        
        try:

        
            pass
            async with self.pool.acquire() as conn:
                # Convert to tuple list for executemany
                param_tuples = [tuple(params.values()) for params in params_list]
                result = await conn.executemany(query, param_tuples)
                return len(param_tuples)
                
        except Exception:

                
            pass
            logger.error(f"PostgreSQL executemany failed: {e}")
            raise QueryError(f"PostgreSQL executemany failed: {e}", retryable=True, original_error=e)
    
    @asynccontextmanager
    async def transaction(self):
        """Async context manager for transactions"""
            raise ConnectionError("PostgreSQL pool not initialized")
        
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                yield conn
    
    async def create_table_if_not_exists(self, table_name: str, schema: Dict[str, str]) -> None:
        """Create table if it doesn't exist"""
            columns.append(f"{col_name} {col_type}")
        
        create_query = f"""
        """
        logger.info(f"Table {table_name} created or verified")

class WeaviateInterface(DatabaseInterface):
    """Weaviate vector database interface"""
        """Establish Weaviate connection via the production client."""
            logger.info("WeaviateInterface connected via ProdWeaviateClient.")
        except Exception:

            pass
            # self.client should remain None or be explicitly set to None on failure
            self.client = None
            logger.error(f"WeaviateInterface failed to connect ProdWeaviateClient: {e}", exc_info=True)
            # Convert to a ConnectionError if not already
            if not isinstance(e, ConnectionError):
                raise ConnectionError(f"Failed to connect Weaviate production client: {e}") from e
            raise
    
    async def disconnect(self) -> None:
        """Close Weaviate connection via the production client."""
            logger.info("WeaviateInterface disconnected via ProdWeaviateClient.")
    
    async def health_check(self) -> bool:
        """Check Weaviate health via the production client."""
            logger.error(f"WeaviateInterface health check failed: {e}", exc_info=True)
            return False
    
    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Execute Weaviate query (GraphQL) via the production client."""
            raise ConnectionError("Weaviate client not initialized or not connected in ProdWeaviateClient.")
        
        start_time = time.time()
        
        try:

        
            pass
            # Assuming direct access to underlying client for raw GraphQL if not encapsulated
            # This is a temporary measure. Ideally ProdWeaviateClient would expose this.
            # result = self._prod_client._client.query.raw(query)
            # For now, let's assume we add a method to ProdWeaviateClient:
            if not hasattr(self._prod_client, 'raw_graphql_query'):
                logger.warning("ProdWeaviateClient does not have raw_graphql_query. Falling back to direct SDK access for execute.")
                if not self._prod_client._client: # Ensure underlying client exists
                     raise ConnectionError("Underlying Weaviate SDK client not available.")
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: self._prod_client._client.query.raw(query))
            else:
                result = await self._prod_client.raw_graphql_query(query) # Ideal case
            
            return QueryResult(
                rows=[result] if result is not None else [], # Ensure result is not None
                count=1 if result is not None else 0,
                execution_time=time.time() - start_time,
                metadata={"query": query, "params": params}
            )
            
        except Exception:

            
            pass
            execution_time = time.time() - start_time
            logger.error(f"WeaviateInterface query failed in {execution_time:.3f}s: {e}", exc_info=True)
            raise QueryError(f"WeaviateInterface query failed: {e}", retryable=True, original_error=e)
    
    async def vector_search(self, collection_name: str, vector: List[float], 
                           limit: int = 10, where_filter: Optional[Dict] = None,
                           return_properties: Optional[List[str]] = None) -> VectorSearchResult:
        """Perform vector similarity search using ProdWeaviateClient."""
            raise ConnectionError("ProdWeaviateClient not initialized in WeaviateInterface.")
        
        start_time = time.time()
        try:

            pass
            # This assumes ProdWeaviateClient will have a generic search method.
            # Let's name it `search_objects_near_vector` for now.
            # This method needs to be added to ProdWeaviateClient.
            if not hasattr(self._prod_client, 'search_objects_near_vector'):
                raise NotImplementedError("ProdWeaviateClient must implement search_objects_near_vector for WeaviateInterface.vector_search")

            # The search_objects_near_vector method in ProdWeaviateClient should return a list of dicts
            # that match the structure expected by VectorSearchResult or be adapted here.
            # For now, assume it returns a list of dicts with 'id', 'properties', 'score', 'distance'.
            
            # Mapping `return_properties` from this interface to ProdWeaviateClient's method
            # Assuming ProdWeaviateClient's search method can take `return_properties`
            search_results = await self._prod_client.search_objects_near_vector(
                collection_name=collection_name,
                vector=vector,
                limit=limit,
                filters=where_filter, # Assuming ProdWeaviateClient uses 'filters'
                return_properties=return_properties
            )

            objects = []
            scores = []
            # ProdWeaviateClient.search_... methods return list of dicts already containing id, properties, score, distance
            for item in search_results: # search_results is List[Dict[str,Any]]
                obj_data = {"id": item.get("id"), "properties": item} # Adjust based on actual return
                # Remove score and distance from properties if they are separate
                obj_props = item.copy()
                score = obj_props.pop("score", 0.0)
                obj_props.pop("distance", None)
                obj_props.pop("id", None) # id is top-level
                
                objects.append({"id": item.get("id"), "properties": obj_props, "metadata": {"score": score, "distance": item.get("distance")}})
                scores.append(score)

            return VectorSearchResult(
                objects=objects,
                scores=scores,
                total_count=len(objects),
                execution_time=time.time() - start_time,
                metadata={"collection": collection_name, "vector_dim": len(vector)}
            )
            
        except Exception:

            
            pass
            execution_time = time.time() - start_time
            logger.error(f"WeaviateInterface vector search failed: {e}", exc_info=True)
            raise QueryError(f"WeaviateInterface vector search failed: {e}", retryable=True, original_error=e)
    
    async def insert_objects(self, collection_name: str, objects: List[Dict[str, Any]]) -> int:
        """Insert multiple objects into collection using ProdWeaviateClient."""
            raise ConnectionError("ProdWeaviateClient not initialized in WeaviateInterface.")
        
        try:

        
            pass
            # This assumes ProdWeaviateClient will have a generic batch insert method.
            # Let's name it `add_objects_batch`. This needs to be added to ProdWeaviateClient.
            if not hasattr(self._prod_client, 'add_objects_batch'):
                 raise NotImplementedError("ProdWeaviateClient must implement add_objects_batch for WeaviateInterface.insert_objects")

            # The objects here are expected to be dicts with properties, and optionally 'id' and 'vector'.
            # ProdWeaviateClient's method should handle this.
            num_inserted = await self._prod_client.add_objects_batch(
                collection_name=collection_name,
                objects=objects
            )
            return num_inserted
            
        except Exception:

            
            pass
            logger.error(f"WeaviateInterface insert_objects failed: {e}", exc_info=True)
            raise QueryError(f"WeaviateInterface insert_objects failed: {e}", retryable=True, original_error=e)
    
    async def create_collection_if_not_exists(self, collection_name: str, 
                                            properties: List[Dict[str, Any]], # e.g. [{"name": "prop_name", "data_type": "TEXT"}]
                                            vectorizer_config: Optional[Dict] = None) -> None: # vectorizer_config is not directly used by current _ensure_schema
        """Create collection if it doesn't exist using ProdWeaviateClient."""
            raise ConnectionError("ProdWeaviateClient not initialized in WeaviateInterface.")
        
        try:

        
            pass
            # ProdWeaviateClient._ensure_schema takes properties in a slightly different format
            # e.g. {"name": "prop_name", "dataType": ["text"]}
            # This method needs to map from WeaviateInterface's property format if different.
            # Current ProdWeaviateClient._ensure_schema takes `properties: List[Dict[str, Any]]`
            # Example: `{"name": "agent_id", "dataType": ["text"]}`. This matches.
            
            # The `vectorizer_config` from `WeaviateInterface` is not explicitly passed to
            # `_ensure_schema` in `ProdWeaviateClient` as it defaults to text2vec-openai.
            # If `vectorizer_config` needs to be dynamic, `_ensure_schema` must be updated.
            if vectorizer_config:
                logger.warning(f"Vectorizer config provided to WeaviateInterface.create_collection_if_not_exists for {collection_name} "
                               f"is not currently passed to ProdWeaviateClient._ensure_schema, which uses defaults. This may need adjustment.")

            await self._prod_client._ensure_schema(
                collection_name=collection_name,
                properties=properties, # Assuming format matches
                description=f"Collection {collection_name}" # Default description
            )
            logger.info(f"WeaviateInterface: Collection {collection_name} ensured via ProdWeaviateClient.")
            
        except Exception:

            
            pass
            logger.error(f"WeaviateInterface failed to create collection {collection_name}: {e}", exc_info=True)
            raise QueryError(f"WeaviateInterface failed to create collection: {e}", retryable=False, original_error=e)

class UnifiedDatabase:
    """
    """
            "postgresql_queries": 0,
            "weaviate_queries": 0,
            "total_execution_time": 0.0,
            "connection_errors": 0,
            "query_errors": 0
        }
    
    async def connect(self) -> None:
        """Connect to both PostgreSQL and Weaviate"""
            logger.info("Unified database connection established")
            
            # Start health monitoring
            self._health_check_task = asyncio.create_task(self._monitor_health())
            
        except Exception:

            
            pass
            self.metrics["connection_errors"] += 1
            logger.error(f"Failed to establish unified database connection: {e}")
            raise ConnectionError(f"Database connection failed: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from both databases"""
        logger.info("Unified database disconnected")
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of both databases"""
            "postgresql": isinstance(postgresql_health, bool) and postgresql_health,
            "weaviate": isinstance(weaviate_health, bool) and weaviate_health,
            "unified": (
                isinstance(postgresql_health, bool) and postgresql_health and
                isinstance(weaviate_health, bool) and weaviate_health
            )
        }
    
    # PostgreSQL Operations
    async def sql_execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Execute SQL query on PostgreSQL"""
            raise ConnectionError("Database not connected")
        
        try:

        
            pass
            self.metrics["postgresql_queries"] += 1
            result = await self.postgresql.execute(query, params)
            self.metrics["total_execution_time"] += result.execution_time
            return result
        except Exception:

            pass
            self.metrics["query_errors"] += 1
            raise
    
    async def sql_execute_many(self, query: str, params_list: List[Dict[str, Any]]) -> int:
        """Execute SQL query with multiple parameter sets"""
            raise ConnectionError("Database not connected")
        
        try:

        
            pass
            return await self.postgresql.execute_many(query, params_list)
        except Exception:

            pass
            self.metrics["query_errors"] += 1
            raise
    
    @asynccontextmanager
    async def sql_transaction(self):
        """SQL transaction context manager"""
            raise ConnectionError("Database not connected")
        
        async with self.postgresql.transaction() as tx:
            yield tx
    
    async def create_table(self, table_name: str, schema: Dict[str, str]) -> None:
        """Create table if not exists"""
        """Perform vector similarity search"""
            raise ConnectionError("Database not connected")
        
        try:

        
            pass
            self.metrics["weaviate_queries"] += 1
            result = await self.weaviate.vector_search(
                collection_name, vector, limit, where_filter, return_properties
            )
            self.metrics["total_execution_time"] += result.execution_time
            return result
        except Exception:

            pass
            self.metrics["query_errors"] += 1
            raise
    
    async def vector_insert(self, collection_name: str, objects: List[Dict[str, Any]]) -> int:
        """Insert objects into vector collection"""
            raise ConnectionError("Database not connected")
        
        try:

        
            pass
            return await self.weaviate.insert_objects(collection_name, objects)
        except Exception:

            pass
            self.metrics["query_errors"] += 1
            raise
    
    async def create_collection(self, collection_name: str, 
                               properties: List[Dict[str, Any]],
                               vectorizer_config: Optional[Dict] = None) -> None:
        """Create vector collection if not exists"""
        """Perform both SQL and vector search simultaneously"""
            raise ConnectionError("Database not connected")
        
        # Execute both queries concurrently
        sql_task = self.sql_execute(sql_query, sql_params)
        vector_task = self.vector_search(collection_name, vector, limit)
        
        sql_result, vector_result = await asyncio.gather(sql_task, vector_task)
        return sql_result, vector_result
    
    async def store_with_vector(self, table_name: str, sql_data: Dict[str, Any],
                               collection_name: str, vector_data: Dict[str, Any]) -> Tuple[str, str]:
        """Store data in both SQL table and vector collection"""
            raise ConnectionError("Database not connected")
        
        # Generate IDs
        sql_id = str(uuid4())
        vector_id = str(uuid4())
        
        # Add IDs to data
        sql_data["id"] = sql_id
        vector_data["id"] = vector_id
        vector_data["sql_reference_id"] = sql_id  # Link to SQL record
        
        try:

        
            pass
            # Use transaction for SQL, batch for vector
            async with self.sql_transaction() as tx:
                # Insert SQL data
                columns = list(sql_data.keys())
                values = list(sql_data.values())
                placeholders = ", ".join([f"${i+1}" for i in range(len(values))])
                
                sql_query = f"""
                INSERT INTO {table_name} ({", ".join(columns)})
                VALUES ({placeholders})
                """
            logger.error(f"Hybrid storage failed: {e}")
            raise QueryError(f"Hybrid storage failed: {e}", retryable=True, original_error=e)
    
    # Monitoring and Maintenance
    async def _monitor_health(self) -> None:
        """Background task to monitor database health"""
                if not health["unified"]:
                    logger.warning(f"Database health check failed: {health}")
                    
                    # Attempt reconnection if needed
                    if not health["postgresql"]:
                        try:

                            pass
                            await self.postgresql.connect()
                        except Exception:

                            pass
                            logger.error(f"PostgreSQL reconnection failed: {e}")
                    
                    if not health["weaviate"]:
                        try:

                            pass
                            await self.weaviate.connect()
                        except Exception:

                            pass
                            logger.error(f"Weaviate reconnection failed: {e}")
                            
            except Exception:

                            
                pass
                break
            except Exception:

                pass
                logger.error(f"Health monitoring error: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get database operation metrics"""
        total_queries = self.metrics["postgresql_queries"] + self.metrics["weaviate_queries"]
        
        return {
            **self.metrics,
            "total_queries": total_queries,
            "average_execution_time": (
                self.metrics["total_execution_time"] / total_queries
                if total_queries > 0 else 0
            ),
            "error_rate": (
                self.metrics["query_errors"] / total_queries
                if total_queries > 0 else 0
            )
        }
    
    # Context manager support
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

# Global database instance
_database_instance: Optional[UnifiedDatabase] = None

def get_database(config: Optional[DatabaseConfig] = None) -> UnifiedDatabase:
    """Get or create the global database instance"""
    """Reset the global database instance"""
    "UnifiedDatabase",
    "DatabaseError",
    "ConnectionError", 
    "QueryError",
    "TransactionError",
    "QueryResult",
    "VectorSearchResult",
    "get_database",
    "reset_database"
] 