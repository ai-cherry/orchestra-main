#!/bin/bash
# Performance-optimized startup script for GCP Cloud Workstations
# This script initializes the workstation environment with optimal settings

set -e

# ANSI color codes for prettier output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Echo helpers
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

# Print banner
echo -e "${CYAN}"
echo '  _____                   ___                         ___           __         __  _           '
echo ' / ___/__  __ _  ___ ___ /   \ _______  ___ __  ___ / _ \_______  / /_______ / /_(_)___ ___   '
echo '/ (_ / _ \/  '"'"' \/ -_) -_) |) / __/ _ \/ __/ / / _ \ /_\ / __/ / / __/ -_) __/ / / _ `/ _ \'
echo '\___/ .__/_/_/_/\__/\__/___/\__/\__\_, /\__/_/ \___//   /_/   /_/_/  \__/\__/_/_/_/\_, / .__/'
echo '   /_/                            /___/                                            /___/_/    '
echo -e "${NC}"
echo -e "${BLUE}Performance-Optimized GCP Workstation Environment${NC}"
echo -e "${BLUE}=============================================${NC}"

# Log startup time
info "Starting environment initialization at $(date)"

# Create directories if they don't exist
info "Setting up directory structure..."
mkdir -p /home/user/persistent/ai-orchestra
mkdir -p /home/user/persistent/.cache/{pip,npm,yarn}
mkdir -p /home/user/persistent/.vscode-server/data/Machine
mkdir -p /home/user/.ai-memory

# Apply performance optimizations
info "Applying system performance optimizations..."

# Adjust Linux kernel parameters for development workloads
sudo sysctl -w vm.swappiness=10 >/dev/null 2>&1 || warn "Could not set vm.swappiness"
sudo sysctl -w vm.vfs_cache_pressure=50 >/dev/null 2>&1 || warn "Could not set vm.vfs_cache_pressure"
sudo sysctl -w fs.inotify.max_user_watches=524288 >/dev/null 2>&1 || warn "Could not set fs.inotify.max_user_watches"
sudo sysctl -w net.core.somaxconn=65535 >/dev/null 2>&1 || warn "Could not set net.core.somaxconn"

# Create .gitconfig with performance optimizations if it doesn't exist
if [ ! -f /home/user/.gitconfig ]; then
  info "Creating optimized git configuration..."
  cat > /home/user/.gitconfig << EOF
[core]
    preloadindex = true
    fscache = true
    fsmonitor = true
    editor = code --wait
[fetch]
    parallel = 8
    prune = true
[feature]
    manyFiles = true
[pack]
    threads = 8
[http]
    postBuffer = 524288000
[pull]
    rebase = true
[push]
    default = current
[credential]
    helper = store
[init]
    defaultBranch = main
[gc]
    auto = 256
[protocol]
    version = 2
EOF
  success "Created optimized git configuration"
fi

# Setup the Python environment
info "Setting up Python environment..."
if [ ! -d /home/user/persistent/.venv ]; then
  python3 -m venv /home/user/persistent/.venv
  source /home/user/persistent/.venv/bin/activate
  pip install --upgrade pip setuptools wheel
  success "Created new Python virtual environment"
else
  source /home/user/persistent/.venv/bin/activate
  success "Using existing Python virtual environment"
fi

# Add venv activation to shell rc files if not already there
for RC_FILE in /home/user/.bashrc /home/user/.zshrc; do
  if [ -f "$RC_FILE" ] && ! grep -q "source /home/user/persistent/.venv/bin/activate" "$RC_FILE"; then
    echo "# Auto-activate Python virtual environment" >> "$RC_FILE"
    echo "source /home/user/persistent/.venv/bin/activate" >> "$RC_FILE"
    success "Added venv activation to $(basename "$RC_FILE")"
  fi
done

# Configure Firestore memory settings if .ai-memory config file doesn't exist
if [ ! -f /home/user/.ai-memory/config.json ]; then
  info "Setting up AI memory configuration..."
  mkdir -p /home/user/.ai-memory
  cat > /home/user/.ai-memory/config.json << EOF
{
  "provider": "firestore",
  "collection": "ai_memory",
  "project_id": "cherry-ai-project",
  "cache_enabled": true,
  "cache_ttl": 300,
  "performance_mode": true
}
EOF
  success "Created AI memory configuration"
fi

# Setup Gemini Code Assist if configuration doesn't exist
if [ ! -f /home/user/.gemini-code-assist.yaml ]; then
  info "Setting up Gemini Code Assist configuration..."
  # Default to placeholder - actual values need to be filled in later
  cat > /home/user/.gemini-code-assist.yaml << EOF
# Performance-optimized Gemini configuration for GCP Workstations
model:
  name: gemini-pro
  temperature: 0.2  # Lower temperature for more deterministic responses
  top_p: 0.85  # Optimized for response speed
  max_output_tokens: 8192

