#!/bin/bash
# This is a compatibility wrapper for the legacy deploy_to_production.sh script
# It redirects to the new unified deployment script (deploy.sh)

# Color codes for output
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${YELLOW}${BOLD}⚠️  DEPRECATED SCRIPT NOTICE ⚠️${NC}"
echo -e "${YELLOW}deploy_to_production.sh is deprecated and will be removed in a future update.${NC}"
echo -e "${YELLOW}Please use the new unified deployment script instead:${NC}"
echo -e "${BLUE}./deploy.sh prod terraform${NC}"
echo -e ""

# Get project ID if provided
PROJECT_ID=${1:-"agi-baby-cherry"}

echo -e "${YELLOW}Redirecting to: ./deploy.sh prod terraform${NC}"
echo -e "${YELLOW}Using project ID: $PROJECT_ID${NC}"
echo -e "${YELLOW}Continuing in 3 seconds... (Press Ctrl+C to cancel)${NC}"
sleep 3

# Set project ID in environment variable for the deploy script to access
export PROJECT_ID=$PROJECT_ID

# Execute the new deploy.sh script with terraform method targeting production
exec ./deploy.sh prod terraform
