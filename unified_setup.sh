#!/bin/bash
# Orchestra Unified Setup Script
# 
# This script automates the complete setup process for Orchestra:
# 1. GCP Authentication setup
# 2. Terraform infrastructure provisioning
# 3. Figma-GCP sync for design tokens
# 4. GitHub Actions integration
# 5. Setting up GitHub secrets

set -e  # Exit on any error

# Text styling
BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m"  # No Color

# Print section header
section() {
    echo ""
    echo -e "${BOLD}${BLUE}==== $1 ====${NC}"
    echo ""
}

# Print success message
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Print warning message
warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Print error message
error() {
    echo -e "${RED}❌ $1${NC}"
}

# Ask for confirmation
confirm() {
    read -p "$1 (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return 1
    fi
    return 0
}

# Variables
PROJECT_ID="agi-baby-cherry"

# Check for Figma PAT
if [ -z "$FIGMA_PAT" ]; then
    error "FIGMA_PAT environment variable is not set."
    echo "Please set your Figma Personal Access Token by running: export FIGMA_PAT=your-token-here"
    exit 1
fi

FIGMA_FILE_ID="368236963"

section "Orchestra Unified Setup"
echo "This script will set up the complete Orchestra environment:"
echo "  - GCP Authentication and service accounts"
echo "  - Infrastructure using Terraform"
echo "  - Figma-GCP sync for design tokens"
echo "  - GitHub Actions workflows"
echo ""
echo "Requirements:"
echo "  - GCP service account key"
echo "  - Figma PAT"
echo "  - GitHub access"
echo ""

if ! confirm "Do you want to proceed with the setup?"; then
    exit 0
fi

section "1. GCP Authentication Setup"

# Check for gcloud CLI
if ! command -v gcloud &> /dev/null; then
    error "gcloud CLI not found. Please install it first."
    exit 1
fi

# Check if logged in
ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null || echo "")
if [[ -z "$ACCOUNT" ]]; then
    echo "You are not logged in to gcloud. Please log in:"
    gcloud auth login
fi

echo "Currently authenticated as: $(gcloud auth list --filter=status:ACTIVE --format="value(account)")"
echo "Project ID: $PROJECT_ID"
if ! confirm "Is this the correct account and project?"; then
    echo "Please set the correct project ID:"
    read -p "Project ID: " PROJECT_ID
    gcloud config set project $PROJECT_ID
fi

# Check for existing service account key
echo "Checking for vertex-agent service account..."
if gcloud iam service-accounts describe vertex-agent@${PROJECT_ID}.iam.gserviceaccount.com &> /dev/null; then
    success "Found vertex-agent service account"
else
    warning "vertex-agent service account not found. Creating it..."
    gcloud iam service-accounts create vertex-agent \
        --display-name="Vertex AI Agent Service Account"
    
    # Grant necessary roles
    echo "Granting necessary roles to the service account..."
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="serviceAccount:vertex-agent@${PROJECT_ID}.iam.gserviceaccount.com" \
        --role="roles/datastore.user"
    
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="serviceAccount:vertex-agent@${PROJECT_ID}.iam.gserviceaccount.com" \
        --role="roles/aiplatform.user"
    
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="serviceAccount:vertex-agent@${PROJECT_ID}.iam.gserviceaccount.com" \
        --role="roles/secretmanager.secretAccessor"
fi

# Create a new key
if confirm "Do you want to create a new service account key for vertex-agent?"; then
    mkdir -p /tmp/credentials
    echo "Creating new key..."
    gcloud iam service-accounts keys create /tmp/credentials/vertex-agent-new-key.json \
        --iam-account=vertex-agent@${PROJECT_ID}.iam.gserviceaccount.com
    
    # Backup existing key if it exists
    if [ -f /tmp/vertex-agent-key.json ]; then
        echo "Backing up existing key file..."
        cp /tmp/vertex-agent-key.json /tmp/vertex-agent-key.json.bak
    fi
    
    # Install the new key
    echo "Installing new key to /tmp/vertex-agent-key.json..."
    cp /tmp/credentials/vertex-agent-new-key.json /tmp/vertex-agent-key.json
    chmod 600 /tmp/vertex-agent-key.json
    
    success "Created and installed new service account key"
