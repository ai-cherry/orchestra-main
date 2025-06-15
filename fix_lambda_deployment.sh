#!/bin/bash

# Fix Lambda Labs deployment
echo "Fixing Lambda Labs deployment..."

ssh -i ~/.ssh/id_rsa ubuntu@150.136.94.139 << 'EOF'
cd ~/orchestra-main

# Create Python virtual environment
echo "Setting up Python environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install fastapi uvicorn sqlalchemy redis python-magic pydantic httpx

# Create logs directory
mkdir -p logs

# Start the API server directly for now
echo "Starting API server..."
cd api
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 > ../logs/api.log 2>&1 &

# Check if it started
sleep 3
echo "API Server status:"
curl -s http://localhost:8000/health || echo "API not responding yet"

echo "Backend is running on port 8000"
echo "Access it at: http://150.136.94.139:8000"
EOF 