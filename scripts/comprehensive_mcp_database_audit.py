import logging
logger = logging.getLogger(__name__)

#!/usr/bin/env python3
"""
Comprehensive MCP Server and Database Architecture Audit
Performs deep analysis of MCP connections, database configurations,
and memory management with optimization recommendations.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import psutil
import redis
import asyncpg
import weaviate
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from shared.database.unified_database import UnifiedDatabase
    from core.redis.resilient_client import ResilientRedisClient, redis_health_check
    from core.redis.config import RedisConfig
    from core.redis.monitoring import RedisHealthMonitor
except ImportError as e:
    print(f"Warning: Some imports failed: {e}")
    UnifiedDatabase = None
    ResilientRedisClient = None


class ComponentStatus(Enum):
    """Component health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class AuditResult:
    """Audit result for a component"""
    component: str
    status: ComponentStatus
    issues: List[str]
    recommendations: List[str]
    metrics: Dict[str, Any]
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


class MCPDatabaseAuditor:
    """Comprehensive auditor for MCP and database infrastructure"""
    
    def __init__(self):
        self.results: List[AuditResult] = []
        self.start_time = time.time()
        
    async def run_full_audit(self) -> Dict[str, Any]:
        """Run comprehensive audit of all components"""
        print("🔍 Starting Comprehensive MCP & Database Audit...")
        print("=" * 80)
        
        # Phase 1: MCP Server Connections
        print("\n📡 Phase 1: MCP Server Connection Audit")
        await self.audit_mcp_servers()
        
        # Phase 2: Database Architecture
        print("\n🗄️ Phase 2: Database Architecture Review")
        await self.audit_database_architecture()
        
        # Phase 3: Memory Management
        print("\n🧠 Phase 3: Memory Management Analysis")
        await self.audit_memory_management()
        
        # Phase 4: Performance Optimization
        print("\n⚡ Phase 4: Performance Optimization Check")
        await self.audit_performance()
        
        # Phase 5: Error Detection
        print("\n🐛 Phase 5: Error Detection & Resolution")
        await self.detect_and_fix_errors()
        
        # Phase 6: Generate Report
        print("\n📊 Phase 6: Generating Comprehensive Report")
        report = self.generate_report()
        
        # Save report
        report_path = f"mcp_database_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n✅ Audit complete! Report saved to: {report_path}")
        return report
    
    async def audit_mcp_servers(self):
        """Audit all MCP server connections"""
        print("  Checking MCP server configurations...")
        
        # Load MCP configuration
        config_path = Path("claude_mcp_config.json")
        if not config_path.exists():
            self.results.append(AuditResult(
                component="MCP Configuration",
                status=ComponentStatus.CRITICAL,
                issues=["MCP configuration file not found"],
                recommendations=["Create claude_mcp_config.json with server definitions"],
                metrics={}
            ))
            return
        
        with open(config_path) as f:
            mcp_config = json.load(f)
        
        servers = mcp_config.get("mcp_servers", {})
        
        for server_name, server_config in servers.items():
            print(f"  - Checking {server_name}...")
            issues = []
            recommendations = []
            metrics = {}
            
            # Check endpoint accessibility
            endpoint = server_config.get("endpoint", "")
            if not endpoint:
                issues.append("No endpoint configured")
            else:
                # Try to connect
                import aiohttp
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"{endpoint}/health", timeout=5) as resp:
                            if resp.status == 200:
                                metrics["health_check"] = "passed"
                            else:
                                issues.append(f"Health check failed with status {resp.status}")
                except Exception as e:
                    issues.append(f"Connection failed: {str(e)}")
                    recommendations.append(f"Ensure {server_name} server is running on {endpoint}")
            
            # Check capabilities
            capabilities = server_config.get("capabilities", [])
            if not capabilities:
                issues.append("No capabilities defined")
                recommendations.append("Define server capabilities for proper routing")
            
            metrics["capabilities_count"] = len(capabilities)
            metrics["priority"] = server_config.get("priority", 0)
            
            status = ComponentStatus.HEALTHY if not issues else (
                ComponentStatus.CRITICAL if len(issues) > 1 else ComponentStatus.DEGRADED
            )
            
            self.results.append(AuditResult(
                component=f"MCP Server: {server_name}",
                status=status,
                issues=issues,
                recommendations=recommendations,
                metrics=metrics
            ))
    
    async def audit_database_architecture(self):
        """Audit PostgreSQL, Redis, and Weaviate configurations"""
        
        # PostgreSQL Audit
        await self._audit_postgresql()
        
        # Redis Audit
        await self._audit_redis()
        
        # Weaviate Audit
        await self._audit_weaviate()
        
        # Integration Audit
        await self._audit_database_integration()
    
    async def _audit_postgresql(self):
        """Audit PostgreSQL configuration and performance"""
        print("  - Auditing PostgreSQL...")
        issues = []
        recommendations = []
        metrics = {}
        
        try:
            # Connect to PostgreSQL
            conn = await asyncpg.connect(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", "5432")),
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "postgres"),
                database=os.getenv("POSTGRES_DB", "conductor")
            )
            
            # Check version
            version = await conn.fetchval("SELECT version()")
            metrics["version"] = version
            
            # Check connection pool settings
            pool_size = await conn.fetchval("SHOW max_connections")
            metrics["max_connections"] = pool_size
            
            # Check database size
            db_size = await conn.fetchval("""
                SELECT pg_database_size(current_database())
            """)
            metrics["database_size_mb"] = db_size / 1024 / 1024
            
            # Check table statistics
            table_stats = await conn.fetch("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    n_live_tup as row_count
                FROM pg_stat_user_tables
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 10
            """)
            metrics["largest_tables"] = [dict(row) for row in table_stats]
            
            # Check for missing indexes
            missing_indexes = await conn.fetch("""
                SELECT 
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    correlation
                FROM pg_stats
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                AND n_distinct > 100
                AND correlation < 0.1
                ORDER BY n_distinct DESC
                LIMIT 5
            """)
            
            if missing_indexes:
                issues.append(f"Found {len(missing_indexes)} columns that may benefit from indexes")
                recommendations.append("Consider adding indexes to frequently queried columns")
            
            # Check query performance
            slow_queries = await conn.fetch("""
                SELECT 
                    query,
                    calls,
                    mean_exec_time,
                    total_exec_time
                FROM pg_stat_statements
                WHERE mean_exec_time > 100
                ORDER BY mean_exec_time DESC
                LIMIT 5
            """)
            
            if slow_queries:
                issues.append(f"Found {len(slow_queries)} slow queries")
                recommendations.append("Optimize slow queries or add appropriate indexes")
                metrics["slow_queries"] = [dict(row) for row in slow_queries]
            
            await conn.close()
            
            status = ComponentStatus.HEALTHY if not issues else ComponentStatus.DEGRADED
            
        except Exception as e:
            issues.append(f"PostgreSQL connection failed: {str(e)}")
            recommendations.append("Ensure PostgreSQL is running and accessible")
            status = ComponentStatus.CRITICAL
        
        self.results.append(AuditResult(
            component="PostgreSQL",
            status=status,
            issues=issues,
            recommendations=recommendations,
            metrics=metrics
        ))
    
    async def _audit_redis(self):
        """Audit Redis configuration and performance"""
        print("  - Auditing Redis...")
        issues = []
        recommendations = []
        metrics = {}
        
        try:
            # Use resilient client if available
            if ResilientRedisClient:
                client = ResilientRedisClient()
                health = await redis_health_check()
                metrics.update(health)
                
                if health.get("status") != "healthy":
                    issues.append("Redis health check failed")
                    
                # Check circuit breaker
                if health.get("metrics", {}).get("circuit_breaker_state") == "open":
                    issues.append("Circuit breaker is open - Redis experiencing failures")
                    recommendations.append("Check Redis logs and connection stability")
            else:
                # Fallback to standard Redis client
                client = redis.Redis(
                    host=os.getenv("REDIS_HOST", "localhost"),
                    port=int(os.getenv("REDIS_PORT", "6379")),
                    decode_responses=True
                )
            
            # Get Redis info
            info = client.info()
            metrics["version"] = info.get("redis_version")
            metrics["connected_clients"] = info.get("connected_clients")
            metrics["used_memory_human"] = info.get("used_memory_human")
            metrics["used_memory_peak_human"] = info.get("used_memory_peak_human")
            
            # Check memory usage
            memory_usage_percent = (
                info.get("used_memory", 0) / info.get("maxmemory", 1) * 100
                if info.get("maxmemory", 0) > 0 else 0
            )
            
            if memory_usage_percent > 80:
                issues.append(f"High memory usage: {memory_usage_percent:.1f}%")
                recommendations.append("Consider increasing maxmemory or implementing eviction policies")
            
            # Check persistence
            aof_enabled = info.get("aof_enabled", 0)
            rdb_last_save = info.get("rdb_last_save_time", 0)
            
            if not aof_enabled and time.time() - rdb_last_save > 3600:
                issues.append("No recent persistence snapshot")
                recommendations.append("Enable AOF or configure more frequent RDB snapshots")
            
            # Check replication
            role = info.get("role")
            if role == "master":
                connected_slaves = info.get("connected_slaves", 0)
                if connected_slaves == 0:
                    recommendations.append("Consider setting up Redis replication for high availability")
            
            # Performance metrics
            metrics["ops_per_sec"] = info.get("instantaneous_ops_per_sec")
            metrics["keyspace_hits"] = info.get("keyspace_hits", 0)
            metrics["keyspace_misses"] = info.get("keyspace_misses", 0)
            
            hit_rate = (
                metrics["keyspace_hits"] / (metrics["keyspace_hits"] + metrics["keyspace_misses"]) * 100
                if (metrics["keyspace_hits"] + metrics["keyspace_misses"]) > 0 else 0
            )
            metrics["cache_hit_rate"] = f"{hit_rate:.1f}%"
            
            if hit_rate < 80 and metrics["keyspace_hits"] > 1000:
                issues.append(f"Low cache hit rate: {hit_rate:.1f}%")
                recommendations.append("Review caching strategy and TTL settings")
            
            status = ComponentStatus.HEALTHY if not issues else ComponentStatus.DEGRADED
            
        except Exception as e:
            issues.append(f"Redis connection failed: {str(e)}")
            recommendations.append("Ensure Redis is running and accessible")
            status = ComponentStatus.CRITICAL
        
        self.results.append(AuditResult(
            component="Redis",
            status=status,
            issues=issues,
            recommendations=recommendations,
            metrics=metrics
        ))
    
    async def _audit_weaviate(self):
        """Audit Weaviate configuration and performance"""
        print("  - Auditing Weaviate...")
        issues = []
        recommendations = []
        metrics = {}
        
        try:
            # Connect to Weaviate
            client = weaviate.Client(
                url=f"http://{os.getenv('WEAVIATE_HOST', 'localhost')}:{os.getenv('WEAVIATE_PORT', '8080')}"
            )
            
            # Check if Weaviate is ready
            if not client.is_ready():
                issues.append("Weaviate is not ready")
                status = ComponentStatus.CRITICAL
            else:
                # Get schema
                schema = client.schema.get()
                metrics["classes_count"] = len(schema.get("classes", []))
                
                # Check each class
                for class_def in schema.get("classes", []):
                    class_name = class_def.get("class")
                    
                    # Get object count
                    result = client.query.aggregate(class_name).with_meta_count().do()
                    count = result.get("data", {}).get("Aggregate", {}).get(class_name, [{}])[0].get("meta", {}).get("count", 0)
                    
                    metrics[f"{class_name}_count"] = count
                    
                    # Check vectorizer
                    vectorizer = class_def.get("vectorizer")
                    if not vectorizer:
                        issues.append(f"No vectorizer configured for class {class_name}")
                        recommendations.append(f"Configure appropriate vectorizer for {class_name}")
                
                # Check modules
                meta = client.get_meta()
                modules = meta.get("modules", {})
                metrics["enabled_modules"] = list(modules.keys())
                
                if "text2vec-openai" in modules and not os.getenv("OPENAI_API_KEY"):
                    issues.append("OpenAI vectorizer enabled but OPENAI_API_KEY not set")
                    recommendations.append("Set OPENAI_API_KEY environment variable")
                
                status = ComponentStatus.HEALTHY if not issues else ComponentStatus.DEGRADED
                
        except Exception as e:
            issues.append(f"Weaviate connection failed: {str(e)}")
            recommendations.append("Ensure Weaviate is running and accessible")
            status = ComponentStatus.CRITICAL
        
        self.results.append(AuditResult(
            component="Weaviate",
            status=status,
            issues=issues,
            recommendations=recommendations,
            metrics=metrics
        ))
    
    async def _audit_database_integration(self):
        """Audit integration between databases"""
        print("  - Auditing database integration...")
        issues = []
        recommendations = []
        metrics = {}
        
        if UnifiedDatabase:
            try:
                # Test unified database
                db = UnifiedDatabase()
                await db.connect()
                
                # Check health
                health = await db.health_check()
                metrics["health_status"] = health
                
                if not health.get("unified"):
                    issues.append("Unified database health check failed")
                    if not health.get("postgresql"):
                        issues.append("PostgreSQL component unhealthy")
                    if not health.get("weaviate"):
                        issues.append("Weaviate component unhealthy")
                
                # Get metrics
                db_metrics = db.get_metrics()
                metrics.update(db_metrics)
                
                # Check error rates
                error_rate = db_metrics.get("error_rate", 0)
                if error_rate > 0.05:  # 5% error rate
                    issues.append(f"High error rate: {error_rate*100:.1f}%")
                    recommendations.append("Investigate database errors and connection stability")
                
                await db.disconnect()
                
            except Exception as e:
                issues.append(f"Unified database test failed: {str(e)}")
                recommendations.append("Check UnifiedDatabase configuration and dependencies")
        else:
            issues.append("UnifiedDatabase not available")
            recommendations.append("Ensure shared.database module is properly installed")
        
        status = ComponentStatus.HEALTHY if not issues else ComponentStatus.DEGRADED
        
        self.results.append(AuditResult(
            component="Database Integration",
            status=status,
            issues=issues,
            recommendations=recommendations,
            metrics=metrics
        ))
    
    async def audit_memory_management(self):
        """Audit memory management and caching strategies"""
        print("  - Analyzing memory management...")
        issues = []
        recommendations = []
        metrics = {}
        
        # System memory
        memory = psutil.virtual_memory()
        metrics["system_memory_percent"] = memory.percent
        metrics["system_memory_available_gb"] = memory.available / 1024 / 1024 / 1024
        
        if memory.percent > 80:
            issues.append(f"High system memory usage: {memory.percent}%")
            recommendations.append("Consider scaling up server resources")
        
        # Process memory
        process = psutil.Process()
        process_memory = process.memory_info()
        metrics["process_memory_mb"] = process_memory.rss / 1024 / 1024
        
        # Check for memory leaks (simplified)
        if hasattr(self, '_last_memory_check'):
            memory_growth = metrics["process_memory_mb"] - self._last_memory_check
            if memory_growth > 100:  # 100MB growth
                issues.append(f"Potential memory leak detected: {memory_growth:.1f}MB growth")
                recommendations.append("Profile application for memory leaks")
        
        self._last_memory_check = metrics["process_memory_mb"]
        
        # Caching analysis
        cache_files = list(Path(".").rglob("*cache*.py"))
        metrics["cache_implementations"] = len(cache_files)
        
        if metrics["cache_implementations"] < 3:
            recommendations.append("Consider implementing more caching layers for better performance")
        
        status = ComponentStatus.HEALTHY if not issues else ComponentStatus.DEGRADED
        
        self.results.append(AuditResult(
            component="Memory Management",
            status=status,
            issues=issues,
            recommendations=recommendations,
            metrics=metrics
        ))
    
    async def audit_performance(self):
        """Audit system performance and optimization opportunities"""
        print("  - Checking performance optimizations...")
        issues = []
        recommendations = []
        metrics = {}
        
        # Connection pooling check
        pool_configs = []
        
        # Check PostgreSQL pooling
        if Path("shared/database/unified_database.py").exists():
            with open("shared/database/unified_database.py") as f:
                content = f.read()
                if "min_size=" in content and "max_size=" in content:
                    pool_configs.append("PostgreSQL")
                else:
                    issues.append("PostgreSQL connection pooling not properly configured")
                    recommendations.append("Configure asyncpg connection pool with min_size and max_size")
        
        # Check Redis pooling
        if Path("core/redis/resilient_client.py").exists():
            pool_configs.append("Redis")
        
        metrics["connection_pooling"] = pool_configs
        
        # Check for async implementations
        async_files = list(Path(".").rglob("*async*.py"))
        metrics["async_implementations"] = len(async_files)
        
        if metrics["async_implementations"] < 10:
            recommendations.append("Consider implementing more async operations for better concurrency")
        
        # Check for batch operations
        batch_operations = []
        for file_path in Path("mcp_server").rglob("*.py"):
            try:
                with open(file_path) as f:
                    content = f.read()
                    if "batch" in content.lower() or "bulk" in content.lower():
                        batch_operations.append(str(file_path))
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                pass
        
        metrics["batch_operations"] = len(batch_operations)
        
        if metrics["batch_operations"] < 5:
            recommendations.append("Implement more batch operations to reduce database round trips")
        
        status = ComponentStatus.HEALTHY if not issues else ComponentStatus.DEGRADED
        
        self.results.append(AuditResult(
            component="Performance Optimization",
            status=status,
            issues=issues,
            recommendations=recommendations,
            metrics=metrics
        ))
    
    async def detect_and_fix_errors(self):
        """Detect and attempt to fix common errors"""
        print("  - Detecting and resolving errors...")
        issues = []
        recommendations = []
        metrics = {}
        fixed_count = 0
        
        # Check for import errors
        import_errors = []
        for file_path in Path(".").rglob("*.py"):
            if "test" in str(file_path) or "__pycache__" in str(file_path):
                continue
                
            try:
                with open(file_path) as f:
                    content = f.read()
                    # Check for common import issues
                    if "from shared.database import" in content:
                        # Verify the import exists
                        module_path = Path("shared/database/__init__.py")
                        if not module_path.exists():
                            import_errors.append(str(file_path))
            except:
                pass
        
        if import_errors:
            issues.append(f"Found {len(import_errors)} files with potential import errors")
            recommendations.append("Fix import paths or ensure modules exist")
            metrics["import_errors"] = import_errors[:5]  # First 5
        
        # Check for configuration errors
        env_vars = [
            "POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_USER", "POSTGRES_PASSWORD",
            "REDIS_HOST", "REDIS_PORT", "WEAVIATE_HOST", "WEAVIATE_PORT",
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY"
        ]
        
        missing_env_vars = [var for var in env_vars if not os.getenv(var)]
        if missing_env_vars:
            issues.append(f"Missing {len(missing_env_vars)} environment variables")
            recommendations.append(f"Set environment variables: {', '.join(missing_env_vars[:5])}")
            metrics["missing_env_vars"] = missing_env_vars
        
        # Check for connection timeouts
        timeout_configs = []
        for config_file in ["docker-compose.local.yml", "config/orchestrator_config.json"]:
            if Path(config_file).exists():
                with open(config_file) as f:
                    content = f.read()
                    if "timeout" not in content.lower():
                        timeout_configs.append(config_file)
        
        if timeout_configs:
            issues.append("Missing timeout configurations")
            recommendations.append("Add appropriate timeout settings to prevent hanging connections")
        
        metrics["errors_fixed"] = fixed_count
        
        status = ComponentStatus.HEALTHY if not issues else ComponentStatus.DEGRADED
        
        self.results.append(AuditResult(
            component="Error Detection",
            status=status,
            issues=issues,
            recommendations=recommendations,
            metrics=metrics
        ))
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive audit report"""
        # Calculate overall health
        status_counts = {
            ComponentStatus.HEALTHY: 0,
            ComponentStatus.DEGRADED: 0,
            ComponentStatus.CRITICAL: 0,
            ComponentStatus.UNKNOWN: 0
        }
        
        for result in self.results:
            status_counts[result.status] += 1
        
        overall_status = ComponentStatus.HEALTHY
        if status_counts[ComponentStatus.CRITICAL] > 0:
            overall_status = ComponentStatus.CRITICAL
        elif status_counts[ComponentStatus.DEGRADED] > 2:
            overall_status = ComponentStatus.DEGRADED
        
        # Compile all issues and recommendations
        all_issues = []
        all_recommendations = []
        
        for result in self.results:
            all_issues.extend(result.issues)
            all_recommendations.extend(result.recommendations)
        
        # Remove duplicates
        all_recommendations = list(set(all_recommendations))
        
        # Priority recommendations
        priority_recommendations = [
            rec for rec in all_recommendations
            if any(keyword in rec.lower() for keyword in ["critical", "failed", "error", "fix"])
        ]
        
        report = {
            "audit_timestamp": datetime.utcnow().isoformat(),
            "duration_seconds": time.time() - self.start_time,
            "overall_status": overall_status.value,
            "status_summary": {k.value: v for k, v in status_counts.items()},
            "total_issues": len(all_issues),
            "total_recommendations": len(all_recommendations),
            "priority_recommendations": priority_recommendations,
            "component_results": [asdict(result) for result in self.results],
            "executive_summary": self._generate_executive_summary(overall_status, all_issues, all_recommendations)
        }
        
        return report
    
    def _generate_executive_summary(
        self,
        status: ComponentStatus,
        issues: List[str],
        recommendations: List[str]
    ) -> str:
        """Generate executive summary of the audit"""
        summary = f"System Status: {status.value.upper()}\n\n"
        
        if status == ComponentStatus.HEALTHY:
            summary += "✅ All systems are operating within normal parameters.\n"
        elif status == ComponentStatus.DEGRADED:
            summary += "⚠️ System is operational but with degraded performance.\n"
        else:
            summary += "🚨 Critical issues detected requiring immediate attention.\n"
        
        summary += f"\nKey Findings:\n"
        summary += f"- Total Issues: {len(issues)}\n"
        summary += f"- Components Audited: {len(self.results)}\n"
        summary += f"- Recommendations: {len(recommendations)}\n"
        
        if issues:
            summary += f"\nTop Issues:\n"
            for issue in issues[:3]:
                summary += f"- {issue}\n"
        
        if recommendations:
            summary += f"\nTop Recommendations:\n"
            for rec in recommendations[:3]:
                summary += f"- {rec}\n"
        
        return summary


async def main():
    """Run the comprehensive audit"""
    auditor = MCPDatabaseAuditor()
    report = await auditor.run_full_audit()
    
    # Print summary
    print("\n" + "=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)
    print(report["executive_summary"])
    
    # Print critical issues
    critical_components = [
        result for result in auditor.results
        if result.status == ComponentStatus.CRITICAL
    ]
    
    if critical_components:
        print("\n🚨 CRITICAL ISSUES:")
        for component in critical_components:
            print(f"\n{component.component}:")
            for issue in component.issues:
                print(f"  ❌ {issue}")
            for rec in component.recommendations:
                print(f"  💡 {rec}")
    
    print("\n✅ Audit complete! Check the generated report for full details.")


if __name__ == "__main__":
    asyncio.run(main())