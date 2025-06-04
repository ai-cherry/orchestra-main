#!/bin/bash
# Quick fix for Cherry-AI.me authentication

set -e

echo "🔧 Quick Auth Fix for Cherry-AI.me..."

# 1. Create a minimal requirements file for just the API
cat > requirements-minimal.txt << 'EOF'
fastapi==0.115.12
uvicorn==0.29.0
gunicorn==20.1.0
pydantic==2.11.4
pydantic-settings==2.9.1
python-jose[cryptography]
python-multipart
pyjwt==2.8.0
passlib[bcrypt]==1.7.4
python-dotenv==1.1.0
structlog==24.1.0
redis==5.0.1
httpx==0.28.1
requests==2.32.3
EOF

# 2. Build a minimal Docker image
cat > Dockerfile.minimal << 'EOF'
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements-minimal.txt .
RUN pip install --no-cache-dir -r requirements-minimal.txt

# Copy only the necessary files
COPY core/ ./core/
COPY agent/ ./agent/

# Run the app
CMD ["gunicorn", "core.conductor.src.api.app:app", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000"]
EOF

# 3. Build the image
echo "📦 Building minimal backend image..."
docker build -t cherry_ai-api-minimal:latest -f Dockerfile.minimal .

# 4. Test locally
echo "🧪 Testing the API locally..."
# Stop any existing test container
docker stop test-api 2>/dev/null || true
docker rm test-api 2>/dev/null || true

# Use port 8001 for testing to avoid conflicts
docker run -d --name test-api -p 8001:8000 cherry_ai-api-minimal:latest
sleep 5

# Check if health endpoint works
if curl -s http://localhost:8001/api/health > /dev/null; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    docker logs test-api
    docker stop test-api
    docker rm test-api
    exit 1
fi

# Check if auth endpoint exists
if curl -s -X POST http://localhost:8001/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}' | grep -q "Invalid credentials"; then
    echo "✅ Auth endpoint working"
else
    echo "❌ Auth endpoint not working"
    docker logs test-api
fi

# Clean up test container
docker stop test-api
docker rm test-api

# 5. Deploy to server
echo "🚀 Ready to deploy. Run these commands on your Vultr server:"
echo ""
echo "# Save the image"
echo "docker save cherry_ai-api-minimal:latest | gzip > cherry_ai-api-minimal.tar.gz"
echo ""
echo "# Copy to server"
echo "scp cherry_ai-api-minimal.tar.gz root@your-vultr-ip:/tmp/"
echo ""
echo "# On the server:"
echo "cd /tmp"
echo "docker load < cherry_ai-api-minimal.tar.gz"
echo "docker stop cherry_ai-api || true"
echo "docker rm cherry_ai-api || true"
echo "docker run -d --name cherry_ai-api -p 8000:8000 --restart always cherry_ai-api-minimal:latest"
echo ""
echo "# Update nginx if needed to proxy to port 8000"

echo ""
echo "✅ Auth fix is ready to deploy!"
