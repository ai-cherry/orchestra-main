#!/bin/bash
# Unified Secret Management - GitHub to GCP Secret Manager Migration Tool
# This script migrates GitHub Secrets to Google Cloud Secret Manager
# with robust error handling and detailed reporting

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}${BOLD}   GitHub Secrets to GCP Secret Manager Migration   ${NC}"
echo -e "${BLUE}======================================================${NC}"
echo -e "${YELLOW}This tool migrates GitHub organization/repository secrets to GCP Secret Manager${NC}"

# Default values
PROJECT_ID=${GCP_PROJECT_ID:-"cherry-ai-project"}
ENVIRONMENT="prod"
INTERACTIVE=true
DRY_RUN=false
GITHUB_TOKEN=${GITHUB_TOKEN:-""}
GITHUB_ORG=""
GITHUB_REPO=""
MAPPING_FILE=""
OUTPUT_FILE=""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not found.${NC}"
    exit 1
fi

# Function to display usage
usage() {
    echo -e "\n${BOLD}Usage:${NC}"
    echo -e "  $0 [options]"
    echo -e "\n${BOLD}Options:${NC}"
    echo -e "  --project-id <id>       GCP Project ID (default: from GCP_PROJECT_ID env var or 'cherry-ai-project')"
    echo -e "  --github-token <token>  GitHub Personal Access Token (default: from GITHUB_TOKEN env var)"
    echo -e "  --github-org <org>      GitHub organization name (for org-level secrets)"
    echo -e "  --github-repo <repo>    GitHub repository name (for repo-level secrets)"
    echo -e "  --environment <env>     Environment suffix for secrets (default: 'prod')"
    echo -e "  --mapping-file <file>   Custom JSON mapping file"
    echo -e "  --non-interactive       Don't prompt for secret values"
    echo -e "  --dry-run               Simulate migration without making changes"
    echo -e "  --output <file>         Write report to file"
    echo -e "  --help                  Display this help message and exit"
    echo -e "\n${BOLD}Example:${NC}"
    echo -e "  $0 --github-org orchestra-project --environment dev"
    echo -e "\n${BOLD}Note:${NC}"
    echo -e "  GitHub secrets are encrypted and their values cannot be retrieved directly."
    echo -e "  You will be prompted to enter the secret values manually during migration."
    exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project-id)
            PROJECT_ID="$2"
            shift 2
            ;;
        --github-token)
            GITHUB_TOKEN="$2"
            shift 2
            ;;
        --github-org)
            GITHUB_ORG="$2"
            shift 2
            ;;
        --github-repo)
            GITHUB_REPO="$2"
            shift 2
            ;;
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --mapping-file)
            MAPPING_FILE="$2"
            shift 2
            ;;
        --non-interactive)
            INTERACTIVE=false
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --help)
            usage
            ;;
        *)
            echo -e "${RED}Error: Unknown option: $1${NC}"
            usage
            ;;
    esac
done

# Check required parameters
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: GCP Project ID is required.${NC}"
    echo -e "Provide it with --project-id or set GCP_PROJECT_ID environment variable."
    usage
fi

if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}Error: GitHub token is required.${NC}"
    echo -e "Provide it with --github-token or set GITHUB_TOKEN environment variable."
    usage
fi

if [ -z "$GITHUB_ORG" ] && [ -z "$GITHUB_REPO" ]; then
    echo -e "${RED}Error: Either GitHub organization or repository must be specified.${NC}"
    echo -e "Use --github-org or --github-repo."
    usage
fi

# Check for GitHub CLI and install if needed
if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}GitHub CLI not found. Attempting to install...${NC}"
    
    if command -v apt-get &> /dev/null; then
        # Ubuntu/Debian
        echo -e "${BLUE}Installing GitHub CLI via apt...${NC}"
        curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
        sudo apt update
        sudo apt install gh -y
    elif command -v brew &> /dev/null; then
        # macOS with Homebrew
        echo -e "${BLUE}Installing GitHub CLI via Homebrew...${NC}"
        brew install gh
    else
        echo -e "${RED}Unable to install GitHub CLI automatically.${NC}"
        echo -e "Please install the GitHub CLI (gh) manually: https://cli.github.com/manual/installation"
        exit 1
    fi
fi

# Check authentication to GCP
echo -e "${YELLOW}Checking GCP authentication...${NC}"
if ! gcloud auth print-access-token &>/dev/null; then
    echo -e "${RED}Not authenticated to GCP. Run 'gcloud auth login' first.${NC}"
    exit 1
