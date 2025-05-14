# Organization Policy Manager for GCP Migration

This document explains how to use the Organization Policy Manager tools to fix the policy constraints that are blocking AI Orchestra's migration to Google Cloud Platform.

## Issue: Organization Policy Restrictions

The following organization policies are restricting your GCP migration:

1. `iam.allowedPolicyMemberDomains` - Restricting what domains can be given access (blocking public access)
2. `run.requireInvokerIam` - Requiring authentication to access Cloud Run services
3. `vertexai.allowedModels` - Restricting which Vertex AI models can be accessed

## Solution Options

We've provided two solutions to fix these organization policy constraints:

1. **GitHub Action Workflow** - For teams who prefer CI/CD-based management
2. **Python Command-Line Script** - For local execution or debugging

Both solutions use the same org-policy-manager service account (`org-policy-manager-sa@cherry-ai-project.iam.gserviceaccount.com`) which has the necessary permissions to modify organization policies.

## Option 1: GitHub Action Workflow

### Setup Instructions

1. **Ensure the GitHub Secret is Set Up**:
   - The GitHub secret `GCP_ORGANIZATION_POLICY_JSON` should be set at the organization level (https://github.com/ai-cherry)
   - This secret contains the service account key for `org-policy-manager-sa@cherry-ai-project.iam.gserviceaccount.com`

2. **Create the Workflow File**:
   - We've already created the workflow file at `.github/workflows/apply_org_policies.yml`
   - Alternatively, you can use the template at `gcp_migration/apply_org_policies_github_action.yml`

3. **Run the Workflow**:
   - Go to the "Actions" tab in your GitHub repository
   - Select the "Apply Organization Policies for GCP Migration" workflow
   - Click "Run workflow"
   - Input parameters as needed (or accept defaults)
   - Click "Run workflow" to start the action

### What This Workflow Does

1. Authenticates with GCP using the organization policy manager service account
2. Creates policy files to modify the restrictive organization policies
3. Applies these policy changes to your project
4. Updates the specified Cloud Run service to allow unauthenticated access
5. Verifies the changes by checking the policy status
6. Generates a report with the results

## Option 2: Python Command-Line Script

### Setup Instructions

1. **Create a Service Account Key File**:
   - Obtain the service account JSON key for `org-policy-manager-sa@cherry-ai-project.iam.gserviceaccount.com`
   - Store it securely on your local machine

2. **Run the Python Script**:
   ```bash
   # Option 1: Provide the JSON content directly as an environment variable
   export GCP_ORGANIZATION_POLICY_JSON='{"type":"service_account",...}'
   ./gcp_migration/use_org_policy_manager.py
   
   # Option 2: Provide path to the key file
   ./gcp_migration/use_org_policy_manager.py --json-secret=/path/to/keyfile.json
   
   # Specify custom service name and region (optional)
   ./gcp_migration/use_org_policy_manager.py --json-secret=/path/to/keyfile.json \
     --service-name=my-service --region=us-west1
   ```

### What This Script Does

1. Sets up authentication using the provided service account key
2. Checks your current organization policies
3. Creates and applies organization policy overrides
4. Updates the Cloud Run service to allow unauthenticated access
5. Tests the service to verify the changes

## Verification

After applying the organization policy changes, verify that:

1. **Cloud Run Access**: 
   ```bash
   curl -s https://ai-orchestra-minimal-yshgcxa7ta-uc.a.run.app/health
   ```
   This should return a successful response without authentication.

2. **Vertex AI Access**:
   ```bash
   python3 gcp_migration/test_vertex_ai.py
   ```
   This should successfully connect to Vertex AI services.

3. **Organization Policies**:
   ```bash
   gcloud org-policies list --project=cherry-ai-project
   ```
   The policies should now be set correctly.

## Policy Details

The following policies are modified:

### 1. run.requireInvokerIam

```yaml
name: projects/cherry-ai-project/policies/run.requireInvokerIam
spec:
  rules:
  - enforce: false
```

This allows Cloud Run services to be publicly accessible without requiring authentication.

### 2. vertexai.allowedModels

```yaml
name: projects/cherry-ai-project/policies/vertexai.allowedModels
spec:
  rules:
  - values:
      allowedValues:
      - resource://aiplatform.googleapis.com/projects/cherry-ai-project/locations/*
```

This allows access to all Vertex AI models within your project.

### 3. iam.allowedPolicyMemberDomains

```yaml
name: projects/cherry-ai-project/policies/iam.allowedPolicyMemberDomains
spec:
  rules:
  - values:
      allowedValues:
      - "domain:cherry-ai.me"
      - "allUsers"
      - "allAuthenticatedUsers"
```

This allows granting public access (`allUsers`) to resources like Cloud Run services.

## Troubleshooting

1. **Permission denied errors**:
   - Ensure the service account has the necessary permissions
   - Check that the key is correct and valid

2. **Policy not updated**:
   - Some policy changes may take time to propagate
   - Try running the script or workflow again after a few minutes

3. **Service still requires authentication**:
   - Run the Cloud Run service update command directly:
     ```
     gcloud run services update ai-orchestra-minimal --region=us-central1 --allow-unauthenticated
     ```

## Next Steps

After fixing the organization policy constraints:

1. Run the complete migration script to deploy all services
2. Verify that all services are working correctly
3. Complete any remaining migration tasks