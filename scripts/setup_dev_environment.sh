#!/bin/bash
# setup_dev_environment.sh
#
# This script sets up a clean development environment for the AI Orchestra project.
# It's part of Phase 1 of the GitHub repository size management implementation.
#
# It configures:
# - Python virtual environment with Poetry
# - VS Code settings
# - Pre-commit hooks
# - SDK installation
#
# Usage: ./scripts/setup_dev_environment.sh [options]
# Options:
#   --with-sdk        Also install Google Cloud SDK
#   --ci              Run in CI mode (non-interactive)
#   --quiet           Reduce output verbosity
#   --skip-checks     Skip environment compatibility checks
#   --help            Show help message

set -eo pipefail

# Default settings
INSTALL_SDK=false
CI_MODE=false
QUIET=false
SKIP_CHECKS=false
LOG_FILE="setup_$(date +%Y%m%d%H%M%S).log"
START_TIME=$(date +%s)
TEMP_DIR=""
TEMP_FILES=()

# Required Python version
MIN_PYTHON_VERSION="3.11.0"

# Show help message
show_help() {
    echo "Usage: ./scripts/setup_dev_environment.sh [options]"
    echo "Options:"
    echo "  --with-sdk        Also install Google Cloud SDK"
    echo "  --ci              Run in CI mode (non-interactive)"
    echo "  --quiet           Reduce output verbosity"
    echo "  --skip-checks     Skip environment compatibility checks"
    echo "  --help            Show help message"
    exit 0
}

# Function to log messages
log() {
    local level="$1"
    shift
    local message="$@"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    
    # Always write to log file
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    
    # Only print to console if not in quiet mode, or if it's an error
    if [[ "$QUIET" == "false" || "$level" == "ERROR" ]]; then
        case "$level" in
            "INFO")  echo "ℹ️ $message" ;;
            "WARN")  echo "⚠️ $message" ;;
            "ERROR") echo "❌ $message" ;;
            "SUCCESS") echo "✅ $message" ;;
            *) echo "$message" ;;
        esac
    fi
}

# Function to clean up temporary files
cleanup() {
    if [[ -n "$TEMP_DIR" && -d "$TEMP_DIR" ]]; then
        rm -rf "$TEMP_DIR"
    fi
    
    for temp_file in "${TEMP_FILES[@]}"; do
        if [[ -f "$temp_file" ]]; then
            rm -f "$temp_file"
        fi
    done
}

# Handle errors and cleanup on exit
handle_error() {
    local exit_code=$?
    log "ERROR" "Command failed with exit code $exit_code"
    cleanup
    exit $exit_code
}

# Set up cleanup on script exit
trap cleanup EXIT
trap handle_error ERR

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --with-sdk)
            INSTALL_SDK=true
            shift
            ;;
        --ci)
            CI_MODE=true
            QUIET=true # CI mode implies quiet
            shift
            ;;
        --quiet)
            QUIET=true
            shift
            ;;
        --skip-checks)
            SKIP_CHECKS=true
            shift
            ;;
        --help)
            show_help
            ;;
        *)
            log "ERROR" "Unknown option: $1"
            show_help
            ;;
    esac
done

# Log settings
log "INFO" "Starting development environment setup with settings:"
log "INFO" "  Install SDK: $INSTALL_SDK"
log "INFO" "  CI mode: $CI_MODE"
log "INFO" "  Skip checks: $SKIP_CHECKS"
log "INFO" "  Log file: $LOG_FILE"

