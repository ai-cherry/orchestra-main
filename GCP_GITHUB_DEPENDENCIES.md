# GCP & GitHub Dependencies and Further Enhancements

This document outlines the exact dependencies required for the AI Orchestra deployment system and suggests further enhancements to the non-interactive authentication approach.

## GCP Dependencies

### Required GCP APIs
The following GCP APIs must be enabled in your project:

```bash
# Core APIs
artifactregistry.googleapis.com    # For storing Docker images
run.googleapis.com                 # For Cloud Run services
secretmanager.googleapis.com       # For managing secrets (optional but recommended)
iam.googleapis.com                 # For IAM permissions management
iamcredentials.googleapis.com      # For token creation/verification
```

To enable these APIs, run:
```bash
gcloud services enable artifactregistry.googleapis.com run.googleapis.com secretmanager.googleapis.com iam.googleapis.com iamcredentials.googleapis.com
```

### Service Account Requirements

The service account used for deployment requires these IAM roles:

1. **For Local Deployment (Key-based auth)**:
   - Cloud Run Admin (`roles/run.admin`)
   - Artifact Registry Administrator (`roles/artifactregistry.admin`)
   - Service Account User (`roles/iam.serviceAccountUser`)
   - Secret Manager Accessor (`roles/secretmanager.secretAccessor`) - if using secrets

2. **For GitHub Actions (Workload Identity Federation)**:
   - Same roles as above, plus:
   - Workload Identity User (`roles/iam.workloadIdentityUser`)

### GCP SDK Requirements
- Google Cloud SDK version 363.0.0 or higher
- Required components: `gcloud`, `docker-credential-gcr`

```bash
# Install specific components
gcloud components install docker-credential-gcr
```

### GCP Project Configuration
- A properly configured GCP project with billing enabled
- Artifact Registry repository (created automatically by the deployment script)
- Cloud Run API enabled and properly configured
- VPC Service Controls configuration (if applicable)

## GitHub Dependencies

### GitHub Actions Requirements
- GitHub Actions runner with Docker support
- `actions/checkout@v3` or newer
- `google-github-actions/auth@v1` or newer
- `google-github-actions/setup-gcloud@v1` or newer
- `docker/setup-buildx-action@v2` or newer
- `docker/build-push-action@v4` or newer

### GitHub Repository Settings
- Repository secrets (if not using Workload Identity Federation)
- Branch protection rules (recommended for production deployments)
- Repository permissions for GitHub Actions

### GitHub OIDC Configuration
For Workload Identity Federation:

1. Workload Identity Pool configured in GCP
   ```bash
   # Example command
   gcloud iam workload-identity-pools create "github-pool" \
     --project="PROJECT_ID" \
     --location="global" \
     --display-name="GitHub Actions Pool"
   ```

2. Workload Identity Provider configured for GitHub
   ```bash
   gcloud iam workload-identity-pools providers create-oidc "github-provider" \
     --project="PROJECT_ID" \
     --location="global" \
     --workload-identity-pool="github-pool" \
     --display-name="GitHub Actions Provider" \
     --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
     --issuer-uri="https://token.actions.githubusercontent.com"
   ```

3. Service Account IAM binding
   ```bash
   gcloud iam service-accounts add-iam-policy-binding "SERVICE_ACCOUNT_EMAIL" \
     --project="PROJECT_ID" \
     --role="roles/iam.workloadIdentityUser" \
     --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/REPO_OWNER/REPO_NAME"
   ```

## Further Enhancements

### 1. Key Rotation System
Implement a key rotation system to enhance security:

```bash
# Create a script that:
# 1. Creates a new service account key
# 2. Updates the local key file
# 3. Revokes the old key after a grace period

#!/bin/bash
# Example key rotation script
NEW_KEY_FILE="$HOME/.gcp/new-service-account.json"
CURRENT_KEY_FILE="$HOME/.gcp/service-account.json"

# Create new key
gcloud iam service-accounts keys create "$NEW_KEY_FILE" --iam-account=SERVICE_ACCOUNT_EMAIL

# Test the new key
if gcloud auth activate-service-account --key-file="$NEW_KEY_FILE"; then
  # Backup current key
  cp "$CURRENT_KEY_FILE" "$CURRENT_KEY_FILE.bak"
  # Update the current key
  mv "$NEW_KEY_FILE" "$CURRENT_KEY_FILE"
  echo "Key rotated successfully"
else
  echo "Failed to authenticate with new key"
  exit 1
fi
```

