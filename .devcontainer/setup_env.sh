#!/bin/bash
# Cherry AI Orchestrator - Enhanced Development Environment Setup
# This script configures the development environment with all necessary API keys and tools

set -e

echo "🚀 Setting up Cherry AI Orchestrator Development Environment..."

# Create necessary directories
mkdir -p /tmp
mkdir -p ~/.config/cherry-ai
mkdir -p ~/.local/bin

# Export file for environment variables
EXPORT_FILE="/tmp/devcontainer_exports.sh"
echo "# Cherry AI Orchestrator Environment Variables" > $EXPORT_FILE
echo "# Generated on $(date)" >> $EXPORT_FILE

# Function to add environment variable
add_env_var() {
    local var_name=$1
    local var_value=$2
    echo "export $var_name=\"$var_value\"" >> $EXPORT_FILE
}

# Core Cherry AI Configuration
add_env_var "CHERRY_AI_ENV" "development"
add_env_var "PROJECT_T" "/workspace"
add_env_var "PYTHONPATH" "/workspace:/workspace/mcp_server"

# API Keys (will be populated from GitHub secrets in production)
add_env_var "OPENAI_API_KEY" "${OPENAI_API_KEY:-your_openai_api_key_here}"
add_env_var "ANTHROPIC_API_KEY" "${ANTHROPIC_API_KEY:-your_anthropic_api_key_here}"
add_env_var "GEMINI_API_KEY" "${GEMINI_API_KEY:-your_gemini_api_key_here}"
add_env_var "PERPLEXITY_API_KEY" "${PERPLEXITY_API_KEY:-your_perplexity_api_key_here}"
add_env_var "OPENROUTER_API_KEY" "${OPENROUTER_API_KEY:-your_openrouter_api_key_here}"

# Database Configuration
add_env_var "POSTGRES_HOST" "${POSTGRES_HOST:-45.77.87.106}"
add_env_var "POSTGRES_PORT" "${POSTGRES_PORT:-5432}"
add_env_var "POSTGRES_DB" "${POSTGRES_DB:-cherry_ai}"
add_env_var "POSTGRES_USER" "${POSTGRES_USER:-postgres}"
add_env_var "POSTGRES_PASSWORD" "${POSTGRES_PASSWORD:-your_secure_password}"
add_env_var "REDIS_URL" "${REDIS_URL:-redis://localhost:6379}"

# Vector Database Configuration
add_env_var "WEAVIATE_URL" "${WEAVIATE_URL:-your_weaviate_url_here}"
add_env_var "WEAVIATE_API_KEY" "${WEAVIATE_API_KEY:-your_weaviate_api_key_here}"
add_env_var "PINECONE_API_KEY" "${PINECONE_API_KEY:-your_pinecone_api_key_here}"

# Infrastructure Configuration
add_env_var "LAMBDA_API_KEY" "${LAMBDA_API_KEY:-your_LAMBDA_API_KEY_here}"
add_env_var "PULUMI_ACCESS_TOKEN" "${PULUMI_ACCESS_TOKEN:-your_pulumi_token_here}"

# MCP Server Configuration
add_env_var "MCP_SERVER_HOST" "0.0.0.0"
add_env_var "MCP_TOOLS_PORT" "8006"
add_env_var "MCP_MEMORY_PORT" "8003"
add_env_var "MCP_CODE_INTELLIGENCE_PORT" "8007"
add_env_var "MCP_GIT_INTELLIGENCE_PORT" "8008"

# Cherry AI Personas Configuration
add_env_var "CHERRY_PERSONAL_PORT" "8001"
add_env_var "SOPHIA_BUSINESS_PORT" "8002"
add_env_var "KAREN_HEALTHCARE_PORT" "8003"

# Production Server Configuration
add_env_var "PRODUCTION_SERVER_IP" "45.32.69.157"
add_env_var "STAGING_SERVER_IP" "207.246.108.201"
add_env_var "DATABASE_SERVER_IP" "45.77.87.106"

