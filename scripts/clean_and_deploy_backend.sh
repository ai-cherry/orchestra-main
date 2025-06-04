#!/bin/bash
# Clean and deploy Cherry AI backend services

echo "🧹 Cherry AI Backend Clean Deployment"
echo "========================================"

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "Port $port is in use by:"
        lsof -Pi :$port -sTCP:LISTEN
        return 0
    else
        return 1
    fi
}

# Function to stop container if exists
stop_container() {
    local name=$1
    if docker ps -a | grep -q $name; then
        echo "Stopping and removing $name..."
        docker stop $name >/dev/null 2>&1
        docker rm $name >/dev/null 2>&1
    fi
}

# 1. Clean up existing services
echo "🧹 Cleaning up existing services..."

# Stop all cherry_ai containers
for container in cherry_ai-postgres cherry_ai-redis cherry_ai-weaviate cherry_ai_postgres cherry_ai_redis cherry_ai_weaviate; do
    stop_container $container
done

# Check for services using our ports
echo ""
echo "📍 Checking ports..."
for port in 5432 6379 8080 8000; do
    if check_port $port; then
        echo "⚠️  Port $port is in use"
        
        # Try to stop the service using the port
        case $port in
            6379)
                echo "  Attempting to stop Redis..."
                sudo systemctl stop redis >/dev/null 2>&1 || true
                sudo service redis stop >/dev/null 2>&1 || true
                pkill -f redis-server >/dev/null 2>&1 || true
                ;;
            5432)
                echo "  Attempting to stop PostgreSQL..."
                sudo systemctl stop postgresql >/dev/null 2>&1 || true
                sudo service postgresql stop >/dev/null 2>&1 || true
                ;;
            8000)
                echo "  Attempting to stop API server..."
                pkill -f uvicorn >/dev/null 2>&1 || true
                ;;
        esac
        
        sleep 2
        
        # Check again
        if check_port $port; then
            echo "  ❌ Could not free port $port"
        else
            echo "  ✅ Port $port is now free"
        fi
    else
        echo "✅ Port $port is free"
    fi
done

# 2. Start services with Python script
echo ""
echo "🚀 Starting services..."
python3 scripts/deploy_backend_services.py

# 3. Additional verification
echo ""
echo "🔍 Final verification..."

# Check Docker containers
echo ""
echo "🐳 Running containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(cherry_ai|NAME)"

# Check API logs if exists
if [ -f /tmp/cherry_ai-api.log ]; then
    echo ""
    echo "📝 Recent API logs:"
    tail -n 20 /tmp/cherry_ai-api.log | grep -E "(ERROR|WARNING|INFO|Started)" || echo "No relevant logs yet"
fi

echo ""
echo "✅ Deployment script completed!"
echo ""
echo "📋 Next steps:"
echo "1. Check service status above"
echo "2. Access API docs at: http://localhost:8000/docs"
echo "3. Monitor logs: tail -f /tmp/cherry_ai-api.log"
echo "4. Run validation: python3 scripts/validate_and_deploy_backend.py"