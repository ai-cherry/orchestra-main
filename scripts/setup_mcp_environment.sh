#!/bin/bash
# Setup MCP environment and verify connections

echo "🚀 Setting up MCP environment for AI conductor"
echo "================================================"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "✓ Virtual environment found"
    source venv/bin/activate
else
    echo "Creating new virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✓ Virtual environment created and activated"
fi

# Upgrade pip to avoid the broken pip issue
echo -e "\n📦 Upgrading pip..."
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
rm get-pip.py

# Install requirements
echo -e "\n📦 Installing requirements..."
pip install -r requirements/production/requirements.txt

# Verify MCP installation
echo -e "\n🔍 Verifying MCP installation..."
python -c "
import mcp
print(f'✓ MCP version: {mcp.__version__}')
"

# Set up environment variables
echo -e "\n🔐 Setting up environment variables..."
cat > .env.example << 'EOF'
# API Keys
OPENROUTER_API_KEY=your-openrouter-api-key
API_KEY=your-api-key

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=cherry_ai
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-postgres-password

# Weaviate Configuration
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
WEAVIATE_API_KEY=your-weaviate-api-key

# API Configuration
API_URL=http://localhost:8080

# MCP Server Ports
CHERRY_AI_CONDUCTOR_PORT=8002
MCP_MEMORY_PORT=8003
MCP_WEAVIATE_DIRECT_PORT=8001
MCP_DEPLOYMENT_PORT=8005
MCP_TOOLS_PORT=8006
EOF

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ Created .env file from template"
    echo "⚠️  Please update .env with your actual credentials"
else
    echo "✓ .env file already exists"
fi

# Create MCP server launcher
echo -e "\n📝 Creating MCP server launcher..."
cat > scripts/start_mcp_servers.py << 'EOF'
#!/usr/bin/env python3
"""
Start MCP servers for AI conductor
"""
import os
import sys
import asyncio
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def start_server(name, command, args):
    """Start an MCP server"""
    print(f"Starting {name} server...")
    try:
        env = os.environ.copy()
        process = subprocess.Popen(
            [command] + args,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return process
    except Exception as e:
        print(f"Failed to start {name}: {e}")
        return None

async def main():
    """Main function to start all MCP servers"""
    servers = []
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Server configurations from .mcp.json
    server_configs = [
        ("conductor", "python", ["mcp_server/servers/conductor_server.py"]),
        ("memory", "python", ["mcp_server/servers/memory_server.py"]),
        ("weaviate", "python", ["mcp_server/servers/weaviate_direct_mcp_server.py"]),
        ("deployment", "python", ["mcp_server/servers/deployment_server.py"]),
        ("tools", "python", ["mcp_server/servers/tools_server.py"])
    ]
    
    # Start all servers
    for name, command, args in server_configs:
        process = start_server(name, command, args)
        if process:
            servers.append((name, process))
    
    print(f"\n✓ Started {len(servers)} MCP servers")
    print("\nPress Ctrl+C to stop all servers")
    
    try:
        # Keep running
        while True:
            await asyncio.sleep(1)
            # Check if any server has died
            for name, process in servers:
                if process.poll() is not None:
                    print(f"\n⚠️  {name} server stopped with code {process.returncode}")
    except KeyboardInterrupt:
        print("\n\nStopping all servers...")
        for name, process in servers:
            process.terminate()
        print("✓ All servers stopped")

if __name__ == "__main__":
    asyncio.run(main())
EOF

chmod +x scripts/start_mcp_servers.py

# Run verification
echo -e "\n🔍 Running final verification..."
python scripts/verify_conductor_mcp_connection.py

echo -e "\n✅ Setup complete!"
echo "Next steps:"
echo "1. Update .env with your actual credentials"
echo "2. Start MCP servers: python scripts/start_mcp_servers.py"
echo "3. Use the conductor CLI: python ai_components/conductor_cli_enhanced.py"