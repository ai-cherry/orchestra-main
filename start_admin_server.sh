#!/bin/bash

# Orchestra AI Admin Server Startup Script
echo "🎼 Starting Orchestra AI Admin Server..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r api/requirements.txt

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start the server
echo "🚀 Starting Orchestra AI Admin API server..."
echo "📊 Admin Dashboard: http://localhost:8000"
echo "📋 API Documentation: http://localhost:8000/docs"
echo "🔍 Interactive API: http://localhost:8000/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd api && python main.py 