fi

# Set environment variables
echo "Setting up environment variables..."
export GOOGLE_APPLICATION_CREDENTIALS=/tmp/vertex-agent-key.json
export GCP_SA_KEY_PATH=/tmp/vertex-agent-key.json
export GCP_PROJECT_ID=${PROJECT_ID}

# Add to .bashrc for persistence
if ! grep -q "export GOOGLE_APPLICATION_CREDENTIALS=/tmp/vertex-agent-key.json" ~/.bashrc; then
    echo '# GCP Authentication' >> ~/.bashrc
    echo 'export GOOGLE_APPLICATION_CREDENTIALS=/tmp/vertex-agent-key.json' >> ~/.bashrc
    echo 'export GCP_SA_KEY_PATH=/tmp/vertex-agent-key.json' >> ~/.bashrc
    echo "export GCP_PROJECT_ID=${PROJECT_ID}" >> ~/.bashrc
    echo 'export FIGMA_PAT=$FIGMA_PAT' >> ~/.bashrc
    success "Added environment variables to .bashrc"
fi

# Test authentication
echo "Testing GCP authentication..."
if [ -f test_gcp_auth.py ]; then
    python test_gcp_auth.py
    success "Authentication test completed"
else
    warning "test_gcp_auth.py not found, skipping authentication test"
fi

section "2. Infrastructure Provisioning"

# Create terraform directory if it doesn't exist
TERRAFORM_DIR="infra/orchestra-terraform"
if [ ! -d "$TERRAFORM_DIR" ]; then
    error "Terraform directory not found at $TERRAFORM_DIR"
    exit 1
else
    success "Found Terraform configuration at $TERRAFORM_DIR"
fi

# Update terraform.tfvars with correct values
echo "Updating Terraform variables..."
cat > ${TERRAFORM_DIR}/terraform.tfvars << EOF
project_id = "${PROJECT_ID}"
region     = "us-central1"
zone       = "us-central1-a"
env        = "dev"
figma_pat  = "\${FIGMA_PAT}"
EOF
success "Updated terraform.tfvars with project ID and Figma PAT"

# Confirm before proceeding with Terraform
echo ""
echo "About to initialize and apply Terraform configuration."
echo "This will provision GCP resources and may incur charges to your GCP account."
if confirm "Do you want to proceed with Terraform deployment?"; then
    cd ${TERRAFORM_DIR}
    
    echo "Initializing Terraform..."
    terraform init
    
    echo "Planning Terraform deployment..."
    terraform plan -out=tfplan
    
    if confirm "Review the plan above. Do you want to apply it?"; then
        echo "Applying Terraform configuration..."
        terraform apply tfplan
        
        # Save output to a file
        terraform output -json > terraform_output.json
        success "Terraform deployment completed and output saved to terraform_output.json"
    else
        warning "Terraform apply cancelled by user"
    fi
    
    cd -
else
    warning "Skipping Terraform deployment"
fi

section "3. Figma-GCP Integration"

# Check for Figma script
if [ ! -f "scripts/figma_gcp_sync.py" ]; then
    error "Figma-GCP sync script not found at scripts/figma_gcp_sync.py"
    exit 1
else
    success "Found Figma-GCP sync script"
fi

# Ensure required Python packages are installed
echo "Installing required Python packages..."
pip install -q google-cloud-secretmanager google-cloud-aiplatform requests

# Run Figma-GCP sync
echo "Running Figma-GCP sync..."
python scripts/figma_gcp_sync.py \
    --file-key ${FIGMA_FILE_ID} \
    --output-dir ./styles \
    --project-id ${PROJECT_ID} \
    --update-secrets \
    --update-terraform

