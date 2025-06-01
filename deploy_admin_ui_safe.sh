#!/bin/bash
#
# deploy_admin_ui_safe.sh
#
# Safe deployment script for Admin UI with validation and rollback
#

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
ADMIN_UI_DIR="admin-ui"
NGINX_DIR="/var/www/orchestra-admin"
BACKUP_DIR="/var/www/orchestra-admin-backup"
DOMAIN="cherry-ai.me"

echo -e "${BLUE}🚀 Safe Admin UI Deployment${NC}"
echo -e "${BLUE}=========================${NC}"

# Function to create backup
backup_current() {
    echo -e "\n${BLUE}📦 Creating backup of current deployment...${NC}"
    
    if [ -d "$NGINX_DIR" ]; then
        sudo rm -rf "$BACKUP_DIR"
        sudo cp -r "$NGINX_DIR" "$BACKUP_DIR"
        echo -e "${GREEN}✓ Backup created at $BACKUP_DIR${NC}"
    else
        echo -e "${YELLOW}⚠ No existing deployment to backup${NC}"
    fi
}

# Function to restore from backup
restore_backup() {
    echo -e "\n${RED}🔄 Restoring from backup...${NC}"
    
    if [ -d "$BACKUP_DIR" ]; then
        sudo rm -rf "$NGINX_DIR"
        sudo cp -r "$BACKUP_DIR" "$NGINX_DIR"
        sudo chown -R www-data:www-data "$NGINX_DIR"
        sudo systemctl reload nginx
        echo -e "${GREEN}✓ Restored from backup${NC}"
    else
        echo -e "${RED}✗ No backup found to restore${NC}"
    fi
}

# Function to validate build
validate_build() {
    echo -e "\n${BLUE}🔍 Validating build...${NC}"
    
    local errors=0
    
    # Check if dist directory exists
    if [ ! -d "$ADMIN_UI_DIR/dist" ]; then
        echo -e "${RED}✗ Build directory not found${NC}"
        ((errors++))
    fi
    
    # Check for index.html
    if [ ! -f "$ADMIN_UI_DIR/dist/index.html" ]; then
        echo -e "${RED}✗ index.html not found${NC}"
        ((errors++))
    else
        echo -e "${GREEN}✓ index.html exists${NC}"
    fi
    
    # Check for assets
    if [ ! -d "$ADMIN_UI_DIR/dist/assets" ]; then
        echo -e "${RED}✗ Assets directory not found${NC}"
        ((errors++))
    else
        # Count JS and CSS files
        js_count=$(find "$ADMIN_UI_DIR/dist/assets" -name "*.js" | wc -l)
        css_count=$(find "$ADMIN_UI_DIR/dist/assets" -name "*.css" | wc -l)
        
        if [ $js_count -eq 0 ]; then
            echo -e "${RED}✗ No JavaScript files found${NC}"
            ((errors++))
        else
            echo -e "${GREEN}✓ Found $js_count JavaScript file(s)${NC}"
        fi
        
        if [ $css_count -eq 0 ]; then
            echo -e "${RED}✗ No CSS files found${NC}"
            ((errors++))
        else
            echo -e "${GREEN}✓ Found $css_count CSS file(s)${NC}"
        fi
    fi
    
    # Check file sizes
    if [ -d "$ADMIN_UI_DIR/dist/assets" ]; then
        local small_files=$(find "$ADMIN_UI_DIR/dist/assets" -name "*.js" -size -10k | wc -l)
        if [ $small_files -gt 0 ]; then
            echo -e "${YELLOW}⚠ Found $small_files suspiciously small JS files${NC}"
        fi
    fi
    
    return $errors
}

# Function to test deployment
test_deployment() {
    echo -e "\n${BLUE}🧪 Testing deployment...${NC}"
    
    # Test local access
    local status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost/admin/")
    if [ "$status" -eq 200 ]; then
        echo -e "${GREEN}✓ Local access successful (HTTP $status)${NC}"
    else
        echo -e "${RED}✗ Local access failed (HTTP $status)${NC}"
        return 1
    fi
    
    # Check for JavaScript errors in response
    local content=$(curl -s "http://localhost/admin/")
    if echo "$content" | grep -q "Something went wrong"; then
        echo -e "${RED}✗ Error page detected${NC}"
        return 1
    fi
    
    if echo "$content" | grep -q "<div id=\"root\"></div>"; then
        echo -e "${GREEN}✓ Root element found${NC}"
    else
        echo -e "${RED}✗ Root element missing${NC}"
        return 1
    fi
    
    return 0
}

# Main deployment flow
cd "$(dirname "$0")"

# Step 1: Backup current deployment
backup_current

# Step 2: Build
echo -e "\n${BLUE}🔨 Building Admin UI...${NC}"
cd "$ADMIN_UI_DIR"

# Clean install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pnpm install --frozen-lockfile || pnpm install

# Build with error handling
echo -e "${BLUE}Running build...${NC}"
if ! NODE_ENV=production pnpm run build-no-ts; then
    echo -e "${RED}✗ Build failed${NC}"
    cd ..
    exit 1
fi

cd ..

# Step 3: Validate build
if ! validate_build; then
    echo -e "${RED}✗ Build validation failed${NC}"
    exit 1
fi

# Step 4: Deploy
echo -e "\n${BLUE}📤 Deploying to nginx...${NC}"

# Clear old files
sudo rm -rf "$NGINX_DIR"/*

# Copy new files
sudo cp -r "$ADMIN_UI_DIR/dist/"* "$NGINX_DIR/"

# Set permissions
sudo chown -R www-data:www-data "$NGINX_DIR"
sudo chmod -R 755 "$NGINX_DIR"

# Test nginx config
if ! sudo nginx -t; then
    echo -e "${RED}✗ Nginx configuration test failed${NC}"
    restore_backup
    exit 1
fi

# Reload nginx
sudo systemctl reload nginx
echo -e "${GREEN}✓ Nginx reloaded${NC}"

# Step 5: Test deployment
sleep 2  # Give nginx time to reload

if ! test_deployment; then
    echo -e "${RED}✗ Deployment test failed, rolling back...${NC}"
    restore_backup
    exit 1
fi

# Step 6: Success
echo -e "\n${GREEN}✅ Deployment successful!${NC}"
echo -e "${GREEN}==========================${NC}"
echo -e "${GREEN}🌐 Admin UI deployed to: https://$DOMAIN/admin/${NC}"
echo -e "${GREEN}📁 Files located at: $NGINX_DIR${NC}"
echo -e "${GREEN}💾 Backup saved at: $BACKUP_DIR${NC}"

# Optional: Clean up old backup after successful deployment
# sudo rm -rf "$BACKUP_DIR"

echo -e "\n${BLUE}📝 Login credentials:${NC}"
echo -e "   Username: scoobyjava"
echo -e "   Password: Huskers1983$" 