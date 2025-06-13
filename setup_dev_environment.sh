#!/bin/bash

# 🎼 Orchestra AI Development Environment Setup Script
# This script fixes all the import and environment issues

set -e  # Exit on any error

echo "🎼 Orchestra AI Development Environment Setup"
echo "=============================================="
echo ""

# Get the script directory (project root)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "📁 Project root: $PROJECT_ROOT"
echo ""

# 1. Check Python installation
echo "🐍 Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ Found: $PYTHON_VERSION"
else
    echo "❌ python3 not found. Please install Python 3.11 or later."
    exit 1
fi

# 2. Setup virtual environment
echo ""
echo "🔧 Setting up virtual environment..."
if [ -d "venv" ]; then
    echo "🗑️  Removing existing venv..."
    rm -rf venv
fi

python3 -m venv venv
echo "✅ Virtual environment created"

# 3. Activate virtual environment
echo ""
echo "⚡ Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"

# 4. Upgrade pip and install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r api/requirements.txt
echo "✅ Dependencies installed"

# 5. Fix Python path issues
echo ""
echo "🔧 Fixing Python path issues..."
export PYTHONPATH="${PROJECT_ROOT}:${PROJECT_ROOT}/api:${PYTHONPATH}"
echo "✅ Python path configured"

# 6. Set environment variables
echo ""
echo "🌍 Setting environment variables..."
export ORCHESTRA_AI_ENV=development
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/orchestra_ai"
export UPLOAD_DIR="${PROJECT_ROOT}/api/uploads"
export PYTHONDONTWRITEBYTECODE=1
echo "✅ Environment variables set"

# 7. Create uploads directory
echo ""
echo "📁 Creating uploads directory..."
mkdir -p api/uploads/temp
mkdir -p api/uploads/processed
echo "✅ Uploads directory created"

# 8. Create startup scripts
echo ""
echo "📝 Creating startup scripts..."

# API startup script
cat > start_api.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
export PYTHONPATH="$(pwd):$(pwd)/api:${PYTHONPATH}"
export ORCHESTRA_AI_ENV=development
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/orchestra_ai"
cd api
echo "🎼 Starting Orchestra AI API Server..."
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
EOF

chmod +x start_api.sh

# Frontend startup script  
cat > start_frontend.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/web"
echo "🌐 Starting Orchestra AI Frontend..."
npm run dev
EOF

chmod +x start_frontend.sh

# Combined startup script
cat > start_orchestra.sh << 'EOF'
#!/bin/bash
echo "🎼 Starting Orchestra AI Full Stack..."
echo "======================================"

# Start API in background
echo "🚀 Starting API server..."
./start_api.sh &
API_PID=$!

# Wait a moment for API to initialize
sleep 3

# Start frontend
echo "🚀 Starting frontend..."
./start_frontend.sh &
FRONTEND_PID=$!

echo ""
echo "✅ Orchestra AI is starting up!"
echo "🔗 Frontend: http://localhost:3000"
echo "🔗 API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap 'echo "🛑 Stopping services..."; kill $API_PID $FRONTEND_PID; exit' SIGINT
wait
EOF

chmod +x start_orchestra.sh

echo "✅ Startup scripts created"

# 9. Test the setup
echo ""
echo "🧪 Testing the setup..."
cd api
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from database.connection import init_database
    from services.file_service import enhanced_file_service
    print('✅ All imports working correctly')
except Exception as e:
    print(f'❌ Import test failed: {e}')
    exit(1)
"

echo ""
echo "🎉 Development Environment Setup Complete!"
echo "=========================================="
echo ""
echo "🚀 Quick Start Commands:"
echo "  ./start_orchestra.sh     # Start both API and frontend"
echo "  ./start_api.sh          # Start API only (port 8000)"
echo "  ./start_frontend.sh     # Start frontend only (port 3000)"
echo ""
echo "🔧 Manual Commands:"
echo "  source venv/bin/activate # Activate virtual environment"
echo "  cd api && python3 -m uvicorn main:app --reload"
echo "  cd web && npm run dev"
echo ""
echo "📚 Access Points:"
echo "  Frontend:  http://localhost:3000"
echo "  API:       http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo "" 