success "Figma-GCP sync completed"

section "4. Setting Up GitHub Actions"

# Create .github/workflows directory if it doesn't exist
WORKFLOWS_DIR=".github/workflows"
mkdir -p ${WORKFLOWS_DIR}

# Create GitHub Actions workflow for CI/CD
echo "Creating GitHub Actions workflow for CI/CD..."
cat > ${WORKFLOWS_DIR}/orchestra_ci_cd.yml << EOF
name: Orchestra CI/CD

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  # Add Figma webhook trigger (requires setup in GitHub)
  repository_dispatch:
    types: [figma-update]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
          
      - name: Run tests
        run: |
          ./run_tests.sh
  
  sync_figma:
    runs-on: ubuntu-latest
    if: github.event_name == 'repository_dispatch' && github.event.action == 'figma-update'
    needs: test
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install google-cloud-secretmanager google-cloud-aiplatform requests
          
      - name: Set up GCP authentication
        uses: google-github-actions/auth@v1
        with:
          credentials_json: \${{ secrets.GCP_SA_KEY_JSON }}
          
      - name: Set up Figma token
        run: |
          echo "FIGMA_PAT=\${{ secrets.FIGMA_PAT }}" >> \$GITHUB_ENV
          
      - name: Run Figma-GCP sync
        run: |
          python scripts/figma_gcp_sync.py \\
            --file-key ${FIGMA_FILE_ID} \\
            --output-dir ./styles \\
            --project-id ${PROJECT_ID} \\
            --update-secrets \\
            --update-terraform
      
      - name: Commit and push changes
        uses: stefanzweifel/git-auto-commit-action@v4
        with:
          commit_message: "Update design tokens from Figma"
          file_pattern: "styles/* infra/orchestra-terraform/figma_variables.tf"
  
  deploy_dev:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    needs: [test, sync_figma]
    environment: development
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up GCP authentication
        uses: google-github-actions/auth@v1
        with:
          credentials_json: \${{ secrets.GCP_SA_KEY_JSON }}
          
      - name: Set up gcloud CLI
        uses: google-github-actions/setup-gcloud@v1
      
      - name: Deploy to Cloud Run
        run: |
          ./deploy_to_cloud_run.sh dev
EOF

success "Created GitHub Actions workflow for CI/CD"

# Create file for GitHub webhook setup instructions
echo "Creating GitHub webhook setup instructions..."
cat > docs/github_webhook_setup.md << 'EOF'
# Setting Up GitHub Webhooks for Figma Integration

This guide explains how to set up a GitHub webhook to trigger automated workflows when changes occur in your Figma designs.

## Prerequisites

- Admin access to the GitHub repository
- Figma account with access to the design file
- Personal Access Token (PAT) from Figma

## Steps

### 1. Create a GitHub Personal Access Token

1. Go to GitHub Settings > Developer Settings > Personal Access Tokens
2. Generate a new token with the `repo` scope
3. Save the token securely

### 2. Create a Repository Dispatch Webhook

1. Go to your repository settings
2. Navigate to "Webhooks" and click "Add webhook"
3. For the Payload URL, use:
   ```
   https://api.github.com/repos/{owner}/{repo}/dispatches
   ```
   Replace `{owner}` and `{repo}` with your GitHub username and repository name
4. Set Content type to `application/json`
5. For Secret, create a secure random string
6. Select "Let me select individual events" and choose "Repository dispatches"
7. Click "Add webhook"

### 3. Set Up Figma Webhook

