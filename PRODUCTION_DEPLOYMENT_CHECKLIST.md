# Production Deployment Checklist

This document outlines everything needed to deploy the Figma webhook integration to a production environment.

## Prerequisites

### Required Accounts

- [ ] **Figma Professional or Organization Account** - Needed for API access and webhook creation
- [ ] **GitHub Account** with access to the target repository
- [ ] **Google Cloud Platform Account** - For deploying the webhook handler

### Required API Keys & Credentials

- [ ] **Figma Personal Access Token** - Generate at https://www.figma.com/settings/personal-access-tokens
- [ ] **GitHub Personal Access Token** with `repo` scope - Generate at https://github.com/settings/tokens
- [ ] **GCP Service Account Key** with appropriate permissions:
  - Cloud Run Admin
  - Secret Manager Admin
  - Storage Admin

## Infrastructure Setup

### 1. GCP Project Setup

- [ ] Create a new GCP project or use an existing one
- [ ] Enable the following APIs:
  - Cloud Run API
  - Secret Manager API
  - Cloud Build API
  - Container Registry API
  - Vertex AI API (if using AI features)

```bash
# Create project (if needed)
gcloud projects create PROJECT_ID --name="Figma Webhook Integration"

# Set project
gcloud config set project PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com \
    secretmanager.googleapis.com \
    cloudbuild.googleapis.com \
    containerregistry.googleapis.com \
    aiplatform.googleapis.com
```

### 2. GitHub Repository Configuration

- [ ] Ensure GitHub Actions is enabled for the repository
- [ ] Add the following secrets to your GitHub repository:
  - `FIGMA_PAT`: Your Figma Personal Access Token
  - `FIGMA_WEBHOOK_SECRET`: A high-entropy random string
  - `GITHUB_PAT`: GitHub Personal Access Token
  - `ORG_GCP_CREDENTIALS`: Your GCP service account key JSON

## Deployment Steps

### 1. Set Up Figma Webhook

Run the webhook setup script to generate a secure webhook secret and register with Figma:

```bash
./scripts/setup_figma_webhook.sh
```

During this process, you'll need to provide:
- Your Figma team ID
- Which events to subscribe to (typically FILE_UPDATE)
- A temporary webhook URL (you'll update this later)

### 2. Deploy Webhook Handler to Cloud Run

```bash
./scripts/deploy_webhook_to_cloud_run.sh --project=YOUR_GCP_PROJECT_ID
```

This script will:
- Create a Dockerfile
- Set up secrets in Google Secret Manager
- Build and deploy to Cloud Run
- Provide you with the public webhook URL

### 3. Update Figma Webhook URL

After deployment, you need to update your Figma webhook with the Cloud Run URL:

```bash
curl -X PATCH \
  -H "X-Figma-Token: $FIGMA_PAT" \
  -H "Content-Type: application/json" \
  "https://api.figma.com/v2/webhooks/YOUR_WEBHOOK_ID" \
  -d "{\"endpoint\": \"https://your-cloud-run-url.run.app/figma-webhook\"}"
```

### 4. Test the Production Webhook

```bash
node scripts/test_figma_webhook.js --url=https://your-cloud-run-url.run.app/figma-webhook --secret=YOUR_WEBHOOK_SECRET
```

## Post-Deployment Configuration

### 1. Set Up Domain (Optional but Recommended)

For production, it's recommended to use a custom domain:

```bash
gcloud beta run domain-mappings create \
  --service figma-webhook-handler \
  --domain webhooks.your-domain.com \
  --region us-central1
```

### 2. Configure Monitoring & Alerts

- [ ] Set up Cloud Monitoring for the Cloud Run service
- [ ] Create alerts for webhook failures
- [ ] Set up logging exports for long-term storage

```bash
# Example: Create an uptime check
gcloud monitoring uptime-check create http \
  --display-name="Figma Webhook Health" \
  --uri="https://your-cloud-run-url.run.app/health" \
  --period=300s
```

### 3. Implement Secret Rotation

Set up a schedule for rotating the webhook secret:

```bash
# Create a Cloud Scheduler job to trigger secret rotation
gcloud scheduler jobs create http rotate-webhook-secret \
  --schedule="0 0 1 */3 *" \
  --uri="https://your-cloud-run-url.run.app/rotate-secret" \
  --http-method=POST \
  --headers="Authorization=Bearer $(gcloud auth print-identity-token)"
```

## Estimated Costs (GCP)

For a typical small to medium implementation:

- **Cloud Run**: ~$5-15/month (depends on traffic)
- **Secret Manager**: ~$0.06/month (for 4-5 secrets)
- **Cloud Monitoring**: Free tier likely sufficient
- **Vertex AI** (if used): Varies based on usage

## Additional Production Considerations

### Security

- [ ] Set up IP allowlisting if possible
- [ ] Configure Cloud Armor for additional protection
- [ ] Implement rate limiting on the webhook endpoint

### Reliability

- [ ] Consider multi-region deployments for critical implementations
- [ ] Implement retry logic for failed webhook deliveries
- [ ] Set up dead-letter queues for failed events

### Compliance

- [ ] Ensure data handling complies with your organization's policies
- [ ] Configure appropriate access controls for secrets and logs
- [ ] Document the production setup for compliance audits

## Production Scaling Guidance

As your usage grows:

1. Increase Cloud Run instance limits
2. Implement request batching for high-volume events
3. Consider asynchronous processing with Pub/Sub for very high loads
4. Scale Vertex AI resources if using AI processing features
