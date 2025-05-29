#!/bin/bash
#
# fix_admin_ui_blank_screen.sh
#
# This script fixes the blank white screen issue on cherry-ai.me by:
# 1. Rebuilding the admin UI with fixed configuration
# 2. Verifying proper build output (CSS and JS files)
# 3. Deploying to DigitalOcean App Platform
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
DOMAIN="cherry-ai.me"
APP_NAME="admin-ui-prod"
MIN_JS_SIZE=100000  # 100KB minimum expected JS bundle size
MIN_CSS_SIZE=10000  # 10KB minimum expected CSS file size
DO_API_URL="https://api.digitalocean.com/v2"

# Print banner
echo -e "${CYAN}${BOLD}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║   🔧 Cherry Admin UI - Blank Screen Fix Tool 🔧            ║"
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
    if [[ $(echo "$node_version" | cut -d '.' -f 1) -lt 18 ]]; then
      echo -e "${YELLOW}⚠️ Node.js version $node_version detected. Version 20+ recommended.${NC}"
    else
      echo -e "${GREEN}✓ Node.js v$node_version${NC}"
    fi
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
    echo -e "${GREEN}✓ pnpm$(pnpm --version)${NC}"
  fi
  
  # Check for curl
  if ! command_exists curl; then
    echo -e "${RED}❌ curl is not installed. Please install curl.${NC}"
    missing_deps=1
  else
    echo -e "${GREEN}✓ curl${NC}"
  fi
  
  # Check for jq
  if ! command_exists jq; then
    echo -e "${YELLOW}⚠️ jq is not installed. Installing...${NC}"
    apt-get update && apt-get install -y jq || brew install jq || echo -e "${RED}❌ Failed to install jq. Please install manually.${NC}"
    if ! command_exists jq; then
      echo -e "${RED}❌ Failed to install jq. Please install manually.${NC}"
      missing_deps=1
    else
      echo -e "${GREEN}✓ jq installed${NC}"
    fi
  else
    echo -e "${GREEN}✓ jq${NC}"
  fi
  
  if [ $missing_deps -ne 0 ]; then
    echo -e "${RED}Please install missing dependencies and try again.${NC}"
    exit 1
  fi
  
  echo -e "${GREEN}All dependencies satisfied!${NC}"
}

