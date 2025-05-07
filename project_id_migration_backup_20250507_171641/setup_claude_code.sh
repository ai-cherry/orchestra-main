#!/bin/bash
# setup_claude_code.sh
#
# Script for installing and configuring Claude Code for GCP project management
# This allows integration of AI assistance into your GCP project workflows
# Compatible with Max plan subscriptions (5x and 20x Pro tiers)

set -e

# Colors for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===== Claude Code Setup for GCP Project Management =====${NC}"

# -----[ Step 1: Check Node.js installation ]-----
echo -e "\n${YELLOW}Step 1: Checking Node.js installation${NC}"

if ! command -v node &> /dev/null; then
  echo -e "${BLUE}Node.js not found. Installing Node.js...${NC}"
  
  # Install Node.js using NVM (Node Version Manager)
  echo -e "${BLUE}Installing NVM...${NC}"
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash
  
  # Load NVM
  export NVM_DIR="$HOME/.nvm"
  [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
  
  # Install latest LTS version of Node.js
  echo -e "${BLUE}Installing Node.js LTS...${NC}"
  nvm install --lts
  
  echo -e "${GREEN}✅ Node.js installed successfully${NC}"
else
  NODE_VERSION=$(node -v)
  echo -e "${GREEN}✅ Node.js is already installed (version: $NODE_VERSION)${NC}"
fi

# -----[ Step 2: Install Claude Code ]-----
echo -e "\n${YELLOW}Step 2: Installing Claude Code${NC}"

if ! command -v claude &> /dev/null; then
  echo -e "${BLUE}Installing Claude Code globally...${NC}"
  npm install -g @anthropic-ai/claude-code
  
  echo -e "${GREEN}✅ Claude Code installed successfully${NC}"
else
  CLAUDE_VERSION=$(claude --version 2>/dev/null || echo "Unknown")
  echo -e "${GREEN}✅ Claude Code is already installed (version: $CLAUDE_VERSION)${NC}"
  
  echo -e "${BLUE}Updating Claude Code to the latest version...${NC}"
  npm update -g @anthropic-ai/claude-code
  
  echo -e "${GREEN}✅ Claude Code updated successfully${NC}"
fi

# -----[ Step 3: Create Claude.md for project memory ]-----
echo -e "\n${YELLOW}Step 3: Creating project memory${NC}"

if [ ! -f "CLAUDE.md" ]; then
  echo -e "${BLUE}Creating CLAUDE.md project memory file...${NC}"
  
  cat > CLAUDE.md <<'EOF'
# AGI Baby Cherry Project Memory

## GCP Project Configuration

- Project ID: agi-baby-cherry
- Organization ID: 873291114285
- Service Account: vertex-agent@agi-baby-cherry.iam.gserviceaccount.com

## Critical Migration Information

- Always use numeric organization ID: 873291114285
- Required IAM propagation delay: 5 minutes
- Critical roles: resourcemanager.projectMover, resourcemanager.projectCreator

## Cloud Workstation Configuration

- Machine type: n2d-standard-32
- GPU: 2x NVIDIA Tesla T4
- Persistent storage: 1TB SSD
- Location: us-central1

## Connected Services

- Vertex AI endpoint: projects/agi-baby-cherry/locations/us-central1/endpoints/agent-core
- Redis instance: agent-memory.redis.us-central1.cherry-ai.cloud.goog:6379
- AlloyDB cluster: postgresql://alloydb-user@agent-storage:5432/agi_baby_cherry

## Common Tasks

- Verify project migration:
  ```bash
  gcloud projects describe agi-baby-cherry --format="value(parent.id)"
  ```

- Check workstation status:
  ```bash
  gcloud workstations list --project=agi-baby-cherry
  ```

- Connect to Redis:
  ```bash
  redis-cli -h agent-memory.redis.us-central1.cherry-ai.cloud.goog
  ```

- Optimize Terraform:
  ```
  Prefer using google-beta provider for workstations
  Configure shielded VM options for security
  Set proper boot disk size (min 500GB)
  ```
EOF
  
  echo -e "${GREEN}✅ CLAUDE.md created successfully${NC}"
else
  echo -e "${BLUE}CLAUDE.md already exists. Skipping creation.${NC}"
fi

# -----[ Step 4: Set up Claude Code configuration ]-----
echo -e "\n${YELLOW}Step 4: Setting up Claude Code configuration${NC}"

mkdir -p ~/.claude

if [ ! -f "~/.claude/config.json" ]; then
  echo -e "${BLUE}Creating Claude Code configuration...${NC}"
  
  cat > ~/.claude/config.json <<'EOF'
{
  "theme": "dark",
  "defaultAllowedTools": [
    "Ask",
    "Browse",
    "Bash(gcloud:*)",
    "Bash(terraform:*)",
    "Write",
    "Read"
  ],
  "defaultDisallowedTools": []
}
EOF
  
  echo -e "${GREEN}✅ Claude Code configuration created successfully${NC}"
else
  echo -e "${BLUE}Claude Code configuration already exists. Skipping creation.${NC}"
fi

# -----[ Final Steps ]-----
echo -e "\n${YELLOW}Claude Code Setup Complete${NC}"
echo -e "${BLUE}To start using Claude Code:${NC}"
echo -e "  1. Navigate to your project directory: cd /workspaces/orchestra-main"
echo -e "  2. Run 'claude' to start the interactive prompt"
echo -e "  3. Use '/init' to initialize the project with Claude"
echo -e "  4. Try commands like 'verify our GCP migration' or 'optimize our Terraform config'"

echo -e "\n${YELLOW}Claude Code Benefits for Migration${NC}"
echo -e "  • Pre-migration analysis: Checks for potential blockers"
echo -e "  • IAM troubleshooting: Advanced permission diagnostics"
echo -e "  • Migration verification: Comprehensive checks across GCP services"
echo -e "  • Terraform optimization: Performance and cost improvements"
echo -e "  • Automated monitoring: Generate monitoring dashboards"

echo -e "\n${YELLOW}Max Plan Rate Limits${NC}"
echo -e "  • Standard Max Plan ($100): ~225 messages or 10-20 coding tasks per 5 hours"
echo -e "  • Enhanced Max Plan ($200): ~900 messages or 40-80 coding tasks per 5 hours"

echo -e "\n${GREEN}Use 'claude help' for more information on all available commands${NC}"
