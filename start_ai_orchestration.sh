#!/bin/bash
# Start AI Agent Orchestration System

echo "🚀 Starting AI Agent Orchestration System..."
echo "=========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install required packages if needed
echo "Checking dependencies..."
pip install -q --upgrade pip
pip install -q pyyaml aiohttp asyncio psycopg2-binary redis weaviate-client \
    beautifulsoup4 prometheus-client pydantic

# Check if services are running
echo ""
echo "Checking required services..."

# Check PostgreSQL
if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "✅ PostgreSQL is running"
else
    echo "⚠️  PostgreSQL is not running."
    echo ""
    echo "To start PostgreSQL:"
    echo "  macOS:   brew services start postgresql"
    echo "  Ubuntu:  sudo systemctl start postgresql"
    echo "  Docker:  docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres"
    echo ""
    echo "Or use the remote database (already configured in GitHub secrets):"
    echo "  DATABASE_URL=postgresql://orchestra:OrchAI_DB_2024!@45.77.87.106:5432/orchestra_main"
    echo ""
    read -p "Continue with remote database? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    USE_REMOTE_DB=true
fi

# Check Redis
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "⚠️  Redis is not running."
    echo ""
    echo "To start Redis:"
    echo "  macOS:   brew services start redis"
    echo "  Ubuntu:  sudo systemctl start redis"
    echo "  Docker:  docker run -d -p 6379:6379 redis"
    echo ""
    echo "Or use the remote Redis (already configured):"
    echo "  REDIS_URL=redis://45.77.87.106:6379"
    echo ""
    read -p "Continue with remote Redis? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    USE_REMOTE_REDIS=true
fi

# Check Weaviate
if curl -s http://localhost:8080/v1/.well-known/ready > /dev/null 2>&1; then
    echo "✅ Weaviate is running"
else
    echo "⚠️  Weaviate is not running."
    echo ""
    echo "To start Weaviate:"
    echo "  Docker:  docker run -d -p 8080:8080 semitechnologies/weaviate:latest"
    echo ""
    echo "Or use the remote Weaviate (already configured):"
    echo "  WEAVIATE_URL=http://45.77.87.106:8080"
    echo ""
    read -p "Continue with remote Weaviate? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    USE_REMOTE_WEAVIATE=true
fi

echo ""
echo "Service configuration complete!"
echo ""

# Set environment variables if using remote services
if [ "$USE_REMOTE_DB" = true ]; then
    export DATABASE_URL="postgresql://orchestra:OrchAI_DB_2024!@45.77.87.106:5432/orchestra_main"
    echo "Using remote PostgreSQL database"
fi

if [ "$USE_REMOTE_REDIS" = true ]; then
    export REDIS_URL="redis://45.77.87.106:6379"
    echo "Using remote Redis"
fi

if [ "$USE_REMOTE_WEAVIATE" = true ]; then
    export WEAVIATE_URL="http://45.77.87.106:8080"
    echo "Using remote Weaviate"
fi

echo ""

# Run deployment
echo "Deploying AI Orchestration System..."
echo "=========================================="
python3 deploy_ai_orchestration.py

# Check if deployment was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ AI Orchestration System started successfully!"
    echo ""
    echo "🌐 Access Points:"
    echo "   - Admin Interface: http://localhost:3000/admin"
    echo "   - API: http://localhost:8000/api/v1/"
    echo "   - WebSocket: ws://localhost:8000/ws"
    echo ""
    echo "📝 Example Commands:"
    echo "   - Test Cherry: curl -X POST http://localhost:8000/api/v1/query -d '{\"domain\":\"cherry\",\"query\":\"What are good swing trades?\"}'"
    echo "   - Test Sophia: curl -X POST http://localhost:8000/api/v1/query -d '{\"domain\":\"sophia\",\"query\":\"Show me Client X health\"}'"
    echo "   - Test Karen: curl -X POST http://localhost:8000/api/v1/query -d '{\"domain\":\"paragon_rx\",\"query\":\"Find diabetes trials\"}'"
    echo ""
else
    echo ""
    echo "❌ Deployment failed. Check the logs above for errors."
    exit 1
fi