#!/bin/bash
# Deploy Cherry AI to cherry-ai.me

set -e

echo "🚀 Deploying Cherry AI to cherry-ai.me..."

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Build and start services
echo "🐳 Starting Docker services..."
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Run database migrations
echo "🗄️ Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T api python scripts/migrate_database.py

# Create admin user
echo "👤 Creating admin user..."
docker-compose -f docker-compose.prod.yml exec -T api python -c "
from src.auth.utils import create_admin_user
import asyncio
asyncio.run(create_admin_user('${ADMIN_USERNAME}', '${ADMIN_PASSWORD}', '${ADMIN_EMAIL}'))
"

# Copy Nginx config
echo "🌐 Setting up Nginx..."
sudo cp nginx-cherry-ai.conf /etc/nginx/sites-available/cherry-ai.me
sudo ln -sf /etc/nginx/sites-available/cherry-ai.me /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Install SSL certificate: sudo certbot --nginx -d cherry-ai.me -d www.cherry-ai.me"
echo "2. Access the API at: https://cherry-ai.me/api"
echo "3. Login with: ${ADMIN_USERNAME} / ${ADMIN_PASSWORD}"
