#!/bin/bash
# Helper script to deploy services via MCP

SERVICE_NAME="${1:-ai-orchestra-minimal}"
IMAGE="${2:-gcr.io/${GCP_PROJECT_ID}/${SERVICE_NAME}:latest}"
MEMORY="${3:-2Gi}"

echo "Deploying $SERVICE_NAME with image $IMAGE..."
# This would be called by Claude through MCP
