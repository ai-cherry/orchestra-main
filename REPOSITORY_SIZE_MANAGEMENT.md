# AI Orchestra Repository Size Management

This document outlines the strategy and implementation details for managing the AI Orchestra repository size. It provides guidance for developers on how to maintain a healthy repository while working with the codebase.

## Background

The AI Orchestra repository was approaching GitHub size limits (4.3GB), primarily due to:
- Google Cloud SDK files in the repository (~712MB)
- SDK staging directories (~526MB)
- Cache directories (.mypy_cache, etc.)
- Other large files and binary artifacts

This implementation follows the comprehensive plan outlined in the GitHub Repository Size Management Implementation Plan.

## Phase 1: Immediate Size Reduction

### 1. External SDK Management

The Google Cloud SDK has been removed from the repository. Instead, use the provided installation script:

```bash
# Install the latest version
./scripts/install_gcloud_sdk.sh

# Install a specific version
./scripts/install_gcloud_sdk.sh 415.0.0
```

**Benefits:**
- Removes >1GB from the repository
- Provides consistent SDK installation across environments
- Allows developers to use their preferred SDK version

### 2. Cache Cleanup

We've updated the `.gitignore` file to exclude cache directories:
- `.mypy_cache/`
- `.ruff_cache/`
- `.pytest_cache/`
- `__pycache__/`

To clean up cache files from your local repository:

```bash
# Remove all cache directories
find . -type d -name "__pycache__" -o -name ".mypy_cache" -o -name ".pytest_cache" -o -name ".ruff_cache" | xargs rm -rf

# Or use the cleanup script with dry-run first
./scripts/cleanup_repo.sh --dry-run
```

### 3. Pre-commit Hooks

Pre-commit hooks have been added to prevent accidental commits of large files or cache directories:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install
```

The pre-commit configuration includes:
- Checking for large files (>500KB)
- Preventing commit of ignored files
- Code formatting with Black and isort
- Linting with Ruff

### 4. Repository History Cleanup

For a comprehensive cleanup of the repository history, use the provided script:

```bash
# First, run in dry-run mode to see what would be removed
./scripts/cleanup_repo.sh --dry-run

# Then run for real (WARNING: modifies git history)
./scripts/cleanup_repo.sh
```

**IMPORTANT:** This script uses git-filter-repo to modify history. All team members will need to re-clone the repository after this operation.

## Development Environment Setup

A standardized development environment has been configured:

```bash
# Set up the development environment
./scripts/setup_dev_environment.sh

# Include SDK installation
./scripts/setup_dev_environment.sh --with-sdk
```

### VS Code Configuration

VS Code settings have been optimized to:
- Properly configure Python tools (Black, MyPy, Flake8)
- Hide cache and build directories from the file explorer
- Configure search exclusions for better performance
- Set up recommended extensions

## Best Practices

1. **Never commit the Google Cloud SDK** - Use the installation script instead
2. **Keep binary files out of the repository** - Consider Git LFS for necessary binaries
3. **Avoid committing cache directories** - Use .gitignore and pre-commit hooks
4. **Monitor repository size** - Regularly check with `du -sh .git`
5. **Be cautious with large files** - Files >500KB will be blocked by pre-commit

## Troubleshooting

### Large Clone Times

If cloning the repository takes too long:

```bash
# Shallow clone (faster)
git clone --depth 1 https://github.com/your-org/ai-orchestra.git

# Or clone with specific branch only
git clone --single-branch --branch main https://github.com/your-org/ai-orchestra.git
```

### Pre-commit Hook Issues

If pre-commit hooks are failing:

```bash
# Update hooks to latest versions
pre-commit autoupdate

# Run hooks manually
pre-commit run --all-files
```

### Missing Google Cloud SDK

If you need the SDK but don't want to install it globally:

```bash
# Install to project-local directory
./scripts/install_gcloud_sdk.sh

# Use local SDK
export PATH=$HOME/google-cloud-sdk/bin:$PATH
```

## Future Plans

Phase 1 implementation focuses on immediate size reduction. Future phases will include:
- Environment standardization
- Repository restructuring
- Advanced optimization with Git LFS
- Multi-root workspace configuration

Refer to the full implementation plan for details on upcoming changes.