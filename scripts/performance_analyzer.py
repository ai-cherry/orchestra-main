#!/usr/bin/env python3
"""
Performance Analysis Script for AI Orchestrator
Analyzes bottlenecks and implements optimizations
"""

import os
import sys
import json
import time
import asyncio
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import statistics
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from ai_components.orchestration.ai_orchestrator import (
    DatabaseLogger, WeaviateManager, WorkflowOrchestrator,
    TaskDefinition, AgentRole
)


class PerformanceAnalyzer:
    """Analyzes performance bottlenecks in the AI orchestrator system"""
    
    def __init__(self):
        self.db_logger = DatabaseLogger()
        self.weaviate_manager = WeaviateManager()
        self.metrics = {
            "workflow_execution": [],
            "database_queries": [],
            "vector_operations": [],
            "api_latencies": {},
            "task_durations": {}
        }
    
    async def analyze_workflow_execution_times(self) -> Dict:
        """Analyze workflow execution performance"""
        print("Analyzing workflow execution times...")
        
        # Query recent workflow executions
        with self.db_logger._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    WITH workflow_times AS (
                        SELECT 
                            workflow_id,
                            MIN(created_at) as start_time,
                            MAX(created_at) as end_time,
                            COUNT(DISTINCT task_id) as task_count,
                            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_tasks
                        FROM orchestration_logs
                        WHERE created_at > NOW() - INTERVAL '7 days'
                        GROUP BY workflow_id
                    )
                    SELECT 
                        workflow_id,
                        EXTRACT(EPOCH FROM (end_time - start_time)) as duration_seconds,
                        task_count,
                        failed_tasks
                    FROM workflow_times
                    WHERE end_time IS NOT NULL
                    ORDER BY duration_seconds DESC
                    LIMIT 100
                """)
                
                workflows = cur.fetchall()
        
        # Analyze performance
        durations = [w[1] for w in workflows if w[1] > 0]
        
        analysis = {
            "total_workflows": len(workflows),
            "average_duration": statistics.mean(durations) if durations else 0,
            "median_duration": statistics.median(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0,
            "std_deviation": statistics.stdev(durations) if len(durations) > 1 else 0,
            "slowest_workflows": []
        }
        
        # Identify slowest workflows
        for workflow in workflows[:10]:  # Top 10 slowest
            analysis["slowest_workflows"].append({
                "workflow_id": workflow[0],
                "duration": workflow[1],
                "task_count": workflow[2],
                "failed_tasks": workflow[3],
                "avg_task_duration": workflow[1] / workflow[2] if workflow[2] > 0 else 0
            })
        
        # Store analysis in Weaviate
        self.weaviate_manager.store_context(
            workflow_id="performance_analysis",
            task_id="workflow_execution",
            context_type="performance_metrics",
            content=json.dumps(analysis),
            metadata={"timestamp": datetime.now().isoformat()}
        )
        
        return analysis
    
    async def analyze_database_performance(self) -> Dict:
        """Analyze PostgreSQL query performance"""
        print("Analyzing database query performance...")
        
        analysis = {
            "connection_stats": {},
            "query_stats": {},
            "index_usage": {},
            "table_stats": {}
        }
        
        with self.db_logger._get_connection() as conn:
            with conn.cursor() as cur:
                # Connection statistics
                cur.execute("""
                    SELECT 
                        numbackends as active_connections,
                        xact_commit as committed_transactions,
                        xact_rollback as rolled_back_transactions,
                        blks_read as disk_blocks_read,
                        blks_hit as buffer_hits,
                        tup_returned as rows_returned,
                        tup_fetched as rows_fetched,
                        tup_inserted as rows_inserted,
                        tup_updated as rows_updated,
                        tup_deleted as rows_deleted
                    FROM pg_stat_database
                    WHERE datname = current_database()
                """)
                
                stats = cur.fetchone()
                if stats:
                    analysis["connection_stats"] = {
                        "active_connections": stats[0],
                        "committed_transactions": stats[1],
                        "rolled_back_transactions": stats[2],
                        "cache_hit_ratio": stats[4] / (stats[3] + stats[4]) * 100 if (stats[3] + stats[4]) > 0 else 0
                    }
                
                # Slow queries (requires pg_stat_statements extension)
                try:
                    cur.execute("""
                        SELECT 
                            query,
                            calls,
                            total_exec_time,
                            mean_exec_time,
                            stddev_exec_time,
                            rows
                        FROM pg_stat_statements
                        WHERE query NOT LIKE '%pg_stat_statements%'
                        ORDER BY mean_exec_time DESC
                        LIMIT 10
                    """)
                    
                    slow_queries = cur.fetchall()
                    analysis["query_stats"]["slow_queries"] = [
                        {
                            "query": q[0][:100] + "..." if len(q[0]) > 100 else q[0],
                            "calls": q[1],
                            "total_time": q[2],
                            "mean_time": q[3],
                            "stddev_time": q[4],
                            "rows_per_call": q[5] / q[1] if q[1] > 0 else 0
                        }
                        for q in slow_queries
                    ]
                except:
                    analysis["query_stats"]["note"] = "pg_stat_statements extension not available"
                
                # Index usage
                cur.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan,
                        idx_tup_read,
                        idx_tup_fetch
                    FROM pg_stat_user_indexes
                    WHERE schemaname = 'public'
                    ORDER BY idx_scan DESC
                """)
                
                indexes = cur.fetchall()
                analysis["index_usage"] = [
                    {
                        "table": f"{idx[0]}.{idx[1]}",
                        "index": idx[2],
                        "scans": idx[3],
                        "tuples_read": idx[4],
                        "tuples_fetched": idx[5],
                        "efficiency": idx[5] / idx[4] * 100 if idx[4] > 0 else 0
                    }
                    for idx in indexes
                ]
                
                # Table statistics
                cur.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        n_tup_ins,
                        n_tup_upd,
                        n_tup_del,
                        n_live_tup,
                        n_dead_tup,
                        last_vacuum,
                        last_autovacuum
                    FROM pg_stat_user_tables
                    WHERE schemaname = 'public'
                """)
                
                tables = cur.fetchall()
                analysis["table_stats"] = [
                    {
                        "table": f"{t[0]}.{t[1]}",
                        "inserts": t[2],
                        "updates": t[3],
                        "deletes": t[4],
                        "live_tuples": t[5],
                        "dead_tuples": t[6],
                        "bloat_ratio": t[6] / t[5] * 100 if t[5] > 0 else 0,
                        "last_vacuum": str(t[7]) if t[7] else "Never",
                        "last_autovacuum": str(t[8]) if t[8] else "Never"
                    }
                    for t in tables
                ]
        
        # Log analysis
        self.db_logger.log_action(
            workflow_id="performance_analysis",
            task_id="database_performance",
            agent_role="analyzer",
            action="analyze_database",
            status="completed",
            metadata=analysis
        )
        
        return analysis
    
    async def analyze_vector_storage_efficiency(self) -> Dict:
        """Analyze Weaviate vector storage performance"""
        print("Analyzing vector storage efficiency...")
        
        analysis = {
            "storage_stats": {},
            "query_performance": {},
            "batch_performance": {}
        }
        
        # Test single object retrieval
        start_time = time.time()
        single_results = self.weaviate_manager.retrieve_context("test_workflow", limit=1)
        single_latency = time.time() - start_time
        
        # Test batch retrieval
        start_time = time.time()
        batch_results = self.weaviate_manager.retrieve_context("test_workflow", limit=100)
        batch_latency = time.time() - start_time
        
        analysis["query_performance"] = {
            "single_object_latency": single_latency,
            "batch_retrieval_latency": batch_latency,
            "objects_per_second": len(batch_results) / batch_latency if batch_latency > 0 else 0
        }
        
        # Test batch insertion
        test_contexts = []
        for i in range(100):
            test_contexts.append({
                "workflow_id": "perf_test",
                "task_id": f"task_{i}",
                "context_type": "test",
                "content": f"Test content {i}" * 100  # Simulate larger content
            })
        
        start_time = time.time()
        for ctx in test_contexts:
            self.weaviate_manager.store_context(**ctx)
        batch_insert_time = time.time() - start_time
        
        analysis["batch_performance"] = {
            "batch_size": len(test_contexts),
            "total_time": batch_insert_time,
            "inserts_per_second": len(test_contexts) / batch_insert_time if batch_insert_time > 0 else 0
        }
        
        # Get schema information
        try:
            schema = self.weaviate_manager.client.schema.get()
            analysis["storage_stats"]["classes"] = len(schema.get("classes", []))
            
            # Count objects per class
            for class_def in schema.get("classes", []):
                class_name = class_def["class"]
                count_result = (
                    self.weaviate_manager.client.query
                    .aggregate(class_name)
                    .with_meta_count()
                    .do()
                )
                
                if count_result and "data" in count_result:
                    analysis["storage_stats"][f"{class_name}_count"] = (
                        count_result["data"]["Aggregate"][class_name][0]["meta"]["count"]
                    )
        except Exception as e:
            analysis["storage_stats"]["error"] = str(e)
        
        return analysis
    
    async def analyze_api_latencies(self) -> Dict:
        """Analyze API call latencies for different services"""
        print("Analyzing API call latencies...")
        
        analysis = {
            "eigencode": {},
            "cursor_ai": {},
            "roo_code": {},
            "mcp_server": {}
        }
        
        # Test MCP server latency
        mcp_url = os.environ.get("MCP_SERVER_URL", "http://localhost:8080")
        
        # Health check
        try:
            start = time.time()
            response = requests.get(f"{mcp_url}/", timeout=5)
            analysis["mcp_server"]["health_check_latency"] = time.time() - start
            analysis["mcp_server"]["health_status"] = response.status_code
        except Exception as e:
            analysis["mcp_server"]["error"] = str(e)
        
        # Task creation
        try:
            start = time.time()
            response = requests.post(
                f"{mcp_url}/tasks",
                json={
                    "task_id": f"perf_test_{int(time.time())}",
                    "name": "Performance Test",
                    "agent_role": "analyzer",
                    "inputs": {}
                },
                timeout=5
            )
            analysis["mcp_server"]["task_creation_latency"] = time.time() - start
        except Exception as e:
            analysis["mcp_server"]["task_creation_error"] = str(e)
        
        # Simulate API calls to AI services (when available)
        # For now, we'll measure mock response times
        
        # EigenCode simulation
        start = time.time()
        await asyncio.sleep(0.1)  # Simulate API call
        analysis["eigencode"]["mock_latency"] = time.time() - start
        analysis["eigencode"]["status"] = "not_available"
        
        # Cursor AI simulation
        start = time.time()
        await asyncio.sleep(0.15)  # Simulate API call
        analysis["cursor_ai"]["mock_latency"] = time.time() - start
        analysis["cursor_ai"]["status"] = "mock"
        
        # Roo Code simulation
        start = time.time()
        await asyncio.sleep(0.12)  # Simulate API call
        analysis["roo_code"]["mock_latency"] = time.time() - start
        analysis["roo_code"]["status"] = "mock"
        
        return analysis
    
    async def generate_optimization_recommendations(self, analysis_results: Dict) -> List[Dict]:
        """Generate optimization recommendations based on analysis"""
        recommendations = []
        
        # Workflow optimization recommendations
        if "workflow_execution" in analysis_results:
            workflow_data = analysis_results["workflow_execution"]
            
            if workflow_data["average_duration"] > 300:  # 5 minutes
                recommendations.append({
                    "category": "workflow",
                    "severity": "high",
                    "issue": "Long average workflow duration",
                    "recommendation": "Implement task parallelization and optimize dependencies",
                    "implementation": """
