#!/bin/bash

# Script to run the Advanced Phidata UI dashboard

# Function to check if a Python package is installed
check_package() {
    python -c "import $1" 2>/dev/null
    return $?
}

# Check for required dependencies
echo "Checking dependencies..."

# Check for requirements file
if [ -f "phidata_requirements.txt" ]; then
    echo "Found phidata_requirements.txt"
    
    # Check if we need to install dependencies
    INSTALL_DEPS=false
    
    # Check each required package
    if ! check_package "phi"; then
        echo "Phidata not found. Will install dependencies."
        INSTALL_DEPS=true
    elif ! check_package "phi.tools.duckduckgo"; then
        echo "DuckDuckGo tool not found. Will install dependencies."
        INSTALL_DEPS=true
    elif ! check_package "phi.tools.wikipedia"; then
        echo "Wikipedia tool not found. Will install dependencies."
        INSTALL_DEPS=true
    fi
    
    # Install dependencies if needed
    if [ "$INSTALL_DEPS" = true ]; then
        echo "Installing required dependencies from phidata_requirements.txt..."
        pip install -r phidata_requirements.txt
    else
        echo "All dependencies appear to be installed."
    fi
else
    echo "Warning: phidata_requirements.txt not found. Dependencies may be missing."
fi

# Check if OPENAI_API_KEY is already set
if [[ -z "${OPENAI_API_KEY}" ]]; then
    echo "OPENAI_API_KEY environment variable is not set."
    echo "Please enter your OpenAI API key (or press enter to skip if you'll set it later):"
    read -s api_key  # -s flag hides the input (for security)
    
    if [[ ! -z "$api_key" ]]; then
        export OPENAI_API_KEY=$api_key
        echo "OPENAI_API_KEY has been set for this session."
    else
        echo "No API key provided. You'll need to set OPENAI_API_KEY before running the dashboard."
        echo "You can do this by running: export OPENAI_API_KEY=your_api_key_here"
        exit 1
    fi
else
    echo "OPENAI_API_KEY is already set."
fi

# Make sure the script path is in the Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run the advanced dashboard
echo "Starting Advanced Phidata UI dashboard..."
echo "Dashboard will be available at http://localhost:7777"
python advanced_playground.py