### 2. Secret Manager Integration
Store service account keys in Secret Manager instead of on disk:

```bash
# Store key in Secret Manager
gcloud secrets create service-account-key --data-file=$HOME/.gcp/service-account.json

# Update scripts to retrieve key when needed
gcloud secrets versions access latest --secret=service-account-key > /tmp/sa-key.json
gcloud auth activate-service-account --key-file=/tmp/sa-key.json
rm /tmp/sa-key.json  # Clean up sensitive data
```

### 3. Local Workload Identity Federation
Extend Workload Identity Federation to local development:

```bash
# Create a local credential configuration
gcloud iam workload-identity-pools create-cred-config \
  projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID \
  --output-file=./.gcp/gcp_credential_configuration.json \
  --service-account=SERVICE_ACCOUNT_EMAIL

# Use this configuration in scripts
export GOOGLE_APPLICATION_CREDENTIALS=./.gcp/gcp_credential_configuration.json
```

### 4. Credential Scoping
Implement credential scoping to limit permissions based on specific actions:

```bash
# Create different service accounts for different operations
gcloud iam service-accounts create deploy-account --display-name="Deployment Account"
gcloud iam service-accounts create build-account --display-name="Build Account"

# Assign more granular permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:deploy-account@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:build-account@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.admin"
```

### 5. Enhanced GitHub Actions Security
Implement additional security measures for GitHub Actions:

```yaml
# Add permission boundaries to workflow files
permissions:
  contents: read
  id-token: write  # Required for GCP authentication
  # Explicitly deny other permissions
  actions: none
  checks: none
  deployments: none
  issues: none
  packages: none
  pull-requests: none
  repository-projects: none
  security-events: none
  statuses: none
```

### 6. Centralized Logging & Monitoring
Implement centralized logging for authentication events:

```bash
# Add to authentication scripts
log_auth_event() {
  local event_type=$1
  local status=$2
  local details=$3
  
  # Log to Cloud Logging
  gcloud logging write auth-events \
    "$(jq -n \
      --arg type "$event_type" \
      --arg status "$status" \
      --arg details "$details" \
      --arg user "$(whoami)" \
      --arg host "$(hostname)" \
      '{type: $type, status: $status, details: $details, user: $user, host: $host}')" \
    --payload-type=json
}

# Example usage
log_auth_event "service_account_auth" "success" "Authenticated as service-account@project-id.iam.gserviceaccount.com"
```

### 7. CI/CD Integration Testing
Add an automatic testing framework for authentication methods:

```bash
# Create a test script that verifies all authentication methods work
#!/bin/bash
# Test service account key authentication
echo "Testing service account key authentication..."
if gcloud auth activate-service-account --key-file="$HOME/.gcp/service-account.json"; then
  echo "✅ Service account key authentication works"
else
  echo "❌ Service account key authentication failed"
fi

# Test environment variable authentication
echo "Testing environment variable authentication..."
export GCP_MASTER_SERVICE_JSON=$(cat "$HOME/.gcp/service-account.json")
export GOOGLE_APPLICATION_CREDENTIALS=""  # Clear existing credential path
./deploy.sh --test-auth-only
unset GCP_MASTER_SERVICE_JSON

# Test GitHub Actions workflow
echo "Testing GitHub Actions workflow..."
act -j test-auth -s GITHUB_TOKEN="$GITHUB_TOKEN"
```

### 8. Auto-Update Service
Implement an auto-update service for authentication methods:

```bash
# Create an auto-update script
#!/bin/bash
# Check for new versions of the authentication system
VERSION_URL="https://raw.githubusercontent.com/your-org/orchestra/main/auth-version.txt"
CURRENT_VERSION=$(cat .auth-version)
LATEST_VERSION=$(curl -s "$VERSION_URL")

if [[ "$CURRENT_VERSION" != "$LATEST_VERSION" ]]; then
  echo "New authentication system available: $LATEST_VERSION"
  echo "Current version: $CURRENT_VERSION"
  echo "Updating..."
  
  # Download latest scripts
  curl -s "https://raw.githubusercontent.com/your-org/orchestra/main/setup_service_account.sh" > setup_service_account.sh
  chmod +x setup_service_account.sh
  
  # Update version file
  echo "$LATEST_VERSION" > .auth-version
  
  echo "Updated to version $LATEST_VERSION"
fi
```

By implementing these enhancements, the AI Orchestra deployment system would become more secure, maintainable, and aligned with GCP best practices.
