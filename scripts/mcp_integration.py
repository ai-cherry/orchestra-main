#!/usr/bin/env python3
"""
MCP Integration Module for AI Orchestra
=======================================
Provides natural language query interfaces for MongoDB and Weaviate
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from mcp import MCPClient, Tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MCPConfig:
    """Configuration for MCP servers"""

    mongodb_endpoint: str = "http://mcp-mongodb:8080"
    weaviate_endpoint: str = "http://mcp-weaviate:8080"
    timeout: int = 30
    max_retries: int = 3


class MCPIntegration:
    """
    MCP Integration for natural language queries to MongoDB and Weaviate
    """

    def __init__(self, config: Optional[MCPConfig] = None):
        self.config = config or MCPConfig()
        self.mongodb_client: Optional[MCPClient] = None
        self.weaviate_client: Optional[MCPClient] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize MCP clients"""
        try:
            # Initialize MongoDB MCP client
            self.mongodb_client = MCPClient(server_url=self.config.mongodb_endpoint, timeout=self.config.timeout)
            await self.mongodb_client.connect()

            # Initialize Weaviate MCP client
            self.weaviate_client = MCPClient(server_url=self.config.weaviate_endpoint, timeout=self.config.timeout)
            await self.weaviate_client.connect()

            self._initialized = True
            logger.info("MCP clients initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize MCP clients: {e}")
            raise

    async def query_mongodb(self, natural_language_query: str) -> Dict[str, Any]:
        """
        Execute natural language query against MongoDB

        Examples:
        - "Show all users created in the last 24 hours"
        - "Find agents with status 'active' and high memory usage"
        - "Get conversation history for user john@example.com"
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Use MongoDB MCP's natural language tool
            result = await self.mongodb_client.call_tool(
                "query",
                {
                    "prompt": natural_language_query,
                    "collection": "auto",  # Let MCP determine the collection
                    "limit": 100,
                },
            )

            return {
                "success": True,
                "data": result.get("documents", []),
                "count": result.get("count", 0),
                "query_interpretation": result.get("interpretation", ""),
            }

        except Exception as e:
            logger.error(f"MongoDB query failed: {e}")
            return {"success": False, "error": str(e), "data": []}

    async def semantic_search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Perform semantic search using Weaviate

        Examples:
        - "Find documents about machine learning optimization"
        - "Search for conversations discussing API integration"
        - "Get similar agents to the research assistant"
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Use Weaviate MCP's semantic search
            result = await self.weaviate_client.call_tool(
                "semantic_search",
                {
                    "query": query,
                    "limit": limit,
                    "certainty": 0.7,  # Minimum similarity threshold
                },
            )

            return {
                "success": True,
                "results": result.get("objects", []),
                "total": result.get("total", 0),
                "query_vector": result.get("vector", []),
            }

        except Exception as e:
            logger.error(f"Weaviate search failed: {e}")
            return {"success": False, "error": str(e), "results": []}

    async def hybrid_query(self, query: str) -> Dict[str, Any]:
        """
        Execute hybrid query combining MongoDB filters with Weaviate semantic search

        Example: "Find active agents similar to research assistant created this week"
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Parse query to identify structured vs semantic parts
            # This is a simplified example - in production, use NLP

            # First, get semantic results from Weaviate
            semantic_results = await self.semantic_search(query)

            if not semantic_results["success"]:
                return semantic_results

            # Extract IDs from semantic results
            semantic_ids = [r["id"] for r in semantic_results["results"]]

            # Query MongoDB with semantic IDs as filter
            mongodb_query = f"Find documents with ids in {semantic_ids[:10]}"
            mongodb_results = await self.query_mongodb(mongodb_query)

            # Combine results
            return {
                "success": True,
                "semantic_matches": semantic_results["results"],
                "structured_data": mongodb_results["data"],
                "query": query,
            }

        except Exception as e:
            logger.error(f"Hybrid query failed: {e}")
            return {"success": False, "error": str(e)}

    async def list_available_tools(self) -> Dict[str, List[Tool]]:
        """List all available MCP tools from both servers"""
        tools = {"mongodb": [], "weaviate": []}

        if not self._initialized:
            await self.initialize()

        try:
            # Get MongoDB tools
            if self.mongodb_client:
                mongodb_tools = await self.mongodb_client.list_tools()
                tools["mongodb"] = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_schema,
                    }
                    for tool in mongodb_tools
                ]

            # Get Weaviate tools
            if self.weaviate_client:
                weaviate_tools = await self.weaviate_client.list_tools()
                tools["weaviate"] = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_schema,
                    }
                    for tool in weaviate_tools
                ]

        except Exception as e:
            logger.error(f"Failed to list tools: {e}")

        return tools

    async def close(self) -> None:
        """Close MCP connections"""
        if self.mongodb_client:
            await self.mongodb_client.close()
        if self.weaviate_client:
            await self.weaviate_client.close()
        self._initialized = False


