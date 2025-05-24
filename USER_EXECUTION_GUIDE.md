# User-Specific Migration Execution Guide

## Where to Run These Commands

All commands in this guide should be run in either:

- **Your Codespaces terminal** (where you're currently working)
- **Google Cloud Shell** (accessible via the GCP Console)

## Preparation Steps

### 1. Ensure Required Permissions for Your Account

For user `scoobyjava@cherry-ai.me`:

```bash
# Grant owner permission on the project
gcloud projects add-iam-policy-binding cherry-ai-project \
  --member="user:scoobyjava@cherry-ai.me" \
  --role="roles/owner"

# Grant project creator permission on the organization
gcloud organizations add-iam-policy-binding 873291114285 \
  --member="user:scoobyjava@cherry-ai.me" \
  --role="roles/resourcemanager.projectCreator"
```

### 2. Configure Default Project

```bash
gcloud config set project cherry-ai-project
```

## Migration Execution

### Option 1: Direct Migration Command

```bash
# Execute the simple migration command
gcloud beta projects move cherry-ai-project --organization 873291114285
```

### Option 2: Use Our Zero-Bullshit Force Migration Script

```bash
# Grant execute permission
chmod +x force_migration_nuclear.sh

# Run the script
./force_migration_nuclear.sh
```

## Verification Steps

After migration, verify success:

```bash
# Verify project is in the correct organization
gcloud projects describe cherry-ai-project

# The output should show: parent: organizations/873291114285
```

## Post-Migration Tasks

### Update Billing Association

```bash
# Link to appropriate billing account
gcloud beta billing projects link cherry-ai-project \
  --billing-account=$(gcloud beta billing accounts list --format="value(name)")
```

### Visual Verification in Console

1. Go to IAM & Admin > Settings in GCP Console
2. The "Organization" field should show "cherry-ai.me"

## Creating a Master Service Account (Organization-Wide Access)

Google Cloud doesn't offer a true "master API key" for organizations, but you can create a service account with broad permissions:

```bash
# 1. Create a new service account
gcloud iam service-accounts create org-master-sa \
  --display-name="Organization Master Service Account"

# 2. Grant it organization-level permissions
gcloud organizations add-iam-policy-binding 873291114285 \
  --member="serviceAccount:org-master-sa@cherry-ai-project.iam.gserviceaccount.com" \
  --role="roles/resourcemanager.organizationAdmin"

# 3. Grant additional needed roles (examples)
gcloud organizations add-iam-policy-binding 873291114285 \
  --member="serviceAccount:org-master-sa@cherry-ai-project.iam.gserviceaccount.com" \
  --role="roles/billing.admin"

gcloud organizations add-iam-policy-binding 873291114285 \
  --member="serviceAccount:org-master-sa@cherry-ai-project.iam.gserviceaccount.com" \
  --role="roles/iam.securityAdmin"

# 4. Create a key for this service account
gcloud iam service-accounts keys create org-master-key.json \
  --iam-account=org-master-sa@cherry-ai-project.iam.gserviceaccount.com
```

### Using the Master Service Account

```bash
# Authenticate with the master service account
gcloud auth activate-service-account --key-file=org-master-key.json

# Now you can run commands with organization-wide permissions
gcloud organizations get-iam-policy 873291114285
```

## Troubleshooting Migration Issues

If the migration fails with permission errors:

```bash
# Wait for IAM propagation (important!)
echo "Waiting for IAM propagation..." && sleep 300

# Retry with force option
gcloud beta projects move cherry-ai-project \
  --organization=873291114285 \
  --billing-project=cherry-ai-project \
  --quiet
```

If billing errors occur:

```bash
# Fix billing project linkage
gcloud beta billing projects link cherry-ai-project \
  --billing-account=$(gcloud beta billing accounts list --format="value(name)")
```

## Security Best Practices

For the master service account:

1. Store the key file securely (chmod 600)
2. Consider rotating the key regularly
3. Limit access to only necessary principals
4. Consider using Workload Identity Federation instead of keys where possible
