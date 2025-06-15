#!/bin/bash
# health-check.sh - Orchestra AI Health Check Script

COMPOSE_FILE=${1:-docker-compose.prod.yml}
TIMEOUT=${2:-300}

echo "🏥 Running comprehensive health checks for Orchestra AI..."

# Function to check service health
check_service_health() {
    local service=$1
    local health_command=$2
    local max_attempts=30
    
    echo "🔍 Checking $service health..."
    
    for i in $(seq 1 $max_attempts); do
        if eval $health_command >/dev/null 2>&1; then
            echo "✅ $service is healthy"
            return 0
        fi
        
        if [ $i -eq $max_attempts ]; then
            echo "❌ $service health check failed after $max_attempts attempts"
            echo "📋 $service logs:"
            docker-compose -f $COMPOSE_FILE logs --tail=20 $service
            return 1
        fi
        
        sleep 2
    done
}

# Check if Docker Compose is running
if ! docker-compose -f $COMPOSE_FILE ps >/dev/null 2>&1; then
    echo "❌ Docker Compose services are not running"
    exit 1
fi

# Check individual services
echo "📋 Checking service status..."
docker-compose -f $COMPOSE_FILE ps

# Backend health check
check_service_health "orchestra-backend" "curl -f http://localhost:8000/health"

# Frontend health check (if running on port 80)
if docker-compose -f $COMPOSE_FILE ps | grep -q "80:80"; then
    check_service_health "orchestra-frontend" "curl -f http://localhost:80/health"
fi

# Database health check
check_service_health "postgres" "docker-compose -f $COMPOSE_FILE exec -T postgres pg_isready -U orchestra"

# Redis health check
check_service_health "redis" "docker-compose -f $COMPOSE_FILE exec -T redis redis-cli ping"

# Check container resource usage
echo "📊 Container resource usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# Check logs for errors
echo "🔍 Checking for recent errors in logs..."
if docker-compose -f $COMPOSE_FILE logs --since=5m | grep -i error; then
    echo "⚠️  Errors found in recent logs"
else
    echo "✅ No errors found in recent logs"
fi

# API endpoint tests
echo "🧪 Testing API endpoints..."

# Test health endpoint
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ Health endpoint responding"
else
    echo "❌ Health endpoint not responding"
fi

# Test system status endpoint
if curl -f http://localhost:8000/api/system/status >/dev/null 2>&1; then
    echo "✅ System status endpoint responding"
else
    echo "❌ System status endpoint not responding"
fi

echo "✅ Health check completed!"
echo ""
echo "🔗 Service URLs:"
echo "   Backend API: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"
if docker-compose -f $COMPOSE_FILE ps | grep -q "80:80"; then
    echo "   Frontend: http://localhost:80"
fi

