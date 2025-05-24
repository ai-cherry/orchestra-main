#!/bin/bash
# Quick fix script for MCP implementation issues

echo "Fixing MCP Implementation Issues..."

# 1. Install missing dependencies
echo "Installing missing Python packages..."
pip install mcp anthropic phidata google-cloud-firestore google-cloud-secret-manager prometheus-client

# 2. Fix agents.yaml structure
echo "Fixing agents.yaml structure..."
cat > config/agents.yaml << 'EOF'
agent_definitions:
  # Example LangChain Agent: Modular, plug-and-play integration
  langchain_example_agent:
    agent_name: LangChain Example
    description: "A modular agent powered by LangChain"
    wrapper_type: langchain
    langchain_agent_class: myproject.langchain.MyLangChainAgent  # Update with actual import path
    llm_ref: llm_gpt4_turbo_via_portkey
    tools: []
    role: "Perform tasks using LangChain"
    instructions:
      - "Respond to user queries using LangChain chains and tools"
      - "Leverage memory and context for improved answers"
    memory:
      memory_type: pgvector

  # Gong Agent: Analyzes call recordings and transcripts
  phidata_gong_analyst:
    agent_name: Gong Analyst
    description: "Analyzes Gong call recordings, transcripts, and sentiment to extract insights"
    wrapper_type: phidata
    phidata_agent_class: phi.agent.Agent
    llm_ref: openai_gpt4
    tools: []
    role: "Call analysis and insights extraction"
    instructions:
      - "Analyze call transcripts for key insights"
      - "Extract action items and follow-ups"
    memory:
      memory_type: redis
EOF

# 3. Create a simple MCP server test
echo "Creating simple MCP server test..."
cat > test_mcp_simple.py << 'EOF'
#!/usr/bin/env python3
import subprocess
import sys
import json

print("Simple MCP Server Test")
print("-" * 40)

# Test 1: Check MCP installation
try:
    import mcp
    print("✓ MCP module installed")
except ImportError:
    print("✗ MCP module not installed")

# Test 2: Check configuration
try:
    with open('mcp_config.json') as f:
        config = json.load(f)
    print("✓ MCP config loaded successfully")
    print(f"  Servers found: {len(config.get('mcpServers', {}))}")
except Exception as e:
    print(f"✗ Failed to load MCP config: {e}")

# Test 3: Check Claude API key
import os
if os.environ.get('ANTHROPIC_API_KEY'):
    print("✓ ANTHROPIC_API_KEY is set")
else:
    print("✗ ANTHROPIC_API_KEY not set")

print("\nQuick Start Commands:")
print("1. Set API key: export ANTHROPIC_API_KEY='your-key-here'")
print("2. Start MCP server: python mcp_server/run_mcp_server.py")
print("3. Test with Claude: claude --mcp-config mcp_config.json")
EOF

chmod +x test_mcp_simple.py

echo "Fix script completed!"
echo ""
echo "Next steps:"
echo "1. Run: source fix_mcp_issues.sh"
echo "2. Set your API key: export ANTHROPIC_API_KEY='your-key-here'"
echo "3. Run simple test: ./test_mcp_simple.py"
echo "4. Run full test: python test_mcp_implementation.py"
