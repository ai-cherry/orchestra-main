#!/bin/bash
# This script ensures we're always in the virtual environment

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate the virtual environment
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
    echo "✅ Virtual environment activated"
    echo "🐍 Python: $(command -v python)"
    echo "📦 Pip: $(command -v pip)"
else
    echo "❌ No virtual environment found. Creating one..."
    python3 -m venv "$SCRIPT_DIR/venv"
    source "$SCRIPT_DIR/venv/bin/activate"
    echo "✅ Virtual environment created and activated"
fi

# Install requirements if they exist
# Check for requirements-app.txt first (clean requirements), then fall back to requirements.txt
if [ -f "$SCRIPT_DIR/requirements-app.txt" ]; then
    echo "📦 Installing from requirements-app.txt..."
    pip install -r "$SCRIPT_DIR/requirements-app.txt"
elif [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    echo "⚠️  No requirements-app.txt found, using requirements.txt..."
    pip install -r "$SCRIPT_DIR/requirements.txt"
fi

# Execute any command passed to this script
if [ $# -gt 0 ]; then
    exec "$@"
else
    # If no command, start a shell
    exec $SHELL
fi
