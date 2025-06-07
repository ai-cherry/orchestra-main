"""
Performance optimization configurations
"""

import os
from typing import Dict, Any

class PerformanceConfig:
    """Performance tuning configurations"""
    
    # Connection pool settings
    DATABASE_POOL_SIZE = int(os.getenv("CONNECTION_POOL_SIZE", "20"))
    DATABASE_POOL_TIMEOUT = 30
    DATABASE_POOL_RECYCLE = 3600
    
    # Request timeouts
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "60"))
    AGENT_TASK_TIMEOUT = 120
    WEB_SCRAPING_TIMEOUT = 30
    
    # Caching settings
    CACHE_TTL = 300  # 5 minutes
    CACHE_MAX_SIZE = 1000
    
    # Batch processing
    BATCH_SIZE = 50
    MAX_BATCH_WAIT = 1.0  # seconds
    
    # Circuit breaker settings
    CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60
    CIRCUIT_BREAKER_EXPECTED_EXCEPTION = (ConnectionError, TimeoutError)
    
    @classmethod
    def get_database_config(cls) -> Dict[str, Any]:
        """Get optimized database configuration"""
        return {
            "pool_size": cls.DATABASE_POOL_SIZE,
            "max_overflow": 10,
            "pool_timeout": cls.DATABASE_POOL_TIMEOUT,
            "pool_recycle": cls.DATABASE_POOL_RECYCLE,
            "pool_pre_ping": True,
            "echo": False,
            "connect_args": {
                "connect_timeout": 10,
                "application_name": "ai_orchestration",
                "options": "-c statement_timeout=60000"  # 60 second statement timeout
            }
        }
        
    @classmethod
    def get_redis_config(cls) -> Dict[str, Any]:
        """Get optimized Redis configuration"""
        return {
            "decode_responses": True,
            "max_connections": 50,
            "socket_timeout": 5,
            "socket_connect_timeout": 5,
            "retry_on_timeout": True,
            "health_check_interval": 30
        }
        
    @classmethod
    def get_async_config(cls) -> Dict[str, Any]:
        """Get async execution configuration"""
        return {
            "max_workers": os.cpu_count() * 2,
            "task_timeout": cls.AGENT_TASK_TIMEOUT,
            "graceful_shutdown_timeout": 30
        }

# Query optimization helpers
OPTIMIZED_INDEXES = [
    # Agent queries
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agents_status ON agents(status) WHERE status = 'active'",
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agents_domain ON agents(domain)",
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agents_created ON agents(created_at DESC)",
    
    # Task queries
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tasks_agent_status ON tasks(agent_id, status)",
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tasks_priority ON tasks(priority DESC, created_at)",
    
    # Metrics queries
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp DESC)",
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_metrics_agent_time ON metrics(agent_id, timestamp DESC)",
    
    # Composite indexes for common queries
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agents_domain_status ON agents(domain, status)",
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tasks_status_priority ON tasks(status, priority DESC)"
]

# Materialized views for reporting
MATERIALIZED_VIEWS = [
    """
    CREATE MATERIALIZED VIEW IF NOT EXISTS agent_performance_summary AS
    SELECT 
        a.id as agent_id,
        a.domain,
        COUNT(t.id) as total_tasks,
        AVG(t.execution_time) as avg_execution_time,
        SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
        SUM(CASE WHEN t.status = 'failed' THEN 1 ELSE 0 END) as failed_tasks,
        MAX(t.completed_at) as last_activity
    FROM agents a
    LEFT JOIN tasks t ON a.id = t.agent_id
    GROUP BY a.id, a.domain
    """,
    
    """
    CREATE MATERIALIZED VIEW IF NOT EXISTS hourly_metrics AS
    SELECT 
        date_trunc('hour', timestamp) as hour,
        agent_id,
        AVG(response_time) as avg_response_time,
        COUNT(*) as request_count,
        SUM(CASE WHEN error_code IS NOT NULL THEN 1 ELSE 0 END) as error_count
    FROM metrics
    WHERE timestamp > NOW() - INTERVAL '7 days'
    GROUP BY date_trunc('hour', timestamp), agent_id
    """
]
