#!/bin/bash
# Immediate Migration Execution Script
# This script will immediately run the migration process with minimal user input.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "${SCRIPT_DIR}/.."

# Banner
echo -e "${BLUE}${BOLD}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║             IMMEDIATE GCP MIGRATION EXECUTION                 ║"
echo "║          Running AI Orchestra Migration to GCP NOW!           ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check for gcloud CLI
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}${BOLD}ERROR: gcloud CLI is required but not found${NC}"
    echo -e "Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check for GitHub CLI
if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}WARNING: GitHub CLI (gh) not found. Some operations will fail${NC}"
    echo -e "Consider installing it: https://cli.github.com/manual/installation"
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}${BOLD}ERROR: Python 3 is required but not found${NC}"
    exit 1
fi

# Initialize directory structure
echo -e "${BLUE}[1/8] Initializing integration structure...${NC}"
mkdir -p gcp_migration/templates
mkdir -p gcp_migration/.github/workflows
mkdir -p gcp_migration/tests
chmod +x "${SCRIPT_DIR}/init_integration_structure.sh"
"${SCRIPT_DIR}/init_integration_structure.sh"
echo -e "${GREEN}✓ Integration structure initialized${NC}"

# Install required dependencies
echo -e "\n${BLUE}[2/8] Installing required dependencies...${NC}"
if [ -f "${SCRIPT_DIR}/fixed_requirements.txt" ]; then
    # Upgrade pip first to ensure latest version
    python3 -m pip install --upgrade pip
    
    # Install dependencies using pip to avoid permission issues
    echo -e "${YELLOW}Installing required Python packages...${NC}"
    pip install -r "${SCRIPT_DIR}/fixed_requirements.txt"
    
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}ERROR: fixed_requirements.txt not found at ${SCRIPT_DIR}/fixed_requirements.txt${NC}"
    exit 1
fi

# Get GCP Project ID
echo -e "\n${BLUE}[3/8] Configuring GCP project...${NC}"
GCP_PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$GCP_PROJECT_ID" ]; then
    echo -e "${YELLOW}No GCP project is currently set.${NC}"
    read -p "Enter your GCP Project ID: " GCP_PROJECT_ID
    gcloud config set project "$GCP_PROJECT_ID"
fi
echo -e "${GREEN}✓ Using GCP project: ${GCP_PROJECT_ID}${NC}"

# Get GCP Region
GCP_REGION=$(gcloud config get-value compute/region 2>/dev/null)
if [ -z "$GCP_REGION" ]; then
    GCP_REGION="us-central1"
    gcloud config set compute/region "$GCP_REGION"
fi
echo -e "${GREEN}✓ Using GCP region: ${GCP_REGION}${NC}"

# Get or create service account key
echo -e "\n${BLUE}[4/8] Setting up service account authentication...${NC}"

# Check if we already have credentials from the environment
if [ -n "$GCP_MASTER_SERVICE_JSON" ]; then
    echo -e "${GREEN}Using existing GCP_MASTER_SERVICE_JSON from environment${NC}"
    # Create credentials directory if it doesn't exist
    mkdir -p "${SCRIPT_DIR}/credentials"
    KEY_FILE="${SCRIPT_DIR}/credentials/orchestra-migration-key.json"
    
    # Write the environment variable content to a file
    echo "$GCP_MASTER_SERVICE_JSON" > "$KEY_FILE"
    echo -e "${GREEN}✓ Service account key saved from environment variable${NC}"
elif [ -n "$GCP_PROJECT_MANAGEMENT_KEY" ]; then
    echo -e "${GREEN}Using existing GCP_PROJECT_MANAGEMENT_KEY from environment${NC}"
    # Create credentials directory if it doesn't exist
    mkdir -p "${SCRIPT_DIR}/credentials"
    KEY_FILE="${SCRIPT_DIR}/credentials/orchestra-migration-key.json"
    
    # Write the environment variable content to a file
    echo "$GCP_PROJECT_MANAGEMENT_KEY" > "$KEY_FILE"
    echo -e "${GREEN}✓ Service account key saved from environment variable${NC}"
