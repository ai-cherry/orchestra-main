# AI Orchestra Deployment Scripts Guide
=====================================

## ⚠️ IMPORTANT: Script Consolidation Notice

We have identified duplication in deployment scripts. **DO NOT** create new deployment scripts without checking existing ones first.

## Recommended Scripts to Use

### 1. `deploy_orchestra.sh` - Primary Deployment Script
**Purpose**: Deploy the complete AI Orchestra stack (includes SuperAGI)
**Use This For**:
- New deployments
- Production deployments
- Full infrastructure setup

```bash
ENVIRONMENT=prod ./scripts/deploy_orchestra.sh
```

### 2. `deploy_with_managed_services.sh` - Quick Deployment with Managed DBs
**Purpose**: Deploy to existing cluster using managed database services
**Use This For**:
- Quick deployments to existing clusters
- When using MongoDB Atlas, DragonflyDB Cloud, Weaviate Cloud
- Development/testing

```bash
./scripts/deploy_with_managed_services.sh
```

## Scripts to AVOID (Duplicates)

- ❌ `deploy_superagi.sh` - Duplicates functionality of deploy_orchestra.sh
- ❌ `deploy_optimized_infrastructure.sh` - Use deploy_orchestra.sh instead
- ❌ Creating new deployment scripts - Use existing ones!

## Decision Tree (Simplified)

```
Need to deploy?
│
├─ Have existing cluster + managed DBs?
│  └─ YES → Use deploy_with_managed_services.sh
│
└─ Need full infrastructure?
   └─ YES → Use deploy_orchestra.sh
```

## Best Practices

1. **Check existing scripts first**
   ```bash
   ls scripts/deploy*.sh
   grep -l "deploy" scripts/*.sh
   ```

2. **Don't create duplicates**
   - If you need different behavior, modify existing scripts
   - Add flags/options rather than creating new scripts

3. **Use environment variables for configuration**
   ```bash
   ENVIRONMENT=prod REGION=us-east1 ./scripts/deploy_orchestra.sh
   ```

## Cleanup Recommendation

Consider removing these duplicate scripts:
```bash
# These scripts duplicate functionality
rm scripts/deploy_superagi.sh  # Duplicates deploy_orchestra.sh
rm scripts/deploy_optimized_infrastructure.sh  # Duplicates deploy_orchestra.sh
```

## If You Need Custom Deployment

Instead of creating a new script:

1. **Add options to existing scripts**:
   ```bash
   # Good: Add flag to existing script
   ./scripts/deploy_orchestra.sh --skip-monitoring

   # Bad: Create deploy_orchestra_no_monitoring.sh
   ```

2. **Use configuration files**:
   ```bash
   # Good: Use config file
   ./scripts/deploy_orchestra.sh --config=configs/minimal.yaml

   # Bad: Create deploy_minimal.sh
   ```

3. **Use Pulumi stacks for variations**:
   ```bash
   # Good: Different stacks for different configs
   PULUMI_STACK=dev-minimal pulumi up

   # Bad: Create deploy_dev_minimal.sh
   ```
