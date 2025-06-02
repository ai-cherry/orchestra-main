#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SERVER_IP="45.32.69.157"

echo -e "${GREEN}Deploying Cherry-AI to Vultr${NC}"
echo "========================================"

# Check if SSH_PRIVATE_KEY is set
if [ -z "$SSH_PRIVATE_KEY" ]; then
    echo -e "${RED}Error: SSH_PRIVATE_KEY environment variable not set${NC}"
    echo "Please set it from GitHub secrets or your local environment"
    exit 1
fi

# Setup SSH
mkdir -p ~/.ssh
echo "$SSH_PRIVATE_KEY" > ~/.ssh/vultr_key
chmod 600 ~/.ssh/vultr_key
ssh-keyscan -H $SERVER_IP >> ~/.ssh/known_hosts 2>/dev/null

# Check if Docker image exists
if [ ! -f "orchestra-api-minimal.tar.gz" ]; then
    echo -e "${YELLOW}Building Docker image...${NC}"
    docker build -f Dockerfile.minimal -t orchestra-api-minimal:latest .
    docker save orchestra-api-minimal:latest | gzip > orchestra-api-minimal.tar.gz
fi

echo -e "${YELLOW}Copying Docker image to server...${NC}"
scp -i ~/.ssh/vultr_key orchestra-api-minimal.tar.gz root@$SERVER_IP:/tmp/

echo -e "${YELLOW}Deploying on server...${NC}"
ssh -i ~/.ssh/vultr_key root@$SERVER_IP << 'ENDSSH'
set -e

# Create directories
mkdir -p /opt/orchestra/config

# Load Docker image
cd /opt/orchestra
mv /tmp/orchestra-api-minimal.tar.gz .
docker load < orchestra-api-minimal.tar.gz

# Stop existing container
docker stop orchestra-api 2>/dev/null || true
docker rm orchestra-api 2>/dev/null || true

# Run new container
docker run -d \
  --name orchestra-api \
  --restart unless-stopped \
  -p 8000:8000 \
  -v /opt/orchestra/config:/app/core/orchestrator/src/config \
  -e ENVIRONMENT=production \
  -e CORS_ORIGINS="*" \
  orchestra-api-minimal:latest

# Wait for container to start
sleep 5

# Check if running
if docker ps | grep orchestra-api; then
    echo "Orchestra API is running!"
    curl -s http://localhost:8000/api/health | jq .
else
    echo "Failed to start Orchestra API"
    docker logs orchestra-api
    exit 1
fi
ENDSSH

# Cleanup
rm -f ~/.ssh/vultr_key

echo -e "${GREEN}Testing deployment...${NC}"
sleep 5
if curl -f http://cherry-ai.me/api/health; then
    echo -e "${GREEN}✓ Cherry-ai.me is working!${NC}"
    echo -e "${GREEN}✓ API URL: http://cherry-ai.me${NC}"
    echo -e "${GREEN}✓ Health check: http://cherry-ai.me/api/health${NC}"
else
    echo -e "${RED}✗ Failed to reach cherry-ai.me${NC}"
    exit 1
fi