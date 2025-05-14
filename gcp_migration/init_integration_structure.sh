#!/bin/bash
# Script to initialize the directory structure for GCP-GitHub integration

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Initializing GCP-GitHub Integration Structure...${NC}"

# Create required directories
mkdir -p gcp_migration/templates
mkdir -p gcp_migration/.github/workflows
mkdir -p gcp_migration/tests

# Copy GitHub workflow file to templates directory
if [[ -f gcp_migration/.github/workflows/deploy-cloud-run.yml ]]; then
    cp gcp_migration/.github/workflows/deploy-cloud-run.yml gcp_migration/templates/
    echo -e "${GREEN}✓ Copied workflow template${NC}"
fi

# Create template directory for incident reports
mkdir -p gcp_migration/templates/incidents
cat > gcp_migration/templates/incidents/incident_report_template.md << 'EOF'
# Migration Incident Report

## Incident Summary
**Date:** {{DATE}}
**Time:** {{TIME}}
**Environment:** {{ENVIRONMENT}}
**Component:** {{COMPONENT}}
**Severity:** {{SEVERITY}}

## Description
{{DESCRIPTION}}

## Impact
{{IMPACT}}

## Root Cause
{{ROOT_CAUSE}}

## Resolution
{{RESOLUTION}}

## Timeline
- **Detection:** {{DETECTION_TIME}} - {{DETECTION_METHOD}}
- **Response:** {{RESPONSE_TIME}} - {{RESPONSE_ACTION}}
- **Resolution:** {{RESOLUTION_TIME}} - {{RESOLUTION_ACTION}}
- **All Clear:** {{ALL_CLEAR_TIME}}

## Lessons Learned
{{LESSONS_LEARNED}}

## Action Items
{{ACTION_ITEMS}}

## Additional Notes
{{ADDITIONAL_NOTES}}
EOF
echo -e "${GREEN}✓ Created incident report template${NC}"

# Create __init__.py files to make the modules importable
touch gcp_migration/__init__.py
echo -e "${GREEN}✓ Created __init__.py files${NC}"

# Create a README file for the gcp_migration directory
cat > gcp_migration/README.md << 'EOF'
# AI Orchestra GCP Migration and GitHub Integration

This directory contains tools and utilities for migrating the AI Orchestra project to Google Cloud Platform and implementing secure GitHub-GCP integration.

## Components

- **secure_auth.py**: Secure authentication module for GCP and GitHub
- **secure_secret_sync.py**: Bidirectional secret synchronization between GitHub and GCP Secret Manager
- **setup_gcp_github_integration.py**: CLI for setting up and managing the GitHub-GCP integration
- **.github/workflows/**: GitHub Actions workflow templates
- **templates/**: Templates for various components
- **requirements.txt**: Required dependencies

## Getting Started

1. Install the required dependencies:
   ```bash
   pip install -r gcp_migration/requirements.txt
   ```

2. Set up the necessary environment variables:
   ```bash
   export GCP_MASTER_SERVICE_JSON='{"type": "service_account", ...}'
   export GH_CLASSIC_PAT_TOKEN='your_github_token'
   ```

3. Run the integration setup:
   ```bash
   python gcp_migration/setup_gcp_github_integration.py setup --project-id=your-project-id --github-org=your-org
   ```

4. See GCP_GITHUB_INTEGRATION.md for detailed documentation
EOF
echo -e "${GREEN}✓ Created README.md${NC}"

# Create a simple test for the authentication module
cat > gcp_migration/tests/test_secure_auth.py << 'EOF'
#!/usr/bin/env python3
"""
Tests for the secure_auth module.
"""

import os
import sys
import unittest
from unittest import mock
from pathlib import Path

# Add parent directory to path
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from secure_auth import (
    GCPAuth, GCPConfig, GitHubAuth, GitHubConfig, AuthMethod, SecureCleanup
)


class TestSecureCleanup(unittest.TestCase):
    """Tests for the SecureCleanup class."""
    
    def test_init(self):
        """Test initialization."""
        cleanup = SecureCleanup()
        self.assertEqual(cleanup._temp_files, [])
        self.assertEqual(cleanup._temp_dirs, [])
    
    def test_register_temp_file(self):
        """Test registering a temporary file."""
        cleanup = SecureCleanup()
        cleanup.register_temp_file("/tmp/test.txt")
        self.assertEqual(len(cleanup._temp_files), 1)
        self.assertEqual(str(cleanup._temp_files[0]), "/tmp/test.txt")


class TestGCPConfig(unittest.TestCase):
    """Tests for the GCPConfig class."""
    
    def test_init(self):
        """Test initialization."""
        config = GCPConfig(project_id="test-project", region="us-central1")
        self.assertEqual(config.project_id, "test-project")
        self.assertEqual(config.region, "us-central1")
        self.assertIsNone(config.zone)


class TestGitHubConfig(unittest.TestCase):
    """Tests for the GitHubConfig class."""
    
    def test_init(self):
        """Test initialization."""
        config = GitHubConfig(org_name="test-org", repo_name="test-repo")
        self.assertEqual(config.org_name, "test-org")
        self.assertEqual(config.repo_name, "test-repo")
        self.assertIsNone(config.token)
        self.assertFalse(config.use_fine_grained_token)


if __name__ == "__main__":
    unittest.main()
EOF
echo -e "${GREEN}✓ Created test file${NC}"

# Make scripts executable
chmod +x gcp_migration/secure_auth.py
chmod +x gcp_migration/secure_secret_sync.py
chmod +x gcp_migration/setup_gcp_github_integration.py
chmod +x gcp_migration/tests/test_secure_auth.py
chmod +x gcp_migration/init_integration_structure.sh
echo -e "${GREEN}✓ Made scripts executable${NC}"

echo -e "${BLUE}GCP-GitHub Integration Structure Initialized!${NC}"
echo
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "1. Install required dependencies: ${BLUE}pip install -r gcp_migration/requirements.txt${NC}"
echo -e "2. Set up required environment variables for authentication"
echo -e "3. Run the integration setup script: ${BLUE}python gcp_migration/setup_gcp_github_integration.py --help${NC}"
echo
echo -e "${BLUE}For more information, see:${NC} ${YELLOW}gcp_migration/GCP_GITHUB_INTEGRATION.md${NC}"