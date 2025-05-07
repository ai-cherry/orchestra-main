# GCP Authentication Issue Diagnosis

## Issue Summary

The service account key file at `/tmp/vertex-agent-key.json` appears to have an invalid signature, preventing proper authentication with Google Cloud. This issue blocks access to Firestore and other GCP services required for the memory management system.

## Detailed Analysis

1. **Service Account Key Format**: 
   - The key file is properly formatted JSON and contains all required fields
   - However, the RSA key appears to be malformed, causing signature validation failures

2. **Signature Validation Error**:
   - Error message: `invalid_grant: Invalid JWT Signature`
   - RSA library warning: `You have provided a malformed keyfile. Either the exponents or the coefficient are incorrect.`

3. **Tests Performed**:
   - Successfully parsed the key file and extracted service account details
   - Failed to authenticate using both direct credentials object and environment variable method
   - Multiple authentication attempts all resulted in the same JWT signature error

## Required Information to Fix the Issue

1. **New Service Account Key**:
   - A new service account key file needs to be generated for the `vertex-agent@cherry-ai-project.iam.gserviceaccount.com` account
   - The key should be in JSON format with proper RSA key values

2. **Proper IAM Permissions**:
   - The service account needs Firestore access permissions:
     - `roles/datastore.user` at minimum
     - `roles/datastore.owner` for full access

3. **Project Configuration**:
   - Verify Firestore API is enabled in the GCP project `cherry-ai-project`

## Recommended Steps

1. **Generate New Service Account Key**:
   ```bash
   # Via Google Cloud Console:
   # 1. Navigate to IAM & Admin > Service Accounts
   # 2. Find the vertex-agent service account
   # 3. Create a new key (JSON format)
   # 4. Download and save to a secure location

   # Or via gcloud CLI (if available):
   gcloud iam service-accounts keys create new-key.json \
     --iam-account=vertex-agent@cherry-ai-project.iam.gserviceaccount.com
   ```

2. **Install the New Key**:
   ```bash
   # Replace the existing key file
   cp /path/to/new-key.json /tmp/vertex-agent-key.json
   
   # Verify file permissions
   chmod 600 /tmp/vertex-agent-key.json
   ```

3. **Verify Authentication**:
   ```bash
   # Test authentication with the new key
   export GOOGLE_APPLICATION_CREDENTIALS=/tmp/vertex-agent-key.json
   export GCP_PROJECT_ID=cherry-ai-project
   python test_gcp_auth.py
   ```

## Next Steps After Authentication Fix

Once authentication is working:

1. Run the connection tests:
   ```bash
   ./run_connection_tests.sh --firestore-only --verbose
   ```

2. Provision required infrastructure:
   ```bash
   cd /workspaces/orchestra-main/infra
   terraform init
   terraform workspace select dev
   terraform plan -var="env=dev"
   terraform apply -var="env=dev"
   ```

3. Run integration tests:
   ```bash
   export RUN_INTEGRATION_TESTS=true
   ./run_integration_tests.sh
   ```
