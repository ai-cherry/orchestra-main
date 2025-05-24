# Deployment Trigger Configuration

## GCP Project Settings

- Project ID: cherry-ai.me
- Project Number: 525398941159
- Region: us-central1

## Service Account

- Email: vertex-agent@cherry-ai.me.iam.gserviceaccount.com
- Display Name: Vertex AI Agent Service Account

## Container Registry

- Registry URL: us-central1-docker.pkg.dev/cherry-ai.me/orchestra
- Container Repository: orchestra

## Cloud Build Triggers

### Development Environment

- Name: orchestra-dev-deploy
- Branch: ^develop$
- Configuration: cloudbuild.yaml
- Substitutions:
  - \_ENV: dev
  - \_REGION: us-central1

### Production Environment

- Name: orchestra-prod-deploy
- Branch: ^main$
- Configuration: cloudbuild.yaml
- Substitutions:
  - \_ENV: prod
  - \_REGION: us-central1

## Cloud Storage Buckets

- Terraform State: tfstate-cherry-ai-me-orchestra
- Build Artifacts: cherry-ai-me-cloudbuild-artifacts
- Model Storage: cherry-ai-me-model-artifacts

## Cloud Run Services

- Development: orchestra-dev
- Production: orchestra-prod
- Container Image: us-central1-docker.pkg.dev/cherry-ai.me/orchestra/api:latest
