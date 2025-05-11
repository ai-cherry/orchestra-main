#!/bin/bash
#
# Start GCP Tools for AI Assistants
# This script starts the GCP Resources MCP server to make GCP tools available
# to all AI assistants (Gemini, Roo, Claude, GitHub Copilot, etc.)

set -e  # Exit on error

# ANSI color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default settings
DEFAULT_HOST="127.0.0.1"
DEFAULT_PORT=8085
DEFAULT_PROJECT_ID=""
DEFAULT_SNAPSHOT_DIR="./.gcp-snapshots"

# Parse arguments
show_usage() {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  -p, --project-id PROJECT_ID    Default GCP Project ID to use"
  echo "  --host HOST                    Host to bind to (default: $DEFAULT_HOST)"
  echo "  --port PORT                    Port to bind to (default: $DEFAULT_PORT)"
  echo "  -d, --snapshot-dir DIR         Directory to store snapshots (default: $DEFAULT_SNAPSHOT_DIR)"
  echo "  -h, --help                     Show this help message"
  exit 1
}

# Parse arguments
HOST=$DEFAULT_HOST
PORT=$DEFAULT_PORT
PROJECT_ID=$DEFAULT_PROJECT_ID
SNAPSHOT_DIR=$DEFAULT_SNAPSHOT_DIR

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--project-id)
      PROJECT_ID="$2"
      shift 2
      ;;
    --host)
      HOST="$2"
      shift 2
      ;;
    --port)
      PORT="$2"
      shift 2
      ;;
    -d|--snapshot-dir)
      SNAPSHOT_DIR="$2"
      shift 2
      ;;
    -h|--help)
      show_usage
      ;;
    *)
      echo "Unknown option: $1"
      show_usage
      ;;
  esac
done

# Helper functions
print_header() {
  echo -e "\n${BLUE}====== $1 ======${NC}\n"
}

print_success() {
  echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
  echo -e "${YELLOW}ℹ️ $1${NC}"
}

print_error() {
  echo -e "${RED}❌ $1${NC}"
}

