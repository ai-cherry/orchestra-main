# GCP Migration Nuclear Verification Suite

This repository contains a "Zero Bullshit" approach to verifying the successful migration of the `agi-baby-cherry` project to organization `873291114285`, with specific focus on confirming Vertex workstations with NVIDIA T4 GPUs and Redis/AlloyDB connections are established.

## Verification Scripts

We provide three distinct verification scripts, each with increasing levels of aggressive validation:

### 1. `execute_gcp_migration_plan.sh` - All-in-one Execution Plan

The comprehensive script that handles the entire verification process from start to finish:

```bash
# Make executable
chmod +x execute_gcp_migration_plan.sh

# Run the full verification plan
./execute_gcp_migration_plan.sh
```

This script:
1. Prepares the key file automatically
2. Authenticates with GCP
3. Runs nuclear verification
4. Validates critical outputs
5. Securely cleans up all credentials

Use this for the fastest and most secure verification experience.

### 2. `verify_migration.sh` - Nuclear Verification

The detailed verification script with nuclear-level validation:

```bash
# Make executable
chmod +x verify_migration.sh

# Run with nuclear verification mode
./verify_migration.sh --nuke

# Other options:
./verify_migration.sh --key-file=your-key-file.json
```

This script provides in-depth verification of:
- Organization membership
- Workstation clusters/configurations
- GPU availability (specifically 2x NVIDIA T4)
- Vertex AI API status
- Redis/AlloyDB connectivity

### 3. `prove_migration.sh` - Direct Evidence Collector

The focused, direct approach to collecting migration evidence:

```bash
# Make executable
chmod +x prove_migration.sh

# Basic execution
./prove_migration.sh

# Force execution even with partial verification
./prove_migration.sh --force

# With secure key rotation
./prove_migration.sh --rotate-keys
```

## Critical Verification Points

The verification suite validates three critical components:

1. **Organization Migration**: Confirms `agi-baby-cherry` is in organization `873291114285`
2. **GPU Configuration**: Verifies 2x NVIDIA T4 GPUs are active in us-central1
3. **Database Connections**: Validates Redis and AlloyDB are properly connected

A successful verification shows:

```
===== CRITICAL VERIFICATION RESULTS: =====
✅ Project agi-baby-cherry in organization 873291114285
✅ 2x NVIDIA T4 GPUs active in us-central1
✅ Redis/AlloyDB connections established
```

## Security Features

The verification suite includes robust security measures:

- **Key File Protection**: All scripts set key file permissions to 600 (owner read/write only)
- **Secure Deletion**: Keys are securely erased with random data overwrite before deletion
- **Service Account Revocation**: Authentication is automatically revoked after verification
- **Evidence Management**: Option to remove all evidence files

## Verification Evidence

Evidence is saved in standardized files:
- `migration_verification_evidence.txt`: Detailed evidence from verify_migration.sh
- `migration_proof_evidence.txt`: Focused evidence from prove_migration.sh

## Usage Examples

### Complete Nuclear Verification

For the most thorough verification:

```bash
./execute_gcp_migration_plan.sh
```

### Targeted GPU Verification

To check only GPU configuration:

```bash
./verify_migration.sh --nuke | grep -A 3 "NVIDIA T4 GPUs"
```

### Force Verification with Existing Key

If you have a key file with a different name:

```bash
./prove_migration.sh --key-file=your-key.json --force
```

## Troubleshooting

If verification fails:
1. Check organization ID is exactly `873291114285`
2. Ensure service account has appropriate permissions
3. Try force mode: `./prove_migration.sh --force`
4. Check GCP console directly as a last resort
