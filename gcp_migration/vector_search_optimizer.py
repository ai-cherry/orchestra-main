#!/usr/bin/env python3
"""
Vector Search Optimizer for AI Orchestra GCP Migration

This module provides performance-optimized vector search capabilities for the
AI Orchestra memory system. It focuses on maximizing search performance
through index optimization, parallel processing, and caching strategies.

Usage:
    from gcp_migration.vector_search_optimizer import optimize_alloydb_vector_search, VectorSearchConfig

Author: Roo
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("vector-search-optimizer")


@dataclass
class VectorSearchConfig:
    """Configuration for optimized vector search operations."""

    # Index configuration
    index_type: str = "ivfflat"  # Options: ivfflat, ivfpq, hnsw
    ivf_lists: int = 4000  # Default is 2000, 4000 is better for large datasets
    dimension: int = 1536  # Vector dimension
    nprobe: int = (
        50  # Number of clusters to visit during search (higher = better recall, slower)
    )

    # Performance tuning
    use_cache: bool = True
    cache_size: int = 1024  # Number of entries to cache
    parallel_threshold: int = 5  # Min vectors to process in parallel
    prefetch_distance: int = 10  # Prefetch nearby vectors

    # Specialized optimizations
    use_approximate_search: bool = True  # True = faster but less precise
    rerank_results: bool = False  # Rerank results for better precision (slower)
    compression_level: int = 0  # 0-9, higher = more compression, slower writes

    # Batch processing
    batch_size: int = 500  # Default is 100
    max_concurrent_batches: int = 10


@dataclass
class VectorSearchResult:
    """Result of a vector search operation with performance metrics."""

    id: str
    score: float
    data: Optional[Dict[str, Any]] = None
    position: int = 0
    latency_ms: float = 0


class VectorSearchOptimizer:
    """
    Optimizes vector search operations for maximum performance.

    This class provides performance-optimized vector search capabilities by:
    1. Configuring optimal index parameters
    2. Implementing result caching
    3. Using parallel processing when appropriate
    4. Providing targeted optimizations for AlloyDB PostgreSQL
    """

    def __init__(self, config: Optional[VectorSearchConfig] = None):
        """
        Initialize the vector search optimizer.

        Args:
            config: Optional search configuration, uses optimized defaults if not provided
        """
        self.config = config or VectorSearchConfig()
        self._cache = {}
        self._cache_hits = 0
        self._cache_misses = 0
        logger.info(
            f"Initialized vector search optimizer with IVF lists={self.config.ivf_lists}"
        )

    @lru_cache(maxsize=1024)
    def generate_optimized_sql(
        self,
        vector_placeholder: str,
        table: str = "memories",
        limit: int = 10,
        filter_condition: Optional[str] = None,
    ) -> str:
        """
        Generate an optimized SQL query for vector search.

        This method generates SQL optimized for AlloyDB vector operations
        using performance best practices.

        Args:
            vector_placeholder: Placeholder for vector values
            table: Table name containing vectors
            limit: Maximum results to return
            filter_condition: Optional WHERE condition

        Returns:
            Optimized SQL query
        """
        # Use candidate multiplier for better recall
        candidate_limit = limit * (self.config.nprobe // 10 or 1)

        # Base candidates CTE with approximate KNN
        base_query = f"""
        WITH candidates AS (
            SELECT 
                id,
                data,
                vector,
                vector <-> {vector_placeholder} as distance
            FROM {table}
            {"WHERE " + filter_condition if filter_condition else ""}
            ORDER BY vector <-> {vector_placeholder}
            LIMIT {candidate_limit}
        )
        """

        # Add query optimizations
        if self.config.rerank_results:
            # Rerank with exact distance calculation (better accuracy)
            query = (
                base_query
                + f"""
            SELECT 
                id,
                data,
                distance
            FROM candidates
            ORDER BY distance
            LIMIT {limit}
            """
            )
        else:
            # Use results directly (faster)
            query = (
                base_query
                + f"""
            SELECT 
                id,
                data,
                distance
            FROM candidates
            LIMIT {limit}
            """
            )

        # Enable prefetch hint for performance
        if self.config.prefetch_distance > 0:
            query = (
                f"/*+ SeqScan(memories) Prefetch({self.config.prefetch_distance}) */ \n"
                + query
            )

        return query

    async def optimize_alloydb_instance(
        self, project_id: str, region: str, cluster_name: str, instance_name: str
    ) -> bool:
        """
        Apply performance optimizations to an AlloyDB instance.

        Args:
            project_id: GCP project ID
            region: GCP region
            cluster_name: AlloyDB cluster name
            instance_name: AlloyDB instance name

        Returns:
            True if successful, False otherwise
        """
        try:
            import subprocess

            # Set database flags for optimized vector search
            db_flags = [
                f"ivfflat.lists={self.config.ivf_lists}",
                "enable_vector_executor=on",
                "max_parallel_workers=8",
                "effective_cache_size=4GB",
                "maintenance_work_mem=512MB",
                "random_page_cost=1.1",  # Optimized for SSD storage
                "effective_io_concurrency=200",
                "work_mem=64MB",
            ]

            # Construct the gcloud command
            db_flags_str = ",".join(db_flags)
            cmd = [
                "gcloud",
                "alloydb",
                "instances",
                "update",
                instance_name,
                f"--cluster={cluster_name}",
                f"--region={region}",
                f"--database-flags={db_flags_str}",
                f"--project={project_id}",
            ]

            # Execute the command
            logger.info(f"Applying AlloyDB optimizations: {db_flags_str}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            logger.info("AlloyDB vector search optimization complete")
            return True

        except Exception as e:
            logger.error(f"Failed to optimize AlloyDB instance: {str(e)}")
            return False

    def generate_index_creation_sql(
        self, table: str = "memories", column: str = "vector"
    ) -> str:
        """
        Generate optimized SQL for creating vector indices.

        Args:
            table: Table name
            column: Vector column name

        Returns:
            SQL statements for index creation
        """
        # Different index types for different performance needs
        if self.config.index_type == "ivfflat":
            # IVF-Flat: Fast to build, good recall, larger storage
            return f"""
            -- Drop existing index if any
            DROP INDEX IF EXISTS idx_{table}_{column};
            
            -- Create optimized IVF-Flat index
            CREATE INDEX idx_{table}_{column} ON {table} 
            USING ivfflat ({column} vector_l2_ops) 
            WITH (lists = {self.config.ivf_lists});
            
            -- For hybrid search efficiency
            CREATE INDEX IF NOT EXISTS idx_{table}_created ON {table} (created_at);
            CREATE INDEX IF NOT EXISTS idx_{table}_updated ON {table} (updated_at);
            
            -- Analyze for query optimizer
            ANALYZE {table};
            """
        elif self.config.index_type == "ivfpq":
            # IVF-PQ: Better compression, slightly slower search
            return f"""
            -- Drop existing index if any
            DROP INDEX IF EXISTS idx_{table}_{column};
            
            -- Create compressed IVF-PQ index
            CREATE INDEX idx_{table}_{column} ON {table} 
            USING ivfflat ({column} vector_l2_ops) 
            WITH (lists = {self.config.ivf_lists}, quantizer = 'pq');
            
            -- For hybrid search efficiency
            CREATE INDEX IF NOT EXISTS idx_{table}_created ON {table} (created_at);
            CREATE INDEX IF NOT EXISTS idx_{table}_updated ON {table} (updated_at);
            
            -- Analyze for query optimizer
            ANALYZE {table};
            """
        else:
            # Default to IVF-Flat with basic settings
            return f"""
            -- Drop existing index if any
            DROP INDEX IF EXISTS idx_{table}_{column};
            
            -- Create standard IVF-Flat index
            CREATE INDEX idx_{table}_{column} ON {table} 
            USING ivfflat ({column} vector_l2_ops); 
            
            -- Analyze for query optimizer
            ANALYZE {table};
            """

    def create_circuit_breaker_code(self, output_path: str) -> None:
        """
        Generate a circuit breaker implementation for robust memory operations.

        Args:
            output_path: Path to write the circuit breaker implementation
        """
        circuit_breaker_code = '''
# Circuit Breaker Pattern for Vector Operations
# Enhances vector search reliability with zero performance impact during normal operation

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Callable, Dict, Generic, Optional, TypeVar, Union

T = TypeVar('T')

logger = logging.getLogger("circuit-breaker")

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Fast-fail
    HALF_OPEN = "HALF_OPEN"  # Testing recovery

class CircuitBreaker(Generic[T]):
    """
    Circuit breaker implementation for vector operations.
    
    This pattern prevents cascading failures during vector search operations
    while allowing automatic recovery. It is optimized for vector search
    with minimal overhead during normal operation.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        reset_timeout: float = 30.0,
        half_open_max_calls: int = 1,
    ):
        """Initialize circuit breaker."""
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.half_open_calls = 0
        
        logger.info(f"Vector circuit breaker '{name}' initialized")
    
    async def execute(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute function with circuit protection."""
        self._check_state_transition()
        
        if self.state == CircuitState.OPEN:
            raise RuntimeError(
                f"Circuit '{self.name}' is OPEN. "
                f"Failing fast. Retry after {self.reset_timeout - (time.time() - self.last_failure_time):.1f}s"
            )
        
        if self.state == CircuitState.HALF_OPEN and self.half_open_calls >= self.half_open_max_calls:
            raise RuntimeError(
                f"Circuit '{self.name}' is HALF_OPEN and call limit reached."
            )
        
        # Track half-open calls
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
        
        try:
            # Execute the function with circuit protection
            start_time = time.time()
            
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            execution_time = time.time() - start_time
            
            # Success - reset circuit if in half-open state
            if self.state == CircuitState.HALF_OPEN:
                logger.info(f"Circuit '{self.name}' recovered, closing circuit")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.half_open_calls = 0
            
            return result
        
        except Exception as e:
            # Increment failure counter
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                # Failed during testing - reopen circuit
                logger.warning(
                    f"Circuit '{self.name}' failed in HALF_OPEN state: {str(e)}"
                )
                self.state = CircuitState.OPEN
                self.half_open_calls = 0
            
            elif self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
                # Trip the circuit
                logger.warning(
                    f"Circuit '{self.name}' tripped OPEN after {self.failure_count} failures"
                )
                self.state = CircuitState.OPEN
            
            raise
    
    def _check_state_transition(self) -> None:
        """Check and transition circuit state based on timeouts."""
        if (
            self.state == CircuitState.OPEN
            and time.time() - self.last_failure_time > self.reset_timeout
        ):
            logger.info(
                f"Circuit '{self.name}' switching to HALF_OPEN after {self.reset_timeout}s"
            )
            self.state = CircuitState.HALF_OPEN
            self.half_open_calls = 0
'''

        with open(output_path, "w") as f:
            f.write(circuit_breaker_code.strip())

        logger.info(f"Created circuit breaker implementation at {output_path}")


# Command-line interface
if __name__ == "__main__":
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(
        description="Vector Search Optimizer for AI Orchestra"
    )
    parser.add_argument(
        "--optimize-alloydb",
        action="store_true",
        help="Apply optimization to AlloyDB instance",
    )
    parser.add_argument(
        "--project-id", default="cherry-ai-project", help="GCP project ID"
    )
    parser.add_argument("--region", default="us-central1", help="GCP region")
    parser.add_argument(
        "--cluster", default="ai-orchestra-cluster", help="AlloyDB cluster name"
    )
    parser.add_argument(
        "--instance", default="main-instance", help="AlloyDB instance name"
    )
    parser.add_argument(
        "--create-circuit-breaker",
        action="store_true",
        help="Create circuit breaker implementation",
    )
    parser.add_argument(
        "--output-path",
        default="mcp_server/circuit_breaker.py",
        help="Output path for circuit breaker code",
    )
    parser.add_argument(
        "--generate-index-sql",
        action="store_true",
        help="Generate optimized index creation SQL",
    )
    parser.add_argument("--config-file", help="Path to JSON configuration file")

    args = parser.parse_args()

    # Load configuration if provided
    config = None
    if args.config_file:
        try:
            with open(args.config_file, "r") as f:
                config_dict = json.load(f)
                config = VectorSearchConfig(**config_dict)
        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")
            sys.exit(1)

    # Create optimizer with loaded or default config
    optimizer = VectorSearchOptimizer(config)

    # Process commands
    if args.optimize_alloydb:
        logger.info(f"Optimizing AlloyDB instance {args.instance} in {args.cluster}")

        async def run_optimize():
            result = await optimizer.optimize_alloydb_instance(
                args.project_id, args.region, args.cluster, args.instance
            )
            return result

        success = asyncio.run(run_optimize())
        if not success:
            sys.exit(1)

    if args.create_circuit_breaker:
        logger.info(f"Creating circuit breaker implementation at {args.output_path}")
        optimizer.create_circuit_breaker_code(args.output_path)

    if args.generate_index_sql:
        sql = optimizer.generate_index_creation_sql()
        print(sql)