1. Use the Figma API to create a webhook:
   ```bash
   curl -X POST \
     -H "X-Figma-Token: YOUR_FIGMA_PAT" \
     -H "Content-Type: application/json" \
     -d '{
       "event_type": "FILE_UPDATE", 
       "team_id": "YOUR_TEAM_ID",
       "passcode": "YOUR_SECURE_PASSCODE",
       "endpoint": "https://api.github.com/repos/{owner}/{repo}/dispatches",
       "description": "Trigger GitHub workflow on Figma changes",
       "client_id": "YOUR_CLIENT_ID",
       "client_secret": "YOUR_CLIENT_SECRET"
     }' \
     https://api.figma.com/v2/webhooks
   ```
   Replace:
   - `YOUR_FIGMA_PAT` with your Figma Personal Access Token
   - `YOUR_TEAM_ID` with your Figma team ID
   - `YOUR_SECURE_PASSCODE` with a secure random string
   - `{owner}` and `{repo}` with your GitHub repository details
   - `YOUR_CLIENT_ID` and `YOUR_CLIENT_SECRET` with your GitHub OAuth application credentials

### 4. Test the Integration

1. Make a small change to your Figma file
2. Save the changes
3. Check the GitHub Actions tab to see if the workflow was triggered

## Troubleshooting

- **Webhook not triggering**: Check the webhook delivery logs in GitHub repository settings
- **Authentication errors**: Verify your Figma PAT and GitHub token have the correct permissions
- **Payload issues**: Ensure the correct event type is being sent from Figma

## Additional Resources

- [GitHub Webhooks Documentation](https://docs.github.com/en/developers/webhooks-and-events/webhooks/about-webhooks)
- [Figma Webhooks API Documentation](https://www.figma.com/developers/api#webhooks-v2)
EOF

success "Created GitHub webhook setup instructions"

section "5. Setting Up GitHub Secrets"

# Create a script to set up GitHub secrets
echo "Creating script for setting up GitHub secrets..."
cat > scripts/setup_github_org_secrets.sh << 'EOF'
#!/bin/bash
# Script to set up GitHub organization/repository secrets for Orchestra

# Determine if we're setting up org or repo secrets
if [ "$1" == "--org" ]; then
    ORG_MODE=true
    ORG_NAME=$2
    shift 2
elif [ "$1" == "--repo" ]; then
    ORG_MODE=false
    REPO_OWNER=$2
    REPO_NAME=$3
    shift 3
else
    echo "Usage: $0 --org ORG_NAME or $0 --repo OWNER REPO"
    exit 1
fi

# GitHub token
if [ -z "$GITHUB_TOKEN" ]; then
    echo "GITHUB_TOKEN environment variable not set"
    echo "Please set it with a token that has admin:org or repo permissions"
    exit 1
fi

# Function to create or update org secret
create_org_secret() {
    local name=$1
    local value=$2
    
    echo "Setting organization secret: $name"
    
    # Get public key for encryption
    local key_response=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
        "https://api.github.com/orgs/$ORG_NAME/actions/secrets/public-key")
    
    local key_id=$(echo $key_response | jq -r .key_id)
    local key=$(echo $key_response | jq -r .key)
    
    # TODO: Implement proper encryption for the value
    # For now, GitHub API handles encryption with the public key
    
    # Create or update the secret
    curl -s -X PUT \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        -d "{\"encrypted_value\":\"$value\", \"key_id\":\"$key_id\", \"visibility\":\"all\"}" \
        "https://api.github.com/orgs/$ORG_NAME/actions/secrets/$name"
}

# Function to create or update repo secret
create_repo_secret() {
    local name=$1
    local value=$2
    
    echo "Setting repository secret: $name"
    
    # Get public key for encryption
    local key_response=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
        "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/actions/secrets/public-key")
    
    local key_id=$(echo $key_response | jq -r .key_id)
    local key=$(echo $key_response | jq -r .key)
    
    # TODO: Implement proper encryption for the value
    # For now, GitHub API handles encryption with the public key
    
    # Create or update the secret
    curl -s -X PUT \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        -d "{\"encrypted_value\":\"$value\", \"key_id\":\"$key_id\"}" \
        "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/actions/secrets/$name"
}

# Main secrets setup
echo "Setting up GitHub secrets for Orchestra..."

