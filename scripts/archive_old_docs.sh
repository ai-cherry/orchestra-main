#!/bin/bash
# Archive Old Documentation
# =========================
# Moves outdated documentation to archive directory

set -euo pipefail

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Archiving old documentation files...${NC}"

# Create archive directory if it doesn't exist
mkdir -p docs/archive/old-root-docs

# Files to archive from root directory
ROOT_FILES=(
    "README_NO_BS.md"
    "UNFUCK_EVERYTHING.md"
    "CLEANUP_COMPLETE.md"
    "setup_github_secrets.md"
    "CLOUDSHELL_DEPLOYMENT_GUIDE.md"
    "PROJECT_PRIORITIES.md"
)

# Archive root files
for file in "${ROOT_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo "Archiving $file..."
        mv "$file" "docs/archive/old-root-docs/" || true
    fi
done

# Archive old deployment guides
if [[ -f "docs/gcp_deployment_guide.md" ]]; then
    echo "Archiving docs/gcp_deployment_guide.md..."
    mv "docs/gcp_deployment_guide.md" "docs/archive/" || true
fi

if [[ -f "docs/cloud_run_deployment.md" ]]; then
    echo "Archiving docs/cloud_run_deployment.md..."
    mv "docs/cloud_run_deployment.md" "docs/archive/" || true
fi

# Update any references to Terraform (old approach)
if [[ -f "docs/agent_infrastructure.md" ]]; then
    echo "Updating docs/agent_infrastructure.md to remove Terraform references..."
    sed -i.bak 's/Terraform/Pulumi/g' "docs/agent_infrastructure.md"
    sed -i.bak 's/terraform\//infra\//g' "docs/agent_infrastructure.md"
    rm -f "docs/agent_infrastructure.md.bak"
fi

echo -e "${GREEN}Documentation cleanup complete!${NC}"
echo
echo "Archived files are in:"
echo "- docs/archive/old-root-docs/"
echo "- docs/archive/"
echo
echo "Current documentation structure:"
echo "- README.md (simplified)"
echo "- docs/QUICK_START_OPTIMIZED.md"
echo "- docs/INFRASTRUCTURE_GUIDE.md"
echo "- docs/DEVELOPMENT_GUIDE.md"
echo "- docs/CURSOR_AI_OPTIMIZATION_GUIDE.md"
