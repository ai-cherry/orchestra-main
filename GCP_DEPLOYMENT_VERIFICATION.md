# GCP Deployment Verification

This document outlines the steps to verify that the GCP resources for the AI Orchestra project have been successfully provisioned, configured, and tested in a production environment.

## Prerequisites

Before proceeding with the verification, ensure that:

1. You have authenticated with GCP using the correct service account
2. The GCP configuration is set up correctly (see [GCP_CONFIGURATION_README.md](GCP_CONFIGURATION_README.md))
3. The gcloud CLI is installed and configured

## Automated Verification

The `test_gcp_deployment.sh` script automates the verification process. It checks:

- GCP API access
- Cloud Run service
- Cloud Storage buckets
- Firestore database
- Vertex AI
- Secret Manager
- IAM permissions

To run the automated verification:

```bash
./test_gcp_deployment.sh
```

Review the output to ensure all resources have been successfully provisioned and configured.

## Manual Verification

If you prefer to verify the deployment manually, follow these steps:

### 1. Verify GCP Configuration

```bash
# Verify gcloud configuration
gcloud config list

# Expected output:
# account = scoobyjava@cherry-ai.me
# project = cherry-ai-project
# ...
```

### 2. Verify Cloud Run Service

```bash
# List Cloud Run services
gcloud run services list --region=us-central1

# Describe the service
gcloud run services describe orchestra-api --region=us-central1

# Test the service
SERVICE_URL=$(gcloud run services describe orchestra-api --region=us-central1 --format="value(status.url)")
curl -v $SERVICE_URL
```

### 3. Verify Cloud Storage Buckets

```bash
# List Cloud Storage buckets
gcloud storage ls

# List objects in a bucket
gcloud storage ls gs://cherry-ai-project-data
```

### 4. Verify Firestore Database

```bash
# Describe Firestore database
gcloud firestore databases describe --project=cherry-ai-project

# List Firestore collections
gcloud firestore indexes composite list --project=cherry-ai-project
```

### 5. Verify Vertex AI

```bash
# List Vertex AI models
gcloud ai models list --region=us-central1 --project=cherry-ai-project

# List Vertex AI endpoints
gcloud ai endpoints list --region=us-central1 --project=cherry-ai-project
```

### 6. Verify Secret Manager

```bash
# List secrets
gcloud secrets list --project=cherry-ai-project

# Verify access to a secret
gcloud secrets versions access latest --secret=api-key --project=cherry-ai-project
```

### 7. Verify IAM Permissions

```bash
# Get IAM policy
gcloud projects get-iam-policy cherry-ai-project

# Verify service account permissions
gcloud projects get-iam-policy cherry-ai-project --flatten="bindings[].members" --filter="bindings.members:serviceAccount:orchestra-api-sa@cherry-ai-project.iam.gserviceaccount.com"
```

## Production Environment Verification

To verify that the deployment is working correctly in a production environment:

### 1. Monitor Cloud Run Service

```bash
# View Cloud Run service logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=orchestra-api" --project=cherry-ai-project --limit=10
```

### 2. Check Error Reporting

```bash
# View Error Reporting errors
gcloud error-reporting events list --project=cherry-ai-project
```

### 3. Monitor Performance

```bash
# View Cloud Monitoring metrics
gcloud monitoring metrics list --project=cherry-ai-project | grep cloud_run
```

### 4. Test API Endpoints

```bash
# Test API endpoints
curl -v $SERVICE_URL/api/health
curl -v $SERVICE_URL/api/version
```

### 5. Verify Data Flow

```bash
# Check Firestore data
gcloud firestore documents list --collection=users --project=cherry-ai-project

# Check Cloud Storage data
gcloud storage ls gs://cherry-ai-project-data
```

## Troubleshooting

If you encounter issues during verification:

1. Check the Cloud Run service logs:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=orchestra-api" --project=cherry-ai-project --limit=10
   ```

2. Verify IAM permissions:
   ```bash
   gcloud projects get-iam-policy cherry-ai-project
   ```

3. Check the service account:
   ```bash
   gcloud iam service-accounts describe orchestra-api-sa@cherry-ai-project.iam.gserviceaccount.com
   ```

4. Verify the Cloud Run service configuration:
   ```bash
   gcloud run services describe orchestra-api --region=us-central1
   ```

5. Check the Firestore database:
   ```bash
   gcloud firestore databases describe --project=cherry-ai-project
   ```

## Deployment Evidence

To document the successful deployment, collect the following evidence:

1. Screenshots of the Cloud Run service in the GCP Console
2. Output of the `test_gcp_deployment.sh` script
3. Logs showing successful API requests
4. Performance metrics from Cloud Monitoring
5. IAM permissions showing correct service account configuration

Store this evidence in a deployment documentation repository for future reference.

## Conclusion

By following the steps in this document, you can verify that the GCP resources for the AI Orchestra project have been successfully provisioned, configured, and tested in a production environment. This ensures that the application is ready for use and meets the requirements for a production deployment.