fi

# Set GCP Project
echo -e "${YELLOW}Setting GCP project to: $PROJECT_ID${NC}"
gcloud config set project "$PROJECT_ID" > /dev/null

# Prepare command arguments
CMD_ARGS=()

# Add GitHub token
CMD_ARGS+=("--github-token" "$GITHUB_TOKEN")

# Add GCP project ID
CMD_ARGS+=("--gcp-project-id" "$PROJECT_ID")

# Add GitHub organization or repository
if [ -n "$GITHUB_ORG" ]; then
    CMD_ARGS+=("--github-org" "$GITHUB_ORG")
else
    CMD_ARGS+=("--github-repo" "$GITHUB_REPO")
fi

# Add environment
CMD_ARGS+=("--environment" "$ENVIRONMENT")

# Add mapping file if provided
if [ -n "$MAPPING_FILE" ]; then
    CMD_ARGS+=("--mapping-file" "$MAPPING_FILE")
fi

# Add interactive mode
if [ "$INTERACTIVE" = false ]; then
    CMD_ARGS+=("--non-interactive")
fi

# Add dry run mode
if [ "$DRY_RUN" = true ]; then
    CMD_ARGS+=("--dry-run")
fi

# Add output file if provided
if [ -n "$OUTPUT_FILE" ]; then
    CMD_ARGS+=("--output" "$OUTPUT_FILE")
fi

# Display migration settings
echo -e "\n${BLUE}Migration settings:${NC}"
echo -e "  ${BOLD}GCP Project:${NC} $PROJECT_ID"
if [ -n "$GITHUB_ORG" ]; then
    echo -e "  ${BOLD}GitHub Organization:${NC} $GITHUB_ORG"
else
    echo -e "  ${BOLD}GitHub Repository:${NC} $GITHUB_REPO"
fi
echo -e "  ${BOLD}Environment:${NC} $ENVIRONMENT"
if [ -n "$MAPPING_FILE" ]; then
    echo -e "  ${BOLD}Custom Mapping:${NC} $MAPPING_FILE"
fi
if [ "$INTERACTIVE" = false ]; then
    echo -e "  ${BOLD}Mode:${NC} Non-interactive"
else
    echo -e "  ${BOLD}Mode:${NC} Interactive"
fi
if [ "$DRY_RUN" = true ]; then
    echo -e "  ${BOLD}Dry Run:${NC} Yes (no changes will be made)"
fi

# Confirm before proceeding
if [ "$DRY_RUN" = false ]; then
    echo -e "\n${YELLOW}Warning: This will migrate GitHub secrets to GCP Secret Manager.${NC}"
    read -p "Do you want to continue? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Migration cancelled by user.${NC}"
        exit 1
    fi
fi

# Install required Python packages
echo -e "\n${BLUE}Checking Python dependencies...${NC}"
if ! python3 -c "import google.cloud.secretmanager" 2>/dev/null; then
    echo -e "${YELLOW}Installing Google Cloud Secret Manager Python package...${NC}"
    pip install google-cloud-secretmanager
fi

# Run the migration script
echo -e "\n${BLUE}Starting migration...${NC}"
python3 -m secret_management.python.gcp_secret_client.github_migrator "${CMD_ARGS[@]}"

# Exit with the same exit code as the Python script
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}Migration completed successfully!${NC}"
    
    if [ "$DRY_RUN" = false ]; then
        # Add instructions for integrating with GitHub Actions
        echo -e "\n${BLUE}To use GCP Secret Manager in GitHub Actions:${NC}"
        echo -e "1. Add the following to your GitHub workflow:"
        echo -e "   ${YELLOW}
      - name: 'Authenticate to Google Cloud'
        uses: 'google-github-actions/auth@v1'
        with:
          credentials_json: '\${{ secrets.GCP_SA_KEY }}'

      - name: 'Set up Cloud SDK'
        uses: 'google-github-actions/setup-gcloud@v1'

      - name: 'Access secret from Secret Manager'
        run: |
          SECRET_VALUE=\$(gcloud secrets versions access latest --secret=SECRET_NAME-${ENVIRONMENT})
          echo \"SECRET_VALUE=\$SECRET_VALUE\" >> \$GITHUB_ENV
        ${NC}"
        echo -e "2. Replace ${BOLD}SECRET_NAME${NC} with the name of your secret"
    fi
else
    echo -e "\n${RED}Migration failed with exit code $EXIT_CODE!${NC}"
fi

exit $EXIT_CODE