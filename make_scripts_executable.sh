#!/bin/bash
# make_scripts_executable.sh - Make deployment scripts executable
#
# This script simply makes all deployment-related scripts executable.

# Color codes for output
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "Making deployment scripts executable..."

# Make the deployment scripts executable
chmod +x prepare_for_deployment.sh
chmod +x update_github_secrets.sh
chmod +x verify_deployment_readiness.sh
chmod +x deploy_to_cloud_run.sh
chmod +x setup_gcp_auth.sh
chmod +x setup_vertex_key.sh
chmod +x setup_redis_for_deployment.sh

if [ -f "infra/run_terraform.sh" ]; then
  chmod +x infra/run_terraform.sh
fi

echo -e "${GREEN}All deployment scripts are now executable.${NC}"
echo "You can run the following commands to prepare for deployment:"
echo "  1. ./verify_deployment_readiness.sh  (to check readiness)"
echo "  2. ./setup_vertex_key.sh             (to set up GCP authentication)"
echo "  3. ./setup_redis_for_deployment.sh   (to configure Redis for production)"
echo "  4. ./prepare_for_deployment.sh       (to install requirements)"
echo "  5. ./update_github_secrets.sh        (to configure CI/CD)"
