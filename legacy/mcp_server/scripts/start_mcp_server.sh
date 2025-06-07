#!/bin/bash
# MCP Server Startup Script
# This script handles starting the MCP server in different environments

set -e

# Default configuration
PORT=8000
CONFIG_FILE="mcp_server/config/mcp_config.json"
LOG_FILE="mcp_server.log"
PYTHON_CMD="python"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --port=*)
      PORT="${1#*=}"
      shift
      ;;
    --config=*)
      CONFIG_FILE="${1#*=}"
      shift
      ;;
    --log=*)
      LOG_FILE="${1#*=}"
      shift
      ;;
    --restart)
      RESTART=true
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --port=PORT      Set server port (default: 8000)"
      echo "  --config=FILE    Set config file path (default: mcp_server/config/mcp_config.json)"
      echo "  --log=FILE       Set log file path (default: mcp_server.log)"
      echo "  --restart        Restart the server if it's already running"
      echo "  --help           Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Function to check if the server is already running
check_server_running() {
  if pgrep -f "mcp_server/main.py" > /dev/null; then
    return 0
  else
    return 1
  fi
}

# Function to stop the server
stop_server() {
  echo "Stopping MCP server..."
  pkill -f "mcp_server/main.py" || true
  sleep 2
}

# Check if we need to restart the server
if [ "$RESTART" = true ] && check_server_running; then
  stop_server
fi

# Check if the server is already running
if check_server_running; then
  echo "MCP server is already running. Use --restart to restart it."
  exit 0
fi

# Determine the environment and start method
if [ -n "$KUBERNETES_SERVICE_HOST" ] || [ -n "$K_SERVICE" ]; then
  # Running in Kubernetes or Cloud Run
  echo "Starting MCP server in cloud environment..."
  $PYTHON_CMD -m mcp_server.main --port=$PORT --config=$CONFIG_FILE > $LOG_FILE 2>&1 &
elif [ -f "$REPO_ROOT/.dev_mode" ] || [ "$ENVIRONMENT" = "development" ]; then
  # Local development environment detection
  echo "Starting MCP server in local development mode..."
  cd $REPO_ROOT
  $PYTHON_CMD -m mcp_server.main --port=$PORT --config=$CONFIG_FILE --debug
elif [ -n "$CI" ] || [ -n "$GITHUB_ACTIONS" ]; then
  # CI environment
  echo "Starting MCP server in CI environment..."
  $PYTHON_CMD -m mcp_server.main --port=$PORT --config=$CONFIG_FILE --ci-mode > $LOG_FILE 2>&1 &
else
  # Default: production-like environment
  echo "Starting MCP server in production mode..."
  cd $REPO_ROOT
  nohup $PYTHON_CMD -m mcp_server.main --port=$PORT --config=$CONFIG_FILE > $LOG_FILE 2>&1 &
  echo "MCP server started in background. Check $LOG_FILE for logs."
fi

# Wait for server to start
echo "Waiting for server to start..."
for i in {1..10}; do
  if curl -s http://localhost:$PORT/health > /dev/null; then
    echo "MCP server started successfully on port $PORT!"
    exit 0
  fi
  sleep 1
done

echo "Warning: Could not confirm server startup. Check $LOG_FILE for details."
exit 1
