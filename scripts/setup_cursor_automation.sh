#!/bin/bash
# 🧠 Cursor AI Automation Setup Script
# Configures Cursor AI for complete Orchestra AI integration

set -e

echo "🚀 Setting up Cursor AI Automation for Orchestra AI"
echo "=================================================="

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CURSOR_CONFIG_DIR="$HOME/.cursor"

# Create Cursor config directory if it doesn't exist
mkdir -p "$CURSOR_CONFIG_DIR"

echo "📁 Project root: $PROJECT_ROOT"
echo "🔧 Cursor config: $CURSOR_CONFIG_DIR"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get secret from fast_secrets.py
get_secret() {
    python3 -c "
import sys
sys.path.append('$PROJECT_ROOT')
from utils.fast_secrets import secrets
print(secrets.get('$1', '$2'))
" 2>/dev/null || echo ""
}

echo "🔐 Validating secrets configuration..."

# Check if fast_secrets.py exists
if [ ! -f "$PROJECT_ROOT/utils/fast_secrets.py" ]; then
    echo "❌ fast_secrets.py not found. Please ensure secrets are configured."
    exit 1
fi

# Validate required secrets
NOTION_TOKEN=$(get_secret "notion" "api_token")
OPENAI_KEY=$(get_secret "openai" "api_key")
VERCEL_TOKEN=$(get_secret "vercel" "api_key")

if [ -z "$NOTION_TOKEN" ] || [ -z "$OPENAI_KEY" ]; then
    echo "❌ Required secrets not configured. Run: ./scripts/quick_production_setup.sh"
    exit 1
fi

echo "✅ Secrets validation passed"

# Create advanced MCP configuration
echo "🔧 Creating MCP configuration..."

cat > "$CURSOR_CONFIG_DIR/mcp.json" << EOF
{
  "mcpServers": {
    "orchestra-unified": {
      "command": "python",
      "args": ["$PROJECT_ROOT/mcp_unified_server.py"],
      "env": {
        "NOTION_API_TOKEN": "$NOTION_TOKEN",
        "OPENAI_API_KEY": "$OPENAI_KEY",
        "ANTHROPIC_API_KEY": "$(get_secret "anthropic" "api_key")",
        "OPENROUTER_API_KEY": "$(get_secret "openrouter" "api_key")"
      }
    },
    "infrastructure-deployment": {
      "command": "python",
      "args": ["$PROJECT_ROOT/infrastructure_deployment_server.py"],
      "env": {
        "VERCEL_TOKEN": "$VERCEL_TOKEN",
        "LAMBDA_LABS_API_KEY": "$(get_secret "lambda_labs" "api_key")",
        "PULUMI_ACCESS_TOKEN": "$(get_secret "pulumi" "access_token")"
      }
    }
  }
}
EOF

echo "✅ MCP configuration created"

# Create Cursor AI automation rules
echo "🤖 Creating automation rules..."

cat > "$CURSOR_CONFIG_DIR/automation_rules.json" << EOF
{
  "auto_approval": {
    "enabled": true,
    "safe_operations": [
      "read_file",
      "list_dir",
      "grep_search",
      "file_search", 
      "web_search",
      "get_memory_status",
      "get_infrastructure_status",
      "chat_with_persona",
      "cross_domain_query",
      "get_notion_workspace",
      "log_insight"
    ],
    "manual_approval_required": [
      "edit_file",
      "delete_file",
      "run_terminal_cmd",
      "deploy_vercel_frontend",
      "manage_lambda_labs_instance",
      "rollback_deployment"
    ],
    "batch_approval": {
      "enabled": true,
      "max_operations": 10,
      "timeout_seconds": 30
    }
  },
  "context_awareness": {
    "auto_load_project_context": true,
    "remember_conversation_history": true,
    "use_mcp_servers": true,
    "smart_routing": {
      "enabled": true,
      "persona_routing": {
        "financial_tasks": "sophia",
        "medical_tasks": "karen",
        "coordination_tasks": "cherry"
      }
    }
  },
  "development_workflow": {
    "auto_format_code": true,
    "auto_fix_imports": true,
    "use_fast_secrets": true,
    "enforce_type_hints": true
  },
  "performance_optimization": {
    "parallel_tool_calls": true,
    "cache_responses": true,
    "batch_similar_operations": true
  }
}
EOF

echo "✅ Automation rules created"

# Create project-specific Cursor settings
echo "⚙️ Creating project settings..."

mkdir -p "$PROJECT_ROOT/.cursor"

cat > "$PROJECT_ROOT/.cursor/settings.json" << EOF
{
  "orchestra_ai": {
    "project_type": "ai_orchestration_platform",
    "architecture": "microservices",
    "primary_languages": ["python", "typescript"],
    "frameworks": ["fastapi", "react", "vite"],
    "infrastructure": ["vercel", "lambda_labs", "pulumi"],
    "ai_services": ["openai", "anthropic", "openrouter"],
    "personas": {
      "cherry": "cross_domain_coordination",
      "sophia": "financial_services_expert",
      "karen": "medical_coding_specialist"
    }
  },
  "automation": {
    "secrets_manager": "$PROJECT_ROOT/utils/fast_secrets.py",
    "mcp_servers": ["orchestra-unified", "infrastructure-deployment"],
    "auto_approval_enabled": true,
    "context_awareness_enabled": true
  }
}
EOF

