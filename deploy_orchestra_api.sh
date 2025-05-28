#!/bin/bash
# deploy_orchestra_api.sh
# DigitalOcean deployment script for Orchestra API
# - Builds Docker image locally and pushes to DigitalOcean Container Registry
# - Deploys to DigitalOcean App Platform
# - Ensures Redis is present via Managed Database
# - Prints deployment checklist

set -e

# Configurable variables
DO_REGION="nyc3"
SERVICE_NAME="orchestra-api"
IMAGE_NAME="orchestra-api"
CONTAINER_REGISTRY="ai-orchestra"
REDIS_NAME="orchestra-redis"
REDIS_SIZE="db-s-1vcpu-1gb"
REDIS_VERSION="7"

# 1. Authenticate with DigitalOcean
echo "Authenticating with DigitalOcean..."
doctl auth init

# 2. Ensure requirements.txt is present in build context
echo "Copying requirements/base.txt to orchestra_api/requirements.txt..."
cp requirements/base.txt orchestra_api/requirements.txt

# 3. Build and push Docker image to DigitalOcean Container Registry
echo "Building Docker image..."
docker build -t $IMAGE_NAME ./orchestra_api

echo "Tagging and pushing to DigitalOcean Container Registry..."
doctl registry login
docker tag $IMAGE_NAME registry.digitalocean.com/$CONTAINER_REGISTRY/$IMAGE_NAME
docker push registry.digitalocean.com/$CONTAINER_REGISTRY/$IMAGE_NAME

# 4. Deploy to DigitalOcean App Platform
echo "Deploying to DigitalOcean App Platform..."
doctl apps create --spec <(cat <<EOF
name: $SERVICE_NAME
region: $DO_REGION
services:
- name: $SERVICE_NAME
  github:
    branch: main
    deploy_on_push: true
  dockerfile_path: ./orchestra_api/Dockerfile
  instance_size_slug: basic-xxs
  instance_count: 1
  envs:
  - key: DRAGONFLY_URI
    scope: RUN_TIME
    value: ${DRAGONFLY_URI}
  - key: MONGO_URI
    scope: RUN_TIME
    value: ${MONGO_URI}
EOF
)

# 5. Ensure Redis instance exists
echo "Checking for Redis instance..."
if ! doctl databases list | grep -q $REDIS_NAME; then
  echo "Creating Redis instance..."
  doctl databases create $REDIS_NAME \
    --engine redis \
    --version $REDIS_VERSION \
    --size $REDIS_SIZE \
    --region $DO_REGION
else
  echo "Redis instance '$REDIS_NAME' already exists."
fi

# 6. Print deployment checklist
cat <<EOF

==========================
DEPLOYMENT COMPLETE

Checklist for Ongoing Evaluation:
- [ ] Confirm App Platform service '$SERVICE_NAME' is running
- [ ] Confirm Redis instance '$REDIS_NAME' is available
- [ ] Confirm secrets are properly configured
- [ ] Monitor logs via DigitalOcean dashboard
- [ ] Update this script as needed

This workflow uses DigitalOcean native services:
Container Registry → App Platform → Managed Databases
==========================

EOF
