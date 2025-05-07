#!/bin/bash
# setup_gemini_ide_integration.sh - Script to set up Gemini Code Assist in the IDE

echo "=== Setting up Gemini Code Assist in VS Code ==="

# Configuration
PROJECT_ID="cherry-ai-project"  # Default project from cloudbuild.yaml
LOCATION="us-west4"        # Default region from cloudbuild.yaml

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --project)
      PROJECT_ID="$2"
      shift 2
      ;;
    --location)
      LOCATION="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [--project PROJECT_ID] [--location LOCATION]"
      echo ""
      echo "Options:"
      echo "  --project   GCP Project ID (default: cherry-ai-project)"
      echo "  --location  GCP Location (default: us-west4)"
      echo "  --help      Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo "Using Project: $PROJECT_ID, Location: $LOCATION"
echo ""

# Check if VS Code is installed
if ! command -v code &> /dev/null; then
    echo "❌ VS Code not found. Please install VS Code first."
    exit 1
fi

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install Google Cloud SDK first."
    exit 1
fi

# Ensure authentication is set up
GCLOUD_AUTH=$(gcloud auth list --format="value(account)")
if [[ -z "$GCLOUD_AUTH" ]]; then
    echo "❌ No gcloud authentication found. Please run 'gcloud auth login' first."
    exit 1
else
    echo "✅ gcloud authenticated as: $GCLOUD_AUTH"
fi

# Set up environment variables
echo "Setting up environment variables for Vertex AI..."
cat << EOF > .env.gemini
# Gemini Code Assist Configuration
VERTEX_AI_PROJECT=${PROJECT_ID}
VERTEX_AI_LOCATION=${LOCATION}
EOF

# Check if .bashrc or .zshrc exists and append environment variables
if [ -f "$HOME/.bashrc" ]; then
    echo "Adding environment variables to .bashrc..."
    cat << EOF >> $HOME/.bashrc

# Gemini Code Assist environment variables
export VERTEX_AI_PROJECT=${PROJECT_ID}
export VERTEX_AI_LOCATION=${LOCATION}
EOF
elif [ -f "$HOME/.zshrc" ]; then
    echo "Adding environment variables to .zshrc..."
    cat << EOF >> $HOME/.zshrc

# Gemini Code Assist environment variables
export VERTEX_AI_PROJECT=${PROJECT_ID}
export VERTEX_AI_LOCATION=${LOCATION}
EOF
fi

# Ensure the Cloud Code extension is installed
echo "Checking for Google Cloud Code extension..."
CLOUD_CODE_INSTALLED=$(code --list-extensions | grep -i "google.cloud-code")

if [[ -z "$CLOUD_CODE_INSTALLED" ]]; then
    echo "Installing Google Cloud Code extension..."
    code --install-extension google.cloud-code
    echo "✅ Google Cloud Code extension installed."
else
    echo "✅ Google Cloud Code extension already installed."
fi

# Set up application default credentials if needed
echo "Setting up application default credentials..."
gcloud auth application-default login

# Enable required APIs
echo "Enabling required GCP APIs..."
gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID
gcloud services enable artifactregistry.googleapis.com --project=$PROJECT_ID
gcloud services enable cloudbuild.googleapis.com --project=$PROJECT_ID
gcloud services enable secretmanager.googleapis.com --project=$PROJECT_ID

# Create a test file for Gemini Code Assist
echo "Creating a test file for Gemini Code Assist..."
cat << EOF > gemini_test.py
# Test file for Gemini Code Assist
import os

# TODO: Implement a function to list all Python files in a directory recursively

def main():
    print("Gemini Code Assist Test")

if __name__ == "__main__":
    main()
EOF

echo "✅ Created test file: gemini_test.py"

# Create a Gemini prompts YAML file if it doesn't exist
if [ ! -d "templates" ]; then
    mkdir -p templates
fi

if [ ! -f "templates/gemini_prompts.yaml" ]; then
    echo "Creating Gemini prompts configuration file..."
    cat << EOF > templates/gemini_prompts.yaml
# Gemini prompt templates
prompts:
  fix_code:
    context: |
      You are a senior Python developer. Review the following code and suggest improvements, 
      identify bugs, or optimize performance. Focus on:
      1. Code quality and best practices
      2. Potential bugs or edge cases
      3. Performance optimizations
      4. Security considerations
      5. Readability and maintainability

  document_code:
    context: |
      You are a technical documentation expert. Generate comprehensive Google-style docstrings
      for the following code. Include:
      1. Clear description of purpose
      2. Parameter descriptions with types
      3. Return value descriptions with types
      4. Examples of usage
      5. Exceptions that might be raised

  refactor_code:
    context: |
      You are a code refactoring specialist. Analyze the following code and suggest refactoring to improve:
      1. Code structure and organization
      2. Separation of concerns
      3. Readability and maintainability
      4. Elimination of code smells
      5. Application of design patterns where appropriate
EOF
    echo "✅ Created templates/gemini_prompts.yaml"
fi

echo ""
echo "=== Gemini Code Assist Setup Complete ==="
echo ""
echo "To use Gemini Code Assist in VS Code:"
echo "1. Open VS Code and ensure you're authenticated with Google Cloud"
echo "2. Open gemini_test.py"
echo "3. Place your cursor on the TODO line"
echo "4. Press Ctrl+I (or Cmd+I on Mac) to trigger Gemini Code Assist"
echo "5. Or right-click and select 'Gemini: Generate' from the context menu"
echo ""
echo "If you need to validate the setup, run the validation script:"
echo "  ./gcp_migration_validator.sh"
echo ""
