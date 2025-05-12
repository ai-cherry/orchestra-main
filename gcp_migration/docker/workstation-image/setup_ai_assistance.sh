#!/bin/bash
# Setup script for AI assistance in GCP Cloud Workstations
# This script configures Roo (Claude), Cline, and Gemini Code Assist

set -e

# ANSI color codes for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display messages
info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

# Print title
echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}  AI Assistance Setup for GCP Cloud Workstations  ${NC}"
echo -e "${BLUE}===============================================${NC}"
echo

# Get GCP Project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
  error "No GCP Project ID found. Please run 'gcloud config set project YOUR_PROJECT_ID' first."
  exit 1
fi

info "Using GCP Project: $PROJECT_ID"

# Create directories
info "Creating AI assistance directories..."
mkdir -p $HOME/.ai-memory
mkdir -p $HOME/.config/Anthropic
mkdir -p $HOME/.config/Google/CloudCodeAI

# Setup MCP memory system
info "Setting up MCP memory system..."
if [ ! -f $HOME/.ai-memory/initialize.py ]; then
  cat > $HOME/.ai-memory/initialize.py << 'EOF'
#!/usr/bin/env python3
"""
MCP Memory system initializer for GCP Cloud Workstations
This script sets up the MCP memory system for AI assistants
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Create initial memory structure
memory_dir = Path.home() / ".ai-memory"
memory_dir.mkdir(exist_ok=True)

# Create memory index
memory_index = {
    "version": "1.0",
    "created": datetime.now().isoformat(),
    "environment": "gcp-workstation",
    "memory_format": "vector",
    "memory_location": "firestore",
    "project_id": os.environ.get("GCP_PROJECT_ID", ""),
    "storage_options": {
        "persistent": True,
        "encrypted": True,
        "geo_redundant": True
    },
    "assistants": [
        {
            "name": "gemini",
            "type": "code-assist",
            "provider": "google",
            "enabled": True
        },
        {
            "name": "roo",
            "type": "chat",
            "provider": "anthropic",
            "enabled": True
        },
        {
            "name": "cline",
            "type": "chat",
            "provider": "anthropic",
            "enabled": True
        }
    ]
}

# Write memory index
with open(memory_dir / "memory_index.json", "w") as f:
    json.dump(memory_index, f, indent=2)

print(f"MCP Memory system initialized at {memory_dir}")

# Create project structure record
project_structure = {
    "version": "1.0",
    "created": datetime.now().isoformat(),
    "repository": os.environ.get("GITHUB_REPOSITORY", ""),
    "project_id": os.environ.get("GCP_PROJECT_ID", ""),
    "environment": "gcp-workstation"
}

# Write project structure
with open(memory_dir / "project_structure.json", "w") as f:
    json.dump(project_structure, f, indent=2)

print("Project structure recorded")
print("MCP Memory system is ready to use")
EOF

  chmod +x $HOME/.ai-memory/initialize.py
  success "Created MCP memory initializer"
fi

# Run MCP memory initializer
info "Initializing MCP memory system..."
export GCP_PROJECT_ID="$PROJECT_ID"
python3 $HOME/.ai-memory/initialize.py
success "MCP memory system initialized"

# Setup Gemini Code Assist
info "Setting up Gemini Code Assist..."

# Copy Gemini Code Assist configuration
GEMINI_CONFIG_SRC="/home/user/persistent/ai-orchestra/gcp_migration/docker/workstation-image/gemini-code-assist.yaml"
GEMINI_CONFIG_DEST="$HOME/.config/Google/CloudCodeAI/gemini-code-assist.yaml"

if [ -f "$GEMINI_CONFIG_SRC" ]; then
  # Replace GCP_PROJECT_ID with actual project ID
  cat "$GEMINI_CONFIG_SRC" | sed "s/\${GCP_PROJECT_ID}/$PROJECT_ID/g" > "$GEMINI_CONFIG_DEST"
  success "Gemini Code Assist configured with project ID: $PROJECT_ID"
else
  # Create config directly if source doesn't exist
  warn "Gemini config source not found, creating directly..."
  mkdir -p "$(dirname "$GEMINI_CONFIG_DEST")"
  cat > "$GEMINI_CONFIG_DEST" << EOF
# Optimized Gemini Code Assist configuration for GCP Cloud Workstations
general:
  telemetry:
    enabled: false
  contexts:
    maxContexts: 10
    contextSize: 3000

api:
  endpoint: "https://us-central1-aiplatform.googleapis.com/v1/projects/$PROJECT_ID/locations/us-central1/publishers/google/models/gemini-1.5-pro:streamGenerateContent"
  authentication: "ADC"
  rateLimit:
    enabled: false

model:
  name: "gemini-1.5-pro"
  temperature: 0.3
  tokenLimit:
    input: 150000
    output: 50000

vertexAi:
  enabled: true
  region: "us-central1"
  projectId: "$PROJECT_ID"

security:
  mcpMemory:
    enabled: true
    path: "$HOME/.ai-memory"
EOF
  success "Basic Gemini Code Assist configuration created"
fi

# Setup Claude (Roo) configuration
info "Setting up Claude (Roo) configuration..."
CLAUDE_CONFIG_FILE="$HOME/.config/Anthropic/config.json"

mkdir -p "$(dirname "$CLAUDE_CONFIG_FILE")"
cat > "$CLAUDE_CONFIG_FILE" << EOF
{
  "apiKey": "sk-secret-access-via-gcp-secret-manager",
  "useSecretManager": true,
  "secretName": "ANTHROPIC_API_KEY",
  "gcpProject": "$PROJECT_ID",
  "mcpMemoryEnabled": true,
  "mcpMemoryPath": "$HOME/.ai-memory",
  "telemetryEnabled": false,
  "contextSize": 100000,
  "temperature": 0.3,
  "modelName": "claude-3-opus-20240229"
}
EOF

success "Claude (Roo) configured to use GCP Secret Manager"

# Create a helper script to retrieve secrets from Secret Manager
info "Creating Secret Manager helper script..."
SECRET_HELPER_SCRIPT="$HOME/bin/get-secret.sh"

mkdir -p "$(dirname "$SECRET_HELPER_SCRIPT")"
cat > "$SECRET_HELPER_SCRIPT" << EOF
#!/bin/bash
# Helper script to retrieve secrets from Secret Manager

if [ -z "\$1" ]; then
  echo "Usage: \$0 SECRET_NAME [PROJECT_ID]"
  exit 1
fi

SECRET_NAME="\$1"
PROJECT_ID="\${2:-$PROJECT_ID}"

gcloud secrets versions access latest --secret="\$SECRET_NAME" --project="\$PROJECT_ID"
EOF

chmod +x "$SECRET_HELPER_SCRIPT"
success "Secret Manager helper script created at $SECRET_HELPER_SCRIPT"

# Create AI assistance test script 
info "Creating AI assistance test script..."
TEST_SCRIPT="$HOME/test-ai-assistance.sh"

cat > "$TEST_SCRIPT" << 'EOF'
#!/bin/bash
# Test AI assistance setup in Cloud Workstation

# ANSI color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Testing AI assistance setup...${NC}"

# 1. Test MCP memory system
echo -e "${YELLOW}Testing MCP memory system...${NC}"
if [ -f "$HOME/.ai-memory/memory_index.json" ]; then
    echo -e "${GREEN}✓ MCP memory system found${NC}"
else
    echo -e "${RED}✗ MCP memory system not found${NC}"
fi

# 2. Test Gemini Code Assist
echo -e "${YELLOW}Testing Gemini Code Assist configuration...${NC}"
if [ -f "$HOME/.config/Google/CloudCodeAI/gemini-code-assist.yaml" ]; then
    echo -e "${GREEN}✓ Gemini Code Assist configuration found${NC}"
    PROJECT_ID=$(grep "projectId:" "$HOME/.config/Google/CloudCodeAI/gemini-code-assist.yaml" | awk '{print $2}' | tr -d '"')
    if [ -n "$PROJECT_ID" ]; then
        echo -e "${GREEN}✓ Project ID in Gemini config: $PROJECT_ID${NC}"
    else
        echo -e "${RED}✗ Project ID not found in Gemini config${NC}"
    fi
else
    echo -e "${RED}✗ Gemini Code Assist configuration not found${NC}"
fi

# 3. Test Claude (Roo) configuration
echo -e "${YELLOW}Testing Claude (Roo) configuration...${NC}"
if [ -f "$HOME/.config/Anthropic/config.json" ]; then
    echo -e "${GREEN}✓ Claude configuration found${NC}"
    SECRET_MANAGER_ENABLED=$(grep "useSecretManager" "$HOME/.config/Anthropic/config.json" | grep -q "true" && echo "yes" || echo "no")
    if [ "$SECRET_MANAGER_ENABLED" = "yes" ]; then
        echo -e "${GREEN}✓ Claude configured to use Secret Manager${NC}"
    else
        echo -e "${RED}✗ Claude not configured to use Secret Manager${NC}"
    fi
else
    echo -e "${RED}✗ Claude configuration not found${NC}"
fi

# 4. Test Secret Manager access
echo -e "${YELLOW}Testing Secret Manager access...${NC}"
if command -v gcloud &> /dev/null; then
    echo -e "${GREEN}✓ gcloud command found${NC}"
    
    # Test project access
    PROJECT_ACCESS=$(gcloud projects describe $(gcloud config get-value project 2>/dev/null) 2>&1 >/dev/null && echo "yes" || echo "no")
    if [ "$PROJECT_ACCESS" = "yes" ]; then
        echo -e "${GREEN}✓ GCP project access verified${NC}"
    else
        echo -e "${RED}✗ GCP project access failed${NC}"
    fi
    
    # Test Secret Manager API
    SM_ENABLED=$(gcloud services list --enabled --filter="secretmanager.googleapis.com" 2>/dev/null | grep -q "secretmanager.googleapis.com" && echo "yes" || echo "no")
    if [ "$SM_ENABLED" = "yes" ]; then
        echo -e "${GREEN}✓ Secret Manager API enabled${NC}"
    else
        echo -e "${RED}✗ Secret Manager API not enabled${NC}"
        echo -e "${YELLOW}→ Run: gcloud services enable secretmanager.googleapis.com${NC}"
    fi
else
    echo -e "${RED}✗ gcloud command not found${NC}"
fi

# 5. Test VSCode extensions
echo -e "${YELLOW}Testing VSCode extensions...${NC}"
if command -v code-server &> /dev/null; then
    CLAUDE_EXT=$(code-server --list-extensions | grep -q "anthropic.claude" && echo "yes" || echo "no")
    if [ "$CLAUDE_EXT" = "yes" ]; then
        echo -e "${GREEN}✓ Claude (Roo) extension installed${NC}"
    else
        echo -e "${RED}✗ Claude extension not installed${NC}"
        echo -e "${YELLOW}→ Run: code-server --install-extension anthropic.claude${NC}"
    fi
    
    GEMINI_EXT=$(code-server --list-extensions | grep -q "google.cloud-code-ai" && echo "yes" || echo "no")
    if [ "$GEMINI_EXT" = "yes" ]; then
        echo -e "${GREEN}✓ Gemini Code Assist extension installed${NC}"
    else
        echo -e "${RED}✗ Gemini Code Assist extension not installed${NC}"
        echo -e "${YELLOW}→ Run: code-server --install-extension google.cloud-code-ai${NC}"
    fi
else
    echo -e "${RED}✗ code-server command not found${NC}"
fi

echo -e "${BLUE}AI assistance test complete!${NC}"
EOF

chmod +x "$TEST_SCRIPT"
success "AI assistance test script created at $TEST_SCRIPT"

# Run the test script
info "Running AI assistance test..."
$TEST_SCRIPT

echo
echo -e "${BLUE}===============================================${NC}"
echo -e "${GREEN}  AI Assistance Setup Complete!  ${NC}"
echo -e "${BLUE}===============================================${NC}"
echo
echo -e "To ensure API keys are properly configured, run:"
echo -e "  1. ${YELLOW}./scripts/sync_github_to_gcp_secrets.sh${NC}"
echo -e "  2. Verify your secrets in GCP Secret Manager"
echo
echo -e "If you need to test your setup:"
echo -e "  ${YELLOW}~/test-ai-assistance.sh${NC}"
echo
success "Your AI assistance is ready for use in GCP Cloud Workstations!"
