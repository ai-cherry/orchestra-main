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

# Function to install Python dependencies from the correct locations
install_core_dependencies() {
    echo "Creating/activating Python virtual environment..."
    # Ensure we are in the project root
    cd /workspaces/orchestra-main
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
    fi
    # Activate virtual environment for this script
    source .venv/bin/activate
    echo "Virtual environment activated for setup."

    # Upgrade pip
    echo "Upgrading pip..."
    python3 -m pip install --upgrade pip

    # Install from root requirements first
    if [ -f "/workspaces/orchestra-main/requirements.txt" ]; then
        echo "Installing root requirements..."
        python3 -m pip install --no-cache-dir -r /workspaces/orchestra-main/requirements.txt
    fi

    echo "Installing dependencies from correct locations..."
    
    # Check for required requirements.txt files
    local missing_files=false
    
    # Check core/orchestrator/requirements.txt
    if [ ! -f "/workspaces/orchestra-main/core/orchestrator/requirements.txt" ]; then
        echo "ERROR: Required file core/orchestrator/requirements.txt not found."
        missing_files=true
    fi
    
    # Check packages/shared/requirements.txt
    if [ ! -f "/workspaces/orchestra-main/packages/shared/requirements.txt" ]; then
        echo "ERROR: Required file packages/shared/requirements.txt not found."
        missing_files=true
    fi
    
    # Only proceed if all required files exist
    if [ "$missing_files" = true ]; then
        echo "Setup failed: Missing required requirements.txt files."
        return 1
    fi
    
    # Install dependencies from the correct paths
    echo "Installing from core/orchestrator/requirements.txt..."
    python3 -m pip install --no-cache-dir -r /workspaces/orchestra-main/core/orchestrator/requirements.txt
    
    echo "Installing from packages/shared/requirements.txt..."
    python3 -m pip install --no-cache-dir -r /workspaces/orchestra-main/packages/shared/requirements.txt
    
    echo "All dependency installations completed successfully."
    echo "Installed packages:"
    pip list
    return 0
}

# Verify Python installation
python3 --version
echo "Python is installed and working"

# Check resources before installing dependencies
if check_resources; then
    if install_core_dependencies; then
        echo "Dependencies installed successfully."
    else
        echo "ERROR: Dependency installation failed."
        exit 1
    fi
else
    echo "Skipping dependency installation due to resource constraints. Install manually if needed."
fi

# Set up .env file from example if it exists
if [ -f ".env.example" ] && [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
fi

# Make sure recovery mode is explicitly disabled
export USE_RECOVERY_MODE=false
echo "USE_RECOVERY_MODE set to false for this session"

echo "Post-creation setup completed successfully!"