else
    # If no environment variable exists, try to create a new service account
    SA_NAME="ai-orchestra-migration"
    SA_EMAIL="${SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
    KEY_FILE="${SCRIPT_DIR}/credentials/orchestra-migration-key.json"

    # Create credentials directory if it doesn't exist
    mkdir -p "${SCRIPT_DIR}/credentials"

    # Check if service account exists
    if ! gcloud iam service-accounts describe "$SA_EMAIL" &>/dev/null; then
        echo -e "${YELLOW}Creating service account: ${SA_EMAIL}${NC}"
        gcloud iam service-accounts create "$SA_NAME" \
            --display-name="AI Orchestra Migration Service Account"

        # Grant necessary permissions
        echo -e "${YELLOW}Granting necessary permissions...${NC}"
        gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
            --member="serviceAccount:${SA_EMAIL}" \
            --role="roles/editor"
        
        gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
            --member="serviceAccount:${SA_EMAIL}" \
            --role="roles/secretmanager.admin"
    fi

    # Create key if it doesn't exist
    if [ ! -f "$KEY_FILE" ]; then
        echo -e "${YELLOW}Creating service account key: ${KEY_FILE}${NC}"
        gcloud iam service-accounts keys create "$KEY_FILE" \
            --iam-account="$SA_EMAIL"
    fi
fi

# Set environment variable with full path to key file
export GOOGLE_APPLICATION_CREDENTIALS="$KEY_FILE"
# Also set the legacy environment variable for compatibility
export GCP_MASTER_SERVICE_JSON="$KEY_FILE"
echo -e "${GREEN}✓ Service account authentication configured${NC}"

# Get GitHub organization and token
echo -e "\n${BLUE}[5/8] Setting up GitHub authentication...${NC}"

# Check if GitHub token is already in environment
if [ -n "$GH_CLASSIC_PAT_TOKEN" ]; then
    echo -e "${GREEN}Using existing GitHub token from environment${NC}"
    
    # Try to extract username from the token
    if command -v gh &> /dev/null; then
        # Set the token for gh CLI
        echo "$GH_CLASSIC_PAT_TOKEN" | gh auth login --with-token
        GH_USER=$(gh api user | jq -r '.login')
        echo -e "${GREEN}✓ Authenticated as GitHub user: ${GH_USER}${NC}"
        
        # List organizations and select one
        echo -e "${YELLOW}Listing your GitHub organizations...${NC}"
        GH_ORGS=$(gh api user/orgs | jq -r '.[].login')
        
        if [ -z "$GH_ORGS" ]; then
            echo -e "${YELLOW}No organizations found. Using your username as the organization.${NC}"
            GITHUB_ORG="$GH_USER"
        else
            echo "Available organizations:"
            select ORG in $GH_ORGS "$GH_USER (personal)"; do
                if [ -n "$ORG" ]; then
                    if [ "$ORG" = "$GH_USER (personal)" ]; then
                        GITHUB_ORG="$GH_USER"
                    else
                        GITHUB_ORG="$ORG"
                    fi
                    break
                fi
            done
        fi
    else
        # Manual input if gh CLI not available
        read -p "Enter your GitHub organization name: " GITHUB_ORG
    fi
else
    # If token not in environment, try gh CLI or manual input
    if command -v gh &> /dev/null; then
        # Check if already authenticated
        if ! gh auth status &>/dev/null; then
            echo -e "${YELLOW}Please authenticate with GitHub:${NC}"
            gh auth login
        fi
        
        # Try to get user and orgs
        GH_USER=$(gh api user | jq -r '.login')
        echo -e "${GREEN}✓ Authenticated as GitHub user: ${GH_USER}${NC}"
        
        # List organizations and select one
        echo -e "${YELLOW}Listing your GitHub organizations...${NC}"
        GH_ORGS=$(gh api user/orgs | jq -r '.[].login')
        
        if [ -z "$GH_ORGS" ]; then
            echo -e "${YELLOW}No organizations found. Using your username as the organization.${NC}"
            GITHUB_ORG="$GH_USER"
        else
            echo "Available organizations:"
            select ORG in $GH_ORGS "$GH_USER (personal)"; do
                if [ -n "$ORG" ]; then
                    if [ "$ORG" = "$GH_USER (personal)" ]; then
                        GITHUB_ORG="$GH_USER"
                    else
                        GITHUB_ORG="$ORG"
                    fi
                    break
                fi
            done
        fi
        
        # Get token
        echo -e "${YELLOW}Creating a GitHub token with necessary scopes...${NC}"
        GH_CLASSIC_PAT_TOKEN=$(gh auth token)
        export GH_CLASSIC_PAT_TOKEN
    else
        # Manual input if gh CLI not available
        read -p "Enter your GitHub organization name: " GITHUB_ORG
        if [ -z "$GH_CLASSIC_PAT_TOKEN" ]; then
            read -sp "Enter your GitHub Personal Access Token: " GH_CLASSIC_PAT_TOKEN
            echo ""
            export GH_CLASSIC_PAT_TOKEN
        fi
    fi
