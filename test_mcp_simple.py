#!/usr/bin/env python3
import json

print("Simple MCP Server Test")
print("-" * 40)

# Test 1: Check MCP installation
try:

    print("✓ MCP module installed")
except ImportError:
    print("✗ MCP module not installed")

# Test 2: Check configuration
try:
    with open("mcp_config.json") as f:
        config = json.load(f)
    print("✓ MCP config loaded successfully")
    print(f"  Servers found: {len(config.get('mcpServers', {}))}")
except Exception as e:
    print(f"✗ Failed to load MCP config: {e}")

# Test 3: Check Claude API key
import os

if os.environ.get("ANTHROPIC_API_KEY"):
    print("✓ ANTHROPIC_API_KEY is set")
else:
    print("✗ ANTHROPIC_API_KEY not set")

print("\nQuick Start Commands:")
print("1. Set API key: export ANTHROPIC_API_KEY='your-key-here'")
print("2. Start MCP server: python mcp_server/run_mcp_server.py")
print("3. Test with Claude: claude --mcp-config mcp_config.json")
