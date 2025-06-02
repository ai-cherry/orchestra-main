#!/bin/bash
# Quick Start Script for AI Orchestrator
# Sets up and runs the AI orchestration system

set -e

echo "================================================"
echo "AI Orchestrator Quick Start"
echo "================================================"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running in the correct directory
if [ ! -f "ai_components/orchestration/ai_orchestrator.py" ]; then
    print_error "Please run this script from the orchestra-main directory"
    exit 1
fi

# Step 1: Check environment variables
print_status "Checking environment variables..."
REQUIRED_VARS=(
    "POSTGRES_HOST"
    "POSTGRES_USER"
    "POSTGRES_PASSWORD"
    "WEAVIATE_URL"
    "WEAVIATE_API_KEY"
)

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    print_error "Missing required environment variables: ${MISSING_VARS[*]}"
    print_status "Please set up your environment variables first."
    print_status "Copy ai_components/configs/.env.template to ai_components/configs/.env and fill in the values"
    exit 1
fi

# Step 2: Install dependencies
print_status "Installing Python dependencies..."
cd ai_components
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Step 3: Run installation script
print_status "Running AI tools installation..."
chmod +x ai_components/install_ai_tools.sh
cd ai_components
sudo ./install_ai_tools.sh
cd ..

# Step 4: Validate configuration
print_status "Validating configuration..."
python scripts/validate_config.py

# Step 5: Initialize Weaviate
print_status "Initializing Weaviate schema..."
python scripts/initialize_weaviate.py

# Step 6: Configure Airbyte
print_status "Configuring Airbyte connections..."
python scripts/configure_airbyte.py || print_warning "Airbyte configuration skipped (may not be available)"

# Step 7: Start MCP server
print_status "Starting MCP server..."
if systemctl is-active --quiet orchestrator-mcp; then
    print_status "MCP server is already running"
else
    sudo systemctl start orchestrator-mcp
    sleep 5
fi

# Step 8: Check MCP server health
print_status "Checking MCP server health..."
if curl -s http://localhost:8080/ > /dev/null; then
    print_status "MCP server is healthy"
else
    print_error "MCP server is not responding"
    exit 1
fi

# Step 9: Run a test workflow
print_status "Running test workflow..."
cd ai_components
./orchestrator_cli.py orchestrate --config configs/example_workflow.json

print_status "================================================"
print_status "AI Orchestrator is ready!"
print_status "================================================"
print_status ""
print_status "Available commands:"
print_status "  ./ai_components/orchestrator_cli.py --help"
print_status ""
print_status "Example usage:"
print_status "  # Analyze codebase"
print_status "  ./ai_components/orchestrator_cli.py analyze --codebase . --output analysis.json"
print_status ""
print_status "  # Implement changes"
print_status "  ./ai_components/orchestrator_cli.py implement --analysis analysis.json --focus performance"
print_status ""
print_status "  # Refine technology stack"
print_status "  ./ai_components/orchestrator_cli.py refine --stack python_postgres_weaviate"
print_status ""
print_status "Monitor services:"
print_status "  # MCP Server logs"
print_status "  sudo journalctl -u orchestrator-mcp -f"
print_status ""
print_status "  # Orchestrator logs"
print_status "  tail -f ai_components/logs/orchestrator.log"