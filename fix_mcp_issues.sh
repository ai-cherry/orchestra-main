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

echo "=== Fixing Authentication and Service Access ==="
echo

# Step 1: Force refresh authentication
echo "Step 1: Refreshing authentication..."
# Removed gcloud command
# Removed gcloud command

# Step 2: Ensure correct account is active
echo
echo "Step 2: Setting correct account..."
# Removed gcloud command
# Removed gcloud command

# Step 3: Test authentication
echo
echo "Step 3: Testing authentication..."
if gcloud projects describe cherry-ai-project --format="value(projectId)" 2>/dev/null; then
    echo "✅ Authentication working!"
else
    echo "❌ Authentication failed. Trying alternative method..."
    # vultr-cli auth application-default login
fi

# Step 4: Make the service public (this is the fix for 403)
echo
echo "Step 4: Making ai-cherry_ai-minimal public..."
# Removed gcloud command
    --region=us-central1 \
    --member="allUsers" \
    --role="roles/run.invoker" \
    --quiet 2>&1 || echo "Failed to update IAM policy. Use Cloud Console instead."

# Step 5: Test the service
echo
echo "Step 5: Testing the service..."
SERVICE_URL="https://ai-cherry_ai-minimal-yshgcxa7ta-uc.a.run.app"
echo "Testing $SERVICE_URL/health"
curl -s "$SERVICE_URL/health" | head -20

echo
echo "=== Summary ==="
echo "If the service still returns 403/401, please:"
echo "1. Go to: https://console.cloud.google.com/run?project=cherry-ai-project"
echo "2. Click on 'ai-cherry_ai-minimal'"
echo "3. Go to PERMISSIONS tab"
echo "4. Add 'allUsers' with 'Cloud Run Invoker' role"
echo
echo "Direct link to service:"
echo "https://console.cloud.google.com/run/detail/us-central1/ai-cherry_ai-minimal/permissions?project=cherry-ai-project"
