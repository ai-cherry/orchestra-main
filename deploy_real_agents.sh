#!/bin/bash
# Deploy real agents on local Vultr server

set -e

echo "🚀 Deploying REAL Orchestra AI agents locally..."

# Ensure we're in the right directory
cd /root/orchestra-main

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements/base.txt

# Run validation
echo "✅ Validating code..."
make validate || true

# Restart services
echo "🔄 Restarting services..."
make stop-services
make start-services

# Check health
echo "🏥 Running health check..."
make health-check

echo "🎉 Deployment complete! Your REAL AI agents are now live!"
echo "📊 Access the API at: http://localhost:8000"
echo "🌐 Admin UI at: http://$(hostname -I | awk '{print $1}')" 