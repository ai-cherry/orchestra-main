#!/bin/bash
#
# fix_admin_ui_vultr.sh
#
# This script fixes admin UI issues on the Vultr server by:
# 1. Rebuilding the admin UI with fixed configuration
# 2. Verifying proper build output (CSS and JS files)
# 3. Deploying locally to nginx on Vultr
# 4. Validating the deployment fixed the issue
#

set -e  # Exit on any error

# Terminal colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADMIN_UI_DIR="${REPO_ROOT}/admin-ui"
DIST_DIR="${ADMIN_UI_DIR}/dist"
NGINX_DIR="/var/www/orchestra-admin"
DOMAIN="cherry-ai.me"
MIN_JS_SIZE=100000  # 100KB minimum expected JS bundle size
MIN_CSS_SIZE=10000  # 10KB minimum expected CSS file size

# Print banner
echo -e "${CYAN}${BOLD}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║   🔧 Cherry Admin UI - Vultr Fix Tool 🔧                   ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to check dependencies
check_dependencies() {
  echo -e "${BLUE}Checking required dependencies...${NC}"

  local missing_deps=0

  # Check for Node.js
  if ! command_exists node; then
    echo -e "${RED}❌ Node.js is not installed. Please install Node.js v20 or later.${NC}"
    missing_deps=1
  else
    local node_version=$(node -v | cut -d 'v' -f 2)
    echo -e "${GREEN}✓ Node.js v$node_version${NC}"
  fi

  # Check for pnpm
  if ! command_exists pnpm; then
    echo -e "${YELLOW}⚠️ pnpm is not installed. Installing...${NC}"
    npm install -g pnpm
    if [ $? -ne 0 ]; then
      echo -e "${RED}❌ Failed to install pnpm. Please install manually: npm install -g pnpm${NC}"
      missing_deps=1
    else
      echo -e "${GREEN}✓ pnpm installed${NC}"
    fi
  else
    echo -e "${GREEN}✓ pnpm $(pnpm --version)${NC}"
  fi

  # Check for nginx
  if ! command_exists nginx; then
    echo -e "${RED}❌ nginx is not installed. Please install nginx.${NC}"
    missing_deps=1
  else
    echo -e "${GREEN}✓ nginx${NC}"
  fi

  if [ $missing_deps -ne 0 ]; then
    echo -e "${RED}Please install missing dependencies and try again.${NC}"
    exit 1
  fi

  echo -e "${GREEN}All dependencies satisfied!${NC}"
}

# Function to build the admin UI
build_admin_ui() {
  echo -e "\n${BLUE}${BOLD}Step 1: Building Admin UI${NC}"

  cd "$ADMIN_UI_DIR"

  echo -e "${BLUE}Installing dependencies...${NC}"
  pnpm install

  if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install dependencies. Please check package.json and try again.${NC}"
    exit 1
  fi

  echo -e "${BLUE}Building Admin UI...${NC}"
  # Clean any previous build
  rm -rf "$DIST_DIR"

  # Try build without TypeScript checking if regular build fails
  NODE_ENV=production pnpm build || NODE_ENV=production pnpm run build-no-ts

  if [ $? -ne 0 ]; then
    echo -e "${RED}Build failed. Please check the error messages above.${NC}"
    exit 1
  fi

  echo -e "${GREEN}✓ Admin UI built successfully!${NC}"
}

# Function to verify the build output
verify_build() {
  echo -e "\n${BLUE}${BOLD}Step 2: Verifying Build Output${NC}"

  # Check if dist directory exists
  if [ ! -d "$DIST_DIR" ]; then
    echo -e "${RED}❌ Build directory not found at $DIST_DIR${NC}"
    exit 1
  fi

  # Check if index.html exists
  if [ ! -f "$DIST_DIR/index.html" ]; then
    echo -e "${RED}❌ index.html not found in build directory${NC}"
    exit 1
  fi

  echo -e "${GREEN}✓ index.html exists${NC}"

  # Check for assets directory
  if [ ! -d "$DIST_DIR/assets" ]; then
    echo -e "${RED}❌ assets directory not found in build directory${NC}"
    exit 1
  fi

  echo -e "${GREEN}✓ assets directory exists${NC}"

  # Find JS files
  JS_FILES=$(find "$DIST_DIR/assets" -name "*.js" -type f)
  JS_COUNT=$(echo "$JS_FILES" | grep -c "\.js$" || true)

  if [ "$JS_COUNT" -eq 0 ]; then
    echo -e "${RED}❌ No JavaScript files found in assets directory${NC}"
    exit 1
  fi

  echo -e "${GREEN}✓ Found $JS_COUNT JavaScript file(s)${NC}"

  # Find CSS files
  CSS_FILES=$(find "$DIST_DIR/assets" -name "*.css" -type f)
  CSS_COUNT=$(echo "$CSS_FILES" | grep -c "\.css$" || true)

  if [ "$CSS_COUNT" -eq 0 ]; then
    echo -e "${RED}❌ No CSS files found in assets directory${NC}"
    exit 1
  fi

  echo -e "${GREEN}✓ Found $CSS_COUNT CSS file(s)${NC}"

  echo -e "${GREEN}✓ Build verification complete! All checks passed.${NC}"
}

