#!/usr/bin/env python3
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
    print("\n" + "=" * 80)
    print("HEALTH CHECK RESULTS")
    print("=" * 80)
    print(f"Overall Status: {results['overall_status'].upper()}")
    print(f"Check Duration: {results['duration_seconds']:.2f}s")
    
    # MCP Servers
    print("\nMCP Servers:")
    for server, health in results["mcp_servers"].items():
        status_icon = "✅" if health["status"] == "healthy" else "❌"
        print(f"  {status_icon} {server}: {health['status']}")
        if health.get("error"):
            print(f"     Error: {health['error']}")
    
    # Databases
    for db_name in ["postgresql", "redis", "weaviate"]:
        health = results[db_name]
        status_icon = "✅" if health["status"] == "healthy" else "❌"
        print(f"\n{db_name.capitalize()}:")
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
