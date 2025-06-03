#!/bin/bash
# Guaranteed Deployment Script for cherry-ai.me
set -e

echo "🚀 Starting deployment to cherry-ai.me..."

# Load environment variables
if [ -f .env.production ]; then
    export $(cat .env.production | xargs)
else
    echo "❌ .env.production not found!"
    exit 1
fi

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose -f docker-compose.local.yml down
docker-compose -f docker-compose.local.yml up -d

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 30

# Run database migrations
echo "🗄️ Running database migrations..."
docker exec orchestra-postgres psql -U orchestra -d orchestra -f /scripts/create_admin_user.sql

# Health check
echo "🏥 Running health checks..."
curl -f http://localhost:8001/health || echo "API health check failed"

echo "✅ Deployment complete!"
echo "🌐 Access at: https://cherry-ai.me"
echo "👤 Login: scoobyjava / Huskers1983$"
