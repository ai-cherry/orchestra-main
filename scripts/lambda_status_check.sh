#!/bin/bash
# Lambda Labs Status Check & Deployment Script
# Execute this on Lambda Labs server: https://161b3292a006449cb3dcf794b2bd5d4e-0.lambdaspaces.com/

echo "🔍 LAMBDA LABS STATUS CHECK & DEPLOYMENT"
echo "========================================"
echo "Server: 150.136.94.139"
echo "Time: $(date)"
echo ""

# Function to check service health
check_service() {
    local service=$1
    local port=$2
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        echo "✅ $service is running on port $port"
    else
        echo "❌ $service is NOT running on port $port"
        return 1
    fi
}

# 1. CHECK CURRENT STATE
echo "1️⃣ CHECKING CURRENT STATE..."
echo "----------------------------"

# Check if repo exists
if [ -d "/home/ubuntu/orchestra-main" ]; then
    echo "✅ Repository exists at /home/ubuntu/orchestra-main"
    cd /home/ubuntu/orchestra-main
    
    # Check current commit
    CURRENT_COMMIT=$(git rev-parse --short HEAD)
    echo "📍 Current commit: $CURRENT_COMMIT"
    
    # Check if it's the latest
    if [ "$CURRENT_COMMIT" = "6e7ef68" ]; then
        echo "✅ Latest commit deployed!"
    else
        echo "⚠️  Not on latest commit. Pulling updates..."
        git pull origin main
    fi
else
    echo "❌ Repository not found. Cloning..."
    cd /home/ubuntu
    git clone https://github.com/ai-cherry/orchestra-main.git
    cd orchestra-main
fi

echo ""
echo "2️⃣ CHECKING DOCKER SERVICES..."
echo "------------------------------"

# Check if docker-compose is running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Docker services detected"
    docker-compose ps
else
    echo "❌ No Docker services running"
fi

echo ""
echo "3️⃣ CHECKING INDIVIDUAL SERVICES..."
echo "---------------------------------"

# Check each service
check_service "API" 8000
check_service "AI Bridge" 8766
check_service "AI Context Server" 8765
check_service "PostgreSQL" 5432
check_service "Redis" 6379
check_service "Weaviate" 8080
check_service "Nginx" 80

echo ""
echo "4️⃣ DEPLOYMENT ACTIONS..."
echo "------------------------"

# If services aren't running, deploy
if ! docker-compose ps | grep -q "Up"; then
    echo "🚀 Starting deployment..."
    
    # Create .env.production if it doesn't exist
    if [ ! -f ".env.production" ]; then
        echo "📝 Creating .env.production..."
        cat > .env.production << 'EOF'
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/cherry_ai_production
POSTGRES_DB=cherry_ai_production
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis Stack
REDIS_URL=redis://localhost:6379

# Vector Stores
WEAVIATE_URL=http://localhost:8080
PINECONE_API_KEY=${PINECONE_API_KEY:-your-key-here}
PINECONE_ENV=us-east1-gcp

# AI Services
AI_BRIDGE_PORT=8766
AI_CONTEXT_PORT=8765
BRIDGE_HOST=0.0.0.0
CONTEXT_SERVER_HOST=0.0.0.0

# Domain
DOMAIN=cherry-ai.me
SERVER_IP=150.136.94.139

# Security
SECRET_KEY=c6NbaFwcC3UcBJNzJcZm9sNjdFV1sQKg3VBcCLLbDiQ=

# API Keys
OPENAI_API_KEY=${OPENAI_API_KEY:-your-key-here}
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-your-key-here}
EOF
    fi
    
    # Update docker-compose for Redis Stack
    echo "📦 Updating Redis to Redis Stack..."
    sed -i 's/redis:7-alpine/redis\/redis-stack:latest/g' docker-compose.production.yml
    
    # Deploy services
    echo "🐳 Starting Docker services..."
    docker-compose -f docker-compose.production.yml --env-file .env.production up -d --build
    
    # Wait for services to start
    echo "⏳ Waiting for services to stabilize (30s)..."
    sleep 30
fi

echo ""
echo "5️⃣ WEBSOCKET CONNECTION TEST..."
echo "-------------------------------"

# Test AI Bridge WebSocket
echo "Testing AI Bridge WebSocket..."
if command -v wscat &> /dev/null; then
    timeout 5 wscat -c ws://localhost:8766/ws <<< '{"ai_name":"test","api_key":"manus-key-2024","capabilities":["test"]}' && echo "✅ AI Bridge WebSocket OK" || echo "❌ AI Bridge WebSocket FAILED"
else
    echo "⚠️  wscat not installed. Install with: npm install -g wscat"
fi

echo ""
echo "6️⃣ FINAL STATUS REPORT..."
echo "-------------------------"

# Summary
SERVICES_UP=$(docker-compose ps | grep -c "Up")
TOTAL_SERVICES=$(docker-compose ps | grep -c "cherry_ai")

echo "📊 Services Running: $SERVICES_UP / $TOTAL_SERVICES"
echo ""
echo "🔗 SERVICE ENDPOINTS:"
echo "- API: http://localhost:8000 (https://cherry-ai.me/api)"
echo "- AI Bridge: ws://localhost:8766/ws (wss://cherry-ai.me/bridge/ws)"
echo "- AI Context: ws://localhost:8765/context/ws (wss://cherry-ai.me/context/ws)"
echo "- PostgreSQL: localhost:5432"
echo "- Redis Stack: localhost:6379"
echo "- Weaviate: localhost:8080"
echo ""

# Check if we're ready for coding
if [ "$SERVICES_UP" -ge 6 ]; then
    echo "✅ READY FOR JOINT CODING SESSION!"
    echo "Working Directory: /home/ubuntu/orchestra-main"
    echo "All services on localhost - no network complexity!"
else
    echo "❌ NOT READY - Some services are down"
    echo "Run: docker-compose logs -f"
    echo "to see what's happening"
fi

echo ""
echo "📝 QUICK COMMANDS:"
echo "- View logs: docker-compose logs -f"
echo "- Restart all: docker-compose restart"
echo "- Stop all: docker-compose down"
echo "- Rebuild: docker-compose up -d --build"
echo ""
echo "========================================"
echo "Status check complete at $(date)" 