# Creating a Least-Privilege GCP Service Account

This guide provides step-by-step instructions for creating a secure, least-privilege service account for the Orchestrator system to authenticate with Google Cloud Platform services.

## Why Use a Dedicated Service Account?

When deploying applications that interact with GCP services, it's a security best practice to:

1. Use a dedicated service account with only the necessary permissions (principle of least privilege)
2. Avoid using personal accounts or overly-permissive accounts like Owner or Editor
3. Create separate service accounts for different environments (development, staging, production)

## Prerequisites

- Google Cloud Platform account with administrative access to your project
- `gcloud` CLI installed and configured (optional, you can also use the GCP Console)

## Step 1: Create the Service Account

### Using the GCP Console

1. Navigate to the [IAM & Admin > Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts) page in the GCP Console
2. Select your project
3. Click **CREATE SERVICE ACCOUNT**
4. Enter the following details:
   - **Service account name**: `orchestrator-runtime`
   - **Service account ID**: `orchestrator-runtime` (auto-generated)
   - **Description**: "Least-privilege service account for the Orchestrator application runtime"
5. Click **CREATE AND CONTINUE**

### Using gcloud CLI

```bash
# Set your project ID
export PROJECT_ID=your-project-id

# Create the service account
gcloud iam service-accounts create orchestrator-runtime \
    --description="Least-privilege service account for the Orchestrator application runtime" \
    --display-name="Orchestrator Runtime"
```

## Step 2: Assign Required Roles

Assign only the necessary roles based on which GCP services your Orchestrator instance needs to access. Here are common roles needed:

### Using the GCP Console

1. On the Service Accounts page, click on the newly created service account
2. Click on the **PERMISSIONS** tab
3. Click **GRANT ACCESS**
4. Add each required role:

### Using gcloud CLI

```bash
# For Firestore access
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:orchestrator-runtime@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/datastore.user"

# For Redis (Memorystore) access (if needed)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:orchestrator-runtime@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/redis.editor"

# For Secret Manager access
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:orchestrator-runtime@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# For Vertex AI access (if needed)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:orchestrator-runtime@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# For Pub/Sub (if needed)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:orchestrator-runtime@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/pubsub.publisher"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:orchestrator-runtime@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/pubsub.subscriber"
```

## Step 3: Create a Service Account Key

**Note**: While service account keys are convenient, they should be treated as sensitive credentials. For production, consider using [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation) or other keyless methods when possible.

### Using the GCP Console

1. On the Service Accounts page, click on the service account
2. Click on the **KEYS** tab
3. Click **ADD KEY** > **Create new key**
4. Select **JSON** format
5. Click **CREATE**
6. The key file will be automatically downloaded to your computer

### Using gcloud CLI

```bash
gcloud iam service-accounts keys create orchestrator-key.json \
    --iam-account=orchestrator-runtime@$PROJECT_ID.iam.gserviceaccount.com
```

## Step 4: Configure Orchestrator to Use the Service Account

You can use the service account with Orchestrator in one of two ways:

### Option 1: Use the Service Account JSON Content (Recommended for Codespaces/Cloud Run)

1. Open the downloaded JSON key file
2. Copy the entire content
3. Set the `GCP_SA_KEY_JSON` environment variable in your `.env` file:

```
GCP_PROJECT_ID=your-project-id
GCP_SA_KEY_JSON={"type":"service_account","project_id":"...","private_key_id":"...",...}
```

For Cloud Run or other secure environments, set this as a secret environment variable.

### Option 2: Use the Service Account Key File

1. Save the key file to a secure location
2. Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable in your `.env` file:

```
GCP_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/orchestrator-key.json
```

## Step 5: Test the Configuration

Run the integration tests to verify that the service account is working correctly:

```bash
# Run integration tests for GCP authentication
pytest tests/integration/test_gcp_auth.py -v
```

## Security Best Practices

1. **Key Rotation**: Regularly rotate service account keys (at least every 90 days)
2. **Access Review**: Periodically review the permissions granted to ensure they remain minimal
3. **Key Storage**: Store the key securely (e.g., in a secret manager)
4. **Monitoring**: Enable audit logging for the service account to track its usage
5. **Environment Separation**: Use different service accounts for development, staging, and production

## Troubleshooting

### Permission Issues

If you encounter permission errors:

1. Verify that the service account has the necessary roles for the specific GCP resources it needs to access
2. Check that the key file or JSON content is correctly configured in the environment variables
3. Look at Cloud Audit Logs to see what operations are being denied and what permissions are needed

### Authentication Issues

If authentication fails:

1. Ensure the key file is accessible and readable by the application
2. Check that the environment variables are correctly set
3. Verify that the key has not been revoked or expired
4. Ensure the service account itself has not been disabled

## Cleaning Up

To revoke a key:

```bash
gcloud iam service-accounts keys delete KEY_ID \
    --iam-account=orchestrator-runtime@$PROJECT_ID.iam.gserviceaccount.com
```

To delete the service account when no longer needed:

```bash
gcloud iam service-accounts delete \
    orchestrator-runtime@$PROJECT_ID.iam.gserviceaccount.com
```
