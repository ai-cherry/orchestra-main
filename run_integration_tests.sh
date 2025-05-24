#!/bin/bash
# Script to run integration tests for FirestoreMemoryManager against GCP
# This script helps set up and run integration tests against live GCP resources

set -e

# Default values
ENV="dev"
TEST_PATH="tests/integration/test_firestore_memory.py"
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --env|-e)
      ENV="$2"
      shift 2
      ;;
    --test|-t)
      TEST_PATH="$2"
      shift 2
      ;;
    --verbose|-v)
      VERBOSE=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --env, -e ENV             Environment to test against (dev, stage, prod). Default: dev"
      echo "  --test, -t TEST_PATH      Path to test file or directory. Default: tests/integration/test_firestore_memory.py"
      echo "  --verbose, -v             Enable verbose output for tests"
      echo "  --help, -h                Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $key"
      exit 1
      ;;
  esac
done

# Check if we're in the correct directory
if [ ! -d "future" ] || [ ! -d "tests" ]; then
  echo "ERROR: Please run this script from the project root directory"
  exit 1
fi

# Export test environment variables
export RUN_INTEGRATION_TESTS=true
export RUN_FIRESTORE_TESTS=true

# Check for GCP credentials
if [ -f "/tmp/gsa-key.json" ]; then
  echo "Using service account key at /tmp/gsa-key.json"
  export GCP_SA_KEY_PATH="/tmp/gsa-key.json"
  export GOOGLE_APPLICATION_CREDENTIALS="/tmp/gsa-key.json"
elif [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
  echo "Using credentials from GOOGLE_APPLICATION_CREDENTIALS: $GOOGLE_APPLICATION_CREDENTIALS"
  export GCP_SA_KEY_PATH="$GOOGLE_APPLICATION_CREDENTIALS"
else
  echo "WARNING: No GCP credentials found. Using Application Default Credentials."
  echo "If tests fail, run 'gcloud auth application-default login' or set GOOGLE_APPLICATION_CREDENTIALS."
fi

# Try to get GCP project ID from Terraform outputs
cd infra
echo "Retrieving project ID from Terraform outputs..."

# Try to get output from terraform
if command -v terraform &> /dev/null; then
  echo "Using Terraform to get project ID..."
  terraform -chdir="$ENV" init -reconfigure > /dev/null
  if terraform -chdir="$ENV" output -raw project_id &> /dev/null; then
    PROJECT_ID=$(terraform -chdir="$ENV" output -raw project_id)
    echo "Retrieved project ID from Terraform: $PROJECT_ID"
  else
    echo "Could not retrieve project ID from Terraform outputs."
    if [ -f "dev/main.tf" ]; then
      # Try to extract project ID from the Terraform file
      PROJECT_ID=$(grep -A 5 'variable "project_id"' "dev/main.tf" | grep 'default' | cut -d '"' -f 2)
      if [ -n "$PROJECT_ID" ]; then
        echo "Extracted project ID from Terraform file: $PROJECT_ID"
      fi
    fi
  fi
else
  echo "Terraform not installed. Skipping project ID retrieval from Terraform."
fi

# Go back to the project root
cd ..

# If we couldn't get project ID from Terraform, prompt the user
if [ -z "$PROJECT_ID" ]; then
  # Default from gcloud if available
  if command -v gcloud &> /dev/null; then
    DEFAULT_PROJECT=$(gcloud config get-value project 2>/dev/null)
  fi

  # Prompt with default if available
  if [ -n "$DEFAULT_PROJECT" ]; then
    read -p "Enter GCP project ID [$DEFAULT_PROJECT]: " INPUT_PROJECT_ID
    PROJECT_ID=${INPUT_PROJECT_ID:-$DEFAULT_PROJECT}
  else
    read -p "Enter GCP project ID: " PROJECT_ID
    if [ -z "$PROJECT_ID" ]; then
      echo "ERROR: Project ID is required"
      exit 1
    fi
  fi
fi

# Export GCP project ID for tests
export GCP_PROJECT_ID="$PROJECT_ID"
echo "Using project ID: $GCP_PROJECT_ID"

# Try to get Redis host from Terraform outputs if we're testing Redis as well
cd infra
if [ -d "$ENV" ]; then
  if terraform -chdir="$ENV" output -raw redis_host &> /dev/null; then
    REDIS_HOST=$(terraform -chdir="$ENV" output -raw redis_host)
    REDIS_PORT=$(terraform -chdir="$ENV" output -raw redis_port 2>/dev/null || echo "6379")
    echo "Retrieved Redis host from Terraform: $REDIS_HOST:$REDIS_PORT"
    export REDIS_HOST="$REDIS_HOST"
    export REDIS_PORT="$REDIS_PORT"
  fi
fi
cd ..

# Check for required packages
PACKAGES_TO_CHECK=(
  "google-cloud-firestore"
  "pytest"
  "pytest-asyncio"
)

MISSING_PACKAGES=()
for package in "${PACKAGES_TO_CHECK[@]}"; do
  if ! python -c "import $package" &> /dev/null; then
    MISSING_PACKAGES+=("$package")
  fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
  echo "Missing required packages: ${MISSING_PACKAGES[*]}"
  read -p "Do you want to install them now? (y/n): " INSTALL_PACKAGES
  if [[ $INSTALL_PACKAGES =~ ^[Yy]$ ]]; then
    pip install "${MISSING_PACKAGES[@]}"
  else
    echo "Aborting due to missing packages."
    exit 1
  fi
fi

# Run the tests
echo "Running integration tests..."
if [ "$VERBOSE" = true ]; then
  python -m pytest "$TEST_PATH" -v
else
  python -m pytest "$TEST_PATH"
fi

echo "Integration tests completed."