# Function to compare version strings
version_compare() {
    if [[ "$1" == "$2" ]]; then
        return 0
    fi
    local IFS=.
    local i ver1=($1) ver2=($2)
    # fill empty fields in ver1 with zeros
    for ((i=${#ver1[@]}; i<${#ver2[@]}; i++)); do
        ver1[i]=0
    done
    for ((i=0; i<${#ver1[@]}; i++)); do
        if [[ -z ${ver2[i]} ]]; then
            # fill empty fields in ver2 with zeros
            ver2[i]=0
        fi
        if ((10#${ver1[i]} > 10#${ver2[i]})); then
            return 1
        fi
        if ((10#${ver1[i]} < 10#${ver2[i]})); then
            return 2
        fi
    done
    return 0
}

# Function to check Python version
check_python_version() {
    if [[ "$SKIP_CHECKS" == "true" ]]; then
        log "INFO" "Skipping Python version check."
        return 0
    fi

    log "INFO" "Checking Python version..."
    if ! command -v python3 &>/dev/null; then
        log "ERROR" "Python 3 is not installed or not in PATH."
        exit 1
    fi
    
    local py_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
    log "INFO" "Found Python version: $py_version"
    
    version_compare "$py_version" "$MIN_PYTHON_VERSION"
    local result=$?
    
    if [[ $result -eq 2 ]]; then
        log "ERROR" "Python version must be at least $MIN_PYTHON_VERSION"
        log "ERROR" "Please upgrade your Python installation."
        exit 1
    fi
    
    log "SUCCESS" "Python version check passed."
}

# Ensure running from repository root
check_repository_root() {
    if [ ! -f "pyproject.toml" ]; then
        log "ERROR" "This script must be run from the repository root."
        log "ERROR" "Please navigate to the repository root and try again."
        exit 1
    fi
    log "SUCCESS" "Running from repository root."
}

# Create local bin directory
create_local_bin() {
    log "INFO" "Creating .local/bin directory for project tools..."
    mkdir -p .local/bin
    log "SUCCESS" "Created .local/bin directory."
}

# Make scripts executable
make_scripts_executable() {
    log "INFO" "Making scripts executable..."
    find scripts -name "*.sh" -type f -exec chmod +x {} \;
    log "SUCCESS" "Made scripts executable."
}

# Install Poetry safely
install_poetry() {
    log "INFO" "Checking Poetry installation..."
    if ! command -v poetry &> /dev/null; then
        log "INFO" "Poetry not found. Installing Poetry..."
        
        # Create temporary directory for downloading installer
        TEMP_DIR=$(mktemp -d)
        cd "$TEMP_DIR"
        
        # Download the installer to a temporary file
        log "INFO" "Downloading Poetry installer..."
        curl -sSL -o install-poetry.py https://install.python-poetry.org

        # Verify the download (this isn't a full security check but better than nothing)
        if [[ ! -s install-poetry.py ]]; then
            log "ERROR" "Poetry installer download failed or is empty."
            exit 1
        fi
        
        # Check file content starts with expected Python shebang
        if ! head -n 1 install-poetry.py | grep -q "^#!.*python"; then
            log "ERROR" "Poetry installer doesn't appear to be a valid Python script."
            exit 1
        fi
        
        # Install Poetry
        log "INFO" "Running Poetry installer..."
        python3 install-poetry.py
        
        # Return to original directory
        cd - > /dev/null
        
        # Verify installation succeeded
        if ! command -v poetry &> /dev/null; then
            if [[ -f "$HOME/.poetry/bin/poetry" ]]; then
                log "WARN" "Poetry installed but not in PATH. You may need to add $HOME/.poetry/bin to your PATH."
                export PATH="$HOME/.poetry/bin:$PATH"
            else
                log "ERROR" "Poetry installation failed."
                exit 1
            fi
        fi
        
        log "SUCCESS" "Poetry installed successfully."
    else
        log "SUCCESS" "Poetry already installed."
    fi

    # Configure Poetry to use in-project virtual environments
    log "INFO" "Configuring Poetry to use in-project virtual environments..."
    poetry config virtualenvs.in-project true
}

# Install Python dependencies
install_dependencies() {
    log "INFO" "Installing Python dependencies with Poetry..."
    if [[ "$CI_MODE" == "true" ]]; then
        poetry install --no-interaction --no-ansi
    else
        poetry install --no-interaction
    fi
    log "SUCCESS" "Dependencies installed."
}

# Setup pre-commit hooks
setup_pre_commit() {
    log "INFO" "Setting up pre-commit hooks..."
    if [ -f ".pre-commit-config.yaml" ]; then
        if ! poetry run pre-commit &>/dev/null; then
            log "WARN" "pre-commit not found in Poetry environment."
            log "INFO" "Installing pre-commit..."
            poetry add --group dev pre-commit
        fi
        
        log "INFO" "Installing pre-commit hooks..."
        poetry run pre-commit install
        log "SUCCESS" "Pre-commit hooks installed."
    else
        log "WARN" ".pre-commit-config.yaml not found. Skipping pre-commit setup."
    fi
}

# Configure VS Code
setup_vscode() {
    log "INFO" "Setting up VS Code configuration..."
    if [ ! -d ".vscode" ]; then
        log "INFO" "Creating .vscode directory..."
        mkdir -p .vscode
    fi

    if [ ! -f ".vscode/settings.json" ]; then
        log "WARN" ".vscode/settings.json not found. Please run the repo setup script first."
    else
        log "SUCCESS" "VS Code settings already configured."
    fi

    # Create extensions.json if it doesn't exist
    if [ ! -f ".vscode/extensions.json" ]; then
        log "INFO" "Creating recommended extensions list..."
        cat > .vscode/extensions.json << EOL
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "charliermarsh.ruff",
    "matangover.mypy",
    "tamasfe.even-better-toml",
    "ms-azuretools.vscode-docker",
    "hashicorp.terraform",
    "eamodio.gitlens"
  ]
}
EOL
        log "SUCCESS" "VS Code extensions recommendations created."
    else
        log "SUCCESS" "VS Code extensions recommendations already configured."
    fi
}

# Check if Poetry commands exist
verify_poetry_commands() {
    log "INFO" "Verifying Poetry commands..."
    # Get available scripts from pyproject.toml