class MCPAgentInterface:
    """
    High-level interface for AI agents to use MCP
    """

    def __init__(self, mcp_integration: MCPIntegration):
        self.mcp = mcp_integration

    async def answer_question(self, question: str) -> str:
        """
        Answer a question using available data sources
        """
        # Determine if question needs semantic search, structured query, or both
        keywords_semantic = ["similar", "like", "about", "related", "semantic"]
        keywords_structured = ["count", "list", "show", "find", "get", "filter"]

        use_semantic = any(keyword in question.lower() for keyword in keywords_semantic)
        use_structured = any(keyword in question.lower() for keyword in keywords_structured)

        results = []

        if use_semantic or not use_structured:
            # Default to semantic search for open-ended questions
            semantic_result = await self.mcp.semantic_search(question)
            if semantic_result["success"]:
                results.append(f"Found {semantic_result['total']} semantically similar results")
                for idx, result in enumerate(semantic_result["results"][:3]):
                    results.append(f"{idx+1}. {result.get('title', 'Untitled')}: {result.get('summary', '')}")

        if use_structured:
            # Use MongoDB for structured queries
            mongodb_result = await self.mcp.query_mongodb(question)
            if mongodb_result["success"]:
                results.append(f"\nFound {mongodb_result['count']} matching documents")
                results.append(f"Query interpretation: {mongodb_result['query_interpretation']}")
                for doc in mongodb_result["data"][:3]:
                    results.append(f"- {json.dumps(doc, indent=2)}")

        if not results:
            return "I couldn't find any relevant information for your question."

        return "\n".join(results)

    async def store_memory(self, memory_type: str, content: Dict[str, Any]) -> bool:
        """
        Store memory in appropriate backend
        """
        # Short-term memories go to MongoDB
        if memory_type in ["conversation", "short_term", "cache"]:
            query = f"Insert into {memory_type} collection: {json.dumps(content)}"
            result = await self.mcp.query_mongodb(query)
            return result["success"]

        # Long-term memories go to Weaviate for semantic search
        elif memory_type in ["knowledge", "long_term", "learned"]:
            # This would use a different MCP tool for insertion
            # For now, we'll just log it
            logger.info(f"Would store to Weaviate: {content}")
            return True

        return False


# Example usage and testing
async def main():
    """Example usage of MCP integration"""

    # Initialize MCP integration
    config = MCPConfig(
        mongodb_endpoint="http://localhost:8081",  # For local testing
        weaviate_endpoint="http://localhost:8082",
    )

    mcp = MCPIntegration(config)
    agent_interface = MCPAgentInterface(mcp)

    try:
        # Initialize connections
        await mcp.initialize()

        # List available tools
        tools = await mcp.list_available_tools()
        print("Available MCP Tools:")
        print(json.dumps(tools, indent=2))

        # Example queries
        queries = [
            "Show all active agents created in the last week",
            "Find conversations about API integration",
            "Get users with high token usage",
            "Search for documents similar to machine learning optimization",
        ]

        for query in queries:
            print(f"\nQuery: {query}")
            answer = await agent_interface.answer_question(query)
            print(f"Answer: {answer}")

    finally:
        await mcp.close()


if __name__ == "__main__":
    asyncio.run(main())
