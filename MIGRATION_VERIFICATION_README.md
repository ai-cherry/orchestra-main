# GCP Migration Verification Suite

This suite provides tools to verify that the migration of the `cherry-ai-project` project to organization `873291114285` happened successfully and that all required infrastructure components (Vertex workstations, Google Cloud IDE, etc.) are properly set up.

## Available Verification Scripts

### 1. `verify_migration.sh` (Real Verification)

This script performs actual verification of the migration by connecting to GCP and checking:

- Whether the project is correctly in organization `873291114285`
- The existence and configuration of Vertex workstations with GPU support
- The presence of Google Cloud IDE instances
- Whether required services like Vertex AI, AlloyDB, and Redis are properly configured

It requires proper GCP authentication with a service account key that has sufficient permissions.

#### Usage:

```bash
# Make the script executable
chmod +x verify_migration.sh

# Run the verification
./verify_migration.sh
```

The script will prompt you to enter the service account key if needed, and will guide you through the verification process.

### 2. `simulate_verification.sh` (For Testing/Demonstration)

This script simulates what successful verification looks like, without actually connecting to GCP. It's useful for:

- Understanding what evidence to expect when migration is successful
- Testing the output format without requiring GCP credentials
- Demonstrating the verification process to stakeholders

#### Usage:

```bash
# Make the script executable
chmod +x simulate_verification.sh

# Run the simulation
./simulate_verification.sh
```

The simulation produces a `migration_verification_evidence.txt` file identical to what would be produced by the real verification script when a successful migration is detected.

## Evidence Collection

Both scripts collect evidence in the `migration_verification_evidence.txt` file, which includes:

1. **Organization Status**: Confirms the project is in the correct organization (primary evidence)
2. **Workstation Clusters**: Number and details of found clusters
3. **Workstation Configurations**: Number and details of workstation configs
4. **GPU Configuration**: Verification of NVIDIA T4 GPUs (quantity: 2)
5. **API Status**: Whether Vertex AI API is enabled
6. **Database Services**: AlloyDB and Redis instance status

## Interpreting Results

The verification has three possible outcomes:

1. **SUCCESS**: Migration complete with all infrastructure properly configured
   - Project is in organization `873291114285`
   - Workstation clusters and configurations found with GPUs
   - All required services enabled

2. **PARTIAL**: Organization migration successful but infrastructure incomplete
   - Project is in organization `873291114285`
   - Some infrastructure components missing or misconfigured

3. **FAILED**: Critical verification failed
   - Project is not in organization `873291114285`
   - Migration appears to have failed or is incomplete

## Security Notes

- The verification script handles service account keys securely by:
  - Setting permissions to 600 (read/write for owner only)
  - Offering to remove the key file after verification completes
  - Not logging sensitive key material

## Troubleshooting

If verification fails:

1. Check that you have proper service account credentials
2. Verify that you're using the correct organization ID (`873291114285`)
3. Ensure the service account has sufficient permissions
4. Review the migration steps in `exact_migration_steps.sh` to verify all steps were completed

## Complete Verification Checklist

A successful migration should show:

- [x] Project in organization `873291114285`
- [x] Workstation cluster "ai-development" exists
- [x] Workstation configuration "ai-dev-config" exists 
- [x] GPU configuration with NVIDIA T4 (count: 2)
- [x] Vertex AI API enabled
- [x] AlloyDB cluster "agent-storage" exists
- [x] Redis instance "agent-memory" exists
