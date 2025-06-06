# GitHub Workflows - Unified Lambda Architecture

## Overview
Cherry AI uses a simplified GitHub Actions workflow that syncs code directly to the production Lambda server where all development and deployment occur.

## Active Workflows

### 1. `sync-lambda.yml` - Main Deployment Workflow
- **Trigger**: Push to main branch or manual dispatch
- **Purpose**: Sync code from GitHub to Lambda server
- **Features**:
  - Automatic git pull on server
  - Optional service restart
  - Health checks after deployment
  - Smart restart detection (only restarts if Python/requirements change)

## Deprecated Workflows
The following workflows are kept for reference but are no longer used:
- `deploy.yaml` - Old multi-environment deployment
- `deploy-lambda.yml` - Superseded by sync-lambda.yml
- `ci.yml` - Testing now happens on server
- `pulumi-deploy.yml` - Infrastructure is stable, no frequent changes

## Usage

### Automatic Deployment
Every push to main automatically:
1. SSHs to Lambda server
2. Pulls latest code
3. Runs validation
4. Restarts services if needed

### Manual Deployment
Use workflow dispatch to:
- Force a sync
- Optionally restart services

## Required Secrets
- `SSH_PRIVATE_KEY`: SSH key for Lambda server access

## Benefits
- No environment confusion
- Instant deployments
- Simple and reliable
- Direct server development
