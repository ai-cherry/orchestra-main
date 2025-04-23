# GCP Deployment Guide for Orchestra Project

This guide explains how to set up and manage the deployment of the Orchestra project to Google Cloud Platform (GCP) using GitHub Actions.

## Prerequisites

- Access to the Orchestra GitHub repository
- Google Cloud Platform account with admin privileges
- Google Kubernetes Engine (GKE) clusters for staging and production
- Google Cloud Firestore database set up
- Docker Hub account to store container images

## Setting Up GitHub Secrets

For the CI/CD pipeline to work correctly, you need to set up the following secrets in your GitHub repository:

1. Go to your GitHub repository → Settings → Secrets and variables → Actions
2. Add the following secrets:

| Secret Name | Description |
|-------------|-------------|
| `DOCKERHUB_USERNAME` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | Your Docker Hub access token |
| `GCP_CREDENTIALS` | JSON credentials for GCP service account (with GKE and Firestore access) |
| `GOOGLE_CLOUD_PROJECT` | Your GCP project ID |
| `GCP_REGION` | The region where your GKE clusters are hosted (e.g., `us-central1`) |
| `GKE_CLUSTER_NAME_PROD` | The name of your production GKE cluster |
| `GKE_CLUSTER_NAME_STAGING` | The name of your staging GKE cluster |
| `GCP_SERVICE_ACCOUNT_KEY` | The JSON content of your service account key |
| `SLACK_WEBHOOK_URL` | (Optional) Webhook URL for Slack notifications |

## Setting Up GCP Resources

### 1. Create a Service Account

1. Go to GCP Console → IAM & Admin → Service Accounts
2. Create a new service account with:
   - Kubernetes Engine Admin role
   - Firestore User role
   - Storage Object Admin role
3. Create and download a JSON key for this service account
4. Store this JSON content in the `GCP_SERVICE_ACCOUNT_KEY` GitHub secret

### 2. Set Up Firestore Database

1. Go to GCP Console → Firestore
2. Create a new database in Native mode
3. Note the project ID for your `GOOGLE_CLOUD_PROJECT` secret

### 3. Set Up GKE Clusters

For both production and staging environments:

1. Go to GCP Console → Kubernetes Engine → Clusters
2. Create a new cluster:
   - For production:
     - Name: `orchestra-prod` (use this for `GKE_CLUSTER_NAME_PROD`)
     - Region: Your preferred region (use this for `GCP_REGION`)
     - Node count: 3
     - Machine type: e2-standard-2 (2 vCPUs, 8GB memory)
   - For staging:
     - Name: `orchestra-staging` (use this for `GKE_CLUSTER_NAME_STAGING`)
     - Region: Same as production
     - Node count: 1 or 2
     - Machine type: e2-small (2 vCPUs, 2GB memory)

### 4. Setting up Kubernetes Secrets

Once your clusters are created, set up the GCP credentials secret in each cluster:

```bash
# Authenticate to GKE Production Cluster
gcloud container clusters get-credentials orchestra-prod --region=YOUR_REGION

# Create secret for production
kubectl create secret generic gcp-credentials \
  --from-file=gcp-credentials.json=/path/to/your/credentials.json

# Authenticate to GKE Staging Cluster
gcloud container clusters get-credentials orchestra-staging --region=YOUR_REGION

# Create secret for staging
kubectl create secret generic gcp-credentials \
  --from-file=gcp-credentials.json=/path/to/your/credentials.json
```

## Deployment Process

The deployment process is fully automated through GitHub Actions:

1. Push to `develop` branch: Deploys to staging environment
2. Push to `main` branch: Deploys to production environment

The workflow:
1. Runs tests and linting
2. Builds and pushes a Docker image
3. Deploys the image to the appropriate GKE cluster
4. Sends a notification when complete

## Monitoring and Troubleshooting

### Monitoring

1. GCP Console → Kubernetes Engine → Workloads: To see the status of your deployments
2. GCP Console → Kubernetes Engine → Services: To see the status of your services
3. GCP Console → Logging: To view application logs

### Troubleshooting Common Issues

1. **Authentication Failures**:
   - Check if your `GCP_CREDENTIALS` and `GCP_SERVICE_ACCOUNT_KEY` are valid and not expired
   - Ensure the service account has the necessary permissions

2. **Deployment Fails**:
   - Check the GitHub Actions workflow logs
   - Check the pod logs in GKE for application errors

3. **Firestore Connection Issues**:
   - Ensure your service account has Firestore access
   - Check that the `GOOGLE_APPLICATION_CREDENTIALS` path in containers matches the mount path

## Manual Deployment

You can also deploy manually using:

```bash
# Deploy to staging
kubectl apply -f kubernetes/staging-deployment.yaml
kubectl apply -f kubernetes/staging-service.yaml

# Deploy to production
kubectl apply -f kubernetes/production-deployment.yaml
kubectl apply -f kubernetes/production-service.yaml
```

## Future Enhancements

Consider these improvements for your GCP infrastructure:

1. Set up Cloud Monitoring and alerts for your application
2. Implement Firestore backup strategy
3. Configure Cloud CDN for better performance
4. Implement Cloud Armor for additional security
5. Use Workload Identity for better security than service account keys