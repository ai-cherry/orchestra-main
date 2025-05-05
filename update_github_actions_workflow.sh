#!/bin/bash
# Script to update GitHub Actions workflows to use Poetry for dependency management,
# add Bandit security scanning, and set up Firestore emulator for tests

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}=================================================================${NC}"
echo -e "${BLUE}${BOLD}   GITHUB ACTIONS WORKFLOW UPDATER   ${NC}"
echo -e "${BLUE}=================================================================${NC}"

# Configuration
GITHUB_ORG="ai-cherry"
GITHUB_PAT="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"
WORKFLOW_DIR=".github/workflows"

# Ensure workflow directory exists
mkdir -p "$WORKFLOW_DIR"

# Create a Python workflow template with Poetry, Bandit, and Firestore emulator
create_python_workflow() {
  local workflow_file="$WORKFLOW_DIR/python-tests.yml"
  
  echo -e "${YELLOW}Creating Python workflow with Poetry, Bandit, and Firestore emulator...${NC}"
  
  cat > "$workflow_file" << 'EOF'
name: Python Tests with Poetry

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: '1.4.0'
          virtualenvs-create: true
          virtualenvs-in-project: true
          
      - name: Install dependencies
        run: poetry install --with dev
        
      - name: Run linters
        run: poetry run flake8 .
        
      - name: Run Bandit security scan
        uses: mdegis/bandit-action@v1
        with:
          path: '.'
          level: medium
          confidence: medium

  test:
    runs-on: ubuntu-latest
    services:
      firestore-emulator:
        image: mtlynch/firestore-emulator:latest
        ports:
          - 8080:8080
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: '1.4.0'
          virtualenvs-create: true
          virtualenvs-in-project: true
          
      - name: Install dependencies
        run: poetry install --with dev
        
      - name: Run tests with pytest
        run: poetry run pytest
        env:
          FIRESTORE_EMULATOR_HOST: localhost:8080
          
  build:
    runs-on: ubuntu-latest
    needs: [lint, test]
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: '1.4.0'
          virtualenvs-create: true
          virtualenvs-in-project: true
          
      - name: Install dependencies
        run: poetry install
        
      - name: Build package
        run: poetry build
        
      - name: Store build artifacts
        uses: actions/upload-artifact@v3
        with:
          name: dist
          path: dist/
EOF

  echo -e "${GREEN}Python workflow created at ${workflow_file}${NC}"
}

# Update the GCP migration workflow to use Poetry if it contains Python steps
update_gcp_migration_workflow() {
  local workflow_file="github_actions_migration_workflow.yml"
  local updated_file="$WORKFLOW_DIR/gcp-migration.yml"
  
  if [ -f "$workflow_file" ]; then
    echo -e "${YELLOW}Updating GCP migration workflow to use Poetry...${NC}"
    
    # Create .github/workflows directory if it doesn't exist
    mkdir -p "$WORKFLOW_DIR"
    
    # Add Poetry sections to the workflow
    cat "$workflow_file" | 
    sed 's/name: GCP Project Migration/name: GCP Project Migration (with Poetry)/' |
    sed '/steps:/a\      - name: Set up Python\n        uses: actions/setup-python@v4\n        with:\n          python-version: '\''3.10'\''\n\n      - name: Install Poetry\n        uses: snok/install-poetry@v1\n        with:\n          version: '\''1.4.0'\''\n          virtualenvs-create: true\n          virtualenvs-in-project: true\n\n      - name: Install dependencies\n        run: poetry install --with dev\n\n      - name: Run Bandit security scan\n        uses: mdegis/bandit-action@v1\n        with:\n          path: '\''.'\''\n          level: medium\n          confidence: medium' > "$updated_file"
    
    echo -e "${GREEN}GCP migration workflow updated at ${updated_file}${NC}"
    
    # Convert any direct Python commands to use Poetry
    sed -i 's/python /poetry run python /g' "$updated_file"
    sed -i 's/pytest /poetry run pytest /g' "$updated_file"
    
    echo -e "${GREEN}Python commands updated to use Poetry in ${updated_file}${NC}"
  else
    echo -e "${YELLOW}GCP migration workflow file not found. Skipping update.${NC}"
  fi
}

# Create a deployment workflow that uses Poetry
create_deployment_workflow() {
  local workflow_file="$WORKFLOW_DIR/deploy.yml"
  
  echo -e "${YELLOW}Creating deployment workflow with Poetry...${NC}"
  
  cat > "$workflow_file" << 'EOF'
name: Deploy to GCP

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: '1.4.0'
          virtualenvs-create: true
          virtualenvs-in-project: true
          
      - name: Install dependencies
        run: poetry install --with dev
        
      - name: Run Bandit security scan
        uses: mdegis/bandit-action@v1
        with:
          path: '.'
          level: medium
          confidence: medium
      
      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.VERTEX_AI_BADASS_KEY }}
          
      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        
      - name: Deploy application
        run: poetry run python deploy.py
        env:
          GCP_PROJECT_ID: ${{ vars.GCP_PROJECT_ID }}
          GCP_REGION: ${{ vars.GCP_REGION }}
EOF

  echo -e "${GREEN}Deployment workflow created at ${workflow_file}${NC}"
}

