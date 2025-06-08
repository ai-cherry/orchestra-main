#!/bin/bash

echo "🚀 SETTING UP CURSOR AI OPTIMIZATION..."

# Create Cursor AI directory structure
echo "Creating Cursor AI directory structure..."
mkdir -p .cursor/rules/projects/{admin-interface,infrastructure,backend}

# Create optimized .cursorignore
echo "Creating optimized .cursorignore..."
cat > .cursor/.cursorignore << 'EOF'
# Performance optimization for large monorepo
node_modules/
dist/
build/
.git/
*.log
coverage/
.next/
.nuxt/
vendor/
*.cache
tmp/
.env*

# Project-specific large files
data/
uploads/
storage/

# Cloud/Infrastructure artifacts
terraform.tfstate*
pulumi.*.yaml
.pulumi/

# IDE artifacts
.vscode/
.idea/

# Language-specific
__pycache__/
*.pyc
target/
pkg/

# Cleanup artifacts
.roo/
.roomodes*
roo_integration.db
EOF

# Create MCP configuration
echo "Creating MCP server configuration..."
cat > .cursor/mcp.json << 'EOF'
{
  "mcpServers": {
    "pulumi": {
      "type": "stdio",
      "command": "npx",
      "args": ["@pulumi/mcp-server"],
      "priority": "critical",
      "description": "Infrastructure as Code acceleration"
    },
    "sequential_thinking": {
      "type": "stdio",
      "command": "npx",
      "args": ["@modelcontextprotocol/server-sequential-thinking"],
      "priority": "high",
      "description": "Complex task breakdown and workflow management"
    },
    "github": {
      "type": "stdio",
      "command": "npx",
      "args": ["@modelcontextprotocol/server-github"],
      "priority": "high",
      "description": "CI/CD integration and repository management"
    },
    "filesystem": {
      "type": "stdio",
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem"],
      "priority": "medium",
      "description": "Advanced file operations"
    },
    "puppeteer": {
      "type": "stdio",
      "command": "npx",
      "args": ["@modelcontextprotocol/server-puppeteer"],
      "priority": "medium",
      "description": "Browser automation and testing"
    }
  }
}
EOF

echo "✅ CURSOR AI OPTIMIZATION SETUP COMPLETE!"
echo ""
echo "📋 NEXT STEPS:"
echo "1. Install MCP servers: npx @pulumi/mcp-server"
echo "2. Configure Cursor AI rules in .cursor/rules/"
echo "3. Restart Cursor IDE to apply changes"

