# GCP Deployment Verification

This document outlines the steps to verify that the AI Orchestra project has been successfully deployed to Google Cloud Platform (GCP) using our consolidated deployment approach.

## Prerequisites

Before proceeding with the verification, ensure that:

1. You have authenticated with GCP using the correct credentials
2. The GCP configuration is set up correctly
3. The gcloud CLI is installed and configured

## Automated Verification

The `deploy.sh` script includes built-in verification steps. When running a deployment:

```bash
./deploy.sh --project your-project-id --region your-region
```

The script automatically performs these verification checks at the end of deployment:
- Health endpoint check
- Service URL validation
- Recent logs examination

For a more comprehensive verification, you can use the included test script:

```bash
./test_cloud_run_deployment.sh
```

This script deploys a test application to Cloud Run, verifies its functionality, and then cleans up the resources.

## Manual Verification

If you prefer to verify the deployment manually, follow these steps:

### 1. Verify GCP Configuration

```bash
# Verify gcloud configuration
gcloud config list

# Expected output should include:
# project = your-project-id
# ...
```

### 2. Verify Cloud Run Service

```bash
# List Cloud Run services
gcloud run services list --region=us-central1

# Describe the service (replace with your service name)
gcloud run services describe orchestra-api --region=us-central1

# Test the service
SERVICE_URL=$(gcloud run services describe orchestra-api --region=us-central1 --format="value(status.url)")
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" $SERVICE_URL/health
```

### 3. Verify Artifact Registry Repository

```bash
# List Artifact Registry repositories
gcloud artifacts repositories list --location=us-central1

# List images in a repository (replace with your repository name)
gcloud artifacts docker images list us-central1-docker.pkg.dev/your-project-id/orchestra-repo
```

### 4. Verify Environment Configuration

```bash
# Check environment variables configured for the service
gcloud run services describe orchestra-api --region=us-central1 --format="yaml(spec.template.spec.containers[0].env)"

# Check secrets configured for the service
gcloud run services describe orchestra-api --region=us-central1 --format="yaml(spec.template.spec.containers[0].envFrom)"
```

### 5. Verify Service Scaling

```bash
# Check service scaling configuration
gcloud run services describe orchestra-api --region=us-central1 --format="yaml(spec.template.spec.containerConcurrency,spec.template.metadata.annotations)"
```

### 6. Verify Service Security

```bash
# Check if the service allows unauthenticated access
gcloud run services describe orchestra-api --region=us-central1 --format="value(status.url,status.address.url)"

# Check IAM policy
gcloud run services get-iam-policy orchestra-api --region=us-central1
```

## Production Environment Verification

To verify that the deployment is working correctly in a production environment:

### 1. Monitor Cloud Run Service

```bash
# View Cloud Run service logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=orchestra-api-prod" --limit=10
```

### 2. Check Error Reporting

```bash
# View Error Reporting errors
gcloud error-reporting events list
```

### 3. Monitor Performance

```bash
# View Cloud Monitoring metrics
gcloud monitoring metrics list | grep cloud_run
```

### 4. Test API Endpoints

```bash
# Test API endpoints with authentication
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" $SERVICE_URL/health
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" $SERVICE_URL/api/version
```

### 5. Verify Deployment Revisions

```bash
# List service revisions
gcloud run revisions list --service=orchestra-api --region=us-central1

# Describe the latest revision
LATEST_REVISION=$(gcloud run revisions list --service=orchestra-api --region=us-central1 --limit=1 --format="value(metadata.name)")
gcloud run revisions describe $LATEST_REVISION --region=us-central1
```

## GitHub Actions Workflow Verification

If you're using the GitHub Actions workflow for deployment:

1. Go to the Actions tab in your GitHub repository
2. Select the latest run of the "Deploy to Cloud Run" workflow
3. Verify that all steps completed successfully
4. Check the logs of the "Verify Deployment" step to ensure it returned a successful health check

## Troubleshooting

If you encounter issues during verification:

1. Check the Cloud Run service logs:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=orchestra-api" --limit=10
   ```

2. Verify the service is using the correct container image:
   ```bash
   gcloud run services describe orchestra-api --region=us-central1 --format="value(spec.template.spec.containers[0].image)"
   ```

3. Check for any errors in the deployment step:
   ```bash
   gcloud run services describe orchestra-api --region=us-central1 --format="yaml(status.conditions)"
   ```

4. Verify that the Artifact Registry repository exists:
   ```bash
   gcloud artifacts repositories describe orchestra-repo --location=us-central1
   ```

5. Check if the image was successfully pushed:
   ```bash
   gcloud artifacts docker images list us-central1-docker.pkg.dev/your-project-id/orchestra-repo/orchestra-api
   ```

## Deployment Evidence

To document the successful deployment, collect the following evidence:

1. Screenshots of the Cloud Run service in the GCP Console
2. Output of the `deploy.sh` script showing successful deployment
3. Logs showing successful API requests
4. Performance metrics from Cloud Monitoring
5. GitHub Actions workflow run logs showing successful deployment

## Conclusion

By following the steps in this document, you can verify that the AI Orchestra project has been successfully deployed to Google Cloud Run using our consolidated deployment approach. This ensures that the application is ready for use and meets the requirements for a production deployment.
