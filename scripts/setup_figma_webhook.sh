#!/bin/bash
# Figma Webhook Setup Script
# This script sets up a Figma webhook that triggers a GitHub repository dispatch event
# when a Figma file is updated.

set -e

# Colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print usage information
usage() {
  echo -e "${BLUE}Figma Webhook Setup Script${NC}"
  echo ""
  echo "This script sets up a Figma webhook to trigger a GitHub Actions workflow"
  echo "when a specific Figma file is updated."
  echo ""
  echo "Usage:"
  echo "  $0 --file-key <figma_file_key> --team-id <figma_team_id> --github-repo <owner/repo> --github-token <token> [options]"
  echo ""
  echo "Required Arguments:"
  echo "  --file-key          Figma file key (from the URL)"
  echo "  --team-id           Figma team ID"
  echo "  --github-repo       GitHub repository in format 'owner/repo'"
  echo "  --github-token      GitHub personal access token with repo scope"
  echo ""
  echo "Optional Arguments:"
  echo "  --figma-pat         Figma Personal Access Token (if not set, will use FIGMA_PAT env var)"
  echo "  --endpoint-url      Custom endpoint URL (default: GitHub repository dispatch endpoint)"
  echo "  --secret            Webhook secret for added security (recommended)"
  echo "  --event-types       Comma-separated list of event types (default: FILE_UPDATE)"
  echo "  --description       Description for the webhook (default: 'Figma to GitHub webhook')"
  echo "  --help              Show this help message"
}

# Check if required tools are installed
check_requirements() {
  if ! command -v curl &> /dev/null; then
    echo -e "${RED}Error: curl is not installed${NC}"
    exit 1
  fi

  if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is not installed${NC}"
    echo "Please install jq: apt-get install jq or yum install jq"
    exit 1
  fi
}

# Parse command line arguments
parse_args() {
  while [[ $# -gt 0 ]]; do
    case $1 in
      --file-key)
        FILE_KEY="$2"
        shift 2
        ;;
      --team-id)
        TEAM_ID="$2"
        shift 2
        ;;
      --github-repo)
        GITHUB_REPO="$2"
        shift 2
        ;;
      --github-token)
        GITHUB_TOKEN="$2"
        shift 2
        ;;
      --figma-pat)
        FIGMA_PAT="$2"
        shift 2
        ;;
      --endpoint-url)
        ENDPOINT_URL="$2"
        shift 2
        ;;
      --secret)
        WEBHOOK_SECRET="$2"
        shift 2
        ;;
      --event-types)
        EVENT_TYPES="$2"
        shift 2
        ;;
      --description)
        DESCRIPTION="$2"
        shift 2
        ;;
      --help)
        usage
        exit 0
        ;;
      *)
        echo -e "${RED}Error: Unknown option $1${NC}"
        usage
        exit 1
        ;;
    esac
  done
}

# Validate required arguments
validate_args() {
  MISSING=""
  
  if [ -z "$FILE_KEY" ]; then
    MISSING="$MISSING --file-key"
  fi
  
  if [ -z "$TEAM_ID" ]; then
    MISSING="$MISSING --team-id"
  fi
  
  if [ -z "$GITHUB_REPO" ]; then
    MISSING="$MISSING --github-repo"
  fi
  
  if [ -z "$GITHUB_TOKEN" ]; then
    MISSING="$MISSING --github-token"
  fi
  
  if [ -z "$FIGMA_PAT" ]; then
    FIGMA_PAT="${FIGMA_PAT:-$FIGMA_PAT_ENV}"
    if [ -z "$FIGMA_PAT" ]; then
      MISSING="$MISSING --figma-pat or FIGMA_PAT env var"
    fi
  fi
  
  if [ ! -z "$MISSING" ]; then
    echo -e "${RED}Error: Missing required arguments:${NC}$MISSING"
    usage
    exit 1
  fi
}

# Set default values for optional arguments
set_defaults() {
  EVENT_TYPES="${EVENT_TYPES:-FILE_UPDATE}"
  DESCRIPTION="${DESCRIPTION:-Figma to GitHub webhook}"
  
  if [ -z "$ENDPOINT_URL" ]; then
    ENDPOINT_URL="https://api.github.com/repos/${GITHUB_REPO}/dispatches"
  fi
  
  if [ -z "$WEBHOOK_SECRET" ]; then
    # Generate random secret if not provided
    WEBHOOK_SECRET=$(openssl rand -hex 16)
    echo -e "${YELLOW}Warning: No webhook secret provided. Using generated secret:${NC} $WEBHOOK_SECRET"
    echo -e "${YELLOW}Store this secret securely for future use.${NC}"
  fi
}

