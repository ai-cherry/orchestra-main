#!/usr/bin/env python3
"""
Validate AI Agent MCP Integration
"""

import asyncio
import aiohttp
import json

async def validate_mcp_integration():
    """Validate that all AI agents can connect to MCP servers."""
    
    print("🔍 Validating AI Agent MCP Integration...")
    
    # Check discovery endpoint
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8010/discover") as resp:
                if resp.status == 200:
                    discovery = await resp.json()
                    print(f"✅ Discovery endpoint working ({len(discovery.get('mcp_servers', {}))} servers)")
                else:
                    print("❌ Discovery endpoint failed")
        except Exception as e:
            print(f"❌ Discovery endpoint error: {e}")
    
    # Check individual MCP servers
    servers = [8001, 8002, 8003, 8005, 8006, 8007, 8008]
    for port in servers:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:{port}/health", timeout=5) as resp:
                    if resp.status == 200:
                        print(f"✅ MCP server on port {port} healthy")
                    else:
                        print(f"⚠️  MCP server on port {port} status: {resp.status}")
        except Exception:
            print(f"❌ MCP server on port {port} unreachable")

if __name__ == "__main__":
    asyncio.run(validate_mcp_integration())
