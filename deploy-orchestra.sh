#!/bin/bash
# deploy-orchestra.sh - Orchestra AI Deployment Script

set -e

ENVIRONMENT=${1:-production}
COMPOSE_FILE="docker-compose.prod.yml"

if [ "$ENVIRONMENT" = "development" ]; then
    COMPOSE_FILE="docker-compose.dev.yml"
fi

echo "🚀 Deploying Orchestra AI in $ENVIRONMENT mode..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed. Aborting." >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose is required but not installed. Aborting." >&2; exit 1; }

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating environment file from template..."
    cp .env.template .env
    echo "⚠️  Please edit .env with your configuration before proceeding"
    echo "Press Enter to continue after editing .env..."
    read
fi

# Build and start services
echo "🏗️ Building and starting Orchestra AI services..."
docker-compose -f $COMPOSE_FILE down --remove-orphans
docker-compose -f $COMPOSE_FILE build --no-cache
docker-compose -f $COMPOSE_FILE up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Health checks
echo "🏥 Running health checks..."

# Check backend health
echo "Checking backend health..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo "✅ Backend is healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend health check failed"
        docker-compose -f $COMPOSE_FILE logs orchestra-backend
        exit 1
    fi
    sleep 2
done

# Check frontend health (production only)
if [ "$ENVIRONMENT" = "production" ]; then
    echo "Checking frontend health..."
    for i in {1..30}; do
        if curl -f http://localhost:80/health >/dev/null 2>&1; then
            echo "✅ Frontend is healthy"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "❌ Frontend health check failed"
            docker-compose -f $COMPOSE_FILE logs orchestra-frontend
            exit 1
        fi
        sleep 2
    done
fi

# Check database health
echo "Checking database health..."
if docker-compose -f $COMPOSE_FILE exec -T postgres pg_isready -U orchestra >/dev/null 2>&1; then
    echo "✅ Database is healthy"
else
    echo "❌ Database health check failed"
    docker-compose -f $COMPOSE_FILE logs postgres
    exit 1
fi

# Check Redis health
echo "Checking Redis health..."
if docker-compose -f $COMPOSE_FILE exec -T redis redis-cli ping >/dev/null 2>&1; then
    echo "✅ Redis is healthy"
else
    echo "❌ Redis health check failed"
    docker-compose -f $COMPOSE_FILE logs redis
    exit 1
fi

echo "✅ Orchestra AI deployment completed successfully!"
echo ""
echo "🌐 Services are available at:"
if [ "$ENVIRONMENT" = "development" ]; then
    echo "   Frontend: http://localhost:3000"
    echo "   Backend API: http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
else
    echo "   Frontend: http://localhost:80"
    echo "   Backend API: http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
fi
echo ""
echo "📊 To view logs: docker-compose -f $COMPOSE_FILE logs -f"
echo "🛑 To stop: docker-compose -f $COMPOSE_FILE down"

