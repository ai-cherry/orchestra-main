#!/bin/bash
# setup_codespaces_gemini.sh - Script to set up Cloud Code and Gemini Code Assist in Codespaces

echo "=== Setting up Cloud Code and Gemini Code Assist in Codespaces ==="

# Install VS Code extensions
echo "Installing VS Code extensions..."
code --install-extension GoogleCloudTools.cloudcode
code --install-extension GoogleCloudTools.cloudcode-gemini

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

# Set GCP project
echo "Setting GCP project to cherry-ai-project..."
gcloud config set project cherry-ai-project

# Configure VS Code settings
echo "Configuring VS Code settings..."
mkdir -p .vscode
cat << EOF > .vscode/settings.json
{
  "geminiCodeAssist.projectId": "cherry-ai-project",
  "geminiCodeAssist.contextAware": true,
  "geminiCodeAssist.codeReview.enabled": true,
  "cloudcode.duetAI.project": "cherry-ai-project",
  "cloudcode.project": "cherry-ai-project"
}
EOF

# Enable required APIs
echo "Enabling required GCP APIs..."
gcloud services enable aiplatform.googleapis.com --project=cherry-ai-project

echo ""
echo "=== Cloud Code and Gemini Code Assist Setup Complete ==="
echo ""
echo "The following configurations have been applied:"
echo "1. Cloud Code and Gemini Code Assist extensions installed"
echo "2. GCP project set to 'cherry-ai-project'"
echo "3. Context-aware code completion enabled"
echo "4. Gemini-powered code review enabled"
echo ""
echo "If you're using a Codespace, these settings are already applied via the devcontainer.json"
echo "This script can be used to manually apply the settings if needed."
echo ""
