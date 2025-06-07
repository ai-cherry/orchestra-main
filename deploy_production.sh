#!/bin/bash
# Enhanced AI Orchestration Deployment Script

set -e  # Exit on error

echo "🚀 Starting AI Orchestration Deployment..."

# Color codes
RED='[0;31m'
GREEN='[0;32m'
YELLOW='[1;33m'
NC='[0m'

# Configuration
DEPLOYMENT_ENV=${1:-staging}
HEALTH_CHECK_RETRIES=30
HEALTH_CHECK_INTERVAL=10

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Python version
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    required_version="3.8"
    
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)"; then
        log_error "Python 3.8+ required. Found: $python_version"
        exit 1
    fi
    
    # Check required services
    services=("postgresql" "redis" "docker")
    for service in "${services[@]}"; do
        if ! command -v $service &> /dev/null; then
            log_error "$service is not installed"
            exit 1
        fi
    done
    
    log_info "Prerequisites check passed ✓"
}

setup_environment() {
    log_info "Setting up environment..."
    
    # Create .env from example if not exists
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            log_warn "Created .env from .env.example - please update with actual values"
        else
            log_error ".env file not found"
            exit 1
        fi
    fi
    
    # Load environment variables
    export $(cat .env | grep -v '^#' | xargs)
    
    # Validate required variables
    required_vars=("DATABASE_URL" "REDIS_URL" "WEAVIATE_URL")
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_error "Required environment variable $var is not set"
            exit 1
        fi
    done
}

install_dependencies() {
    log_info "Installing dependencies..."
    
    # Create virtual environment if not exists
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    pip install -r requirements_ai_orchestration.txt
    
    log_info "Dependencies installed ✓"
}

run_migrations() {
    log_info "Running database migrations..."
    
    # Create migration script if needed
    cat > run_migrations.py << 'EOF'
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
import os

async def create_tables():
    engine = create_async_engine(os.getenv("DATABASE_URL"))
    
    async with engine.begin() as conn:
        # Create tables
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id SERIAL PRIMARY KEY,
                domain VARCHAR(50) NOT NULL,
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                agent_id INTEGER REFERENCES agents(id),
                status VARCHAR(20) DEFAULT 'pending',
                priority INTEGER DEFAULT 0,
                execution_time FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id SERIAL PRIMARY KEY,
                agent_id INTEGER REFERENCES agents(id),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                response_time FLOAT,
                error_code VARCHAR(50),
                request_type VARCHAR(50)
            )
        """)
        
        # Create indexes
        from core.performance_config import OPTIMIZED_INDEXES
        for index_sql in OPTIMIZED_INDEXES:
            try:
                await conn.execute(index_sql)
            except Exception as e:
                print(f"Index creation warning: {e}")
    
    await engine.dispose()
    print("Database setup complete")

asyncio.run(create_tables())
EOF
    
    python3 run_migrations.py
    rm run_migrations.py
    
    log_info "Database migrations complete ✓"
}

start_services() {
    log_info "Starting services..."
    
    # Start Weaviate if using Docker
    if [ "$DEPLOYMENT_ENV" != "production" ]; then
        if ! docker ps | grep -q weaviate; then
            log_info "Starting Weaviate..."
            docker run -d                 --name weaviate                 -p 8080:8080                 -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true                 -e PERSISTENCE_DATA_PATH=/var/lib/weaviate                 semitechnologies/weaviate:latest
        fi
    fi
    
    # Start the orchestration service
    log_info "Starting AI Orchestration service..."
    
    if [ "$DEPLOYMENT_ENV" == "production" ]; then
        # Production: Use gunicorn with uvicorn workers
        gunicorn services.ai_agent_orchestrator:app             --workers 4             --worker-class uvicorn.workers.UvicornWorker             --bind 0.0.0.0:8000             --timeout 60             --access-logfile -             --error-logfile -             --daemon
    else
        # Development/Staging: Use uvicorn directly
        uvicorn services.ai_agent_orchestrator:app             --host 0.0.0.0             --port 8000             --reload &
    fi
    
    SERVICE_PID=$!
    echo $SERVICE_PID > orchestration.pid
    
    log_info "Service started with PID: $SERVICE_PID"
}

health_check() {
    log_info "Performing health checks..."
    
    for i in $(seq 1 $HEALTH_CHECK_RETRIES); do
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            log_info "Health check passed ✓"
            return 0
        fi
        
        log_warn "Health check attempt $i/$HEALTH_CHECK_RETRIES failed, retrying..."
        sleep $HEALTH_CHECK_INTERVAL
    done
    
    log_error "Health check failed after $HEALTH_CHECK_RETRIES attempts"
    return 1
}

run_tests() {
    log_info "Running integration tests..."
    
    # Run pytest with coverage
    pytest tests/test_ai_orchestration_integration.py         --cov=services         --cov=core         --cov-report=term-missing         --cov-report=html         -v
        
    if [ $? -eq 0 ]; then
        log_info "All tests passed ✓"
    else
        log_error "Tests failed"
        exit 1
    fi
}

# Main deployment flow
main() {
    log_info "Deployment environment: $DEPLOYMENT_ENV"
    
    check_prerequisites
    setup_environment
    install_dependencies
    run_migrations
    
    if [ "$DEPLOYMENT_ENV" != "production" ]; then
        run_tests
    fi
    
    start_services
    health_check
    
    if [ $? -eq 0 ]; then
        log_info "🎉 AI Orchestration deployment successful!"
        log_info "Service running at: http://localhost:8000"
        log_info "Health endpoint: http://localhost:8000/health"
        log_info "Metrics endpoint: http://localhost:8000/metrics"
    else
        log_error "Deployment failed"
        exit 1
    fi
}

# Run main function
main