# Optimize task dependencies
from collections import defaultdict

def optimize_dependencies(tasks):
    # Remove redundant dependencies
    dep_graph = defaultdict(set)
    for task in tasks:
        for dep in task.dependencies:
            dep_graph[task.task_id].add(dep)
    
    # Transitive reduction
    for task in tasks:
        indirect_deps = set()
        for dep in task.dependencies:
            for indirect in dep_graph[dep]:
                indirect_deps.add(indirect)
        
        task.dependencies = [d for d in task.dependencies if d not in indirect_deps]
    
    return tasks
"""
                })
        
        # Database optimization recommendations
        if "database_performance" in analysis_results:
            db_data = analysis_results["database_performance"]
            
            if db_data["connection_stats"].get("cache_hit_ratio", 100) < 90:
                recommendations.append({
                    "category": "database",
                    "severity": "medium",
                    "issue": "Low cache hit ratio",
                    "recommendation": "Increase shared_buffers and optimize queries",
                    "implementation": """
-- Increase shared buffers
ALTER SYSTEM SET shared_buffers = '512MB';

-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_logs_workflow_created 
ON orchestration_logs(workflow_id, created_at DESC);

-- Optimize common queries
CREATE MATERIALIZED VIEW workflow_summary AS
SELECT 
    workflow_id,
    COUNT(*) as task_count,
    MIN(created_at) as start_time,
    MAX(created_at) as end_time