# Read service account key
if [ -f "/tmp/vertex-agent-key.json" ]; then
    GCP_SA_KEY_CONTENT=$(cat /tmp/vertex-agent-key.json)
else
    echo "Service account key not found at /tmp/vertex-agent-key.json"
    exit 1
fi

# Read Figma PAT from environment or prompt
FIGMA_PAT=${FIGMA_PAT:-""}
if [ -z "$FIGMA_PAT" ]; then
    read -p "Enter your Figma Personal Access Token: " FIGMA_PAT
fi

# Set up secrets
if [ "$ORG_MODE" == "true" ]; then
    create_org_secret "GCP_SA_KEY_JSON" "$GCP_SA_KEY_CONTENT"
    create_org_secret "GCP_PROJECT_ID" "${GCP_PROJECT_ID:-agi-baby-cherry}"
    create_org_secret "FIGMA_PAT" "$FIGMA_PAT"
else
    create_repo_secret "GCP_SA_KEY_JSON" "$GCP_SA_KEY_CONTENT"
    create_repo_secret "GCP_PROJECT_ID" "${GCP_PROJECT_ID:-agi-baby-cherry}"
    create_repo_secret "FIGMA_PAT" "$FIGMA_PAT"
fi

echo "GitHub secrets setup completed!"
EOF

chmod +x scripts/setup_github_org_secrets.sh
success "Created script for setting up GitHub secrets"

section "6. Running Memory Management Tests"

# Run the memory test with in-memory implementation
echo "Running memory management tests (in-memory)..."
if [ -f "test_memory_inmemory.py" ]; then
    python test_memory_inmemory.py
    success "Memory management tests completed"
else
    warning "test_memory_inmemory.py not found, skipping memory tests"
fi

# Install dependencies from pyproject.toml
install_dependencies() {
    section "Installing Dependencies"
    
    # Check if pyproject.toml exists
    if [ ! -f "pyproject.toml" ]; then
        error "pyproject.toml not found. Please run the script from the project root directory."
        return 1
    fi
    
    # Parse installation profile (default to development mode)
    PROFILE=${1:-"dev"}
    
    case $PROFILE in
        "minimal")
            echo "Installing minimal dependencies..."
            pip install .
            ;;
        "full")
            echo "Installing full dependencies with all extras..."
            pip install ".[all]"
            ;;
        "phidata")
            echo "Installing Phidata-specific dependencies..."
            pip install -e ".[phidata]"
            ;;
        "dev")
            echo "Installing development dependencies..."
            pip install -e ".[dev]"
            ;;
        *)
            warning "Unknown profile: $PROFILE. Defaulting to development installation."
            pip install -e ".[dev]"
            ;;
    esac
    
    # Verify installation
    if python -c "import phi" &> /dev/null; then
        success "Phi/Agno dependencies installed successfully."
    else
        error "Failed to install dependencies. Please check the output for errors."
        return 1
    fi
}

section "Setup Complete"
echo ""
echo -e "${GREEN}Orchestra setup has been completed successfully!${NC}"
echo ""
echo "Next steps:"
echo "  1. Review the terraform_output.json file for connection details"
echo "  2. Check the styles/ directory for the generated design tokens"
echo "  3. Set up GitHub secrets using scripts/setup_github_org_secrets.sh"
echo "  4. Create a webhook from Figma to GitHub using docs/github_webhook_setup.md"
echo ""
echo "For memory management verification, run:"
echo "  python test_memory_inmemory.py"
echo ""
echo "For integration tests (requires real GCP infrastructure):"
echo "  export RUN_INTEGRATION_TESTS=true"
echo "  ./run_integration_tests.sh"
echo ""
echo "To install dependencies from pyproject.toml, run:"
echo "  source ./unified_setup.sh && install_dependencies [profile]"
echo "  Profiles: minimal, full, phidata, dev (default)"
echo ""
echo "Thank you for using Orchestra!"
