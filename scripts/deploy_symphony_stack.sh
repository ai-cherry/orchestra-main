#!/bin/bash
# deploy_symphony_stack.sh
# Deploys the full Symphony stack (backend and admin-ui frontend) to an existing server.

set -e # Exit immediately if a command exits with a non-zero status.
# set -x # Debug mode: Print each command before executing it (optional)

# --- Configuration ---
PROJECT_ROOT_ON_SERVER="/root/cherry_ai-main" # Adjust if your project is cloned elsewhere on the server
ADMIN_UI_DIR_RELATIVE="admin-ui" # Relative to project root
NGINX_WEBROOT="/var/www/cherry_ai-admin"
NGINX_CONFIG_REPO_PATH="cherry_ai-admin.nginx.conf" # Path to the master Nginx config in your repo
NGINX_CONFIG_SERVER_PATH="/etc/nginx/sites-available/cherry_ai-admin" # Standard path on server
NGINX_ENABLED_LINK="/etc/nginx/sites-enabled/cherry_ai-admin"
BACKEND_SERVICE_NAME="cherry_ai-real.service" # As defined in deploy_to_vultr.sh or similar initial setup
BACKUP_DIR_ADMIN_UI="/var/www/cherry_ai-admin-backup_$(date +%Y%m%d%H%M%S)"

PYTHON_VENV_PATH="$PROJECT_ROOT_ON_SERVER/venv"
PRODUCTION_REQUIREMENTS="requirements/production/requirements.txt"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Deploying Symphony Stack (Backend & Admin UI)...${NC}"

# --- Helper Functions ---
ensure_sudo() {
    if [[ $EUID -ne 0 ]]; then
        echo -e "${RED}This script needs to run some commands with sudo. Please run as root or with sudo privileges.${NC}"
        # Re-run with sudo if not already root
        # exec sudo bash "$0" "$@" # This can be tricky with script paths, ensure it finds itself
        exit 1
    fi
}

# --- Pre-flight Checks (on the server this script runs on) ---
echo -e "${YELLOW}Running pre-flight checks...${NC}"
ensure_sudo # Ensure we can run sudo commands when needed (most server operations)

if ! command -v git &> /dev/null; then echo -e "${RED}Git not found! Exiting.${NC}"; exit 1; fi
if ! command -v pnpm &> /dev/null; then echo -e "${RED}pnpm not found! (cd $ADMIN_UI_DIR_RELATIVE && npm install -g pnpm) Exiting.${NC}"; exit 1; fi
if ! command -v nginx &> /dev/null; then echo -e "${RED}Nginx not found! Exiting.${NC}"; exit 1; fi
if [ ! -f "$PYTHON_VENV_PATH/bin/python" ]; then echo -e "${RED}Python venv not found at $PYTHON_VENV_PATH! Exiting.${NC}"; exit 1; fi

echo -e "${GREEN}Pre-flight checks passed.${NC}"

# --- Main Deployment Steps ---
cd "$PROJECT_ROOT_ON_SERVER" || { echo -e "${RED}Failed to cd to project root $PROJECT_ROOT_ON_SERVER. Exiting.${NC}"; exit 1; }

# 1. Update Codebase
echo -e "${BLUE}Updating codebase from Git...${NC}"
git fetch origin
# Option 1: Reset to origin/main (discard local changes) - DANGEROUS if there are legitimate local changes
# git reset --hard origin/main 
# Option 2: Stash local changes and pull (safer, but might have conflicts)
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "On branch: $CURRENT_BRANCH. Pulling latest..."
if ! git pull origin "$CURRENT_BRANCH"; then
    echo -e "${RED}Git pull failed. Please resolve conflicts manually in $PROJECT_ROOT_ON_SERVER.${NC}"
    exit 1
fi
echo -e "${GREEN}Codebase updated.${NC}"

# 2. Backend Deployment
echo -e "${BLUE}Deploying backend...${NC}"
source "$PYTHON_VENV_PATH/bin/activate" || { echo -e "${RED}Failed to activate Python venv. Exiting.${NC}"; exit 1; }

echo "Installing/updating Python dependencies..."
if ! pip install -r "$PRODUCTION_REQUIREMENTS"; then
    echo -e "${RED}Failed to install Python dependencies. Exiting.${NC}"
    deactivate
    exit 1
fi

# Add database migration step here if applicable
# echo "Running database migrations..."
# python manage.py migrate (example)

echo "Restarting backend service ($BACKEND_SERVICE_NAME)..."
if ! systemctl restart "$BACKEND_SERVICE_NAME"; then
    echo -e "${RED}Failed to restart backend service. Check service status: systemctl status $BACKEND_SERVICE_NAME${NC}"
    deactivate
    exit 1
fi
systemctl status "$BACKEND_SERVICE_NAME" --no-pager # Show status briefly
deactivate
echo -e "${GREEN}Backend deployed and restarted.${NC}"

# 3. Frontend (Admin UI) Deployment
echo -e "${BLUE}Deploying Admin UI frontend...${NC}"
ADMIN_UI_FULL_PATH="$PROJECT_ROOT_ON_SERVER/$ADMIN_UI_DIR_RELATIVE"
if [ ! -d "$ADMIN_UI_FULL_PATH" ]; then
    echo -e "${RED}Admin UI directory not found at $ADMIN_UI_FULL_PATH. Exiting.${NC}"
    exit 1
fi
cd "$ADMIN_UI_FULL_PATH" || { echo -e "${RED}Failed to cd to Admin UI directory. Exiting.${NC}"; exit 1; }

echo "Installing frontend dependencies..."
if ! pnpm install --frozen-lockfile; then
    echo -e "${YELLOW}pnpm install --frozen-lockfile failed, trying without frozen lockfile...${NC}"
    if ! pnpm install; then
        echo -e "${RED}Failed to install frontend dependencies even without frozen lockfile. Exiting.${NC}"
        exit 1
    fi
