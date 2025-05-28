#!/bin/bash
# Fixes common Prometheus configuration errors for DigitalOcean monitoring

set -euo pipefail

# Check for required commands
if ! command -v doctl &> /dev/null; then
    echo "Error: doctl not found. Please install DigitalOcean CLI"
    exit 1
fi

# Get current monitoring config
echo "Current Prometheus configuration:"
doctl monitoring config get

# Update scrape intervals
echo "Updating scrape intervals..."
doctl monitoring config update \
    --scrape-interval "30s" \
    --evaluation-interval "30s"

# Verify changes
echo "Updated configuration:"
doctl monitoring config get

echo "Prometheus configuration updated successfully"