# GitHub Configuration
add_env_var "GITHUB_TOKEN" "${GITHUB_TOKEN:-your_github_token_here}"
add_env_var "GITHUB_REPO" "ai-cherry/orchestra-main"

# Logging Configuration
add_env_var "LOG_LEVEL" "INFO"
add_env_var "LOG_FORMAT" "json"

# Make the export file executable
chmod +x $EXPORT_FILE

# Source the environment variables
source $EXPORT_FILE

echo "✅ Environment variables configured"

# Install additional Python packages for Cherry AI
echo "📦 Installing Cherry AI specific packages..."
pip install --quiet --no-cache-dir \
    openai \
    anthropic \
    google-generativeai \
    weaviate-client \
    pinecone-client \
    redis \
    psycopg2-binary \
    sqlalchemy \
    alembic \
    fastapi \
    uvicorn \
    websockets \
    aiofiles \
    python-multipart \
    jinja2 \
    python-dotenv \
    pydantic \
    httpx \
    asyncio-mqtt \
    watchdog \
    gitpython \
    psutil \
    rich \
    typer \
    click

echo "✅ Python packages installed"

# Create Cherry AI CLI tool
cat > ~/.local/bin/cherry-ai << 'EOF'
#!/usr/bin/env python3
"""
Cherry AI CLI Tool
Quick access to Cherry AI Orchestrator functions
"""
import sys
import os
import subprocess
import json
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Cherry AI Orchestrator CLI")
        print("Usage: cherry-ai <command> [args]")
        print("\nCommands:")
        print("  start-mcp     Start MCP servers")
        print("  stop-mcp      Stop MCP servers")
        print("  status        Show system status")
        print("  deploy        Deploy to production")
        print("  test          Run tests")
        print("  codex         Use OpenAI Codex for code generation")
        return
    
    command = sys.argv[1]
    
    if command == "start-mcp":
        print("🚀 Starting Cherry AI MCP servers...")
        subprocess.run(["python", "/workspace/mcp_server/start_all.py"])
    elif command == "stop-mcp":
        print("🛑 Stopping Cherry AI MCP servers...")
        subprocess.run(["pkill", "-f", "mcp_server"])
    elif command == "status":
        print("📊 Cherry AI System Status")
        subprocess.run(["python", "/workspace/scripts/system_status.py"])
    elif command == "deploy":
        print("🚀 Deploying to production...")
        subprocess.run(["bash", "/workspace/deploy_to_production.sh"])
    elif command == "test":
        print("🧪 Running Cherry AI tests...")
        subprocess.run(["python", "-m", "pytest", "/workspace/tests/"])
    elif command == "codex":
        print("🤖 Cherry AI Codex Integration")
        subprocess.run(["python", "/workspace/mcp_server/codex_integration.py"] + sys.argv[2:])
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
EOF

chmod +x ~/.local/bin/cherry-ai

echo "✅ Cherry AI CLI tool created"

# Create MCP server startup script
cat > /workspace/start_mcp_servers.sh << 'EOF'
#!/bin/bash
# Start all Cherry AI MCP servers

echo "🚀 Starting Cherry AI MCP Servers..."

# Start Redis if not running
if ! pgrep redis-server > /dev/null; then
    echo "Starting Redis server..."
    redis-server --daemonize yes
fi

# Start MCP servers in background
cd /workspace

echo "Starting MCP Tools Server..."
python mcp_server/servers/tools_server.py &

echo "Starting MCP Memory Server..."
python mcp_server/servers/memory_server.py &

echo "Starting MCP Code Intelligence Server..."
python mcp_server/servers/code_intelligence_server.py &

echo "Starting MCP Git Intelligence Server..."
python mcp_server/servers/git_intelligence_server.py &

echo "✅ All MCP servers started"
echo "Use 'cherry-ai status' to check server status"
EOF

chmod +x /workspace/start_mcp_servers.sh

echo "✅ MCP startup script created"