fi

echo "Building Admin UI (production mode)..."
if ! NODE_ENV=production pnpm build; then # Vite should handle hashing with NODE_ENV=production
    echo -e "${YELLOW}pnpm build failed, trying build-no-ts...${NC}"
    if ! NODE_ENV=production pnpm run build-no-ts; then
      echo -e "${RED}Admin UI build failed. Exiting.${NC}"
      exit 1
    fi
fi

if [ ! -d "dist" ] || [ ! -f "dist/index.html" ]; then
    echo -e "${RED}Admin UI build verification failed: dist/index.html not found. Exiting.${NC}"
    exit 1
fi
echo -e "${GREEN}Admin UI build complete.${NC}"

echo "Backing up current Admin UI webroot..."
if [ -d "$NGINX_WEBROOT" ]; then
    mkdir -p "$(dirname "$BACKUP_DIR_ADMIN_UI")" # Ensure backup parent dir exists
    if ! cp -r "$NGINX_WEBROOT" "$BACKUP_DIR_ADMIN_UI"; then
        echo -e "${YELLOW}Warning: Failed to create backup of $NGINX_WEBROOT. Proceeding with caution.${NC}"
    else
        echo -e "${GREEN}Backup created at $BACKUP_DIR_ADMIN_UI${NC}"
    fi
else
    echo -e "${YELLOW}No existing deployment at $NGINX_WEBROOT to backup. Creating directory.${NC}"
    mkdir -p "$NGINX_WEBROOT"
fi

echo "Clearing old Admin UI files from $NGINX_WEBROOT..."
rm -rf "$NGINX_WEBROOT"/*

echo "Deploying new Admin UI build..."
cp -r dist/* "$NGINX_WEBROOT/"

echo "Setting permissions for $NGINX_WEBROOT..."
chown -R www-data:www-data "$NGINX_WEBROOT"
chmod -R 755 "$NGINX_WEBROOT"
cd "$PROJECT_ROOT_ON_SERVER" # Return to project root
echo -e "${GREEN}Admin UI files deployed.${NC}"

# 4. Nginx Configuration Update
echo -e "${BLUE}Updating Nginx configuration...${NC}"
if [ ! -f "$NGINX_CONFIG_REPO_PATH" ]; then
    echo -e "${RED}Master Nginx config $NGINX_CONFIG_REPO_PATH not found in repository. Exiting.${NC}"
    exit 1
fi

echo "Copying Nginx config from repository to $NGINX_CONFIG_SERVER_PATH..."
cp "$NGINX_CONFIG_REPO_PATH" "$NGINX_CONFIG_SERVER_PATH"

# Ensure symlink exists in sites-enabled
if [ ! -L "$NGINX_ENABLED_LINK" ] || [ "$(readlink -f "$NGINX_ENABLED_LINK")" != "$NGINX_CONFIG_SERVER_PATH" ]; then
    echo "Creating/updating Nginx enabled site symlink..."
    ln -sf "$NGINX_CONFIG_SERVER_PATH" "$NGINX_ENABLED_LINK"
fi

# Remove default Nginx config if it exists and symlink is not for default
if [ -L "/etc/nginx/sites-enabled/default" ] && [ "$NGINX_ENABLED_LINK" != "/etc/nginx/sites-enabled/default" ]; then
    echo "Removing default Nginx symlink..."
    rm -f "/etc/nginx/sites-enabled/default"
fi

echo "Testing Nginx configuration..."
if ! nginx -t; then
    echo -e "${RED}Nginx configuration test failed! Check $NGINX_CONFIG_SERVER_PATH. Exiting without reloading Nginx.${NC}"
    # Consider automated rollback of Nginx config if a backup mechanism is in place
    exit 1
fi

echo "Reloading Nginx..."
if ! systemctl reload nginx; then
    echo -e "${RED}Failed to reload Nginx. Check Nginx status: systemctl status nginx${NC}"
    exit 1
fi
echo -e "${GREEN}Nginx configuration updated and reloaded.${NC}"

# 5. Post-Deployment Validation (Simplified)
echo -e "${BLUE}Running post-deployment validation...${NC}"
# Give services a moment to settle
sleep 5 

API_HEALTH_URL="http://localhost/api/health" # Assuming Nginx proxies this to the backend health endpoint
ADMIN_UI_URL="http://localhost/" # Assuming Admin UI is at root via Nginx

echo "Checking backend API health at $API_HEALTH_URL..."
if curl --fail --silent --max-time 5 "$API_HEALTH_URL" > /dev/null; then
    echo -e "${GREEN}Backend API health check PASSED.${NC}"
else
    echo -e "${RED}Backend API health check FAILED. Check $BACKEND_SERVICE_NAME logs and Nginx proxy.${NC}"
    # Consider rollback actions here based on severity
fi

echo "Checking Admin UI accessibility at $ADMIN_UI_URL..."
if curl --fail --silent --max-time 5 "$ADMIN_UI_URL" | grep -q -E "<title>|id=.*root" ; then # Look for common SPA markers
    echo -e "${GREEN}Admin UI basic accessibility check PASSED.${NC}"
else
    echo -e "${RED}Admin UI basic accessibility check FAILED. Check Nginx logs and $NGINX_WEBROOT contents.${NC}"
fi

echo -e "${GREEN}🚀 Symphony Stack deployment process finished.${NC}"
echo -e "Please verify your application manually at http://cherry-ai.me (or your server IP)."

# Optional: Clean up old backups after a few successful deployments
# find /var/www -maxdepth 1 -name 'cherry_ai-admin-backup_*' -mtime +7 -exec rm -rf {} \; 