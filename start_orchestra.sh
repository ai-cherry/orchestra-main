#!/bin/bash
# Start Cherry AI Services with Real Agents

set -e

echo "🚀 Starting Cherry AI Services..."

# Check if we're in the correct directory
if [ ! -f "agent/app/main.py" ]; then
    echo "❌ Error: Not in cherry_ai root directory"
    echo "Please run from the project root directory"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
if [[ "$PYTHON_VERSION" < "3.10" ]]; then
    echo "❌ Error: Python 3.10+ required (found $PYTHON_VERSION)"
    exit 1
fi

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "⚠️  No virtual environment found. Creating one..."
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements/production/requirements.txt
fi

# Check dependencies
echo "📦 Checking dependencies..."
pip show psutil > /dev/null 2>&1 || pip install psutil

# Kill any existing processes
echo "🔄 Stopping any existing services..."
pkill -f "uvicorn agent.app.main" || true
sleep 2

# Start the API server
echo "🌐 Starting API server..."
nohup python -m uvicorn agent.app.main:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &
API_PID=$!

echo "✅ Cherry AI started!"
echo "   API PID: $API_PID"
echo "   API URL: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📋 To view logs: tail -f api.log"
echo "🛑 To stop: ./stop_cherry_ai.sh"
echo ""
echo "🔑 Default API Key: 4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd"
