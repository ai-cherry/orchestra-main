#!/bin/bash
set -e

echo "Running setup script for Orchestra development environment..."

# Function to check if system has sufficient resources
check_resources() {
    echo "Checking system resources..."
    
    # Check available memory (in MB)
    local available_memory=$(free -m | awk '/^Mem:/{print $7}')
    local required_memory=500 # Minimum 500MB required
    
    # Check available CPU cores
    local available_cores=$(nproc)
    local required_cores=1 # Minimum 1 core required
    
    echo "Available memory: ${available_memory}MB (minimum required: ${required_memory}MB)"
    echo "Available CPU cores: ${available_cores} (minimum required: ${required_cores})"
    
    # Return success if we have enough resources, failure otherwise
    if [ "${available_memory}" -ge "${required_memory}" ] && [ "${available_cores}" -ge "${required_cores}" ]; then
        return 0 # Success
    else
        return 1 # Failure
    fi
}

# Function to install Python dependencies
install_dependencies() {
    echo "Installing Python dependencies..."
    # Use python3 -m pip for clarity
    python3 -m pip install --no-cache-dir -r /workspaces/orchestra-main/core/orchestrator/requirements.txt
    python3 -m pip install --no-cache-dir -r /workspaces/orchestra-main/packages/shared/requirements.txt
    # Add other requirements files if they exist and are needed now
    echo "Python dependencies installation attempted."
}

# Verify Python installation
python3 --version
echo "Python is installed and working"

# Check resources before installing dependencies
if check_resources; then
    install_dependencies
else
    echo "Skipping dependency installation due to resource constraints. Install manually if needed."
fi

# Set up pre-commit hooks if .pre-commit-config.yaml exists
# Note: pre-commit install is deferred as per comments in the task
if [ -f ".pre-commit-config.yaml" ]; then
    echo "Installing pre-commit hooks..."
    pre-commit install
fi

# Set up .env file from example if it exists
if [ -f ".env.example" ] && [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
fi

echo "Attempting to install core Python dependencies..."
python3 -m pip install --no-cache-dir -r /workspaces/orchestra-main/core/orchestrator/requirements.txt
python3 -m pip install --no-cache-dir -r /workspaces/orchestra-main/packages/shared/requirements.txt
echo "Core Python dependency installation attempt finished."

echo "Post-creation setup completed successfully!"