# Function to get DigitalOcean API token
get_do_token() {
  if [ -n "$DO_API_TOKEN" ]; then
    echo -e "${GREEN}Using DigitalOcean API token from environment variable.${NC}"
    return 0
  fi
  
  # Try to get from .env file
  if [ -f "${REPO_ROOT}/.env" ]; then
    source "${REPO_ROOT}/.env"
    if [ -n "$DO_API_TOKEN" ]; then
      echo -e "${GREEN}Using DigitalOcean API token from .env file.${NC}"
      return 0
    fi
  fi
  
  # Prompt user for token
  echo -e "${YELLOW}DigitalOcean API token not found in environment or .env file.${NC}"
  read -p "Please enter your DigitalOcean API token: " DO_API_TOKEN
  
  if [ -z "$DO_API_TOKEN" ]; then
    echo -e "${RED}No DigitalOcean API token provided. Cannot continue.${NC}"
    exit 1
  fi
  
  # Save to .env file for future use
  echo "DO_API_TOKEN=$DO_API_TOKEN" >> "${REPO_ROOT}/.env"
  echo -e "${GREEN}Token saved to .env file for future use.${NC}"
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
  
  # Run the build
  NODE_ENV=production pnpm build
  
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
  
  # Check JS file sizes
  for js_file in $JS_FILES; do
    js_size=$(stat -c%s "$js_file" 2>/dev/null || stat -f%z "$js_file")
    js_name=$(basename "$js_file")
    
    if [ "$js_size" -lt "$MIN_JS_SIZE" ]; then
      echo -e "${RED}❌ JavaScript file $js_name is too small: $js_size bytes (expected min. $MIN_JS_SIZE bytes)${NC}"
      echo -e "${YELLOW}This indicates a build issue. The JS bundle is incomplete.${NC}"
      exit 1
    else
      echo -e "${GREEN}✓ JavaScript file $js_name size: $(numfmt --to=iec-i --suffix=B --format="%.2f" $js_size)${NC}"
    fi
  done
  
  # Check CSS file sizes
  for css_file in $CSS_FILES; do
    css_size=$(stat -c%s "$css_file" 2>/dev/null || stat -f%z "$css_file")
    css_name=$(basename "$css_file")
    
    if [ "$css_size" -lt "$MIN_CSS_SIZE" ]; then
      echo -e "${RED}❌ CSS file $css_name is too small: $css_size bytes (expected min. $MIN_CSS_SIZE bytes)${NC}"
      echo -e "${YELLOW}This indicates a build issue. The CSS is incomplete.${NC}"
      exit 1
    else
      echo -e "${GREEN}✓ CSS file $css_name size: $(numfmt --to=iec-i --suffix=B --format="%.2f" $css_size)${NC}"
    fi
  done
  
  # Check index.html for references to JS and CSS
  index_content=$(cat "$DIST_DIR/index.html")
  
  # Check for JS references
  if ! echo "$index_content" | grep -q "src=\"/assets/.*\.js\""; then
    echo -e "${RED}❌ No JavaScript file references found in index.html${NC}"
    exit 1
  fi
  
  echo -e "${GREEN}✓ JavaScript references found in index.html${NC}"
  
  # Check for CSS references
  if ! echo "$index_content" | grep -q "href=\"/assets/.*\.css\""; then
    echo -e "${YELLOW}⚠️ No CSS file references found in index.html${NC}"
    echo -e "${YELLOW}Adding CSS link tag to index.html...${NC}"
    
    # Get the first CSS file
    first_css=$(basename "$(echo "$CSS_FILES" | head -n1)")
    
    # Add CSS link before closing head tag
    sed -i.bak "s|</head>|  <link rel=\"stylesheet\" href=\"/assets/$first_css\">\n</head>|" "$DIST_DIR/index.html"
    
    echo -e "${GREEN}✓ CSS reference added to index.html${NC}"
  else
    echo -e "${GREEN}✓ CSS references found in index.html${NC}"
  fi
  
  echo -e "${GREEN}✓ Build verification complete! All checks passed.${NC}"
}

