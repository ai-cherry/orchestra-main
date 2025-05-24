#!/bin/bash
# Enhanced setup script for Claude Code with MCP integration
# Optimized for AI Orchestra project goals

set -e

echo "🚀 Setting up Claude Code with MCP for AI Orchestra (Enhanced)..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Load environment variables from multiple sources
echo -e "${YELLOW}Loading environment configuration...${NC}"

# Try to load from GCP env setup
if [ -f "$HOME/.gcp_env_setup.sh" ]; then
    source "$HOME/.gcp_env_setup.sh" 2>/dev/null || true
    echo -e "${GREEN}✓ Loaded GCP environment${NC}"
fi

# Load from .env if exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
    echo -e "${GREEN}✓ Loaded .env file${NC}"
fi

# Set defaults for critical variables
export GCP_PROJECT_ID="${GCP_PROJECT_ID:-cherry-ai-project}"
export GCP_REGION="${GCP_REGION:-us-central1}"
export FIRESTORE_NAMESPACE="${FIRESTORE_NAMESPACE:-orchestra-local}"

# Verify Claude Code installation
if ! command -v claude &> /dev/null; then
    echo -e "${YELLOW}Claude Code CLI not found. Installing...${NC}"
    sudo npm install -g @anthropic-ai/claude-code
else
    echo -e "${GREEN}✓ Claude Code CLI is already installed ($(claude --version))${NC}"
fi

# Create claude config directory
CLAUDE_CONFIG_DIR="$HOME/.config/claude"
mkdir -p "$CLAUDE_CONFIG_DIR"
mkdir -p "$CLAUDE_CONFIG_DIR/logs"

# Create comprehensive MCP configuration
echo -e "${YELLOW}Creating enhanced MCP configuration...${NC}"

cat > "$CLAUDE_CONFIG_DIR/config.json" << EOF
{
  "mcpServers": {
    "gcp-cloud-run": {
      "command": "python",
      "args": [
        "$PROJECT_ROOT/mcp_server/servers/gcp_cloud_run_server.py"
      ],
      "env": {
        "GCP_PROJECT_ID": "${GCP_PROJECT_ID}",
        "GCP_REGION": "${GCP_REGION}",
        "GOOGLE_APPLICATION_CREDENTIALS": "${GOOGLE_APPLICATION_CREDENTIALS}"
      }
    },
    "gcp-secrets": {
      "command": "python",
      "args": [
        "$PROJECT_ROOT/mcp_server/servers/gcp_secret_manager_server.py"
      ],
      "env": {
        "GCP_PROJECT_ID": "${GCP_PROJECT_ID}",
        "GOOGLE_APPLICATION_CREDENTIALS": "${GOOGLE_APPLICATION_CREDENTIALS}"
      }
    },
    "dragonfly": {
      "command": "python",
      "args": [
        "$PROJECT_ROOT/mcp_server/servers/dragonfly_server.py"
      ],
      "env": {
        "DRAGONFLY_HOST": "${DRAGONFLY_HOST:-localhost}",
        "DRAGONFLY_PORT": "${DRAGONFLY_PORT:-6379}",
        "DRAGONFLY_PASSWORD": "${DRAGONFLY_PASSWORD}",
        "DRAGONFLY_DB_INDEX": "${DRAGONFLY_DB_INDEX:-0}"
      }
    },
    "firestore": {
      "command": "python",
      "args": [
        "$PROJECT_ROOT/mcp_server/servers/firestore_server.py"
      ],
      "env": {
        "GCP_PROJECT_ID": "${GCP_PROJECT_ID}",
        "FIRESTORE_NAMESPACE": "${FIRESTORE_NAMESPACE}",
        "GOOGLE_APPLICATION_CREDENTIALS": "${GOOGLE_APPLICATION_CREDENTIALS}"
      }
    },
    "qdrant": {
      "command": "python",
      "args": [
        "$PROJECT_ROOT/mcp_server/servers/qdrant_server.py"
      ],
      "env": {
        "QDRANT_HOST": "${QDRANT_HOST:-localhost}",
        "QDRANT_PORT": "${QDRANT_PORT:-6333}",
        "QDRANT_API_KEY": "${QDRANT_API_KEY}",
        "QDRANT_COLLECTION": "${QDRANT_COLLECTION:-orchestra_vectors}"
      }
    },
    "orchestrator": {
      "command": "python",
      "args": [
        "$PROJECT_ROOT/mcp_server/servers/orchestrator_server.py"
      ],
      "env": {
        "ORCHESTRATOR_API_URL": "${ORCHESTRATOR_API_URL:-http://localhost:8000}",
        "ORCHESTRATOR_API_KEY": "${ORCHESTRATOR_API_KEY}"
      }
    }
  },
  "defaultModel": "claude-4",
  "features": {
    "mcp": true,
    "codeCompletion": true,
    "diffViewer": true,
    "contextSharing": true,
    "memoryIntegration": true
  },
  "settings": {
    "autoSaveMemory": true,
    "memoryRetentionDays": 30,
    "logLevel": "info",
    "confirmDestructiveActions": true
  }
}
EOF

