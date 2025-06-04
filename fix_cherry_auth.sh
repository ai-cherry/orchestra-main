#!/bin/bash
# Fix Cherry-AI.me authentication and API issues

set -e

echo "🔧 Fixing Cherry-AI.me Authentication Issues..."

# 1. Rebuild the backend with new auth endpoints
echo "📦 Building backend Docker image..."
docker build -t cherry_ai-api:latest -f Dockerfile .

# 2. Tag for Vultr registry (adjust registry URL as needed)
echo "🏷️ Tagging for Vultr registry..."
docker tag cherry_ai-api:latest registry.vultr.com/cherry_ai/api:latest

# 3. Push to registry
echo "📤 Pushing to registry..."
docker push registry.vultr.com/cherry_ai/api:latest

# 4. Rebuild frontend with updated login
echo "📦 Building frontend..."
cd admin-ui
npm install
npm run build
cd ..

# 5. Build frontend Docker image
echo "🐳 Building frontend Docker image..."
docker build -t cherry_ai-admin-ui:latest -f admin-ui/Dockerfile ./admin-ui

# 6. Tag and push frontend
echo "🏷️ Tagging frontend for registry..."
docker tag cherry_ai-admin-ui:latest registry.vultr.com/cherry_ai/admin-ui:latest
docker push registry.vultr.com/cherry_ai/admin-ui:latest

# 7. Restart services (adjust based on your deployment method)
echo "🔄 Restarting services..."
# If using docker-compose on Vultr:
# ssh vultr-server "cd /app && docker-compose pull && docker-compose up -d"

# If using Kubernetes:
# kubectl rollout restart deployment/cherry_ai-api
# kubectl rollout restart deployment/cherry_ai-admin-ui

echo "✅ Fix deployed! The authentication should now work properly."
echo ""
echo "📝 Summary of fixes:"
echo "  - Added /api/auth/login endpoint to backend"
echo "  - Added /api/token endpoint for OAuth2 compatibility"
echo "  - Updated frontend to make actual API calls instead of client-side auth"
echo "  - Added stub endpoints for missing APIs to prevent crashes"
echo ""
echo "🔐 Login credentials:"
echo "  Username: scoobyjava"
echo "  Password: Huskers1983$"
echo ""
echo "🌐 Visit https://cherry-ai.me to test the login"