# Create a workflow for Gemini-specific operations
create_gemini_workflow() {
  local workflow_file="$WORKFLOW_DIR/gemini-operations.yml"
  
  echo -e "${YELLOW}Creating Gemini operations workflow with Poetry...${NC}"
  
  cat > "$workflow_file" << 'EOF'
name: Gemini Operations

on:
  workflow_dispatch:
    inputs:
      operation:
        description: 'Gemini operation to perform'
        required: true
        default: 'deploy'
        type: choice
        options:
          - deploy
          - update
          - test

jobs:
  gemini-ops:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: '1.4.0'
          virtualenvs-create: true
          virtualenvs-in-project: true
          
      - name: Install dependencies
        run: poetry install --with dev
        
      - name: Run Bandit security scan
        uses: mdegis/bandit-action@v1
        with:
          path: '.'
          level: medium
          confidence: medium
      
      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GEMINI_API_BADASS_KEY }}
          
      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        
      - name: Run Gemini operation
        run: |
          OPERATION=${{ github.event.inputs.operation }}
          echo "Running Gemini operation: $OPERATION"
          
          if [ "$OPERATION" == "deploy" ]; then
            poetry run python gemini_deploy.py
          elif [ "$OPERATION" == "update" ]; then
            poetry run python gemini_update.py
          elif [ "$OPERATION" == "test" ]; then
            poetry run pytest tests/gemini/ -v
          else
            echo "Unknown operation: $OPERATION"
            exit 1
          fi
        env:
          GCP_PROJECT_ID: ${{ vars.GCP_PROJECT_ID }}
          GCP_REGION: ${{ vars.GCP_REGION }}
EOF

  echo -e "${GREEN}Gemini operations workflow created at ${workflow_file}${NC}"
}

# Create a poetry.toml file for project configuration
create_poetry_config() {
  echo -e "${YELLOW}Creating Poetry configuration file...${NC}"
  
  cat > "poetry.toml" << 'EOF'
[virtualenvs]
in-project = true
create = true

[repositories]
[repositories.testpypi]
url = "https://test.pypi.org/simple/"

[build]
generate-setup-file = true
EOF

  echo -e "${GREEN}Poetry configuration created at poetry.toml${NC}"
}

# Create pyproject.toml if it doesn't exist
create_pyproject_toml() {
  if [ ! -f "pyproject.toml" ]; then
    echo -e "${YELLOW}Creating pyproject.toml file...${NC}"
    
    cat > "pyproject.toml" << 'EOF'
[tool.poetry]
name = "cherry-ai"
version = "0.1.0"
description = "Cherry AI Project"
authors = ["Cherry AI Team <team@cherry-ai.com>"]
readme = "README.md"
packages = [{include = "cherry_ai"}]

[tool.poetry.dependencies]
python = "^3.10"
fastapi = "^0.95.0"
uvicorn = "^0.21.1"
google-cloud-aiplatform = "^1.36.0"
google-cloud-storage = "^2.10.0"
google-cloud-firestore = "^2.11.1"
pydantic = "^1.10.7"
python-dotenv = "^1.0.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.3.1"
pytest-cov = "^4.1.0"
black = "^23.3.0"
flake8 = "^6.0.0"
mypy = "^1.3.0"
isort = "^5.12.0"
bandit = "^1.7.5"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 88
target-version = ["py310"]

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
EOF

    echo -e "${GREEN}pyproject.toml created${NC}"
  else
    echo -e "${YELLOW}pyproject.toml already exists. Skipping creation.${NC}"
  fi
}

# Main function
main() {
  echo -e "${BLUE}Starting GitHub Actions workflow updates...${NC}"
  
  # Create Python workflow with Poetry, Bandit, and Firestore emulator
  create_python_workflow
  
  # Update GCP migration workflow to use Poetry
  update_gcp_migration_workflow
  
  # Create deployment workflow with Poetry
  create_deployment_workflow
  
  # Create Gemini operations workflow
  create_gemini_workflow
  
  # Create Poetry configuration
  create_poetry_config
  
  # Create pyproject.toml if it doesn't exist
  create_pyproject_toml
  
  echo -e "${BLUE}=================================================================${NC}"
  echo -e "${GREEN}${BOLD}   GITHUB ACTIONS WORKFLOWS UPDATED SUCCESSFULLY!   ${NC}"
  echo -e "${BLUE}=================================================================${NC}"
  
  echo -e "${YELLOW}The following workflows were created/updated:${NC}"
  echo -e "  - .github/workflows/python-tests.yml (Poetry + Bandit + Firestore emulator)"
  echo -e "  - .github/workflows/gcp-migration.yml (Updated with Poetry)"
  echo -e "  - .github/workflows/deploy.yml (Poetry + GCP deployment)"
  echo -e "  - .github/workflows/gemini-operations.yml (Poetry + Gemini operations)"
  
  echo -e "\n${YELLOW}Poetry configuration files:${NC}"
  echo -e "  - poetry.toml"
  echo -e "  - pyproject.toml (if it didn't already exist)"
  
  echo -e "\n${YELLOW}Key features implemented:${NC}"
  echo -e "  - Poetry installation with snok/install-poetry@v1"
  echo -e "  - Dependency installation with poetry install --with dev"
  echo -e "  - Command execution with poetry run"
  echo -e "  - Bandit security scanning with mdegis/bandit-action@v1"
  echo -e "  - Firestore emulator with mtlynch/firestore-emulator:latest"
  echo -e "  - Environment variable FIRESTORE_EMULATOR_HOST=localhost:8080"
  
  echo -e "\n${YELLOW}Next steps:${NC}"
  echo -e "  1. Commit the updated workflows to your repository"
  echo -e "  2. Verify the workflows run correctly on GitHub"
  echo -e "  3. Adjust the workflows as needed for your specific requirements"
}

# Execute the main function
main
