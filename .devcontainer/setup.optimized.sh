#!/bin/bash
# Enhanced setup script for AI Orchestra development environment
# Implements recommendations from the infrastructure audit

set -e

echo "Setting up AI Orchestra development environment..."

# Create a log file for the setup process
SETUP_LOG="/tmp/orchestra_setup_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$SETUP_LOG") 2>&1

echo "Setup started at $(date)"
echo "Python version: $(python --version)"

# Ensure Poetry is properly configured
echo "Configuring Poetry..."
poetry config virtualenvs.in-project true

# Check if poetry.lock exists and is up-to-date
if [ ! -f "poetry.lock" ] || [ "pyproject.toml" -nt "poetry.lock" ]; then
  echo "Generating poetry.lock file..."
  poetry lock --no-update
fi

# Install dependencies with retry mechanism
MAX_RETRIES=3
RETRY_COUNT=0
SUCCESS=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ] && [ "$SUCCESS" = false ]; do
  echo "Installing dependencies (attempt $((RETRY_COUNT+1))/$MAX_RETRIES)..."
  if poetry install --with dev; then
    SUCCESS=true
  else
    RETRY_COUNT=$((RETRY_COUNT+1))
    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
      echo "Retrying in 5 seconds..."
      sleep 5
    fi
  fi
done

if [ "$SUCCESS" = false ]; then
  echo "Failed to install dependencies after $MAX_RETRIES attempts."
  exit 1
fi

# Create standard mode marker file
touch .standard_mode

# Install pre-commit hooks if config exists
if [ -f ".pre-commit-config.yaml" ]; then
  echo "Installing pre-commit hooks..."
  pre-commit install
fi

# Create .env file from template if it doesn't exist
if [ -f ".env.example" ] && [ ! -f ".env" ]; then
  echo "Creating .env file from template..."
  cp .env.example .env
  echo "Please update .env with your credentials"
fi

# Create GCP credentials directory if it doesn't exist
mkdir -p ~/.config/gcloud

# Prevent VS Code restricted mode
echo "Preventing VS Code restricted mode..."
# Set critical environment variables
export USE_RECOVERY_MODE=false
export STANDARD_MODE=true
export VSCODE_DISABLE_WORKSPACE_TRUST=true
export DISABLE_WORKSPACE_TRUST=true

# Run the comprehensive fix script if it exists
if [ -f "./fix_restricted_mode.sh" ]; then
  echo "Running comprehensive restricted mode fix script..."
  bash ./fix_restricted_mode.sh
else
  echo "Comprehensive fix script not found, using basic prevention..."
fi

# Make all scripts executable
find . -name "*.sh" -type f -exec chmod +x {} \; 2>/dev/null || true

# Update VS Code settings
mkdir -p .vscode
if [ ! -f .vscode/settings.json ]; then
  echo "Creating VS Code settings file..."
  cat > .vscode/settings.json << EOF
{
  "python.defaultInterpreterPath": "./.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.pylintEnabled": false,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.nosetestsEnabled": false,
  "python.testing.pytestArgs": [
    "tests"
  ],
  "security.workspace.trust.enabled": false,
  "security.workspace.trust.startupPrompt": "never",
  "security.workspace.trust.banner": "never",
  "security.workspace.trust.emptyWindow": false
}
EOF
else
  # Ensure workspace trust settings are correct
  sed -i 's/"security.workspace.trust.enabled": *true/"security.workspace.trust.enabled": false/g' .vscode/settings.json 2>/dev/null || true
  sed -i 's/"security.workspace.trust.startupPrompt": *".*"/"security.workspace.trust.startupPrompt": "never"/g' .vscode/settings.json 2>/dev/null || true
  sed -i 's/"security.workspace.trust.banner": *".*"/"security.workspace.trust.banner": "never"/g' .vscode/settings.json 2>/dev/null || true
  sed -i 's/"security.workspace.trust.emptyWindow": *true/"security.workspace.trust.emptyWindow": false/g' .vscode/settings.json 2>/dev/null || true
  echo "VS Code settings updated to prevent restricted mode"
fi

# Create launch configurations for debugging
if [ ! -f .vscode/launch.json ]; then
  echo "Creating VS Code launch configurations..."
  mkdir -p .vscode
  cat > .vscode/launch.json << EOF
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "core.orchestrator.src.api.app:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000"
      ],
      "jinja": true,
      "justMyCode": false,
      "env": {
        "ENVIRONMENT": "development",
        "LOG_LEVEL": "DEBUG",
        "STANDARD_MODE": "true",
        "USE_RECOVERY_MODE": "false"
      }
    },
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "\${file}",
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
EOF
fi

