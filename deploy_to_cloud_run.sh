#!/bin/bash
# This is a compatibility wrapper for the legacy deploy_to_cloud_run.sh script
# It redirects to the new unified deployment script (deploy.sh)

# Color codes for output
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${YELLOW}${BOLD}⚠️  DEPRECATED SCRIPT NOTICE ⚠️${NC}"
echo -e "${YELLOW}deploy_to_cloud_run.sh is deprecated and will be removed in a future update.${NC}"
echo -e "${YELLOW}Please use the new unified deployment script instead:${NC}"
echo -e "${BLUE}./deploy.sh [env] cloud-run${NC}"
echo -e ""

# Check if user provided an environment argument
ENV=${1:-dev}

echo -e "${YELLOW}Redirecting to: ./deploy.sh $ENV cloud-run${NC}"
echo -e "${YELLOW}Continuing in 3 seconds... (Press Ctrl+C to cancel)${NC}"
sleep 3

# Execute the new deploy.sh script with cloud-run method
exec ./deploy.sh $ENV cloud-run
