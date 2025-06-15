#!/bin/bash

# Deploy Docker setup to Lambda Labs instance
# This script syncs the Docker configuration and deploys the unified Orchestra AI platform

set -e

echo "🚀 Orchestra AI Docker Deployment to Lambda Labs"
echo "=============================================="

# Configuration
LAMBDA_HOST="150.136.94.139"
LAMBDA_USER="ubuntu"
SSH_KEY_PATH="$HOME/.ssh/lambda-labs-key"

# Check if SSH key exists
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo "❌ SSH key not found at $SSH_KEY_PATH"
    echo "Please ensure the Lambda Labs SSH key is available"
    exit 1
fi

echo "📦 Preparing deployment package..."

# Create deployment directory
DEPLOY_DIR="orchestra-docker-deploy"
rm -rf $DEPLOY_DIR
mkdir -p $DEPLOY_DIR

# Copy necessary files
cp Dockerfile docker-compose.yml requirements.txt $DEPLOY_DIR/
cp -r src/ database/ nginx/ monitoring/ $DEPLOY_DIR/
cp .env.production $DEPLOY_DIR/.env 2>/dev/null || echo "⚠️  No .env.production found, using defaults"

# Create deployment script
cat > $DEPLOY_DIR/deploy.sh << 'EOF'
#!/bin/bash
set -e

echo "🔧 Setting up Docker environment..."

# Update system
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# Add user to docker group
sudo usermod -aG docker $USER

# Stop existing services
docker-compose down || true

# Build and start services
echo "🏗️  Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check health
echo "🏥 Checking service health..."
docker-compose ps
curl -s http://localhost:5000/api/health | jq || echo "Health check failed"

echo "✅ Deployment complete!"
echo "Services available at:"
echo "- API: http://$HOSTNAME:5000"
echo "- Grafana: http://$HOSTNAME:3000"
echo "- Prometheus: http://$HOSTNAME:9090"
EOF

chmod +x $DEPLOY_DIR/deploy.sh

echo "📤 Uploading to Lambda Labs instance..."
rsync -avz --exclude 'node_modules' --exclude '__pycache__' --exclude '.git' \
    -e "ssh -i $SSH_KEY_PATH -o StrictHostKeyChecking=no" \
    $DEPLOY_DIR/ $LAMBDA_USER@$LAMBDA_HOST:~/orchestra-ai/

echo "🔧 Running deployment on Lambda Labs..."
ssh -i $SSH_KEY_PATH -o StrictHostKeyChecking=no $LAMBDA_USER@$LAMBDA_HOST \
    "cd ~/orchestra-ai && ./deploy.sh"

echo "🧹 Cleaning up local deployment directory..."
rm -rf $DEPLOY_DIR

echo "✅ Docker deployment to Lambda Labs complete!"
echo ""
echo "Access your services at:"
echo "- API: http://$LAMBDA_HOST:5000"
echo "- Grafana: http://$LAMBDA_HOST:3000"
echo "- Prometheus: http://$LAMBDA_HOST:9090"
echo ""
echo "To view logs: ssh -i $SSH_KEY_PATH $LAMBDA_USER@$LAMBDA_HOST 'cd ~/orchestra-ai && docker-compose logs -f'" 