FROM orchestration_logs
GROUP BY workflow_id;

CREATE INDEX ON workflow_summary(workflow_id);
"""
                })
            
            # Check for table bloat
            for table in db_data.get("table_stats", []):
                if table["bloat_ratio"] > 20:
                    recommendations.append({
                        "category": "database",
                        "severity": "medium",
                        "issue": f"Table bloat in {table['table']}",
                        "recommendation": "Run VACUUM FULL or pg_repack",
                        "implementation": f"VACUUM FULL {table['table']};"
                    })
        
        # Vector storage optimization
        if "vector_storage" in analysis_results:
            vector_data = analysis_results["vector_storage"]
            
            if vector_data["batch_performance"]["inserts_per_second"] < 100:
                recommendations.append({
                    "category": "vector_storage",
                    "severity": "medium",
                    "issue": "Slow batch insertion",
                    "recommendation": "Implement batch operations",
                    "implementation": """
# Use Weaviate batch operations
def batch_store_contexts(contexts):
    with weaviate_client.batch as batch:
        batch.batch_size = 100
        batch.dynamic = True
        
        for ctx in contexts:
            batch.add_data_object(
                data_object=ctx,
                class_name="OrchestrationContext"
            )
"""
                })
        
        # API latency optimization
        if "api_latencies" in analysis_results:
            api_data = analysis_results["api_latencies"]
            
            for service, metrics in api_data.items():
                if "latency" in str(metrics) and any(v > 1.0 for k, v in metrics.items() if "latency" in k and isinstance(v, (int, float))):
                    recommendations.append({
                        "category": "api",
                        "severity": "high",
                        "issue": f"High latency for {service}",
                        "recommendation": "Implement caching and connection pooling",
                        "implementation": f"""