# Check requirements
check_requirements() {
  print_header "Checking requirements"
  
  # Check Python and required packages
  if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
  fi
  print_success "Python 3 is installed"
  
  # Check for required Python packages
  local required_packages=("fastapi" "uvicorn" "pydantic")
  local missing_packages=()
  
  for package in "${required_packages[@]}"; do
    if ! python3 -c "import $package" &> /dev/null; then
      missing_packages+=("$package")
    fi
  done
  
  if [ ${#missing_packages[@]} -gt 0 ]; then
    print_error "The following Python packages are missing: ${missing_packages[*]}"
    print_info "Installing missing packages..."
    pip install "${missing_packages[@]}" --quiet
    print_success "Installed missing packages"
  else
    print_success "All required Python packages are installed"
  fi
  
  # Check for snapshot_gcp_resources.sh script
  if [ ! -f "snapshot_gcp_resources.sh" ]; then
    print_error "snapshot_gcp_resources.sh not found in current directory"
    exit 1
  fi
  print_success "Found snapshot_gcp_resources.sh script"
  
  # Check for gcp_resources_mcp_server.py
  if [ ! -f "gcp_resources_mcp_server.py" ]; then
    print_error "gcp_resources_mcp_server.py not found in current directory"
    exit 1
  fi
  print_success "Found gcp_resources_mcp_server.py script"
  
  # Check that snapshot_gcp_resources.sh is executable
  if [ ! -x "snapshot_gcp_resources.sh" ]; then
    print_info "Making snapshot_gcp_resources.sh executable..."
    chmod +x "snapshot_gcp_resources.sh"
    print_success "Made snapshot_gcp_resources.sh executable"
  fi
  
  # Ensure MCP server directory exists
  if [ ! -d "mcp-servers" ]; then
    print_info "Creating mcp-servers directory..."
    mkdir -p "mcp-servers"
    print_success "Created mcp-servers directory"
  fi
  
  # Check that the MCP server configuration exists
  if [ ! -f "mcp-servers/gcp-resources-server.yaml" ]; then
    print_error "MCP server configuration not found in mcp-servers/gcp-resources-server.yaml"
    exit 1
  fi
  print_success "Found MCP server configuration"
  
  # Ensure snapshot directory exists
  if [ ! -d "$SNAPSHOT_DIR" ]; then
    print_info "Creating snapshot directory $SNAPSHOT_DIR..."
    mkdir -p "$SNAPSHOT_DIR"
    print_success "Created snapshot directory"
  else
    print_success "Snapshot directory already exists"
  fi
}

# Start the MCP server
start_server() {
  print_header "Starting GCP Resources MCP server"
  
  # Build command
  local cmd="python3 gcp_resources_mcp_server.py --host $HOST --port $PORT --snapshot-dir $SNAPSHOT_DIR"
  if [ -n "$PROJECT_ID" ]; then
    cmd="$cmd --project-id $PROJECT_ID"
  fi
  
  print_info "Starting server with command: $cmd"
  
  # Execute command
  eval "$cmd"
}

# Update the Roo Modes configuration (if needed)
update_roo_modes() {
  print_header "Updating Roo Modes configuration"
  
  # Check if .roomodes file exists
  if [ ! -f ".roomodes" ]; then
    print_info "No .roomodes file found. Skipping."
    return
  fi
  
  print_info "Found .roomodes configuration. Checking if gcp-resources is already included..."
  
  # Check if gcp-resources is already included
  if grep -q "gcp-resources" ".roomodes"; then
    print_success "gcp-resources already included in .roomodes configuration"
    return
  fi
  
  print_info "Adding gcp-resources to .roomodes configuration will be done manually for now."
  print_info "Please edit your .roomodes file to include the GCP Resources MCP server."
  print_info "Example addition to the 'customModes' section:"
  echo
  echo '{
  "slug": "gcp-tools",
  "name": "☁️ GCP Tools",
  "roleDefinition": "You are a Google Cloud Platform specialist who uses real-time GCP resource snapshots to provide recommendations and analyses. You help compare actual cloud resources with infrastructure-as-code, identify optimization opportunities, and suggest best practices.",
  "customInstructions": "When analyzing GCP resources, use the GCP Resources MCP server to get snapshots of current infrastructure. Compare cloud resources with code to identify gaps in infrastructure-as-code. Focus on performance-oriented recommendations aligned with PROJECT_PRIORITIES.md.",
  "groups": ["read", "command", "mcp"],
  "model": "anthropic/claude-3-sonnet-20240229"
}'
}

# Main function
main() {
  print_header "GCP Tools for AI Assistants"
  
  # Check requirements
  check_requirements
  
  # Display server information
  print_info "GCP Resources MCP server is ready to start with the following configuration:"
  echo "  Host: $HOST"
  echo "  Port: $PORT"
  echo "  Snapshot directory: $SNAPSHOT_DIR"
  if [ -n "$PROJECT_ID" ]; then
    echo "  Default project ID: $PROJECT_ID"
  else
    echo "  Default project ID: Not set (will need to be provided for each snapshot)"
  fi
  echo
  
  # Display usage information
  print_info "Once started, this server will make GCP tools available to all AI assistants."
  print_info "The server exposes the following tools:"
  echo "  - create_gcp_snapshot: Capture a snapshot of your GCP project resources"
  echo "  - list_gcp_resources: List resources of a specific type from a snapshot"
  echo "  - compare_gcp_with_code: Compare GCP resources with your codebase"
  echo
  print_info "Usage example with Roo:"
  echo "  1. Start the server: ./start_gcp_tools_for_ai.sh"
  echo "  2. Roo will automatically detect the server and make the tools available"
  echo "  3. Use a prompt like: 'Create a snapshot of my GCP project and compare it with my Terraform code'"
  echo
  print_info "Usage example with Gemini Code Assist:"
  echo "  1. Start the server: ./start_gcp_tools_for_ai.sh"
  echo "  2. Run: python -m mcp_serverless.discovery discover --server http://localhost:8085"
  echo "  3. Use a prompt: 'What Cloud Run services do I have running in my GCP project?'"
  echo
  print_info "Press Ctrl+C to stop the server at any time."
  echo
  
  # Start the server
  start_server
}

# Run the main function
main