editor:
  auto_apply_suggestions: true  # Speed up workflow with auto-apply
  inline_suggestions: true
  
# Direct Vertex AI integration for faster responses
tool_integrations:
  vertex_ai:
    endpoint: projects/cherry-ai-project/locations/us-central1/endpoints/agent-core
    api_version: v1
    
# Fast local semantic cache
redis:
  connection_string: redis://localhost:6379/0
  cache_ttl: 86400  # 24-hour cache for repeated queries
EOF
  success "Created Gemini Code Assist configuration"
fi

# Check if VS Code settings exists, otherwise copy from the image
if [ ! -f /home/user/persistent/.vscode-server/data/Machine/settings.json ]; then
  info "Applying optimized VS Code settings..."
  mkdir -p /home/user/persistent/.vscode-server/data/Machine/
  cp /home/user/.vscode-server/data/Machine/settings.json /home/user/persistent/.vscode-server/data/Machine/
  success "Applied optimized VS Code settings"
fi

# Monitor for performance issues
if command -v glances &> /dev/null; then
  info "Starting Glances performance monitor..."
  nohup glances --webserver --disable-plugin docker --disable-plugin sensors > /tmp/glances.log 2>&1 &
  GLANCES_PID=$!
  success "Glances started with PID $GLANCES_PID on http://localhost:61208"
fi

# Check for GCP authentication
if gcloud auth print-access-token &> /dev/null; then
  success "GCP authentication is already configured"
else
  warn "GCP authentication not configured. Please run 'gcloud auth login' after startup."
fi

# Check if repository exists
if [ -d /home/user/persistent/ai-orchestra/.git ]; then
  info "AI Orchestra repository already cloned"
  
  # Update repository if requested
  if [ "${AUTO_UPDATE_REPO:-false}" = "true" ]; then
    info "Auto-updating repository..."
    (cd /home/user/persistent/ai-orchestra && git pull)
    success "Repository updated"
  fi
else
  info "AI Orchestra repository not found. Ready for repository clone."
  
  # Show instructions
  cat > /home/user/persistent/GETTING_STARTED.md << EOF
# Getting Started with AI Orchestra on GCP Workstations

## Clone the Repository

\`\`\`bash
cd /home/user/persistent
git clone https://github.com/your-org/ai-orchestra.git
cd ai-orchestra
\`\`\`

## Setup Development Environment

\`\`\`bash
# Install dependencies using Poetry
poetry install

# Configure GCP authentication
gcloud auth login
\`\`\`

## Run the Application

\`\`\`bash
poetry run python -m ai_orchestra
\`\`\`

## Performance Tips

- Use the persistent directory for all your work
- The environment is optimized for AI/ML development
- Glances performance monitor runs at http://localhost:61208
- Run `htop` to monitor system resources
\`\`\`
EOF
  
  success "Created getting started guide: /home/user/persistent/GETTING_STARTED.md"
fi

# Run a quick disk performance check
info "Checking disk performance..."
dd if=/dev/zero of=/tmp/disk_test bs=64k count=1000 conv=fdatasync &> /dev/null
rm /tmp/disk_test
success "Disk performance check complete"

# Print environment information
info "Environment information:"
echo -e "  ${CYAN}Python:${NC} $(python3 --version)"
echo -e "  ${CYAN}Node:${NC} $(node --version)"
echo -e "  ${CYAN}npm:${NC} $(npm --version)"
echo -e "  ${CYAN}git:${NC} $(git --version)"
echo -e "  ${CYAN}Poetry:${NC} $(poetry --version 2>/dev/null || echo 'Not activated')"
echo -e "  ${CYAN}Terraform:${NC} $(terraform --version | head -n 1)"
echo -e "  ${CYAN}gcloud:${NC} $(gcloud --version | head -n 1)"
echo -e "  ${CYAN}VS Code:${NC} $(code-server --version | head -n 1)"

# Final success message
success "Environment initialization complete at $(date)"
success "Ready for development!"

# Display helpful message to user
cat << EOF

${GREEN}============================================================${NC}
${GREEN}  Welcome to AI Orchestra GCP Cloud Workstation!  ${NC}
${GREEN}============================================================${NC}

The environment has been configured for optimal performance.
All your work will be saved in the persistent directory.

${YELLOW}Quick Start:${NC}
1. Clone your repository if not already present
2. Use Poetry for dependency management
3. Get coding!

${BLUE}Performance tools:${NC}
- Glances: http://localhost:61208
- htop: For resource monitoring
- py-spy: For Python profiling

EOF

# Execute the original command or start code-server
if [ $# -gt 0 ]; then
  exec "$@"
else
  # Default: start VS Code server
  exec code-server --auth none --bind-addr 0.0.0.0:3000 /home/user/persistent
fi