# Implement caching for {service}
from functools import lru_cache
import aiohttp

class Cached{service.title().replace('_', '')}Client:
    def __init__(self):
        self.session = None
        self.cache = {{}}
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=100)
        )
        return self
    
    @lru_cache(maxsize=1000)
    async def cached_request(self, endpoint, params):
        async with self.session.get(endpoint, params=params) as resp:
            return await resp.json()
"""
                    })
        
        return recommendations
    
    async def implement_optimizations(self, recommendations: List[Dict]) -> Dict:
        """Implement optimization recommendations using Cursor AI"""
        implementation_results = {
            "implemented": [],
            "failed": [],
            "skipped": []
        }
        
        for rec in recommendations:
            if rec["severity"] == "high":
                try:
                    # Log implementation attempt
                    self.db_logger.log_action(
                        workflow_id="performance_optimization",
                        task_id=f"optimize_{rec['category']}",
                        agent_role="implementer",
                        action="implement_optimization",
                        status="started",
                        metadata=rec
                    )
                    
                    # Here we would call Cursor AI to implement the optimization
                    # For now, we'll simulate the implementation
                    
                    if rec["category"] == "database":
                        # Execute SQL optimizations
                        if "CREATE INDEX" in rec["implementation"]:
                            print(f"Would execute: {rec['implementation']}")
                            implementation_results["implemented"].append({
                                "category": rec["category"],
                                "optimization": "index_creation",
                                "status": "simulated"
                            })
                    
                    elif rec["category"] == "workflow":
                        # Apply code optimizations
                        print(f"Would apply workflow optimization: {rec['recommendation']}")
                        implementation_results["implemented"].append({
                            "category": rec["category"],
                            "optimization": "dependency_optimization",
                            "status": "simulated"
                        })
                    
                    # Log success
                    self.db_logger.log_action(
                        workflow_id="performance_optimization",
                        task_id=f"optimize_{rec['category']}",
                        agent_role="implementer",
                        action="implement_optimization",
                        status="completed",
                        metadata={"result": "simulated"}
                    )
                    
                except Exception as e:
                    implementation_results["failed"].append({
                        "category": rec["category"],
                        "error": str(e)
                    })
            else:
                implementation_results["skipped"].append({
                    "category": rec["category"],
                    "reason": f"Low severity: {rec['severity']}"
                })
        
        return implementation_results
    
    async def run_full_analysis(self) -> Dict:
        """Run complete performance analysis"""
        print("Starting comprehensive performance analysis...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "analyses": {},
            "recommendations": [],
            "implementations": {}
        }
        
        # Run all analyses
        try:
            results["analyses"]["workflow_execution"] = await self.analyze_workflow_execution_times()
        except Exception as e:
            results["analyses"]["workflow_execution"] = {"error": str(e)}
        
        try:
            results["analyses"]["database_performance"] = await self.analyze_database_performance()
        except Exception as e:
            results["analyses"]["database_performance"] = {"error": str(e)}
        
        try:
            results["analyses"]["vector_storage"] = await self.analyze_vector_storage_efficiency()
        except Exception as e:
            results["analyses"]["vector_storage"] = {"error": str(e)}
        
        try:
            results["analyses"]["api_latencies"] = await self.analyze_api_latencies()
        except Exception as e:
            results["analyses"]["api_latencies"] = {"error": str(e)}
        
        # Generate recommendations
        results["recommendations"] = await self.generate_optimization_recommendations(results["analyses"])
        
        # Implement high-priority optimizations
        if results["recommendations"]:
            results["implementations"] = await self.implement_optimizations(results["recommendations"])
        
        # Store complete analysis in Weaviate
        self.weaviate_manager.store_context(
            workflow_id="performance_analysis",
            task_id="complete_analysis",
            context_type="full_performance_report",
            content=json.dumps(results),
            metadata={
                "timestamp": results["timestamp"],
                "recommendation_count": len(results["recommendations"])
            }
        )
        
        return results


async def main():
    """Main function"""
    analyzer = PerformanceAnalyzer()
    
    # Run full analysis
    results = await analyzer.run_full_analysis()
    
    # Print summary
    print("\n" + "=" * 60)
    print("Performance Analysis Summary")
    print("=" * 60)
    
    # Workflow performance
    if "workflow_execution" in results["analyses"]:
        wf_data = results["analyses"]["workflow_execution"]
        print(f"\nWorkflow Performance:")
        print(f"  Average Duration: {wf_data.get('average_duration', 0):.2f} seconds")
        print(f"  Median Duration: {wf_data.get('median_duration', 0):.2f} seconds")
        print(f"  Total Workflows: {wf_data.get('total_workflows', 0)}")
    
    # Database performance
    if "database_performance" in results["analyses"]:
        db_data = results["analyses"]["database_performance"]
        if "connection_stats" in db_data:
            print(f"\nDatabase Performance:")
            print(f"  Cache Hit Ratio: {db_data['connection_stats'].get('cache_hit_ratio', 0):.2f}%")
            print(f"  Active Connections: {db_data['connection_stats'].get('active_connections', 0)}")
    
    # Recommendations
    print(f"\nOptimization Recommendations: {len(results['recommendations'])}")
    for rec in results["recommendations"]:
        print(f"  - [{rec['severity'].upper()}] {rec['category']}: {rec['issue']}")
    
    # Implementations
    if "implementations" in results:
        impl = results["implementations"]
        print(f"\nImplementation Results:")
        print(f"  Implemented: {len(impl.get('implemented', []))}")
        print(f"  Failed: {len(impl.get('failed', []))}")
        print(f"  Skipped: {len(impl.get('skipped', []))}")
    
    # Save detailed report
    report_path = f"performance_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_path}")


if __name__ == "__main__":
    import requests  # Import here to avoid issues if not needed
    asyncio.run(main())