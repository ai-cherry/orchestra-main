#!/bin/bash
# setup_redis_for_deployment.sh - Set up a Redis instance in GCP for production deployment
#
# This script creates and configures a Redis instance in GCP for production deployment.

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PROJECT_ID="agi-baby-cherry"
REGION="us-central1"
ENV=${1:-prod}
REDIS_NAME="orchestra-redis-${ENV}"
REDIS_TIER="basic"
REDIS_SIZE=1  # Size in GB
REDIS_VERSION="redis_6_x"
NETWORK="default"

# Print header
echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}   Setting up Redis for Orchestra Deployment (${ENV})  ${NC}"
echo -e "${BLUE}======================================================${NC}"

# Function to check if command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Check if gcloud is installed
if ! command_exists gcloud; then
  echo -e "${RED}Google Cloud SDK not found. Please run ./setup_vertex_key.sh first.${NC}"
  exit 1
fi

# Check if key exists
if [ ! -f "/tmp/vertex-agent-key.json" ]; then
  echo -e "${RED}GCP service account key not found at /tmp/vertex-agent-key.json${NC}"
  echo -e "${YELLOW}Please run ./setup_vertex_key.sh first.${NC}"
  exit 1
fi

# Set environment variables
export GOOGLE_APPLICATION_CREDENTIALS=/tmp/vertex-agent-key.json

# Enable required APIs
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable redis.googleapis.com --quiet

# Check if Redis instance already exists
echo -e "${YELLOW}Checking if Redis instance already exists...${NC}"
redis_exists=$(gcloud redis instances list --region=${REGION} --filter="name:${REDIS_NAME}" --format="value(name)" 2>/dev/null || echo "")

if [ -z "$redis_exists" ]; then
  echo -e "${YELLOW}Creating Redis instance ${REDIS_NAME}...${NC}"
  gcloud redis instances create ${REDIS_NAME} \
    --region=${REGION} \
    --zone=${REGION}-a \
    --network=${NETWORK} \
    --tier=${REDIS_TIER} \
    --size=${REDIS_SIZE} \
    --redis-version=${REDIS_VERSION} \
    --project=${PROJECT_ID}
    
  echo -e "${GREEN}Redis instance created successfully.${NC}"
else
  echo -e "${GREEN}Redis instance ${REDIS_NAME} already exists.${NC}"
fi

# Get Redis connection information
echo -e "${YELLOW}Getting Redis connection information...${NC}"
redis_host=$(gcloud redis instances describe ${REDIS_NAME} --region=${REGION} --format="value(host)")
redis_port=$(gcloud redis instances describe ${REDIS_NAME} --region=${REGION} --format="value(port)")

# Create a random password for Redis
echo -e "${YELLOW}Generating Redis password and storing in Secret Manager...${NC}"
redis_password=$(openssl rand -base64 16)
secret_name="redis-password-${ENV}"

# Create Secret Manager secret if it doesn't exist
secret_exists=$(gcloud secrets list --filter="name:${secret_name}" --format="value(name)" 2>/dev/null || echo "")
if [ -z "$secret_exists" ]; then
  gcloud secrets create ${secret_name} --replication-policy="automatic"
fi

# Add password as a new version
echo -n "${redis_password}" | gcloud secrets versions add ${secret_name} --data-file=-

echo -e "${GREEN}Redis password stored in Secret Manager as '${secret_name}'.${NC}"

# Update environment file
echo -e "${YELLOW}Updating .env file with Redis settings...${NC}"

# Backup the original .env file
cp .env .env.bak

# Update or add Redis configuration
if grep -q "REDIS_HOST=" .env; then
  sed -i "s/REDIS_HOST=.*/REDIS_HOST=${redis_host}/" .env
  sed -i "s/REDIS_PORT=.*/REDIS_PORT=${redis_port}/" .env
  sed -i "s/REDIS_PASSWORD_SECRET_NAME=.*/REDIS_PASSWORD_SECRET_NAME=${secret_name}/" .env
else
  echo "" >> .env
  echo "# Redis Configuration" >> .env
  echo "REDIS_HOST=${redis_host}" >> .env
  echo "REDIS_PORT=${redis_port}" >> .env
  echo "REDIS_PASSWORD_SECRET_NAME=${secret_name}" >> .env
fi

echo -e "${GREEN}Environment file updated with Redis settings.${NC}"

# Display summary
echo -e "${BLUE}======================================================${NC}"
echo -e "${GREEN}Redis setup complete!${NC}"
echo -e "${YELLOW}Redis Host: ${redis_host}${NC}"
echo -e "${YELLOW}Redis Port: ${redis_port}${NC}"
echo -e "${YELLOW}Redis Password: Stored in Secret Manager as '${secret_name}'${NC}"
echo -e "${BLUE}======================================================${NC}"

# Instructions for accessing Redis
echo -e "${YELLOW}To connect to Redis from your local machine, you need to:${NC}"
echo -e "1. Create a VPC connector: 'gcloud compute networks vpc-access connectors create'"
echo -e "2. Ensure your firewall rules allow access to Redis port"
echo -e "3. Use the following connection string in your application:"
echo -e "   redis://:${redis_password}@${redis_host}:${redis_port}"
echo -e "${BLUE}======================================================${NC}"

echo -e "${GREEN}You can now continue with deployment using:${NC}"
echo -e "  ./deploy_to_cloud_run.sh ${ENV}"
