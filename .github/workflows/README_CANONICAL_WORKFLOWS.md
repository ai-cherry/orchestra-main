# GitHub Workflows - Unified Vultr Architecture

## Overview
Orchestra AI uses a simplified GitHub Actions workflow that syncs code directly to the production Vultr server where all development and deployment occur.

## Active Workflows

### 1. `sync-vultr.yml` - Main Deployment Workflow
- **Trigger**: Push to main branch or manual dispatch
- **Purpose**: Sync code from GitHub to Vultr server
- **Features**:
  - Automatic git pull on server
  - Optional service restart
  - Health checks after deployment
  - Smart restart detection (only restarts if Python/requirements change)

## Deprecated Workflows
The following workflows are kept for reference but are no longer used:
- `deploy.yaml` - Old multi-environment deployment
- `deploy-vultr.yml` - Superseded by sync-vultr.yml
- `ci.yml` - Testing now happens on server
- `pulumi-deploy.yml` - Infrastructure is stable, no frequent changes

## Usage

### Automatic Deployment
Every push to main automatically:
1. SSHs to Vultr server
2. Pulls latest code
3. Runs validation
4. Restarts services if needed

### Manual Deployment
Use workflow dispatch to:
- Force a sync
- Optionally restart services

## Required Secrets
- `SSH_PRIVATE_KEY`: SSH key for Vultr server access

## Benefits
- No environment confusion
- Instant deployments
- Simple and reliable
- Direct server development
