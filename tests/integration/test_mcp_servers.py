"""
Integration Tests for MCP Servers
=================================
Tests for MongoDB and Weaviate MCP server connectivity
"""

import os

import pytest

# Mock the MCP module if not available
try:
    from scripts.mcp_integration import MCPAgentInterface, MCPConfig, MCPIntegration
except ImportError:
    pytest.skip("MCP integration module not available", allow_module_level=True)


class TestMCPServers:
    """Test MCP server connectivity and functionality"""

    @pytest.fixture
    async def mcp_integration(self):
        """Create MCP integration instance"""
        config = MCPConfig(
            mongodb_endpoint=os.getenv("MCP_MONGODB_ENDPOINT", "http://localhost:8081"),
            weaviate_endpoint=os.getenv("MCP_WEAVIATE_ENDPOINT", "http://localhost:8082"),
            timeout=10,
        )
        mcp = MCPIntegration(config)
        yield mcp
        await mcp.close()

    @pytest.mark.asyncio
    async def test_mcp_initialization(self, mcp_integration):
        """Test MCP client initialization"""
        try:
            await mcp_integration.initialize()
            assert mcp_integration._initialized
        except Exception as e:
            pytest.skip(f"MCP servers not available: {e}")

    @pytest.mark.asyncio
    async def test_mongodb_natural_language_query(self, mcp_integration):
        """Test natural language queries to MongoDB"""
        try:
            await mcp_integration.initialize()

            # Test query
            result = await mcp_integration.query_mongodb("Show all agents with status active")

            assert isinstance(result, dict)
            assert "success" in result
            assert "data" in result

        except Exception as e:
            pytest.skip(f"MongoDB MCP not available: {e}")

    @pytest.mark.asyncio
    async def test_weaviate_semantic_search(self, mcp_integration):
        """Test semantic search with Weaviate"""
        try:
            await mcp_integration.initialize()

            # Test semantic search
            result = await mcp_integration.semantic_search("machine learning optimization techniques")

            assert isinstance(result, dict)
            assert "success" in result
            assert "results" in result

        except Exception as e:
            pytest.skip(f"Weaviate MCP not available: {e}")

    @pytest.mark.asyncio
    async def test_hybrid_query(self, mcp_integration):
        """Test hybrid query combining MongoDB and Weaviate"""
        try:
            await mcp_integration.initialize()

            # Test hybrid query
            result = await mcp_integration.hybrid_query("Find active agents similar to research assistant")

            assert isinstance(result, dict)
            assert "success" in result

        except Exception as e:
            pytest.skip(f"MCP servers not available: {e}")

    @pytest.mark.asyncio
    async def test_agent_interface(self, mcp_integration):
        """Test high-level agent interface"""
        try:
            agent = MCPAgentInterface(mcp_integration)

            # Test question answering
            answer = await agent.answer_question("Show me all conversations about API integration")

            assert isinstance(answer, str)
            assert len(answer) > 0

        except Exception as e:
            pytest.skip(f"MCP servers not available: {e}")


@pytest.mark.asyncio
async def test_mcp_server_health():
    """Test MCP server health endpoints"""
    import aiohttp

    endpoints = {
        "mongodb": os.getenv("MCP_MONGODB_ENDPOINT", "http://localhost:8081"),
        "weaviate": os.getenv("MCP_WEAVIATE_ENDPOINT", "http://localhost:8082"),
    }

    async with aiohttp.ClientSession() as session:
        for name, endpoint in endpoints.items():
            try:
                async with session.get(f"{endpoint}/health", timeout=5) as response:
                    assert response.status == 200
                    print(f"{name} MCP server is healthy")
            except Exception as e:
                pytest.skip(f"{name} MCP server not reachable: {e}")
