#!/bin/bash
# Initialize Paperspace ESC environment with improved validation

set -euo pipefail

# Standardize environment prefix
ENV_PREFIX="PAPERSPACE"  # Fixed typo from PAPERSACE

# Validate dependencies
check_dependency() {
    if ! command -v "$1" &> /dev/null; then
        echo >&2 "Error: $1 is required but not installed"
        exit 1
    fi
}

check_dependency pulumi
check_dependency docker
check_dependency python3

# Check for port conflicts
check_port_available() {
    if lsof -i :"$1" &> /dev/null; then
        echo >&2 "Error: Port $1 is already in use"
        exit 1
    fi
}

check_port_available 8080  # Weaviate
check_port_available 8081  # Weaviate MCP
check_port_available 6379  # DragonflyDB
check_port_available 8082  # Redis MCP

# Set environment name
ESC_ENV="orchestra-ai/dev-paperspace"

# Initialize or update environment
if ! pulumi env ls | grep -q "$ESC_ENV"; then
    echo "Creating new ESC environment: $ESC_ENV"
    pulumi env init "$ESC_ENV"
else
    echo "Updating existing ESC environment: $ESC_ENV"
fi

# Set configuration values with standardized prefixes
echo "Setting Paperspace configuration values..."
pulumi env set "$ESC_ENV" "${ENV_PREFIX}_WEAVIATE_URL" "http://localhost:8080"
pulumi env set "$ESC_ENV" "${ENV_PREFIX}_MCP_WEAVIATE_HOST" "localhost"
pulumi env set "$ESC_ENV" "${ENV_PREFIX}_MCP_WEAVIATE_PORT" "8081"
pulumi env set "$ESC_ENV" "${ENV_PREFIX}_DRAGONFLYDB_URL" "redis://localhost:6379"
pulumi env set "$ESC_ENV" "${ENV_PREFIX}_MCP_REDIS_PORT" "8082"

# Set secrets with standardized prefixes
echo "Setting Paperspace secrets..."
pulumi env set "$ESC_ENV" "${ENV_PREFIX}_WEAVIATE_API_KEY" --secret
pulumi env set "$ESC_ENV" "${ENV_PREFIX}_MCP_OPENAI_API_KEY" --secret
pulumi env set "$ESC_ENV" "${ENV_PREFIX}_DRAGONFLYDB_PASSWORD" --secret
pulumi env set "$ESC_ENV" "OPENAI_API_KEY" --secret  # Global key name maintained

echo "Paperspace ESC environment setup complete!"
echo "To use: eval \"\$(pulumi env open $ESC_ENV --shell=sh)\""
echo "Recommended next steps:"
echo "1. Start Weaviate: docker run -d -p 8080:8080 semitechnologies/weaviate"
echo "2. Start DragonflyDB: docker run -d -p 6379:6379 docker.dragonflydb.io/dragonflydb/dragonfly"
