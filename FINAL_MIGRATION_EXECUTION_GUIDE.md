# Final Migration Execution Guide

This document brings together all the migration verification tools and provides a simple, step-by-step approach for different user profiles.

## Quick Decision Tree

1. **Are you scoobyjava@cherry-ai.me?**
   - YES → Use [Personal Migration Script](#personal-migration-for-scoobyjava) (simplest option)
   - NO → Continue to step 2

2. **Do you have a service account key?**
   - YES → Use [Force Migration Script](#force-migration-with-service-account) (most reliable option)
   - NO → Continue to step 3

3. **Do you just want to verify if migration already happened?**
   - YES → Use [Verification Only](#verification-only) (non-destructive)
   - NO → Use [Direct Command Migration](#direct-command-migration) (simplest option)

## Personal Migration for scoobyjava

The simplest option if you are scoobyjava@cherry-ai.me:

```bash
# One-click execution
chmod +x personal_migrate.sh
./personal_migrate.sh
```

This script:
1. Grants all necessary permissions to your user account
2. Performs the migration
3. Verifies the migration succeeded
4. Optionally creates a master service account

## Force Migration with Service Account

Most reliable option with full debug logging:

```bash
# Using the service account approach
chmod +x force_migration_nuclear.sh
./force_migration_nuclear.sh
```

If prompted, enter your service account private key (the part between BEGIN PRIVATE KEY and END PRIVATE KEY).

This script:
1. Sets up key file with secure permissions
2. Forces migration with full debug logging
3. Performs immediate post-migration checks
4. Applies critical fixes if needed
5. Validates migration success

## Verification Only

To check if migration has already happened without making changes:

```bash
# Just verification
chmod +x definitive_migration_verify.sh
./definitive_migration_verify.sh
```

This will check:
- Organization membership (primary indicator)
- Workstation and GPU configuration
- Database connections
- Provides detailed evidence

## Direct Command Migration

For users who prefer direct gcloud commands:

```bash
# Step 1: Set correct permissions
gcloud projects add-iam-policy-binding cherry-ai-project \
  --member="user:YOUR_EMAIL" \
  --role="roles/owner"

gcloud organizations add-iam-policy-binding 873291114285 \
  --member="user:YOUR_EMAIL" \
  --role="roles/resourcemanager.projectCreator"

# Step 2: Wait for permissions to propagate (important!)
sleep 300  # Wait 5 minutes

# Step 3: Execute migration
gcloud beta projects move cherry-ai-project --organization 873291114285

# Step 4: Verify migration
gcloud projects describe cherry-ai-project --format="value(parent.id)"
# Should return: organizations/873291114285
```

## Critical Success Indicators

All methods verify these critical indicators:

1. **PRIMARY INDICATOR**: Project parent organization ID
   ```
   ✅ Project cherry-ai-project in organization 873291114285
   ```

2. **INFRASTRUCTURE INDICATOR**: GPU configuration
   ```
   ✅ 2x NVIDIA T4 GPUs active in us-west4
   ```

3. **SERVICE INDICATOR**: Database connections
   ```
   ✅ Redis/AlloyDB connections established
   ```

## Troubleshooting

If migration fails, common issues and solutions include:

1. **Permission Denied**
   - Solution: Wait longer for IAM propagation (5+ minutes)
   - Alternative: Grant higher-level permissions

2. **Billing Project Error**
   - Solution: 
     ```bash
     gcloud beta billing projects link cherry-ai-project \
       --billing-account=$(gcloud beta billing accounts list --format="value(name)")
     ```

3. **Organization Policy Error**
   - Solution: Try force option

## Evidence Collection

All scripts save evidence files:

- `migration_verification_evidence.txt`: Detailed verification evidence
- `migration_proof_evidence.txt`: Proof the migration succeeded
- `migration_debug.log`: Debug output from the migration command

## Final Verification in GCP Console

After script verification, check GCP Console visually:

1. Go to IAM & Admin > Settings
2. The "Organization" field should show "cherry-ai.me"
