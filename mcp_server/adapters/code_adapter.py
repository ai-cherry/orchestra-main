"""Code Adapter for Factory AI integration.

This adapter bridges the Code Droid with the tools MCP server,
handling fast code generation and optimization capabilities.
"""

import asyncio
import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from .factory_mcp_adapter import FactoryMCPAdapter

logger = logging.getLogger(__name__)


class CodeAdapter(FactoryMCPAdapter):
    """Adapter for Code Droid to tools MCP server communication.

    Specializes in:
    - Fast code generation
    - Code optimization
    - Streaming responses for real-time generation
    - Incremental code updates
    """

    def __init__(self, mcp_server: Any, droid_config: Dict[str, Any]) -> None:
        """Initialize the Code adapter.

        Args:
            mcp_server: The tools MCP server instance
            droid_config: Configuration for the Code droid
        """
        super().__init__(mcp_server, droid_config, "code")
        self.supported_methods = [
            "generate_code",
            "optimize_code",
            "refactor_code",
            "complete_code",
            "analyze_code",
            "fix_code",
        ]
        self.streaming_enabled = droid_config.get("streaming", True)
        self.chunk_size = droid_config.get("chunk_size", 1024)

    async def translate_to_factory(
        self, mcp_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Translate MCP request to Factory AI Code format.

        Args:
            mcp_request: Request in MCP format

        Returns:
            Request in Factory AI Code format
        """
        method = mcp_request.get("method", "")
        params = mcp_request.get("params", {})

        # Map MCP methods to Factory AI Code capabilities
        factory_request = {
            "droid": "code",
            "action": self._map_method_to_action(method),
            "context": {
                "language": params.get("language", "python"),
                "framework": params.get("framework", ""),
                "existing_code": params.get("existing_code", ""),
                "requirements": params.get("requirements", []),
                "style_guide": params.get("style_guide", "google"),
            },
            "options": {
                "streaming": self.streaming_enabled and params.get("stream", False),
                "optimization_level": params.get("optimization_level", "balanced"),
                "include_tests": params.get("include_tests", True),
                "include_docs": params.get("include_docs", True),
                "max_tokens": params.get("max_tokens", 4096),
            },
        }

        # Handle specific code generation scenarios
        if method == "generate_code":
            factory_request["context"]["template"] = params.get("template", "")
            factory_request["context"]["specifications"] = params.get(
                "specifications", {}
            )

        elif method == "optimize_code":
            factory_request["context"]["optimization_goals"] = params.get(
                "optimization_goals", ["performance", "readability"]
            )
            factory_request["context"]["metrics"] = params.get("metrics", {})

        elif method == "refactor_code":
            factory_request["context"]["refactor_type"] = params.get(
                "refactor_type", "general"
            )
            factory_request["context"]["target_patterns"] = params.get(
                "patterns", []
            )

        elif method == "complete_code":
            factory_request["context"]["cursor_position"] = params.get(
                "cursor_position", 0
            )
            factory_request["context"]["completion_type"] = params.get(
                "completion_type", "line"
            )

        logger.debug(f"Translated to Factory request: {factory_request}")
        return factory_request

    async def translate_to_mcp(
        self, factory_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Translate Factory AI Code response to MCP format.

        Args:
            factory_response: Response from Factory AI Code

        Returns:
            Response in MCP format
        """
        if "error" in factory_response:
            return {
                "error": {
                    "code": -32603,
                    "message": factory_response["error"].get(
                        "message", "Unknown error"
                    ),
                    "data": factory_response["error"].get("details", {}),
                }
            }

        result = factory_response.get("result", {})
        
        # Handle streaming responses
        if result.get("streaming"):
            return {
                "result": {
                    "code": "",  # Will be filled by stream
                    "streaming": True,
                    "stream_id": result.get("stream_id"),
                }
            }

        mcp_response = {
            "result": {
                "code": result.get("code", ""),
                "language": result.get("language", "python"),
                "tests": result.get("tests", ""),
                "documentation": result.get("documentation", ""),
                "metrics": {
                    "lines_of_code": result.get("loc", 0),
                    "complexity": result.get("complexity", 0),
                    "generation_time": result.get("generation_time", 0),
                    "optimization_score": result.get("optimization_score", 0),
                },
                "suggestions": result.get("suggestions", []),
                "warnings": result.get("warnings", []),
            }
        }

        # Include refactoring details if present
        if "refactoring" in result:
            mcp_response["result"]["refactoring"] = {
                "changes": result["refactoring"].get("changes", []),
                "impact": result["refactoring"].get("impact", {}),
                "preview": result["refactoring"].get("preview", ""),
            }

        logger.debug(f"Translated to MCP response: {mcp_response}")
        return mcp_response

    async def _call_factory_droid(
        self, factory_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call the Factory AI Code droid.

        Args:
            factory_request: Request in Factory AI format

        Returns:
            Response from Factory AI Code droid
        """
        try:
            # Import Factory AI client dynamically
            from factory_ai import FactoryAI

            if not self._factory_client:
                self._factory_client = FactoryAI(
                    api_key=self.droid_config.get("api_key"),
                    base_url=self.droid_config.get(
                        "base_url", "https://api.factory.ai"
                    ),
                )

            # Handle streaming requests
            if factory_request["options"].get("streaming"):
                return await self._handle_streaming_request(factory_request)

            # Regular request
            response = await self._factory_client.droids.code.execute(
                action=factory_request["action"],
                context=factory_request["context"],
                options=factory_request["options"],
            )

            return {"result": response}

        except ImportError:
            logger.warning("Factory AI SDK not available, using mock response")
            return self._get_mock_response(factory_request)

        except Exception as e:
            logger.error(f"Error calling Code droid: {e}", exc_info=True)
            raise

    async def _handle_streaming_request(
        self, factory_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle streaming code generation request.

        Args:
            factory_request: Request in Factory AI format

        Returns:
            Streaming response setup
        """
        try:
            # Create streaming session
            stream_id = f"stream_{id(factory_request)}"
            
            # Start async streaming task
            asyncio.create_task(
                self._stream_code_generation(stream_id, factory_request)
            )
            
            return {
                "result": {
                    "streaming": True,
                    "stream_id": stream_id,
                }
            }
        except Exception as e:
            logger.error(f"Error setting up streaming: {e}", exc_info=True)
            raise

    async def _stream_code_generation(
        self, stream_id: str, factory_request: Dict[str, Any]
    ) -> None:
        """Stream code generation responses.

        Args:
            stream_id: Unique stream identifier
            factory_request: Request in Factory AI format
        """
        try:
            async for chunk in self._factory_client.droids.code.stream(
                action=factory_request["action"],
                context=factory_request["context"],
                options=factory_request["options"],
            ):
                # Send chunk to MCP server's streaming handler
                if hasattr(self.mcp_server, "send_stream_chunk"):
                    await self.mcp_server.send_stream_chunk(stream_id, chunk)
                    
        except Exception as e:
            logger.error(f"Error in streaming: {e}", exc_info=True)
            if hasattr(self.mcp_server, "close_stream"):
                await self.mcp_server.close_stream(stream_id, error=str(e))

    def _map_method_to_action(self, method: str) -> str:
        """Map MCP method to Factory AI Code action.

        Args:
            method: MCP method name

        Returns:
            Factory AI action name
        """
        method_mapping = {
            "generate_code": "generate",
            "optimize_code": "optimize",
            "refactor_code": "refactor",
            "complete_code": "complete",
            "analyze_code": "analyze",
            "fix_code": "fix",
        }
        return method_mapping.get(method, "generate")

    def _get_mock_response(
        self, factory_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate mock response for testing.

        Args:
            factory_request: The Factory AI request

        Returns:
            Mock response
        """
        action = factory_request["action"]
        language = factory_request["context"].get("language", "python")
        
        if action == "generate":
            code = self._generate_mock_code(language, factory_request["context"])
            return {
                "result": {
                    "code": code,
                    "language": language,
                    "tests": self._generate_mock_tests(language),
                    "documentation": "# Generated Code\n\nThis is mock generated code.",
                    "loc": len(code.split("\n")),
                    "complexity": 5,
                    "generation_time": 0.5,
                    "optimization_score": 8.5,
                    "suggestions": [
                        "Consider adding type hints",
                        "Add error handling for edge cases",
                    ],
                }
            }
        
        elif action == "optimize":
            return {
                "result": {
                    "code": "# Optimized code\n# Performance improvements applied",
                    "language": language,
                    "optimization_score": 9.2,
                    "metrics": {
                        "before": {"performance": 5.0, "memory": 100},
                        "after": {"performance": 8.5, "memory": 75},
                    },
                    "generation_time": 0.3,
                }
            }
        
        elif action == "refactor":
            return {
                "result": {
                    "code": "# Refactored code\n# Improved structure and readability",
                    "language": language,
                    "refactoring": {
                        "changes": [
                            {
                                "type": "extract_method",
                                "description": "Extracted complex logic into separate method",
                            }
                        ],
                        "impact": {"readability": "+30%", "maintainability": "+25%"},
                    },
                    "generation_time": 0.4,
                }
            }
        
        return {
            "result": {
                "message": f"Mock response for action: {action}",
                "code": "# Mock code",
                "language": language,
            }
        }

    def _generate_mock_code(
        self, language: str, context: Dict[str, Any]
    ) -> str:
        """Generate mock code based on language and context.

        Args:
            language: Programming language
            context: Request context

        Returns:
            Mock code string
        """
        if language == "python":
            return """from typing import List, Dict, Any

class DataProcessor:
    \"\"\"Process data with optimized algorithms.\"\"\"
    
    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self._cache: Dict[str, Any] = {}
    
    async def process(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        \"\"\"Process data asynchronously.\"\"\"
        results = []
        for item in data:
            result = await self._process_item(item)
            results.append(result)
        return results
    
    async def _process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Process individual item.\"\"\"
        # Implementation here
        return {"processed": True, **item}
"""
        elif language == "typescript":
            return """interface DataItem {
  id: string;
  value: any;
}

class DataProcessor {
  private config: Record<string, any>;
  private cache: Map<string, any>;

  constructor(config: Record<string, any>) {
    this.config = config;
    this.cache = new Map();
  }

  async process(data: DataItem[]): Promise<DataItem[]> {
    const results = await Promise.all(
      data.map(item => this.processItem(item))
    );
    return results;
  }

  private async processItem(item: DataItem): Promise<DataItem> {
    // Implementation here
    return { ...item, processed: true };
  }
}
"""
        return f"// Mock {language} code\n// Generated based on context"

    def _generate_mock_tests(self, language: str) -> str:
        """Generate mock test code.

        Args:
            language: Programming language

        Returns:
            Mock test code
        """
        if language == "python":
            return """import pytest
from unittest.mock import Mock, patch

class TestDataProcessor:
    def test_process_data(self):
        processor = DataProcessor({})
        result = processor.process([{"id": 1}])
        assert len(result) == 1
        assert result[0]["processed"] is True
"""
        return f"// Mock {language} tests"