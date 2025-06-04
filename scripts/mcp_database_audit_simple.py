#!/usr/bin/env python3
"""
Simplified MCP Server and Database Architecture Audit
Performs analysis without external dependencies like psutil
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MCPDatabaseAuditor:
    """Simplified auditor for MCP and database infrastructure"""
    
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        
    async def run_audit(self):
        """Run simplified audit"""
        print("🔍 Starting MCP & Database Audit...")
        print("=" * 80)
        
        # Check MCP Configuration
        print("\n📡 Checking MCP Server Configuration...")
        self.check_mcp_config()
        
        # Check Database Configuration
        print("\n🗄️ Checking Database Configuration...")
        self.check_database_config()
        
        # Check Redis Configuration
        print("\n💾 Checking Redis Configuration...")
        self.check_redis_config()
        
        # Check Code Structure
        print("\n📂 Checking Code Structure...")
        self.check_code_structure()
        
        # Generate Report
        print("\n📊 Generating Report...")
        report = self.generate_report()
        
        # Save report
        report_path = f"mcp_audit_simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n✅ Audit complete! Report saved to: {report_path}")
        return report
    
    def check_mcp_config(self):
        """Check MCP server configuration"""
        issues = []
        recommendations = []
        
        # Check if MCP config exists
        config_path = Path("claude_mcp_config.json")
        if not config_path.exists():
            issues.append("MCP configuration file not found")
            recommendations.append("Create claude_mcp_config.json with server definitions")
        else:
            with open(config_path) as f:
                config = json.load(f)
                
            servers = config.get("mcp_servers", {})
            print(f"  Found {len(servers)} MCP servers configured")
            
            for server_name, server_config in servers.items():
                print(f"  - {server_name}: {server_config.get('endpoint', 'No endpoint')}")
                
                if not server_config.get("endpoint"):
                    issues.append(f"{server_name} has no endpoint configured")
                    
                if not server_config.get("capabilities"):
                    issues.append(f"{server_name} has no capabilities defined")
                    recommendations.append(f"Define capabilities for {server_name}")
        
        self.results.append({
            "component": "MCP Configuration",
            "issues": issues,
            "recommendations": recommendations,
            "status": "healthy" if not issues else "degraded"
        })
    
    def check_database_config(self):
        """Check database configuration files"""
        issues = []
        recommendations = []
        
        # Check docker-compose
        docker_compose_path = Path("docker-compose.local.yml")
        if docker_compose_path.exists():
            with open(docker_compose_path) as f:
                content = f.read()
                
            # Check PostgreSQL
            if "postgres:" in content:
                print("  ✓ PostgreSQL configured in docker-compose")
                if "POSTGRES_PASSWORD: postgres" in content:
                    issues.append("Using default PostgreSQL password")
                    recommendations.append("Change PostgreSQL password for production")
            else:
                issues.append("PostgreSQL not found in docker-compose")
                
            # Check Redis
            if "redis:" in content:
                print("  ✓ Redis configured in docker-compose")
            else:
                issues.append("Redis not found in docker-compose")
                
            # Check Weaviate
            if "weaviate:" in content:
                print("  ✓ Weaviate configured in docker-compose")
                if "AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'" in content:
                    issues.append("Weaviate anonymous access enabled")
                    recommendations.append("Configure Weaviate authentication for production")
            else:
                issues.append("Weaviate not found in docker-compose")
        else:
            issues.append("docker-compose.local.yml not found")
            recommendations.append("Create docker-compose configuration")
        
        # Check environment variables
        required_env_vars = [
            "POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_USER", "POSTGRES_PASSWORD",
            "REDIS_HOST", "REDIS_PORT", 
            "WEAVIATE_HOST", "WEAVIATE_PORT"
        ]
        
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            print(f"  ⚠️ Missing {len(missing_vars)} environment variables")
            issues.append(f"Missing environment variables: {', '.join(missing_vars[:5])}")
            recommendations.append("Set all required environment variables")
        
        self.results.append({
            "component": "Database Configuration",
            "issues": issues,
            "recommendations": recommendations,
            "status": "healthy" if not issues else "degraded"
        })
    
    def check_redis_config(self):
        """Check Redis resilience configuration"""
        issues = []
        recommendations = []
        
        # Check for resilient client
        resilient_client_path = Path("core/redis/resilient_client.py")
        if resilient_client_path.exists():
            print("  ✓ Redis resilient client found")
            
            with open(resilient_client_path) as f:
                content = f.read()
                
            # Check for circuit breaker
            if "CircuitBreaker" in content:
                print("  ✓ Circuit breaker pattern implemented")
            else:
                issues.append("Circuit breaker not implemented")
                recommendations.append("Implement circuit breaker for Redis resilience")
                
            # Check for connection pooling
            if "ConnectionPool" in content:
                print("  ✓ Connection pooling configured")
            else:
                issues.append("Connection pooling not configured")
                recommendations.append("Configure Redis connection pooling")
                
            # Check for fallback
            if "InMemoryFallback" in content:
                print("  ✓ In-memory fallback implemented")
            else:
                issues.append("No fallback mechanism for Redis failures")
                recommendations.append("Implement fallback mechanism")
        else:
            issues.append("Redis resilient client not found")
            recommendations.append("Implement resilient Redis client with circuit breaker")
        
        self.results.append({
            "component": "Redis Configuration",
            "issues": issues,
            "recommendations": recommendations,
            "status": "healthy" if not issues else "degraded"
        })
    
    def check_code_structure(self):
        """Check code structure and patterns"""
        issues = []
        recommendations = []
        metrics = {}
        
        # Check for memory management patterns
        memory_files = list(Path(".").rglob("*memory*.py"))
        metrics["memory_management_files"] = len(memory_files)
        print(f"  Found {len(memory_files)} memory management files")
        
        if len(memory_files) < 5:
            recommendations.append("Consider implementing more memory management modules")
        
        # Check for async patterns
        async_count = 0
        for py_file in Path(".").rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                with open(py_file) as f:
                    content = f.read()
                    if "async def" in content:
                        async_count += 1
            except:
                pass
        
        metrics["async_implementations"] = async_count
        print(f"  Found {async_count} files with async implementations")
        
        if async_count < 20:
            recommendations.append("Implement more async operations for better performance")
        
        # Check for connection pooling
        pool_count = 0
        for py_file in Path(".").rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                with open(py_file) as f:
                    content = f.read()
                    if "pool" in content.lower() and ("connection" in content or "redis" in content):
                        pool_count += 1
            except:
                pass
        
        metrics["connection_pooling_files"] = pool_count
        print(f"  Found {pool_count} files with connection pooling")
        
        if pool_count < 3:
            issues.append("Limited connection pooling implementation")
            recommendations.append("Implement connection pooling for all database connections")
        
        # Check for error handling
        error_handling_count = 0
        for py_file in Path(".").rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                with open(py_file) as f:
                    content = f.read()
                    if "try:" in content and "except" in content:
                        error_handling_count += 1
            except:
                pass
        
        metrics["error_handling_files"] = error_handling_count
        print(f"  Found {error_handling_count} files with error handling")
        
        self.results.append({
            "component": "Code Structure",
            "issues": issues,
            "recommendations": recommendations,
            "metrics": metrics,
            "status": "healthy" if not issues else "degraded"
        })
    
    def generate_report(self):
        """Generate audit report"""
        # Count issues
        total_issues = sum(len(r["issues"]) for r in self.results)
        total_recommendations = sum(len(r["recommendations"]) for r in self.results)
        
        # Determine overall status
        critical_count = sum(1 for r in self.results if r["status"] == "critical")
        degraded_count = sum(1 for r in self.results if r["status"] == "degraded")
        
        if critical_count > 0:
            overall_status = "critical"
        elif degraded_count > 2:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        # Create summary
        summary = f"System Status: {overall_status.upper()}\n\n"
        summary += f"Components Audited: {len(self.results)}\n"
        summary += f"Total Issues: {total_issues}\n"
        summary += f"Total Recommendations: {total_recommendations}\n\n"
        
        if total_issues > 0:
            summary += "Top Issues:\n"
            for result in self.results:
                for issue in result["issues"][:2]:
                    summary += f"- {issue}\n"
        
        summary += "\nTop Recommendations:\n"
        all_recommendations = []
        for result in self.results:
            all_recommendations.extend(result["recommendations"])
        
        for rec in all_recommendations[:5]:
            summary += f"- {rec}\n"
        
        report = {
            "audit_timestamp": datetime.utcnow().isoformat(),
            "duration_seconds": time.time() - self.start_time,
            "overall_status": overall_status,
            "total_issues": total_issues,
            "total_recommendations": total_recommendations,
            "component_results": self.results,
            "summary": summary
        }
        
        return report


async def main():
    """Run the audit"""
    auditor = MCPDatabaseAuditor()
    report = await auditor.run_audit()
    
    print("\n" + "=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)
    print(report["summary"])
    
    # Show critical issues
    for result in auditor.results:
        if result["issues"]:
            print(f"\n{result['component']}:")
            for issue in result["issues"]:
                print(f"  ❌ {issue}")
            for rec in result["recommendations"]:
                print(f"  💡 {rec}")


if __name__ == "__main__":
    asyncio.run(main())