# Create Cursor AI configuration for Cherry AI
mkdir -p ~/.config/cursor
cat > ~/.config/cursor/cherry-ai-config.json << 'EOF'
{
  "ai_models": {
    "primary": "gpt-4",
    "fallback": "claude-3-sonnet",
    "code_completion": "codex"
  },
  "cherry_ai_context": {
    "project_type": "AI Orchestrator",
    "personas": ["Cherry Personal", "Sophia Business", "Karen Healthcare"],
    "tech_stack": ["Python", "Flask", "FastAPI", "PostgreSQL", "Redis", "Weaviate"],
    "infrastructure": ["Lambda", "Pulumi", "GitHub Actions"]
  },
  "mcp_servers": {
    "enabled": true,
    "auto_start": true,
    "servers": [
      "cherry-ai-tools",
      "cherry-ai-memory", 
      "cherry-ai-code-intelligence",
      "cherry-ai-git-intelligence"
    ]
  }
}
EOF

echo "✅ Cursor AI configuration created"

# Create development environment status check
cat > /workspace/check_dev_env.py << 'EOF'
#!/usr/bin/env python3
"""
Cherry AI Development Environment Status Check
"""
import os
import sys
import subprocess
import json
from pathlib import Path

def check_api_keys():
    """Check if API keys are configured"""
    keys = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY", 
        "GEMINI_API_KEY",
        "WEAVIATE_API_KEY",
        "PINECONE_API_KEY"
    ]
    
    print("🔑 API Keys Status:")
    for key in keys:
        value = os.getenv(key)
        if value and len(value) > 10:
            print(f"  ✅ {key}: Configured")
        else:
            print(f"  ❌ {key}: Missing or invalid")

def check_services():
    """Check if services are running"""
    print("\n🔧 Services Status:")
    
    # Check Redis
    try:
        result = subprocess.run(["redis-cli", "ping"], capture_output=True, text=True)
        if result.returncode == 0 and "PONG" in result.stdout:
            print("  ✅ Redis: Running")
        else:
            print("  ❌ Redis: Not running")
    except:
        print("  ❌ Redis: Not available")

def check_mcp_servers():
    """Check MCP server configuration"""
    print("\n🤖 MCP Servers:")
    mcp_config = Path("/workspace/.cursor/mcp.json")
    if mcp_config.exists():
        print("  ✅ MCP configuration: Found")
        try:
            with open(mcp_config) as f:
                config = json.load(f)
                servers = config.get("mcp-servers", {})
                print(f"  📊 Configured servers: {len(servers)}")
                for name in servers.keys():
                    print(f"    - {name}")
        except:
            print("  ⚠️  MCP configuration: Invalid JSON")
    else:
        print("  ❌ MCP configuration: Not found")

def main():
    print("🍒 Cherry AI Development Environment Status\n")
    check_api_keys()
    check_services()
    check_mcp_servers()
    
    print("\n🎯 Quick Commands:")
    print("  cherry-ai start-mcp  - Start MCP servers")
    print("  cherry-ai status     - Show detailed status")
    print("  cherry-ai deploy     - Deploy to production")

if __name__ == "__main__":
    main()
EOF

chmod +x /workspace/check_dev_env.py

echo "✅ Development environment status checker created"

echo ""
echo "🎉 Cherry AI Orchestrator Development Environment Setup Complete!"
echo ""
echo "📋 What's been configured:"
echo "  ✅ Environment variables exported to $EXPORT_FILE"
echo "  ✅ Python packages for AI development installed"
echo "  ✅ Cherry AI CLI tool created (cherry-ai command)"
echo "  ✅ MCP server startup scripts configured"
echo "  ✅ Cursor AI configuration optimized"
echo "  ✅ Development environment status checker"
echo ""
echo "🚀 Next steps:"
echo "  1. Restart your terminal or run: source $EXPORT_FILE"
echo "  2. Run: python /workspace/check_dev_env.py"
echo "  3. Start MCP servers: cherry-ai start-mcp"
echo "  4. Open Cursor AI and enjoy enhanced AI coding!"
echo ""
echo "🔗 Useful commands:"
echo "  cherry-ai status     - Check system status"
echo "  cherry-ai start-mcp  - Start MCP servers"
echo "  cherry-ai codex      - Use OpenAI Codex"
echo ""

