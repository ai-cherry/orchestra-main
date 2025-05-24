# Zero Bullshit Migration Verification

This repository contains a suite of tools to definitively prove the GCP project migration happened, with focus on Vertex workstations, GPUs, and database connections.

## Execution Plan

### 1. Direct Verification (Takes 10 seconds)

```bash
# Most direct proof possible
gcloud projects describe cherry-ai-project --format="value(name,parent.id)"

# Expected output: cherry-ai-project organizations/873291114285
```

If this shows the correct organization, the migration succeeded. Continue to verify infrastructure:

```bash
# Verify GPU workstations
gcloud workstations configs describe ai-dev-config \
  --cluster=ai-development \
  --region=us-west4 \
  --format="json(container.guestAccelerators)"

# Verify database connections
gcloud redis instances describe agent-memory --region=us-west4 --format="value(state)"
gcloud alloydb clusters describe agent-storage --region=us-west4 --format="value(state)"
```

### 2. Nuclear Verification (Takes 30-60 seconds)

For complete verification with one command:

```bash
# Make executable and run
chmod +x definitive_migration_verify.sh
./definitive_migration_verify.sh
```

This provides comprehensive verification of all migration aspects and creates an evidence file.

### 3. Force Migration + Verification (Takes 1-5 minutes)

If verification fails or you want to force migration:

```bash
# Make executable and run
chmod +x force_migration_nuclear.sh
./force_migration_nuclear.sh
```

This script:

1. Authenticates with your key
2. Forces migration with full debug logging
3. Performs immediate post-migration checks
4. Applies critical fixes if needed
5. Provides final atomic verification

## Interpreting Results

Look for these critical indicators:

1. **Primary Success Indicator**: `Project cherry-ai-project in organization 873291114285`
2. **GPU Verification**: `2x NVIDIA T4 GPUs active in us-west4`
3. **Database Verification**: `Redis/AlloyDB connections established`

Example successful output:

```
===== CRITICAL VERIFICATION RESULTS =====
✅ Project cherry-ai-project in organization 873291114285
✅ 2x NVIDIA T4 GPUs active in us-west4
✅ Redis/AlloyDB connections established
```

## Troubleshooting Common Issues

Issues are rare but might include:

1. **Permission Denied**

   - Fix: `force_migration_nuclear.sh` recreates service account key

2. **Billing Project Error**

   - Fix: Script automatically attempts billing project linkage fix

3. **Organization Policy Error**
   - Fix: Script handles org policy exceptions automatically

## Critical Command Reference

All verification has been reduced to these critical commands:

```bash
# Organization verification (PRIMARY)
gcloud projects describe cherry-ai-project --format="value(parent.id)"

# Force migration
gcloud beta projects move cherry-ai-project \
  --organization=873291114285 \
  --billing-project=cherry-ai-project \
  --verbosity=debug \
  --log-http

# Service account roles
gcloud organizations get-iam-policy 873291114285 \
  --filter="bindings.members:vertex-agent@cherry-ai-project.iam.gserviceaccount.com"
```

## Security

All scripts securely handle credentials:

1. Key file permissions set to 600
2. Option to securely delete keys after verification
3. Evidence files for audit trail

## Evidence Collection

Verification evidence is saved to:

- `definitive_migration_evidence.txt` - Comprehensive evidence
- `migration_debug.log` - Migration command debug output

## Next Steps

After verification, check GCP Console to visually confirm:

1. Project appears under the correct organization
2. Workstations show correct GPU configuration
3. Database services show correct status
