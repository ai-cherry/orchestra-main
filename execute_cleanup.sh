#!/bin/bash
# Execute Cleanup Script for cherry_ai
#
# This script implements the cleanup plan documented in final_cleanup_plan.md
# Updated: May 2025
# WARNING: Only run this script after verifying that:
# 1. The FirestoreMemoryManagerV2 adapter is working correctly
# 2. The pre-deployment checks are passing

set -e  # Exit on error

# ANSI color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BLUE='\033[0;34m'

echo -e "${BLUE}========================================================${NC}"
echo -e "${BLUE}      cherry_ai Redundancy Elimination Execution        ${NC}"
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
if [ ! -f "/workspaces/cherry_ai-main/packages/shared/src/storage/firestore/v2/adapter.py" ]; then
    echo -e "${RED}Error: FirestoreMemoryManagerV2 not found at expected location.${NC}"
    exit 1
fi

# Check that unified scripts exist
if [ ! -f "/workspaces/cherry_ai-main/unified_setup.sh" ] || [ ! -f "/workspaces/cherry_ai-main/unified_diagnostics.py" ]; then
    echo -e "${RED}Error: Unified scripts not found.${NC}"
    exit 1
fi

echo -e "${GREEN}Prerequisites checked successfully.${NC}"

# Step 1: Remove redundant files
echo -e "${YELLOW}Step 1: Removing deprecated files...${NC}"

# Updated list of files to remove based on current needs (May 2025)
FILES_TO_REMOVE=(
    "updated_phidata_wrapper.py"
    "setup_Vultr_auth.sh"
    "diagnose_environment.py"
    "deprecated_firestore_v1.py"
    "legacy_migration_script.sh"
    "old_gemini_adapter.py"
)

for file in "${FILES_TO_REMOVE[@]}"; do
    if [ -f "/workspaces/cherry_ai-main/$file" ]; then
        echo "Removing $file..."
        git rm "/workspaces/cherry_ai-main/$file"
    else
        echo "File $file not found, skipping removal."
    fi
done

echo -e "${GREEN}Deprecated files removed successfully.${NC}"

# Step 2: Fix import issues
echo -e "${YELLOW}Step 2: Fixing import issues...${NC}"

echo "Creating a backup of files with import issues..."
BACKUP_DIR="/workspaces/cherry_ai-main/backups/import_fixes_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Find files with deprecated imports and back them up
grep -r --include="*.py" "from packages.memory.src.base" /workspaces/cherry_ai-main | awk -F: '{print $1}' | sort -u | xargs -I{} cp {} "$BACKUP_DIR"/

echo "Updating imports from packages.memory.src.base to packages.shared.src.memory.memory_manager..."
find /workspaces/cherry_ai-main -type f -name "*.py" -exec sed -i 's/from packages\.memory\.src\.base import MemoryManager/from packages.shared.src.memory.memory_manager import MemoryManager/g' {} \;

# Also update any other outdated imports
echo "Updating additional deprecated imports..."
find /workspaces/cherry_ai-main -type f -name "*.py" -exec sed -i 's/from packages\.shared\.src\.storage\.firestore\.firestore_memory import FirestoreMemoryManager/from packages.shared.src.storage.firestore.v2.adapter import FirestoreMemoryManagerV2/g' {} \;

echo -e "${GREEN}Import issues fixed. Backup created in $BACKUP_DIR${NC}"

# Step 3: Create documentation
echo -e "${YELLOW}Step 3: Creating documentation for memory system structure...${NC}"

mkdir -p /workspaces/cherry_ai-main/docs
cat > /workspaces/cherry_ai-main/docs/MEMORY_SYSTEM_STRUCTURE.md << 'EOF'
# Memory System Structure

This document outlines the current structure of the memory system components in cherry_ai.

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

## Workload Identity Federation

For production deployments, always use Workload Identity Federation instead of service account keys.
See the `cherry_ai_wif_master.sh` script for setting up Workload Identity Federation.
EOF

echo -e "${GREEN}Documentation created at /workspaces/cherry_ai-main/docs/MEMORY_SYSTEM_STRUCTURE.md${NC}"

# Step 4: Add detailed deprecation notice to FirestoreMemoryManager
echo -e "${YELLOW}Step 4: Adding detailed deprecation notice to FirestoreMemoryManager...${NC}"

