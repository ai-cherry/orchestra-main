"""Example integration script for Factory AI MCP Server Adapters.

This script demonstrates how to set up and use all adapters together
in a real-world scenario.
"""

import asyncio
import logging
from typing import Any, Dict, List

from mcp_server.adapters import (
    ArchitectAdapter,
    CodeAdapter,
    DebugAdapter,
    ReliabilityAdapter,
    KnowledgeAdapter,
)
from mcp_server.adapters.config import (
    load_config_from_env,
    validate_config,
    DEVELOPMENT_CONFIG,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class MockMCPServer:
    """Mock MCP server for demonstration."""

    def __init__(self, name: str):
        self.name = name

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Mock request handler."""
        logger.info(f"{self.name} handling fallback request: {request['method']}")
        return {
            "result": {
                "message": f"Handled by {self.name}",
                "method": request.get("method"),
            }
        }


class IntegratedAdapterSystem:
    """Integrated system using all Factory AI adapters."""

    def __init__(self, config=None):
        """Initialize the integrated adapter system.

        Args:
            config: Adapter system configuration (uses env if None)
        """
        self.config = config or load_config_from_env()
        
        # Validate configuration
        try:
            validate_config(self.config)
        except ValueError as e:
            logger.warning(f"Configuration validation failed: {e}")
            logger.info("Using development configuration")
            self.config = DEVELOPMENT_CONFIG
        
        # Initialize MCP servers (mocked for example)
        self.mcp_servers = {
            "orchestrator": MockMCPServer("orchestrator"),
            "tools": MockMCPServer("tools"),
            "deployment": MockMCPServer("deployment"),
            "memory": MockMCPServer("memory"),
        }
        
        # Initialize adapters
        self.adapters = {
            "architect": ArchitectAdapter(
                self.mcp_servers["orchestrator"],
                self.config.architect.__dict__,
            ),
            "code": CodeAdapter(
                self.mcp_servers["tools"],
                self.config.code.__dict__,
            ),
            "debug": DebugAdapter(
                self.mcp_servers["tools"],
                self.config.debug.__dict__,
            ),
            "reliability": ReliabilityAdapter(
                self.mcp_servers["deployment"],
                self.config.reliability.__dict__,
            ),
            "knowledge": KnowledgeAdapter(
                self.mcp_servers["memory"],
                self.config.knowledge.__dict__,
            ),
        }

    async def design_and_implement_system(
        self, requirements: List[str]
    ) -> Dict[str, Any]:
        """Design and implement a system based on requirements.

        This demonstrates a complete workflow using multiple adapters.

        Args:
            requirements: List of system requirements

        Returns:
            Complete system implementation results
        """
        results = {}
        
        # Step 1: Design the system architecture
        logger.info("Step 1: Designing system architecture...")
        design_request = {
            "method": "design_system",
            "params": {
                "project_type": "microservices",
                "requirements": requirements,
                "cloud_provider": "vultr",
                "generate_diagrams": True,
            },
        }
        results["architecture"] = await self.adapters["architect"].process_request(
            design_request
        )
        
        # Step 2: Generate implementation code
        logger.info("Step 2: Generating implementation code...")
        code_request = {
            "method": "generate_code",
            "params": {
                "language": "python",
                "framework": "fastapi",
                "requirements": requirements,
                "specifications": results["architecture"]["result"].get("design", {}),
                "include_tests": True,
            },
        }
        results["code"] = await self.adapters["code"].process_request(code_request)
        
        # Step 3: Store knowledge for future reference
        logger.info("Step 3: Storing system knowledge...")
        knowledge_request = {
            "method": "store_knowledge",
            "params": {
                "content": f"System Design: {results['architecture']}",
                "collection": "system_designs",
                "metadata": {
                    "type": "architecture",
                    "requirements": requirements,
                },
            },
        }
        results["knowledge"] = await self.adapters["knowledge"].process_request(
            knowledge_request
        )
        
        # Step 4: Set up reliability monitoring
        logger.info("Step 4: Setting up reliability monitoring...")
        reliability_request = {
            "method": "generate_runbook",
            "params": {
                "system_components": ["api-gateway", "database", "cache"],
                "incident_types": ["high_latency", "connection_errors"],
            },
        }
        results["reliability"] = await self.adapters["reliability"].process_request(
            reliability_request
        )
        
        return results

    async def debug_production_issue(
        self, error_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Debug a production issue using multiple adapters.

        Args:
            error_info: Information about the error

        Returns:
            Debugging results and solutions
        """
        results = {}
        
        # Step 1: Diagnose the error
        logger.info("Step 1: Diagnosing error...")
        debug_request = {
            "method": "diagnose_error",
            "params": {
                "error_type": error_info.get("type", "unknown"),
                "stack_trace": error_info.get("stack_trace", ""),
                "environment": "production",
                "logs": error_info.get("logs", []),
            },
        }
        results["diagnosis"] = await self.adapters["debug"].process_request(
            debug_request
        )
        
        # Step 2: Search for similar issues in knowledge base
        logger.info("Step 2: Searching knowledge base...")
        search_request = {
            "method": "search_knowledge",
            "params": {
                "query": error_info.get("error_message", ""),
                "search_type": "semantic",
                "filters": {"type": "error_resolution"},
            },
        }
        results["similar_issues"] = await self.adapters["knowledge"].process_request(
            search_request
        )
        
        # Step 3: Generate fix code if needed
        if results["diagnosis"]["result"].get("solutions"):
            logger.info("Step 3: Generating fix code...")
            fix_request = {
                "method": "fix_code",
                "params": {
                    "existing_code": error_info.get("code_context", ""),
                    "error_diagnosis": results["diagnosis"]["result"],
                    "language": "python",
                },
            }
            results["fix"] = await self.adapters["code"].process_request(fix_request)
        
        # Step 4: Create incident and remediation plan
        logger.info("Step 4: Creating incident and remediation plan...")
        incident_request = {
            "method": "manage_incident",
            "params": {
                "incident_details": {
                    "title": f"Production Error: {error_info.get('type')}",
                    "description": error_info.get("error_message"),
                    "severity": "high",
                },
                "auto_remediate": False,  # Manual review for production
            },
        }
        results["incident"] = await self.adapters["reliability"].process_request(
            incident_request
        )
        
        return results

    async def optimize_system_performance(self) -> Dict[str, Any]:
        """Optimize system performance using multiple adapters.

        Returns:
            Optimization results
        """
        results = {}
        
        # Step 1: Profile current performance
        logger.info("Step 1: Profiling system performance...")
        profile_request = {
            "method": "profile_performance",
            "params": {
                "profile_data": {
                    "cpu_usage": {"average": 75, "peak": 95},
                    "memory_usage": {"used": 8192, "total": 16384},
                    "response_times": {"p50": 100, "p95": 500, "p99": 1000},
                },
            },
        }
        results["profile"] = await self.adapters["debug"].process_request(
            profile_request
        )
        
        # Step 2: Optimize identified bottlenecks
        logger.info("Step 2: Optimizing code...")
        optimize_request = {
            "method": "optimize_code",
            "params": {
                "existing_code": "# Sample code with performance issues",
                "optimization_goals": ["performance", "memory"],
                "metrics": results["profile"]["result"].get("performance_insights", {}),
            },
        }
        results["optimized_code"] = await self.adapters["code"].process_request(
            optimize_request
        )
        
        # Step 3: Update system architecture if needed
        logger.info("Step 3: Analyzing architecture improvements...")
        arch_request = {
            "method": "analyze_architecture",
            "params": {
                "current_architecture": {},
                "performance_issues": results["profile"]["result"].get("bottlenecks", []),
            },
        }
        results["architecture_improvements"] = await self.adapters[
            "architect"
        ].process_request(arch_request)
        
        # Step 4: Document optimization results
        logger.info("Step 4: Documenting optimizations...")
        doc_request = {
            "method": "generate_documentation",
            "params": {
                "doc_type": "performance_optimization",
                "content": {
                    "profile": results["profile"],
                    "optimizations": results["optimized_code"],
                    "architecture": results["architecture_improvements"],
                },
            },
        }
        results["documentation"] = await self.adapters["knowledge"].process_request(
            doc_request
        )
        
        return results

    async def health_check_all(self) -> Dict[str, Any]:
        """Perform health check on all adapters.

        Returns:
            Health status of all adapters
        """
        health_results = {}
        
        for name, adapter in self.adapters.items():
            try:
                health = await adapter.health_check()
                health_results[name] = health
                logger.info(f"{name} adapter health: {'healthy' if health['healthy'] else 'unhealthy'}")
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                health_results[name] = {"healthy": False, "error": str(e)}
        
        return health_results


async def main():
    """Main function demonstrating adapter integration."""
    # Initialize the integrated system
    system = IntegratedAdapterSystem()
    
    # Example 1: Design and implement a new system
    logger.info("=== Example 1: Design and Implement System ===")
    requirements = [
        "Handle 10k requests per second",
        "Sub-100ms response time",
        "Fault tolerant with 99.9% uptime",
        "Scalable microservices architecture",
    ]
    
    try:
        implementation_results = await system.design_and_implement_system(requirements)
        logger.info(f"System design completed: {implementation_results.keys()}")
    except Exception as e:
        logger.error(f"System design failed: {e}")
    
    # Example 2: Debug a production issue
    logger.info("\n=== Example 2: Debug Production Issue ===")
    error_info = {
        "type": "DatabaseConnectionError",
        "error_message": "Connection pool exhausted",
        "stack_trace": "Traceback (most recent call last)...",
        "logs": ["ERROR: Too many connections", "WARNING: Pool size limit reached"],
        "code_context": "async def get_db_connection():\n    return await pool.acquire()",
    }
    
    try:
        debug_results = await system.debug_production_issue(error_info)
        logger.info(f"Debugging completed: {debug_results.keys()}")
    except Exception as e:
        logger.error(f"Debugging failed: {e}")
    
    # Example 3: Optimize system performance
    logger.info("\n=== Example 3: Optimize System Performance ===")
    try:
        optimization_results = await system.optimize_system_performance()
        logger.info(f"Optimization completed: {optimization_results.keys()}")
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
    
    # Health check all adapters
    logger.info("\n=== Health Check All Adapters ===")
    health_status = await system.health_check_all()
    
    # Summary
    healthy_count = sum(1 for h in health_status.values() if h.get("healthy", False))
    logger.info(f"\nHealth Summary: {healthy_count}/{len(health_status)} adapters healthy")


if __name__ == "__main__":
    asyncio.run(main())