# Create the webhook
create_webhook() {
  echo -e "${BLUE}Creating Figma webhook...${NC}"
  
  # Prepare webhook payload
  WEBHOOK_PAYLOAD=$(cat <<EOF
{
  "event_type": "${EVENT_TYPES}",
  "team_id": "${TEAM_ID}",
  "description": "${DESCRIPTION}",
  "endpoint": "${ENDPOINT_URL}",
  "passcode": "${WEBHOOK_SECRET}",
  "status": "ACTIVE"
}
EOF
)

  # Create webhook using Figma API
  WEBHOOK_RESPONSE=$(curl -s -X POST "https://api.figma.com/v2/webhooks" \
    -H "X-Figma-Token: ${FIGMA_PAT}" \
    -H "Content-Type: application/json" \
    -d "${WEBHOOK_PAYLOAD}")
  
  # Check if webhook was created successfully
  if echo "$WEBHOOK_RESPONSE" | jq -e '.id' > /dev/null; then
    WEBHOOK_ID=$(echo "$WEBHOOK_RESPONSE" | jq -r '.id')
    echo -e "${GREEN}✓ Webhook created successfully!${NC}"
    echo -e "Webhook ID: ${BLUE}${WEBHOOK_ID}${NC}"
    echo -e "Event type: ${EVENT_TYPES}"
    echo -e "Endpoint: ${ENDPOINT_URL}"
    
    # Save webhook details to file
    save_webhook_details "$WEBHOOK_ID"
  else
    ERROR_MSG=$(echo "$WEBHOOK_RESPONSE" | jq -r '.message')
    echo -e "${RED}✗ Failed to create webhook: ${ERROR_MSG}${NC}"
    exit 1
  fi
}

# Save webhook details for future reference
save_webhook_details() {
  WEBHOOK_ID=$1
  DETAILS_FILE="figma_webhook_details.json"
  
  cat > "$DETAILS_FILE" <<EOF
{
  "webhook_id": "${WEBHOOK_ID}",
  "file_key": "${FILE_KEY}",
  "team_id": "${TEAM_ID}",
  "event_types": "${EVENT_TYPES}",
  "endpoint": "${ENDPOINT_URL}",
  "description": "${DESCRIPTION}",
  "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF

  echo -e "${GREEN}✓ Webhook details saved to ${DETAILS_FILE}${NC}"
}

# Configure GitHub repository secret for webhook
configure_github_secret() {
  echo -e "\n${BLUE}Configuring GitHub repository secret for webhook...${NC}"
  
  # Encode the secret for the GitHub API
  PUBLIC_KEY_RESPONSE=$(curl -s -H "Authorization: token ${GITHUB_TOKEN}" \
    "https://api.github.com/repos/${GITHUB_REPO}/actions/secrets/public-key")
  
  if ! echo "$PUBLIC_KEY_RESPONSE" | jq -e '.key' > /dev/null; then
    ERROR_MSG=$(echo "$PUBLIC_KEY_RESPONSE" | jq -r '.message')
    echo -e "${RED}✗ Failed to get GitHub public key: ${ERROR_MSG}${NC}"
    echo -e "${YELLOW}Skipping GitHub secret configuration. You will need to manually set the FIGMA_WEBHOOK_SECRET secret.${NC}"
    return
  fi
  
  PUBLIC_KEY=$(echo "$PUBLIC_KEY_RESPONSE" | jq -r '.key')
  PUBLIC_KEY_ID=$(echo "$PUBLIC_KEY_RESPONSE" | jq -r '.key_id')
  
  # Encode the secret (this requires the npm package @actions/core which we won't use here)
  # Instead, provide instructions for manual configuration
  echo -e "${YELLOW}To complete the setup, manually add the following secret to your GitHub repository:${NC}"
  echo -e "Secret name: ${BLUE}FIGMA_WEBHOOK_SECRET${NC}"
  echo -e "Secret value: ${BLUE}${WEBHOOK_SECRET}${NC}"
  echo -e "\nYou can add this secret at: https://github.com/${GITHUB_REPO}/settings/secrets/actions"
}

# Display instructions for GitHub Actions workflow
display_workflow_instructions() {
  echo -e "\n${BLUE}GitHub Actions Workflow Instructions${NC}"
  echo -e "${YELLOW}Make sure your GitHub Actions workflow is configured to handle the repository_dispatch event:${NC}"
  
  cat <<EOF

Create or update your workflow file (e.g., .github/workflows/figma-triggered.yml) with:

name: Figma Integration

on:
  repository_dispatch:
    types: [figma-update]

jobs:
  process-figma-update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Verify webhook signature
        env:
          WEBHOOK_SECRET: \${{ secrets.FIGMA_WEBHOOK_SECRET }}
        run: |
          # Add webhook signature verification here
      
      - name: Process Figma update
        run: |
          # Add your Figma sync logic here
EOF
}

# Main function
main() {
  check_requirements
  parse_args "$@"
  
  # Get FIGMA_PAT from environment if not provided as argument
  FIGMA_PAT_ENV=${FIGMA_PAT:-$FIGMA_PAT}
  
  validate_args
  set_defaults
  
  # Create webhook and save details
  create_webhook
  
  # Configure GitHub secret and display instructions
  configure_github_secret
  display_workflow_instructions
  
  echo -e "\n${GREEN}✓ Figma webhook setup completed successfully!${NC}"
}

# Entry point
main "$@"