if [ -f "/workspaces/cherry_ai-main/add_deprecation_notices.py" ]; then
    chmod +x /workspaces/cherry_ai-main/add_deprecation_notices.py
    /workspaces/cherry_ai-main/add_deprecation_notices.py --file packages/shared/src/storage/firestore/firestore_memory.py
    echo -e "${GREEN}Deprecation notice added to FirestoreMemoryManager.${NC}"
else
    echo -e "${YELLOW}Warning: add_deprecation_notices.py not found, adding deprecation notice manually...${NC}"

    # Add deprecation notice manually if the Python script doesn't exist
    FIRESTORE_FILE="packages/shared/src/storage/firestore/firestore_memory.py"
    if [ -f "$FIRESTORE_FILE" ]; then
        # Create a temporary file
        TEMP_FILE=$(mktemp)

        # Add deprecation notice to the beginning of the file
        cat > "$TEMP_FILE" << 'EOD'
"""
DEPRECATED: This module is deprecated and will be removed in a future version.

Please use the V2 implementation instead:
from packages.shared.src.storage.firestore.v2.adapter import FirestoreMemoryManagerV2

Migration is straightforward as the V2 implementation maintains API compatibility.
"""
import warnings

warnings.warn(
    "FirestoreMemoryManager is deprecated. Use FirestoreMemoryManagerV2 instead.",
    DeprecationWarning,
    stacklevel=2
)

EOD

        # Append the original content
        cat "$FIRESTORE_FILE" >> "$TEMP_FILE"

        # Replace the original file
        mv "$TEMP_FILE" "$FIRESTORE_FILE"

        echo -e "${GREEN}Deprecation notice added manually to FirestoreMemoryManager.${NC}"
    else
        echo -e "${RED}Error: FirestoreMemoryManager file not found at $FIRESTORE_FILE${NC}"
    fi
fi

# Step 5: Check for hardcoded organization names and update them
echo -e "${YELLOW}Step 5: Checking for hardcoded organization references...${NC}"

# Look for hardcoded references to 'ai-cherry' organization and suggest updating them
HARDCODED_ORG_FILES=$(grep -l "ai-cherry" --include="*.sh" --include="*.py" --include="*.yml" --include="*.yaml" /workspaces/cherry_ai-main)

if [ -n "$HARDCODED_ORG_FILES" ]; then
    echo -e "${YELLOW}Found hardcoded organization references in the following files:${NC}"
    echo "$HARDCODED_ORG_FILES"
    echo -e "${YELLOW}Consider updating these to use environment variables instead.${NC}"

    read -p "Would you like to see examples of the hardcoded references? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        grep -n "ai-cherry" --include="*.sh" --include="*.py" --include="*.yml" --include="*.yaml" /workspaces/cherry_ai-main | head -10
    fi

    read -p "Would you like to automatically update these references to use environment variables? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Updating hardcoded references...${NC}"

        # Create backups
        for file in $HARDCODED_ORG_FILES; do
            cp "$file" "$file.bak"
        done

        # Update the files
        find /workspaces/cherry_ai-main -type f \( -name "*.sh" -o -name "*.py" -o -name "*.yml" -o -name "*.yaml" \) -exec sed -i 's/ai-cherry/${GITHUB_ORG:-ai-cherry}/g' {} \;

        echo -e "${GREEN}Updated hardcoded references. Backups created with .bak extension.${NC}"
    fi
else
    echo -e "${GREEN}No hardcoded organization references found.${NC}"
fi

# Step 6: Verify changes and commit
echo -e "${YELLOW}Step 6: Verifying changes...${NC}"

git add /workspaces/cherry_ai-main/docs/MEMORY_SYSTEM_STRUCTURE.md
git status -s

echo -e "${GREEN}=============================================================${NC}"
echo -e "${GREEN}Cleanup execution completed successfully!${NC}"
echo -e "${GREEN}=============================================================${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Review the changes with 'git status'"
echo "2. Run tests with './run_tests.sh'"
echo "3. Verify with pre-deployment checks"
echo "4. Commit with appropriate message: git commit -m \"Remove deprecated files and update memory module imports\""
echo "5. Consider running './cleanup_workspace.sh' to clean up temporary files and directories"
echo "6. If deploying to production, use Workload Identity Federation instead of service account keys"