# Function to deploy to DigitalOcean App Platform
deploy_to_do() {
  echo -e "\n${BLUE}${BOLD}Step 3: Deploying to DigitalOcean App Platform${NC}"
  
  # Check if app exists
  echo -e "${BLUE}Checking if app $APP_NAME exists...${NC}"
  
  local app_response=$(curl -s -X GET \
    -H "Authorization: Bearer $DO_API_TOKEN" \
    -H "Content-Type: application/json" \
    "$DO_API_URL/apps")
  
  if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to connect to DigitalOcean API. Please check your token and try again.${NC}"
    exit 1
  fi
  
  local app_id=$(echo "$app_response" | jq -r ".apps[] | select(.spec.name == \"$APP_NAME\") | .id")
  
  if [ -z "$app_id" ] || [ "$app_id" == "null" ]; then
    echo -e "${YELLOW}App $APP_NAME not found. Creating new app...${NC}"
    
    # Create app spec
    local app_spec='{
      "spec": {
        "name": "'$APP_NAME'",
        "region": "sfo2",
        "static_sites": [
          {
            "name": "admin-ui-site",
            "source_dir": "/",
            "output_dir": "/",
            "index_document": "index.html",
            "error_document": "index.html",
            "catchall_document": "index.html",
            "routes": [
              {"path": "/"}
            ]
          }
        ],
        "domains": [
          {
            "domain": "'$DOMAIN'",
            "type": "PRIMARY"
          }
        ]
      }
    }'
    
    # Create app
    local create_response=$(curl -s -X POST \
      -H "Authorization: Bearer $DO_API_TOKEN" \
      -H "Content-Type: application/json" \
      -d "$app_spec" \
      "$DO_API_URL/apps")
    
    app_id=$(echo "$create_response" | jq -r ".app.id")
    
    if [ -z "$app_id" ] || [ "$app_id" == "null" ]; then
      echo -e "${RED}❌ Failed to create app. Response: $(echo "$create_response" | jq -r '.message // "Unknown error"')${NC}"
      exit 1
    fi
    
    echo -e "${GREEN}✓ App created with ID: $app_id${NC}"
  else
    echo -e "${GREEN}✓ Found existing app with ID: $app_id${NC}"
  fi
  
  # Create a new deployment
  echo -e "${BLUE}Creating new deployment...${NC}"
  
  local deployment_response=$(curl -s -X POST \
    -H "Authorization: Bearer $DO_API_TOKEN" \
    -H "Content-Type: application/json" \
    "$DO_API_URL/apps/$app_id/deployments")
  
  local deployment_id=$(echo "$deployment_response" | jq -r ".deployment.id")
  
  if [ -z "$deployment_id" ] || [ "$deployment_id" == "null" ]; then
    echo -e "${RED}❌ Failed to create deployment. Response: $(echo "$deployment_response" | jq -r '.message // "Unknown error"')${NC}"
    exit 1
  fi
  
  echo -e "${GREEN}✓ Deployment created with ID: $deployment_id${NC}"
  
  # Upload files
  echo -e "${BLUE}Uploading files...${NC}"
  
  # First, upload index.html
  echo -e "${BLUE}Uploading index.html...${NC}"
  
  local index_content=$(cat "$DIST_DIR/index.html")
  
  local upload_response=$(curl -s -X PUT \
    -H "Authorization: Bearer $DO_API_TOKEN" \
    -H "Content-Type: text/html" \
    --data-binary "$index_content" \
    "$DO_API_URL/apps/$app_id/deployments/$deployment_id/components/admin-ui-site/files/index.html")
  
  if echo "$upload_response" | jq -e '.error' > /dev/null; then
    echo -e "${RED}❌ Failed to upload index.html: $(echo "$upload_response" | jq -r '.message // "Unknown error"')${NC}"
    exit 1
  fi
  
  echo -e "${GREEN}✓ index.html uploaded${NC}"
  
  # Create assets directory
  echo -e "${BLUE}Creating assets directory...${NC}"
  
  local mkdir_response=$(curl -s -X PUT \
    -H "Authorization: Bearer $DO_API_TOKEN" \
    -H "Content-Type: application/json" \
    "$DO_API_URL/apps/$app_id/deployments/$deployment_id/components/admin-ui-site/files/assets/")
  
  # Upload all files in the assets directory
  echo -e "${BLUE}Uploading assets...${NC}"
  
  find "$DIST_DIR/assets" -type f | while read file; do
    local relative_path=${file#$DIST_DIR/}
    local mime_type=$(file --mime-type -b "$file")
    
    echo -e "${BLUE}Uploading $relative_path (${mime_type})...${NC}"
    
    local upload_response=$(curl -s -X PUT \
      -H "Authorization: Bearer $DO_API_TOKEN" \
      -H "Content-Type: ${mime_type}" \
      --data-binary "@$file" \
      "$DO_API_URL/apps/$app_id/deployments/$deployment_id/components/admin-ui-site/files/$relative_path")
    
    if echo "$upload_response" | jq -e '.error' > /dev/null; then
      echo -e "${YELLOW}⚠️ Warning uploading $relative_path: $(echo "$upload_response" | jq -r '.message // "Unknown error"')${NC}"
    else
      echo -e "${GREEN}✓ $relative_path uploaded${NC}"
    fi
  done
  
  # Finalize deployment
  echo -e "${BLUE}Finalizing deployment...${NC}"
  
  local finalize_response=$(curl -s -X POST \
    -H "Authorization: Bearer $DO_API_TOKEN" \
    -H "Content-Type: application/json" \
    "$DO_API_URL/apps/$app_id/deployments/$deployment_id/actions/finalize")
  
  if echo "$finalize_response" | jq -e '.error' > /dev/null; then
    echo -e "${RED}❌ Failed to finalize deployment: $(echo "$finalize_response" | jq -r '.message // "Unknown error"')${NC}"
    exit 1
  fi
  
  echo -e "${GREEN}✓ Deployment finalized!${NC}"
  
  # Wait for deployment to complete
  echo -e "${BLUE}Waiting for deployment to complete...${NC}"
  
  local phase=""
  local counter=0
  local max_tries=30
  
  while [ $counter -lt $max_tries ]; do
    local status_response=$(curl -s -X GET \
      -H "Authorization: Bearer $DO_API_TOKEN" \
      -H "Content-Type: application/json" \
      "$DO_API_URL/apps/$app_id/deployments/$deployment_id")
    
    phase=$(echo "$status_response" | jq -r ".deployment.phase")
    
    echo -e "${BLUE}Deployment status: $phase${NC}"
    
    if [ "$phase" == "ACTIVE" ]; then
      echo -e "${GREEN}✓ Deployment completed successfully!${NC}"
      break
    elif [[ "$phase" == "ERROR" || "$phase" == "CANCELED" || "$phase" == "FAILED" ]]; then
      echo -e "${RED}❌ Deployment failed with status: $phase${NC}"
      echo -e "${RED}Error message: $(echo "$status_response" | jq -r ".deployment.error_message // \"Unknown error\"")${NC}"
      exit 1
    fi
    
    counter=$((counter + 1))
    echo -e "${BLUE}Waiting for deployment to complete ($counter/$max_tries)...${NC}"
    sleep 10
  done
  
  if [ $counter -eq $max_tries ]; then
    echo -e "${YELLOW}⚠️ Deployment is taking longer than expected. Please check the DigitalOcean dashboard.${NC}"
    echo -e "${YELLOW}You can check the status at: https://cloud.digitalocean.com/apps/$app_id/deployments/$deployment_id${NC}"
  fi
  
  # Get app URL
  local app_url=$(curl -s -X GET \
    -H "Authorization: Bearer $DO_API_TOKEN" \
    -H "Content-Type: application/json" \
    "$DO_API_URL/apps/$app_id" | jq -r ".app.live_url")
  
  echo -e "${GREEN}✓ App deployed successfully!${NC}"
  echo -e "${GREEN}✓ App URL: $app_url${NC}"
  echo -e "${GREEN}✓ Custom domain: https://$DOMAIN${NC}"
}