echo -e "${GREEN}✓ Enhanced MCP configuration created${NC}"

# Create project-specific .mcp.json with full capabilities
echo -e "${YELLOW}Creating comprehensive project MCP configuration...${NC}"

cat > "$PROJECT_ROOT/.mcp.json" << 'EOF'
{
  "name": "AI Orchestra MCP Configuration",
  "version": "2.0.0",
  "description": "Comprehensive MCP servers for AI Orchestra development with memory architecture",
  "servers": {
    "gcp-cloud-run": {
      "description": "Deploy and manage Cloud Run services",
      "capabilities": ["deploy", "update", "status", "list", "logs", "scale"],
      "requiredPermissions": ["roles/run.admin"]
    },
    "gcp-secrets": {
      "description": "Manage Google Secret Manager",
      "capabilities": ["get", "create", "update", "list", "versions"],
      "requiredPermissions": ["roles/secretmanager.admin"]
    },
    "dragonfly": {
      "description": "Short-term memory cache (DragonflyDB)",
      "capabilities": ["get", "set", "delete", "list", "ttl", "pipeline"],
      "memoryLayer": "short-term"
    },
    "firestore": {
      "description": "Mid-term episodic memory (Firestore)",
      "capabilities": ["create", "read", "update", "query", "batch", "transaction"],
      "memoryLayer": "mid-term",
      "collections": ["agent_states", "conversations", "tasks", "reflections"]
    },
    "qdrant": {
      "description": "Long-term semantic memory (Qdrant vector DB)",
      "capabilities": ["search", "upsert", "delete", "createCollection", "similarity"],
      "memoryLayer": "long-term",
      "vectorDimension": 1536
    },
    "orchestrator": {
      "description": "AI agent orchestration and mode management",
      "capabilities": ["switchMode", "runWorkflow", "getStatus", "executeTask"],
      "modes": ["code", "debug", "architect", "strategy", "ask", "creative"]
    }
  },
  "memoryArchitecture": {
    "shortTerm": {
      "provider": "DragonflyDB",
      "ttl": "1 hour",
      "purpose": "Recent agent states and temporary data"
    },
    "midTerm": {
      "provider": "Firestore",
      "retention": "30 days",
      "purpose": "Episodic memory, conversations, task history"
    },
    "longTerm": {
      "provider": "Qdrant",
      "retention": "permanent",
      "purpose": "Semantic memory, embeddings, knowledge base"
    }
  },
  "workflows": {
    "deploymentPipeline": {
      "description": "Full deployment workflow from code to production",
      "steps": ["test", "build", "deploy", "verify"]
    },
    "memoryConsolidation": {
      "description": "Consolidate short-term memories to long-term storage",
      "steps": ["extract", "embed", "store", "index"]
    }
  }
}
EOF

echo -e "${GREEN}✓ Comprehensive project configuration created${NC}"

# Create enhanced launcher script
echo -e "${YELLOW}Creating enhanced Cursor launcher...${NC}"

cat > "$PROJECT_ROOT/launch_cursor_with_claude_enhanced.sh" << 'EOF'
#!/bin/bash
# Enhanced launcher for Cursor with Claude Code and MCP servers

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 Launching AI Orchestra Development Environment${NC}"

# Load environment
echo -e "${YELLOW}Loading environment...${NC}"
source ~/.gcp_env_setup.sh 2>/dev/null || true
[ -f .env ] && source .env

# Verify critical services
echo -e "${YELLOW}Verifying services...${NC}"

