# GCP Project Migration Verification Guide

## Nuclear Verification Suite

This guide explains how to use the verification scripts to definitively prove the migration of `cherry-ai-project` project to organization `873291114285`, including verification of workstations, GPUs, and database connections.

## Quick Reference

### Option 1: Definitive Force Migration & Verification (Recommended)

```bash
# Make executable
chmod +x force_migration_nuclear.sh

# Run the script
./force_migration_nuclear.sh
```

This script:
1. Creates service account key file (or uses existing)
2. Authenticates with GCP
3. Forces migration with debug logging
4. Conducts immediate post-migration checks
5. Performs final atomic verification
6. Securely cleans up credentials

### Option 2: Comprehensive Verification (No Migration)

```bash
# Make executable
chmod +x definitive_migration_verify.sh

# Run the script
./definitive_migration_verify.sh
```

This script:
1. Performs direct organization verification
2. Checks service account authentication
3. Validates IAM bindings
4. Verifies workstation clusters and GPU configuration
5. Checks database connections
6. Provides atomic proof of success
7. Attempts migration only if verification fails

### Option 3: Individual Tools

```bash
# Verify migration with nuclear option
./verify_migration.sh --nuke

# Prove migration with force option
./prove_migration.sh --force

# Execute migration plan with all steps
./execute_gcp_migration_plan.sh
```

## Verification Indicators

All scripts check for these critical success indicators:

1. **Organization Membership** (PRIMARY indicator)
   - Command: `gcloud projects describe cherry-ai-project --format="value(parent.id)"`
   - Success: `organizations/873291114285`

2. **GPU Configuration**
   - Command: `gcloud workstations configs describe ai-dev-config --cluster=ai-development --region=us-west4 --format="json(container.guestAccelerators)"`
   - Success: 2x NVIDIA T4 GPUs 

3. **Database Connections**
   - Redis: `gcloud redis instances describe agent-memory --region=us-west4 --format="value(state)"`
   - AlloyDB: `gcloud alloydb clusters describe agent-storage --region=us-west4 --format="value(state)"`
   - Success: Redis "READY" and AlloyDB "RUNNING"

## Troubleshooting & Critical Fixes

If verification fails, the scripts offer these remedies:

1. **Service Account Key Recreation**
   ```bash
   gcloud iam service-accounts keys create new-key.json \
     --iam-account=vertex-agent@cherry-ai-project.iam.gserviceaccount.com
   ```

2. **Billing Project Linkage**
   ```bash
   gcloud beta billing projects link cherry-ai-project \
     --billing-project=cherry-ai-project
   ```

3. **Organization Policy Exceptions**
   ```bash
   # Creates and applies appropriate policy exceptions
   # (Script creates this automatically when needed)
   ```

4. **Force Migration Retry**
   ```bash
   gcloud beta projects move cherry-ai-project \
     --organization=873291114285 \
     --billing-project=cherry-ai-project \
     --quiet
   ```

## Security Measures

All scripts include these security features:

1. Key file permissions restricted to 600 (owner read/write only)
2. Options to securely delete credentials after verification
3. Evidence files for audit trail
4. Secure random data overwrite before key deletion

## Obtaining Definitive Proof

For a simple command that provides atomic proof of migration:

```bash
gcloud projects describe cherry-ai-project --format="value(name,parent.id)"
```

Expected output: `cherry-ai-project organizations/873291114285`

This single command provides the most direct evidence that migration succeeded.