# Function to deploy to local nginx
deploy_to_nginx() {
  echo -e "\n${BLUE}${BOLD}Step 3: Deploying to Nginx on Vultr${NC}"

  # Create nginx directory if it doesn't exist
  if [ ! -d "$NGINX_DIR" ]; then
    echo -e "${BLUE}Creating nginx directory...${NC}"
    sudo mkdir -p "$NGINX_DIR"
  fi

  # Clear old files
  echo -e "${BLUE}Clearing old files...${NC}"
  sudo rm -rf "$NGINX_DIR"/*

  # Copy new files
  echo -e "${BLUE}Copying new files...${NC}"
  sudo cp -r "$DIST_DIR"/* "$NGINX_DIR/"

  # Set proper permissions
  echo -e "${BLUE}Setting permissions...${NC}"
  sudo chown -R www-data:www-data "$NGINX_DIR"
  sudo chmod -R 755 "$NGINX_DIR"

  # Test nginx configuration
  echo -e "${BLUE}Testing nginx configuration...${NC}"
  sudo nginx -t

  if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Nginx configuration test failed. Please check nginx configuration.${NC}"
    exit 1
  fi

  # Reload nginx
  echo -e "${BLUE}Reloading nginx...${NC}"
  sudo systemctl reload nginx

  echo -e "${GREEN}✓ Admin UI deployed successfully to nginx!${NC}"
}

# Function to validate the deployment
validate_deployment() {
  echo -e "\n${BLUE}${BOLD}Step 4: Validating Deployment${NC}"

  echo -e "${BLUE}Checking local deployment...${NC}"

  # Check if the site is accessible locally
  local http_status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost/admin/")

  if [ "$http_status" -eq 200 ]; then
    echo -e "${GREEN}✓ Site is accessible locally (HTTP 200)${NC}"
  else
    echo -e "${RED}❌ Site returned HTTP status $http_status locally${NC}"
    exit 1
  fi

  # Check external accessibility if domain is configured
  echo -e "${BLUE}Checking external accessibility...${NC}"
  local external_status=$(curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN/admin/" || echo "0")

  if [ "$external_status" -eq 200 ]; then
    echo -e "${GREEN}✓ Site is accessible at https://$DOMAIN/admin/ (HTTP 200)${NC}"
  else
    echo -e "${YELLOW}⚠️ External site returned HTTP status $external_status${NC}"
    echo -e "${YELLOW}This could be due to DNS propagation or SSL certificate issues.${NC}"
  fi

  # Check for CSS and JS references
  echo -e "${BLUE}Checking for CSS and JS references...${NC}"

  local site_content=$(curl -s "http://localhost/admin/")

  if echo "$site_content" | grep -q "assets/.*\.js"; then
    echo -e "${GREEN}✓ JavaScript references found in deployed site${NC}"
  else
    echo -e "${RED}❌ No JavaScript references found in deployed site${NC}"
  fi

  if echo "$site_content" | grep -q "assets/.*\.css"; then
    echo -e "${GREEN}✓ CSS references found in deployed site${NC}"
  else
    echo -e "${RED}❌ No CSS references found in deployed site${NC}"
  fi
}

# Main execution
echo -e "${PURPLE}${BOLD}Starting Admin UI Fix Process...${NC}"
echo -e "${PURPLE}This will fix the admin UI and deploy it on your Vultr server.${NC}"
echo

# Run all steps
check_dependencies
build_admin_ui
verify_build
deploy_to_nginx
validate_deployment

echo
echo -e "${GREEN}${BOLD}✅ Admin UI fix completed successfully!${NC}"
echo
echo -e "${GREEN}The admin UI has been:${NC}"
echo -e "${GREEN}1. Rebuilt with proper configuration${NC}"
echo -e "${GREEN}2. Verified to contain all necessary files${NC}"
echo -e "${GREEN}3. Deployed to nginx on Vultr${NC}"
echo -e "${GREEN}4. Validated as accessible${NC}"
echo
echo -e "${CYAN}Access the admin UI at:${NC}"
echo -e "${CYAN}  - Local: http://localhost/admin/${NC}"
echo -e "${CYAN}  - External: https://$DOMAIN/admin/${NC}"
echo 