fi

echo -e "${GREEN}✓ Using GitHub organization: ${GITHUB_ORG}${NC}"
echo -e "${GREEN}✓ GitHub authentication configured${NC}"

# Run the repository setup for GitHub
echo -e "\n${BLUE}[6/8] Setting up GitHub repository...${NC}"
GITHUB_REPO="${GITHUB_ORG}/orchestra-main"

if command -v gh &> /dev/null; then
    # Check if repo exists
    if ! gh repo view "$GITHUB_REPO" &>/dev/null; then
        echo -e "${YELLOW}Repository ${GITHUB_REPO} does not exist.${NC}"
        read -p "Would you like to create it? (y/n): " CREATE_REPO
        if [[ "$CREATE_REPO" =~ ^[Yy]$ ]]; then
            gh repo create "$GITHUB_REPO" --public
            echo -e "${GREEN}✓ Repository created: ${GITHUB_REPO}${NC}"
        else
            echo -e "${YELLOW}Using existing repository name for configuration only.${NC}"
        fi
    else
        echo -e "${GREEN}✓ Repository exists: ${GITHUB_REPO}${NC}"
    fi
fi

# Enable APIs
echo -e "\n${BLUE}[7/8] Enabling required GCP APIs...${NC}"
gcloud services enable iam.googleapis.com \
  cloudresourcemanager.googleapis.com \
  secretmanager.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  iamcredentials.googleapis.com
echo -e "${GREEN}✓ Required GCP APIs enabled${NC}"

# Run the full integration setup
echo -e "\n${BLUE}[8/8] Running GCP-GitHub integration...${NC}"
chmod +x "${SCRIPT_DIR}/setup_gcp_github_integration.py"

# Check if we have Workload Identity Provider info
if [ -n "$GCP_WORKLOAD_IDENTITY_PROVIDER" ]; then
    echo -e "${GREEN}Using existing Workload Identity Provider from environment${NC}"
    WIF_ARGS="--workload-identity-provider=\"$GCP_WORKLOAD_IDENTITY_PROVIDER\""
else
    WIF_ARGS=""
fi

# Check if we have Project Authentication Email
if [ -n "$GCP_PROJECT_AUTHENTICATION_EMAIL" ]; then
    echo -e "${GREEN}Using existing Project Authentication Email from environment${NC}"
    AUTH_EMAIL_ARGS="--service-account=\"$GCP_PROJECT_AUTHENTICATION_EMAIL\""
else
    AUTH_EMAIL_ARGS=""
fi

echo -e "${YELLOW}Running integration setup script...${NC}"
CMD="python3 \"${SCRIPT_DIR}/setup_gcp_github_integration.py\" setup \
  --project-id=\"$GCP_PROJECT_ID\" \
  --region=\"$GCP_REGION\" \
  --github-org=\"$GITHUB_ORG\" \
  --github-repo=\"$GITHUB_REPO\" \
  $WIF_ARGS $AUTH_EMAIL_ARGS \
  --verbose"

echo -e "${YELLOW}Executing: $CMD${NC}"
eval $CMD

# Verify the integration
echo -e "\n${BLUE}Verifying integration...${NC}"
python3 "${SCRIPT_DIR}/setup_gcp_github_integration.py" verify \
  --project-id="$GCP_PROJECT_ID" \
  --region="$GCP_REGION" \
  --github-org="$GITHUB_ORG" \
  --github-repo="$GITHUB_REPO"

echo -e "\n${GREEN}${BOLD}GCP MIGRATION COMPLETE!${NC}"
echo -e "Your GitHub repository is now integrated with GCP and ready for deployments."
echo -e "\n${BLUE}Next Steps:${NC}"
echo -e "1. Push your code to the GitHub repository"
echo -e "2. GitHub Actions will automatically deploy to Cloud Run"
echo -e "3. Monitor deployments in GitHub Actions tab"
echo -e "\nFor more information, see: ${YELLOW}gcp_migration/GCP_GITHUB_INTEGRATION.md${NC}"

# Clean up the service account key file
echo -e "\n${YELLOW}Cleaning up sensitive files...${NC}"
if [ -f "$KEY_FILE" ]; then
    shred -u "$KEY_FILE"
    echo -e "${GREEN}✓ Service account key file securely deleted${NC}"
fi

echo -e "\n${GREEN}${BOLD}AI Orchestra is now running in Google Cloud Platform!${NC}"