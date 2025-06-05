#!/bin/bash
# Orchestra AI Quick Start

# Auto-activate environment
eval "$(pyenv init -)" 2>/dev/null || true
source venv/bin/activate

# Check if main_app.py exists
if [ -f "main_app.py" ]; then
    echo "🚀 Starting Orchestra AI server..."
    uvicorn main_app:app --reload --host 0.0.0.0 --port 8000
elif [ -f "agent/app/main.py" ]; then
    echo "🚀 Starting Orchestra AI agent server..."
    uvicorn agent.app.main:app --reload --host 0.0.0.0 --port 8000
else
    echo "⚠️  No main application file found. Creating a simple test server..."
    cat > test_server.py << 'PYEOF'
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Orchestra AI Test Server")

class HealthResponse(BaseModel):
    status: str
    message: str

@app.get("/", response_model=HealthResponse)
async def root():
    return HealthResponse(status="ok", message="Orchestra AI is running!")

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="healthy", message="All systems operational")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
PYEOF
    echo "🚀 Starting test server..."
    python test_server.py
fi
