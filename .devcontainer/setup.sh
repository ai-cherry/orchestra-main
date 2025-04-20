#!/bin/bash
# Simple setup script with robust error handling
set -e

echo "Starting minimal setup process..."

# No critical actions that could fail and cause recovery mode
# Just create a simple .env file if it doesn't exist

if [ ! -f /workspaces/orchestra-main/.env ]; then
  echo "Creating basic .env file..."
  echo "ENVIRONMENT=development" > /workspaces/orchestra-main/.env
  echo ".env file created."
fi

echo "Setup completed successfully."