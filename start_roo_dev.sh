#!/bin/bash
# Quick start for Roo development

echo "🪃 Starting Roo Development Environment"
echo "======================================"

# Load environment
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Activate virtual environment
if [ -d venv ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
fi

# Start MCP server
if ! curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo "🔧 Starting MCP Server..."
    python mcp_roo_server.py > /tmp/roo_mcp.log 2>&1 &
    sleep 3
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo "✅ MCP Server running"
    else
        echo "❌ MCP Server failed to start"
    fi
else
    echo "✅ MCP Server already running"
fi

# Check Roo configuration
if [ -f .roo/config.json ]; then
    echo "✅ Roo configuration found"
else
    echo "❌ Roo configuration missing"
fi

echo ""
echo "🎯 Ready for Roo Code development!"
echo "📋 Next steps:"
echo "   1. Install Roo Code VS Code extension"
echo "   2. Open VS Code in this directory" 
echo "   3. Use Orchestrator mode for complex tasks"
echo "   4. Test integration with: python test_roo_integration.py"
