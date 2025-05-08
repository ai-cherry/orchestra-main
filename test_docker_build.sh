#!/bin/bash
set -e

# AI Orchestra Docker Build Test Script
# This script builds and tests the Docker image locally

# Default values
IMAGE_NAME="orchestra-api-test"
CONTAINER_NAME="orchestra-api-test"
PORT=8080
HEALTH_ENDPOINT="/health"

echo "=== AI Orchestra Docker Build Test ==="

# Clean up any existing containers with the same name
echo "Cleaning up any existing test containers..."
docker rm -f ${CONTAINER_NAME} 2>/dev/null || true

# Build the Docker image
echo "Building Docker image..."
docker build -t ${IMAGE_NAME} .

# Prepare for authentication if available
if [[ -f "$HOME/.gcp/service-account.json" ]]; then
  echo "Using local service account key for authentication..."
  GCP_AUTH_MOUNT="-v $HOME/.gcp:/app/.gcp:ro"
else
  echo "No service account key found at $HOME/.gcp/service-account.json"
  echo "Container will use application default credentials if available"
  GCP_AUTH_MOUNT=""
fi

# Run the container
echo "Running container for testing..."
docker run -d --name ${CONTAINER_NAME} -p ${PORT}:${PORT} ${GCP_AUTH_MOUNT} ${IMAGE_NAME}

# Wait for the container to start
echo "Waiting for container to start..."
sleep 5

# Check container status
echo "Checking container status..."
if [ "$(docker inspect -f {{.State.Running}} ${CONTAINER_NAME})" = "true" ]; then
  echo "✅ Container is running"
else
  echo "❌ Container failed to start"
  docker logs ${CONTAINER_NAME}
  docker rm -f ${CONTAINER_NAME} 2>/dev/null || true
  exit 1
fi

# Test the health endpoint
echo "Testing health endpoint..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${PORT}${HEALTH_ENDPOINT} || echo "failed")

if [ "${HEALTH_STATUS}" = "200" ]; then
  echo "✅ Health check passed"
else
  echo "❌ Health check failed with status: ${HEALTH_STATUS}"
  echo "Container logs:"
  docker logs ${CONTAINER_NAME}
fi

# Clean up
echo "Cleaning up..."
docker rm -f ${CONTAINER_NAME}

# Summary
if [ "${HEALTH_STATUS}" = "200" ]; then
  echo "=== Test Completed Successfully ==="
  echo "The Docker image is working correctly."
  echo "You can now proceed with deployment to Cloud Run."
  exit 0
else
  echo "=== Test Failed ==="
  echo "Please check the logs above for details."
  exit 1
fi