# Check if MCP servers should auto-start
if [ "${MCP_AUTO_START:-true}" = "true" ]; then
    echo -e "${YELLOW}Starting MCP servers...${NC}"
    
    # Start MCP servers with proper logging
    mkdir -p logs/mcp
    
    echo "Starting Cloud Run MCP server..."
    python ~/orchestra-main/mcp_server/servers/gcp_cloud_run_server.py \
        > logs/mcp/cloud_run.log 2>&1 &
    MCP_PIDS+=($!)
    
    # Add other servers as they're implemented
    # echo "Starting Secret Manager MCP server..."
    # python ~/orchestra-main/mcp_server/servers/gcp_secret_manager_server.py \
    #     > logs/mcp/secrets.log 2>&1 &
    # MCP_PIDS+=($!)
    
    echo -e "${GREEN}✓ MCP servers started${NC}"
fi

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down MCP servers...${NC}"
    for pid in ${MCP_PIDS[@]}; do
        kill $pid 2>/dev/null || true
    done
    echo -e "${GREEN}✓ Cleanup complete${NC}"
}
trap cleanup EXIT

# Launch Cursor
echo -e "${GREEN}Launching Cursor IDE...${NC}"
cursor ~/orchestra-main

# Keep script running
wait
EOF

chmod +x "$PROJECT_ROOT/launch_cursor_with_claude_enhanced.sh"

echo -e "${GREEN}✓ Enhanced launcher created${NC}"

# Create helper scripts for common MCP operations
echo -e "${YELLOW}Creating MCP helper scripts...${NC}"

mkdir -p "$PROJECT_ROOT/scripts/mcp"

# Deploy helper
cat > "$PROJECT_ROOT/scripts/mcp/deploy_to_cloud_run.sh" << 'EOF'
#!/bin/bash
# Helper script to deploy services via MCP

SERVICE_NAME="${1:-ai-orchestra-minimal}"
IMAGE="${2:-gcr.io/${GCP_PROJECT_ID}/${SERVICE_NAME}:latest}"
MEMORY="${3:-2Gi}"

echo "Deploying $SERVICE_NAME with image $IMAGE..."
# This would be called by Claude through MCP
EOF
chmod +x "$PROJECT_ROOT/scripts/mcp/deploy_to_cloud_run.sh"

# Memory consolidation helper
cat > "$PROJECT_ROOT/scripts/mcp/consolidate_memory.sh" << 'EOF'
#!/bin/bash
# Helper script to consolidate memories across layers

echo "Consolidating memories from DragonflyDB to Firestore/Qdrant..."
# This would be called by Claude through MCP
EOF
chmod +x "$PROJECT_ROOT/scripts/mcp/consolidate_memory.sh"

echo -e "${GREEN}✓ Helper scripts created${NC}"

# Display summary and next steps
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Claude Code Enhanced Setup Complete!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}Configuration Summary:${NC}"
echo "• Claude Code CLI: $(claude --version 2>/dev/null || echo 'Installed')"
echo "• MCP Servers: 6 configured (Cloud Run, Secrets, DragonflyDB, Firestore, Qdrant, Orchestrator)"
echo "• Memory Layers: Short-term (DragonflyDB), Mid-term (Firestore), Long-term (Qdrant)"
echo "• Project: ${GCP_PROJECT_ID:-Not set}"
echo "• Region: ${GCP_REGION:-Not set}"
echo ""
echo -e "${GREEN}Quick Start:${NC}"
echo "1. Launch Cursor with MCP: ./launch_cursor_with_claude_enhanced.sh"
echo "2. In Cursor terminal: claude"
echo "3. Authenticate with Claude Max account"
echo ""
echo -e "${GREEN}Example Claude + MCP Commands:${NC}"
echo '• "Deploy the orchestrator to Cloud Run with 4GB memory"'
echo '• "Get the ANTHROPIC_API_KEY from Secret Manager"'
echo '• "Cache the current agent state in DragonflyDB"'
echo '• "Store this conversation in Firestore episodic memory"'
echo '• "Search Qdrant for similar code patterns"'
echo '• "Switch to architect mode and design the memory consolidation pipeline"'
echo ""
echo -e "${YELLOW}⚠️  Note: Some MCP servers are pending implementation${NC}"
echo "   Implemented: gcp_cloud_run_server.py"
echo "   TODO: Secret Manager, DragonflyDB, Firestore, Qdrant, Orchestrator servers"
echo "" 