#!/bin/bash
#
# cleanup_cloud_references.sh
#
# This script helps identify and clean up DigitalOcean and GCP references
# from the Orchestra AI codebase, ensuring only Vultr infrastructure is referenced
#

set -e

# Terminal colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Print banner
echo -e "${CYAN}${BOLD}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║   🧹 Cloud Reference Cleanup Tool 🧹                       ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Function to find references
find_references() {
    local pattern=$1
    local name=$2
    
    echo -e "\n${BLUE}Searching for $name references...${NC}"
    
    # Search in all files except git and node_modules
    local results=$(grep -r -i "$pattern" . \
        --exclude-dir=.git \
        --exclude-dir=node_modules \
        --exclude-dir=venv \
        --exclude-dir=.venv \
        --exclude-dir=__pycache__ \
        --exclude-dir=dist \
        --exclude="*.pyc" \
        --exclude="cleanup_cloud_references.sh" \
        2>/dev/null | head -20)
    
    if [ -n "$results" ]; then
        echo -e "${YELLOW}Found $name references:${NC}"
        echo "$results" | while IFS= read -r line; do
            echo "  $line"
        done
        return 0
    else
        echo -e "${GREEN}✓ No $name references found${NC}"
        return 1
    fi
}

# Function to count references
count_references() {
    local pattern=$1
    
    grep -r -i "$pattern" . \
        --exclude-dir=.git \
        --exclude-dir=node_modules \
        --exclude-dir=venv \
        --exclude-dir=.venv \
        --exclude-dir=__pycache__ \
        --exclude-dir=dist \
        --exclude="*.pyc" \
        --exclude="cleanup_cloud_references.sh" \
        2>/dev/null | wc -l
}

# Main execution
echo -e "${BLUE}Scanning codebase for cloud provider references...${NC}"

# Count references
DO_COUNT=$(count_references "digitalocean\|digital ocean")
GCP_COUNT=$(count_references "gcp\|google cloud\|google-cloud")

echo -e "\n${BLUE}Summary:${NC}"
echo -e "  DigitalOcean references: ${YELLOW}$DO_COUNT${NC}"
echo -e "  GCP references: ${YELLOW}$GCP_COUNT${NC}"

# Find specific references
find_references "digitalocean\|digital ocean" "DigitalOcean"
find_references "gcp\|google cloud\|google-cloud" "GCP"

# List specific files that need attention
echo -e "\n${BLUE}High-priority files to clean up:${NC}"

PRIORITY_FILES=(
    "fix_admin_ui_blank_screen.sh"
    ".cursor/mcp.json"
    ".cursor/rules/ALWAYS_APPLY_main_directives.mdc"
    ".cursor/rules/PULUMI_GCP_PATTERNS.mdc"
    "infra/Pulumi.yaml"
    "infra/Pulumi.dev.yaml"
    "mcp_server/servers/deployment_server.py"
    ".bashrc.orchestra"
    "DEPLOYMENT_ACTION_PLAN.md"
)

for file in "${PRIORITY_FILES[@]}"; do
    if [ -f "$file" ]; then
        if grep -q -i "digitalocean\|gcp\|google cloud" "$file" 2>/dev/null; then
            echo -e "  ${YELLOW}⚠ $file${NC}"
        else
            echo -e "  ${GREEN}✓ $file${NC}"
        fi
    fi
done

# Suggest actions
echo -e "\n${BLUE}Recommended Actions:${NC}"
echo -e "1. Replace fix_admin_ui_blank_screen.sh with fix_admin_ui_vultr.sh"
echo -e "2. Update .cursor/mcp.json to use only local services (PostgreSQL + Weaviate)"
echo -e "3. Update Cursor rules to reference Vultr instead of GCP"
echo -e "4. Remove any Pulumi configurations for DigitalOcean or GCP"
echo -e "5. Update deployment scripts to use Vultr infrastructure"
echo -e "6. Clean up documentation to reflect Vultr-only architecture"

echo -e "\n${CYAN}To automatically replace the most common references, run:${NC}"
echo -e "${CYAN}  ./cleanup_cloud_references.sh --fix${NC}"

# If --fix flag is provided, perform automatic fixes
if [ "$1" == "--fix" ]; then
    echo -e "\n${BLUE}Performing automatic fixes...${NC}"
    
    # Remove old DigitalOcean fix script
    if [ -f "fix_admin_ui_blank_screen.sh" ]; then
        echo -e "${YELLOW}Removing fix_admin_ui_blank_screen.sh...${NC}"
        rm -f fix_admin_ui_blank_screen.sh
        echo -e "${GREEN}✓ Removed${NC}"
    fi
    
    # Make the new Vultr fix script executable
    if [ -f "fix_admin_ui_vultr.sh" ]; then
        chmod +x fix_admin_ui_vultr.sh
        echo -e "${GREEN}✓ Made fix_admin_ui_vultr.sh executable${NC}"
    fi
    
    # Update deploy_admin_ui.sh to use local deployment
    if [ -f "deploy_admin_ui.sh" ]; then
        echo -e "${YELLOW}Updating deploy_admin_ui.sh...${NC}"
        cat > deploy_admin_ui.sh << 'EOF'
#!/bin/bash
# Deploy Admin UI to Vultr nginx
set -e

echo "🚀 Deploying Admin UI..."

cd admin-ui

# Build
echo "📦 Building Admin UI..."
pnpm run build-no-ts || pnpm build

# Deploy
echo "🗑️  Clearing old files..."
sudo rm -rf /var/www/orchestra-admin/*

echo "📤 Deploying new build..."
sudo cp -r dist/* /var/www/orchestra-admin/

# Set permissions
sudo chown -R www-data:www-data /var/www/orchestra-admin
sudo chmod -R 755 /var/www/orchestra-admin

# Reload nginx
echo "🔄 Reloading nginx..."
sudo systemctl reload nginx

echo "✅ Admin UI deployed successfully!"
echo "🌐 Access at: https://cherry-ai.me/admin/"
echo ""
echo "📝 Login credentials:"
echo "   Username: scoobyjava"
echo "   Password: Huskers1983$"
EOF
        chmod +x deploy_admin_ui.sh
        echo -e "${GREEN}✓ Updated${NC}"
    fi
    
    echo -e "\n${GREEN}Automatic fixes completed!${NC}"
    echo -e "${YELLOW}Please manually review and update the remaining files.${NC}"
fi

echo -e "\n${GREEN}Cleanup scan complete!${NC}" 