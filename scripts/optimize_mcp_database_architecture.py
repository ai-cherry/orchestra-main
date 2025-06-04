#!/usr/bin/env python3
"""
MCP and Database Architecture Optimization Script
Implements best practices and fixes issues identified in the audit
"""

import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


class MCPDatabaseOptimizer:
    """Optimizer for MCP and database architecture"""
    
    def __init__(self):
        self.optimizations = []
        self.start_time = datetime.now()
    
    async def run_optimizations(self):
        """Run all optimizations"""
        print("🚀 Starting MCP & Database Architecture Optimization...")
        print("=" * 80)
        
        # 1. Fix Environment Variables
        print("\n1️⃣ Setting up environment variables...")
        self.setup_environment_variables()
        
        # 2. Optimize Database Configurations
        print("\n2️⃣ Optimizing database configurations...")
        self.optimize_database_configs()
        
        # 3. Enhance MCP Server Configuration
        print("\n3️⃣ Enhancing MCP server configuration...")
        self.enhance_mcp_config()
        
        # 4. Implement Performance Optimizations
        print("\n4️⃣ Implementing performance optimizations...")
        self.implement_performance_optimizations()
        
        # 5. Create Health Check Scripts
        print("\n5️⃣ Creating health check scripts...")
        self.create_health_check_scripts()
        
        # 6. Generate Optimization Report
        print("\n6️⃣ Generating optimization report...")
        self.generate_report()
        
        print("\n✅ Optimization complete!")
    
    def setup_environment_variables(self):
        """Create environment configuration file"""
        env_template = """# Orchestra Database Configuration
# Copy this to .env and adjust values as needed

# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=conductor

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5

# Weaviate Configuration
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
WEAVIATE_API_KEY=your_weaviate_api_key_here

# API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Performance Settings
DATABASE_POOL_MIN_SIZE=5
DATABASE_POOL_MAX_SIZE=20
CACHE_TTL=3600
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60

# Cherry AI Website Settings
CHERRY_AI_API_URL=https://api.cherry.ai
CHERRY_AI_DOMAIN=cherry.ai
"""
        
        env_path = Path(".env.template")
        with open(env_path, 'w') as f:
            f.write(env_template)
        
        print(f"  ✓ Created {env_path}")
        self.optimizations.append("Created environment variable template")
        
        # Create production docker-compose with proper security
        self.create_production_docker_compose()
    
    def create_production_docker_compose(self):
        """Create production-ready docker-compose configuration"""
        docker_compose_prod = """version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: cherry_ai_postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --lc-collate=C --lc-ctype=C"
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    command: >
      postgres
      -c shared_buffers=256MB
      -c max_connections=200
      -c effective_cache_size=1GB
      -c maintenance_work_mem=64MB
      -c checkpoint_completion_target=0.9
      -c wal_buffers=16MB
      -c default_statistics_target=100
      -c random_page_cost=1.1
      -c effective_io_concurrency=200
      -c work_mem=4MB
      -c min_wal_size=1GB
      -c max_wal_size=4GB

  redis:
    image: redis:7-alpine
    container_name: cherry_ai_redis
    restart: unless-stopped
    command: >
      redis-server
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru
      --save 900 1
      --save 300 10
      --save 60 10000
      --appendonly yes
      --appendfsync everysec
      ${REDIS_PASSWORD:+--requirepass ${REDIS_PASSWORD}}
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  weaviate:
    image: semitechnologies/weaviate:latest
    container_name: cherry_ai_weaviate
    restart: unless-stopped
    ports:
      - "${WEAVIATE_PORT:-8080}:8080"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'false'
      AUTHENTICATION_APIKEY_ENABLED: 'true'
      AUTHENTICATION_APIKEY_ALLOWED_KEYS: '${WEAVIATE_API_KEY}'
      AUTHENTICATION_APIKEY_USERS: 'admin'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'text2vec-openai'
      ENABLE_MODULES: 'text2vec-openai,generative-openai'
      CLUSTER_HOSTNAME: 'node1'
      OPENAI_APIKEY: '${OPENAI_API_KEY}'
      LIMIT_RESOURCES: 'true'
      GOMAXPROCS: '4'
      PERSISTENCE_LSM_ACCESS_STRATEGY: 'mmap'
      TRACK_VECTOR_DIMENSIONS: 'true'
    volumes:
      - weaviate_data:/var/lib/weaviate
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:8080/v1/.well-known/ready"]
      interval: 10s
      timeout: 5s
      retries: 5
    mem_limit: 2g
    mem_reservation: 1g

  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: cherry_ai_api
    restart: unless-stopped
    environment:
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - WEAVIATE_HOST=weaviate
      - WEAVIATE_PORT=8080
      - WEAVIATE_API_KEY=${WEAVIATE_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DATABASE_POOL_MIN_SIZE=${DATABASE_POOL_MIN_SIZE:-5}
      - DATABASE_POOL_MAX_SIZE=${DATABASE_POOL_MAX_SIZE:-20}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      weaviate:
        condition: service_healthy
    volumes:
      - ./src:/app/src
      - ./scripts:/app/scripts
      - ./config:/app/config
      - ./data:/app/data
    command: uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4

volumes:
  postgres_data:
  redis_data:
  weaviate_data:

networks:
  default:
    name: cherry_ai_network
"""
        
        with open("docker-compose.production.yml", 'w') as f:
            f.write(docker_compose_prod)
        
        print("  ✓ Created docker-compose.production.yml with optimized settings")
        self.optimizations.append("Created production Docker Compose configuration")
    
    def optimize_database_configs(self):
        """Create optimized database configuration files"""
        
        # PostgreSQL optimization script
        pg_init_script = """-- PostgreSQL Initialization Script for Cherry AI

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create optimized indexes for common queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_memories_agent_id ON memories(agent_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_memories_created_at ON memories(created_at);

-- Create partitioned tables for high-volume data
CREATE TABLE IF NOT EXISTS conversations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id UUID NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE IF NOT EXISTS conversations_2025_01 PARTITION OF conversations
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE IF NOT EXISTS conversations_2025_02 PARTITION OF conversations
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- Add more partitions as needed

-- Performance tuning for Cherry AI workload
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
"""
        
        os.makedirs("init-scripts", exist_ok=True)
        with open("init-scripts/01-optimize-postgres.sql", 'w') as f:
            f.write(pg_init_script)
        
        print("  ✓ Created PostgreSQL optimization script")
        self.optimizations.append("Created PostgreSQL optimization script")
        
        # Redis configuration
        redis_config = """# Redis Configuration for Cherry AI

# Memory Management
maxmemory 512mb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec

# Performance
tcp-backlog 511
timeout 0
tcp-keepalive 300

# Slow Log
slowlog-log-slower-than 10000
slowlog-max-len 128

# Client Output Buffer Limits
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60

# Threading
io-threads 4
io-threads-do-reads yes
"""
        
        with open("redis.conf", 'w') as f:
            f.write(redis_config)
        
        print("  ✓ Created Redis configuration file")
        self.optimizations.append("Created Redis configuration")
    
    def enhance_mcp_config(self):
        """Enhance MCP server configuration"""
        
        # Load existing config
        config_path = Path("claude_mcp_config.json")
        with open(config_path) as f:
            config = json.load(f)
        
        # Add health check endpoints
        for server_name, server_config in config["mcp_servers"].items():
            if "health_check" not in server_config:
                server_config["health_check"] = {
                    "endpoint": f"{server_config['endpoint']}/health",
                    "interval": 30,
                    "timeout": 5,
                    "retries": 3
                }
            
            # Add retry configuration
            if "retry_config" not in server_config:
                server_config["retry_config"] = {
                    "max_retries": 3,
                    "backoff_factor": 2,
                    "max_backoff": 60
                }
        
        # Add load balancing configuration
        config["load_balancing"] = {
            "strategy": "round_robin",
            "health_check_interval": 30,
            "failover_timeout": 5
        }
        
        # Add circuit breaker configuration
        config["circuit_breaker"] = {
            "failure_threshold": 5,
            "recovery_timeout": 60,
            "half_open_requests": 3
        }
        
        # Save enhanced config
        with open("claude_mcp_config_enhanced.json", 'w') as f:
            json.dump(config, f, indent=2)
        
        print("  ✓ Created enhanced MCP configuration")
        self.optimizations.append("Enhanced MCP server configuration")
    
    def implement_performance_optimizations(self):
        """Create performance optimization utilities"""
        
        # Connection pool manager
        pool_manager = '''#!/usr/bin/env python3
"""
Connection Pool Manager for Orchestra
Manages database connection pools with monitoring
"""

import asyncio
import asyncpg
import redis.asyncio as redis
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ConnectionPoolManager:
    """Manages connection pools for all databases"""
    
    def __init__(self):
        self.pg_pool: Optional[asyncpg.Pool] = None
        self.redis_pool: Optional[redis.ConnectionPool] = None
        self._initialized = False
    
    async def initialize(self, config: Dict[str, Any]):
        """Initialize all connection pools"""
        if self._initialized:
            return
        
        # PostgreSQL pool
        self.pg_pool = await asyncpg.create_pool(
            host=config.get("POSTGRES_HOST", "localhost"),
            port=config.get("POSTGRES_PORT", 5432),
            user=config.get("POSTGRES_USER", "postgres"),
            password=config.get("POSTGRES_PASSWORD", "postgres"),
            database=config.get("POSTGRES_DB", "conductor"),
            min_size=config.get("DATABASE_POOL_MIN_SIZE", 5),
            max_size=config.get("DATABASE_POOL_MAX_SIZE", 20),
            command_timeout=60,
            max_queries=50000,
            max_inactive_connection_lifetime=300
        )
        logger.info("PostgreSQL connection pool initialized")
        
        # Redis pool
        self.redis_pool = redis.ConnectionPool(
            host=config.get("REDIS_HOST", "localhost"),
            port=config.get("REDIS_PORT", 6379),
            password=config.get("REDIS_PASSWORD"),
            max_connections=config.get("REDIS_MAX_CONNECTIONS", 50),
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            socket_keepalive=True,
            socket_keepalive_options={},
            health_check_interval=30
        )
        logger.info("Redis connection pool initialized")
        
        self._initialized = True
    
    async def get_pg_connection(self):
        """Get PostgreSQL connection from pool"""
        if not self.pg_pool:
            raise RuntimeError("PostgreSQL pool not initialized")
        return await self.pg_pool.acquire()
    
    def get_redis_client(self) -> redis.Redis:
        """Get Redis client with pool"""
        if not self.redis_pool:
            raise RuntimeError("Redis pool not initialized")
        return redis.Redis(connection_pool=self.redis_pool)
    
    async def close(self):
        """Close all connection pools"""
        if self.pg_pool:
            await self.pg_pool.close()
        if self.redis_pool:
            await self.redis_pool.disconnect()
        self._initialized = False
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all connections"""
        health = {
            "postgresql": False,
            "redis": False
        }
        
        # Check PostgreSQL
        try:
            async with self.pg_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                health["postgresql"] = True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
        
        # Check Redis
        try:
            client = self.get_redis_client()
            await client.ping()
            health["redis"] = True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
        
        return health


# Global instance
_pool_manager = ConnectionPoolManager()


async def get_pool_manager() -> ConnectionPoolManager:
    """Get global connection pool manager"""
    return _pool_manager
'''
        
        os.makedirs("src/core", exist_ok=True)
        with open("src/core/connection_pool_manager.py", 'w') as f:
            f.write(pool_manager)
        
        print("  ✓ Created connection pool manager")
        self.optimizations.append("Created connection pool manager")
        
        # Cache warming utility
        cache_warmer = '''#!/usr/bin/env python3
"""
Cache Warming Utility for Cherry AI
Pre-loads frequently accessed data into cache
"""

import asyncio
import json
from typing import List, Dict, Any
from datetime import datetime, timedelta


class CacheWarmer:
    """Warms cache with frequently accessed data"""
    
    def __init__(self, redis_client, weaviate_client):
        self.redis = redis_client
        self.weaviate = weaviate_client
        self.warming_tasks = []
    
    async def warm_agent_configs(self):
        """Pre-load agent configurations"""
        # Load agent configs from file
        with open("config/agents.yaml") as f:
            agents = yaml.safe_load(f)
        
        for agent_id, config in agents.items():
            cache_key = f"agent:config:{agent_id}"
            await self.redis.set(
                cache_key,
                json.dumps(config),
                ex=3600  # 1 hour TTL
            )
        
        print(f"  Warmed {len(agents)} agent configurations")
    
    async def warm_recent_memories(self, agent_ids: List[str]):
        """Pre-load recent memories for active agents"""
        for agent_id in agent_ids:
            # Get recent memories from Weaviate
            result = self.weaviate.query.get(
                "Memory",
                ["content", "memory_type", "importance", "timestamp"]
            ).with_where({
                "path": ["agent_id"],
                "operator": "Equal",
                "valueText": agent_id
            }).with_limit(100).do()
            
            if result and "data" in result:
                memories = result["data"]["Get"]["Memory"]
                cache_key = f"agent:memories:recent:{agent_id}"
                await self.redis.set(
                    cache_key,
                    json.dumps(memories),
                    ex=1800  # 30 minutes TTL
                )
        
        print(f"  Warmed recent memories for {len(agent_ids)} agents")
    
    async def warm_knowledge_base(self):
        """Pre-load frequently accessed knowledge"""
        # Get top knowledge items by access count
        result = self.weaviate.query.aggregate(
            "Knowledge"
        ).with_meta_count().with_group_by_filter(
            ["category"]
        ).do()
        
        if result and "data" in result:
            for category in result["data"]["Aggregate"]["Knowledge"]:
                cache_key = f"knowledge:category:{category['groupedBy']['category']}"
                await self.redis.set(
                    cache_key,
                    json.dumps(category),
                    ex=3600  # 1 hour TTL
                )
        
        print("  Warmed knowledge base categories")
    
    async def run_warming_cycle(self):
        """Run a complete cache warming cycle"""
        print("🔥 Starting cache warming cycle...")
        
        await self.warm_agent_configs()
        await self.warm_recent_memories(["cherry", "assistant", "conductor"])
        await self.warm_knowledge_base()
        
        print("✅ Cache warming complete")


async def schedule_cache_warming(warmer: CacheWarmer, interval_minutes: int = 30):
    """Schedule periodic cache warming"""
    while True:
        try:
            await warmer.run_warming_cycle()
        except Exception as e:
            print(f"Cache warming error: {e}")
        
        await asyncio.sleep(interval_minutes * 60)
'''
        
        with open("src/core/cache_warmer.py", 'w') as f:
            f.write(cache_warmer)
        
        print("  ✓ Created cache warming utility")
        self.optimizations.append("Created cache warming utility")
    
    def create_health_check_scripts(self):
        """Create comprehensive health check scripts"""
        
        health_check_script = '''#!/usr/bin/env python3
"""
Comprehensive Health Check for Cherry AI Infrastructure
"""

import asyncio
import aiohttp
import asyncpg
import redis
import weaviate
import json
from datetime import datetime
from typing import Dict, Any, List


class HealthChecker:
    """Performs comprehensive health checks"""
    
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()
    
    async def check_mcp_servers(self) -> Dict[str, Any]:
        """Check all MCP servers"""
        with open("claude_mcp_config.json") as f:
            config = json.load(f)
        
        results = {}
        async with aiohttp.ClientSession() as session:
            for server_name, server_config in config["mcp_servers"].items():
                endpoint = server_config["endpoint"]
                try:
                    async with session.get(f"{endpoint}/health", timeout=5) as resp:
                        results[server_name] = {
                            "status": "healthy" if resp.status == 200 else "unhealthy",
                            "response_time": resp.headers.get("X-Response-Time", "N/A"),
                            "endpoint": endpoint
                        }
                except Exception as e:
                    results[server_name] = {
                        "status": "unreachable",
                        "error": str(e),
                        "endpoint": endpoint
                    }
        
        return results
    
    async def check_postgresql(self) -> Dict[str, Any]:
        """Check PostgreSQL health"""
        try:
            conn = await asyncpg.connect(
                host="localhost",
                port=5432,
                user="postgres",
                password="postgres",
                database="conductor"
            )
            
            # Basic health
            version = await conn.fetchval("SELECT version()")
            
            # Connection count
            active_connections = await conn.fetchval(
                "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
            )
            
            # Database size
            db_size = await conn.fetchval(
                "SELECT pg_database_size(current_database())"
            )
            
            # Cache hit ratio
            cache_stats = await conn.fetchrow("""
                SELECT 
                    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as cache_hit_ratio
                FROM pg_statio_user_tables
            """)
            
            await conn.close()
            
            return {
                "status": "healthy",
                "version": version.split()[1],
                "active_connections": active_connections,
                "database_size_mb": db_size / 1024 / 1024,
                "cache_hit_ratio": float(cache_stats["cache_hit_ratio"] or 0)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis health"""
        try:
            r = redis.Redis(host="localhost", port=6379, decode_responses=True)
            
            # Ping
            r.ping()
            
            # Get info
            info = r.info()
            
            return {
                "status": "healthy",
                "version": info["redis_version"],
                "connected_clients": info["connected_clients"],
                "used_memory_human": info["used_memory_human"],
                "ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_weaviate(self) -> Dict[str, Any]:
        """Check Weaviate health"""
        try:
            client = weaviate.Client("http://localhost:8080")
            
            if client.is_ready():
                # Get schema
                schema = client.schema.get()
                
                # Get node status
                nodes = client.cluster.get_nodes_status()
                
                return {
                    "status": "healthy",
                    "classes": len(schema.get("classes", [])),
                    "nodes": len(nodes),
                    "version": nodes[0].get("version", "unknown") if nodes else "unknown"
                }
            else:
                return {"status": "unhealthy", "error": "Weaviate not ready"}
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        print("🏥 Running comprehensive health checks...")
        
        # Run checks in parallel
        mcp_task = asyncio.create_task(self.check_mcp_servers())
        pg_task = asyncio.create_task(self.check_postgresql())
        redis_task = asyncio.create_task(self.check_redis())
        weaviate_task = asyncio.create_task(self.check_weaviate())
        
        # Wait for all checks
        mcp_health = await mcp_task
        pg_health = await pg_task
        redis_health = await redis_task
        weaviate_health = await weaviate_task
        
        # Compile results
        results = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
            "mcp_servers": mcp_health,
            "postgresql": pg_health,
            "redis": redis_health,
            "weaviate": weaviate_health,
            "overall_status": self._determine_overall_status(
                mcp_health, pg_health, redis_health, weaviate_health
            )
        }
        
        return results
    
    def _determine_overall_status(self, *healths) -> str:
        """Determine overall system status"""
        statuses = []
        
        # Check MCP servers
        for server, health in healths[0].items():
            statuses.append(health.get("status", "unknown"))
        
        # Check databases
        for health in healths[1:]:
            statuses.append(health.get("status", "unknown"))
        
        if all(s == "healthy" for s in statuses):
            return "healthy"
        elif any(s == "unhealthy" or s == "unreachable" for s in statuses):
            return "unhealthy"
        else:
            return "degraded"


async def main():
    """Run health checks and display results"""
    checker = HealthChecker()
    results = await checker.run_health_checks()
    
    # Display results
    print("\\n" + "=" * 80)
    print("HEALTH CHECK RESULTS")
    print("=" * 80)
    print(f"Overall Status: {results['overall_status'].upper()}")
    print(f"Check Duration: {results['duration_seconds']:.2f}s")
    
    # MCP Servers
    print("\\nMCP Servers:")
    for server, health in results["mcp_servers"].items():
        status_icon = "✅" if health["status"] == "healthy" else "❌"
        print(f"  {status_icon} {server}: {health['status']}")
        if health.get("error"):
            print(f"     Error: {health['error']}")
    
    # Databases
    for db_name in ["postgresql", "redis", "weaviate"]:
        health = results[db_name]
        status_icon = "✅" if health["status"] == "healthy" else "❌"
        print(f"\\n{db_name.capitalize()}:")
        print(f"  {status_icon} Status: {health['status']}")
        if health.get("error"):
            print(f"  Error: {health['error']}")
        else:
            for key, value in health.items():
                if key != "status":
                    print(f"  {key}: {value}")
    
    # Save results
    with open(f"health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
'''
        
        with open("scripts/health_check_comprehensive.py", 'w') as f:
            f.write(health_check_script)
        
        os.chmod("scripts/health_check_comprehensive.py", 0o755)
        
        print("  ✓ Created comprehensive health check script")
        self.optimizations.append("Created health check script")
    
    def generate_report(self):
        """Generate optimization report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "optimizations_performed": self.optimizations,
            "files_created": [
                ".env.template",
                "docker-compose.production.yml",
                "init-scripts/01-optimize-postgres.sql",
                "redis.conf",
                "claude_mcp_config_enhanced.json",
                "src/core/connection_pool_manager.py",
                "src/core/cache_warmer.py",
                "scripts/health_check_comprehensive.py"
            ],
            "next_steps": [
                "1. Copy .env.template to .env and fill in your actual values",
                "2. Run docker-compose -f docker-compose.production.yml up -d",
                "3. Run scripts/health_check_comprehensive.py to verify all services",
                "4. Set up cron job for periodic health checks",
                "5. Monitor logs and metrics for optimization opportunities"
            ]
        }
        
        # Save report
        report_path = f"optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Optimization report saved to: {report_path}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("OPTIMIZATION SUMMARY")
        print("=" * 80)
        print(f"✅ Completed {len(self.optimizations)} optimizations:")
        for opt in self.optimizations:
            print(f"  - {opt}")
        
        print("\n📋 Next Steps:")
        for step in report["next_steps"]:
            print(f"  {step}")
        
        self.optimizations.append("Generated optimization report")


async def main():
    """Run the optimization process"""
    optimizer = MCPDatabaseOptimizer()
    await optimizer.run_optimizations()


if __name__ == "__main__":
    asyncio.run(main())