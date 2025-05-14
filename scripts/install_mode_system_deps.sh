#!/bin/bash
# install_mode_system_deps.sh - Install dependencies for the enhanced mode system
#
# This script installs the necessary Python dependencies for the mode system
# to function properly, including PyYAML which is required for configuration.
#
# Usage:
#   ./scripts/install_mode_system_deps.sh

set -e

echo "Installing required Python dependencies for the mode system..."

# Check for pip
if ! command -v pip &> /dev/null; then
    echo "pip not found. Trying pip3..."
    if ! command -v pip3 &> /dev/null; then
        echo "Error: Neither pip nor pip3 is installed. Please install pip and try again."
        exit 1
    else
        PIP="pip3"
    fi
else
    PIP="pip"
fi

# Install required packages
echo "Installing PyYAML and other dependencies..."
$PIP install pyyaml colorama

# Check if in a Poetry project and install dependencies if needed
if [ -f "pyproject.toml" ]; then
    if command -v poetry &> /dev/null; then
        echo "Poetry project detected. Installing dependencies..."
        poetry add pyyaml colorama
    else
        echo "Poetry not found, but pyproject.toml exists. Consider installing Poetry."
    fi
fi

# Install optional Google Cloud dependencies if requested
read -p "Do you want to install optional Google Cloud dependencies for persistence? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing Google Cloud dependencies..."
    $PIP install google-cloud-storage google-cloud-firestore google-cloud-secretmanager
    
    if [ -f "pyproject.toml" ] && command -v poetry &> /dev/null; then
        poetry add google-cloud-storage google-cloud-firestore google-cloud-secretmanager
    fi
fi

echo "Dependencies installed successfully!"
echo "You can now run the mode switcher: python tools/mode_switcher.py --interactive"