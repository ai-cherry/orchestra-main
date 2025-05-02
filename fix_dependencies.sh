#!/bin/bash
# Script to forcefully install critical dependencies

set -e

echo "Installing critical dependencies for Orchestra..."

# Ensure we're in the correct directory
cd /workspaces/orchestra-main

# Detect Python executable
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: No Python executable found"
    exit 1
fi

echo "Using Python: $($PYTHON_CMD --version)"

# Create and activate virtual environment (with error handling)
echo "Setting up virtual environment..."
if [ -d ".venv" ]; then
    echo "Existing virtual environment found, removing..."
    rm -rf .venv
fi

$PYTHON_CMD -m venv .venv || { echo "Error creating virtual environment with $PYTHON_CMD"; exit 1; }

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "Virtual environment activated"
elif [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
    echo "Virtual environment activated (Windows style)"
else
    echo "Error: Could not find virtual environment activation script"
    exit 1
fi

# Verify we're in the virtual environment
echo "Using Python from: $(which python)"

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install consolidated dependencies first
echo "Installing consolidated dependencies..."
if [ -f "requirements-consolidated.txt" ]; then
    python -m pip install -r requirements-consolidated.txt
else
    echo "WARNING: requirements-consolidated.txt not found, using direct install method"
    python -m pip install fastapi uvicorn pydantic loguru google-cloud-storage
fi

# Install dev dependencies
if [ -f "requirements-dev.txt" ]; then
    echo "Installing development dependencies..."
    python -m pip install -r requirements-dev.txt
fi

# Validate the installation worked
echo "Validating key package imports..."
python -c "import fastapi, uvicorn, pydantic, loguru, google.cloud.storage" || echo "WARNING: Some packages failed to import correctly"

# Print dependency versions
echo "Installed dependency versions:"
python -m pip list | grep -E 'fastapi|uvicorn|pydantic|redis|openai|google-cloud'

# Automate dependency updates and vulnerability audits
echo "Updating dependencies and auditing for vulnerabilities..."
pip install --upgrade pip
pip list --outdated --format=freeze | cut -d'=' -f1 | xargs -n1 pip install -U

if command -v safety &> /dev/null; then
    safety check
else
    echo "Safety not installed. Skipping vulnerability audit."
fi

echo "Dependencies updated successfully."

# Set critical environment variables
export PYTHONPATH=/workspaces/orchestra-main
export USE_RECOVERY_MODE=false
export STANDARD_MODE=true
export ENVIRONMENT=development

# Make a simple env file that can be sourced later
cat > /workspaces/orchestra-main/set_env.sh << EOL
#!/bin/bash
# Environment setup for Orchestra
export PYTHONPATH=/workspaces/orchestra-main
export USE_RECOVERY_MODE=false
export STANDARD_MODE=true
export ENVIRONMENT=development
EOL
chmod +x /workspaces/orchestra-main/set_env.sh

echo "Dependencies installed. Run the following commands in your terminal:"
echo ""
echo "source .venv/bin/activate"
echo "source ./set_env.sh"
echo ""
echo "Then run python diagnose_environment.py again to verify the fix."
