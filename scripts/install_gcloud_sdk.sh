#!/bin/bash
# install_gcloud_sdk.sh
#
# This script installs the Google Cloud SDK for development environments.
# It's part of Phase 1 of the GitHub repository size management implementation.
#
# Usage: ./scripts/install_gcloud_sdk.sh [version] [--quiet]
# Options:
#   [version]: Specific SDK version to install (e.g. 415.0.0)
#   --quiet: Suppress output for CI/CD usage
#
# Examples:
#   ./scripts/install_gcloud_sdk.sh           # Install latest version
#   ./scripts/install_gcloud_sdk.sh 415.0.0   # Install specific version
#   ./scripts/install_gcloud_sdk.sh --quiet   # Install quietly

set -eo pipefail

# Global variables
INSTALL_DIR="$HOME/google-cloud-sdk"
CURRENT_DIR=$(pwd)
QUIET=false
TEMP_DIR=""
VERSION="latest"

# Function to cleanup resources
cleanup() {
    # Return to original directory
    cd "$CURRENT_DIR"
    # Clean up temp directory if it exists and is not empty
    if [[ -n "$TEMP_DIR" && -d "$TEMP_DIR" ]]; then
        rm -rf "$TEMP_DIR"
    fi
}

# Function to handle errors
handle_error() {
    local exit_code=$?
    echo "❌ Error: Command failed with exit code $exit_code"
    cleanup
    exit $exit_code
}

# Set up error handling
trap handle_error ERR

# Function to log messages
log() {
    if [[ "$QUIET" != "true" ]]; then
        echo "$@"
    fi
}

# Parse arguments
for arg in "$@"; do
    if [[ "$arg" == "--quiet" ]]; then
        QUIET=true
    elif [[ "$arg" != -* ]]; then
        VERSION="$arg"
    fi
done

log "📦 Installing Google Cloud SDK..."
log "Version: ${VERSION}"
log "Install Directory: ${INSTALL_DIR}"

# Detect platform
PLATFORM="linux"
MACHINE_TYPE="x86_64"
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="darwin"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    PLATFORM="windows"
fi

# Detect architecture
if [[ "$(uname -m)" == "arm64" || "$(uname -m)" == "aarch64" ]]; then
    MACHINE_TYPE="arm"
fi

log "Detected platform: $PLATFORM-$MACHINE_TYPE"

# Check if SDK is already installed
if [ -d "$INSTALL_DIR" ]; then
    log "⚠️  Google Cloud SDK is already installed at $INSTALL_DIR"
    log "To update, run: gcloud components update"
    log "To reinstall, remove the directory first: rm -rf $INSTALL_DIR"
    exit 0
fi

# Create a temporary directory
TEMP_DIR=$(mktemp -d)
log "Using temporary directory: $TEMP_DIR"
cd "$TEMP_DIR"

if [ "$VERSION" == "latest" ]; then
    log "Downloading latest Google Cloud SDK..."
    
    # Different download approaches based on platform
    if [[ "$PLATFORM" == "windows" ]]; then
        curl -o install_google_cloud_sdk.ps1 https://sdk.cloud.google.com/
        # Windows installation would need PowerShell, just download for now
        log "For Windows, please run the installer manually"
        exit 0
    else
        curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/install_google_cloud_sdk.bash
        
        # Verify download succeeded
        if [ ! -f "install_google_cloud_sdk.bash" ]; then
            echo "❌ Error: Failed to download installer"
            cleanup
            exit 1
        fi
        
        # Execute installer with appropriate args
        if [ "$QUIET" == "true" ]; then
            bash install_google_cloud_sdk.bash --disable-prompts --install-dir="$HOME" --quiet
        else
            bash install_google_cloud_sdk.bash --disable-prompts --install-dir="$HOME"
        fi
    fi
else
    # Specific version installation
    log "Downloading Google Cloud SDK version $VERSION..."
    
    # Construct URL based on platform and version
    SDK_URL="https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-${VERSION}-${PLATFORM}-${MACHINE_TYPE}.tar.gz"
    ARCHIVE_NAME="google-cloud-sdk-${VERSION}-${PLATFORM}-${MACHINE_TYPE}.tar.gz"
    
    # Download with error checking
    if ! curl -L -O "$SDK_URL"; then
        echo "❌ Error: Failed to download SDK version $VERSION for $PLATFORM-$MACHINE_TYPE"
        echo "Check if this version/platform combination exists at https://cloud.google.com/sdk/docs/downloads-versioned-archives"
        cleanup
        exit 1
    fi
    
    # Verify the file exists and is not empty
    if [ ! -f "$ARCHIVE_NAME" ] || [ ! -s "$ARCHIVE_NAME" ]; then
        echo "❌ Error: Downloaded file is missing or empty"
        cleanup
        exit 1
    fi
    
    # Extract the archive
    log "Extracting SDK archive..."
    tar -xf "$ARCHIVE_NAME" -C "$HOME"
    
    # Run the installer
    cd "$HOME/google-cloud-sdk"
    if [ "$QUIET" == "true" ]; then
        ./install.sh --quiet
    else
        ./install.sh --quiet
    fi
fi

# Cleanup
cleanup

log "✅ Google Cloud SDK installation complete"
log "To initialize the SDK, run: gcloud init"
log "To access gcloud commands, source the following in your shell profile:"
log "  source '$INSTALL_DIR/path.bash.inc'"
log "  source '$INSTALL_DIR/completion.bash.inc'"

# Create symlinks in the project for development convenience
if [ -d "./.local/bin" ]; then
    log "Creating symlinks in .local/bin..."
    mkdir -p ./.local/bin
    ln -sf "$INSTALL_DIR/bin/gcloud" ./.local/bin/gcloud
    ln -sf "$INSTALL_DIR/bin/gsutil" ./.local/bin/gsutil
    ln -sf "$INSTALL_DIR/bin/bq" ./.local/bin/bq
    log "You can add ./.local/bin to your PATH for development convenience"
fi

log "Google Cloud SDK installation script executed successfully"