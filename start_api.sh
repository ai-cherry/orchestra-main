#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
export PYTHONPATH="$(pwd):$(pwd)/api:${PYTHONPATH}"
export ORCHESTRA_AI_ENV=development
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/orchestra_ai"
export MAGIC_LIB=/opt/homebrew/lib/libmagic.dylib
export PYTHONDONTWRITEBYTECODE=1
cd api
echo "🎼 Starting Orchestra AI API Server..."
echo "🔧 Environment: $ORCHESTRA_AI_ENV"
echo "🐍 Python path: $PYTHONPATH"
echo "🔮 Magic lib: $MAGIC_LIB"
echo ""
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