# Create extensions.json to recommend VS Code extensions
if [ ! -f .vscode/extensions.json ]; then
  echo "Creating VS Code extensions recommendations..."
  cat > .vscode/extensions.json << EOF
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "ms-python.flake8",
    "ms-python.isort",
    "ms-azuretools.vscode-docker",
    "hashicorp.terraform",
    "redhat.vscode-yaml",
    "github.vscode-github-actions",
    "googlecloudtools.cloudcode"
  ]
}
EOF
fi

# Verify Docker is installed and running
if command -v docker &> /dev/null; then
  echo "Docker is installed."
  if docker info &> /dev/null; then
    echo "Docker is running."
  else
    echo "WARNING: Docker is installed but not running. Please start Docker."
  fi
else
  echo "WARNING: Docker is not installed. Some features may not work."
fi

# Verify gcloud CLI is installed
if command -v gcloud &> /dev/null; then
  echo "Google Cloud SDK is installed: $(gcloud --version | head -n 1)"

  # Check if authenticated
  if gcloud auth list --filter=status=ACTIVE --format="value(account)" &> /dev/null; then
    echo "Authenticated with Google Cloud as: $(gcloud auth list --filter=status=ACTIVE --format="value(account)")"
  else
    echo "WARNING: Not authenticated with Google Cloud. Run 'gcloud auth login' to authenticate."
  fi
else
  echo "WARNING: Google Cloud SDK is not installed. Some features may not work."
fi

# Create a verification script
cat > verify_environment.sh << 'EOF'
#!/bin/bash
# Verify the development environment setup

set -e

echo "Verifying AI Orchestra development environment..."

# Check Python version
PYTHON_VERSION=$(python --version)
echo "Python version: $PYTHON_VERSION"
if [[ "$PYTHON_VERSION" != *"3.11"* ]]; then
  echo "WARNING: Python version should be 3.11.x"
fi

# Check Poetry installation
if command -v poetry &> /dev/null; then
  echo "Poetry is installed: $(poetry --version)"
else
  echo "ERROR: Poetry is not installed"
  exit 1
fi

# Check virtual environment
if [ -d ".venv" ]; then
  echo "Virtual environment exists"
else
  echo "WARNING: Virtual environment not found"
fi

# Check required files
for file in "pyproject.toml" ".env"; do
  if [ -f "$file" ]; then
    echo "$file exists"
  else
    echo "WARNING: $file not found"
  fi
done

# Check Docker
if command -v docker &> /dev/null; then
  echo "Docker is installed: $(docker --version)"
  if docker info &> /dev/null; then
    echo "Docker is running"
  else
    echo "WARNING: Docker is installed but not running"
  fi
else
  echo "WARNING: Docker is not installed"
fi

# Check Google Cloud SDK
if command -v gcloud &> /dev/null; then
  echo "Google Cloud SDK is installed: $(gcloud --version | head -n 1)"

  # Check if authenticated
  if gcloud auth list --filter=status=ACTIVE --format="value(account)" &> /dev/null; then
    echo "Authenticated with Google Cloud as: $(gcloud auth list --filter=status=ACTIVE --format="value(account)")"
  else
    echo "WARNING: Not authenticated with Google Cloud"
  fi
else
  echo "WARNING: Google Cloud SDK is not installed"
fi

# Check if required Python packages are installed
echo "Checking required Python packages..."
REQUIRED_PACKAGES=("fastapi" "pydantic" "google-cloud-secret-manager" "google-cloud-firestore")
for package in "${REQUIRED_PACKAGES[@]}"; do
  if python -c "import $package" &> /dev/null; then
    echo "$package is installed"
  else
    echo "WARNING: $package is not installed"
  fi
done

echo "Environment verification complete!"
EOF

chmod +x verify_environment.sh

# Display environment information
echo "Environment setup complete!"
echo "Python version: $(python --version)"
echo "Poetry version: $(poetry --version)"
echo "Setup log saved to: $SETUP_LOG"
echo ""
echo "Run './verify_environment.sh' to verify your environment setup."

echo "Restricted mode prevention complete"

# Create a marker file to indicate setup has completed
touch .setup_complete
