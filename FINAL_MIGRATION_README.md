# GCP Migration Toolkit

This repository contains everything needed to move the `agi-baby-cherry` project to organization `873291114285` and configure workstations with n2d-standard-32 machines and 2x NVIDIA T4 GPUs.

## Quick Decision Tree

1. **Direct Command Approach**
   ```bash
   # Execute single command migration
   gcloud beta projects move agi-baby-cherry --organization=873291114285
   
   # Verify success
   gcloud projects describe agi-baby-cherry --format="value(parent.id)"
   # Expected output: organizations/873291114285
   ```

2. **Scripts for Common Scenarios**
   - If you're scoobyjava@cherry-ai.me: `./personal_migrate.sh`
   - If you have a service account key: `./force_migration_nuclear.sh`
   - If you just want to verify: `./definitive_migration_verify.sh`

3. **Gemini Code Assist Templates**
   - Migration: Open `gemini_migration_script.js` and use Gemini prompt
   - Workstation Upgrade: Open `gemini_workstation_upgrade.js` and use Gemini prompt
   - Terraform: Open `gemini_terraform_workstation.js` and use Gemini prompt

## Ready-to-Use Migration Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `personal_migrate.sh` | User-specific migration for scoobyjava@cherry-ai.me | `chmod +x personal_migrate.sh && ./personal_migrate.sh` |
| `force_migration_nuclear.sh` | Force migration with service account key | `chmod +x force_migration_nuclear.sh && ./force_migration_nuclear.sh` |
| `definitive_migration_verify.sh` | Comprehensive verification | `chmod +x definitive_migration_verify.sh && ./definitive_migration_verify.sh` |
| `execute_gcp_migration_plan.sh` | All-in-one execution plan | `chmod +x execute_gcp_migration_plan.sh && ./execute_gcp_migration_plan.sh` |

## Gemini Code Assist Templates

Install Gemini Code Assist extension in VS Code/Codespaces, then use these files:

1. **Generate Migration Script**
   - Open `gemini_migration_script.js`
   - Use prompt: `/generate migration script that moves agi-baby-cherry to organization 873291114285`

2. **Fix Workstation Configuration**
   - Open `gemini_workstation_upgrade.js`
   - Use prompt: `/fix workstation configuration to upgrade from e2-standard-4 to n2d-standard-32 with 2x T4 GPUs`

3. **Generate Terraform for Infrastructure**
   - Open `gemini_terraform_workstation.js`
   - Use prompt: `/generate terraform to deploy n2d-standard-32 with T4 GPUs for project agi-baby-cherry`

## Documentation

| Document | Purpose |
|----------|---------|
| `FINAL_MIGRATION_EXECUTION_GUIDE.md` | Step-by-step guide for all user profiles |
| `ZERO_BULLSHIT_EXECUTION_SUMMARY.md` | Concise guide with direct commands |
| `USER_EXECUTION_GUIDE.md` | User-specific instructions |
| `MIGRATION_VERIFICATION_GUIDE.md` | Migration verification instructions |
| `NUCLEAR_VERIFICATION_README.md` | Documentation for verification suite |

## Required Manual Steps

If all automated approaches fail, follow these minimal manual steps:

```bash
# Set correct permissions
gcloud projects add-iam-policy-binding agi-baby-cherry \
  --member="user:YOUR_EMAIL" \
  --role="roles/owner"

gcloud organizations add-iam-policy-binding 873291114285 \
  --member="user:YOUR_EMAIL" \
  --role="roles/resourcemanager.projectCreator"

# Wait for IAM propagation (critical)
sleep 300  # 5 minutes

# Execute migration
gcloud beta projects move agi-baby-cherry --organization=873291114285

# Verify migration success
gcloud projects describe agi-baby-cherry --format="value(parent.id)"
# Expected output: organizations/873291114285
```

## Critical Success Indicators

All scripts verify these critical indicators:

1. **PRIMARY INDICATOR**: Project parent organization ID
   ```
   ✅ Project agi-baby-cherry in organization 873291114285
   ```

2. **INFRASTRUCTURE INDICATOR**: GPU configuration
   ```
   ✅ 2x NVIDIA T4 GPUs active in us-central1
   ```

3. **SERVICE INDICATOR**: Database connections
   ```
   ✅ Redis/AlloyDB connections established
   ```

## Security Notes

All scripts include these security features:
- Key file permissions restricted to 600 (owner read/write only)
- Options to securely delete credentials after verification
- Evidence files for audit trail
- Secure random data overwrite before key deletion

## Final Verification

After script execution, visually verify in GCP Console:
1. Go to IAM & Admin > Settings
2. Confirm the "Organization" field shows "cherry-ai.me"
