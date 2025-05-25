# Orchestra Redundancy Elimination Plan

Based on the code review, this document outlines the safest redundancy elimination plan to simplify the codebase before deployment.

## Verified Current Structure

- **Phidata Agent Wrapper**:

  - Current official implementation: `packages/agents/src/phidata/wrapper.py`
  - Deprecated implementation: `updated_phidata_wrapper.py` (root directory)

- **Memory System**:

  - Current location: `packages/shared/src/storage/firestore/`
  - Original implementation: `firestore_memory.py`
  - V2 implementation: `v2/adapter.py`
  - Note: There is no `packages/memory/` directory as previously mentioned

- **Setup & Diagnostics**:
  - Current official implementations: `unified_setup.sh` and `unified_diagnostics.py`
  - Deprecated implementations: `setup_gcp_auth.sh` and `diagnose_environment.py`

## Priority 1 Cleanup (Safe to Execute)

These changes are safe to execute as they only remove files that are explicitly marked as deprecated and have clear replacements:

```bash
# Remove deprecated Phidata wrapper
git rm updated_phidata_wrapper.py

# Remove deprecated setup script
git rm setup_gcp_auth.sh

# Remove deprecated diagnostic script
git rm diagnose_environment.py

# Commit the changes
git commit -m "Remove deprecated scripts in favor of unified implementations"
```

## Priority 2 Cleanup (Requires Verification)

Before executing these changes, run `run_pre_deployment_automated.sh` to ensure all tests pass with the current structure:

```bash
# Create a backup of the original firestore implementation (if not already backed up)
# Note: There's already a backup at packages/shared/src/storage/firestore/backups/firestore_memory.py.bak

# Add a deprecation notice to the firestore_memory.py file
# This is safer than removing it immediately

# Update all imports to use the V2 implementation
# Search for: from packages.shared.src.storage.firestore.firestore_memory import FirestoreMemoryManager
# Replace with: from packages.shared.src.storage.firestore.v2.adapter import FirestoreMemoryManagerV2
```

## Future Structure Decisions

Rather than creating a new `packages/memory/` directory structure, the current recommendation is to:

1. Continue using the existing structure in `packages/shared/src/storage/firestore/`
2. Document this as the official location
3. Update any documentation that refers to a planned migration to `packages/memory/`

This approach minimizes disruption while providing a clear path forward.

## Final Verification

After making any changes, run the `run_pre_deployment_automated.sh` script to ensure all tests still pass.
