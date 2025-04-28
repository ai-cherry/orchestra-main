#!/bin/bash
# Execute Cleanup Script for Orchestra
#
# This script implements the cleanup plan documented in final_cleanup_plan.md
# WARNING: Only run this script after verifying that:
# 1. The FirestoreMemoryManagerV2 adapter is working correctly
# 2. The run_pre_deployment_automated.sh script passes

set -e  # Exit on error

# ANSI color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BLUE='\033[0;34m'

echo -e "${BLUE}========================================================${NC}"
echo -e "${BLUE}      Orchestra Redundancy Elimination Execution        ${NC}"
echo -e "${BLUE}========================================================${NC}"

# Confirm before proceeding
read -p "This script will remove deprecated files and fix import issues. Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo -e "${RED}Aborted.${NC}"
    exit 1
fi

echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check that FirestoreMemoryManagerV2 exists
if [ ! -f "/workspaces/orchestra-main/packages/shared/src/storage/firestore/v2/adapter.py" ]; then
    echo -e "${RED}Error: FirestoreMemoryManagerV2 not found at expected location.${NC}"
    exit 1
fi

# Check that unified scripts exist
if [ ! -f "/workspaces/orchestra-main/unified_setup.sh" ] || [ ! -f "/workspaces/orchestra-main/unified_diagnostics.py" ]; then
    echo -e "${RED}Error: Unified scripts not found.${NC}"
    exit 1
fi

echo -e "${GREEN}Prerequisites checked successfully.${NC}"

# Step 1: Remove redundant files
echo -e "${YELLOW}Step 1: Removing deprecated files...${NC}"

# Check if files exist before removing
FILES_TO_REMOVE=("updated_phidata_wrapper.py" "setup_gcp_auth.sh" "diagnose_environment.py")
for file in "${FILES_TO_REMOVE[@]}"; do
    if [ -f "/workspaces/orchestra-main/$file" ]; then
        echo "Removing $file..."
        git rm "/workspaces/orchestra-main/$file"
    else
        echo "File $file not found, skipping removal."
    fi
done

echo -e "${GREEN}Deprecated files removed successfully.${NC}"

# Step 2: Fix import issues
echo -e "${YELLOW}Step 2: Fixing import issues...${NC}"

echo "Creating a backup of files with import issues..."
mkdir -p /workspaces/orchestra-main/backups/import_fixes_$(date +%Y%m%d_%H%M%S)
grep -r --include="*.py" "from packages.memory.src.base" /workspaces/orchestra-main | awk -F: '{print $1}' | sort -u | xargs -I{} cp {} /workspaces/orchestra-main/backups/import_fixes_$(date +%Y%m%d_%H%M%S)/

echo "Updating imports from packages.memory.src.base to packages.shared.src.memory.memory_manager..."
find /workspaces/orchestra-main -type f -name "*.py" -exec sed -i 's/from packages\.memory\.src\.base import MemoryManager/from packages.shared.src.memory.memory_manager import MemoryManager/g' {} \;

echo -e "${GREEN}Import issues fixed. Backup created in /workspaces/orchestra-main/backups/import_fixes_*${NC}"

# Step 3: Create documentation
echo -e "${YELLOW}Step 3: Creating documentation for memory system structure...${NC}"

mkdir -p /workspaces/orchestra-main/docs
cat > /workspaces/orchestra-main/docs/MEMORY_SYSTEM_STRUCTURE.md << 'EOF'
# Memory System Structure

This document outlines the current structure of the memory system components in Orchestra.

## Directory Structure

Memory management components are located in two main areas:

1. **packages/shared/src/memory/**
   - `memory_manager.py`: Base MemoryManager abstract class
   - `privacy_enhanced_memory_manager.py`: Enhanced version with privacy features
   - `dev_notes_manager.py`: Specialized manager for development notes

2. **packages/shared/src/storage/firestore/**
   - `firestore_memory.py`: Original Firestore implementation (DEPRECATED)
   - `v2/adapter.py`: V2 Firestore implementation (RECOMMENDED)
   - `v2/core.py`: Core functionality for V2 implementation 
   - `v2/models.py`: Data models for V2 implementation

3. **packages/phidata/src/**
   - `cloudsql_pgvector.py`: PG Vector configuration for memory storage

## Import Guidelines

When importing memory management components:

```python
# Import MemoryManager base class
from packages.shared.src.memory.memory_manager import MemoryManager

# Import enhanced memory managers
from packages.shared.src.memory.privacy_enhanced_memory_manager import PrivacyEnhancedMemoryManager
from packages.shared.src.memory.dev_notes_manager import DevNotesManager

# Import Firestore implementation (preferred V2 version)
from packages.shared.src.storage.firestore.v2.adapter import FirestoreMemoryManagerV2

# Import PG Vector configuration
from packages.phidata.src.cloudsql_pgvector import get_pgvector_memory, get_pg_agent_storage
```

**IMPORTANT:** Do not import from `packages.memory.src.base` as this path does not exist.

## Migration Recommendations

For code still using the original Firestore memory manager:

```python
# OLD
from packages.shared.src.storage.firestore.firestore_memory import FirestoreMemoryManager

# NEW
from packages.shared.src.storage.firestore.v2.adapter import FirestoreMemoryManagerV2
```

Note that initialization parameters are compatible between versions.
EOF

echo -e "${GREEN}Documentation created at /workspaces/orchestra-main/docs/MEMORY_SYSTEM_STRUCTURE.md${NC}"

# Step 4: Add detailed deprecation notice to FirestoreMemoryManager
echo -e "${YELLOW}Step 4: Adding detailed deprecation notice to FirestoreMemoryManager...${NC}"

if [ -f "/workspaces/orchestra-main/add_deprecation_notices.py" ]; then
    chmod +x /workspaces/orchestra-main/add_deprecation_notices.py
    /workspaces/orchestra-main/add_deprecation_notices.py --file packages/shared/src/storage/firestore/firestore_memory.py
    echo -e "${GREEN}Deprecation notice added to FirestoreMemoryManager.${NC}"
else
    echo -e "${YELLOW}Warning: add_deprecation_notices.py not found, skipping this step.${NC}"
    echo "You may want to manually add a deprecation notice to packages/shared/src/storage/firestore/firestore_memory.py"
fi

# Step 5: Verify changes
echo -e "${YELLOW}Step 5: Committing changes...${NC}"

git add /workspaces/orchestra-main/docs/MEMORY_SYSTEM_STRUCTURE.md
git status -s

echo -e "${GREEN}=============================================================${NC}"
echo -e "${GREEN}Cleanup execution completed successfully!${NC}"
echo -e "${GREEN}=============================================================${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Review the changes with 'git status'"
echo "2. Run tests with './run_tests.sh'"
echo "3. Verify with './run_pre_deployment_automated.sh'"
echo "4. Commit with appropriate message: git commit -m \"Remove deprecated files and fix memory module imports\""
