# Vertex Workbench Data Synchronization Guide

This guide provides detailed instructions for automating data transfer between Vertex AI Workbench instances and Google Cloud Storage. 

## Overview

The Vertex Workbench Data Sync solution offers:

- **Bidirectional synchronization** between Jupyter environments and GCS buckets
- **Incremental data transfer** using `gsutil rsync` for efficient operations
- **Data integrity validation** with checksums to ensure accurate transfers
- **Automated validation** to detect and report inconsistencies
- **CI/CD integration** for automated synchronization during deployments

## Components

The solution consists of the following components:

1. **vertex_data_sync.sh** - Core script for manual data synchronization
2. **data_sync_ci_cd.sh** - Script for CI/CD pipeline integration
3. **cloudbuild_data_sync.yaml** - Cloud Build configuration for automated synchronization
4. **vertex_workbench_config.tf** - Terraform configuration for Vertex AI Workbench setup

## Getting Started

### Prerequisites

- Google Cloud SDK (`gcloud` & `gsutil`) installed and configured
- Authenticated GCP account with appropriate permissions
- GCS bucket for migration data storage
- Vertex AI Workbench instance

### Installation

#### Option 1: Manual Installation

1. Copy the scripts to your Vertex AI Workbench instance:

```bash
# Make the script executable
chmod +x vertex_data_sync.sh
```

2. Test the installation:

```bash
./vertex_data_sync.sh --help
```

#### Option 2: Terraform Deployment

1. Update the Terraform variables in `vertex_workbench_config.tf`:

```hcl
variable "project_id" {
  description = "GCP Project ID"
  type        = string
  # Set your project ID here or via terraform.tfvars
}
```

2. Deploy using Terraform:

```bash
terraform init
terraform plan
terraform apply
```

The Terraform configuration will create a Vertex AI Workbench instance with the data sync scripts pre-installed and configured to run automatically.

## Usage

### Manual Data Synchronization

#### Push local changes to GCS

```bash
./vertex_data_sync.sh --push
```

#### Pull data from GCS to local environment

```bash
./vertex_data_sync.sh --pull
```

#### Verify data integrity only (no transfer)

```bash
./vertex_data_sync.sh --verify-only
```

#### Use a different bucket

```bash
./vertex_data_sync.sh --push --bucket my-custom-bucket
```

### CI/CD Integration

#### Using with Cloud Build

1. Configure Cloud Build trigger to use the `cloudbuild_data_sync.yaml` file.

2. Set variables for your environment:

```yaml
substitutions:
  _BUCKET: "your-bucket-name"
  _ENVIRONMENT: "dev"  # dev, test, prod
  _DIRECTION: "push"   # push or pull
  _NOTIFICATION_EMAIL: "your-email@example.com"
  _SLACK_WEBHOOK: "https://hooks.slack.com/services/..."
```

3. Trigger a build manually or via code changes:

```bash
gcloud builds submit --config=cloudbuild_data_sync.yaml .
```

#### Using in custom CI/CD pipelines

The `data_sync_ci_cd.sh` script can be integrated into any CI/CD pipeline:

```bash
./data_sync_ci_cd.sh --environment prod --direction push
```

## Data Integrity Verification

All synchronization operations include data integrity validation using MD5 checksums:

1. Before transfer, checksums are calculated for all files
2. After transfer, checksums are compared to verify data integrity
3. Any differences are reported with detailed information
4. Notifications are sent via email or Slack if configured

### Manual verification

To manually verify data integrity:

```bash
./vertex_data_sync.sh --verify-only
```

## Best Practices

1. **Regular Synchronization**: Set up a cron job for daily synchronization:

```
# Example cron entry for daily sync at 2 AM
0 2 * * * /home/jupyter/vertex_data_sync.sh --push
```

2. **Environment Separation**: Use environment-specific directories for different stages:

```bash
./data_sync_ci_cd.sh --environment dev --direction push
./data_sync_ci_cd.sh --environment test --direction push
./data_sync_ci_cd.sh --environment prod --direction push
```

3. **Validation Reports**: Review validation reports regularly to ensure data integrity

4. **Notification Integration**: Configure email or Slack notifications for critical operations

## Troubleshooting

### Common Issues

#### Authentication Problems

```
ERROR: Not authenticated with gcloud
```

Resolution:
```bash
gcloud auth login
```

#### Bucket Access Issues

```
ERROR: Bucket not accessible
```

Resolution:
- Verify bucket exists and is correctly named
- Check permissions for the authenticated account
- Ensure storage access APIs are enabled

#### Checksum Mismatch

```
WARNING: Data integrity issues detected
```

Resolution:
- Review the diff file to identify specific files with issues
- Manually compare files to resolve discrepancies
- Re-synchronize with the correct direction

## Advanced Configuration

### Custom Exclude Patterns

To modify which files are excluded from synchronization, edit the `EXCLUDE_PATTERNS` array in the scripts:

```bash
EXCLUDE_PATTERNS=(".git" "__pycache__" "*.pyc" "venv" ".venv" "node_modules" ".env" "*.log" "*.tar.gz")
```

### Notification Setup

For email notifications:
```bash
./data_sync_ci_cd.sh --notification-email your-email@example.com
```

For Slack notifications:
```bash
./data_sync_ci_cd.sh --slack-webhook https://hooks.slack.com/services/...
```

## FAQ

### How does this differ from the existing migration scripts?

The original migration scripts (`gcp_archive_migrate.sh` and `gcp_archive_restore.sh`) focused on one-time full migrations using tar archives. This new solution provides:

- Incremental synchronization (only transferring changed files)
- Bidirectional capabilities (push and pull)
- Automated integrity verification
- CI/CD integration
- Multi-environment support

### What if I need to transfer sensitive data?

For sensitive data:
1. Exclude sensitive files using the `EXCLUDE_PATTERNS` configuration
2. Use service accounts with limited permissions
3. Consider client-side encryption before transfer
4. Ensure proper bucket permissions are set

### How can I schedule synchronization?

In a Vertex Workbench instance:
```bash
# Add to crontab
(crontab -l 2>/dev/null || echo "") | { cat; echo "0 2 * * * /home/jupyter/vertex_data_sync.sh --push"; } | crontab -
```

## Support

For issues or questions:
1. Check the logs in `/home/jupyter/logs/` directory
2. Review the status file at `/tmp/data_sync_status.json`
3. Contact your system administrator or cloud support team
