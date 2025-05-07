# GCP Workspace Migration Guide

This guide provides instructions for archiving your workspace and migrating it to a new Google Cloud environment.

## Overview

The provided scripts facilitate:

1. **Archiving** all source code, notebooks, and configuration files into a tarball
2. **Uploading** the archive to a Google Cloud Storage bucket
3. **Restoring** the workspace in a new Vertex AI Workbench instance or Google Cloud Workstation

## Prerequisites

- Google Cloud SDK (`gcloud` command-line tool) installed and configured
- Authenticated access to GCP and permissions to write to the target bucket
- Sufficient storage space for the archive creation

## Migration Scripts

Two scripts are provided for the migration process:

1. `gcp_archive_migrate.sh` - Creates an archive of your current workspace and uploads it to GCS
2. `gcp_archive_restore.sh` - Downloads and extracts the archive in a new environment

## Step 1: Archive and Upload

### Usage

Make the script executable and run it:

```bash
chmod +x gcp_archive_migrate.sh
./gcp_archive_migrate.sh
```

### What This Script Does

- Creates a timestamped `.tar.gz` archive of your workspace
- Excludes unnecessary files (`.git`, `__pycache__`, `.env`, etc.)
- Uploads the archive to `gs://agi-baby-cherry-migration/` bucket
- Creates and uploads a metadata JSON file with archive information
- Verifies the upload was successful
- Displays detailed restoration instructions

### Configuration

By default, the script uses:
- Bucket: `gs://agi-baby-cherry-migration/`
- Archive name: `orchestra_migration_[TIMESTAMP].tar.gz`

To customize these settings, modify the variables at the top of the script:

```bash
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
ARCHIVE_NAME="orchestra_migration_${TIMESTAMP}.tar.gz"
GCS_BUCKET="gs://agi-baby-cherry-migration"
```

## Step 2: Restore in New Environment

### Usage

In your new Vertex AI Workbench instance or Google Cloud Workstation:

1. Download both scripts:

```bash
gsutil cp gs://agi-baby-cherry-migration/gcp_archive_migrate.sh .
gsutil cp gs://agi-baby-cherry-migration/gcp_archive_restore.sh .
chmod +x gcp_archive_restore.sh
```

2. Run the restore script with required parameters:

```bash
./gcp_archive_restore.sh --bucket gs://agi-baby-cherry-migration --archive orchestra_migration_20250501_123456.tar.gz
```

Or use the short options:

```bash
./gcp_archive_restore.sh -b gs://agi-baby-cherry-migration -a orchestra_migration_20250501_123456.tar.gz
```

3. Optionally specify a destination directory:

```bash
./gcp_archive_restore.sh -b gs://agi-baby-cherry-migration -a orchestra_migration_20250501_123456.tar.gz -d /path/to/destination
```

### Command-Line Options

```
Usage: ./gcp_archive_restore.sh [options]

Options:
  -b, --bucket       GCS bucket URL (required, e.g. gs://agi-baby-cherry-migration)
  -a, --archive      Archive filename (required, e.g. orchestra_migration_20250501_123456.tar.gz)
  -d, --directory    Destination directory (optional, defaults to current directory)
  -h, --help         Show this help message
```

### What This Script Does

- Downloads the specified archive from GCS
- Downloads the associated metadata file (if available)
- Extracts the archive
- Sets correct permissions on shell scripts
- Verifies the restoration was successful

## Common Use Cases

### 1. Migrating to a New Vertex AI Workbench Instance

```bash
# On original instance
./gcp_archive_migrate.sh

# Note the archive name from the output, e.g. orchestra_migration_20250501_123456.tar.gz

# On new instance
gcloud auth login
gsutil cp gs://agi-baby-cherry-migration/gcp_archive_restore.sh .
chmod +x gcp_archive_restore.sh
./gcp_archive_restore.sh -b gs://agi-baby-cherry-migration -a orchestra_migration_20250501_123456.tar.gz
```

### 2. Migrating to a Google Cloud Workstation

```bash
# Upload both scripts to the GCS bucket from your original environment
gsutil cp gcp_archive_migrate.sh gs://agi-baby-cherry-migration/
gsutil cp gcp_archive_restore.sh gs://agi-baby-cherry-migration/

# On original environment
./gcp_archive_migrate.sh

# On Cloud Workstation
gsutil cp gs://agi-baby-cherry-migration/gcp_archive_restore.sh .
chmod +x gcp_archive_restore.sh
./gcp_archive_restore.sh -b gs://agi-baby-cherry-migration -a orchestra_migration_20250501_123456.tar.gz
```

### 3. Finding Available Archives

To list available archives in the bucket:

```bash
gsutil ls gs://agi-baby-cherry-migration/orchestra_migration_*.tar.gz
```

To list available metadata files:

```bash
gsutil ls gs://agi-baby-cherry-migration/migration_metadata_*.json
```

## Troubleshooting

### Authentication Issues

If you encounter authentication errors:

```bash
# Login with your Google account
gcloud auth login

# Or set up application default credentials
gcloud auth application-default login
```

### Permission Issues

If you don't have permission to access the bucket:

```bash
# Check if you have the required permissions
gsutil iam get gs://agi-baby-cherry-migration

# Request access from your administrator or create a new bucket where you have permissions
```

### Disk Space Issues

If you run out of disk space during archive creation:

1. Free up space by removing unnecessary files
2. Modify the exclude patterns in `gcp_archive_migrate.sh` to exclude more directories

### Extraction Issues

If archive extraction fails:

1. Check if the archive was downloaded completely
2. Verify you have write permissions in the destination directory
3. Ensure you have sufficient disk space

## Customization

### Excluding Additional Files

To exclude additional files/directories from the archive, modify the `EXCLUDE_PATTERNS` array in `gcp_archive_migrate.sh`:

```bash
EXCLUDE_PATTERNS=(
  "--exclude=.git"
  "--exclude=__pycache__"
  "--exclude=*.pyc"
  "--exclude=venv"
  "--exclude=.venv"
  "--exclude=node_modules"
  "--exclude=.env"
  "--exclude=*.log"
  "--exclude=*.tar.gz"
  "--exclude=your_additional_pattern"
)
```

### Using a Different Bucket

To use a different GCS bucket, modify the `GCS_BUCKET` variable in both scripts.

## Security Considerations

- The scripts don't handle sensitive data by default but be careful if your codebase contains credentials or tokens
- Consider excluding sensitive files from the archive
- Ensure the GCS bucket has appropriate access controls
- Both scripts check for proper authentication before attempting operations

## Next Steps After Migration

After restoring your workspace:

1. Install any required dependencies
2. Reconfigure environment variables (especially those excluded in `.env` files)
3. Verify that everything works as expected in the new environment

---

For additional assistance or to report issues, please contact your system administrator or cloud support team.
