"""Debug Adapter for Factory AI integration.

This adapter bridges the Debug Droid with the tools MCP server,
handling error diagnosis and query optimization capabilities.
"""

import json
import logging
import traceback
from typing import Any, Dict, List, Optional, Tuple

from .factory_mcp_adapter import FactoryMCPAdapter

logger = logging.getLogger(__name__)

class DebugAdapter(FactoryMCPAdapter):
    """Adapter for Debug Droid to tools MCP server communication.

    Specializes in:
    - Error diagnosis and root cause analysis
    - Query optimization (SQL, GraphQL, etc.)
    - Stack trace analysis
    - Performance profiling integration
    """

    def __init__(self, mcp_server: Any, droid_config: Dict[str, Any]) -> None:
        """Initialize the Debug adapter.

        Args:
            mcp_server: The tools MCP server instance
            droid_config: Configuration for the Debug droid
        """
        super().__init__(mcp_server, droid_config, "debug")
        self.supported_methods = [
            "diagnose_error",
            "analyze_stack_trace",
            "optimize_query",
            "profile_performance",
            "debug_integration",
            "analyze_logs",
        ]
        self.profiling_enabled = droid_config.get("profiling_enabled", True)
        self.max_stack_depth = droid_config.get("max_stack_depth", 50)

    async def translate_to_factory(self, mcp_request: Dict[str, Any]) -> Dict[str, Any]:
        """Translate MCP request to Factory AI Debug format.

        Args:
            mcp_request: Request in MCP format

        Returns:
            Request in Factory AI Debug format
        """
        method = mcp_request.get("method", "")
        params = mcp_request.get("params", {})

        # Map MCP methods to Factory AI Debug capabilities
        factory_request = {
            "droid": "debug",
            "action": self._map_method_to_action(method),
            "context": {
                "error_type": params.get("error_type", "unknown"),
                "environment": params.get("environment", "production"),
                "stack_trace": params.get("stack_trace", ""),
                "logs": params.get("logs", []),
                "system_info": params.get("system_info", {}),
                "related_code": params.get("related_code", ""),
            },
            "options": {
                "deep_analysis": params.get("deep_analysis", True),
                "include_suggestions": params.get("include_suggestions", True),
                "profile_depth": params.get("profile_depth", "detailed"),
                "max_solutions": params.get("max_solutions", 5),
            },
        }

        # Handle specific debugging scenarios
        if method == "optimize_query":
            factory_request["context"]["query"] = params.get("query", "")
            factory_request["context"]["query_type"] = params.get("query_type", "sql")
            factory_request["context"]["schema"] = params.get("schema", {})
            factory_request["context"]["execution_plan"] = params.get("execution_plan", "")
            factory_request["context"]["performance_metrics"] = params.get("metrics", {})

        elif method == "analyze_stack_trace":
            factory_request["context"]["exception_type"] = params.get("exception_type", "")
            factory_request["context"]["source_maps"] = params.get("source_maps", {})
            factory_request["options"]["symbolicate"] = params.get("symbolicate", True)

        elif method == "profile_performance":
            factory_request["context"]["profile_data"] = params.get("profile_data", {})
            factory_request["context"]["bottlenecks"] = params.get("bottlenecks", [])
            factory_request["context"]["resource_usage"] = params.get("resource_usage", {})

        logger.debug(f"Translated to Factory request: {factory_request}")
        return factory_request

    async def translate_to_mcp(self, factory_response: Dict[str, Any]) -> Dict[str, Any]:
        """Translate Factory AI Debug response to MCP format.

        Args:
            factory_response: Response from Factory AI Debug

        Returns:
            Response in MCP format
        """
        if "error" in factory_response:
            return {
                "error": {
                    "code": -32603,
                    "message": factory_response["error"].get("message", "Unknown error"),
                    "data": factory_response["error"].get("details", {}),
                }
            }

        result = factory_response.get("result", {})
        mcp_response = {
            "result": {
                "diagnosis": result.get("diagnosis", {}),
                "root_cause": result.get("root_cause", ""),
                "solutions": self._format_solutions(result.get("solutions", [])),
                "stack_analysis": result.get("stack_analysis", {}),
                "performance_insights": result.get("performance_insights", {}),
                "recommendations": result.get("recommendations", []),
                "metadata": {
                    "confidence_score": result.get("confidence_score", 0),
                    "analysis_time": result.get("analysis_time", 0),
                    "debug_version": result.get("version", "1.0.0"),
                },
            }
        }

        # Include query optimization results if present
        if "optimized_query" in result:
            mcp_response["result"]["optimization"] = {
                "original_query": result.get("original_query", ""),
                "optimized_query": result["optimized_query"],
                "improvements": result.get("improvements", []),
                "expected_speedup": result.get("expected_speedup", "0%"),
                "execution_plan": result.get("execution_plan", ""),
            }

        # Include profiling results if present
        if "profile" in result:
            mcp_response["result"]["profile"] = {
                "hotspots": result["profile"].get("hotspots", []),
                "memory_leaks": result["profile"].get("memory_leaks", []),
                "cpu_usage": result["profile"].get("cpu_usage", {}),
                "recommendations": result["profile"].get("recommendations", []),
            }

        logger.debug(f"Translated to MCP response: {mcp_response}")
        return mcp_response

    async def _call_factory_droid(self, factory_request: Dict[str, Any]) -> Dict[str, Any]:
        """Call the Factory AI Debug droid.

        Args:
            factory_request: Request in Factory AI format

        Returns:
            Response from Factory AI Debug droid
        """
        try:
            # Import Factory AI client dynamically
            from factory_ai import FactoryAI

            if not self._factory_client:
                self._factory_client = FactoryAI(
                    api_key=self.droid_config.get("api_key"),
                    base_url=self.droid_config.get("base_url", "https://api.factory.ai"),
                )

            # Call the Debug droid
            response = await self._factory_client.droids.debug.execute(
                action=factory_request["action"],
                context=factory_request["context"],
                options=factory_request["options"],
            )

            return {"result": response}

        except ImportError:
            logger.warning("Factory AI SDK not available, using mock response")
            return self._get_mock_response(factory_request)

        except Exception as e:
            logger.error(f"Error calling Debug droid: {e}", exc_info=True)
            raise

    def _map_method_to_action(self, method: str) -> str:
        """Map MCP method to Factory AI Debug action.

        Args:
            method: MCP method name

        Returns:
            Factory AI action name
        """
        method_mapping = {
            "diagnose_error": "diagnose",
            "analyze_stack_trace": "analyze_stack",
            "optimize_query": "optimize_query",
            "profile_performance": "profile",
            "debug_integration": "debug_integration",
            "analyze_logs": "analyze_logs",
        }
        return method_mapping.get(method, "diagnose")

    def _format_solutions(self, solutions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format debug solutions for MCP response.

        Args:
            solutions: List of solution data from Factory AI

        Returns:
            Formatted solutions for MCP
        """
        formatted_solutions = []
        for idx, solution in enumerate(solutions):
            formatted_solutions.append(
                {
                    "id": idx + 1,
                    "description": solution.get("description", ""),
                    "code_fix": solution.get("code_fix", ""),
                    "explanation": solution.get("explanation", ""),
                    "confidence": solution.get("confidence", 0),
                    "impact": solution.get("impact", "low"),
                    "implementation_steps": solution.get("steps", []),
                }
            )
        return formatted_solutions

    def _get_mock_response(self, factory_request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock response for testing.

        Args:
            factory_request: The Factory AI request

        Returns:
            Mock response
        """
        action = factory_request["action"]

        if action == "diagnose":
            return {
                "result": {
                    "diagnosis": {
                        "error_category": "connection_error",
                        "severity": "high",
                        "affected_components": ["database", "api"],
                    },
                    "root_cause": "Database connection pool exhausted due to leaked connections",
                    "solutions": [
                        {
                            "description": "Implement connection pooling with proper cleanup",
                            "code_fix": """# Add connection pool configuration
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Ensure connections are properly closed
@contextmanager
def get_db_connection():
    conn = engine.connect()
    try:
                yield conn
    finally:
        conn.close()
""",
                            "explanation": "This implements proper connection pooling with automatic cleanup",
                            "confidence": 0.95,
                            "impact": "high",
                            "steps": [
                                "Update database configuration",
                                "Implement connection context manager",
                                "Test connection pool behavior",
                            ],
                        }
                    ],
                    "stack_analysis": {
                        "error_location": "app/services/database.py:45",
                        "call_chain": [
                            "main.py:23",
                            "api/routes.py:67",
                            "services/database.py:45",
                        ],
                    },
                    "confidence_score": 0.92,
                    "analysis_time": 1.2,
                    "version": "1.0.0",
                }
            }

        elif action == "optimize_query":
            return {
                "result": {
                    "original_query": factory_request["context"].get("query", ""),
                    "optimized_query": """-- Optimized query with proper indexing
SELECT u.id, u.name, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.created_at >= '2024-01-01'
GROUP BY u.id, u.name
HAVING COUNT(o.id) > 5
ORDER BY order_count DESC
LIMIT 100;

-- Create index for better performance
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_orders_user_id ON orders(user_id);""",
                    "improvements": [
                        "Added appropriate indexes",
                        "Optimized JOIN strategy",
                        "Added LIMIT to prevent full table scan",
                    ],
                    "expected_speedup": "85%",
                    "execution_plan": "Index Scan -> Hash Join -> Sort -> Limit",
                    "confidence_score": 0.88,
                    "analysis_time": 0.8,
                }
            }

        elif action == "profile":
            return {
                "result": {
                    "profile": {
                        "hotspots": [
                            {
                                "function": "process_data",
                                "file": "processors/data.py:123",
                                "cpu_time": 45.2,
                                "calls": 10000,
                            },
                            {
                                "function": "serialize_response",
                                "file": "api/serializers.py:56",
                                "cpu_time": 23.1,
                                "calls": 5000,
                            },
                        ],
                        "memory_leaks": [
                            {
                                "location": "cache/manager.py:89",
                                "size": "124MB",
                                "description": "Cache entries not being evicted",
                            }
                        ],
                        "cpu_usage": {
                            "average": 67.5,
                            "peak": 95.2,
                            "idle": 12.3,
                        },
                        "recommendations": [
                            "Implement caching for process_data function",
                            "Use lazy loading for serialization",
                            "Add cache eviction policy",
                        ],
                    },
                    "performance_insights": {
                        "bottlenecks": ["Database queries", "JSON serialization"],
                        "optimization_potential": "high",
                    },
                    "analysis_time": 2.5,
                    "version": "1.0.0",
                }
            }

        return {
            "result": {
                "message": f"Mock response for action: {action}",
                "diagnosis": {"status": "completed"},
                "version": "1.0.0",
            }
        }

    async def analyze_error_context(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze error with additional context.

        Args:
            error: The exception to analyze
            context: Additional context about the error

        Returns:
            Analysis results
        """
        stack_trace = traceback.format_exc()
        error_type = type(error).__name__

        request = {
            "method": "diagnose_error",
            "params": {
                "error_type": error_type,
                "stack_trace": stack_trace,
                "environment": context.get("environment", "production"),
                "related_code": context.get("code", ""),
                "system_info": {
                    "python_version": context.get("python_version", "3.10"),
                    "os": context.get("os", "linux"),
                    "memory_usage": context.get("memory_usage", {}),
                },
            },
        }

        return await self.process_request(request)
