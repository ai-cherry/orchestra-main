#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Removing Legacy Code${NC}"
echo "===================="

# Remove deprecated scripts
echo -e "${YELLOW}Removing deprecated scripts...${NC}"
rm -f scripts/migrate_dragonfly_to_weaviate.py
rm -f mcp_server/scripts/deploy_monitoring.py

# Remove legacy memory manager references
echo -e "${YELLOW}Cleaning up legacy memory manager code...${NC}"
sed -i '/# Initialize legacy memory manager/,/logger\.warning("Legacy memory manager initialization failed/d' core/orchestrator/src/main.py
sed -i '/logger\.info("Closing legacy memory manager")/,/logger\.error(f"Error closing legacy memory manager/d' core/orchestrator/src/main.py

# Remove legacy LLM client references
echo -e "${YELLOW}Removing legacy LLM client code...${NC}"
sed -i '/def get_legacy_router/,/return get_router()/d' core/llm/factory.py
sed -i '/get_legacy_router/d' core/llm/__init__.py

# Remove GCP legacy references
echo -e "${YELLOW}Removing GCP legacy references...${NC}"
sed -i '/# Legacy GCP fields/,/gcp_project_id:/d' core/env_config.py
sed -i '/# Legacy Vector DB endpoints/,/pinecone_api_key:/d' core/env_config.py

# Remove old auth implementations
echo -e "${YELLOW}Removing old authentication files...${NC}"
rm -f core/auth/legacy_auth.py
rm -f core/auth/old_auth_handler.py

# Clean up imports
echo -e "${YELLOW}Cleaning up imports...${NC}"
find . -name "*.py" -type f -exec sed -i '/from.*legacy.*import/d' {} \;
find . -name "*.py" -type f -exec sed -i '/import.*legacy/d' {} \;

# Remove empty directories
echo -e "${YELLOW}Removing empty directories...${NC}"
find . -type d -empty -delete 2>/dev/null || true

# Summary
echo -e "${GREEN}Legacy code removal complete!${NC}"
echo -e "${GREEN}✓ Deprecated scripts removed${NC}"
echo -e "${GREEN}✓ Legacy memory manager code cleaned${NC}"
echo -e "${GREEN}✓ Legacy LLM client references removed${NC}"
echo -e "${GREEN}✓ GCP legacy fields removed${NC}"
echo -e "${GREEN}✓ Old authentication files removed${NC}"
echo -e "${GREEN}✓ Legacy imports cleaned${NC}"

echo -e "${YELLOW}Note: Please review the changes and test the application${NC}"