#!/bin/bash
# Script to check if common dependencies are correctly installed

set -e

echo "Validating Python dependencies installation..."

# Ensure we're in the project root
cd /workspaces/orchestra-main

# Source the virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "Using virtual environment at .venv"
else
    echo "Warning: No .venv directory found. Using system Python."
fi

# Check Python version
echo "Python version:"
python3 --version

# Check pip version
echo "Pip version:"
pip3 --version

# Try to import common dependencies
echo "Testing imports of common packages..."

# Define packages to test
PACKAGES=(
    # Core dependencies
    "fastapi"
    "pydantic"
    "pydantic_settings"
    "uvicorn"
    "starlette"

    # API and networking
    "httpx"
    "python_multipart"

    # Async utilities
    "asyncio"
    "aiohttp"

    # LLM dependencies
    "openai"
    "tiktoken"

    # Storage dependencies
    "redis"
    "google.cloud.firestore"
    "google.auth"
    "google.cloud.storage"

    # Test dependencies
    "pytest"
    "pytest_asyncio"

    # Utilities
    "typer"
    "loguru"
    "tenacity"
    "requests"
)

# Try importing each package
for pkg in "${PACKAGES[@]}"; do
    echo -n "Testing import of $pkg: "
    if python3 -c "import $pkg" 2>/dev/null; then
        echo "✅ Success"
    else
        echo "❌ Failed"
    fi
done

echo "Dependency check completed."