echo "✅ Project settings created"

# Create enhanced .cursorignore
echo "🚫 Creating enhanced .cursorignore..."

cat > "$PROJECT_ROOT/.cursorignore" << EOF
# Secrets and sensitive files
.env
.env.*
*.key
*.pem
*.p12
*.pfx
secrets/
config/secrets/

# Build and cache directories
node_modules/
.next/
dist/
build/
.cache/
.vite/
__pycache__/
*.pyc
.pytest_cache/

# Database and logs
*.db
*.sqlite
*.log
logs/
weaviate-data/

# Temporary and backup files
*.tmp
*.temp
*.backup
*.old
syntax_backup_*/

# IDE and system files
.DS_Store
.vscode/
*.swp
*.swo

# Large data files
*.csv
*.json.gz
*.parquet
data/
datasets/

# Documentation that doesn't need context
docs/archive/
*.pdf
*.docx
EOF

echo "✅ Enhanced .cursorignore created"

# Test MCP server connectivity
echo "🔍 Testing MCP server connectivity..."

if command_exists python3; then
    # Test if MCP servers can start
    echo "Testing orchestra-unified server..."
    timeout 5 python3 "$PROJECT_ROOT/mcp_unified_server.py" --test 2>/dev/null && echo "✅ Orchestra unified server OK" || echo "⚠️ Orchestra unified server may need attention"
    
    echo "Testing infrastructure deployment server..."
    timeout 5 python3 "$PROJECT_ROOT/infrastructure_deployment_server.py" --test 2>/dev/null && echo "✅ Infrastructure deployment server OK" || echo "⚠️ Infrastructure deployment server may need attention"
else
    echo "⚠️ Python3 not found, skipping MCP server tests"
fi

# Create startup script for development
echo "🚀 Creating development startup script..."

cat > "$PROJECT_ROOT/start_cursor_development.sh" << EOF
#!/bin/bash
# 🚀 Start Orchestra AI development environment with Cursor AI

echo "🚀 Starting Orchestra AI Development Environment"
echo "=============================================="

cd "$PROJECT_ROOT"

# Start API service in background
echo "🔌 Starting API service..."
uvicorn src.api.main:app --host 0.0.0.0 --port 8010 &
API_PID=\$!

# Start admin interface in background  
echo "🌐 Starting admin interface..."
cd admin-interface
npm run dev &
ADMIN_PID=\$!

cd "$PROJECT_ROOT"

echo "✅ Services started:"
echo "   🔌 API: http://localhost:8010"
echo "   🌐 Admin: http://localhost:5174"
echo "   📝 Notion: https://www.notion.so/Orchestra-AI-Workspace-20bdba04940280ca9ba7f9bce721f547"

echo ""
echo "🧠 Cursor AI is configured with:"
echo "   ✅ Auto-approval for safe operations"
echo "   ✅ Context awareness enabled"
echo "   ✅ MCP servers: orchestra-unified, infrastructure-deployment"
echo "   ✅ Smart persona routing"
echo "   ✅ Fast secrets integration"

echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap 'echo "Stopping services..."; kill \$API_PID \$ADMIN_PID 2>/dev/null; exit' INT
wait
EOF

chmod +x "$PROJECT_ROOT/start_cursor_development.sh"

echo "✅ Development startup script created"

# Final validation
echo "🔍 Final validation..."

# Check if all config files were created
CONFIG_FILES=(
    "$CURSOR_CONFIG_DIR/mcp.json"
    "$CURSOR_CONFIG_DIR/automation_rules.json"
    "$PROJECT_ROOT/.cursor/settings.json"
    "$PROJECT_ROOT/.cursorignore"
    "$PROJECT_ROOT/start_cursor_development.sh"
)

ALL_GOOD=true
for file in "${CONFIG_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file"
        ALL_GOOD=false
    fi
done

if [ "$ALL_GOOD" = true ]; then
    echo ""
    echo "🎉 Cursor AI Automation Setup Complete!"
    echo "======================================"
    echo ""
    echo "🧠 Cursor AI is now configured with:"
    echo "   ✅ Complete Orchestra AI context awareness"
    echo "   ✅ Auto-approval for safe operations"
    echo "   ✅ Smart persona routing (Cherry, Sophia, Karen)"
    echo "   ✅ Infrastructure deployment automation"
    echo "   ✅ Fast secrets integration"
    echo "   ✅ Notion workspace integration"
    echo ""
    echo "🚀 To start development:"
    echo "   ./start_cursor_development.sh"
    echo ""
    echo "🎯 Cursor AI will now:"
    echo "   • Automatically understand project context"
    echo "   • Route tasks to appropriate AI personas"
    echo "   • Auto-approve safe operations"
    echo "   • Use centralized secrets management"
    echo "   • Log important operations to Notion"
    echo ""
    echo "Ready for maximum AI-assisted productivity! 🚀"
else
    echo ""
    echo "❌ Setup incomplete. Please check the errors above."
    exit 1
fi 