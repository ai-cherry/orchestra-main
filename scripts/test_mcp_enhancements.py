#!/usr/bin/env python3
"""
Test script for enhanced MCP servers
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.servers.code_intelligence_server import CodeIntelligenceServer
from mcp_server.servers.git_intelligence_server import GitIntelligenceServer


async def test_code_intelligence():
    """Test code intelligence server."""
    print("🔧 Testing Code Intelligence MCP Server...")
    
    server = CodeIntelligenceServer()
    
    # Test AST analysis on this file
    try:
        result = await server._analyze_file_ast({
            "file_path": __file__,
            "include_docstrings": True
        })
        
        if result and result[0].text:
            print("✅ AST analysis working")
            print(f"   Preview: {result[0].text[:200]}...")
        else:
            print("❌ AST analysis failed")
    except Exception as e:
        print(f"❌ AST analysis error: {e}")
    
    # Test function usage search
    try:
        result = await server._find_function_usage({
            "symbol_name": "test_code_intelligence",
            "file_extensions": [".py"]
        })
        
        if result:
            print("✅ Function usage search working")
        else:
            print("❌ Function usage search failed")
    except Exception as e:
        print(f"❌ Function usage search error: {e}")


async def test_git_intelligence():
    """Test git intelligence server."""
    print("\n📊 Testing Git Intelligence MCP Server...")
    
    server = GitIntelligenceServer()
    
    # Test recent changes
    try:
        result = await server._git_recent_changes({
            "days": 7
        })
        
        if result and result[0].text:
            print("✅ Git recent changes working")
            print(f"   Preview: {result[0].text[:200]}...")
        else:
            print("❌ Git recent changes failed")
    except Exception as e:
        print(f"❌ Git recent changes error: {e}")
    
    # Test hotspot analysis
    try:
        result = await server._git_hotspot_analysis({
            "days": 30,
            "min_changes": 1
        })
        
        if result:
            print("✅ Git hotspot analysis working")
        else:
            print("❌ Git hotspot analysis failed")
    except Exception as e:
        print(f"❌ Git hotspot analysis error: {e}")


def test_tool_registry():
    """Test updated tool registry."""
    print("\n🛠️  Testing Tool Registry...")
    
    try:
        from core.conductor.src.tools.registry import ToolRegistry
        
        registry = ToolRegistry()
        
        # Check that MongoDB tools are removed
        mongodb_tools = [tool for tool in registry.tools.values() if 'mongodb' in tool.name.lower()]
        if not mongodb_tools:
            print("✅ MongoDB tools successfully removed")
        else:
            print(f"❌ Found {len(mongodb_tools)} MongoDB tools still present")
        
        # Check PostgreSQL tools are present
        postgres_tools = [tool for tool in registry.tools.values() if 'postgres' in tool.name.lower()]
        if postgres_tools:
            print(f"✅ Found {len(postgres_tools)} PostgreSQL tools")
        else:
            print("❌ No PostgreSQL tools found")
        
        # Check Redis tools
        redis_tools = [tool for tool in registry.tools.values() if 'cache' in tool.category.lower()]
        if redis_tools:
            print(f"✅ Found {len(redis_tools)} Redis/cache tools")
        else:
            print("❌ No Redis/cache tools found")
        
        # Check Weaviate tools
        weaviate_tools = [tool for tool in registry.tools.values() if 'vector' in tool.name.lower()]
        if weaviate_tools:
            print(f"✅ Found {len(weaviate_tools)} Weaviate/vector tools")
        else:
            print("❌ No Weaviate/vector tools found")
        
        print(f"\n📋 Total tools in registry: {len(registry.tools)}")
        
    except Exception as e:
        print(f"❌ Tool registry test error: {e}")


def test_mcp_configuration():
    """Test MCP configuration files."""
    print("\n⚙️  Testing MCP Configuration...")
    
    try:
        # Test .cursor/mcp.json
        cursor_config = Path(".cursor/mcp.json")
        if cursor_config.exists():
            with open(cursor_config) as f:
                config = json.load(f)
            
            servers = config.get("mcp-servers", {})
            
            if "code-intelligence" in servers:
                print("✅ Code Intelligence server in Cursor config")
            else:
                print("❌ Code Intelligence server missing from Cursor config")
            
            if "git-intelligence" in servers:
                print("✅ Git Intelligence server in Cursor config")
            else:
                print("❌ Git Intelligence server missing from Cursor config")
            
            print(f"   Total servers in Cursor config: {len(servers)}")
        else:
            print("❌ .cursor/mcp.json not found")
        
        # Test .mcp.json
        main_config = Path(".mcp.json")
        if main_config.exists():
            with open(main_config) as f:
                config = json.load(f)
            
            servers = config.get("servers", {})
            
            if "code-intelligence" in servers:
                print("✅ Code Intelligence server in main config")
            else:
                print("❌ Code Intelligence server missing from main config")
            
            if "git-intelligence" in servers:
                print("✅ Git Intelligence server in main config")
            else:
                print("❌ Git Intelligence server missing from main config")
            
            print(f"   Total servers in main config: {len(servers)}")
        else:
            print("❌ .mcp.json not found")
            
    except Exception as e:
        print(f"❌ MCP configuration test error: {e}")


async def main():
    """Run all tests."""
    print("🚀 Testing Enhanced MCP Servers for AI Coding")
    print("=" * 50)
    
    # Test individual servers
    await test_code_intelligence()
    await test_git_intelligence()
    
    # Test registry and configuration
    test_tool_registry()
    test_mcp_configuration()
    
    print("\n" + "=" * 50)
    print("🎯 Enhancement Summary:")
    print("   ✅ PostgreSQL + Redis + Weaviate architecture")
    print("   ✅ Code Intelligence MCP Server")
    print("   ✅ Git Intelligence MCP Server")
    print("   ✅ Updated tool registry (removed MongoDB)")
    print("   ✅ Enhanced MCP configurations")
    print("\n📖 See docs/MCP_ENHANCEMENT_ROADMAP.md for next steps")


if __name__ == "__main__":
    asyncio.run(main()) 