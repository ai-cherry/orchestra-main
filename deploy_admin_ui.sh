#!/bin/bash
# deploy_admin_ui.sh - Script to build and deploy Admin UI to DigitalOcean App Platform
# Usage: ./deploy_admin_ui.sh [--skip-build]

set -e  # Exit on any error

# Terminal colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADMIN_UI_DIR="${REPO_ROOT}/admin-ui"
DIST_DIR="${ADMIN_UI_DIR}/dist"
DOMAIN="cherry-ai.me"
APP_NAME="admin-ui-prod"

# Parse command line arguments
SKIP_BUILD=false
for arg in "$@"; do
  case $arg in
    --skip-build)
      SKIP_BUILD=true
      shift
      ;;
  esac
done

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Check required tools
echo -e "${BLUE}Checking required tools...${NC}"
if ! command_exists pnpm; then
  echo -e "${YELLOW}pnpm not found. Installing...${NC}"
  npm install -g pnpm
fi

if ! command_exists doctl; then
  echo -e "${RED}Error: doctl (DigitalOcean CLI) not found.${NC}"
  echo "Please install doctl: https://docs.digitalocean.com/reference/doctl/how-to/install/"
  exit 1
fi

# Authenticate with DigitalOcean if needed
if ! doctl account get > /dev/null 2>&1; then
  echo -e "${YELLOW}Not authenticated with DigitalOcean. Please run:${NC}"
  echo "doctl auth init"
  exit 1
fi

# Build Admin UI
if [ "$SKIP_BUILD" = false ]; then
  echo -e "${BLUE}Building Admin UI...${NC}"
  cd "$ADMIN_UI_DIR"
  
  # Install dependencies
  echo -e "${BLUE}Installing dependencies...${NC}"
  pnpm install
  
  # Build the project
  echo -e "${BLUE}Running build...${NC}"
  pnpm build
  
  # Check if build was successful
  if [ ! -d "$DIST_DIR" ] || [ ! -f "$DIST_DIR/index.html" ]; then
    echo -e "${RED}Error: Build failed! The dist directory or index.html is missing.${NC}"
    exit 1
  fi
  
  echo -e "${GREEN}Build successful!${NC}"
else
  echo -e "${YELLOW}Skipping build step...${NC}"
  
  # Still check if dist exists
  if [ ! -d "$DIST_DIR" ] || [ ! -f "$DIST_DIR/index.html" ]; then
    echo -e "${RED}Error: dist directory or index.html is missing. Cannot deploy.${NC}"
    exit 1
  fi
fi

# Deploy to DigitalOcean App Platform
echo -e "${BLUE}Deploying to DigitalOcean App Platform...${NC}"

# Check if app exists
if doctl apps get "$APP_NAME" > /dev/null 2>&1; then
  echo -e "${BLUE}Updating existing app: $APP_NAME${NC}"
  
  # Create a temporary spec file
  TEMP_SPEC=$(mktemp)
  doctl apps get "$APP_NAME" --format Spec --no-header > "$TEMP_SPEC"
  
  # Update the app with the new build
  doctl apps update "$APP_NAME" --spec "$TEMP_SPEC" --upsert
  rm "$TEMP_SPEC"
else
  echo -e "${BLUE}Creating new app: $APP_NAME${NC}"
  
  # Create app spec
  cat > app_spec.yaml << EOF
name: $APP_NAME
region: sfo2
static_sites:
- name: admin-ui-site
  source_dir: $DIST_DIR
  build_command: echo "Using pre-built assets"
  output_dir: .
  index_document: index.html
  error_document: index.html
  catchall_document: index.html
  routes:
  - path: /
domains:
- domain: $DOMAIN
  type: PRIMARY
EOF
  
  # Create the app
  doctl apps create --spec app_spec.yaml
  rm app_spec.yaml
fi

# Wait for deployment to complete
echo -e "${BLUE}Waiting for deployment to complete...${NC}"
APP_ID=$(doctl apps get "$APP_NAME" --format ID --no-header)
doctl apps get "$APP_ID" --format "DefaultIngress,LiveURL" --no-header

echo -e "${GREEN}Deployment initiated! Your site should be available soon at:${NC}"
echo -e "${GREEN}https://$DOMAIN${NC}"
echo ""
echo -e "${YELLOW}Note: DNS and SSL certificate propagation may take up to 15 minutes.${NC}"
echo -e "${YELLOW}You can check deployment status with: doctl apps get $APP_NAME${NC}"

# Check site accessibility
echo -e "${BLUE}Checking site accessibility...${NC}"
if curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN"; then
  echo -e "${GREEN}Site is accessible!${NC}"
else
  echo -e "${YELLOW}Site is not yet accessible. This is normal during initial deployment.${NC}"
  echo -e "${YELLOW}Please check again in a few minutes.${NC}"
fi

echo -e "${GREEN}Deployment process completed!${NC}"
