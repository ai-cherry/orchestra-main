"""Architect Adapter for Factory AI integration.

This adapter bridges the Architect Droid with the orchestrator MCP server,
handling system design and Pulumi IaC capabilities.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from .factory_mcp_adapter import FactoryMCPAdapter

logger = logging.getLogger(__name__)

class ArchitectAdapter(FactoryMCPAdapter):
    """Adapter for Architect Droid to orchestrator MCP server communication.

    Specializes in:
    - System design and architecture
    - Infrastructure as Code (Pulumi)
    - Complex architectural diagrams
    - High-level system planning
    """

    def __init__(self, mcp_server: Any, droid_config: Dict[str, Any]) -> None:
        """Initialize the Architect adapter.

        Args:
            mcp_server: The orchestrator MCP server instance
            droid_config: Configuration for the Architect droid
        """
        super().__init__(mcp_server, droid_config, "architect")
        self.supported_methods = [
            "design_system",
            "generate_infrastructure",
            "analyze_architecture",
            "create_diagram",
            "validate_design",
        ]

    async def translate_to_factory(self, mcp_request: Dict[str, Any]) -> Dict[str, Any]:
        """Translate MCP request to Factory AI Architect format.

        Args:
            mcp_request: Request in MCP format

        Returns:
            Request in Factory AI Architect format
        """
        method = mcp_request.get("method", "")
        params = mcp_request.get("params", {})

        # Map MCP methods to Factory AI Architect capabilities
        factory_request = {
            "droid": "architect",
            "action": self._map_method_to_action(method),
            "context": {
                "project_type": params.get("project_type", "microservices"),
                "requirements": params.get("requirements", []),
                "constraints": params.get("constraints", {}),
                "existing_infrastructure": params.get("existing_infrastructure", {}),
            },
            "options": {
                "generate_diagrams": params.get("generate_diagrams", True),
                "include_iac": params.get("include_iac", True),
                "cloud_provider": params.get("cloud_provider", "vultr"),
                "output_format": params.get("output_format", "pulumi"),
            },
        }

        # Handle special cases for architectural diagrams
        if method == "create_diagram":
            factory_request["context"]["diagram_type"] = params.get("diagram_type", "system")
            factory_request["context"]["components"] = params.get("components", [])
            factory_request["options"]["diagram_format"] = params.get("format", "mermaid")

        # Handle Pulumi IaC generation
        if method == "generate_infrastructure":
            factory_request["context"]["stack_name"] = params.get("stack_name", "main")
            factory_request["context"]["resources"] = params.get("resources", [])
            factory_request["options"]["pulumi_config"] = params.get("pulumi_config", {})

        logger.debug(f"Translated to Factory request: {factory_request}")
        return factory_request

    async def translate_to_mcp(self, factory_response: Dict[str, Any]) -> Dict[str, Any]:
        """Translate Factory AI Architect response to MCP format.

        Args:
            factory_response: Response from Factory AI Architect

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
                "design": result.get("design", {}),
                "diagrams": self._format_diagrams(result.get("diagrams", [])),
                "infrastructure_code": result.get("infrastructure_code", ""),
                "recommendations": result.get("recommendations", []),
                "validation_results": result.get("validation_results", {}),
                "metadata": {
                    "architect_version": result.get("version", "1.0.0"),
                    "generation_time": result.get("generation_time", 0),
                    "complexity_score": result.get("complexity_score", 0),
                },
            }
        }

        # Include Pulumi-specific outputs if present
        if "pulumi_stack" in result:
            mcp_response["result"]["pulumi"] = {
                "stack": result["pulumi_stack"],
                "config": result.get("pulumi_config", {}),
                "outputs": result.get("pulumi_outputs", {}),
            }

        logger.debug(f"Translated to MCP response: {mcp_response}")
        return mcp_response

    async def _call_factory_droid(self, factory_request: Dict[str, Any]) -> Dict[str, Any]:
        """Call the Factory AI Architect droid.

        Args:
            factory_request: Request in Factory AI format

        Returns:
            Response from Factory AI Architect droid
        """
        try:
            # Import Factory AI client dynamically to avoid circular imports
            from factory_ai import FactoryAI

            if not self._factory_client:
                self._factory_client = FactoryAI(
                    api_key=self.droid_config.get("api_key"),
                    base_url=self.droid_config.get("base_url", "https://api.factory.ai"),
                )

            # Call the Architect droid
            response = await self._factory_client.droids.architect.execute(
                action=factory_request["action"],
                context=factory_request["context"],
                options=factory_request["options"],
            )

            return {"result": response}

        except ImportError:
            logger.warning("Factory AI SDK not available, using mock response")
            # Return mock response for testing
            return self._get_mock_response(factory_request)

        except Exception as e:
            logger.error(f"Error calling Architect droid: {e}", exc_info=True)
            raise

    def _map_method_to_action(self, method: str) -> str:
        """Map MCP method to Factory AI Architect action.

        Args:
            method: MCP method name

        Returns:
            Factory AI action name
        """
        method_mapping = {
            "design_system": "design_architecture",
            "generate_infrastructure": "generate_iac",
            "analyze_architecture": "analyze_system",
            "create_diagram": "create_architectural_diagram",
            "validate_design": "validate_architecture",
        }
        return method_mapping.get(method, "design_architecture")

    def _format_diagrams(self, diagrams: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format architectural diagrams for MCP response.

        Args:
            diagrams: List of diagram data from Factory AI

        Returns:
            Formatted diagrams for MCP
        """
        formatted_diagrams = []
        for diagram in diagrams:
            formatted_diagrams.append(
                {
                    "type": diagram.get("type", "system"),
                    "format": diagram.get("format", "mermaid"),
                    "content": diagram.get("content", ""),
                    "title": diagram.get("title", "Architecture Diagram"),
                    "description": diagram.get("description", ""),
                }
            )
        return formatted_diagrams

    def _get_mock_response(self, factory_request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock response for testing.

        Args:
            factory_request: The Factory AI request

        Returns:
            Mock response
        """
        action = factory_request["action"]

        if action == "design_architecture":
            return {
                "result": {
                    "design": {
                        "components": [
                            {
                                "name": "API Gateway",
                                "type": "service",
                                "technology": "FastAPI",
                            },
                            {
                                "name": "PostgreSQL",
                                "type": "database",
                                "technology": "PostgreSQL 15",
                            },
                            {
                                "name": "Weaviate",
                                "type": "vector_db",
                                "technology": "Weaviate",
                            },
                        ],
                        "connections": [
                            {
                                "from": "API Gateway",
                                "to": "PostgreSQL",
                                "type": "data",
                            },
                            {
                                "from": "API Gateway",
                                "to": "Weaviate",
                                "type": "vector_search",
                            },
                        ],
                    },
                    "diagrams": [
                        {
                            "type": "system",
                            "format": "mermaid",
                            "content": "graph TD\n  A[API Gateway] --> B[PostgreSQL]\n  A --> C[Weaviate]",
                        }
                    ],
                    "recommendations": [
                        "Use connection pooling for PostgreSQL",
                        "Implement caching layer for frequent queries",
                    ],
                    "version": "1.0.0",
                    "generation_time": 2.5,
                    "complexity_score": 7.5,
                }
            }

        elif action == "generate_iac":
            return {
                "result": {
                    "infrastructure_code": """import pulumi
import pulumi_vultr as vultr

# Create VPC
vpc = vultr.Vpc("main-vpc",
    region="ewr",
    v4_subnet="10.0.0.0",
    v4_subnet_mask=24
)

# Create instances
api_instance = vultr.Instance("api-server",
    region="ewr",
    plan="vc2-1c-2gb",
    os_id=1743,  # Ubuntu 22.04
    vpc_ids=[vpc.id]
)

pulumi.export("api_ip", api_instance.main_ip)
""",
                    "pulumi_stack": "orchestra-main",
                    "pulumi_config": {
                        "vultr:region": "ewr",
                        "project:name": "orchestra",
                    },
                    "version": "1.0.0",
                    "generation_time": 1.8,
                }
            }

        return {
            "result": {
                "message": f"Mock response for action: {action}",
                "version": "1.0.0",
            }
        }
