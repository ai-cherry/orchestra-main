# GCP Resources and Gemini Code Assist Integration

This guide explains how to maintain coordination between your Google Cloud resources and your codebase using the provided tools and Gemini Code Assist.

## Overview

Gemini Code Assist doesn't have built-in access to your live Google Cloud resources. However, with the tools provided in this repository, you can:

1. Capture a comprehensive snapshot of your GCP resources
2. Compare your actual cloud resources with your codebase
3. Use these snapshots with Gemini Code Assist to get better recommendations

## The GCP Snapshot Tool

We've created a powerful script called `snapshot_gcp_resources.sh` that captures detailed information about your GCP resources and services. This script:

- Creates a structured directory of JSON files with resource details
- Generates both human-readable summaries and machine-readable data
- Can compare resources to your codebase to identify inconsistencies
- Works with service account credentials in your Codespaces environment

### Usage

Basic usage:

```bash
./snapshot_gcp_resources.sh -p your-gcp-project-id
```

Full options:

```bash
./snapshot_gcp_resources.sh -p your-gcp-project-id -a -c -d /workspaces/orchestra-main -o /workspaces/orchestra-main/.gcp-snapshots
```

Parameters:

- `-p, --project-id`: GCP Project ID (required)
- `-o, --output-dir`: Output directory for snapshots (default: ./gcp_snapshots)
- `-a, --all`: Capture all resources (more comprehensive but slower)
- `-c, --compare`: Compare snapshot with code in specified directory
- `-d, --code-dir`: Directory containing code to compare (default: .)

### Example workflow

1. **Create a baseline snapshot**:
   ```bash
   ./snapshot_gcp_resources.sh -p cherry-ai-project -a -c -o /workspaces/orchestra-main/.gcp-snapshots
   ```

2. **Review the summary**:
   The script generates a `resource_summary.md` file with a high-level overview of your GCP resources.

3. **Check the code comparison**:
   The script creates a `code_comparison.md` file that identifies resources that might not be properly tracked in your code.

## Integrating with Gemini Code Assist

We've already configured Gemini Code Assist to be aware of your codebase structure. Here's how to use the GCP snapshots with it:

1. **Place the snapshots in an indexed location**:
   The Gemini configuration in `.gemini-code-assist.yaml` already includes `/workspaces/orchestra-main` with high priority, so saving snapshots to `.gcp-snapshots` will make them visible to Gemini.

2. **Reference the snapshots in your queries**:
   When asking Gemini for help, explicitly mention the snapshot files. For example:
   
   ```
   Help me create Terraform for a new Cloud Run service similar to our existing ones in .gcp-snapshots/cherry-ai-project_2025-05-11-123456/compute/cloud_run_services.json
   ```

3. **Compare code with actual resources**:
   Ask Gemini to help identify discrepancies:
   
   ```
   Compare our Terraform code in terraform/ with the actual GCP resources in .gcp-snapshots/cherry-ai-project_2025-05-11-123456/ and suggest updates
   ```

## Best Practices for Code-Resource Coordination

To keep your code and cloud resources in sync:

1. **Regular snapshots**: Run the snapshot script periodically (e.g., daily) to keep your local resource information current

2. **Pre-commit checks**: Before making major changes, take a snapshot and verify that your code reflects the current state

3. **Post-deployment verification**: After deploying changes, take a new snapshot to verify that the changes were applied correctly

4. **Resource tagging**: When creating resources, use consistent tagging that corresponds to your code organization

5. **Include snapshots in version control**: Store important snapshots in your repository so they're available to other developers

6. **Update snapshots after significant changes**: When you know resources have changed, take a new snapshot

## Limitations and Considerations

- **Authentication scope**: The snapshot script requires appropriate IAM permissions (viewer access to all relevant resources)
- **Resource freshness**: Snapshots are point-in-time captures and may become outdated
- **Sensitive information**: Snapshots may contain sensitive configuration details; be cautious about sharing them
- **Performance impact**: Comprehensive snapshots with `-a` flag may take several minutes to complete

## Troubleshooting

If you encounter authentication issues:

1. Verify you're authenticated with gcloud:
   ```bash
   gcloud auth list
   ```

2. Ensure your credentials have sufficient permissions:
   ```bash
   gcloud projects get-iam-policy your-project-id
   ```

3. Check that the service account has the necessary roles:
   - roles/viewer
   - roles/iam.securityReviewer
   - roles/compute.viewer
   - roles/storage.objectViewer
   - roles/run.viewer

## Example: Maintaining Cloud Run Services

Here's a typical workflow for ensuring Cloud Run services in your code match what's deployed:

1. Take a snapshot:
   ```bash
   ./snapshot_gcp_resources.sh -p cherry-ai-project
   ```

2. Examine Cloud Run services:
   ```bash
   cat ./gcp_snapshots/cherry-ai-project_*/compute/cloud_run_services.json | jq
   ```

3. Compare with Terraform:
   ```bash
   grep -r "google_cloud_run_service" --include="*.tf" .
   ```

4. Ask Gemini Code Assist to help with any discrepancies:
   ```
   Help me update the Terraform in terraform/cloud_run.tf to match the actual Cloud Run services in our GCP snapshot
   ```

By following this workflow, you can ensure your infrastructure-as-code accurately reflects your actual cloud resources, even though Gemini doesn't have direct access to your GCP environment.
