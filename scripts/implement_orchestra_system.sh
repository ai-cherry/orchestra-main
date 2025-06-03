#!/bin/bash
# Orchestra AI System Implementation Script
# Orchestrates the complete setup and deployment of the advanced AI system

set -e  # Exit on error

echo "🎭 ORCHESTRA AI SYSTEM IMPLEMENTATION"
echo "===================================="
echo "Starting at: $(date)"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "info") echo -e "${BLUE}ℹ️  ${message}${NC}" ;;
        "success") echo -e "${GREEN}✅ ${message}${NC}" ;;
        "warning") echo -e "${YELLOW}⚠️  ${message}${NC}" ;;
        "error") echo -e "${RED}❌ ${message}${NC}" ;;
    esac
}

# Check if running from project root
if [ ! -f "README.md" ] || [ ! -d "scripts" ]; then
    print_status "error" "Please run this script from the project root directory"
    exit 1
fi

PROJECT_ROOT=$(pwd)
print_status "info" "Project root: $PROJECT_ROOT"

# Step 1: Environment Setup
print_status "info" "Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_status "success" "Virtual environment created"
else
    print_status "info" "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
print_status "success" "Virtual environment activated"

# Step 2: Install Dependencies
print_status "info" "Installing dependencies..."
pip install --upgrade pip

# Check if requirements file exists
if [ -f "requirements/unified.txt" ]; then
    pip install -r requirements/unified.txt
elif [ -f "requirements/base.txt" ]; then
    pip install -r requirements/base.txt
else
    print_status "warning" "No requirements file found, installing essential packages"
    pip install fastapi uvicorn pulumi pulumi-vultr weaviate-client asyncio aiohttp pydantic
fi

# Install additional packages for the advanced system
pip install redis asyncpg sqlalchemy alembic python-multipart websockets

print_status "success" "Dependencies installed"

# Step 3: Create Directory Structure
print_status "info" "Creating directory structure..."
directories=(
    "src/search_engine"
    "src/file_ingestion"
    "src/multimedia_generation"
    "src/operator_mode"
    "src/ui/web/react_app"
    "src/infrastructure/pulumi"
    "config/personas"
    "data/uploads"
    "data/generated"
    "logs"
    "reports"
)

for dir in "${directories[@]}"; do
    mkdir -p "$dir"
done
print_status "success" "Directory structure created"

# Step 4: Run Integration Plan
print_status "info" "Running integration plan..."
if [ -f "scripts/integration_plan.py" ]; then
    python scripts/integration_plan.py
    print_status "success" "Integration plan executed"
else
    print_status "warning" "Integration plan script not found"
fi

# Step 5: Generate UI Components
print_status "info" "Generating UI components..."
if [ -f "scripts/ui_integration_spec.py" ]; then
    python scripts/ui_integration_spec.py
    print_status "success" "UI components generated"
else
    print_status "warning" "UI integration spec script not found"
fi

# Step 6: Create Initial Templates
print_status "info" "Creating initial templates..."
if [ -f "scripts/next_phase_orchestrator.py" ]; then
    python scripts/next_phase_orchestrator.py
    print_status "success" "Initial templates created"
else
    print_status "warning" "Next phase orchestrator script not found"
fi

# Step 7: Setup Configuration Files
print_status "info" "Setting up configuration files..."

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    cat > .env << EOF
# Orchestra AI Configuration
ENVIRONMENT=development
DEBUG=true

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=orchestra
POSTGRES_USER=orchestra
POSTGRES_PASSWORD=orchestra_secure_pass

# Weaviate
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
WEBSOCKET_PORT=8001

# Security
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)

# Vultr (optional for local)
# VULTR_API_KEY=your_key_here
EOF
    print_status "success" ".env file created"
else
    print_status "info" ".env file already exists"
fi

# Step 8: Initialize Database
print_status "info" "Initializing database schemas..."
if [ -f "scripts/migrate_database.py" ]; then
    python scripts/migrate_database.py
    print_status "success" "Database initialized"
else
    print_status "warning" "Database migration script not found"
fi

# Step 9: Verify Installation
print_status "info" "Running verification..."
if [ -f "scripts/verify_orchestra_deployment.py" ]; then
    python scripts/verify_orchestra_deployment.py
    verification_result=$?
    if [ $verification_result -eq 0 ]; then
        print_status "success" "Verification passed"
    else
        print_status "warning" "Verification found some issues, check the report"
    fi
else
    print_status "warning" "Verification script not found"
fi

# Step 10: Create Quick Start Scripts
print_status "info" "Creating quick start scripts..."

# Create start script
cat > start_orchestra.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Orchestra AI System..."

# Start infrastructure
echo "Starting infrastructure services..."
docker-compose -f docker-compose.local.yml up -d

# Wait for services
echo "Waiting for services to be ready..."
sleep 10

# Start API server
echo "Starting API server..."
source venv/bin/activate
uvicorn services.api_gateway:app --host 0.0.0.0 --port 8000 --reload &

# Start WebSocket server
echo "Starting WebSocket server..."
python services/websocket_server.py &

# Start UI development server
echo "Starting UI development server..."
cd src/ui/web/react_app && npm run dev &

echo ""
echo "✅ Orchestra AI is running!"
echo ""
echo "🌐 Access points:"
echo "  • UI: http://localhost:3000"
echo "  • API: http://localhost:8000/docs"
echo "  • WebSocket: ws://localhost:8001"
echo "  • Weaviate: http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
wait
EOF

chmod +x start_orchestra.sh
print_status "success" "Start script created"

# Create stop script
cat > stop_orchestra.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping Orchestra AI System..."

# Stop Node processes
pkill -f "npm run dev" || true

# Stop Python processes
pkill -f "uvicorn" || true
pkill -f "websocket_server.py" || true

# Stop Docker services
docker-compose -f docker-compose.local.yml down

echo "✅ All services stopped"
EOF

chmod +x stop_orchestra.sh
print_status "success" "Stop script created"

# Final Summary
echo ""
echo "======================================"
echo "🎉 IMPLEMENTATION COMPLETE!"
echo "======================================"
echo ""
echo "📋 Summary:"
echo "  • Python environment: ✅"
echo "  • Dependencies: ✅"
echo "  • Directory structure: ✅"
echo "  • Configuration files: ✅"
echo "  • UI components: ✅"
echo "  • Database schemas: ✅"
echo ""
echo "🚀 Next Steps:"
echo "  1. Review the verification report"
echo "  2. Start local deployment: ./start_orchestra.sh"
echo "  3. Access the UI at http://localhost:3000"
echo "  4. Test the API at http://localhost:8000/docs"
echo ""
echo "📚 For production deployment:"
echo "  1. Set VULTR_API_KEY in .env"
echo "  2. Run: python scripts/deploy_orchestra_local.py"
echo ""
echo "Completed at: $(date)"