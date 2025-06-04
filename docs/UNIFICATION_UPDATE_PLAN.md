# Unification Update Plan

## Overview
This document tracks the necessary updates to align all documentation, tools, and workflows with the unified Vultr server architecture where development, deployment, and production all occur on the same server.

## Current State
- ✅ Server is operational at 45.32.69.157
- ✅ Development happens directly on server via SSH/Cursor
- ❌ GitHub workflows still assume multi-environment
- ❌ Legacy scripts reference old infrastructure
- ❌ Documentation mentions CI/CD and staging

## Required Updates

### 1. GitHub Workflows
**File: `.github/workflows/deploy.yaml`**
- Remove `deploy-to-dev` and `deploy-to-prod` separation
- Remove GitHub environments
- Simplify to single deployment that syncs code to server
- Remove Pulumi stack selection (only one stack needed)

**Files to Archive/Delete:**
- `.github/workflows/pulumi-deploy.yml` (old)
- `.github/workflows/ci.yml` (if not used)

### 2. Scripts to Update/Remove
**Remove/Archive:**
- `deploy_with_aiven.sh` - References Paperspace, Railway
- `implement_two_node_architecture.sh` - DigitalOcean specific
- `deploy_gcp_infra_complete.sh` - GCP specific
- Any scripts referencing staging/production separation

**Update:**
- `deploy_real_agents.sh` - Simplify for single server
- `start_cherry_ai.sh` - Ensure it works for unified setup

### 3. Documentation Updates
**Files to Update:**
- `specs/admin-ui-promotion-process.md` - Remove dev/prod promotion
- `specs/admin-ui-executive-summary.md` - Update deployment section
- `ADMIN_UI_DEPLOYMENT_GUIDE.md` - Simplify for single server
- `.cursor/rules/activeContext.md` - Remove Paperspace/Cloud Run references

**Files to Archive:**
- Old migration docs that reference multi-cloud setup
- CI/CD specific documentation

### 4. Configuration Simplification
**Pulumi:**
- Single stack configuration
- Remove environment-specific configs
- Simplify to one set of resources

**Environment Variables:**
- Single `.env` file (no .env.dev, .env.prod)
- Remove environment switching logic

### 5. New Simplified Workflow
```yaml
name: Sync to Vultr

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Vultr
        uses: appleboy/ssh-action@v0.1.5
        with:
          host: 45.32.69.157
          username: root
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /root/cherry_ai-main
            git pull origin main
            make validate
            make restart-services
```

### Obsolete Scripts (To Be Removed or Replaced)
- `deploy_gcp_infra_quick.sh` - GCP specific, covered by Pulumi/Vultr
- `deploy_aws_infra.sh` - AWS specific
- `quick_start_cloud_run.sh` - GCP specific
- `scripts/migrate_firestore_to_postgres.py` - One-time migration script
- Any scripts relying on `gcloud` or `aws` CLI heavily without Vultr alternatives.

### Monitoring & Logging (To Be Standardized)

## Implementation Steps
1. Create new simplified GitHub workflow
2. Archive old workflows and scripts
3. Update all documentation
4. Test the simplified deployment
5. Remove unnecessary complexity

## Benefits
- No more environment confusion
- Instant deployments
- Simpler operations
- Lower cognitive overhead
- Faster development 