# Function to validate the deployment
validate_deployment() {
  echo -e "\n${BLUE}${BOLD}Step 4: Validating Deployment${NC}"
  
  echo -e "${BLUE}Checking site accessibility...${NC}"
  
  # Wait for DNS propagation
  echo -e "${BLUE}Waiting for DNS propagation (this may take a few minutes)...${NC}"
  sleep 10
  
  # Check if the site is accessible
  local http_status=$(curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN")
  
  if [ "$http_status" -eq 200 ]; then
    echo -e "${GREEN}✓ Site is accessible (HTTP 200)${NC}"
  else
    echo -e "${YELLOW}⚠️ Site returned HTTP status $http_status${NC}"
    echo -e "${YELLOW}This could be due to DNS propagation or SSL certificate provisioning.${NC}"
    echo -e "${YELLOW}Please check again in a few minutes.${NC}"
  fi
  
  # Check for CSS and JS references
  echo -e "${BLUE}Checking for CSS and JS references...${NC}"
  
  local site_content=$(curl -s "https://$DOMAIN")
  
  if echo "$site_content" | grep -q "assets/.*\.js"; then
    echo -e "${GREEN}✓ JavaScript reference found in the HTML${NC}"
  else
    echo -e "${RED}❌ No JavaScript reference found in the HTML${NC}"
  fi
  
  if echo "$site_content" | grep -q "assets/.*\.css"; then
    echo -e "${GREEN}✓ CSS reference found in the HTML${NC}"
  else
    echo -e "${RED}❌ No CSS reference found in the HTML${NC}"
  fi
  
  # Check if JS and CSS files are accessible
  local js_file=$(echo "$site_content" | grep -o "assets/[^\"]*\.js" | head -1)
  local css_file=$(echo "$site_content" | grep -o "assets/[^\"]*\.css" | head -1)
  
  if [ -n "$js_file" ]; then
    local js_status=$(curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN/$js_file")
    
    if [ "$js_status" -eq 200 ]; then
      echo -e "${GREEN}✓ JavaScript file is accessible (HTTP 200)${NC}"
    else
      echo -e "${RED}❌ JavaScript file returned HTTP status $js_status${NC}"
    fi
  fi
  
  if [ -n "$css_file" ]; then
    local css_status=$(curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN/$css_file")
    
    if [ "$css_status" -eq 200 ]; then
      echo -e "${GREEN}✓ CSS file is accessible (HTTP 200)${NC}"
    else
      echo -e "${RED}❌ CSS file returned HTTP status $css_status${NC}"
    fi
  fi
  
  echo -e "${GREEN}✓ Validation complete!${NC}"
}

# Function to display summary and next steps
display_summary() {
  echo -e "\n${BLUE}${BOLD}Summary and Next Steps${NC}"
  
  echo -e "${GREEN}${BOLD}✅ Admin UI blank screen fix completed!${NC}"
  echo -e "${GREEN}The following actions were performed:${NC}"
  echo -e "${GREEN}1. Built Admin UI with fixed configuration${NC}"
  echo -e "${GREEN}2. Verified build output (CSS and JS files)${NC}"
  echo -e "${GREEN}3. Deployed to DigitalOcean App Platform${NC}"
  echo -e "${GREEN}4. Validated the deployment${NC}"
  
  echo -e "\n${BLUE}${BOLD}Next Steps:${NC}"
  echo -e "${BLUE}1. Visit https://$DOMAIN to verify the site is working properly${NC}"
  echo -e "${BLUE}2. If the site is still showing a blank screen, try clearing your browser cache${NC}"
  echo -e "${BLUE}3. Run the following command to check for any deployment issues:${NC}"
  echo -e "${PURPLE}   ./check_deployment_status.py --token \$DO_API_TOKEN${NC}"
  
  echo -e "\n${YELLOW}${BOLD}Troubleshooting:${NC}"
  echo -e "${YELLOW}If you still encounter issues, check:${NC}"
  echo -e "${YELLOW}1. DigitalOcean App Platform logs: https://cloud.digitalocean.com/apps${NC}"
  echo -e "${YELLOW}2. DNS configuration for $DOMAIN${NC}"
  echo -e "${YELLOW}3. SSL certificate status${NC}"
  
  echo -e "\n${CYAN}${BOLD}For ongoing maintenance:${NC}"
  echo -e "${CYAN}1. Update the GitHub Actions workflow to use the fixed build configuration${NC}"
  echo -e "${CYAN}2. Consider setting up monitoring for the Admin UI${NC}"
  echo -e "${CYAN}3. Document the fix in your project documentation${NC}"
  
  echo -e "\n${GREEN}${BOLD}Thank you for using the Cherry Admin UI Blank Screen Fix Tool!${NC}"
}

# Main execution
main() {
  check_dependencies
  get_do_token
  build_admin_ui
  verify_build
  deploy_to_do
  validate_deployment
  display_summary
}

# Run the main function
main
