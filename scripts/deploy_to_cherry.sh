#!/bin/bash
# Cherry AI Deployment Script
# Generated: 2025-06-03 22:26:07

set -e

echo "🚀 Cherry AI Deployment"
echo "========================="

# Configuration
DOMAIN="cherry-ai.me"
LOCAL_BUILD="/root/cherry_ai-main/admin-ui/dist"
REMOTE_USER="root"
REMOTE_HOST="$DOMAIN"
REMOTE_PATH="/var/www/cherry_ai-admin"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to print colored output
print_status() {
    case $1 in
        "error") echo -e "${RED}❌ $2${NC}" ;;
        "success") echo -e "${GREEN}✅ $2${NC}" ;;
        "warning") echo -e "${YELLOW}⚠️  $2${NC}" ;;
        *) echo "$2" ;;
    esac
}

# Step 1: Build check
print_status "info" "Checking local build..."
if [ ! -d "$LOCAL_BUILD" ]; then
    print_status "error" "Build directory not found!"
    print_status "info" "Running build..."
    cd /root/cherry_ai-main/admin-ui
    npm run build
fi

# Step 2: Create backup
print_status "info" "Creating backup on remote server..."
ssh $REMOTE_USER@$REMOTE_HOST "mkdir -p /backup/$(date +%Y%m%d) && tar -czf /backup/$(date +%Y%m%d)/cherry_ai-backup-$(date +%H%M%S).tar.gz $REMOTE_PATH"

# Step 3: Deploy new build
print_status "info" "Deploying new build..."
rsync -avz --delete $LOCAL_BUILD/ $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH-new/

# Step 4: Swap deployments
print_status "info" "Swapping deployments..."
ssh $REMOTE_USER@$REMOTE_HOST << 'EOF'
    mv /var/www/cherry_ai-admin /var/www/cherry_ai-admin-old
    mv /var/www/cherry_ai-admin-new /var/www/cherry_ai-admin
    chown -R www-data:www-data /var/www/cherry_ai-admin
    chmod -R 755 /var/www/cherry_ai-admin
    systemctl reload nginx
EOF

# Step 5: Verify deployment
print_status "info" "Verifying deployment..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN)

if [ "$HTTP_STATUS" = "200" ]; then
    print_status "success" "Deployment successful! Site is accessible."
    
    # Check for new build
    BUILD_CHECK=$(curl -s https://$DOMAIN | grep -o 'index-[0-9]*' | head -1)
    print_status "success" "Current build: $BUILD_CHECK"
else
    print_status "error" "Site returned HTTP $HTTP_STATUS"
    print_status "warning" "Rolling back..."
    
    ssh $REMOTE_USER@$REMOTE_HOST << 'EOF'
        mv /var/www/cherry_ai-admin /var/www/cherry_ai-admin-failed
        mv /var/www/cherry_ai-admin-old /var/www/cherry_ai-admin
        systemctl reload nginx
EOF
    
    print_status "error" "Deployment failed and rolled back!"
    exit 1
fi

print_status "success" "Deployment complete!"
print_status "info" "Next steps:"
echo "  1. Test in incognito browser"
echo "  2. Clear CDN cache if applicable"
echo "  3. Monitor error logs: ssh $REMOTE_USER@$REMOTE_HOST 'tail -f /var/log/nginx/error.log'"
