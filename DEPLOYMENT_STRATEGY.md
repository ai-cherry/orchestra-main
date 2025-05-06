# Orchestra Deployment Strategy

## Project Details
- Project ID: cherry-ai.me
- Project Number: 525398941159
- Primary Region: us-central1
- Service Account: vertex-agent@cherry-ai.me.iam.gserviceaccount.com

## Container Registry Strategy
- Primary Registry: us-central1-docker.pkg.dev/cherry-ai.me/orchestra
- Development Images: us-central1-docker.pkg.dev/cherry-ai.me/orchestra-dev
- AI Model Images: us-central1-docker.pkg.dev/cherry-ai.me/ai-models

## Storage Strategy
- Terraform State: tfstate-cherry-ai-me-orchestra
- Build Artifacts: cherry-ai-me-cloudbuild-artifacts
- Model Storage: cherry-ai-me-model-artifacts

## Deployment Environments

### Development
- Cloud Run Service: orchestra-dev
- Image: us-central1-docker.pkg.dev/cherry-ai.me/orchestra-dev/api:latest
- Environment: development
- Allow Public Access: Yes
- Auto Scale: 0-3 instances

### Staging
- Cloud Run Service: orchestra-staging
- Image: us-central1-docker.pkg.dev/cherry-ai.me/orchestra/api:staging
- Environment: staging
- Allow Public Access: No
- Auto Scale: 1-5 instances

### Production
- Cloud Run Service: orchestra-prod
- Image: us-central1-docker.pkg.dev/cherry-ai.me/orchestra/api:prod
- Environment: production
- Allow Public Access: No
- Auto Scale: 2-10 instances

## Deployment Process
1. Build and test locally
2. Push to development registry
3. Deploy to development environment
4. Run integration tests
5. Push to staging/production registry
6. Deploy to staging/production

## Rollback Strategy
- Keep last 5 successful versions
- Enable automatic rollback on failure
- Store deployment state in cherry-ai-me-deployment-state bucket

## Monitoring
- Cloud Run metrics
- Cloud Monitoring alerts
- Cloud Logging integration
- Error tracking with Stackdriver

## Cloud Run as Primary Deployment Target

Based on careful evaluation of Orchestra's deployment needs, **Cloud Run** has been selected as the primary deployment target over Google Kubernetes Engine (GKE). This document explains this decision and provides guidance for deployment.

## Why Cloud Run?

Cloud Run offers several advantages for Orchestra's current needs:

1. **Simplicity**: Reduced operational overhead compared to managing Kubernetes clusters
2. **Cost Effectiveness**: Pay-per-use billing model with scaling to zero when not in use
3. **Managed Infrastructure**: Google handles the underlying infrastructure, reducing maintenance burden
4. **Fast Deployment**: Quicker deployment process with fewer moving parts
5. **Suitable for Stateless Applications**: Well-aligned with Orchestra's stateless API architecture

## Existing Deployment Infrastructure

The deployment infrastructure is already configured for Cloud Run:

1. **Terraform Configuration**: `infra/orchestra-terraform/` defines Cloud Run services
2. **Deployment Scripts**: `deploy.sh` and `deploy_to_production.sh` target Cloud Run
3. **Cloud Build**: `cloudbuild.yaml` is configured for Cloud Run deployment

## Deployment Process

To deploy Orchestra to production:

```bash
# Deploy to development environment
./deploy.sh dev

# Deploy to production environment
./deploy.sh prod
# or use the legacy script (redirects to deploy.sh)
./deploy_to_production.sh
```

The deployment script handles:
- Infrastructure provisioning via Terraform
- Docker image building and pushing
- Cloud Run service deployment
- PostgreSQL schema setup (if needed)
- Phidata UI deployment (if configured)

## CI/CD Integration

Continuous deployment is configured using Cloud Build:

1. **Build Trigger**: Create a Cloud Build trigger that uses `cloudbuild.yaml`
2. **Environment Variables**: Configure necessary variables in the trigger settings
3. **Secret Management**: Secrets are managed through Google Secret Manager and accessed securely

## GKE Resources (Deprecated)

The project originally contained Kubernetes manifests for GKE deployment. These files have been moved to `archived_files/kubernetes/` and are no longer maintained:

- `production-deployment.yaml`
- `production-service.yaml`
- `staging-deployment.yaml`
- `staging-service.yaml`

## When to Consider GKE

While Cloud Run is the preferred deployment target, GKE might be considered in these scenarios:

1. **Complex Stateful Workloads**: If Orchestra evolves to include stateful components that require specific persistence guarantees
2. **Special Scheduling Requirements**: Workloads requiring specific node selection or advanced scheduling
3. **Extremely High Scale**: When reaching the upper limits of Cloud Run's scaling capabilities
4. **Custom Network Policies**: Need for advanced network security beyond what Cloud Run provides

## Migration to GKE (If Needed)

If future requirements necessitate a move to GKE:

1. Update the archived Kubernetes manifests
2. Create a new deployment script targeting GKE
3. Update CI/CD pipeline to deploy to GKE
4. Plan a phased migration approach

For now, all deployment efforts and improvements should focus on optimizing the Cloud Run deployment path.
