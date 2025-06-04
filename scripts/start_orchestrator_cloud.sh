#!/bin/bash
# Start Comprehensive AI conductor on Cloud Instance

set -e

echo "🚀 Starting AI conductor on Cloud Instance"
echo "==========================================="

# Ensure we're in the right directory
cd /root/cherry_ai-main

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "Run: ./scripts/configure_api_keys.sh first"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Install Python dependencies if needed
echo "📦 Checking Python dependencies..."
# Check if we're in a venv, if not create one
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "Using existing virtual environment: $VIRTUAL_ENV"
    pip install -q watchdog websockets aiohttp pyjwt psycopg2-binary weaviate-client
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -q watchdog websockets aiohttp pyjwt psycopg2-binary weaviate-client
fi

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "🗄️  Starting PostgreSQL..."
    sudo service postgresql start
    sleep 3
fi

# Check if Weaviate is running
if ! curl -s http://localhost:8080/v1/.well-known/ready > /dev/null 2>&1; then
    echo "🔮 Starting Weaviate..."
    docker run -d \
        --name weaviate \
        --restart always \
        -p 8080:8080 \
        -e QUERY_DEFAULTS_LIMIT=25 \
        -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
        -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
        -e DEFAULT_VECTORIZER_MODULE=text2vec-openai \
        -e OPENAI_APIKEY=$OPENAI_API_KEY \
        semitechnologies/weaviate:latest
    
    echo "Waiting for Weaviate to start..."
    sleep 15
fi

# Create logs directory
mkdir -p logs

# Stop any existing conductor
if [ -f "conductor.pid" ]; then
    OLD_PID=$(cat conductor.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "Stopping existing conductor..."
        kill $OLD_PID 2>/dev/null || true
        sleep 2
    fi
fi

# Start the comprehensive conductor
echo "🎯 Starting Comprehensive conductor..."
nohup python3 -u ai_components/coordination/comprehensive_conductor.py \
    > logs/conductor.log 2>&1 &

CONDUCTOR_PID=$!
echo $CONDUCTOR_PID > conductor.pid

# Wait for startup
sleep 5

# Check if running
if ps -p $CONDUCTOR_PID > /dev/null; then
    echo "✅ conductor started successfully!"
    
    # Start the existing AI conductor CLI for interaction
    echo ""
    echo "🤖 Starting AI Assistant Interface..."
    echo "===================================="
    echo "You can now interact with the AI conductor."
    echo "It will monitor your coding activities and provide assistance."
    echo ""
    echo "Available commands:"
    echo "  - Type your coding questions or requests"
    echo "  - The AI will automatically detect file changes"
    echo "  - Use 'exit' to quit"
    echo ""
    
    # Run the enhanced CLI
    python3 ai_components/conductor_cli_enhanced.py
else
    echo "❌ Failed to start conductor"
    echo "Check logs/conductor.log for details"
    exit 1
fi